# RepoMend — CONTEXT
# Single entry point for Claude. Read this first, every session.
# Last updated: 2026-06-23

---

## What this is
Local-first multi-repo security agent. Scans code for vulnerabilities (Semgrep,
Bandit, pip-audit, Trivy, etc.), runs a Fix-Gen subagent to patch them inside a
sandboxed git worktree branch, then verifies the patch with a deterministic
Verifier (no LLM). Goal: automated security remediation with human sign-off at
phase gates.

## Owner
Yehor (solo project)

## Location
D:\Dev\Projects\RepoMend\            ← project root
D:\Dev\Projects\repomend-fixture\    ← fixture repo (also cloned at tests/fixture_repo)

## Current state
- Phase 6 — CLOSED 2026-06-23. Keystone Report signed.
- Phase 7 — IN PROGRESS (Session 012, 2026-06-23).
  INTAKE signed. KS-P7-02 through KS-P7-07 COMPLETE.
- Tests: 371 passed · 1 deselected (last confirmed 2026-06-23, Session 012)
- Trivy installed on dev machine (winget, v0.71.2) — KL-P6-04 resolved.

## ⚡ NEXT TASK — KS-P7-08: Keystone Report Phase 7
All functional + distribution tasks complete. Write and sign the report.

## Phase 7 backlog (post-signature)
- KS-P7-02: AsyncAnthropic migration in fix_gen.py (C-P7-03, AC-P7-03)
- KS-P7-03: RunLog threading into run_repo_pipeline() (C-P7-04, AC-P7-05)
- KS-P7-04: Multi-finding loop + max_findings_per_repo config
            (C-P7-01/02, AC-P7-01/02/04/11)
- KS-P7-05: uv tool install verification + repomend.toml.example
            (C-P7-05/06, AC-P7-06/07)
- KS-P7-06: docs/user_guide.md + README.md update (C-P7-07/08, AC-P7-08/09)
- KS-P7-07: End-to-end integration test AC-P7-10
- KS-P7-08: Keystone Report Phase 7

## Key rules (RULE-1 is the most important)
RULE-1: ALL file writes via bash heredoc — NEVER use Edit/Write tools directly.
        Edit/Write truncate NTFS overlay files at ~1067 bytes. Use cat heredoc or
        python3 write. This rule has no exceptions.
RULE-2: Python 3.10 in sandbox, 3.12 target. Use timezone.utc not datetime.UTC.
RULE-3: ruff enforces 79-char line limit on ALL lines. Verify before writing.
RULE-4: uv run pytest (Windows) — tests cannot run in Linux sandbox (no network for uv).
RULE-5: All architectural decisions logged to memory/architectural_decisions.md.
RULE-6: Stale worktree lock files — use PowerShell Remove-Item -Force, NOT del /f 2>nul.
        del with 2>nul redirect raises a non-terminating error in PowerShell that
        silently prevents deletion. Remove-Item -ErrorAction SilentlyContinue works.

## Key files
memory/project_open_tasks.md      — full phase backlog with status
memory/project_session_log.md     — session history
memory/architectural_decisions.md — ADR log (ADR-001 through ADR-026; ADR-023–026 approved)
docs/intake_phase7.md             — Phase 7 INTAKE contract (SIGNED 2026-06-23)
docs/intake_phase6.md             — Phase 6 INTAKE contract (signed 2026-06-23)
reports/keystone_report_phase6.md — Phase 6 Keystone Report (signed 2026-06-23)
src/repomend/fix_gen.py           — Fix-Gen subagent (AsyncAnthropic, async apply_fix)
src/repomend/pipeline.py          — async multi-repo pipeline (run_batch, run_repo_pipeline)
src/repomend/verifier.py          — deterministic Gate 1/2/3 verifier (no LLM)
src/repomend/cli.py               — scan + fix commands

## Session start protocol
1. Read this file
2. Ask user to run from D:\Dev\Projects\RepoMend:
   uv run pytest --override-ini="addopts=" -q
   --ignore=tests\test_golden_dataset.py
   --ignore=tests\test_docker_sandbox.py
   --ignore=tests\fixture_repo
3. Confirm baseline: 371 passed, 1 deselected
4. State: "Last done: KS-P7-07 — Integration test COMPLETE (Session 012, 2026-06-23).
   Next: KS-P7-08 — Keystone Report Phase 7.
   Ready to begin — confirm or redirect."
