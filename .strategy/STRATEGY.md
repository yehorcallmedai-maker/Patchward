# Project Memory — Patchward

## Mission
Ship Patchward as a publishable, credible open-source Python codebase-audit
tool: PyPI release chain working end-to-end, webhook deployed on Fly, site
(callmed-landing) reflecting the Patchward name. (inferred from
memory/STATE.md + BUILD_PLAN_2026-07-10.md — confirm with Yehor)

## Success criteria
1. ✅ `workflow_dispatch` publish to PyPI succeeds via OIDC Trusted Publisher.
   MET 2026-07-22 — `patchward` v0.1.0 live on PyPI, Tier-0 verified.
2. ✅ callmed-landing copy says Patchward, not RepoMend (0 grep hits). MET
   2026-07-22 — 45→0 verified; corrected files await Yehor's commit.
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
- [2026-07-21, CLOSED at session close] `webhook-reqs.txt` — Yehor
  gitignored it (commit `3ecc3e4`); confirmed untracked (`git ls-files`
  empty) and the `.gitignore` line present, both re-verified fresh at
  close. No longer an open thread.
- [2026-07-21, CLOSED at session close] `memory/Patchward_Turning-Point_Industrial-Plan_2026-07-16.md`
  mojibake — confirmed a non-issue, twice independently: this session's
  own non-ASCII character census (only legitimate `—`/`→`/`–`/`·`/`≥`/`§`/`≤`,
  no replacement characters or double-encoding artifacts) and Yehor's own
  `Get-Content -Encoding UTF8` re-read, both clean. The file was never
  corrupted; the working hypothesis (an earlier unqualified `Get-Content`
  call rendering valid UTF-8 as mojibake in a non-UTF-8 console code
  page) is plausible but is itself a Tier 1 causal claim about a prior
  command never directly observed — the file-state finding is Tier 0,
  the "why" is not.
- [2026-07-21] PR #1283 disclosure comment (unrelated repo) — not chased
  this session per standing instruction ("your pace," unrelated repo).
  Still UNVERIFIED, unchanged.
- [2026-07-21] No agent-startable code work is queued. Confirmed: the
  only remaining open BACKLOG items (8 site rename, 9 PyPI publisher
  verification, 12 CRA/GDPR legal) are all Yehor-or-external-only, same
  as every prior session's finding — nothing new surfaced this session
  to contradict that.
- [2026-07-22] Session 022 open reconfirmed HEAD fresh via two
  independent methods: `git ls-remote origin main` and a sandbox-local
  fresh clone both return `07f97d356c0e931ce0e9006b08acfd920345662f`
  ("docs: close Session 021"), matching the SHA cited at resume —
  exactly the commit chain this file already describes above, no drift.
  Fly `/healthz` fresh `WebFetch` → `{"status":"ok"}` (curl still
  blocked per H4, not a health signal).
- [2026-07-22] `memory/project_session_log.md` on the D:\ mount carries
  ~240 uncommitted lines (real Session 021-023 narrative on the webhook
  rate-limiter reorder and env-parser hardening work) not present at git
  HEAD — confirmed via `diff` against a fresh clone; git's last touch to
  that file was `793a1d0`. Narrative only, no code/config drift, not
  urgent — but this is the fact that triggered H8's promotion (see
  Heuristics). `.strategy/STRATEGY.md`, `memory/BACKLOG.md`, and
  `memory/NEXT_SESSION_START.md` were all diffed identical mount-vs-HEAD
  (no drift there).
- [2026-07-22] **BACKLOG items 8 and 9 both CLOSED this session** (see
  `memory/BACKLOG.md` for full detail). Item 9: real `workflow_dispatch`
  triggered by Yehor, `patchward` v0.1.0 published live on PyPI, Tier-0
  verified via the Actions run (both jobs green) and the actual PyPI
  release page (explicit Trusted-Publishing-from-the-right-repo
  confirmation). Item 8: `C:\Dev\Projects` connected mid-session,
  surfacing the real callmed-landing and Autonomous-Core repos for the
  first time; the "34 occurrences" estimate was DRIFTED (a line-count,
  not a word-count — real figure was 45), and the investigation caught 3
  occurrences that were actively wrong technical instructions (stale CLI
  install command, wrong branch-naming convention, wrong PyPI namespace),
  not just old branding — all corrected, cross-checked against the real
  `src/patchward/` source, written uncommitted to Yehor's working tree for
  his own review/commit. Surfaced a new, untriaged finding: ~59 internal
  "repomend" references remain in the real Patchward codebase across 15
  files (e.g. `RepomendConfig` class) — logged as new BACKLOG item 16, not
  acted on.

## Open threads
- BACKLOG 12: CRA/GDPR — external legal input, unchanged
- BACKLOG 16 (new): ~59 internal "repomend" references across 15 files in
  the real Patchward codebase (`RepomendConfig` class in `config.py`/
  `webhook.py` and others) — untriaged, needs a usage inventory before
  scoping as a real rename job
- `pending_change_cancelled` — noted in BACKLOG item 5's closing text as a
  low-priority open question (does it exist as a distinct Marketplace
  action needing the same `is_entitled()` reasoning?) — not urgent
- ssh-audit fork: 2 stale repomend/* branches, optional cleanup
- PR #1283 disclosure comment, unrelated repo — Yehor's own pace
- `memory/STATE.md` stale relative to reality — still describes the
  webhook's security posture as of commit `0bb0286`, predating the
  entire Phase 9 chain (`0c6a742` → `4b6a023` → `3d1ec08`). Low priority
  (this file already treats STATE.md as secondary, not a source of
  gating facts), flagged 2026-07-22 for whenever memory upkeep is next
  in scope — not a queued session goal unless Yehor wants it to be.
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
  **Session 022 correction — Tier 0 vs Tier 1, kept separate on purpose:**
  **Tier 0 (directly observed):** `/usr/bin/python3.13` exists in this
  sandbox right now; `uv run patchward ...` found and used it with zero
  network calls, and a real `uv run pytest --cov` executed successfully —
  `480 passed, 2 skipped, 15 deselected, 90.59% coverage`. **Tier 1
  (plausible, NOT independently confirmed):** the inference that H4's
  original diagnosis was merely *incomplete* (tested "fetch a new
  interpreter," never checked "is one already present") rather than the
  sandbox's base image having genuinely changed between sessions. Nobody
  re-ran the old failing `uv python install 3.12` command in this exact
  environment to see if it still fails the same way — both explanations
  predict the same observed outcome, so this is genuinely underdetermined
  from what was actually checked, same distinction this file already
  draws for the Session 021 mojibake finding. **Do not treat "just check
  for a local interpreter first" as a universal fix until a future session
  re-tests the old failure mode directly in this same environment.**
  **The 480-vs-483 test-count gap is now fully resolved, Tier 0:** a
  `--collect-only` diff between this sandbox (Python 3.13) and Yehor's
  machine (Python 3.14.4) found the exact 3 missing test IDs, all in
  `tests/fixture_repo/tests/test_clean.py` — not a version/platform
  marker at all, but `tests/fixture_repo`'s known bare-gitlink-with-no-
  `.gitmodules` state (BACKLOG 7d): a plain `git clone` in the sandbox
  leaves that submodule directory empty, so those 3 tests never collect
  here, while Yehor's local checkout has real content. See
  `memory/STATE.md`'s Tests section for full detail.
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
- H8 [active, PROMOTED 2026-07-22, evidence: two independent occurrences
  across two different files — Session 021 (`BACKLOG.md` +
  `NEXT_SESSION_START.md`, partial uncommitted corrections stopping short
  of true HEAD) and Session 022 (`memory/project_session_log.md`, ~240
  uncommitted lines of real Session 021-023 narrative, last touched by
  git at `793a1d0`)]: local disk can be ahead of git in ways
  `git log`/`git clone` will never show — a memory file can carry real,
  substantive uncommitted content for multiple sessions running. This is
  now a standing step, not a one-off check: at session open, diff every
  memory file on the D:\ mount against a fresh clone before assuming
  memory starts clean from the last commit. (Formerly H8-candidate,
  which required one more occurrence before promotion; that occurrence
  happened this session.)

## Failed approaches (ledger)
- [2026-07-15] Trusting sandbox `git status` for close-out verification —
  false report caught twice (Session 018, this session). Retry only if the
  mount sync mechanism verifiably changes.
- [2026-07-21] Trying to install a Python 3.12+ interpreter in-sandbox via
  `uv python install` to re-run the real test suite — blocked by H4 (403
  from the python-build-standalone release CDN). **SUPERSEDED 2026-07-22:**
  fetching a *new* interpreter is still blocked, but this session found
  `/usr/bin/python3.13` already present — `uv run pytest` used it directly
  with no network fetch and a real run succeeded (480/2/15, 90.59% cov,
  vs. Yehor's 483/2/15, 90.46% — 3-test collection gap, **RESOLVED same
  session via `--collect-only` diff: `tests/fixture_repo`'s bare-gitlink
  submodule has no content after a plain sandbox clone, see H4/STATE.md**).
  The real fix for future sessions: check for an existing compatible
  interpreter before assuming this failed approach applies; don't retry
  `uv python install` itself, that part is still blocked.

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
- [2026-07-22, Session 022 open] Verified fresh via two independent
  methods: `git ls-remote origin main` and a sandbox-local fresh clone
  both confirm HEAD `07f97d3` ("docs: close Session 021"), matching the
  SHA cited at resume exactly — 0 drift on git state. Fly `/healthz`
  fresh `WebFetch` → `{"status":"ok"}`. Diffed the D:\ mount against the
  fresh clone for `.strategy/STRATEGY.md`, `memory/BACKLOG.md`,
  `memory/NEXT_SESSION_START.md` (all identical, no drift) and
  `memory/STATE.md` (identical but stale in content — flagged in Open
  threads) and `memory/project_session_log.md` (real difference: ~240
  uncommitted lines of Session 021-023 narrative on disk, invisible to
  git). That last finding is H8-candidate's second occurrence across a
  second file → promoted to H8 (see Heuristics). BACKLOG item 5 (Phase 9)
  reconfirmed fully closed; no agent-startable code work queued — L2 goal
  is pending Yehor's choice among BACKLOG 8/9/12, none of which an agent
  can start without his or external input first. No git commits made from
  the sandbox this session; only this memory file touched, written back
  to `D:\` for Yehor's own review and commit.
- [2026-07-22, Session 022 continued] Yehor picked "9 then 8." Item 9:
  confirmed PyPI's pending-publisher environment field showed `(Any)` —
  identified as PyPI's own UI placeholder for "no restriction" (italic +
  parenthesized, not literal typed text), so no OIDC mismatch risk;
  guided Yehor through GitHub's UI to trigger `workflow_dispatch`
  (screenshots at each step); verified the result two independent ways
  (Actions run status via `WebFetch`, and the live PyPI release page) —
  real publish, real Tier-0 confirmation, not inferred. Item 8: `C:\Dev\Projects`
  got connected, re-ran Ground→Verify→Synthesize scoped to item 8 per
  Yehor's explicit request; found the "34 occurrences" figure was a
  line-count undercounting the true 45 word-occurrences, and found 3
  occurrences were stale technical claims (CLI command, branch-naming
  convention, PyPI namespace) rather than pure branding — cross-checked
  each against the real `src/patchward/` source before writing the fix,
  not paraphrased from memory. Executed the fix (case-sensitive two-pass
  swap + one manual HTML-entity-encoded correction), verified 45→0,
  delivered diffs + corrected files, wrote them uncommitted to Yehor's
  `callmed-landing` working tree. Did not commit or push either repo's
  changes — Yehor's own review stays the gate, per standing process.
- [2026-07-22, Session 022 continued] Pre-commit double-check on item 8's
  two riskiest claims, both independently verified rather than trusted
  from the diff text: (1) rendered `security.html` in real headless
  Chromium and read the actual visible text — confirmed
  `patchward/fix-<finding-id>` displays correctly, not as literal HTML
  entities; (2) ran the real `patchward --help` / `patchward fix --help`
  — confirmed the page's CLI sample (`patchward fix --repo .`) matches
  exactly. Bonus finding in the process: this sandbox has
  `/usr/bin/python3.13` already present, which `uv` used directly with no
  network fetch, enabling a real `uv run pytest --cov` — see H4 correction
  and the superseded Failed-approaches entry. Nothing committed by the
  agent this session in either repo; Yehor has the reviewed diffs and the
  commit sequence to run himself.

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

## Session log (close)
- [2026-07-21, Session 021 close] Reconciliation commits landed and
  independently re-verified: `2074db3` (memory rewrite, diffed
  byte-identical against the agent's drafts — zero corruption in the
  write→commit chain) and `3ecc3e4` (Yehor's own `webhook-reqs.txt`
  gitignore fix). Real `uv run pytest --cov` pasted from Yehor's machine
  at HEAD `3ecc3e4`: 483 passed, 2 skipped, 15 deselected, 90.46%
  coverage, Python 3.14.4 — converts the one remaining Tier 1 claim in
  the Phase 9 chain to Tier 0. Mojibake and `webhook-reqs.txt` both
  closed (see Current state / Open threads above). Full detail:
  `memory/SESSION_CLOSE_2026-07-21.md`. No further agent-startable work
  queued — next session opens by having Yehor pick among BACKLOG 8/9/12.

## Calibration record (close)
- [2026-07-21 close] Of this close's own claims (git state, commit
  content, test results, mojibake resolution): 7 fully CONFIRMED via a
  method independent of the in-chat report (fresh `git ls-remote`/`fetch`,
  byte-diff of committed vs. drafted content, `.gitignore`/`git ls-files`
  checks), 1 PARTIALLY confirmed (the file-clean finding is Tier 0; the
  specific causal story for the earlier garbled read stays Tier 1,
  correctly labeled as inference, not fact). Roughly 7.5/8 (~0.94) —
  a real recovery from the open's 0.75, and consistent with that 0.75
  being the audit getting more rigorous rather than the project getting
  less reliable: the one open-session drift (mojibake) is now resolved
  as a genuine non-issue, and the two open-session unverified items
  (real pytest run, mount-noise trick) resolved to one real Tier-0
  confirmation and one correctly-avoided-not-needed. No heuristic
  promotions this close — H8-candidate (uncommitted local reconciliation
  drafts) had no second occurrence to test against this close, stays a
  candidate at 1 occurrence.

- [2026-07-22 open] Of 5 checkable claims (git HEAD match via ls-remote,
  git HEAD match via fresh clone, Fly health, mount-vs-clone drift check
  across 5 memory files, H8-candidate's second-occurrence status): 5/5
  CONFIRMED, each via a method independent of the in-chat/resume-prompt
  report (ls-remote + fresh clone as two separate confirmations of the
  same SHA; fresh WebFetch for Fly; direct `diff` for every mount-vs-HEAD
  comparison). 1.00 on checkable claims. One heuristic promoted
  (H8-candidate → H8) on real second-occurrence evidence, not asserted.

- [2026-07-22, Session 022 continued] Of the execution-phase claims (PyPI
  environment-field reading, workflow_dispatch result, PyPI release-page
  content, item 8's occurrence count, the 3 technical corrections' factual
  basis): all CONFIRMED via a method independent of the initial read in
  each case — the `(Any)` reading was corroborated by the actual publish
  succeeding with no identity-mismatch error (if the reading had been
  wrong, the real-world publish would have failed, and it didn't); the
  Actions run and the PyPI release page are two separate, independently
  fetched sources agreeing with each other; the 45-occurrence count was
  verified by a different grep invocation (`-o` vs `-c`) than the one that
  produced the original "34" estimate; each of the 3 technical corrections
  was checked against the real source file, not asserted from the prior
  session's or Autonomous-Core's description. 1.00 on checkable claims —
  no drift found in this execution phase itself (the drift was in the
  *prior* estimate this phase was verifying against, correctly caught).

- [2026-07-22, Session 022 pre-commit check] Of 3 checkable claims (branch-
  naming line renders as visible text not raw entities; CLI sample matches
  real `--help` output; H4's "no compatible Python in-sandbox" premise):
  2 CONFIRMED via a method independent of the diff text itself (real
  headless-Chromium render, real `--help` invocation), 1 DRIFTED —
  H4's blanket "real pytest runs stay Yehor-machine-only" turned out to
  be broader than the evidence supported; a compatible interpreter was
  present all along, just never checked for. 1.00 on the claims this
  check was actually scoped to; the H4 drift is scored separately since
  it was a standing heuristic being corrected, not a claim from this
  session's own opening brief.

- [2026-07-22, Session 022 final check] The 480-vs-483 test-count gap,
  opened UNVERIFIED-why in the prior entry: bounded, closed-scope
  `--collect-only` diff (this sandbox's Python 3.13 output vs. Yehor's
  Python 3.14.4 output, both generated the same way, staged and diffed
  directly rather than eyeballed) found exactly 3 missing test IDs, all in
  `tests/fixture_repo/tests/test_clean.py` — root cause CONFIRMED (not
  inferred): that submodule is a bare gitlink with no `.gitmodules`, so a
  plain `git clone` in the sandbox leaves it empty. Not a Python-version
  or platform marker, as originally guessed — a known, pre-existing
  submodule-checkout gap (BACKLOG 7d). 1.00 on this check's own claim
  (exactly 3 IDs, exact file, confirmed empty directory) — genuinely
  closed, not left dangling. Also worth noting for calibration: the
  original hypothesis going in ("likely a skipif marker on version/
  platform") was wrong, but the check was structured to catch that (step
  4's "if no marker explains it, stop and flag, don't guess further") —
  correctly wouldn't have papered over a wrong guess if the collect-only
  diff hadn't found a clean, complete explanation.
