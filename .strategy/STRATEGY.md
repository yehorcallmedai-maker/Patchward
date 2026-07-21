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
- [2026-07-21] main @ `3d1ec086972445373ac6a1eb7ac8abed238559a5`
  ("harden(webhook): range-validate rate-limit/body-size env parsers
  (Phase 9)"). Confirmed via THREE independent methods, none relying on
  the local `D:\` mount: (1) `git ls-remote origin main` from the cloud
  sandbox's own bash, (2) a fresh `git clone` of the repo + `git log -1`,
  (3) a direct `raw.githubusercontent.com` fetch of `src/patchward/webhook.py`
  at this exact hash, sha256-compared against the fresh clone's copy —
  identical (`fc7254b3...f1a229`). This is 4 commits ahead of the
  `7654b1e` this file previously cited: `0c6a742` (rate limiting /
  body-size limits / `X-GitHub-Delivery` logging) → `793a1d0` (docs close)
  → `4b6a023` (3 defense-in-depth spy tests proving the post-read
  body-size check) → `3d1ec08` (Phase 9 security-boundary hardening).
- [2026-07-21] **BACKLOG item 5 (Phase 9 Exposure Gate) is FULLY CLOSED,
  COMMITTED AND PUSHED** — not merely staged, and further along than
  either `BACKLOG.md`'s or `NEXT_SESSION_START.md`'s own uncommitted
  local drafts said (both existed on disk, partially correcting the
  "pending Yehor's commit" framing, but both stopped at commit `793a1d0`
  and didn't know about `4b6a023`/`3d1ec08`). The two commits after
  `793a1d0` did real additional security work, not just docs:
  `3d1ec08`'s commit message: "Reject non-finite (inf/nan/-inf) and
  out-of-range (<1, <=0) env overrides... Closes the guard hole found in
  adversarial review of the post-HMAC limiter reorder. 10 range-validation
  tests, proven discriminating via negative control against the unguarded
  variant." Verified directly against the diff: the rate limiter call was
  moved to run *after* `_verify_signature` (so unauthenticated floods
  can't consume the rate-limit budget — a real starvation-vector fix, not
  cosmetic), and the three env-parser helpers
  (`_max_body_bytes`/`_rate_limit_max_requests`/`_rate_limit_window_seconds`)
  now reject non-finite/out-of-range values via `math.isfinite()` and
  range checks instead of a bare `except ValueError`, falling back to
  documented defaults. `test_infinite_window_env_still_expires_limiter_recovers`
  is a genuine negative-control test — it proves the guard doesn't just
  suppress a 500, it proves the limiter actually *recovers* afterward,
  which an unguarded `float("inf")` would never do. **Test-count
  cross-check (independent of trusting any reported total):** counted the
  actual test functions/parametrize cases added in each commit's diff —
  `4b6a023` adds 3, `3d1ec08` adds 12 (6 functions, 9 of which are
  parametrized range-validation cases + 2 non-range-validation) → 468
  (Session 020 close figure) + 3 + 12 = **483**, exactly matching what
  was reported at session open. **What is NOT independently re-verified
  this session:** the actual `483 passed, 2 skipped, 15 deselected,
  90.46% coverage, Python 3.14.4` pytest run — this sandbox has no
  Python ≥3.12 interpreter and can't fetch one
  (`uv python install 3.12` → 403 from the python-build-standalone
  release CDN, consistent with H4). Treat the real-machine run as Tier 1
  (self-reported, not reproduced here) but strongly corroborated by the
  arithmetic cross-check above. Also Tier 1, not Tier 0: the specific
  claim of "two adversarial reviews, both clean" — the *outcome* (the
  guard hole and its fix) is fully confirmed in the diff; the *review
  process itself* (how many passes, by whom) isn't checkable from repo
  artifacts and is corroborated only by the commit message's own wording.
- [2026-07-21] Fly webhook healthy — fresh `WebFetch` this session →
  `{"status":"ok"}` (Tier 1; direct bash `curl` to `patchward-webhook.fly.dev`
  fails with connection status 000 from this sandbox's own egress
  restrictions, consistent with H4 — not a health signal).
- [2026-07-21] `webhook-reqs.txt` confirmed present at repo root (154,468
  bytes, `device_list_dir` — Tier 0), untracked (`git ls-files` empty)
  and absent from `.gitignore`. Still pending Yehor's gitignore-or-delete
  call; not touched this session.
- [2026-07-21] `memory/Patchward_Turning-Point_Industrial-Plan_2026-07-16.md`
  mojibake claim **NOT REPRODUCED**: full non-ASCII character census of
  the file (`Python` `collections.Counter` over every char with
  `ord(ch) > 127`) found only `—`(em-dash, ×99), `→`(×14), `–`(en-dash,
  ×14), `·`(×6), `≥`(×3), `§`(×2), `≤`(×1) — all legitimate, no
  replacement characters (`�`) or double-encoded UTF-8 artifacts
  (`â€™`-style sequences). File is confirmed untracked (not in git at
  all). If Yehor still sees garbled text, it's most likely a rendering
  issue in whatever he's viewing it in, not corruption in the saved
  file — worth him naming the specific line if it recurs.
- [2026-07-21] PR #1283 disclosure comment (unrelated repo) — not chased
  this session per standing instruction ("your pace," unrelated repo).
  Still UNVERIFIED, unchanged.
- [2026-07-21] No agent-startable code work is queued. Confirmed: the
  only remaining open BACKLOG items (8 site rename, 9 PyPI publisher
  verification, 12 CRA/GDPR legal) are all Yehor-or-external-only, same
  as every prior session's finding — nothing new surfaced this session
  to contradict that.

## Open threads
- BACKLOG 9: PyPI pending-publisher environment field — "Any" literal vs
  unrestricted? Yehor checks PyPI UI, then one workflow_dispatch to prove chain
- BACKLOG 8: RepoMend→Patchward swap in callmed-landing (34 occurrences, 3 files)
- BACKLOG 12: CRA/GDPR — external legal input, unchanged
- webhook-reqs.txt (repo root, 154KB, untracked) — gitignore or delete, Yehor's call
- `pending_change_cancelled` — noted in BACKLOG item 5's closing text as a
  low-priority open question (does it exist as a distinct Marketplace
  action needing the same `is_entitled()` reasoning?) — not urgent
- ssh-audit fork: 2 stale repomend/* branches, optional cleanup
- PR #1283 disclosure comment, unrelated repo — Yehor's own pace
- Detailed engineering memory lives in memory/ (STATE.md, BACKLOG.md,
  project_session_log.md) — this file is the calibration layer, not a fork of it

## Heuristics (earned)
- H1 [active, promoted 2026-07-15, evidence: Session 018 close + Session
  020, WIDENED 2026-07-16]: Sandbox git status/diff and file reads
  against the D:\ mount serve stale content and false diffs; `git show
  HEAD:<path>` can also serve stale/truncated content. Revised trust
  boundary: only remote-ref operations (`git ls-remote`), a **fresh
  `git clone`**, and direct fetches of hosted content
  (`raw.githubusercontent.com` via `web_fetch` or sandbox bash, both
  reachable) are fully trustworthy — local git object reads against an
  existing mounted checkout cannot be assumed safe. **Session 021
  addendum: cloning fresh into the sandbox's own filesystem (not reading
  the D:\ mount at all) sidesteps this entire class of bug** — used this
  session for all git-state verification, zero mount-staleness issues
  encountered as a result.
- H2 [active, promoted 2026-07-15, evidence: twice in Session 018 close]:
  Never cite "the current commit hash" inside a committed handoff file —
  structurally always stale. Run git ls-remote at session open instead.
- H3 [active, carried from project rules, evidence: Sessions 015–018]:
  Tier 2 sources (another project's memory files, unauthenticated proxies)
  are leads, never gating facts.
- H4 [active, promoted 2026-07-16, evidence: Sessions 020, 021]: this
  sandbox's bash has no general internet egress to arbitrary hosts
  (GitHub release CDN via `uv python install`, Fly proxy via direct
  `curl`) even though `web_fetch`, `pip install` from PyPI, `git`
  operations against `github.com`/`api.github.com`, and direct `curl` to
  `raw.githubusercontent.com` all work. Don't assume a bash-level network
  failure means the target is down or the technique is unusable — test
  the specific host/tool combination before concluding "network
  blocked." **Session 021: this is also why a real `uv run pytest`
  re-run isn't possible from this sandbox** (`requires-python = ">=3.12"`,
  sandbox has 3.11.15, and fetching 3.12+ via `uv python install` hits
  this exact block) — a standing, not per-session, limitation.
- H5 [active, promoted 2026-07-16, evidence: Session 020]: before calling
  a status-check/entitlement condition a "bug" from code alone, check
  what the upstream system (here, GitHub's own webhook docs) actually
  says that status means — a correct reading of the code is not the same
  as a correct reading of the domain.
- H6 [active, promoted 2026-07-16, evidence: 3 occurrences in Session
  020]: after using `Edit` on a source or test file in this sandbox, do
  not trust bash's own view of that file for running tests — re-read via
  `Read` and, if bash's line count/`ast.parse` disagrees, rewrite it
  byte-for-byte through a bash heredoc before trusting any sandbox test run.
- H7 [active, promoted 2026-07-16, evidence: Session 020's Correction 1-3
  exchange]: when summarizing multi-step work after time has passed
  within the same session, re-paste the actual evidence (diff, raw
  command output) rather than asserting "already done."
- H8-candidate [1 occurrence, Session 021, NOT yet promoted]: a memory
  reconciliation task can itself be started and left uncommitted across
  sessions — this session found `BACKLOG.md` and `NEXT_SESSION_START.md`
  both already had partial, uncommitted local corrections sitting on
  `D:\`, written after `793a1d0` but before `4b6a023`/`3d1ec08`, that
  would have been invisible from `git log`/`git clone` alone. Check the
  local disk (via the device bridge, diffed against a fresh clone) for
  uncommitted drafts before assuming a stale-memory task starts from
  the last committed state. Needs a second occurrence before promotion.

## Failed approaches (ledger)
- [2026-07-15] Trusting sandbox `git status` for close-out verification —
  false report caught twice (Session 018, this session). Retry only if the
  mount sync mechanism verifiably changes.
- [2026-07-21] Trying to install a Python 3.12+ interpreter in-sandbox via
  `uv python install` to re-run the real test suite — blocked by H4 (403
  from the python-build-standalone release CDN). Retry only if the
  sandbox's network egress policy changes; until then, real pytest runs
  stay Yehor-machine-only and the arithmetic test-count cross-check is
  the best available substitute.

## Session log
- [2026-07-15, Session 019 close] Bootstrap session: created this file,
  ran first open-verification pass. Drift at open: 0 substantive; 1 sandbox
  false-positive (fake 644-line deletion) attributed to mount staleness.
- [2026-07-16, Session 020 open] Verified all 019 claims fresh (0 drift).
  Surfaced BACKLOG 5 as the highest-leverage move (only agent-owned item).
- [2026-07-16, Session 020 close] All 4 sub-parts of BACKLOG 5 closed or
  resolved; real self-correction on `pending_change` held under Yehor's
  independent re-check; nothing committed all session.
- [2026-07-21, Session 021 open] Opened with a device-bridge outage at
  session start (folder not yet connected) — worked around entirely via
  a fresh `git clone` of `https://github.com/yehorcallmedai-maker/Patchward.git`
  from the cloud sandbox, which turned out to be sufficient for all
  git-state and code-content verification (see H1 addendum). Device
  bridge came online mid-session; used it only for the two genuinely
  local-only checks (`webhook-reqs.txt` existence, Turning-Point file
  mojibake) and to discover the uncommitted partial-reconciliation drafts
  (see H8-candidate). Found: BACKLOG item 5 is further along than any
  memory file said — genuinely closed through `3d1ec08`, not `793a1d0`.
  Drift: `.strategy/STRATEGY.md` (both committed and local-uncommitted
  copies) still cited `7654b1e` and "pending Yehor's commit"; `BACKLOG.md`
  and `NEXT_SESSION_START.md` had uncommitted local partial fixes that
  themselves stopped 2 commits short of true HEAD; the mojibake claim
  did not reproduce against the file as currently saved. L2 goal: finish
  the memory reconciliation through true HEAD across all three files —
  this session's edits (STRATEGY.md full rewrite, BACKLOG.md item 5
  section, NEXT_SESSION_START.md new addendum) do that. No git commits
  made from the sandbox (standing rule); files written to `D:\` for
  Yehor's own review and commit.

## Calibration record
- [2026-07-15 open] 5/6 confirmed, 1 UNVERIFIED, 0 drifted. 1.00 on checkable claims.
- [2026-07-15 close] 4/4 close claims confirmed. 1.00.
- [2026-07-16 open] 6/7 confirmed, 1 UNVERIFIED, 0 drifted. 1.00 on checkable claims.
- [2026-07-16 close] All logged claims confirmed at close via independent
  method. 1 real-time self-correction (positive signal, not a miss).
- [2026-07-21 open] Of ~12 checkable claims in the session-opening brief:
  9 CONFIRMED (Phase 9 closure, the 4-method verification chain and its
  results, Fly health, the exact commit hash, the hosted-content-hash
  technique's validity, both memory-drift claims, webhook-reqs.txt's
  existence, "no agent-startable work queued"), 1 DRIFTED (Turning-Point
  mojibake — not reproduced against the file as saved), 2 UNVERIFIED
  (the real pytest run itself — sandbox can't get Python ≥3.12, only
  cross-checked arithmetically; the CRLF/`git diff --stat -w` mount-noise
  trick — not exercised, since this session avoided the mount for git
  ops entirely via H1's fresh-clone addendum). **0.75 on checkable
  claims (9/12).** First session to score below 1.00 across this
  project's calibration history — driven by one real drift (mojibake,
  a claim that simply didn't hold up, not a memory-hygiene failure) and
  two claims this session's method choices left genuinely untested
  rather than confirmed-or-refuted. Not below the 0.7-for-two-sessions
  threshold that would trigger a memory-hygiene warning; worth watching
  next session rather than acting on yet.
