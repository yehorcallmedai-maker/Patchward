# KS-TRACE: AC-P6-01, AC-P6-02, AC-P6-03, AC-P6-04, C-P6-01,
#           C-P6-02, C-P6-03, ADR-020, ADR-021, AD-P6-03,
#           AC-P7-01, AC-P7-02, AC-P7-04, AC-P7-05, C-P7-01,
#           C-P7-02, C-P7-04, AD-P7-01, AD-P7-02, AD-P7-03
# assumption: asyncio.to_thread correctly yields the event loop
# during synchronous fix_gen/verifier/scanner calls;
# fix_worktree_context is a sync context manager compatible with
# async wrappers inside the with block
# test: test_async_pipeline.py, test_orchestrator.py
from __future__ import annotations

import asyncio
import logging
import uuid
from pathlib import Path
from typing import TYPE_CHECKING

import anthropic
import typer

from patchward.credential_proxy import CredentialProxy
from patchward.fix_gen import FixGenSubagent
from patchward.fix_worktree import fix_worktree_context
from patchward.pr_publisher import PRPublisher
from patchward.run_log import RunLog
from patchward.scanner import run_all_scanners
from patchward.verifier import Verifier

if TYPE_CHECKING:
    from patchward.config import RepomendConfig, RepoConfig

logger = logging.getLogger(__name__)


async def _with_retry(
    coro_fn,
    max_retries: int = 3,
    base_delay: float = 1.0,
):
    """
    Retry coro_fn() on RateLimitError with exponential backoff.

    coro_fn must be a zero-arg callable that returns a fresh
    coroutine on each call (use a lambda — never reuse the same
    coroutine object across attempts).

    Delays: base_delay * 2^attempt (1 s, 2 s, 4 s by default).
    Raises RateLimitError if all retries are exhausted.

    # KS-TRACE: AD-P6-03
    """
    for attempt in range(max_retries + 1):
        try:
            return await coro_fn()
        except anthropic.RateLimitError:
            if attempt == max_retries:
                raise
            delay = base_delay * (2 ** attempt)
            await asyncio.sleep(delay)


async def run_repo_pipeline(
    repo: "RepoConfig",
    cfg: "RepomendConfig",
    semaphore: asyncio.Semaphore,
    api_key: str,
    github_token: str,
    run_log: RunLog | None = None,
) -> dict:
    """
    Run the full scan→fix→verify→PR pipeline for one repo.

    Acquires ``semaphore`` on entry and releases it on all exit
    paths via ``async with`` — including unhandled exceptions.
    Returns a result dict on both success and failure so that
    ``run_batch`` always receives a uniform list.

    Result schema::

        {
            "repo":               "<owner>/<repo>",
            "status":             "<last-finding-status>",
            "pr_url":             "<url>" | None,
            "error":              None | "<message>",
            "findings_attempted": int,
        }

    All subprocess calls (scanner, verifier, git push) are wrapped
    in ``asyncio.to_thread()`` so they never block the event loop.
    (C-P6-03, AC-P6-03)

    When ``run_log`` is provided, one record is appended per
    finding regardless of outcome. (C-P7-04, AC-P7-05)

    ``cfg.batch.max_findings_per_repo`` caps the number of findings
    Fix-Gen will attempt. Cap is enforced before Fix-Gen is called.
    (C-P7-02, AC-P7-04)

    A single FixGenSubagent (and its AsyncAnthropic client) is
    constructed once per repo pipeline invocation and reused across
    all findings for that repo. (AD-P7-03)

    # KS-TRACE: AC-P6-01, AC-P6-02, C-P6-01, C-P6-02, C-P6-03,
    #           ADR-020, AC-P7-01, AC-P7-02, AC-P7-04, AC-P7-05,
    #           C-P7-01, C-P7-02, C-P7-04, AD-P7-03
    """
    repo_label = f"{repo.owner}/{repo.repo}"
    result: dict = {
        "repo": repo_label,
        "status": "error",
        "pr_url": None,
        "error": None,
        "findings_attempted": 0,
    }

    async with semaphore:
        try:
            repo_path = Path(repo.path)
            logger.debug("[pipeline] starting %s", repo_label)

            # ----------------------------------------------------------
            # Step 1: Scan — subprocess via asyncio.to_thread
            # (C-P6-03: no blocking calls on the event loop)
            # ----------------------------------------------------------
            sarif_runs = await asyncio.to_thread(
                run_all_scanners,
                repo_path,
                cfg.semgrep_rules,
            )
            findings: list[dict] = []
            for sarif_run in sarif_runs:
                findings.extend(sarif_run.to_findings())

            if not findings:
                result["status"] = "no_findings"
                return result

            # Single client per repo — AD-P7-03, C-P7-03.
            # Construct ONCE before the loop; reuse across findings.
            agent = FixGenSubagent(
                api_key=api_key,
                config=cfg,
            )
            verifier = Verifier(
                timeout_seconds=cfg.verifier.timeout_seconds
            )

            # ----------------------------------------------------------
            # Per-finding loop (C-P7-01, C-P7-02, AC-P7-01).
            # Cap enforced BEFORE Fix-Gen is called (C-P7-02).
            # One finding failure does not abort the loop (C-P7-01).
            # ----------------------------------------------------------
            max_findings = cfg.batch.max_findings_per_repo
            findings_attempted = 0

            for finding in findings:
                # C-P7-02: enforce cap before Fix-Gen
                if findings_attempted >= max_findings:
                    break
                findings_attempted += 1

                # uuid suffix prevents branch-name collision across
                # findings in the same repo (assumption §KS-P7-04)
                finding_id = (
                    f"{repo.repo}"
                    f"-{finding['rule_id'][:20]}"
                    f"-{uuid.uuid4().hex[:6]}"
                )
                finding_pr_url: str | None = None
                finding_status = "error"

                try:
                    # Step 2: Fix-Gen — async LLM (C-P7-03)
                    with fix_worktree_context(
                        repo_path, finding_id
                    ) as handle:
                        fix_result = await _with_retry(
                            lambda: agent.apply_fix(
                                finding,
                                handle.worktree_path,
                                finding_id=finding_id,
                                branch_name=handle.branch,
                            )
                        )

                        if not fix_result.success:
                            finding_status = "fix_failed"
                            result["error"] = fix_result.error
                        else:
                            # Step 3: Verify
                            verify_result = (
                                await asyncio.to_thread(
                                    verifier.verify,
                                    worktree_path=(
                                        handle.worktree_path
                                    ),
                                    repo_path=repo_path,
                                    file_path=finding["file_path"],
                                    rule_id=finding["rule_id"],
                                    line_start=finding["line_start"],
                                    line_end=finding["line_end"],
                                )
                            )

                            if (
                                verify_result.verification_status
                                != "verified"
                            ):
                                finding_status = "verify_failed"
                                result["error"] = (
                                    "gate_2: "
                                    f"{verify_result.gate_2.reason}"
                                )
                            else:
                                handle.mark_success()

                                # Step 4: PR Publisher
                                proxy = CredentialProxy().load()
                                publisher = PRPublisher(
                                    config=cfg,
                                    credential_proxy=proxy,
                                    http_client=None,
                                )
                                pr_dict = await asyncio.to_thread(
                                    publisher.publish,
                                    fix_result=fix_result,
                                    verifier_result=verify_result,
                                    finding=finding,
                                    run_log=None,
                                    worktree_path=(
                                        handle.worktree_path
                                    ),
                                )
                                finding_pr_url = pr_dict.get("url")
                                finding_status = "pr_opened"
                                logger.info(
                                    "[pipeline] %s → PR: %s",
                                    repo_label,
                                    finding_pr_url,
                                )

                except anthropic.RateLimitError as exc:
                    finding_status = "rate_limited"
                    result["error"] = str(exc)
                    logger.warning(
                        "[pipeline] rate-limited %s: %s",
                        repo_label,
                        exc,
                    )

                except Exception as exc:  # noqa: BLE001
                    err_str = str(exc) or repr(exc)
                    finding_status = "error"
                    result["error"] = err_str
                    logger.error(
                        "[pipeline] error for %s: %s",
                        repo_label,
                        err_str,
                    )

                finally:
                    if run_log is not None:
                        run_log.append_batch_result({
                            "repo": repo_label,
                            "finding_id": finding_id,
                            "rule_id": finding.get(
                                "rule_id", ""
                            ),
                            "file_path": finding.get(
                                "file_path", ""
                            ),
                            "severity": finding.get(
                                "severity", ""
                            ),
                            "status": finding_status,
                            "pr_url": finding_pr_url,
                        })

                result["status"] = finding_status
                result["pr_url"] = finding_pr_url

            result["findings_attempted"] = findings_attempted
            return result

        except typer.Exit as exc:
            err_str = repr(exc)
            logger.error(
                "[pipeline] scanner tool missing for %s: %s",
                repo_label,
                err_str,
            )
            result["status"] = "scanner_unavailable"
            result["error"] = err_str
            return result

        except Exception as exc:  # noqa: BLE001
            err_str = str(exc) or repr(exc)
            logger.error(
                "[pipeline] unhandled error for %s: %s",
                repo_label,
                err_str,
            )
            result["error"] = err_str
            return result


async def run_batch(
    cfg: "RepomendConfig",
    api_key: str,
    github_token: str,
    run_log: RunLog | None = None,
) -> list[dict]:
    """
    Process all ``cfg.repos`` concurrently, bounded by
    ``asyncio.Semaphore(cfg.batch.max_concurrent)``.

    Returns a list of result dicts — one per repo — in the same
    order as ``cfg.repos``.  Uses ``return_exceptions=True`` as
    defense-in-depth; escaped exceptions are converted to error
    dicts rather than propagating to the caller.

    # KS-TRACE: AC-P6-01, AC-P6-02, C-P6-02, ADR-020
    """
    semaphore = asyncio.Semaphore(cfg.batch.max_concurrent)
    tasks = [
        run_repo_pipeline(
            repo, cfg, semaphore, api_key, github_token,
            run_log=run_log,
        )
        for repo in cfg.repos
    ]
    raw = await asyncio.gather(*tasks, return_exceptions=True)

    results: list[dict] = []
    for repo, item in zip(cfg.repos, raw):
        if isinstance(item, dict):
            results.append(item)
        else:
            results.append({
                "repo": f"{repo.owner}/{repo.repo}",
                "status": "error",
                "pr_url": None,
                "error": str(item),
            })
    return results
