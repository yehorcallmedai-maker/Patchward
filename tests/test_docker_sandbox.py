# KS-TRACE: C-P2-01, C-P2-02, C-P2-04, C-P2-06, AC-P2-01, AC-P2-02, AC-P2-05
# | assumption: Docker available for integration tests; unit tests mock subprocess
# | test: this file
"""
KS-P2-02 + KS-P3-02 Docker sandbox tests.

Test categories:
  1. require_docker() — fail-fast unit tests (AC-P2-02)
  2. _build_docker_cmd() — structural invariants: --rm, :ro, --network, no credentials
  3. Per-scanner network policy assertions
  3b. C-P3-08 structural tests — --cap-add NET_ADMIN and REPOMEND_NETWORK_POLICY env var
  4. AC-P2-01 integration tests — requires Docker running
  5. AC-P3-01/AC-P3-02 egress hardening integration tests — requires Docker + repomend-scanner:0.1.0
"""
from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from repomend.docker_sandbox import (
    BASE_IMAGE,
    NetworkPolicy,
    DockerNotAvailableError,
    DockerSandbox,
    _CREDENTIAL_KEYS,
    require_docker,
)
from repomend.scanner import (
    _SCANNER_NETWORK_POLICIES,
    run_semgrep,
    run_bandit,
    run_pip_audit,
    run_eslint,
    run_npm_audit,
    run_trivy,
    run_osv_scanner,
)


# ---------------------------------------------------------------------------
# 1. require_docker() — AC-P2-02
# ---------------------------------------------------------------------------

def test_require_docker_fails_fast_on_nonzero_returncode() -> None:
    """AC-P2-02: docker info non-zero → DockerNotAvailableError with correct message."""
    mock_result = MagicMock()
    mock_result.returncode = 1
    with patch("repomend.docker_sandbox.subprocess.run", return_value=mock_result):
        with pytest.raises(DockerNotAvailableError) as exc_info:
            require_docker()
    assert "Docker is not running" in str(exc_info.value)
    assert "https://docs.docker.com/desktop/" in str(exc_info.value)


def test_require_docker_fails_fast_when_docker_not_found() -> None:
    """AC-P2-02: docker not on PATH (FileNotFoundError) → DockerNotAvailableError."""
    with patch(
        "repomend.docker_sandbox.subprocess.run",
        side_effect=FileNotFoundError("docker not found"),
    ):
        with pytest.raises(DockerNotAvailableError) as exc_info:
            require_docker()
    assert "Docker is not running" in str(exc_info.value)


def test_require_docker_passes_when_docker_running() -> None:
    """require_docker() must not raise when docker info returns 0."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    with patch("repomend.docker_sandbox.subprocess.run", return_value=mock_result):
        require_docker()  # must not raise


# ---------------------------------------------------------------------------
# 2. _build_docker_cmd() structural invariants
# ---------------------------------------------------------------------------

def test_container_always_removed() -> None:
    """C-P2-01: --rm must always be present in docker command."""
    sandbox = DockerSandbox()
    cmd = sandbox._build_docker_cmd(
        ["semgrep", "--sarif", "."],
        Path("/repo"),
        NetworkPolicy.OFFLINE,
    )
    assert "--rm" in cmd


def test_repo_mounted_readonly() -> None:
    """C-P2-01: repo mount must include :ro flag."""
    sandbox = DockerSandbox()
    cmd = sandbox._build_docker_cmd(
        ["semgrep", "--sarif", "."],
        Path("/repo"),
        NetworkPolicy.OFFLINE,
    )
    mount_flags = [arg for arg in cmd if ":/repo:ro" in arg]
    assert len(mount_flags) == 1, f"Expected exactly one :ro mount, got: {mount_flags}"


def test_credentials_not_in_container_when_passed_in_extra_env() -> None:
    """
    C-P2-04 / AC-P2-05: credential keys must be excluded even if passed in extra_env.
    Structural test — verifies docker command contains no -e CREDENTIAL=... flags.
    """
    sandbox = DockerSandbox()
    poisoned_env = {
        "ANTHROPIC_API_KEY": "sk-ant-secret",
        "LANGFUSE_PUBLIC_KEY": "pk-lf-secret",
        "LANGFUSE_SECRET_KEY": "sk-lf-secret",
        "SAFE_VAR": "allowed",
    }
    cmd = sandbox._build_docker_cmd(
        ["python", "-c", "pass"],
        Path("/repo"),
        NetworkPolicy.OFFLINE,
        extra_env=poisoned_env,
    )
    cmd_str = " ".join(cmd)
    for cred_key in _CREDENTIAL_KEYS:
        assert cred_key not in cmd_str, (
            f"Credential key '{cred_key}' found in docker command — violates C-P2-04"
        )
    # Safe var must be present
    assert "SAFE_VAR=allowed" in cmd_str


def test_credentials_absent_with_no_extra_env() -> None:
    """AC-P2-05: no credential keys in docker command when extra_env is None.

    REPOMEND_NETWORK_POLICY is always present in the command — intentional (C-P3-08).
    This test only asserts that credential keys are structurally absent.
    """
    sandbox = DockerSandbox()
    cmd = sandbox._build_docker_cmd(
        ["python", "-c", "pass"],
        Path("/repo"),
        NetworkPolicy.OFFLINE,
        extra_env=None,
    )
    cmd_str = " ".join(cmd)
    # REPOMEND_NETWORK_POLICY always present — expected, not a credential.
    # Credential keys must be structurally absent — C-P2-04.
    for cred_key in _CREDENTIAL_KEYS:
        assert cred_key not in cmd_str, (
            f"Credential key '{cred_key}' found in docker command — violates C-P2-04"
        )


def test_credential_keys_constant_contains_all_three() -> None:
    """_CREDENTIAL_KEYS must cover all three credential vars."""
    assert "ANTHROPIC_API_KEY" in _CREDENTIAL_KEYS
    assert "LANGFUSE_PUBLIC_KEY" in _CREDENTIAL_KEYS
    assert "LANGFUSE_SECRET_KEY" in _CREDENTIAL_KEYS


# ---------------------------------------------------------------------------
# 3. Per-scanner network policy
# ---------------------------------------------------------------------------

def test_offline_scanner_gets_network_none() -> None:
    """C-P2-02: NetworkPolicy.OFFLINE must map to --network none."""
    sandbox = DockerSandbox()
    cmd = sandbox._build_docker_cmd(
        ["semgrep", "--sarif", "."],
        Path("/repo"),
        NetworkPolicy.OFFLINE,
    )
    assert "--network" in cmd
    network_idx = cmd.index("--network")
    assert cmd[network_idx + 1] == "none"


def test_pypi_only_gets_bridge_network() -> None:
    """C-P2-02: NetworkPolicy.PYPI_ONLY → --network bridge."""
    sandbox = DockerSandbox()
    cmd = sandbox._build_docker_cmd(
        ["pip-audit", "-r", "requirements.txt"],
        Path("/repo"),
        NetworkPolicy.PYPI_ONLY,
    )
    network_idx = cmd.index("--network")
    assert cmd[network_idx + 1] == "bridge"


def test_npm_only_gets_bridge_network() -> None:
    """C-P2-02: NetworkPolicy.NPM_ONLY → --network bridge."""
    sandbox = DockerSandbox()
    cmd = sandbox._build_docker_cmd(
        ["npm", "audit", "--json"],
        Path("/repo"),
        NetworkPolicy.NPM_ONLY,
    )
    network_idx = cmd.index("--network")
    assert cmd[network_idx + 1] == "bridge"


def test_per_scanner_network_policy_table() -> None:
    """All 7 scanners must have an entry in _SCANNER_NETWORK_POLICIES."""
    expected_scanners = {
        "semgrep", "bandit", "pip-audit",
        "eslint", "npm-audit", "trivy", "osv-scanner",
    }
    assert set(_SCANNER_NETWORK_POLICIES.keys()) == expected_scanners


def test_semgrep_uses_offline_policy() -> None:
    assert _SCANNER_NETWORK_POLICIES["semgrep"] == "OFFLINE"


def test_pip_audit_uses_pypi_only_policy() -> None:
    assert _SCANNER_NETWORK_POLICIES["pip-audit"] == "PYPI_ONLY"


def test_npm_audit_uses_npm_only_policy() -> None:
    assert _SCANNER_NETWORK_POLICIES["npm-audit"] == "NPM_ONLY"


def test_bandit_eslint_trivy_osv_use_offline() -> None:
    for scanner in ("bandit", "eslint", "trivy", "osv-scanner"):
        assert _SCANNER_NETWORK_POLICIES[scanner] == "OFFLINE", (
            f"Expected OFFLINE for {scanner}"
        )


def test_sandbox_passes_correct_network_to_semgrep() -> None:
    """run_semgrep with sandbox → docker command must use --network none."""
    sandbox = DockerSandbox()
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = '{"runs": []}'

    with patch.object(sandbox, "run_in_container", return_value=mock_result) as mock_run:
        run_semgrep(Path("/repo"), sandbox=sandbox)
        call_kwargs = mock_run.call_args
        policy = call_kwargs.args[2]  # network_policy positional arg
        assert policy == NetworkPolicy.OFFLINE


def test_sandbox_passes_pypi_only_to_pip_audit(tmp_path: Path) -> None:
    """run_pip_audit with sandbox → docker command must use PYPI_ONLY."""
    (tmp_path / "requirements.txt").write_text("requests==2.31.0\n")
    sandbox = DockerSandbox()
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = '{"dependencies": []}'

    with patch.object(sandbox, "run_in_container", return_value=mock_result) as mock_run:
        run_pip_audit(tmp_path, sandbox=sandbox)
        policy = mock_run.call_args.args[2]
        assert policy == NetworkPolicy.PYPI_ONLY


def test_image_is_in_docker_cmd() -> None:
    """BASE_IMAGE must appear in the built docker command."""
    sandbox = DockerSandbox()
    cmd = sandbox._build_docker_cmd(["python", "-V"], Path("/repo"), NetworkPolicy.OFFLINE)
    assert BASE_IMAGE in cmd


def test_custom_image_used_when_passed() -> None:
    """DockerSandbox(image=...) must use the provided image, not BASE_IMAGE."""
    pinned = "python:3.12-slim@sha256:abc123"
    sandbox = DockerSandbox(image=pinned)
    cmd = sandbox._build_docker_cmd(["python", "-V"], Path("/repo"), NetworkPolicy.OFFLINE)
    assert pinned in cmd
    assert BASE_IMAGE not in cmd  # floating tag must not appear


# ---------------------------------------------------------------------------
# 3b. C-P3-08 structural tests — NET_ADMIN cap + REPOMEND_NETWORK_POLICY env var
# ---------------------------------------------------------------------------

def test_pypi_only_gets_net_admin_cap() -> None:
    """C-P3-08: PYPI_ONLY must include --cap-add NET_ADMIN for iptables enforcement."""
    # KS-TRACE: C-P3-08, ADR-013 | assumption: NET_ADMIN present for bridge policies
    sandbox = DockerSandbox()
    cmd = sandbox._build_docker_cmd(
        ["pip-audit", "-r", "requirements.txt"],
        Path("/repo"),
        NetworkPolicy.PYPI_ONLY,
    )
    assert "--cap-add" in cmd, "--cap-add missing from PYPI_ONLY command"
    cap_idx = cmd.index("--cap-add")
    assert cmd[cap_idx + 1] == "NET_ADMIN", f"Expected NET_ADMIN, got {cmd[cap_idx + 1]}"


def test_npm_only_gets_net_admin_cap() -> None:
    """C-P3-08: NPM_ONLY must include --cap-add NET_ADMIN for iptables enforcement."""
    sandbox = DockerSandbox()
    cmd = sandbox._build_docker_cmd(
        ["npm", "audit", "--json"],
        Path("/repo"),
        NetworkPolicy.NPM_ONLY,
    )
    assert "--cap-add" in cmd, "--cap-add missing from NPM_ONLY command"
    cap_idx = cmd.index("--cap-add")
    assert cmd[cap_idx + 1] == "NET_ADMIN"


def test_offline_does_not_get_net_admin_cap() -> None:
    """C-P3-08: OFFLINE must NOT include --cap-add NET_ADMIN (--network none is sufficient)."""
    sandbox = DockerSandbox()
    cmd = sandbox._build_docker_cmd(
        ["semgrep", "--sarif", "."],
        Path("/repo"),
        NetworkPolicy.OFFLINE,
    )
    assert "--cap-add" not in cmd, "--cap-add must not appear for OFFLINE policy"


def test_pypi_only_passes_policy_env_var() -> None:
    """C-P3-08: REPOMEND_NETWORK_POLICY=PYPI_ONLY must be passed to entrypoint."""
    sandbox = DockerSandbox()
    cmd = sandbox._build_docker_cmd(
        ["pip-audit", "-r", "requirements.txt"],
        Path("/repo"),
        NetworkPolicy.PYPI_ONLY,
    )
    assert "REPOMEND_NETWORK_POLICY=PYPI_ONLY" in cmd


def test_npm_only_passes_policy_env_var() -> None:
    """C-P3-08: REPOMEND_NETWORK_POLICY=NPM_ONLY must be passed to entrypoint."""
    sandbox = DockerSandbox()
    cmd = sandbox._build_docker_cmd(
        ["npm", "audit", "--json"],
        Path("/repo"),
        NetworkPolicy.NPM_ONLY,
    )
    assert "REPOMEND_NETWORK_POLICY=NPM_ONLY" in cmd


def test_offline_passes_policy_env_var() -> None:
    """C-P3-08: REPOMEND_NETWORK_POLICY=OFFLINE must be passed to entrypoint."""
    sandbox = DockerSandbox()
    cmd = sandbox._build_docker_cmd(
        ["semgrep", "--sarif", "."],
        Path("/repo"),
        NetworkPolicy.OFFLINE,
    )
    assert "REPOMEND_NETWORK_POLICY=OFFLINE" in cmd


# ---------------------------------------------------------------------------
# 4. AC-P2-01 integration tests — requires Docker running
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_run_in_container_returns_output() -> None:
    """
    AC-P2-01: run_in_container executes a command and returns output.
    Uses `python --version` — no scanner install needed.
    Requires: Docker Desktop running.
    """
    sandbox = DockerSandbox()
    result = sandbox.run_in_container(
        ["python", "--version"],
        repo_path=Path("C:/Dev/Projects/repomend-fixture"),
        network_policy=NetworkPolicy.OFFLINE,
        timeout=60,
        acceptable_exit_codes=(0,),
    )
    assert result.returncode == 0
    # Python version appears on stdout or stderr depending on version
    output = result.stdout + result.stderr
    assert "Python 3" in output


@pytest.mark.integration
def test_network_none_blocks_egress() -> None:
    """
    AC-P2-03: --network none actually blocks outbound connections.
    Uses Python's urllib — no curl required in the image.
    Requires: Docker Desktop running.
    """
    sandbox = DockerSandbox()
    result = sandbox.run_in_container(
        [
            "python", "-c",
            (
                "import urllib.request; "
                "urllib.request.urlopen('https://example.com', timeout=5); "
                "print('REACHABLE')"
            ),
        ],
        repo_path=Path("C:/Dev/Projects/repomend-fixture"),
        network_policy=NetworkPolicy.OFFLINE,
        timeout=30,
        acceptable_exit_codes=(0, 1),  # 1 = unhandled exception (network blocked)
    )
    # If network is blocked, urlopen raises → "REACHABLE" never printed
    assert "REACHABLE" not in result.stdout


@pytest.mark.integration
def test_pypi_only_allows_pip_index_query() -> None:
    """
    AC-P2-03: PYPI_ONLY (bridge) allows pip to query the PyPI index.
    Uses `pip index versions requests` — reads from PyPI, installs nothing.
    Requires: Docker Desktop running, outbound HTTPS to pypi.org.
    """
    sandbox = DockerSandbox()
    result = sandbox.run_in_container(
        ["pip", "index", "versions", "requests", "--no-input"],
        repo_path=Path("C:/Dev/Projects/repomend-fixture"),
        network_policy=NetworkPolicy.PYPI_ONLY,
        timeout=60,
        acceptable_exit_codes=(0,),
    )
    assert result.returncode == 0
    # pip index versions prints the available versions to stdout
    assert "requests" in result.stdout or "Available versions" in result.stdout


@pytest.mark.integration
def test_run_in_container_semgrep_on_fixture() -> None:
    """
    AC-P2-01 full: run semgrep inside Docker on fixture repo, assert SARIF returned.
    semgrep is baked into repomend-scanner:0.1.0 — no runtime install needed (ADR-014).
    Requires: Docker Desktop running.
    """
    import json
    fixture = Path("C:/Dev/Projects/repomend-fixture")
    if not fixture.exists():
        pytest.skip("repomend-fixture not available")

    sandbox = DockerSandbox()
    result = sandbox.run_in_container(
        [
            # --pattern with --lang runs fully offline — no ruleset download from registry.
            # p/python requires fetching rules from semgrep.dev, blocked by OFFLINE policy.
            # This pattern matches the subprocess-shell-true plant in vulnerable.py (line 24).
            # --metrics off: without this, semgrep blocks for its full internal timeout
            # (~60s) waiting for a metrics/version-check call that is dropped by --network none.
            "semgrep", "--pattern", "subprocess.run($...ARGS, shell=True)",
            "--lang", "python", "--sarif", "--quiet", "--metrics", "off", ".",
        ],
        repo_path=fixture,
        network_policy=NetworkPolicy.OFFLINE,  # semgrep baked in; inline pattern = no network
        extra_env={"SEMGREP_SEND_METRICS": "off"},  # belt-and-suspenders: env var also disables telemetry
        timeout=120,
        acceptable_exit_codes=(0, 1),
    )
    assert result.returncode in (0, 1)
    sarif = json.loads(result.stdout)
    assert "runs" in sarif


# ---------------------------------------------------------------------------
# 5. AC-P3-01 / AC-P3-02 egress hardening — requires repomend-scanner:0.1.0
# KS-TRACE: C-P3-08, AC-P3-01, AC-P3-02, ADR-013, ADR-014
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_npm_only_allows_npm_registry_query() -> None:
    """
    AC-P3-01: NPM_ONLY policy allows npm to query the npm registry.

    Uses `npm view lodash version` — reads package metadata from registry.npmjs.org,
    installs nothing. If iptables ACCEPT rules for registry.npmjs.org are applied
    correctly, npm must succeed.
    Requires: Docker Desktop running, outbound HTTPS to registry.npmjs.org.
    """
    sandbox = DockerSandbox()
    result = sandbox.run_in_container(
        ["npm", "view", "lodash", "version"],
        repo_path=Path("C:/Dev/Projects/repomend-fixture"),
        network_policy=NetworkPolicy.NPM_ONLY,
        timeout=60,
        acceptable_exit_codes=(0,),
    )
    assert result.returncode == 0
    output = result.stdout + result.stderr
    # npm view returns the latest version string e.g. "4.17.21"
    assert any(c.isdigit() for c in output), (
        f"Expected version number in npm output, got: {output!r}"
    )


@pytest.mark.integration
def test_pypi_only_blocks_non_pypi_hostname() -> None:
    """
    AC-P3-01: PYPI_ONLY blocks connections to non-allowlisted hostnames.

    Uses Python urllib to attempt HTTPS to example.com (not in PYPI_ONLY allowlist).
    iptables OUTPUT DROP default must block the SYN before TCP handshake completes.
    """
    sandbox = DockerSandbox()
    result = sandbox.run_in_container(
        [
            "python", "-c",
            (
                "import urllib.request; "
                "urllib.request.urlopen('https://example.com', timeout=5); "
                "print('REACHABLE')"
            ),
        ],
        repo_path=Path("C:/Dev/Projects/repomend-fixture"),
        network_policy=NetworkPolicy.PYPI_ONLY,
        timeout=30,
        acceptable_exit_codes=(0, 1),
    )
    assert "REACHABLE" not in (result.stdout + result.stderr), (
        "example.com was reachable from PYPI_ONLY container — iptables not blocking"
    )


@pytest.mark.integration
def test_ac_p3_02_pypi_only_blocks_raw_ip_not_dns() -> None:
    """
    AC-P3-02: PYPI_ONLY container blocks curl to a raw non-allowlisted IP address.

    Target: 1.1.1.1 (Cloudflare DNS resolver — confirmed non-allowlisted for PYPI_ONLY).
    curl targets the IP directly — no hostname, no DNS resolution involved.

    Pass conditions:
      - curl fails (iptables OUTPUT DROP blocks the SYN packet)
      - "Could not resolve" absent from output (no DNS involved for raw IP curl)
      - "Name or service not known" absent (same — confirms iptables, not DNS, is blocking)
      - iptables -L OUTPUT shows DROP default policy (mechanism verified in same exec)

    Failure conditions:
      - curl CURL_EXIT:0 → connection succeeded, iptables not enforcing
      - DNS error in output → entrypoint regression (raw IP bypasses DNS, so any DNS
        error here indicates a different configuration problem)

    This test closes the bypass-by-IP gap that motivated rejecting Option B (DNS blocklist)
    in ADR-013. A DNS blocklist would not block this curl; iptables OUTPUT rules will.

    # KS-TRACE: AC-P3-02, ADR-013, C-P3-08
    """
    sandbox = DockerSandbox()
    # Run curl to raw IP + dump iptables OUTPUT chain in one container exec.
    # iptables rules set by entrypoint persist for the lifetime of this container,
    # so iptables -L inside the same sh -c invocation reflects the active rules.
    result = sandbox.run_in_container(
        [
            "sh", "-c",
            (
                "curl --max-time 5 --silent --output /dev/null https://1.1.1.1/ 2>&1;"
                " echo CURL_EXIT:$?;"
                " iptables -L OUTPUT -n 2>&1"
            ),
        ],
        repo_path=Path("C:/Dev/Projects/repomend-fixture"),
        network_policy=NetworkPolicy.PYPI_ONLY,
        timeout=30,
        acceptable_exit_codes=(0,),
    )
    output = result.stdout + result.stderr

    # curl must have failed — iptables DROP blocked the connection
    assert "CURL_EXIT:0" not in output, (
        "curl to non-allowlisted IP 1.1.1.1 succeeded — "
        "iptables OUTPUT rules not enforcing PYPI_ONLY allowlist"
    )

    # Confirm DNS was not involved (raw IP curl cannot trigger DNS failure;
    # if either string appears, the entrypoint has a configuration regression)
    assert "Could not resolve" not in output, (
        "DNS error on raw IP curl — unexpected; check entrypoint /etc/hosts ordering"
    )
    assert "Name or service not known" not in output

    # Confirm iptables OUTPUT DROP policy is active in this container
    assert "DROP" in output, (
        "iptables OUTPUT DROP policy not found in chain listing — "
        "entrypoint may not have applied iptables rules (check --cap-add NET_ADMIN)"
    )
