# Patchward — CONTEXT
# Single entry point for Claude. Read this first, every session.
# Last updated: 2026-07-10 (Session — see note below; content below this
# block through "Phase 7 backlog" is the RepoMend-era record, last touched
# 2026-06-23, and is kept as history — do not treat it as current status.)

---

## ⚠️ RECORD GAP — READ THIS FIRST
Between 2026-06-23 (RepoMend v0.1.0 "PROJECT COMPLETE") and 2026-07-09,
substantial work happened that was never logged to this file or to
project_open_tasks.md:
  - Renamed RepoMend → Patchward (repomend.com is a live unrelated
    competitor); commit c27ea40, 2026-07-07.
  - New work stream, "Phase 1.3-1.5": GitHub App webhook receiver +
    Marketplace billing state (src/patchward/webhook.py,
    github_app_auth.py, installations_db.py). Commit 0bb0286, 2026-07-09.
  - fly.toml + docker/webhook.Dockerfile added — Fly.io deployment
    (patchward-webhook.fly.dev) is live, /healthz confirmed OK
    (verified fresh 2026-07-10).
  - PyPI Trusted Publisher CI scaffolded (not yet active).
No session log entries, ADRs, or task records exist for this period.
This file's own history (below) has NOT been updated to reflect any of
it. Treat everything from "## What this is" through "Phase 7 backlog"
as pre-rename RepoMend history, not current project state.

## Session 2026-07-10 — item #27 resolved, verification lesson logged
Prior close-out (2026-07-09) believed commit 0bb0286 (the webhook/
billing commit) existed on GitHub but was NOT reachable from `main` —
one branch, zero PRs, orphaned commit. Re-verified fresh this session:
- Unauthenticated `api.github.com/repos/.../git/refs/heads/main` reads
  (made from the Claude sandbox, which routes through a shared/rate-
  limited proxy) repeatedly and incorrectly returned the OLD sha
  (9bbe4967), even after confirming with Yehor that the push had
  already succeeded.
- Ground truth, confirmed two independent authoritative ways:
  `git ls-remote origin main` (run by Yehor, real machine, real
  network) AND the GitHub web UI commits page (logged in) — both show
  `main` at 0bb0286, committed 2026-07-09.
- **LESSON: unauthenticated api.github.com reads made from this sandbox
  are not reliable ground truth — they can silently serve stale/cached
  data under shared rate limits. Always corroborate with `git
  ls-remote` (run by Yehor on his own machine) or the authenticated
  GitHub web UI before treating an API read as confirmed state.**
Item #27 is CLOSED. src/patchward/webhook.py, github_app_auth.py, and
installations_db.py are confirmed on `main` (content-addressed commit
hash match, no ambiguity).

## Owner
Yehor (solo project)

## Location
D:\Dev\Projects\Patchward\           ← project root (renamed from RepoMend, 2026-07-07)
D:\Dev\Projects\repomend-fixture\    ← fixture repo (also cloned at tests/fixture_repo)
Deployed: patchward-webhook.fly.dev  ← Fly.io webhook receiver, /healthz OK

## Current state (as last actually verified, 2026-07-10)
- Item #27 (webhook/billing commit reachable from main) — CLOSED, see above.
- Fly deployment — alive, healthz OK.
- Everything else below "## What this is" is RepoMend-era (pre-2026-06-23)
  and has not been reconciled against the Patchward rename or the
  Phase 1.3-1.5 webhook/billing work. Full reconciliation not yet done —
  next session should either do it or explicitly decide it's not worth doing.

## ⚡ NEXT TASK
Backlog choices (per Yehor, 2026-07-10 session): authorized end-to-end
test push (scan→fix→verify→PR pipeline, costs Anthropic credits, may
open a real draft PR), Mirror Pass Tier 2, or callmed-landing rename.
Not yet chosen. Also open: ClinInsight/Databutton LinkedIn DM replies
— unconfirmed as of 2026-07-10.

---

## (HISTORICAL — RepoMend era, last updated 2026-06-23, not reconciled)

## ⚡ OLD NEXT TASK — KS-P7-08: Keystone Report Phase 7
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
