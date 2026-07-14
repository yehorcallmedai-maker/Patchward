# KS-TRACE: AC-01, AC-02, AC-05, AC-06, AC-P6-01, AC-P6-02, AC-P6-05
# assumption: patchward.toml in cwd | test: test_config.py,
# test_async_pipeline.py
from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional

import typer

from patchward.config import load_config, validate_github_config
from patchward.pipeline import run_batch
from patchward.pr_publisher import PRPublisher
from patchward.credential_proxy import CredentialProxy
from patchward.db import (
    open_db,
    get_or_create_repo,
    create_run,
    finish_run,
    insert_finding,
)
from patchward.fix_gen import FixGenSubagent
from patchward.fix_worktree import fix_worktree_context
from patchward.run_log import RunLog
from patchward.scanner import run_all_scanners
from patchward.subagent import ScannerSubagent
from patchward.verifier import Verifier
from patchward.worktree import require_git_version, worktree_context
from patchward.worktree_common import sanitize_branch_component
from patchward import tracing

app = typer.Typer(
    name="patchward",
    help="Local-first multi-repo security agent.",
    add_completion=False,
    no_args_is_help=True,
)

_VERSION = "0.1.0"


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"patchward {_VERSION}")
        raise typer.Exit()


@app.callback()
def _main(
    version: Optional[bool] = typer.Option(  # noqa: UP007
        None,
        "--version",
        "-V",
        help="Print version and exit.",
        callback=_version_callback,
        is_eager=True,
    ),
) -> None:
    pass


@app.command()
def version() -> None:
    """Print patchward version and exit."""
    from patchward import __version__
    typer.echo(f"patchward {__version__}")


@app.command()
def scan(
    repo: Optional[Path] = typer.Option(
        None, "--repo", help="Path to repository to scan"
    ),
    config: Optional[Path] = typer.Option(
        None, "--config", help="Path to patchward.toml"
    ),
) -> None:
    """Scan a repository for security vulnerabilities using Semgrep."""

    cfg = load_config(config)
    repo_path = repo or cfg.repo_path

    # AC-P2-05: Load credentials outside the sandbox boundary.
    # Credentials reach the Anthropic SDK client directly — never
    # forwarded to any Docker container.
    # assert_credentials_excluded() is the hard block before any
    # sandbox operation.
    # KS-TRACE: C-P2-04, AC-P2-05
    proxy = CredentialProxy().load()
    proxy.assert_credentials_excluded(proxy.get_container_env())

    # Phase 2: git 2.5+ required for worktree isolation (C-P2-05)
    require_git_version()

    tracing.setup_tracing(cfg.langfuse_host, cfg.tracing_enabled)

    with tracing.span(
        "patchward.scan", repo=str(repo_path), rules=cfg.semgrep_rules
    ):
        conn = open_db(cfg.db_path)
        repo_id = get_or_create_repo(conn, str(repo_path))
        run_id = create_run(
            conn, repo_id, scanner="all", semgrep_rules=cfg.semgrep_rules
        )

        typer.echo(
            f"[patchward] Scanning {repo_path} "
            f"with rules: {cfg.semgrep_rules}"
        )

        try:
            # Phase 2: all scanners run on worktree path — C-P2-05,
            # C-P2-08
            # KS-TRACE: C-P2-05, C-P2-08, AC-P2-06
            with worktree_context(repo_path) as scan_path:
                with tracing.span(
                    "patchward.scan_all", repo=str(scan_path)
                ):
                    sarif_runs = run_all_scanners(
                        scan_path, cfg.semgrep_rules
                    )
            # Worktree cleaned up here — outside scanner span

            findings = [f for run in sarif_runs for f in run.to_findings()]

            with tracing.span(
                "patchward.store_findings", count=len(findings)
            ):
                for f in findings:
                    insert_finding(
                        conn,
                        run_id=run_id,
                        rule_id=f["rule_id"],
                        file_path=f["file_path"],
                        line_start=f["line_start"],
                        line_end=f["line_end"],
                        severity=f["severity"],
                        message=proxy.scrub(f["message"]),
                        fingerprint=f["fingerprint"],
                    )

            finish_run(conn, run_id, status="success")
            typer.echo(
                f"[patchward] Scan complete. Findings: {len(findings)}"
            )

            for f in findings:
                typer.echo(
                    f"  [{f['severity'].upper()}] {f['rule_id']} "
                    f"@ {f['file_path']}:{f['line_start']}"
                )

            # KS-P1-06: Scanner subagent triage (Model B — receives
            # SARIF, never raw stdout)
            # KS-TRACE: AC-P1-05, C-03, C-04, C-09
            if cfg.anthropic_api_key and findings:
                try:
                    with tracing.span(
                        "patchward.subagent.triage", repo=str(repo_path)
                    ):
                        agent = ScannerSubagent(
                            api_key=cfg.anthropic_api_key
                        )
                        triage = agent.triage(
                            sarif_runs, repo_path=repo_path
                        )
                    typer.echo(
                        f"\n[patchward] Triage summary: {triage.summary}"
                    )
                    for tf in triage.findings:
                        typer.echo(
                            f"  [{tf.priority.upper()}] "
                            f"{tf.rule_id} — {tf.rationale}"
                        )
                except Exception as exc:
                    typer.echo(
                        f"[patchward] Triage skipped "
                        f"(subagent error): {exc}",
                        err=True,
                    )

        except SystemExit:
            finish_run(conn, run_id, status="error", error="scanner failed")
            raise
        except Exception as exc:
            finish_run(conn, run_id, status="error", error=str(exc))
            typer.echo(
                f"[patchward] ERROR: unexpected failure: {exc}", err=True
            )
            raise typer.Exit(code=1)
        finally:
            conn.close()
            tracing.flush()


@app.command()
def fix(
    repo: Optional[Path] = typer.Option(
        None, "--repo", help="Path to repository to scan and fix"
    ),
    config: Optional[Path] = typer.Option(
        None, "--config", help="Path to patchward.toml"
    ),
    log: Optional[Path] = typer.Option(
        None,
        "--log",
        help="Path for the NDJSON run log "
        "(default: runs/session_<ts>.json)",
    ),
    model: Optional[str] = typer.Option(
        None,
        "--model",
        help=(
            "Override the fix-gen model for this run "
            "(e.g. claude-sonnet-4-6). "
            "Takes precedence over [models].fix_model in patchward.toml. "
            "Severity 'error' always uses Opus regardless. "
            "(AC-P6-05, C-P6-05)"
        ),
    ),
) -> None:
    """Scan a repository, generate fixes with Fix-Gen, and verify.

    Requires ANTHROPIC_API_KEY in the environment or .env file.

    For each finding:
      1. Fix-Gen subagent attempts a patch on an isolated git
         worktree branch.
      2. Verifier evaluates the patch against three deterministic
         gates.
      3. Result (verified | failed) is written to the run log
         (NDJSON).
      4. Branch persists only when verification_status == "verified".

    KS-TRACE: C-P4-06, C-P4-07, AC-P4-10, AC-P6-05
    """
    cfg = load_config(config)
    repo_path = repo or cfg.repo_path

    # --model CLI flag overrides [models].fix_model (AC-P6-05)
    if model is not None:
        cfg.models.fix_model = model

    if not cfg.anthropic_api_key:
        typer.echo(
            "[patchward] ERROR: ANTHROPIC_API_KEY is required for "
            "the fix command.",
            err=True,
        )
        raise typer.Exit(code=1)

    # C-P5-10, AC-P5-13: abort early if [github] section is missing
    # or incomplete so the user gets a clear error before any LLM/API
    # calls are made.
    validate_github_config(cfg)

    proxy = CredentialProxy().load()
    proxy.assert_credentials_excluded(proxy.get_container_env())

    require_git_version()

    tracing.setup_tracing(cfg.langfuse_host, cfg.tracing_enabled)

    run_log = RunLog(path=log)

    with tracing.span(
        "patchward.fix", repo=str(repo_path), rules=cfg.semgrep_rules
    ):
        conn = open_db(cfg.db_path)
        repo_id = get_or_create_repo(conn, str(repo_path))
        run_id = create_run(
            conn, repo_id, scanner="all", semgrep_rules=cfg.semgrep_rules
        )

        typer.echo(
            f"[patchward] Scanning {repo_path} "
            f"with rules: {cfg.semgrep_rules}"
        )

        try:
            with worktree_context(repo_path) as scan_path:
                with tracing.span(
                    "patchward.fix.scan_all", repo=str(scan_path)
                ):
                    sarif_runs = run_all_scanners(
                        scan_path, cfg.semgrep_rules
                    )

            findings = [f for run in sarif_runs for f in run.to_findings()]

            with tracing.span(
                "patchward.fix.store_findings", count=len(findings)
            ):
                for f in findings:
                    insert_finding(
                        conn,
                        run_id=run_id,
                        rule_id=f["rule_id"],
                        file_path=f["file_path"],
                        line_start=f["line_start"],
                        line_end=f["line_end"],
                        severity=f["severity"],
                        message=proxy.scrub(f["message"]),
                        fingerprint=f["fingerprint"],
                    )

            finish_run(conn, run_id, status="success")
            typer.echo(
                f"[patchward] Scan complete. Findings: {len(findings)}"
            )

            if not findings:
                typer.echo("[patchward] No findings — nothing to fix.")
                return

            # Pre-filter: skip findings in test directories/files.
            # Fix-Gen must never modify test files — pytest assert is
            # intentional, and automated patches to test code produce
            # bad PRs.  Filter before Fix-Gen is invoked (not after).
            def _is_test_path(fp: str) -> bool:
                parts = fp.replace("\\", "/").split("/")
                filename = parts[-1] if parts else ""
                return (
                    "tests" in parts
                    or filename.startswith("test_")
                    or filename.endswith("_test.py")
                )

            actionable = [f for f in findings if not _is_test_path(f["file_path"])]
            skipped_count = len(findings) - len(actionable)
            if skipped_count:
                typer.echo(
                    f"[patchward] Skipping {skipped_count} finding(s) in "
                    f"test files (Fix-Gen does not modify test code)."
                )
            findings = actionable

            if not findings:
                typer.echo(
                    "[patchward] No actionable findings after filtering."
                )
                return

            # Fix-Gen + Verifier loop
            # KS-TRACE: C-P4-06, C-P4-07, AC-P4-10
            fix_agent = FixGenSubagent(
                api_key=cfg.anthropic_api_key,
                config=cfg,
            )
            verifier = Verifier(
                timeout_seconds=cfg.verifier.timeout_seconds
            )

            verified_count = 0
            failed_count = 0

            for finding in findings:
                import uuid as _uuid
                _base_id = finding["fingerprint"] or finding["rule_id"]
                # BACKLOG 3d: _base_id comes straight from scanner
                # output (semgrep SARIF fingerprint/rule_id) and is not
                # guaranteed to be a valid git ref component — sanitize
                # before it becomes part of the branch name.
                finding_id = (
                    f"{sanitize_branch_component(_base_id)}"
                    f"-{_uuid.uuid4().hex[:6]}"
                )
                rule_id = finding["rule_id"]
                file_path = finding["file_path"]

                # Translate scan-worktree absolute path → repo-relative path.
                # Scan runs in a temp dir (patchward-scan-{uuid}); fix and verifier
                # need the relative path from the repo root (e.g. "checkdmarc/spf.py").
                _fp = Path(file_path)
                rel_file_path = file_path
                if _fp.is_absolute():
                    for _i, _part in enumerate(_fp.parts):
                        if _part.startswith("patchward-scan-") or _part.startswith("patchward-fix-"):
                            _rel_parts = _fp.parts[_i + 1:]
                            if _rel_parts:
                                # Use forward slashes — required for git show HEAD:<path>
                                rel_file_path = "/".join(_rel_parts)
                            break

                typer.echo(
                    f"\n[patchward] Fixing "
                    f"[{finding['severity'].upper()}] "
                    f"{rule_id} @ {file_path}:{finding['line_start']}"
                )

                try:
                    with tracing.span(
                        "patchward.fix.apply",
                        rule_id=rule_id,
                        file_path=file_path,
                    ):
                        with fix_worktree_context(
                            repo_path, finding_id
                        ) as handle:
                            fix_result = asyncio.run(
                                fix_agent.apply_fix(
                                    finding,
                                    handle.worktree_path,
                                    finding_id=finding_id,
                                    branch_name=handle.branch,
                                )
                            )

                            if not fix_result.success:
                                typer.echo(
                                    f"  [SKIP] Fix-Gen did not produce"
                                    f" a fix: {fix_result.error}"
                                )
                                run_log.append({
                                    "finding_id": finding_id,
                                    "file_path": file_path,
                                    "rule_id": rule_id,
                                    "severity": finding["severity"],
                                    "model_used": fix_result.model,
                                    "branch_name": (
                                        fix_result.branch_name
                                    ),
                                    "success": False,
                                    "verifier": None,
                                })
                                failed_count += 1
                                continue

                            # C-P4-06: Verifier receives branch name
                            # + finding coords only
                            # C-P4-07: result written to log before
                            # branch returned to caller
                            with tracing.span(
                                "patchward.fix.verify",
                                rule_id=rule_id,
                                branch=handle.branch,
                            ):
                                verify_result = verifier.verify(
                                    worktree_path=handle.worktree_path,
                                    repo_path=repo_path,
                                    file_path=rel_file_path,
                                    rule_id=rule_id,
                                    line_start=finding["line_start"],
                                    line_end=finding["line_end"],
                                )

                            # AC-P4-10: run log entry contains all
                            # five verifier fields
                            run_log.append({
                                "finding_id": finding_id,
                                "file_path": file_path,
                                "rule_id": rule_id,
                                "severity": finding["severity"],
                                "model_used": fix_result.model,
                                "branch_name": fix_result.branch_name,
                                "success": fix_result.success,
                                "verifier": verify_result.as_log_dict(),
                            })

                            status = verify_result.verification_status
                            fp = verify_result.false_positive_candidate
                            typer.echo(
                                f"  [Verifier] {status.upper()}"
                            )
                            typer.echo(
                                f"    gate_1="
                                f"{verify_result.gate_1.status} "
                                f"gate_2={verify_result.gate_2.status}"
                                f" gate_3={verify_result.gate_3.status}"
                            )
                            if fp:
                                typer.echo(
                                    "    [!] false_positive_candidate"
                                    "=true"
                                )

                            if status == "verified":
                                # C-P3-12: branch persists only on
                                # verified fix
                                handle.mark_success()
                                verified_count += 1
                                typer.echo(
                                    f"  [OK] Branch persisted: "
                                    f"{fix_result.branch_name}"
                                )
                                # AC-P5-10: push branch + open PR
                                # KS-TRACE: C-P5-01, C-P5-08,
                                #           ADR-018, ADR-019
                                try:
                                    publisher = PRPublisher(
                                        config=cfg,
                                        credential_proxy=(
                                            CredentialProxy().load()
                                        ),
                                        http_client=None,
                                    )
                                    pr_dict = publisher.publish(
                                        fix_result=fix_result,
                                        verifier_result=verify_result,
                                        finding=finding,
                                        run_log=run_log,
                                    )
                                    # BACKLOG 3c: pr_dict['status'] can be
                                    # "opened", "already_open" (idempotent —
                                    # see pr_publisher._create_pr), or
                                    # "api_error" (403/422/unexpected — url
                                    # is blank). Previously this printed
                                    # "[PR] Opened: " unconditionally, so a
                                    # 403 looked identical to success with a
                                    # blank URL. Confirmed in the 2026-07-13
                                    # Stage-1 E2E test.
                                    pr_status = pr_dict.get("status", "")
                                    if pr_status == "opened":
                                        typer.echo(
                                            f"  [PR] Opened: "
                                            f"{pr_dict['url']}"
                                        )
                                    elif pr_status == "already_open":
                                        typer.echo(
                                            f"  [PR] Already open: "
                                            f"{pr_dict['url']}"
                                        )
                                    else:
                                        typer.echo(
                                            f"  [PR] Failed to open "
                                            f"(status={pr_status!r})",
                                            err=True,
                                        )
                                except Exception as pr_exc:
                                    typer.echo(
                                        f"  [PR] Publish failed: "
                                        f"{pr_exc}",
                                        err=True,
                                    )
                            else:
                                # Worktree discarded at context exit
                                failed_count += 1

                except Exception as exc:
                    typer.echo(
                        f"  [ERROR] Fix/Verify failed for "
                        f"{rule_id}: {exc}",
                        err=True,
                    )
                    failed_count += 1

            typer.echo(
                f"\n[patchward] Fix complete. "
                f"verified={verified_count} "
                f"failed/skipped={failed_count} "
                f"log={run_log.path}"
            )

        except SystemExit:
            finish_run(
                conn, run_id, status="error", error="scanner failed"
            )
            raise
        except Exception as exc:
            finish_run(conn, run_id, status="error", error=str(exc))
            typer.echo(
                f"[patchward] ERROR: unexpected failure: {exc}", err=True
            )
            raise typer.Exit(code=1)
        finally:
            conn.close()
            tracing.flush()


@app.command()
def batch(
    config: Optional[Path] = typer.Option(
        None, "--config", help="Path to patchward.toml"
    ),
    log: Optional[Path] = typer.Option(
        None,
        "--log",
        help="Path for the NDJSON run log "
        "(default: runs/session_<ts>.json)",
    ),
    model: Optional[str] = typer.Option(
        None,
        "--model",
        help=(
            "Override the fix-gen model for this batch run "
            "(e.g. claude-sonnet-4-6). "
            "Takes precedence over [models].fix_model in patchward.toml. "
            "Severity 'error' always uses Opus regardless. "
            "(AC-P6-05, C-P6-05)"
        ),
    ),
) -> None:
    """Process all [[repos]] entries concurrently (Phase 6).

    Reads ``[[repos]]`` from ``patchward.toml``, processes each
    concurrently bounded by ``[batch].max_concurrent``, and prints
    a summary table.  Exits 0 if all repos succeeded, 1 if any
    failed.

    Requires ANTHROPIC_API_KEY and GITHUB_TOKEN in the environment
    or .env file.

    # KS-TRACE: AC-P6-01, AC-P6-02, AC-P6-05, AC-P6-09,
    #           C-P6-01, C-P6-02, C-P6-09, ADR-020
    """

    cfg = load_config(config)

    # --model CLI flag overrides [models].fix_model (AC-P6-05)
    if model is not None:
        cfg.models.fix_model = model

    if not cfg.anthropic_api_key:
        typer.echo(
            "[patchward] ERROR: ANTHROPIC_API_KEY is required for "
            "the batch command.",
            err=True,
        )
        raise typer.Exit(code=1)

    proxy = CredentialProxy().load()
    github_token: str = proxy._creds.get(  # noqa: SLF001
        "GITHUB_TOKEN", ""
    )
    if not github_token:
        typer.echo(
            "[patchward] ERROR: GITHUB_TOKEN is required for "
            "the batch command.",
            err=True,
        )
        raise typer.Exit(code=1)

    if not cfg.repos:
        typer.echo(
            "[patchward] ERROR: No [[repos]] entries found in "
            "patchward.toml. Add at least one [[repos]] entry or "
            "set [github] owner and repo for single-repo fallback.",
            err=True,
        )
        raise typer.Exit(code=1)

    typer.echo(
        f"[patchward] Starting batch run: "
        f"{len(cfg.repos)} repo(s), "
        f"max_concurrent={cfg.batch.max_concurrent}"
    )

    run_log = RunLog(path=log)

    results = asyncio.run(
        run_batch(
            cfg, cfg.anthropic_api_key, github_token,
            run_log=run_log,
        )
    )

    # Per-repo run log records (AC-P6-09, C-P6-09)
    for r in results:
        run_log.append_batch_result(r)

    # Summary table
    typer.echo(
        "\n{:<30} {:<8} {:<50} {}".format(
            "REPO", "STATUS", "PR_URL", "ERROR"
        )
    )
    typer.echo("-" * 100)
    any_failed = False
    for r in results:
        status = r.get("status", "error")
        if status != "ok":
            any_failed = True
        typer.echo(
            "{:<30} {:<8} {:<50} {}".format(
                r.get("repo", "?"),
                status,
                r.get("pr_url") or "-",
                r.get("error") or "-",
            )
        )

    typer.echo(f"[patchward] Batch log: {run_log.path}")
    raise typer.Exit(code=1 if any_failed else 0)
