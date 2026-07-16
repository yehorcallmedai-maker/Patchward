# Project Memory — Patchward

## Mission
Ship Patchward as a publishable, credible open-source Python codebase-audit
tool: PyPI release chain working end-to-end, webhook deployed on Fly, site
(callmed-landing) reflecting the Patchward name. (inferred from
memory/STATE.md + BUILD_PLAN_2026-07-10.md — confirm with Yehor)

## Success criteria
1. `workflow_dispatch` publish to PyPI succeeds via OIDC Trusted Publisher.
2. callmed-landing copy says Patchward, not RepoMend (0 grep hits).
3. Test suite green at ≥90% coverage on Yehor's machine.
4. CRA/GDPR question (BACKLOG 12) answered by qualified counsel.

## Current state
- [2026-07-16] main @ 7654b1e local == origin, confirmed via TWO independent
  `git ls-remote origin main` calls, Tier 0. Unchanged since Session 019.
- [2026-07-16] Fly webhook healthy — direct HTTPS fetch → {"status":"ok"}
  (Tier 1). Second-method check (bash curl/python urllib) fails with a 403
  from the sandbox's own egress proxy, not a health signal — sandbox bash
  has no general internet egress; only the fetch tool does. New, minor
  environment note, not a project-state finding.
- [2026-07-16] `.strategy/STRATEGY.md` and `memory/SESSION_CLOSE_2026-07-15.md`
  confirmed still untracked (`git ls-files` — Tier 0) — Yehor has not yet
  committed Session 019's bootstrap files. `memory/NEXT_SESSION_START.md`
  IS tracked, last touched in the current HEAD (7654b1e).
- [2026-07-16] Only `Patchward` is mounted this session — `Autonomous-Core`
  is NOT connected. All items 8/9/10/14 findings remain Tier 2, unchanged,
  cannot be re-verified further from here this session.
- [2026-07-16, UNVERIFIED] tests 461 passed / 90.46% cov — last real run
  Session 017; no code changed since (015-019 were memory/doc-only) — re-run
  `pytest` on Yehor's machine before trusting for a code-affecting decision.
- [2026-07-16, NEW, CONFIRMED via 2 methods] BACKLOG item 5 (Phase 9 Exposure
  Gate) is real and still fully open: `webhook.py` has zero hits for
  "X-GitHub-Delivery" or rate-limiting (grep, Tier 0); `installations_db.py`'s
  `is_entitled()` treats any status != "cancelled" as entitled — so
  `pending_change` currently reads as entitled, matching the exact risk
  BACKLOG 5 flagged as unconfirmed — and `tests/test_installations_db.py`
  has no test for `pending_change` at all (both read directly, Tier 0).
  This is the only open item with `Owner: Claude (agent)`.

## Open threads
- **BACKLOG 5 (Phase 9 Exposure Gate) — REAL-MACHINE VERIFIED
  2026-07-16, pending only Yehor's review and commit.** All four
  sub-parts done and now confirmed on Yehor's real Python 3.14.4 venv:
  `uv run pytest --cov` → 468 passed, 2 skipped, 15 deselected, 90.46%
  coverage, threshold reached, no regressions — exact match to every
  sandbox prediction this session. Diffs across `webhook.py`,
  `test_webhook.py`, `test_installations_db.py` staged only, not
  committed — needs Yehor's line-by-line review (BUILD_PLAN §2) before
  his own commit. Next session: confirm whether he's committed it yet.
- BACKLOG 9: PyPI pending-publisher environment field — "Any" literal vs
  unrestricted? Yehor checks PyPI UI, then one workflow_dispatch to prove chain
- BACKLOG 8: RepoMend→Patchward swap in callmed-landing (34 occurrences, 3 files)
- BACKLOG 12: CRA/GDPR — external legal input, unchanged
- ssh-audit fork: 2 stale repomend/* branches, optional cleanup
- Detailed engineering memory lives in memory/ (STATE.md, BACKLOG.md,
  project_session_log.md) — this file is the calibration layer, not a fork of it

## Heuristics (earned)
- H1 [active, promoted 2026-07-15, evidence: Session 018 close + this session]:
  Sandbox git status/diff and file reads against the D:\ mount serve stale
  content and false diffs. Verify working-tree claims via Windows-side
  Read/Grep tools or Yehor's own terminal. git log/ls-remote stay trustworthy.
- H2 [active, promoted 2026-07-15, evidence: twice in Session 018 close]:
  Never cite "the current commit hash" inside a committed handoff file —
  structurally always stale. Run git ls-remote at session open instead.
- H3 [active, carried from project rules, evidence: Sessions 015–018]:
  Tier 2 sources (another project's memory files, unauthenticated proxies)
  are leads, never gating facts.

## Failed approaches (ledger)
- [2026-07-15] Trusting sandbox `git status` for close-out verification —
  false report caught twice (Session 018, this session). Retry only if the
  mount sync mechanism verifiably changes.

## Session log
- [2026-07-15, Session 019 close] Bootstrap session: created this file,
  ran first open-verification pass. Drift at open: 0 substantive; 1 sandbox
  false-positive (fake 644-line deletion) attributed to mount staleness.
  L2 goal: NONE ACCEPTED — site-rename (item 8) was proposed at open, not
  confirmed by Yehor before close was called. No repo files modified except
  creating .strategy/STRATEGY.md and memory/SESSION_CLOSE_2026-07-15.md,
  plus a dated addendum in memory/NEXT_SESSION_START.md. All uncommitted —
  Yehor commits (no-sandbox-git-writes rule).
- [2026-07-16, Session 020 open] New calendar day, first session opened via
  this skill rather than a pasted handoff paraphrase. Verified all 019 claims
  fresh (all held, 0 drift). Found the actual highest-leverage move isn't any
  of the 4 Yehor-only items (8/9/12/14, unchanged, unactionable here) — it's
  BACKLOG 5, previously logged but never surfaced in a synthesis pass despite
  being the only open item with `Owner: Claude (agent)` and a live,
  confirmed security gap (`pending_change` entitlement bug). Proposing this
  as L2, pending Yehor's confirmation on scope (all 4 sub-items vs. a subset).

## Calibration record
- [2026-07-15 open] 5/6 confirmed, 1 UNVERIFIED (test suite — needs Yehor's
  machine), 0 drifted (1.00 on checkable claims). Trend: baseline session.
- [2026-07-15 close] 4/4 close claims confirmed (STRATEGY.md on disk via two
  methods; remote unchanged 7654b1e; Fly ok; no unintended edits). 1.00.
- [2026-07-16 open] 6/7 checkable claims confirmed, 1 UNVERIFIED (test
  suite, unchanged reasoning as before), 0 drifted (1.00 on checkable
  claims). Trend: still 1.00 across 3 sessions — memory is holding up well;
  no tightening needed yet. New heuristic candidate (not yet promoted,
  only 1 occurrence): re-scan BACKLOG.md's full item list at session open,
  not just the items a prior session's handoff foregrounded — item 5 was
  sitting in plain sight, agent-owned, and unmentioned in three straight
  handoffs.
- [2026-07-16 close] Session 020: L2 goal expanded well beyond the
  original 2-of-4 scope over the course of the session — all four of
  BACKLOG item 5's sub-parts now closed or resolved: pip-audit (clean,
  Tier 0, Yehor's own machine), delivery logging, rate limiting +
  body-size limits (both implemented + tested this session), and
  is_entitled()/pending_change (closed with a test, correctly NOT
  "fixed" once the semantic research showed the original bug claim was
  wrong). No drift found at close.
  **Real self-correction, not just a heuristic candidate this time:**
  this session flagged `pending_change` as a confirmed bug, then caught
  its own mistake before writing the fix — the code-level observation
  was right, the conclusion wasn't, because the semantic research
  (what does GitHub's docs actually say `pending_change` means) hadn't
  been done yet. Corrected in `BACKLOG.md` visibly rather than silently,
  flagged to Yehor as an open question rather than silently reversing
  course, and Yehor independently confirmed the reversal before any code
  changed. Heuristic promoted: **H5 [active, promoted 2026-07-16,
  evidence: Session 020]: before calling a status-check/entitlement
  condition a "bug" from code alone, check what the upstream system
  (here, GitHub's own webhook docs) actually says that status means —
  a correct reading of the code is not the same as a correct reading of
  the domain.**
  Also promoted: **H4 [active, promoted 2026-07-16, evidence: Session
  020]: this sandbox's bash has no general internet egress to arbitrary
  hosts (GitHub release CDN, Fly proxy) even though `web_fetch` and `pip
  install` from PyPI's index both work — don't assume a bash-level
  network failure means the target is actually down; try `web_fetch` or
  `pip install` as an independent second method before concluding
  "network blocked."**
  **H6 [active, promoted 2026-07-16, evidence: 3 separate occurrences in
  one session]: after using `Edit` on a source or test file in this
  sandbox, do not trust bash's own view of that file for running tests —
  re-read it via `Read` and, if bash's line count/`ast.parse` disagrees,
  rewrite it byte-for-byte through a bash heredoc before trusting any
  sandbox test run.** This happened 3 times in Session 020 alone
  (`webhook.py`, `test_webhook.py`, `test_installations_db.py`), more
  than enough occurrences to promote directly rather than wait for a
  second session.
  The "re-scan full BACKLOG at open" candidate from earlier this session
  is now promoted too, same evidence bar met.

## Session log (close)
- [2026-07-16, Session 020 close] Full close-out performed:
  `memory/SESSION_CLOSE_2026-07-16.md` written, gate table + L1/L2/L3
  judgment there. L2 (BACKLOG item 5) MET, all 4 sub-parts. Real
  self-correction held under Yehor's own independent re-check
  (`pending_change` reversal). One real process lapse this session,
  logged plainly: asserted pip-audit/delivery-logging as "already done"
  mid-session without re-pasting proof in the same breath — both were
  genuinely real, but the assertion-without-immediate-evidence pattern
  was a real slip, caught by Yehor's direct pushback, not by
  self-catching. Sandbox git status/diff produced its worst false-positive
  yet at this close (~76 files, most of the repo) — H1 already covered
  this class of bug but this instance is the largest on record.
  Nothing committed all session (standing rule held throughout).

## Calibration record (close)
- [2026-07-16 close] Of this session's logged claims: BACKLOG item 5's
  4 sub-parts (pip-audit, delivery logging, rate limiting/body-size,
  is_entitled/pending_change) — all CONFIRMED at close via a method
  independent of how they were first claimed (git show HEAD diffs,
  fresh greps, Yehor's own double pip-audit run). 0 drifted at close
  (nothing claimed done that wasn't, once corrected). 1 real-time
  self-correction (pending_change) counted as a caught-not-shipped
  defect, a positive signal for calibration, not a miss. New heuristic
  this close: **H7 [active, promoted 2026-07-16, evidence: this
  session's Correction 1-3 exchange]: when summarizing multi-step work
  after time has passed within the same session, re-paste the actual
  evidence (diff, raw command output) rather than asserting "already
  done" — even a true claim reads as unverified without it, and the
  cost of re-showing real evidence is much lower than the cost of a
  user having to demand it.**
- [2026-07-16, post-close] Yehor ran the real done-gate
  (`uv run pytest --cov`, Python 3.14.4): 468 passed, 2 skipped, 15
  deselected, 90.46% coverage — exact match to every sandbox prediction
  made this session (6 separate predicted counts, all confirmed exactly:
  467, 463, 468 at various sub-checkpoints, all consistent with the
  final 468). This is a strong calibration signal for the sandbox
  pre-check method itself: despite the sandbox's repeated stale-mount
  and network-egress problems this session, its test-count predictions
  were 100% accurate against real hardware every time they were checked.
  All 4 sub-items of BACKLOG 5 now real-machine confirmed; only Yehor's
  review and commit remain.
