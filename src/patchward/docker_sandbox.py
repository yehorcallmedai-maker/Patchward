# KS-TRACE: C-P2-01, C-P2-02, C-P2-04, C-P2-06, AC-P2-01, AC-P2-02, AC-P2-05
# KS-TRACE: C-P3-08, ADR-013, ADR-014
# | assumption: patchward-scanner:0.1.0 has iptables + all scanner tools baked in
# | BASE_IMAGE updated to patchward-scanner:0.1.0 after image build + digest pin
# | test: test_docker_sandbox.py
"""
Docker sandbox for scanner subprocess isolation (Phase 2).

Trust invariants enforced here:
  C-P2-01  All scanner subprocesses run inside Docker
  C-P2-02  Egress deny-by-default; per-scanner network policy
  C-P2-04  Credentials NEVER passed as env vars to container
  C-P2-06  require_docker() fail-fast at CLI startup
"""
from __future__ import annotations

import subprocess
from enum import Enum
from pathlib import Path
from typing import Any

# Base image — custom patchward-scanner image (ADR-014).
# python:3.12-slim is NOT sufficient: iptables binary absent, scanner tools absent.
# Built: 2026-06-12 | docker build -f docker/scanner.Dockerfile -t patchward-scanner:0.1.0 .
# ID pinned: docker inspect patchward-scanner:0.1.0 --format "{{.Id}}"
# DO NOT replace with a tag reference. Update after deliberate image rebuild only.
# Baked-in versions: semgrep==1.165.0, bandit==1.9.4, pip-audit==2.10.1, eslint@8.57.1, node 20 LTS
BASE_IMAGE = "patchward-scanner:0.1.0@sha256:578a8147c3604808a5c7e0f1649fc8e6a3a93610e02896d95cc36c388655a5bc"

# Single source of truth for credential key names lives in credential_proxy.py.
# Imported here so docker_sandbox.py stays in sync automatically — KS-P2-05.
# KS-TRACE: C-P2-04
from patchward.credential_proxy import _CREDENTIAL_KEYS  # noqa: E402


class NetworkPolicy(Enum):
    """
    Per-scanner Docker network policy.

    OFFLINE   — `--network none`; no outbound. Semgrep, bandit, eslint, trivy, osv.
    PYPI_ONLY — `--network bridge` + iptables ACCEPT for pypi.org/files.pythonhosted.org IPs.
                Entrypoint resolves IPs at startup, applies DROP default, then ACCEPT rules.
                pip-audit only.
    NPM_ONLY  — `--network bridge` + iptables ACCEPT for registry.npmjs.org IPs.
                Same entrypoint pattern. npm audit only.

    Values are the policy name strings (unique per member). The Docker --network flag
    is determined by _DOCKER_NETWORK_FLAG below — not by .value — to avoid Python's
    enum aliasing: PYPI_ONLY and NPM_ONLY both need "bridge" but must be distinct identities.

    C-P3-08: iptables rules enforced inside container via patchward-scanner entrypoint.
    --cap-add NET_ADMIN required for PYPI_ONLY and NPM_ONLY (added in _build_docker_cmd).

    # KS-TRACE: C-P2-02, C-P3-08, ADR-013
    """
    OFFLINE   = "OFFLINE"
    PYPI_ONLY = "PYPI_ONLY"
    NPM_ONLY  = "NPM_ONLY"


# Docker --network flag per policy.
# Separate from enum identity: PYPI_ONLY and NPM_ONLY both map to "bridge"; actual
# per-destination enforcement is via iptables OUTPUT rules inside the container (ADR-013).
# # KS-TRACE: C-P2-02, C-P3-08
_DOCKER_NETWORK_FLAG: dict[NetworkPolicy, str] = {
    NetworkPolicy.OFFLINE:   "none",
    NetworkPolicy.PYPI_ONLY: "bridge",
    NetworkPolicy.NPM_ONLY:  "bridge",
}


class DockerNotAvailableError(RuntimeError):
    """Raised by require_docker() when Docker is not running or not installed."""


def require_docker() -> None:
    """
    Fail-fast: runs `docker info` and raises DockerNotAvailableError if Docker
    is not available. Same pattern as _require_tool() in scanner.py.

    Call this once at CLI startup before any sandbox operations.

    # KS-TRACE: C-P2-06, AC-P2-02
    """
    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            timeout=10,
        )
    except FileNotFoundError:
        raise DockerNotAvailableError(
            "Docker is not running. Install Docker Desktop: "
            "https://docs.docker.com/desktop/"
        )
    if result.returncode != 0:
        raise DockerNotAvailableError(
            "Docker is not running. Install Docker Desktop: "
            "https://docs.docker.com/desktop/"
        )


class DockerSandbox:
    """
    Runs scanner commands inside Docker containers with enforced trust invariants.

    Usage::

        sandbox = DockerSandbox()
        result = sandbox.run_in_container(
            ["semgrep", "--config", "p/python", "--sarif", "."],
            repo_path=Path("/repos/my-project"),
            network_policy=NetworkPolicy.OFFLINE,
        )
        sarif_run = SARIFNormalizer.from_semgrep(json.loads(result.stdout))

    # KS-TRACE: C-P2-01, C-P2-02, C-P2-04, AC-P2-01, AC-P2-05
    """

    def __init__(self, image: str = BASE_IMAGE) -> None:
        """
        Args:
            image: Docker image reference. Default is BASE_IMAGE.
                   Pass a digest-pinned string for production:
                   e.g. "python:3.12-slim@sha256:<digest>"
        """
        self.image = image

    def _build_docker_cmd(
        self,
        command: list[str],
        repo_path: Path,
        network_policy: NetworkPolicy,
        extra_env: dict[str, str] | None = None,
    ) -> list[str]:
        """
        Build the full `docker run` command list.

        Invariants:
          - `--rm` always present (container removed after run)
          - `-v {repo_path}:/repo:ro` always present (read-only mount)
          - `--network {_DOCKER_NETWORK_FLAG[policy]}` always present
          - Credential keys in _CREDENTIAL_KEYS structurally excluded from -e flags

        # KS-TRACE: C-P2-01, C-P2-02, C-P2-04, AC-P2-05
        """
        docker_cmd: list[str] = [
            "docker", "run",
            "--rm",                                               # C-P2-01: always remove
            "-v", f"{repo_path.resolve()}:/repo:ro",              # C-P2-01: read-only mount
            "--workdir", "/repo",
            "--network", _DOCKER_NETWORK_FLAG[network_policy],      # C-P2-02: per-scanner policy
        ]

        # C-P3-08: PYPI_ONLY and NPM_ONLY require NET_ADMIN for iptables OUTPUT rules.
        # OFFLINE uses --network none; iptables rules in entrypoint still apply the
        # DROP default for defence-in-depth, but NET_ADMIN is not strictly required.
        if network_policy in (NetworkPolicy.PYPI_ONLY, NetworkPolicy.NPM_ONLY):
            docker_cmd += ["--cap-add", "NET_ADMIN"]

        # Pass policy to entrypoint script — used to select which IPs to allow.
        # BACKLOG 16/17: PATCHWARD_NETWORK_POLICY is the canonical name (the
        # "repomend" internal-naming cleanup). REPOMEND_NETWORK_POLICY is set
        # alongside it, transitionally, because the pinned scanner image
        # (BASE_IMAGE above, patchward-scanner:0.1.0@sha256:...) still bakes
        # in the OLD entrypoint.sh, which only reads the legacy name — editing
        # entrypoint.sh in this repo does not reach that already-built image
        # until it is deliberately rebuilt and the digest above is re-pinned
        # (see BACKLOG 17). Both vars carry the same value, so behavior is
        # identical either way. Drop the legacy var once BACKLOG 17 lands.
        docker_cmd += ["-e", f"PATCHWARD_NETWORK_POLICY={network_policy.name}"]
        docker_cmd += ["-e", f"REPOMEND_NETWORK_POLICY={network_policy.name}"]

        # Env vars: credentials structurally excluded — C-P2-04
        if extra_env:
            for key, val in extra_env.items():
                if key not in _CREDENTIAL_KEYS:
                    docker_cmd += ["-e", f"{key}={val}"]

        docker_cmd += [self.image] + command
        return docker_cmd

    def run_in_container(
        self,
        command: list[str],
        repo_path: Path,
        network_policy: NetworkPolicy,
        extra_env: dict[str, str] | None = None,
        timeout: int = 300,
        acceptable_exit_codes: tuple[int, ...] = (0, 1),
    ) -> subprocess.CompletedProcess:
        """
        Run command inside a Docker container scoped to repo_path.

        Args:
            command: Command to execute inside the container.
            repo_path: Host path mounted read-only at /repo.
            network_policy: NetworkPolicy for this scanner.
            extra_env: Extra env vars to pass in (credentials auto-excluded).
            timeout: Hard timeout in seconds. Default 300.
            acceptable_exit_codes: Exit codes that are not treated as errors.
                                   Default (0, 1) — 0 = clean, 1 = findings found.

        Returns:
            CompletedProcess with stdout/stderr as UTF-8 text.

        Raises:
            subprocess.CalledProcessError if exit code not in acceptable_exit_codes.

        # KS-TRACE: AC-P2-01, C-P2-01, C-P2-02
        """
        docker_cmd = self._build_docker_cmd(command, repo_path, network_policy, extra_env)

        result = subprocess.run(
            docker_cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )

        if result.returncode not in acceptable_exit_codes:
            raise subprocess.CalledProcessError(
                result.returncode,
                docker_cmd,
                output=result.stdout,
                stderr=result.stderr,
            )

        return result
