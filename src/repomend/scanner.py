# KS-TRACE: AC-P1-01, AC-P1-02, AC-P1-03, AC-P1-08, AC-P1-09, C-03, C-07, C-08
# KS-TRACE: C-P2-01, C-P2-02 — sandbox parameter wires Docker path (Phase 2)
# | assumption: all scanners on PATH for local path; Docker path uses container
# | test: test_sarif.py (normalizer unit), test_docker_sandbox.py (sandbox path)
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

import typer

from repomend.sarif import SARIFNormalizer, SARIFRun

if TYPE_CHECKING:
    from repomend.docker_sandbox import DockerSandbox, NetworkPolicy


# ---------------------------------------------------------------------------
# Ecosystem detection  (C-08, AC-P1-09)
# ---------------------------------------------------------------------------

def is_node_repo(repo_path: Path) -> bool:
    """True if repo contains a package.json — gates ESLint and npm audit."""
    return (repo_path / "package.json").exists()


# ---------------------------------------------------------------------------
# PATH checks — fail fast with actionable messages (Risk R-01)
# ---------------------------------------------------------------------------

def _require_tool(name: str, install_hint: str) -> None:
    if shutil.which(name) is None:
        typer.echo(
            f"[repomend] ERROR: '{name}' not found on PATH. {install_hint}",
            err=True,
        )
        raise typer.Exit(code=1)


# ---------------------------------------------------------------------------
# Subprocess helper
# ---------------------------------------------------------------------------

def _run_subprocess(
    cmd: list[str],
    *,
    timeout: int = 120,
    cwd: Path | None = None,
    acceptable_exit_codes: tuple[int, ...] = (0,),
) -> subprocess.CompletedProcess:
    """
    Run a command, capture stdout/stderr, raise typer.Exit on unexpected failures.
    acceptable_exit_codes: non-zero codes that mean "findings found" not "tool error".
    """
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(cwd) if cwd else None,
        )
    except subprocess.TimeoutExpired:
        typer.echo(f"[repomend] ERROR: '{cmd[0]}' timed out after {timeout}s", err=True)
        raise typer.Exit(code=1)
    except Exception as exc:
        typer.echo(f"[repomend] ERROR: '{cmd[0]}' failed to launch: {exc}", err=True)
        raise typer.Exit(code=1)

    if result.returncode not in acceptable_exit_codes:
        typer.echo(
            f"[repomend] ERROR: '{cmd[0]}' exited {result.returncode}:\n{result.stderr[:500]}",
            err=True,
        )
        raise typer.Exit(code=1)

    return result


def _parse_json(raw: str, tool_name: str) -> dict | list:
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        typer.echo(
            f"[repomend] ERROR: could not parse {tool_name} output as JSON: {exc}",
            err=True,
        )
        raise typer.Exit(code=1)


# ---------------------------------------------------------------------------
# Scanner wrappers — each returns a SARIFRun
# ---------------------------------------------------------------------------

def run_semgrep(
    repo_path: Path,
    rules: str = "p/python",
    sandbox: "DockerSandbox | None" = None,
) -> SARIFRun:
    """
    Run Semgrep and return a SARIFRun.
    sandbox=None → local subprocess (Phase 1 path)
    sandbox=DockerSandbox() → container with NetworkPolicy.OFFLINE (Phase 2 path)
    # KS-TRACE: AC-P1-01, AC-P1-02, C-03, C-P2-01 | semgrep exits 1 when findings found
    """
    cmd = ["semgrep", "--config", rules, "--sarif", "--quiet", "."]
    if sandbox is not None:
        from repomend.docker_sandbox import NetworkPolicy
        result = sandbox.run_in_container(cmd, repo_path, NetworkPolicy.OFFLINE)
    else:
        _require_tool("semgrep", "Install: pip install semgrep")
        result = _run_subprocess(
            ["semgrep", "--config", rules, "--sarif", "--quiet", str(repo_path)],
            acceptable_exit_codes=(0, 1),
        )
    raw = _parse_json(result.stdout, "semgrep")
    return SARIFNormalizer.from_semgrep(raw)  # type: ignore[arg-type]


def run_bandit(
    repo_path: Path,
    sandbox: "DockerSandbox | None" = None,
) -> SARIFRun:
    """
    Run Bandit recursively and return a SARIFRun.
    # KS-TRACE: AC-P1-03, C-03, C-P2-01 | bandit exits 1 when findings found
    """
    cmd = ["bandit", "-r", "/repo", "--format", "json", "-q"]
    if sandbox is not None:
        from repomend.docker_sandbox import NetworkPolicy
        result = sandbox.run_in_container(cmd, repo_path, NetworkPolicy.OFFLINE)
    else:
        _require_tool("bandit", "Install: pip install bandit")
        result = _run_subprocess(
            ["bandit", "-r", str(repo_path), "--format", "json", "-q"],
            acceptable_exit_codes=(0, 1),
        )
    raw = _parse_json(result.stdout, "bandit")
    return SARIFNormalizer.from_bandit(raw)  # type: ignore[arg-type]


def run_pip_audit(
    repo_path: Path,
    sandbox: "DockerSandbox | None" = None,
) -> SARIFRun:
    """
    Run pip-audit against requirements.txt in repo_path (if present).
    Returns empty SARIFRun (not an error) if no requirements.txt found.
    # KS-TRACE: AC-P1-08, C-03, C-P2-01, C-P2-02
    """
    req_file = repo_path / "requirements.txt"
    if not req_file.exists():
        typer.echo(
            f"[repomend] SKIP: pip-audit — no requirements.txt in {repo_path}",
            err=True,
        )
        return SARIFRun(tool_name="pip-audit")

    cmd = ["pip-audit", "-r", "/repo/requirements.txt", "--format", "json"]
    if sandbox is not None:
        from repomend.docker_sandbox import NetworkPolicy
        result = sandbox.run_in_container(cmd, repo_path, NetworkPolicy.PYPI_ONLY)
    else:
        _require_tool("pip-audit", "Install: pip install pip-audit")
        result = _run_subprocess(
            ["pip-audit", "-r", str(req_file), "--format", "json"],
            acceptable_exit_codes=(0, 1),
        )
    raw = _parse_json(result.stdout, "pip-audit")
    return SARIFNormalizer.from_pip_audit(raw)  # type: ignore[arg-type]


def run_eslint(
    repo_path: Path,
    sandbox: "DockerSandbox | None" = None,
) -> SARIFRun:
    """
    Run ESLint on repo_path. Skipped (not errored) if no package.json.
    # KS-TRACE: AC-P1-09, C-08, C-03, C-P2-01
    """
    if not is_node_repo(repo_path):
        typer.echo(
            f"[repomend] SKIP: eslint — no package.json in {repo_path}",
            err=True,
        )
        return SARIFRun(tool_name="eslint")

    cmd = ["eslint", "/repo", "--format", "json"]
    if sandbox is not None:
        from repomend.docker_sandbox import NetworkPolicy
        result = sandbox.run_in_container(cmd, repo_path, NetworkPolicy.OFFLINE)
    else:
        _require_tool("eslint", "Install: npm install -g eslint")
        result = _run_subprocess(
            ["eslint", str(repo_path), "--format", "json"],
            acceptable_exit_codes=(0, 1),
        )
    raw = _parse_json(result.stdout, "eslint")
    return SARIFNormalizer.from_eslint(raw)  # type: ignore[arg-type]


def run_npm_audit(
    repo_path: Path,
    sandbox: "DockerSandbox | None" = None,
) -> SARIFRun:
    """
    Run npm audit from within repo_path. Skipped if no package.json.
    # KS-TRACE: AC-P1-09, C-08, C-03, C-P2-01, C-P2-02
    """
    if not is_node_repo(repo_path):
        typer.echo(
            f"[repomend] SKIP: npm-audit — no package.json in {repo_path}",
            err=True,
        )
        return SARIFRun(tool_name="npm-audit")

    cmd = ["npm", "audit", "--json"]
    if sandbox is not None:
        from repomend.docker_sandbox import NetworkPolicy
        result = sandbox.run_in_container(cmd, repo_path, NetworkPolicy.NPM_ONLY)
    else:
        _require_tool("npm", "Install Node.js: https://nodejs.org")
        result = _run_subprocess(
            ["npm", "audit", "--json"],
            cwd=repo_path,
            acceptable_exit_codes=(0, 1),
        )
    raw = _parse_json(result.stdout, "npm-audit")
    return SARIFNormalizer.from_npm_audit(raw)  # type: ignore[arg-type]


def run_trivy(
    repo_path: Path,
    sandbox: "DockerSandbox | None" = None,
) -> SARIFRun:
    """
    Run Trivy filesystem scan with SARIF output.
    # KS-TRACE: AC-P1-03, C-03, C-P2-01 | trivy exits 1 when vulnerabilities found
    """
    cmd = ["trivy", "fs", "--format", "sarif", "--quiet", "/repo"]
    if sandbox is not None:
        from repomend.docker_sandbox import NetworkPolicy
        result = sandbox.run_in_container(cmd, repo_path, NetworkPolicy.OFFLINE)
    else:
        if shutil.which("trivy") is None:
            typer.echo(
                "[repomend] SKIP: trivy — not found on PATH"
                " (Install: https://aquasecurity.github.io/trivy/latest/getting-started/installation/)",
                err=True,
            )
            return SARIFRun(tool_name="trivy")
        result = _run_subprocess(
            ["trivy", "fs", "--format", "sarif", "--quiet", str(repo_path)],
            acceptable_exit_codes=(0, 1),
        )
    if not result.stdout.strip():
        typer.echo(
            "[repomend] SKIP: trivy — no scannable targets (no Dockerfile or IaC files found)",
            err=True,
        )
        return SARIFRun(tool_name="trivy")
    raw = _parse_json(result.stdout, "trivy")
    return SARIFNormalizer.from_trivy(raw)  # type: ignore[arg-type]


def run_osv_scanner(
    repo_path: Path,
    sandbox: "DockerSandbox | None" = None,
) -> SARIFRun:
    """
    Run OSV-Scanner on repo_path with JSON output.
    Skipped (not errored) if osv-scanner is not on PATH.
    # KS-TRACE: AC-P1-03, C-03, C-P2-01 | osv-scanner exits 1 when vulnerabilities found
    """
    cmd = ["osv-scanner", "--json", "/repo"]
    if sandbox is not None:
        from repomend.docker_sandbox import NetworkPolicy
        result = sandbox.run_in_container(cmd, repo_path, NetworkPolicy.OFFLINE)
    else:
        if shutil.which("osv-scanner") is None:
            typer.echo(
                "[repomend] SKIP: osv-scanner — not found on PATH"
                " (Install: https://google.github.io/osv-scanner/installation/)",
                err=True,
            )
            return SARIFRun(tool_name="osv-scanner")
        result = _run_subprocess(
            ["osv-scanner", "--json", str(repo_path)],
            acceptable_exit_codes=(0, 1),
        )
    if not result.stdout.strip():
        typer.echo(
            "[repomend] SKIP: osv-scanner — no scannable targets found",
            err=True,
        )
        return SARIFRun(tool_name="osv-scanner")
    raw = _parse_json(result.stdout, "osv-scanner")
    return SARIFNormalizer.from_osv_scanner(raw)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Convenience: run all scanners and return combined findings list
# ---------------------------------------------------------------------------

# Per-scanner network policy table — used by run_all_scanners with sandbox
_SCANNER_NETWORK_POLICIES: dict[str, str] = {
    "semgrep":     "OFFLINE",
    "bandit":      "OFFLINE",
    "pip-audit":   "PYPI_ONLY",
    "eslint":      "OFFLINE",
    "npm-audit":   "NPM_ONLY",
    "trivy":       "OFFLINE",
    "osv-scanner": "OFFLINE",
}


def run_all_scanners(
    repo_path: Path,
    semgrep_rules: str = "p/python",
    sandbox: "DockerSandbox | None" = None,
) -> list[SARIFRun]:
    """
    Run all 7 scanners. JS/TS scanners are skipped (not errored) for non-Node repos.
    sandbox=None → local subprocess (Phase 1 path, all existing tests unaffected)
    sandbox=DockerSandbox() → all subprocesses routed through Docker (Phase 2 path)
    Returns one SARIFRun per scanner regardless of finding count.
    # KS-TRACE: C-07, C-08, AC-P1-09, C-P2-01, C-P2-02
    """
    runners = [
        lambda: run_semgrep(repo_path, semgrep_rules, sandbox),
        lambda: run_bandit(repo_path, sandbox),
        lambda: run_pip_audit(repo_path, sandbox),
        lambda: run_eslint(repo_path, sandbox),
        lambda: run_npm_audit(repo_path, sandbox),
        lambda: run_trivy(repo_path, sandbox),
        lambda: run_osv_scanner(repo_path, sandbox),
    ]
    runs: list[SARIFRun] = []
    for runner in runners:
        try:
            runs.append(runner())
        except SystemExit:
            raise  # propagate hard failures; skip logging handled inside each runner
    return runs
