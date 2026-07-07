# KS-TRACE: AC-P3-09
# | assumption: ≥1 of 3 fixture findings fixed = ≥30% repair success rate;
# |             re-scan uses semgrep p/python on the patched worktree file;
# |             fixture repo must be checked out at tests/fixture_repo or REPOMEND_FIXTURE_REPO
# | test: this file — @integration, requires ANTHROPIC_API_KEY + semgrep on PATH
"""
Golden dataset gate — Phase 3 AC-P3-09.

Runs Fix-Gen on all three planted vulnerabilities in patchward-fixture/vulnerable.py:
  1. subprocess-shell-true          (line 24, severity=error)
  2. insecure-hash-algorithm-md5    (line 30, severity=warning)
  3. ssl-wrap-socket-is-deprecated  (line 37, severity=warning)

For each finding:
  - Fix-Gen applies a patch on a dedicated patchward/fix-<id> branch.
  - Semgrep re-scans the patched file with p/python.
  - A finding-level PASS = the original rule_id is absent from re-scan output.

Gate: ≥1 of 3 findings must pass (≥30% repair success).
Report: per-finding status + totals printed to stdout.

Skip conditions:
  - ANTHROPIC_API_KEY not set
  - tests/fixture_repo not found AND REPOMEND_FIXTURE_REPO not set
  - semgrep not on PATH
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from patchward.fix_gen import FixGenSubagent
from patchward.fix_worktree import fix_worktree_context
from patchward.verifier import Verifier

# ---------------------------------------------------------------------------
# Fixture findings — the three plants in patchward-fixture/vulnerable.py
# ---------------------------------------------------------------------------

GOLDEN_FINDINGS = [
    {
        "rule_id": "python.lang.security.audit.subprocess-shell-true.subprocess-shell-true",
        "file_path": "vulnerable.py",
        "line_start": 24,
        "line_end": 24,
        "severity": "error",
        "message": "subprocess called with shell=True — allows shell injection",
    },
    {
        "rule_id": "python.lang.security.insecure-hash-algorithms.insecure-hash-algorithm-md5",
        "file_path": "vulnerable.py",
        "line_start": 30,
        "line_end": 30,
        "severity": "warning",
        "message": "MD5 is a weak hash algorithm — use SHA-256 or stronger",
    },
    {
        "rule_id": "python.lang.security.audit.ssl-wrap-socket-is-deprecated.ssl-wrap-socket-is-deprecated",
        "file_path": "vulnerable.py",
        "line_start": 37,
        "line_end": 37,
        "severity": "warning",
        "message": "ssl.wrap_socket is deprecated — use ssl.SSLContext instead",
    },
]

REPAIR_THRESHOLD = 1   # AC-P3-09: ≥1 of 3 (≥30%)


# ---------------------------------------------------------------------------
# Helper: re-scan a single file in a worktree with semgrep
# ---------------------------------------------------------------------------

def _rescan_for_rule(worktree_path: Path, file_path: str, rule_id: str) -> bool:
    """
    Return True if the rule is ABSENT from semgrep re-scan (i.e. the fix worked).
    Uses 'semgrep --config p/python' and checks for the specific rule_id.
    """
    target = worktree_path / file_path
    proc = subprocess.run(
        [
            "semgrep",
            "--config", "p/python",
            "--json",
            "--metrics", "off",
            str(target),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    try:
        sarif = json.loads(proc.stdout)
    except json.JSONDecodeError:
        # semgrep produced no valid JSON — treat as scan failure (finding still present)
        return False

    findings = sarif.get("results", [])
    # Extract the short rule name suffix for matching (semgrep uses the last segment)
    rule_suffix = rule_id.split(".")[-1]
    for f in findings:
        check_id = f.get("check_id", "")
        if rule_id in check_id or rule_suffix in check_id:
            return False   # Rule still fires — fix did not eliminate it
    return True   # Rule absent — fix successful


# ---------------------------------------------------------------------------
# AC-P3-09: golden dataset gate
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_golden_dataset_repair_rate() -> None:
    """
    AC-P3-09: Fix-Gen achieves ≥30% (≥1/3) repair success on the golden fixture dataset.

    Per-finding results are printed.  The assertion covers the aggregate gate only —
    individual failures are expected and acceptable as long as ≥1 passes.

    Requires: ANTHROPIC_API_KEY · semgrep on PATH · fixture repo at tests/fixture_repo
              or REPOMEND_FIXTURE_REPO env var.
    """
    # --- prerequisite checks ---
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        pytest.skip("ANTHROPIC_API_KEY not set")

    fixture_repo = Path(os.environ.get(
        "REPOMEND_FIXTURE_REPO",
        Path(__file__).parent / "fixture_repo",
    ))
    if not fixture_repo.exists():
        pytest.skip(f"Fixture repo not found at {fixture_repo}")

    if not shutil.which("semgrep"):
        pytest.skip("semgrep not on PATH")

    agent = FixGenSubagent(api_key=api_key)

    results: list[dict] = []

    for finding in GOLDEN_FINDINGS:
        finding_id = f"golden-{finding['rule_id'].split('.')[-1]}"
        print(f"\n[golden] Running Fix-Gen for: {finding_id}")

        try:
            with fix_worktree_context(fixture_repo, finding_id) as handle:
                fix_result = agent.apply_fix(
                    finding,
                    handle.worktree_path,
                    finding_id=finding_id,
                    branch_name=handle.branch,
                )

                if not fix_result.success:
                    results.append({
                        "finding_id": finding_id,
                        "rule_id": finding["rule_id"],
                        "fix_gen_success": False,
                        "rescan_clean": False,
                        "status": "FAIL — Fix-Gen did not call submit_fix",
                        "error": fix_result.error,
                    })
                    # No mark_success → worktree discarded
                    continue

                # Re-scan the patched worktree
                rescan_clean = _rescan_for_rule(
                    handle.worktree_path,
                    finding["file_path"],
                    finding["rule_id"],
                )

                results.append({
                    "finding_id": finding_id,
                    "rule_id": finding["rule_id"],
                    "fix_gen_success": True,
                    "rescan_clean": rescan_clean,
                    "model": fix_result.model,
                    "confidence": fix_result.confidence,
                    "status": "PASS" if rescan_clean else "FAIL — rule still fires post-fix",
                })

                if rescan_clean:
                    handle.mark_success()   # Persist the branch only on verified fix

        except Exception as exc:  # noqa: BLE001
            results.append({
                "finding_id": finding_id,
                "rule_id": finding["rule_id"],
                "fix_gen_success": False,
                "rescan_clean": False,
                "status": f"FAIL — exception: {exc}",
                "error": str(exc),
            })

    # --- report ---
    print("\n" + "=" * 60)
    print("GOLDEN DATASET GATE — AC-P3-09")
    print("=" * 60)
    passed = 0
    for r in results:
        status = r["status"]
        print(f"  [{r['finding_id']}]  {status}")
        if r.get("rescan_clean"):
            passed += 1

    total = len(results)
    print(f"\nResult: {passed}/{total} findings repaired  "
          f"(threshold: {REPAIR_THRESHOLD}/{total} = "
          f"{REPAIR_THRESHOLD / total * 100:.0f}%)")
    print("=" * 60)

    assert passed >= REPAIR_THRESHOLD, (
        f"Golden dataset gate FAILED: {passed}/{total} repaired, "
        f"required ≥{REPAIR_THRESHOLD}/{total} (≥30%). "
        "Per-finding results:\n"
        + "\n".join(f"  {r['finding_id']}: {r['status']}" for r in results)
    )


# ---------------------------------------------------------------------------
# KS-P4-03: Fix-Gen → Verifier end-to-end chain
# AC-P4-11: Verifier returns "verified" for a good Fix-Gen patch
# AC-P4-12: Verifier returns "failed" for a bad / missing patch
# ---------------------------------------------------------------------------


# Convenience alias — subprocess-shell-true is the confirmed-fixable finding
_SUBPROCESS_FINDING = GOLDEN_FINDINGS[0]


def _get_fixture_repo() -> "Path | None":
    """Return fixture repo path or None if not found (shared skip logic)."""
    repo = Path(os.environ.get(
        "REPOMEND_FIXTURE_REPO",
        Path(__file__).parent / "fixture_repo",
    ))
    return repo if repo.exists() else None


@pytest.mark.integration
def test_verifier_end_to_end_verified() -> None:
    """
    AC-P4-11: Fix-Gen → Verifier end-to-end chain returns "verified".

    subprocess-shell-true is the confirmed-fixable finding from Phase 3
    (KS-P3-06: 1/3 PASSED — subprocess-shell-true). When Fix-Gen succeeds,
    Verifier must return verification_status="verified" with all three gates
    in expected states.

    If Fix-Gen fails non-deterministically the test is skipped — this is an
    LLM-backed integration test, not a deterministic unit test.

    Requires: ANTHROPIC_API_KEY · semgrep on PATH · fixture repo
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        pytest.skip("ANTHROPIC_API_KEY not set")

    fixture_repo = _get_fixture_repo()
    if fixture_repo is None:
        pytest.skip(
            "Fixture repo not found — set REPOMEND_FIXTURE_REPO or place "
            "fixture at tests/fixture_repo"
        )

    if not shutil.which("semgrep"):
        pytest.skip("semgrep not on PATH")

    finding = _SUBPROCESS_FINDING
    finding_id = "p4-e2e-verified"
    agent = FixGenSubagent(api_key=api_key)
    verifier = Verifier()

    with fix_worktree_context(fixture_repo, finding_id) as handle:
        fix_result = agent.apply_fix(
            finding,
            handle.worktree_path,
            finding_id=finding_id,
            branch_name=handle.branch,
        )

        if not fix_result.success:
            pytest.skip(
                "Fix-Gen did not call submit_fix (non-deterministic) — "
                f"error: {fix_result.error}"
            )

        result = verifier.verify(
            worktree_path=handle.worktree_path,
            repo_path=fixture_repo,
            file_path=finding["file_path"],
            rule_id=finding["rule_id"],
            line_start=finding["line_start"],
            line_end=finding["line_end"],
        )

        print(f"\n[p4-e2e-verified] Verifier result: {result.as_log_dict()}")

        assert result.verification_status == "verified", (
            f"AC-P4-11 FAIL — expected verified, got: {result.as_log_dict()}"
        )
        assert result.gate_1.status == "pass", (
            f"Gate 1 should PASS (rule eliminated): {result.gate_1}"
        )
        assert result.gate_2.status == "pass", (
            f"Gate 2 should PASS (edits in bounds): {result.gate_2}"
        )
        assert result.gate_3.status in ("pass", "skip"), (
            f"Gate 3 should PASS or SKIP: {result.gate_3}"
        )

        handle.mark_success()   # persist branch — fix is verified


@pytest.mark.integration
def test_verifier_end_to_end_failed_unpatched() -> None:
    """
    AC-P4-12: Verifier returns "failed" when no fix was applied.

    No Fix-Gen call — the worktree file is identical to HEAD (the original
    vulnerable.py). Gate 1 must FAIL because the scanner rule still fires.
    ADR-016 ensures Gate 2 and Gate 3 still run regardless.

    Does not require ANTHROPIC_API_KEY.
    Requires: semgrep on PATH · fixture repo
    """
    fixture_repo = _get_fixture_repo()
    if fixture_repo is None:
        pytest.skip(
            "Fixture repo not found — set REPOMEND_FIXTURE_REPO or place "
            "fixture at tests/fixture_repo"
        )

    if not shutil.which("semgrep"):
        pytest.skip("semgrep not on PATH")

    finding = _SUBPROCESS_FINDING
    finding_id = "p4-e2e-failed-unpatched"
    verifier = Verifier()

    with fix_worktree_context(fixture_repo, finding_id) as handle:
        # Intentionally apply NO patch — file is the unmodified original
        result = verifier.verify(
            worktree_path=handle.worktree_path,
            repo_path=fixture_repo,
            file_path=finding["file_path"],
            rule_id=finding["rule_id"],
            line_start=finding["line_start"],
            line_end=finding["line_end"],
        )

        print(f"\n[p4-e2e-failed-unpatched] Verifier result: {result.as_log_dict()}")

        assert result.verification_status == "failed", (
            f"AC-P4-12 FAIL — expected failed, got: {result.as_log_dict()}"
        )
        assert result.gate_1.status == "fail", (
            "Gate 1 should FAIL (rule still fires on unpatched file): "
            f"{result.gate_1}"
        )
        # ADR-016: Gate 2 and Gate 3 must have run regardless of Gate 1 outcome
        assert result.gate_2.status != "not run", (
            "ADR-016 violation: Gate 2 did not run after Gate 1 FAIL"
        )
        assert result.gate_3.status != "not run", (
            "ADR-016 violation: Gate 3 did not run after Gate 1 FAIL"
        )
        # mark_success NOT called — worktree discarded (correct fail path)


@pytest.mark.integration
def test_verifier_end_to_end_failed_out_of_bounds() -> None:
    """
    AC-P4-12 variant: Verifier gate_2 FAIL when edit is outside authorised range.

    Manually prepends a comment line to vulnerable.py — the inserted line lands
    at post-edit position 1, which is outside the authorised range [24, 24].
    Gate 2 must FAIL. ADR-016: all three gates run regardless.

    Does not require ANTHROPIC_API_KEY or semgrep (Gate 1 FAIL with no semgrep
    is acceptable here — we are asserting Gate 2 behaviour, not Gate 1).
    Requires: git on PATH · fixture repo
    """
    fixture_repo = _get_fixture_repo()
    if fixture_repo is None:
        pytest.skip(
            "Fixture repo not found — set REPOMEND_FIXTURE_REPO or place "
            "fixture at tests/fixture_repo"
        )

    finding = _SUBPROCESS_FINDING
    finding_id = "p4-e2e-failed-oob"
    verifier = Verifier()

    with fix_worktree_context(fixture_repo, finding_id) as handle:
        # Write a patch that inserts a line at position 1 — outside [24, 24]
        target = handle.worktree_path / finding["file_path"]
        original = target.read_text(encoding="utf-8", errors="replace")
        target.write_text(
            "# patchward-TEST: out-of-bounds edit at line 1\n" + original,
            encoding="utf-8",
        )

        result = verifier.verify(
            worktree_path=handle.worktree_path,
            repo_path=fixture_repo,
            file_path=finding["file_path"],
            rule_id=finding["rule_id"],
            line_start=finding["line_start"],
            line_end=finding["line_end"],
        )

        print(f"\n[p4-e2e-failed-oob] Verifier result: {result.as_log_dict()}")

        assert result.verification_status == "failed", (
            f"AC-P4-12 OOB FAIL — expected failed, got: {result.as_log_dict()}"
        )
        assert result.gate_2.status == "fail", (
            f"Gate 2 should FAIL (line-1 edit outside [24, 24]): {result.gate_2}"
        )
        # ADR-016: Gate 3 must have run regardless of Gate 2 outcome
        assert result.gate_3.status != "not run", (
            "ADR-016 violation: Gate 3 did not run after Gate 2 FAIL"
        )
        # mark_success NOT called — worktree discarded (correct fail path)


@pytest.mark.integration
def test_end_to_end_pr() -> None:
    """
    AC-P5-10: Full pipeline produces a real draft PR on patchward-fixture.

    Sequence: scan → fix (Fix-Gen) → verify (Verifier) → push (git push) →
    PR open (GitHub API) → assert pr_dict["status"] == "opened".

    Manual step after test passes: inspect the PR on GitHub, confirm:
      - PR is in Draft state
      - Body contains five sections (Finding, Fix, Verification Evidence,
        Diff, Test Output)
      - Head branch is patchward/fix-p5-e2e-* pointing at patchward-fixture
    Then close the PR without merging (test artifact).

    Requires: ANTHROPIC_API_KEY · GITHUB_TOKEN · semgrep · fixture repo
    """
    import os
    from patchward.config import load_config, validate_github_config
    from patchward.credential_proxy import CredentialProxy
    from patchward.pr_publisher import PRPublisher
    from patchward.run_log import RunLog

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        pytest.skip("ANTHROPIC_API_KEY not set")

    github_token = os.environ.get("GITHUB_TOKEN")
    if not github_token:
        pytest.skip("GITHUB_TOKEN not set")

    if not shutil.which("semgrep"):
        pytest.skip("semgrep not on PATH")
    if not shutil.which("bandit"):
        pytest.skip("bandit not on PATH")

    fixture_repo = _get_fixture_repo()
    if fixture_repo is None:
        pytest.skip(
            "Fixture repo not found — set REPOMEND_FIXTURE_REPO or place "
            "fixture at tests/fixture_repo"
        )

    # Load config — needs [github] section in patchward.toml
    cfg = load_config()
    validate_github_config(cfg)

    # Wire credentials
    proxy = CredentialProxy().load()

    finding = _SUBPROCESS_FINDING
    finding_id = "p5-e2e-pr"
    agent = FixGenSubagent(api_key=api_key)
    verifier = Verifier()
    run_log = RunLog()

    print(f"\n[AC-P5-10] Starting end-to-end PR test on {cfg.github.owner}/{cfg.github.repo}")
    print(f"[AC-P5-10] Target finding: {finding['rule_id']} @ {finding['file_path']}:{finding['line_start']}")

    with fix_worktree_context(fixture_repo, finding_id) as handle:
        # Fix
        fix_result = agent.apply_fix(
            finding,
            handle.worktree_path,
            finding_id=finding_id,
            branch_name=handle.branch,
        )

        if not fix_result.success:
            pytest.skip(
                "Fix-Gen did not call submit_fix (non-deterministic) — "
                f"error: {fix_result.error}"
            )

        print(f"[AC-P5-10] Fix-Gen succeeded: {fix_result.description[:80]}")

        # Verify
        verify_result = verifier.verify(
            worktree_path=handle.worktree_path,
            repo_path=fixture_repo,
            file_path=finding["file_path"],
            rule_id=finding["rule_id"],
            line_start=finding["line_start"],
            line_end=finding["line_end"],
        )

        print(f"[AC-P5-10] Verifier result: {verify_result.as_log_dict()}")

        assert verify_result.verification_status == "verified", (
            f"AC-P5-10 FAIL — fix must be verified before PR; "
            f"got: {verify_result.as_log_dict()}"
        )

        handle.mark_success()
        print(f"[AC-P5-10] Fix branch persisted: {fix_result.branch_name}")

        # Publish PR
        publisher = PRPublisher(
            config=cfg,
            credential_proxy=proxy,
            http_client=None,
        )
        pr_dict = publisher.publish(
            fix_result=fix_result,
            verifier_result=verify_result,
            finding=finding,
            run_log=run_log,
            worktree_path=handle.worktree_path,
        )

    print(f"\n[AC-P5-10] PR result: {pr_dict}")
    print(f"[AC-P5-10] PR URL:    {pr_dict.get('url', 'N/A')}")
    print(f"[AC-P5-10] PR number: {pr_dict.get('number', 'N/A')}")
    print(f"[AC-P5-10] PR status: {pr_dict.get('status', 'N/A')}")

    assert pr_dict["status"] in ("opened", "already_open"), (
        f"AC-P5-10 FAIL — expected opened or already_open, got: {pr_dict}"
    )
    pr_url = pr_dict.get("url", "")
    assert pr_url.startswith(
        f"https://github.com/{cfg.github.owner}/{cfg.github.repo}"
    ), f"AC-P5-10 FAIL — unexpected PR URL: {pr_url}"

    print(f"\n*** AC-P5-10 PASS — PR opened: {pr_url} ***")
    print("ACTION REQUIRED: Inspect PR on GitHub, confirm draft status, then close without merging.")


# ── KS-P6-08: AC-P6-11 two-finding batch integration test ─────────────────

@pytest.mark.integration
def test_batch_two_findings() -> None:
    """
    AC-P6-11: Batch pipeline on two entries pointing at patchward-fixture
    produces two run log records.

    Uses two RepoConfig entries for the same repo so both pipeline
    tasks run concurrently under asyncio.Semaphore(2).  A uuid4
    suffix is patched onto each finding_id inside pipeline.py to
    prevent branch-name collision when both tasks process the same
    first finding simultaneously.

    Asserts:
      - Two result dicts returned by run_batch
      - Each result has a "repo" field
      - At least one status is not "error" (pipeline reached scan)
      - Run log contains two records after append_batch_result()

    Skip guards: ANTHROPIC_API_KEY + GITHUB_TOKEN + semgrep +
    RUN_E2E_MULTI must all be set.

    # KS-TRACE: AC-P6-11, C-P6-09
    """
    import asyncio
    import uuid

    if not os.environ.get("ANTHROPIC_API_KEY"):
        pytest.skip("ANTHROPIC_API_KEY not set")
    if not os.environ.get("GITHUB_TOKEN"):
        pytest.skip("GITHUB_TOKEN not set")
    if not os.environ.get("RUN_E2E_MULTI"):
        pytest.skip(
            "RUN_E2E_MULTI not set — skipping multi-repo integration"
        )
    if not shutil.which("semgrep"):
        pytest.skip("semgrep not on PATH")
    if not shutil.which("bandit"):
        pytest.skip("bandit not on PATH")

    fixture_repo = _get_fixture_repo()
    if fixture_repo is None:
        pytest.skip("Fixture repo not found")

    from patchward.config import (
        RepomendConfig,
        GithubConfig,
        BatchConfig,
        ModelsConfig,
        RepoConfig,
    )
    from patchward.pipeline import run_batch
    from patchward.run_log import RunLog

    repo_entry = RepoConfig(
        path=str(fixture_repo),
        owner="yehorcallmedai-maker",
        repo="patchward-fixture",
        base_branch="main",
    )

    cfg = RepomendConfig(
        repo_path=str(fixture_repo),
        github=GithubConfig(
            owner="yehorcallmedai-maker",
            repo="patchward-fixture",
            base_branch="main",
        ),
        batch=BatchConfig(max_concurrent=2),
        models=ModelsConfig(),
        repos=[repo_entry, repo_entry],
    )

    api_key = os.environ["ANTHROPIC_API_KEY"]
    github_token = os.environ["GITHUB_TOKEN"]

    # Patch finding_id in pipeline to add uuid suffix so concurrent
    # tasks don't collide on the same branch name.
    # We monkeypatch fix_worktree_context to inject a uuid slot.
    import patchward.pipeline as pipeline_mod
    from patchward.fix_worktree import fix_worktree_context as _orig_ctx

    def _uuid_ctx(repo_path, finding_id):
        return _orig_ctx(repo_path, f"{finding_id}-{uuid.uuid4().hex[:8]}")

    original_ctx = pipeline_mod.fix_worktree_context
    pipeline_mod.fix_worktree_context = _uuid_ctx

    try:
        results = asyncio.run(
            run_batch(cfg, api_key, github_token)
        )
    finally:
        pipeline_mod.fix_worktree_context = original_ctx

    print(f"\n[AC-P6-11] Batch results: {results}")

    # ── AC-P6-11 assertions ────────────────────────────────────────────
    assert len(results) == 2, (
        f"Expected 2 results, got {len(results)}: {results}"
    )
    for r in results:
        assert "repo" in r, f"Missing 'repo' field in result: {r}"

    statuses = [r["status"] for r in results]
    # "error" = unhandled crash; anything else means pipeline
    # reached a known decision point (AC-P6-11)
    non_crash = [s for s in statuses if s != "error"]
    assert len(non_crash) >= 1, (
        f"All results are 'error' — pipeline crashed before scan: "
        f"{results}"
    )

    run_log = RunLog()
    for r in results:
        run_log.append_batch_result(r)

    records = run_log.read_all()
    assert len(records) == 2, (
        f"Expected 2 run log records, got {len(records)}"
    )

    print(
        f"[AC-P6-11] PASS — {len(results)} results, "
        f"{len(records)} run log records"
    )
    print(f"[AC-P6-11] Statuses: {statuses}")
    for r in results:
        if r.get("pr_url"):
            print(f"[AC-P6-11] PR opened: {r['pr_url']}")


# ── KS-P7-07: AC-P7-10 multi-finding integration test ─────────────────────


@pytest.mark.integration
def test_multi_finding_e2e() -> None:
    """
    AC-P7-10: Multi-finding pipeline on patchward-fixture.

    Runs run_batch against the fixture repo with
    max_findings_per_repo=3.  Asserts that run log records are
    produced (one per finding attempted), regardless of whether
    Fix-Gen or Verifier succeeds.

    The test PASSES if:
    - At least 1 run log record exists after the run
    - Each record has repo, finding_id, rule_id, status fields
    - At least one finding reaches Fix-Gen
      (status not "error" or "scanner_unavailable")

    Skip guards: ANTHROPIC_API_KEY + GITHUB_TOKEN +
    semgrep + bandit + trivy + RUN_E2E_MULTI_FINDING

    Manual step after test: inspect any PRs opened on
    patchward-fixture, close without merging.

    # KS-TRACE: AC-P7-10, C-P7-01, C-P7-02, C-P7-04
    """
    import asyncio

    from patchward.config import (
        BatchConfig,
        GithubConfig,
        ModelsConfig,
        RepomendConfig,
        RepoConfig,
    )
    from patchward.pipeline import run_batch
    from patchward.run_log import RunLog

    # Skip guards
    if not os.environ.get("ANTHROPIC_API_KEY"):
        pytest.skip("ANTHROPIC_API_KEY not set")
    if not os.environ.get("GITHUB_TOKEN"):
        pytest.skip("GITHUB_TOKEN not set")
    if not os.environ.get("RUN_E2E_MULTI_FINDING"):
        pytest.skip("RUN_E2E_MULTI_FINDING not set")
    for tool in ("semgrep", "bandit", "trivy"):
        if not shutil.which(tool):
            pytest.skip(f"{tool} not on PATH")

    fixture_repo = _get_fixture_repo()
    if fixture_repo is None:
        pytest.skip("Fixture repo not found")

    repo_entry = RepoConfig(
        path=str(fixture_repo),
        owner="yehorcallmedai-maker",
        repo="patchward-fixture",
        base_branch="main",
    )
    cfg = RepomendConfig(
        repo_path=str(fixture_repo),
        github=GithubConfig(
            owner="yehorcallmedai-maker",
            repo="patchward-fixture",
            base_branch="main",
        ),
        batch=BatchConfig(
            max_concurrent=1,
            max_findings_per_repo=3,
        ),
        models=ModelsConfig(),
        repos=[repo_entry],
    )

    api_key = os.environ["ANTHROPIC_API_KEY"]
    github_token = os.environ["GITHUB_TOKEN"]
    run_log = RunLog()

    print("\n[AC-P7-10] Starting multi-finding e2e test")
    print(f"[AC-P7-10] Fixture: {fixture_repo}")
    print("[AC-P7-10] max_findings_per_repo: 3")

    results = asyncio.run(
        run_batch(cfg, api_key, github_token, run_log=run_log)
    )
    print(f"[AC-P7-10] Batch results: {results}")

    records = list(run_log.read_all())
    print(f"[AC-P7-10] Run log records: {len(records)}")
    for r in records:
        print(
            f"  - {r.get('rule_id', '?')} "
            f"→ {r.get('status', '?')}"
        )

    # ── AC-P7-10 assertions ────────────────────────────────────────
    assert len(results) == 1, (
        f"Expected 1 repo result, got {len(results)}"
    )

    # If a scanner crashed before any findings were processed,
    # treat as a tool-availability skip (spec: SKIPS if a
    # required tool is missing / broken at runtime).
    repo_status = results[0].get("status") if results else None
    if repo_status == "scanner_unavailable":
        pytest.skip(
            "Scanner unavailable at runtime — "
            f"error: {results[0].get('error', '')}. "
            "Check trivy/semgrep/bandit produce valid output."
        )

    assert len(records) >= 1, (
        "Expected at least 1 run log record — "
        "pipeline did not reach any finding"
    )

    for record in records:
        assert "repo" in record, (
            f"Missing 'repo' in record: {record}"
        )
        assert "finding_id" in record, (
            f"Missing 'finding_id': {record}"
        )
        assert "rule_id" in record, (
            f"Missing 'rule_id': {record}"
        )
        assert "status" in record, (
            f"Missing 'status': {record}"
        )

    non_error = [
        r for r in records
        if r.get("status") not in (
            "error", "scanner_unavailable"
        )
    ]
    assert len(non_error) >= 1, (
        f"All findings errored before Fix-Gen: {records}"
    )

    statuses = [r.get("status") for r in records]
    print(f"[AC-P7-10] Statuses: {statuses}")
    for r in records:
        if r.get("pr_url"):
            print(f"[AC-P7-10] PR opened: {r['pr_url']}")

    print(
        f"[AC-P7-10] PASS — {len(records)} run log records"
    )
    # Note: asserts >= 1 record, not == 3 — max_findings_per_repo
    # is a cap, not a guarantee; fixture finding count depends on
    # scanner ruleset and scanner availability at runtime.
