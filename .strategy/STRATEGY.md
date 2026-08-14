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

- [2026-07-23] Session 023 open verified fresh via methods independent of
  the resume prompt and of each other: (1) `git ls-remote origin main` →
  `0def73afd058c873ca4622ed4f27ab3c9f8177c4`, one commit past the
  `5c5a479` that `NEXT_SESSION_START.md` cited as "last known" — expected
  self-reference gap per H2 (that final commit is the one that landed the
  very file being read), not real drift; confirmed via a second, separate
  fresh `git clone`'s `git log` showing the same commit as
  `docs: close Session 022 - items 8/9 shipped, item 16 logged, H4
  corrected, test-gap resolved`. (2) Diffed all 5 memory files (this
  file, `BACKLOG.md`, `STATE.md`, `NEXT_SESSION_START.md`,
  `project_session_log.md`) on the D:\ mount against that fresh clone —
  byte-identical, zero uncommitted drift (H8 check, clean this time). (3)
  Fly `/healthz` fresh `WebFetch` → `{"status":"ok"}`. (4) PyPI: the
  `pypi.org/project/patchward/` HTML page 404'd under `WebFetch` (likely
  bot/robots blocking, not a package-removal signal — `pypi.org/pypi/.../json`
  was explicitly `ROBOTS_DISALLOWED`), so used a genuinely different
  method instead: `pip index versions patchward` from sandbox bash, which
  found `0.1.0 Requires-Python >=3.12` as an ignored-but-listed version —
  confirms the package is live on PyPI without needing the blocked HTML
  route. (5) callmed-landing: fresh `WebFetch` of the live
  `callmedai.com` confirms 0 "RepoMend" mentions, "Patchward" branding
  present, and the exact corrected CLI line (`uv tool install patchward`)
  — the Session 022 fix is confirmed deployed and stable one day later,
  closing the loose end `NEXT_SESSION_START.md` flagged (item 4 of its
  housekeeping list); the specific git hash for that private repo remains
  unconfirmed from this sandbox (no credentials), same limitation as
  before, but the live-content match is now itself a second day of
  confirmation. (6) Test suite: ran a real `uv run --python 3.13 --extra
  webhook pytest --cov` in a **brand-new fresh clone in a brand-new
  sandbox instance** (not the same container as any prior session) →
  `480 passed, 2 skipped, 15 deselected, 90.59% coverage` — exact match to
  Session 022's sandbox figure, now independently reproduced in a second,
  unrelated sandbox instance (strong evidence this is a stable, real
  result and not an artifact of one container's state), and still
  consistent with Yehor's own-machine 483/90.46% given the known
  fixture_repo submodule gap (BACKLOG 7d). (7) BACKLOG item 16: fresh
  `grep -rli "repomend" src/ tests/` and `grep -rno -i "repomend" src/
  tests/ | wc -l` in the fresh clone reproduced **exactly 15 files, 59
  occurrences**, matching the file list `BACKLOG.md` already named — no
  drift in this claim either. Went further than re-verifying the count:
  checked whether `RepomendConfig` is public API before scoping a rename
  — it is **not** exported from `src/patchward/__init__.py` (which only
  defines `__version__`), not in any module's `__all__`, not referenced
  from `README.md` or any `docs/` file except one internal design doc
  (`docs/intake_phase5.md`), and no test or source file imports it via a
  top-level `from patchward import RepomendConfig` pattern — only via
  `from patchward.config import RepomendConfig`. This is new triage
  information beyond what `BACKLOG.md` item 16 already said, and it
  points toward "safe, internal-only rename" rather than "breaking
  change," pending Yehor's go-ahead to execute (see Open threads).
- [2026-07-23, CLOSED] **BACKLOG item 16 executed and pushed, Tier-0
  verified at close.** `main` @ `e4f3cca0684ea04654094e0cb0620664151f1f32`
  ("docs(memory): close BACKLOG 16, log item 17"), confirmed via fresh
  `git ls-remote` and a fresh `git clone` whose file content is
  byte-identical to what this session authored — see the Session 023
  CLOSE entry in Session log for the full verification chain, including
  one real finding (the D:\ mount's `.strategy/STRATEGY.md` had regressed
  to pre-session content after the push — fixed this close, see
  H9-candidate; a matching claim about `BACKLOG.md` was itself corrected,
  see the CORRECTION entry — that file was fine all along). New BACKLOG 17
  tracks the deferred scanner-image rebuild.
- [2026-07-24, Session 024 open] Verified fresh via methods independent of
  the resume prompt: (1) `git ls-remote origin main` → `3e63587306d6...`,
  matching the resume prompt's cited last-known hash exactly (the
  mojibake-repair commit made after Session 023's own close, confirmed via
  a fresh `git clone` + `git log` showing it as `8bdcbcd`'s direct child,
  working tree clean). (2) Diffed all 6 memory files that matter
  (`.strategy/STRATEGY.md`, `memory/BACKLOG.md`, `memory/STATE.md`,
  `memory/NEXT_SESSION_START.md`, `memory/SESSION_CLOSE_2026-07-23.md`,
  `memory/project_session_log.md`) on the D:\ mount against the fresh
  clone — **byte-identical on all 6, zero drift.** This is the first
  session-open check to explicitly re-test H9-candidate (mount falling
  *behind* git after a push) since it opened at Session 023 close: it did
  **not** reproduce — `.strategy/STRATEGY.md` and `memory/BACKLOG.md` both
  matched HEAD cleanly this time. Also confirmed the mojibake-repair
  commit (`3e63587`) itself: diffed its patch, found it replaced
  Windows-1252-mis-decoded em-dashes/arrows (`вЂ”`, `в†’`) with correct UTF-8
  em-dashes/arrows and stripped a leading BOM from `.strategy/STRATEGY.md`
  — a real, now-resolved encoding corruption, not a false alarm; the
  current committed content has zero mojibake and zero BOM, confirmed via
  both pattern search and raw byte inspection of the first 3 bytes.
  (3) Fly `/healthz`: fresh `WebFetch` → `{"status":"ok"}`; a direct bash
  `curl` attempt failed with a proxy-level 403 (H4-consistent, not a health
  signal). (4) PyPI: `pip index versions patchward` again showed
  `0.1.0 Requires-Python >=3.12` filtered out by this sandbox's Python
  3.11.15 — but this session went one step further than prior sessions and
  fetched `pypi.org/simple/patchward/` directly (bypasses this sandbox's
  proxy allowlist, which includes `pypi.org` in `no_proxy`) → HTTP 200,
  explicitly listing the `patchward-0.1.0` wheel and sdist — a stronger,
  more direct confirmation than `pip index`'s filtered-list inference.
  (5) BACKLOG 16/17/12 status all reconfirmed unchanged from
  `NEXT_SESSION_START.md`'s framing: 16 closed and pushed, 17 logged and
  deliberately not started, 12 still open pending counsel. The two
  optional-cleanup straggler files (`BACKLOG16_rename.patch`,
  `collected_314.txt`) flagged at Session 023 close are already gone from
  the working tree (confirmed via device listing) — cleanup done, no
  action needed.
- [2026-07-24, Session 024 continued] Yehor picked BACKLOG 12 over a pure
  housekeeping pass, with a specific, well-reasoned rationale: item 12 is
  the only unchecked pre-distribution gate item with real calendar-time
  lead (finding + engaging counsel), and his launch window (2026-09-08 to
  2026-09-11) lands close to the CRA's own timeline. He reframed the item
  from one indivisible "needs counsel" block into an agent-startable
  technical briefing-packet task (data inventory, product-facts sheet,
  question list, draft disclaimer, fresh CRA-timeline re-verification)
  plus a legal-determination remainder that stays counsel-only — with a
  hard rule to keep those separate and never let the agent hedge toward a
  legal conclusion. Executed via real source reads (not paraphrase): full
  field-by-field inventory of `installations_db.py`'s three tables,
  confirmed a genuine retention gap (`marketplace_purchases` has no
  deletion path at all — logged as new BACKLOG item 18); traced
  `fix_gen.py` + `credential_proxy.py` and found the existing "only the fix
  prompt reaches the Anthropic API, scrubbed of credentials" description is
  **not accurate as stated** — real repository source code reaches
  Anthropic via the Fix-Gen subagent's `read_file` tool results, and
  `CredentialProxy.scrub()` is called exactly once in the whole codebase
  (`cli.py`, on CLI/log output), never on anything actually sent to
  Anthropic — a real, source-verified correction, not an assumption. CRA
  timeline re-verified via the European Commission's own CRA pages
  (near-primary, not just re-asserting `BUILD_PLAN`'s original
  secondary-sourced figure): confirmed 24h/72h/14-day Article 14 reporting,
  binding 2026-09-11, AND surfaced a nuance prior memory didn't carry —
  that date is specifically the reporting-obligation date, distinct from
  the CRA's full conformity-assessment applicability date (2027-12-11).
  Annex III category examples and the open-source-exemption threshold test
  were explicitly left as open questions for counsel (sources found were
  secondary and/or admitted the question was unresolved), per the session's
  hard rule against hedging toward a legal conclusion. Delivered:
  `memory/BACKLOG12_counsel_briefing_packet_2026-07-24.md` (packet),
  `memory/BACKLOG.md` updated (item 12 status proposal + new item 18) —
  both written uncommitted to Yehor's D:\ working tree via SendUserFile +
  device-bridge write, same standing process as prior sessions' code/doc
  deliverables. No git commits made from the sandbox. Incidental, honestly
  flagged, out-of-scope finding noticed while reading source for the
  packet: `README.md` still says "Patchward is not yet published to PyPI"
  — stale since the 2026-07-22 PyPI publish; not fixed this session since
  it wasn't the assigned task, just noted rather than silently ignored.
- [2026-08-11] **A dedicated Patchward product site now exists and is
  live**: `patchward.dev`, served from a NEW sibling repo
  `D:\Dev\Projects\patchward-landing`
  (`github.com/yehorcallmedai-maker/patchward-landing`, HEAD `fcc0af4`),
  deliberately kept out of this repo per the same out-of-repo precedent as
  tax/FixProve/Zerkalnya artifacts. Cloudflare Pages Custom Domain status
  "Active"/"SSL enabled", confirmed by live fetch at Session 033 close —
  a canonical `facts.yaml` is the single source of truth for every number
  the site states. Full detail: `memory/SESSION_CLOSE_2026-08-11.md`.

## Open threads
- BACKLOG 20: CLOSED same day as a false alarm — see `memory/BACKLOG.md`
  item 20. The site is genuinely correct and live at the plain URLs,
  confirmed via a real browser read. Retained here only as a pointer, not
  as an open item — nothing pending.
- The ~57-file "CRLF-only diff" flagged repeatedly this session (`git
  diff --stat -w` → 0, so real content was never at risk) is **only
  visible through `device_bash`'s view of the mount** — Yehor's own `git
  status --short` on his real machine, run at final close, shows zero
  modified files, only the two already-known untracked items. This is
  consistent with the sandbox's own git config (likely `core.autocrlf`)
  normalizing line endings differently than Yehor's local git, not a real
  discrepancy in the repository. **No `.gitattributes` fix is needed on
  Yehor's side** — that suggestion applied to what looked like a repo-wide
  issue but was actually confined to how this sandbox's `device_bash`
  reads the mount. Downgrade this from "low-priority cleanup for Yehor" to
  "harmless artifact of the sandbox's own tooling, no action for anyone."
- BACKLOG 12: CRA/GDPR — briefing packet delivered AND pushed 2026-07-24
  (Session 024, `main` @ `36b0a65`), corrected twice against re-verified
  source before pushing; still genuinely open pending Yehor finding and
  engaging qualified counsel — ~7 weeks to the 2026-09-11 reporting-
  obligation date. See Current state above and
  `memory/BACKLOG12_counsel_briefing_packet_2026-07-24.md`
- BACKLOG 19 (NEW, Session 024, pushed with `36b0a65`): the webhook path's
  `git clone` persists `GITHUB_TOKEN` into the cloned repo's `.git/config`
  in plaintext for the run's duration, and four log/echo sites forward
  unfiltered git subprocess stdout/stderr with no scrubbing. Agent-
  startable. **Yehor's own call: recommend treating as a pre-launch
  consideration, not "logged, no urgency" like 18** — it sits on the
  hosted webhook path he's about to put in front of paying Marketplace
  customers. See `memory/BACKLOG.md` item 19 for the full trace and
  proposed fix.
- BACKLOG 18 (NEW, Session 024): `marketplace_purchases` has no
  retention/TTL policy — no deletion path exists in the codebase at all.
  Agent-startable, low urgency, cheap fix once prioritized — see
  `memory/BACKLOG.md` item 18 for the proposed approach.
- Housekeeping, Session 024 close: a stray, empty `.git/index.lock` was
  left in the Patchward mount by this close's own read-only verification
  commands (`device_bash` can't remove it). Confirm it's gone before the
  next git operation there — same one-line fix as the mid-session
  commit-lock incident.
- Memory hygiene: `.strategy/STRATEGY.md` has accumulated duplicate
  "Session log (continued)" / "Calibration record (continued)" headers
  instead of single append-only sections, and at least one entry is filed
  under "Calibration record" that is really session narrative. Not urgent,
  but worth a consolidation pass next time memory upkeep is in scope —
  flagged at Session 024 close, not fixed (too risky to restructure in the
  same pass as the session's substantive work).
- Pattern worth watching, not yet a heuristic (needs a second session's
  evidence per this file's own promotion rule): Session 024 caught two of
  its own introduced errors before they shipped durably (a wrongly-cleared
  "accurate" paragraph, and an overclaimed "no network access" phrase) —
  both mid-correction-pass, both caught by Yehor's own re-read rather than
  the session's own review catching them first. If a future session shows
  the same pattern (self-introduced error caught only by the user's
  independent re-read, not the session's own check), promote to a
  heuristic: re-read your own just-written correction with the same
  skepticism applied to the original defect, not just proofread it.
- BACKLOG 17 (NEW, Session 023): rebuild `patchward-scanner` image, re-pin
  its digest in `docker_sandbox.py`, then drop the transitional legacy
  `REPOMEND_NETWORK_POLICY` env var and rename the image tag
  (`repomend-scanner:0.1.0`) and entrypoint binary
  (`/usr/local/bin/repomend-entrypoint`). Directing-Engineer action, not
  agent-startable — a rebuild pulls current dependency versions
  (`semgrep`/`bandit`/`pip-audit`/`eslint`), which needs its own
  before/after scan-result sanity check, not something to trigger as a
  side effect of a naming cleanup. See `memory/BACKLOG.md` item 17 for the
  exact steps. No urgency — the dual-name transitional design is safe
  indefinitely until this lands.
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

- [2026-07-23, Session 023 open] Verified fresh (see Current state above
  for full detail): git HEAD, all 5 memory files' clean/mount-vs-clone
  state, Fly health, PyPI liveness (via a method independent of the one
  that 404'd), callmed-landing live content, a full independent sandbox
  pytest run, and BACKLOG item 16's occurrence count — all CONFIRMED, 0
  drift. Went beyond re-verification to do new triage work: confirmed
  `RepomendConfig` is not public API (not exported, no external doc/
  README exposure), which is new information that de-risks BACKLOG item
  16 as an execution candidate. L2 goal proposed: triage-plus-execute
  BACKLOG item 16 (the `RepomendConfig`/internal-repomend rename) pending
  Yehor's go-ahead, per `NEXT_SESSION_START.md`'s own framing of it as
  "agent-startable once he says go."

- [2026-07-22, Session 022 CLOSE] Formal close-out run via the
  `session-close` skill, explicitly instructed NOT to trust any hash or
  "confirmed" claim from the conversation transcript. Result: Patchward's
  `origin/main` = `5c5a4790f73e9d0f10163ccf0feea8f738da3cae`, independently
  re-verified via fresh `git ls-remote` (matched the transcript's claim
  exactly) AND a fresh `git clone` whose `.strategy/STRATEGY.md`,
  `memory/BACKLOG.md`, `memory/STATE.md` are byte-identical to this
  agent's own authored drafts — zero corruption end to end.
  `memory/project_session_log.md`'s "missed in prior commit" follow-up fix
  (`5c5a479`) also confirmed: file size/content in the fresh clone matches
  exactly what was already sitting uncommitted on the D:\ mount pre-fix.
  **callmed-landing's claimed hash (`75f1a7b79ed635fa296cec3d890346e1d9860fab`)
  could NOT be independently confirmed** — `git ls-remote` from this
  sandbox failed with "could not read Username... terminal prompts
  disabled" (private repo, no credentials here). Used a different,
  genuinely independent method instead: fresh `WebFetch` of the live
  `callmedai.com` site — confirms 0 "RepoMend" mentions, "Patchward"
  branding present, and the exact corrected CLI line
  (`uv tool install patchward`). This proves the *deploy*, which is
  arguably more meaningful than the hash, but the specific commit hash
  itself stays UNVERIFIED by this agent — flagged plainly rather than
  assumed from the conversation's own claim, per H2/H3. Also flagged, not
  chased: the "hanging credential-prompt push cancelled without
  diagnosis" incident was never independently observed by this agent,
  only reported secondhand — the clean end-state is confirmed, the
  incident's mechanics are not. Full close-out: `memory/SESSION_CLOSE_2026-07-22.md`.
  `memory/NEXT_SESSION_START.md` rewritten clean (not another addendum
  layer — flagged explicitly as a deliberate full rewrite, not silent,
  since this file had grown to 210 lines of nested corrections and this
  file already carries the full historical ledger).

- [2026-07-22 close] Of 9 checkable claims at close (Patchward hash via
  ls-remote, Patchward hash via fresh clone, 3 memory files byte-identical,
  project_session_log.md fix verified, working tree cleaned of tax files,
  Fly health, PyPI page, callmed-landing live-site content, callmed-landing
  exact hash): **7 CONFIRMED** via a method independent of the conversation's
  own claims, **1 CONFIRMED via single-method only** (working-tree cleanliness
  — device listing is the only check available, appropriately flagged as
  such rather than treated as equal-strength to the dual-method checks),
  **1 UNVERIFIED** (callmed-landing's exact commit hash — genuinely
  blocked by lack of sandbox credentials to a private repo, not a
  shortcut). **~0.94 on checkable claims (8.5/9-ish, treating the
  single-method one as partial credit)** — consistent with this project's
  pattern of closes scoring higher than opens (stricter checking applied
  earlier in the session pays off at close) and, more importantly, this is
  the first close where an UNVERIFIED item was caused by a genuine
  environment limitation (no auth to a private repo) rather than a method
  choice that could have been better — worth distinguishing from
  "should have checked harder" style gaps in future calibration. No new
  heuristic promotions this close (H8 was already promoted mid-session,
  correctly not re-promoted twice); H4's correction stands as logged
  mid-session, carried through the close unchanged.

- [2026-07-23 open] Of 7 checkable claims (git HEAD via ls-remote, git
  HEAD via fresh clone, memory files clean vs. mount, Fly health, PyPI
  liveness, callmed-landing live content, BACKLOG 16 occurrence count):
  **7/7 CONFIRMED**, each via a method independent of the resume prompt's
  own claims (ls-remote + a second fresh clone for HEAD; direct `diff`
  for memory cleanliness; fresh `WebFetch` for Fly; `pip index versions`
  for PyPI after the more obvious `WebFetch` route was blocked by
  robots.txt/bot-detection, not treated as a dead end; fresh `WebFetch`
  for callmed-landing; fresh `grep` for BACKLOG 16). **1.00 on checkable
  claims.** The test-suite figure (480/2/15/90.59%) is not counted as one
  of the 7 above since it wasn't an explicit STRATEGY.md claim this
  session opened with, but it independently reproduced Session 022's
  sandbox figure exactly in an unrelated sandbox instance — a strong,
  unprompted corroboration worth noting for calibration even though it
  wasn't itself "graded." No heuristic promotions or demotions this
  open — H1/H2/H4/H8 all behaved exactly as documented, no surprises.

- [2026-07-23, Session 023 continued] Yehor confirmed BACKLOG item 16 as
  the L2 goal, then pushed back twice on the scope before agreeing to
  execute — both times with a substantive technical point, both times
  checked directly against source rather than taken on trust: (1) asked
  whether any of the 59 references cross a serialization/deployment
  boundary, given Patchward is now a live webhook + published package, not
  just a library — a full literal-quoted-string grep (not just the
  identifier grep already done) found exactly one that does
  (`REPOMEND_NETWORK_POLICY`), plus a second, lower-stakes one found
  independently while checking (`REPOMEND_FIXTURE_REPO`, test-only). (2)
  asked about fail-open-vs-fail-closed and image-rebuild skew for that env
  var specifically — traced both directly: `docker/entrypoint.sh` applies
  `iptables -P OUTPUT DROP` unconditionally and only ACCEPTs on an exact
  string match, so a mismatch is fail-closed, never fail-open; and
  `docker_sandbox.py`'s `BASE_IMAGE` is a digest-pinned, manually-rebuilt
  image (built 2026-06-12), so skew during a naming transition is real but
  safe-direction. Executed on that basis: 58 pure-identifier occurrences
  renamed (`RepomendConfig` → `PatchwardConfig` across 12 files, 2 test
  function names, `REPOMEND_FIXTURE_REPO` → `PATCHWARD_FIXTURE_REPO`), the
  one boundary-crossing var handled via a transitional dual-set/dual-read
  rather than a straight rename (both names live until BACKLOG 17's image
  rebuild lands), and the Docker image tag/binary name deliberately
  deferred to that same item 17 rather than bundled in. Full detail in
  `memory/BACKLOG.md` item 16 (now marked EXECUTED) and new item 17.
  Verification: a real `uv run --python 3.13 --extra webhook pytest --cov`
  after all edits reproduced the exact same `480 passed, 2 skipped, 15
  deselected` counts as this session's own pre-edit baseline (90.60% vs.
  90.59% coverage, +1 statement from added comment lines) — the rename
  broke nothing, confirmed by re-running the suite, not by inspection
  alone. A final full-repo grep confirmed zero remaining case-insensitive
  "repomend" hits outside the deliberately-deferred set (docker image
  tag/binary name, `.bandit`/`.env.example` comment-level branding, and
  historical `memory`/`reports`/`runs` artifacts — none of which are code
  BACKLOG 16 was ever scoped to touch). No git commits made from the
  sandbox — all 17 changed files written uncommitted to Yehor's D:\
  working tree, plus a `.patch` file, for his own line-by-line review and
  commit, same standing process as items 8/9.

## Calibration record (continued)
- [2026-07-23, Session 023 execution phase] Of the claims made during
  execution (59-vs-58-vs-1 classification, fail-closed behavior, digest-pin
  skew possibility, post-edit test counts, final zero-remaining-references
  grep): **all 5 CONFIRMED** via a method independent of assertion — the
  classification via an actual literal-string grep (not inferred from the
  identifier grep alone), fail-closed via reading the real `entrypoint.sh`
  iptables sequence line by line, digest-pinning via the real `BASE_IMAGE`
  constant and its comment, test counts via an actual full-suite re-run
  post-edit, and the final grep via a real repo-wide search after all
  edits landed. 1.00 on checkable claims. Worth noting for calibration:
  this is the first session where the *user's own claims* (raised as
  pushback on a proposed plan, not as memory-file content) were the thing
  under verification, rather than a memory file or a prior session's
  report — the two-pass discipline applied the same way regardless of
  source, per H3's spirit (Tier 2 sources are leads, not gating facts,
  whether they come from another project's memory file or from a
  question asked mid-session).

- [2026-07-23, Session 023 CLOSE] Yehor reported committing and pushing the
  staged BACKLOG 16 work himself in three commits and pasted a PowerShell
  transcript plus a summary narrative claiming this was `git ls-remote`
  confirmed. Per this project's own standing rule (never trust a reported
  hash or transcript without re-verifying), ran a full independent
  close-out rather than accepting the narrative. **Findings:**
  (1) `git ls-remote origin main` from a fresh sandbox process →
  `e4f3cca0684ea04654094e0cb0620664151f1f32` — matches the reported hash
  exactly, Tier 0. (2) A fresh `git clone` shows the 3 commits exactly as
  described (`171ccf8` rename, `a979741` dual-env-var, `e4f3cca` memory) —
  diffed all 17 changed source/config/docker files plus `memory/BACKLOG.md`
  against this session's own authored drafts: **byte-identical, zero
  corruption**, confirming the push carried exactly what was staged, not a
  reconstruction. (3) The "commit gap" Yehor's own narrative flagged as
  worth checking (last hash this conversation had confirmed, `5c5a479`,
  vs. the claimed parent `0def73a`) does **not exist** — `git log --oneline
  5c5a479..0def73a` returns only `0def73a` itself, i.e. `0def73a` is
  `5c5a479`'s direct child. This was a drift in the narrative, not in the
  repo; corrected here for the record, not chased further since it doesn't
  change anything material. (4) A real `uv run --python 3.13 --extra
  webhook pytest --cov` against the actual pushed HEAD (not the pre-push
  staged copy) reproduced `480 passed, 2 skipped, 15 deselected, 90.60%
  coverage` exactly — confirms the merge didn't regress anything, checked
  by running the suite again, not by re-reading the diff. (5) **Real
  finding, not a rubber-stamp:** diffing the D:\ mount's *current* files
  against this verified HEAD turned up a genuine divergence, isolated to
  exactly 2 of the 17 changed files — `memory/BACKLOG.md` and
  `.strategy/STRATEGY.md` on Yehor's own disk right now still show the
  **pre-Session-023** content (the old, not-yet-triaged BACKLOG item 16,
  and a STRATEGY.md with zero Session 023 entries at all), while GitHub's
  HEAD has the full, correct Session 023 content byte-identical to what
  this agent authored mid-session. All 15 non-memory changed files (every
  `.py`, `docker/entrypoint.sh`, `docker/scanner.Dockerfile`) matched HEAD
  exactly on the mount — the divergence is isolated to these 2 memory
  files specifically, consistent with something (most plausibly an editor
  buffer open on the old content, autosaved after the commit) reverting
  just the files that were open for review. **This is the mirror image of
  H8**: not local-ahead-of-git (real uncommitted work at risk of being
  lost), but local-*behind*-git (the good content is already safely
  pushed, but the local working tree doesn't reflect it) — lower risk
  since nothing is lost, but a real hazard if left alone: a future blind
  `git add -A` from this state would stage a *revert* of Yehor's own
  memory update. Fixed directly this close: both files rewritten on the
  mount to match verified HEAD content plus this close-out's own
  additions, so the mount and git agree again as of this write. (6) Minor,
  non-blocking observation: all three of Yehor's commits carry the
  identical author timestamp (`Thu Jul 23 15:20:05 2026 +0200` down to the
  second) — mechanically inconsistent with the interactive, sequential
  `git add`/`git status`/`git commit` sequence narrated in the pasted
  transcript (each step should take at least a few real seconds). Flagged
  per H7's spirit (verify the mechanics, don't just accept the narrative)
  — does not change that the *end state* is fully verified correct; only
  the *process* narrative doesn't quite match the evidence, similar to
  Session 022's unverified "hanging credential-prompt" incident mechanics.
  (7) callmed-landing live site re-confirmed a third time (0 "RepoMend", 
  "Patchward" present, exact CLI line) — stable across sessions. (8)
  Working-tree stragglers reconfirmed via device listing, all correctly
  untracked and non-blocking: `webhook-reqs.txt` (gitignored, as designed),
  `collected_314.txt` (pre-existing, unrelated to this session),
  `BACKLOG16_rename.patch` (this session's own delivered patch file, now
  redundant since the rename landed — safe to delete). Full close-out:
  `memory/SESSION_CLOSE_2026-07-23.md`.

- [2026-07-23, Session 023 close, CORRECTION] The finding above overstated
  the divergence. Yehor ran his own `git status` directly on his machine
  (ground truth, not through this agent's device-bridge tools) and it
  showed only `.strategy/STRATEGY.md` as modified — **`memory/BACKLOG.md`
  was NOT modified, i.e. it matched HEAD all along.** This agent's own
  bridge-based diff had reported both files as reverted; that BACKLOG.md
  half of the finding was itself wrong, almost certainly a stale-cache
  read on this agent's side coinciding with the device bridge's
  disconnect/reconnect around the same time — H1's own warning ("mount
  reads can serve stale content") applying to this agent's tooling, not
  just to a hypothetical. The STRATEGY.md divergence was real (confirmed
  independently by Yehor's own `git status`, not just this agent's read).
  Corrected here rather than silently fixed in the original entry, per
  this project's own "never launder history" rule. Yehor ran
  `git checkout HEAD -- .strategy/STRATEGY.md memory/BACKLOG.md` himself
  to reset both (the BACKLOG.md checkout was a harmless no-op given it
  already matched); this agent then re-applied the close-out's additional
  entries on top of that verified-correct base and re-delivered.

## Heuristics (earned) — candidates
- H9-candidate [1 occurrence, Session 023 close, narrowed on correction]:
  after Yehor reports committing/pushing memory-file changes, independently
  diff the D:\ mount's *current* copy against a fresh clone of the pushed
  HEAD — not just `git ls-remote` for the hash, AND prefer Yehor's own
  direct `git status`/`git diff` output over this agent's device-bridge
  reads when the two disagree, since the bridge itself can serve stale
  content (see the correction entry above). A successful push does not
  guarantee the local working tree still reflects what was committed;
  something (an editor autosave on a stale buffer is the leading suspect)
  can revert a file back to its pre-session content on disk after the
  commit already landed safely — confirmed for `STRATEGY.md` specifically
  this session, not for `BACKLOG.md` (that part of the original finding
  was a bridge-read artifact, not a real revert). This is the mirror image
  of H8 (local ahead of git, real work at risk) — here local fell
  *behind* git after a genuine push, lower-risk since nothing is lost, but
  still worth catching before the next session assumes the mount reflects
  reality. Needs one more genuine occurrence, per this project's own
  promotion bar (see H8's history), before promotion to a standing
  heuristic.

## Calibration record (continued)
- [2026-07-23 close] Of 8 checkable claims (reported hash via ls-remote,
  reported hash via fresh clone, 3 commits' diff content vs. this session's
  authored drafts, the flagged commit-gap question, post-merge test suite,
  mount-vs-HEAD consistency for all 17 changed files, callmed-landing live
  content, working-tree straggler status): **7 CONFIRMED** via a method
  independent of the user's own narrative, **1 DRIFTED** — the mount-vs-
  HEAD check (finding #5) initially reported both `BACKLOG.md` and
  `STRATEGY.md` as reverted; not because this session's own work was
  wrong, but because local disk had regressed after the push (real for
  STRATEGY.md) combined with a stale bridge-read on this agent's own side
  (the BACKLOG.md half — corrected once Yehor's own direct `git status`
  disagreed with this agent's read and was trusted over it). Scored as a
  drift caught, not a miss: the point of this close's rigor was to catch
  exactly this class of problem, and — with a second layer of "trust the
  user's direct tool output over your own bridge read when they
  disagree" — it did, including catching this agent's own partial
  over-claim. **0.94 on checkable claims (7.5/8)** — consistent with this
  project's pattern that closes run stricter checks than the narratives
  they're checking, and, this time, stricter than this agent's own first
  pass too. No heuristic promoted this close (H9-candidate needs a second
  genuine occurrence — this session supplies one confirmed instance,
  narrowed to STRATEGY.md only); no heuristic demoted; H1/H2/H3/H7/H8 all
  behaved exactly as documented, with H1's scope now explicitly understood
  to include this agent's own device-bridge reads, not just local git
  reads against the mount.

## Session log (continued)
- [2026-07-24, Session 024 open] Verified fresh: git HEAD (`3e63587`,
  matching resume prompt exactly), all 6 memory files clean vs. a fresh
  clone (H9-candidate re-tested, did not reproduce this session), Fly
  health, PyPI liveness (via a second, more direct method than prior
  sessions — a raw `pypi.org/simple/patchward/` fetch, not just
  `pip index`), and BACKLOG 16/17/12 status. 0 drift. Confirmed the
  mojibake-repair commit (`3e63587`) fixed a real Windows-1252
  mis-decoding + stray BOM in `.strategy/STRATEGY.md` and
  `memory/NEXT_SESSION_START.md` — not a false alarm, and clean now by
  direct byte inspection. Full detail in Current state above.
- [2026-07-24, Session 024 continued] Yehor chose BACKLOG 12 over pure
  housekeeping, reframed it into an agent-startable briefing-packet task
  plus a counsel-only remainder, and the agent executed the packet: data
  inventory (with a genuine retention-gap finding, new BACKLOG 18), a
  corrected data-flow fact about what reaches Anthropic (verified against
  real source, not assumed), a question list, a draft disclaimer, and a
  freshly re-verified CRA timeline with a nuance prior memory lacked
  (reporting-obligation date vs. full-applicability date). BACKLOG 12
  updated to "briefing packet ready, awaiting counsel" — not closed, since
  the actual legal determination remains genuinely blocked on Yehor
  engaging counsel. Full detail in Current state above and
  `memory/BACKLOG12_counsel_briefing_packet_2026-07-24.md`. No git commits
  made from the sandbox; packet + updated `BACKLOG.md` written uncommitted
  to Yehor's D:\ working tree for his own review.

## Calibration record (continued)
- [2026-07-24 open] Of 4 checkable claims (git HEAD via ls-remote+clone,
  all 6 memory files clean vs. fresh clone including the H9-candidate
  re-test, Fly health, PyPI liveness): **4/4 CONFIRMED**, each via a method
  independent of the resume prompt's own claims. PyPI's confirmation this
  session used a genuinely stronger method than prior sessions (a direct
  `pypi.org/simple/` fetch bypassing this sandbox's proxy allowlist,
  rather than relying solely on `pip index`'s filtered/inferred listing).
  **1.00 on checkable claims.** H9-candidate was explicitly re-tested and
  did not reproduce — this is not itself a promotion or demotion event
  (the heuristic tracks occurrences of the bug, not clean sessions), but
  is worth recording: one clean re-check after the Session 023 fix, not
  yet enough to call the fix durably proven, but no new evidence against
  it either.
- [2026-07-24, Session 024 continued] Of the execution-phase claims (the
  `installations_db.py` field inventory and retention-gap finding, the
  corrected Anthropic data-flow fact, the CRA timeline table, the
  Annex III category examples, the DPIA background criteria): the data
  inventory, retention gap, and data-flow correction are **CONFIRMED**
  directly against real source (`installations_db.py`, `webhook.py`,
  `fix_gen.py`, `credential_proxy.py`, verified via an explicit
  `grep -rn "\.scrub("` across the whole repo, not assumed from a
  docstring). The CRA timeline table is **CONFIRMED** via the European
  Commission's own pages, a near-primary source, cross-checked against a
  second independent explainer site — an improvement over the prior
  secondary-sourced-only figure. The Annex III category list and the
  open-source-exemption threshold test are correctly left **UNVERIFIED /
  OPEN**, not forced to a conclusion — sources found were secondary and,
  in the exemption case, explicitly stated the question as unresolved in
  the source material itself. **Scored as fully calibrated for this
  phase**: every claim that could be resolved from real source or a
  near-primary regulatory page was resolved that way; every claim that
  genuinely requires counsel was left open rather than hedged toward an
  answer, matching this session's own hard rule. No heuristic promoted or
  demoted this session — H1/H2/H3/H4/H7/H8 behaved as documented;
  H9-candidate stays a candidate (one clean re-check, not a new bug
  occurrence in either direction).

- [2026-07-24, Session 024 continued — correction pass] Yehor independently
  re-read the packet's own source citations and found three real problems
  with the first draft, all re-verified fresh against source before
  correcting (not accepted on his say-so, same discipline this project
  applies to every other claim): (1) the packet's "`scrub()` called in
  exactly one place" count was wrong — re-grepped and found two call sites
  in `cli.py` (L139, L304) plus one in `credential_proxy.py:27` (confirmed
  to be inside that module's own docstring example, not executable code)
  plus five in tests; the substantive conclusion the count supported (zero
  call sites in `fix_gen.py`/`subagent.py`) was unchanged and re-confirmed.
  (2) the `read_file` finding was upgraded from "the subagent has a tool it
  might use" to Tier 0, source-confirmed: the system prompts in
  `fix_gen.py` **mandate** it on every path including decline (quoted
  L224, L272, L547, L355 — the last confirming it is unrestricted within
  the worktree, not scoped to the finding's line range). (3) a second data
  path the first draft missed entirely: `subagent.py`'s triage stage (runs
  *before* Fix-Gen) has its own `read_file`/`grep_files`/`glob_files` tool
  surface (confirmed at `subagent.py:29-33` and the system prompt at
  `subagent.py:129`) — repository content can reach Anthropic at two
  independent stages, not one. Also added, newly verified rather than
  merely requested: run logs under `runs/` are ~460 bytes each (confirmed
  by directory listing showing dozens of files at that exact size) and one
  was read in full — pure status/timestamp metadata, no prompt or file
  content — so there is currently no audit trail of what was actually
  transmitted to Anthropic. All four corrections applied to
  `memory/BACKLOG12_counsel_briefing_packet_2026-07-24.md` in place (not a
  rewrite), each re-verified against real source before writing, per
  Yehor's own instruction to keep the correction pass factual and
  unsoftened.
- [2026-07-24, Session 024 continued — callmed-landing urgent fix] Yehor's
  own judgment call, stated plainly as engineering judgment and not legal
  advice: the live site's privacy/security copy claiming "raw repository
  contents are never sent externally" / "your code never leaves your
  infrastructure" / "only the fix prompt reaches the Anthropic API,
  scrubbed of credentials" directly contradicts the same source-verified
  finding above, and fixing a live, public, factually-contradicted claim
  outranks counsel engagement on urgency. `C:\Dev\Projects` (present but
  not connected at session start) was granted via
  `device_request_folder_access`, scoped narrowly to
  `C:\Dev\Projects\callmed-landing` only. Found the exact claim, verbatim,
  in three files: `index.html` (FAQ JSON-LD "What is Patchward?", the
  visible "On-premise, auditable" card, and the second FAQ entry),
  `security.html` ("On-premise execution — Patchward" and "Inference
  layer"), `privacy.html` ("Patchward — on-premise processing" and
  "Third-party processors"). Corrected all seven locations to state the
  two-stage (triage + fix-gen), unrestricted-within-worktree data flow
  accurately, while leaving three adjacent paragraphs unchanged after
  confirming they were already accurate as written: security.html's
  "Credential isolation" paragraph (correctly scopes scrubbing to
  logs/CLI output already) and privacy.html's "no repository data reaches
  our systems" line (correctly scoped to CallMed AI's own systems, true as
  written) — corrections were targeted, not a wholesale rewrite, and did
  not touch Symbiote's already-honest full-file-transmission disclosures.
  Bumped both legal pages' version markers (June 2026 v1.1 → July 2026
  v1.2) per the page's own stated "Policy changes" convention. Delivered a
  combined diff, a summary doc, and all three corrected files; written
  uncommitted to the `callmed-landing` working tree for Yehor's own review
  and one commit, same standing process as every other cross-repo
  deliverable this project has produced. Not touched: whether the site's
  own "notify active customers by email" policy clause applies here — left
  as Yehor's business decision, not fabricated.
- [2026-07-24, Session 024 continued — second correction pass + attempted
  commit] Yehor read the corrected files directly and caught a real miss:
  `security.html`'s "Credential isolation — Patchward" paragraph had been
  cleared as accurate in the first pass but wasn't — "any text generated by
  an agent... is scrubbed" is false (both real `scrub()` call sites are on
  a scanner finding's `message` field, never on agent-generated text; zero
  call sites in `fix_gen.py`/`subagent.py`). Rewrote it, and additionally
  verified (not assumed) the paragraph's other claim: `docker_sandbox.py`
  does structurally exclude credential keys from container `-e` flags and
  asserts it before every run, but that guarantee does NOT extend to the
  CLI's other subprocesses (`git` calls in `worktree_common.py`/
  `webhook.py`, the non-Docker path in `scanner.py`) — none pass an
  explicit `env=` override, so they inherit the full parent environment by
  default. Also rescoped "fully auditable" in the Three-gate paragraph
  (re-verified `run_log.py` + a real log) to describe only what the log
  actually contains. Drafted an updated `llms.txt` (previously omitted
  Patchward entirely, and used a different contact email than the rest of
  the site — flagged for Yehor to confirm, not decided unilaterally).
  **Final ground-truth sweep (via `device_bash` reading the actual file,
  not this session's cached staging path) turned up 3 more live instances
  of the same claim in `index.html`** that both prior passes had missed
  (lines 143, 178, 219) — fixed those too. **Real anomaly, disclosed rather
  than quietly resolved:** mid-pass, a check via this session's own
  file-staging path showed the first pass's edits as if reverted; a
  second, independent check via `device_bash` (reading the file directly,
  a genuinely different mechanism) confirmed the edits were present all
  along — the alarming read was stale cached content from this session's
  own initial staging step, not the actual device state. Nothing was lost.
  **Attempted commit of both repos per Yehor's own script:** `git add` of
  the exact intended files succeeded and was verified via `git status` in
  both `Patchward` and `callmed-landing` — but `git commit` failed
  identically in both repos with `Operation not permitted` unlinking
  `.git/index.lock` and temp objects. Root cause: this session's
  device-bridge VM cannot delete/unlink files on the mounted folders (a
  documented constraint of the bridge itself, confirmed via the tool's own
  behavior, not a real concurrent git process) — git's commit step needs
  to remove its own lock/temp files as part of normal operation and can't,
  through this specific channel, on this specific mount. **No partial or
  corrupt commit resulted in either repo** — `git log` in Patchward still
  shows HEAD at `3e63587` unchanged, and both repos' staging areas hold
  exactly the intended files, confirmed via `git status --short` after the
  failed commit. Neither push was attempted after the commit failure
  (network reachability to `github.com` from this same VM was also
  independently confirmed absent — a `git ls-remote` test returned "403
  from proxy after CONNECT," consistent with the cloud sandbox's own
  earlier, separate finding of restricted egress to non-allowlisted hosts,
  though this is a different network boundary — the user's local VM, not
  the cloud container). **Unrelated finding, not part of this session's
  task, not touched:** `git status`/`git diff --stat -w` in Patchward shows
  ~57 files (mostly `src/patchward/*.py`, `tests/*.py`, and old `runs/
  *.json`) with real `git diff` output but zero diff under `-w`
  (whitespace-insensitive) — pure line-ending/whitespace churn, not content
  changes; not staged, not committed, flagged for Yehor to investigate at
  his convenience (likely a CRLF/LF mismatch from a Windows-side tool).
  Both repos' actual commits and pushes remain for Yehor to run himself —
  index.lock removal + `git commit`/`git push`, same commands he provided.
- [2026-07-24, Session 024 continued — third pass: framing refinement +
  two logged-not-acted items] Yehor confirmed all three second-pass
  corrections as accurate on independent re-read, then flagged one
  remaining framing gap: `security.html`'s "Credential isolation —
  Patchward" paragraph stated correct facts but, unlike the neighboring
  "Inference layer" paragraph, didn't explain *why* the boundary sits
  where it does. Verified before writing (not assumed): `docs/
  intake_phase2.md`'s own Phase 2 test contract treats scanned repository
  content as adversarial — its "Adversarial / Break Case" section
  specifies a fixture with a destructive-command-shaped comment and a
  fake `ANTHROPIC_API_KEY=...` string embedded in scanned source, both
  required to fail to reach a credential or escape the container — and
  `architectural_decisions.md`'s ADR-013 states outright: "Threat model
  includes prompt-injection payloads." Correction to the user's own
  hypothesis, not just confirmation of it: the untrusted element is the
  *scanned repository content*, not the scanner binaries themselves —
  Semgrep/Bandit/etc. are version-pinned, vetted tools baked into a
  maintained image (ADR-014), so "third-party scanner binaries are the
  untrusted surface" slightly overstates it. Separately confirmed (
  `worktree_common.py`, `pr_publisher.py`, `github_app_auth.py`) that git
  push authentication does not rely on inherited-environment credential
  passing at all — `_build_remote_url()` embeds `GITHUB_TOKEN` directly
  into the HTTPS remote URL passed as a command argument to `git push`;
  the existing "inherits full environment" sentence is still true as a
  general subprocess fact but doesn't describe how the token itself
  reaches git. Rewrote the paragraph to add the rationale clause and
  correct this mechanism detail, without softening or removing the
  original disclosure. Delivered, not yet committed (Yehor commits).
  **Two items logged per explicit instruction, not acted on:** (1) the
  stale-cache read from the prior pass is the third distinct
  manifestation of the mount-staleness class this project has hit (H1,
  H6, H8) — not a new heuristic, H1 already covers it, but worth a
  standing note that this class recurs across different session/tool
  combinations, not just one. (2) the ~57-file CRLF/whitespace-only diff
  in Patchward (first flagged above) has now shown up as noise in
  multiple sessions this week; a `.gitattributes` with `* text=auto` would
  end it permanently — low priority, not blocking, Yehor's call on timing.
- [2026-07-24, Session 024 continued — bounded token-trace check, new
  BACKLOG 19] Before committing the amended paragraph, Yehor asked for a
  read-only trace of whether `_build_remote_url()`'s token-bearing URL is
  ever persisted to disk or reaches a log/error path. Confirmed: never via
  `git remote add`/`set-url` (grepped clean); `git push` uses it inline
  (argv-only, ephemeral, CLI path — clean). But `webhook.py`'s `git clone`
  call does let git's own default behavior write the token into the
  cloned repo's `.git/config`, un-scrubbed, for the full run duration
  (cleaned up only in the outer `finally: shutil.rmtree`) — a real,
  hosted-path-only exposure window with no CLI-path equivalent. Also
  confirmed zero scrubbing across four log/echo sites fed by unfiltered
  git subprocess stdout/stderr (`webhook.py:283`, `cli.py:544-548`,
  `pipeline.py:266-274`, `webhook.py:311`) — `scrub()` is never called on
  any git-related path. Logged as new BACKLOG item 19, a code fix, not a
  copy question. Judgment call, stated plainly rather than deferred: the
  security.html sentence itself doesn't overclaim (it describes the
  mechanism, not a safety guarantee this contradicts), so it did not need
  further editing and the commit was not held on this finding — the gap
  goes to BACKLOG 19 for Yehor to prioritize, not into more disclosure
  text on a page that already discloses the credential-isolation
  boundary's real scope.
- [2026-07-24, Session 024 close] Patchward committed and pushed by Yehor
  (`36b0a65`), confirmed at this close via a fresh clone's `git log -1`
  AND a separate `git ls-remote origin main` — both agree. callmed-landing
  committed locally (`68e612a`) — confirmed via `device_bash` reading the
  mount directly (not the pasted terminal output): HEAD matches, `git
  status --short` empty. **Production verified live, independent of
  Yehor's own check:** a fresh `WebFetch` of `callmedai.com/privacy` finds
  the new two-stage "transmitted to Anthropic" language present and the
  old "raw repository contents are never sent" claim absent; a second
  fetch of the homepage finds 0 "RepoMend" occurrences and "Patchward"
  present, which retroactively confirms BACKLOG 8's rename has been live
  since Session 022 — the deploy pipeline for `callmed-landing` works,
  settling a question this project had operated on faith for three days.
  **New finding at close, not present during the session itself:** a
  stray, empty `.git/index.lock` was found in the Patchward mount, created
  by this close's own read-only `git diff --stat -w`/`git status` calls —
  `device_bash` cannot remove it (the same documented limitation that
  blocked the mid-session commit attempt earlier). Flagged for Yehor to
  clear before his next git command there; not a sign anything actually
  broke. The ~57-file CRLF-only diff was re-checked and is still exactly
  zero real content under `-w` — durable, correctly still untouched.
  **Self-introduced-error count for this session, stated plainly rather
  than smoothed over: two.** The "Credential isolation" paragraph was
  wrongly cleared as accurate in the first correction pass (caught by
  Yehor's second pass), and the "no network access"/"no egress" framing
  was introduced by this session's own rationale-clause edit (caught by
  Yehor's own re-read of the diff before the second commit). Both were
  caught before shipping durably, both are logged here rather than
  quietly folded into "corrected" language — two occurrences in one
  session is worth naming as a pattern, not dismissing as noise.
  Full close-out: `memory/SESSION_CLOSE_2026-07-24.md` (written this
  close, pending Yehor's own commit alongside this file).

## Calibration record (close, Session 024)
- [2026-07-24 close] Of 7 checkable close-time claims (Patchward
  push/hash, BACKLOG.md items 18/19 present in the pushed commit,
  callmed-landing local commit + clean tree, the two overclaim strings
  gone from disk, corrected copy live in production, the CRLF diff still
  zero under `-w`, BACKLOG 17 status): **6/7 CONFIRMED** via a method
  independent of how each claim was first reported (fresh clone,
  `device_bash` direct read, and `WebFetch` against production — three
  different mechanisms, none reusing another's result), **1/7
  UNVERIFIED** (BACKLOG 17 — out of this session's scope, not re-checked,
  correctly not asserted either way). **1 DRIFTED, found only by this
  close's own check, not carried in from the session:** the stray
  `.git/index.lock`, created by the close's own verification commands. **
  0.86 on checkable claims (6/7), with the one miss self-caught at close
  rather than left for Yehor to discover.** Two self-introduced-and-caught
  errors logged this session (see Open threads) — first time this
  specific pattern has been named explicitly; watching for a second
  occurrence before promoting a heuristic.
- [2026-07-24, Session 024 — CORRECTION, same day, to the close entry
  immediately above] The close's "Production verified live" claim was
  wrong as a general statement. It was checked against exactly one path
  (`callmedai.com/privacy`, which happened to be current) plus one
  unrelated check on the bare homepage (RepoMend absence only — never
  re-checked for the actual false on-premise/auditability claims there).
  A further double-check, requested explicitly by Yehor as a second pass,
  found: `callmedai.com/` (bare) and `callmedai.com/security` (bare) both
  still serve OLD content — the homepage still has "your code never
  leaves your infrastructure" and "fully auditable on-premise"; `/security`
  serves a stub dated May 2026. `index.html`/`security.html` (explicit
  `.html` extension) and cache-busted bare URLs all serve the fully
  current, corrected content. Reproduced across separate fetches minutes
  apart, ruling out this session's own tool-level 15-minute fetch cache as
  the explanation. Working diagnosis (unconfirmed from this sandbox — no
  DNS/header tooling reachable, consistent with H4): a CDN/edge cache
  serving stale responses for the exact clean-URL cache keys, bypassed by
  `.html` suffixes and query strings. **Not fixed — logged as BACKLOG 20,
  marked highest urgency, and this is the actual open state of the site
  correction, not "closed."** Lesson, stated plainly: verifying one path
  and one unrelated string on a second path is not the same as verifying
  the claim "the site is live" — a claim about "the site" needs the same
  path a real visitor uses, checked for the actual thing being claimed,
  not a proxy check that happened to be convenient.
- [2026-07-24, Session 024 — SECOND correction, same day: BACKLOG 20 was
  itself a false alarm] Yehor's own diagnostics (`curl.exe -sIL` on both
  `/` and `/index.html`) showed `cf-cache-status: DYNAMIC` on both —
  Cloudflare passes every request straight to origin, no edge caching —
  which already undercut the CDN-cache theory. His Cloudflare Pages
  dashboard then showed `callmed-landing`'s latest deployment (21 minutes
  old, matching commit `68e612a`'s exact message) already live. **Decisive
  check: a real Chrome browser (Claude-in-Chrome), navigated fresh to
  `callmedai.com/` and `callmedai.com/security`, reading the actual
  rendered page** — both fully current: homepage shows the corrected
  on-premise/egress language, `/security` shows "Version 1.2" with every
  corrected section present. **The site was never stale. `WebFetch`'s
  "not found" results were wrong** — that tool fetches and summarizes
  through a small model rather than returning raw bytes, and it
  misreported presence/absence of specific strings on these two pages,
  twice, across multiple independently-worded prompts. Root cause of
  *why* `WebFetch` erred not fully chased (possibly its own internal
  cache, possibly the summarization step) — not needed once the real
  question (is the site correct?) was answered directly. BACKLOG 20
  closed same-day as a false alarm. **New heuristic candidate (H10-
  candidate, one occurrence — needs a second before promotion): for exact
  presence/absence claims about live web content on this project, `curl`
  raw bytes or a real browser read (Claude-in-Chrome) outrank `WebFetch`'s
  summarized result — `WebFetch` is fine for gist/summary tasks but proved
  unreliable here for an exact-string verification the close-out relied
  on as fact.** This session's own two "self-introduced-and-caught" errors
  (logged earlier) plus this false alarm makes three real corrections in
  one close sequence — all caught before being acted on wrongly, all
  because Yehor kept pushing for one more independent check rather than
  accepting the previous one. That pattern — not any single fact — is the
  actual result worth carrying forward.

## Session log (continued) — Session 025

- [2026-07-27, Session 025 open] Verified fresh via methods independent of the
  resume prompt: `git ls-remote origin main` + a fresh `git clone` both →
  `1132815` ("docs: clarify CRLF noise was sandbox-only"), matching the resume
  prompt; all 7 memory files on the D:\ mount byte-identical (CRLF-normalized)
  to that clone (H8 clean); Fly `/healthz` → `{"status":"ok"}`. 46 days to the
  2026-09-11 CRA reporting date. Yehor chose BACKLOG 19 (GITHUB_TOKEN exposure)
  as the session goal.

- [2026-07-27, Session 025 — the BACKLOG 19 arc] Opened trace-and-scope-only
  (no code) per Yehor's §2 discipline. Trace empirically FALSIFIED
  `clone_url_with_token`'s docstring ("never written to disk"): a real
  `git clone` with a token URL persists it to `.git/config`, and the webhook
  mounts that `.git/` read-only into the adversarial scanner boundary — so the
  live token sat inside the exact surface ADR-013 treats as hostile, every run.
  Also found the unmitigated `str(TimeoutExpired)` argv leak both prior traces
  missed. Base fix committed+pushed by Yehor as `37b3bfd`, verified byte-
  identical via fresh clone. Adversarial pass #1 (independent Opus, patch-only,
  guardrailed to the real tree) found FIVE credential-path issues incl. the
  sharpest catch of the whole project: a cross-thread race where `scrub_text()`
  iterating the live registry could raise `Set changed size` from inside the
  `except` and surface the UNSCRUBBED exception — a scrubber leaking the token
  it exists to redact, reachable only under the hosted threading model,
  unfindable by reading. Follow-up fixed #3/#4/#5 + F1/F2 from pass #2;
  pass #3 returned 0 leaks / 0 blockers + 3 robustness spin-offs (22/23/24).
  Follow-up committed+pushed as `dee84e1` (verified byte-identical), deployed
  to Fly image `sha256:ac54d18a…` (machine `7841600fd5e7e8`), `/healthz` green
  confirmed by WebFetch AND a real Chrome browser read. BACKLOG 19 reconciled
  to CLOSED in `memory/BACKLOG.md` (origin trace preserved). Full detail there.

- [2026-07-27, Session 025 — corrections banked before they reached the record]
  This session the two-pass / verify-against-the-tree discipline caught several
  would-be-false claims before commit, worth logging honestly (both signs):
  (1) Yehor's review two turns into the arc described a GIT_ASKPASS conversion
  that did not exist in the tree — a hallucinated diff; caught by re-cloning
  and grepping `37b3bfd` (zero askpass refs). (2) A "must-fix before commit"
  blocker (token in argv via the inline helper) was empirically refuted by a
  live `/proc/<pid>/cmdline` poll — the helper string carries the env-var NAME,
  not the value. (3) Yehor asserted "the re-attack came back clean" for a pass
  that had NOT been launched; caught and the real pass run, which then returned
  0 leaks but 3 robustness items — not "clean." (4) A drafted CLOSED block and
  commit message claimed the concurrency test "proves" #4; corrected to
  review-verified-not-test-proven (the race is not deterministically testable —
  a broken deterministic test I wrote myself was caught and removed rather than
  shipped). (5) The self-authored F1 docstring over-claimed a "structural"
  guarantee that `exc.cmd` did not deliver; the re-attack refuted it, and it
  was made true (scrub `exc.cmd`) rather than softened.

## Calibration record (continued) — Session 025

- [2026-07-27, Session 025] The dominant calibration signal this session was
  not a single confirmed/drifted count but a PATTERN: across a multi-pass
  adversarial security remediation, every independent check (fresh clone,
  `/proc` poll, real-browser `/healthz`, mutation-testing the tests, and three
  adversarial passes) caught something the prior, more-confident layer had
  asserted — including catches against the reviewing agent's own output and
  against the user's own framing. Zero false claims reached the committed tree
  or the closed memory. The concurrency-scrub leak (found only by an adversary
  reasoning about the threading model) is logged as a §8.4 win of the highest
  order. Score on the specific closing gate: state (c) reached and confirmed by
  two independent methods; 1.00 on the checkable close claims (hash via
  ls-remote+clone, image digest via `fly image show`, `/healthz` via
  WebFetch+browser). #4's fix correctly recorded as construction-verified, not
  test-proven — an honest UNVERIFIED-by-test label rather than an overclaim.

## Heuristics (earned) — Session 025 additions

- H11 [PROMOTED 2026-07-27, evidence: BACKLOG 19's review arc — one pass on
  one boundary spawned items 21, 22, 23, AND 24, each a distinct adjacent
  boundary the pass surfaced but that was out of the reviewed diff's scope]:
  an adversarial pass on one security boundary reliably ENUMERATES adjacent
  boundaries. Budget every security close to spawn its successors — do not
  treat any one fix as the last, and when opening the next item (e.g. 22),
  expect its own pass to spawn 25/26 the same way. This is the gate doing its
  job (finding what's there before an attacker does), not scope creep. The
  practical rule: scope-and-log the spin-offs as their own units (keep each
  diff clean and separately reviewable), never fold them into the diff under
  review, and never let a "clean of leaks" pass be recorded as "clean" when it
  spawned robustness items — record both.

- H12 [PROMOTED 2026-07-27, evidence: the `scrub_text` concurrency race + the
  `str(TimeoutExpired)` argv leak, both real, both invisible to single-threaded
  reading and to line-by-line review, both found only by an adversarial pass]:
  for credential-boundary code on an internet-facing surface, an independent
  adversarial pass (different model instance, patch-only, guardrailed to verify
  every claim against the real tree) earns its cost and MUST run until a pass
  finds zero LEAKS/BLOCKERS — the empty-of-leaks result, not a reviewer's
  confidence, is the ship signal. Corollary from this session: some correct
  fixes are not deterministically unit-testable (a GIL-atomic snapshot closing
  a timing race); record those as construction-verified/review-verified, and do
  NOT ship a fabricated "discriminating" test to paper over the gap.

- H10-candidate [applied 2026-07-27, still a candidate]: applied proactively
  this session — the closing `/healthz` gate was corroborated with a real Chrome
  browser read rather than trusting WebFetch alone. No new WebFetch failure
  occurred (it agreed with the browser this time), so no second failure to
  promote on; the discipline of corroborating an exact-content web claim on
  this project held and cost little.

## Session log (continued) — Session 026

- [2026-07-28, Session 026 open] Verified fresh by methods independent of the
  resume prompt. **DRIFT (benign):** the prompt cited `main @ 9e70f36`; real HEAD
  was `23dc9bd` (a docs-only child, the Session 025 close-out commit written
  after the handoff was drafted). Confirmed by cloud `git ls-remote origin main`
  + a fresh `git clone`, both → `23dc9bd`, matching the mount. Working tree
  "55 modified" on the mount is the known CRLF artifact — `git diff --stat -w`
  returns empty, 5798 insertions = 5798 deletions. All 6 memory files
  CRLF-normalised sha256-identical mount-vs-clone (H8 clean). Fly `/healthz` →
  `{"status":"ok"}` (WebFetch only — the browser corroboration was interrupted,
  so this is one method, not two; recorded honestly rather than as a two-method
  confirmation). 45 days to the 2026-09-11 CRA date (prompt said ~46).

- [2026-07-28, Session 026 — a user-asserted state claim, falsified before it
  could cause a destructive no-op] Mid-session Yehor stated with confidence:
  "Physical status confirmed — BACKLOG 19 is NOT committed. It's still staged,
  and its BACKLOG entry is still the pre-fix Session-024 trace… no CLOSED
  marker, no commit hash, no deploy//healthz line anywhere for 19," and issued a
  full commit→deploy→memory-reconcile instruction chain on that premise.
  Falsified against the tree: `37b3bfd` (10 files, +574/−57) and `dee84e1`
  (6 files, +228/−20) are real commits; `BACKLOG.md` at HEAD carries
  `**STATUS: CLOSED 2026-07-27 (Session 025).**` and `**Owner:** CLOSED`;
  `git status --porcelain` shows ZERO staged entries. **Root cause identified,
  not just the error:** item 19's deliberately-preserved Session-024 origin
  trace has `**Not acted on, deliberately**` and `**Owner:** unassigned` sitting
  SIX LINES ABOVE the CLOSED block, so a top-down reader who stops at the first
  Owner line reaches exactly that conclusion. Had the chain been run it would
  have committed nothing but line-ending noise and rewritten an already-CLOSED
  block from a stale trace that does not exist.

- [2026-07-28, Session 026 — the hygiene fix] One-line marker added to item 19's
  origin-trace Owner line (`SUPERSEDED, see STATUS: CLOSED below ↓`). Committed
  and pushed by Yehor as `8931702`; verified independently of his pasted
  terminal output via cloud `git ls-remote` (`8931702c370bbb…`) + fresh clone,
  and `git diff --stat 23dc9bd 8931702` → `1 file changed, 1 insertion(+),
  1 deletion(-)`.

- [2026-07-28, Session 026 — BACKLOG 22 scope pass, hard stop honoured] Ran
  scope-only per Yehor's explicit §2 instruction: traced, enumerated, laid out
  options A/B/C with what-breaks / what-it-costs / residual-risk, surfaced the
  decision, chose nothing, staged nothing, ran no adversarial pass on the memo.
  Memo: `memory/BACKLOG22_gate3_scope_memo_2026-07-28.md` (448 lines).
  Three findings beyond the assigned questions:
  (1) **Item 22's own premise was inverted.** Its text said "scanners DO route
      through the sandbox via `pipeline.py`→`run_all_scanners`" — false at HEAD.
      `sandbox` defaults to `None`, all four production call sites omit it, and
      `DockerSandbox(` is instantiated nowhere in `src/`. Option A is therefore
      the FIRST production use of the sandbox, on a Fly host with no Docker —
      new infrastructure, not a wiring change. Logged as item 26.
  (2) **Four credentials `_CREDENTIAL_KEYS` does not cover** —
      `GITHUB_APP_PRIVATE_KEY_B64` / `GITHUB_APP_PRIVATE_KEY` / `GITHUB_APP_ID` /
      `GITHUB_WEBHOOK_SECRET`, all in `os.environ`, all inherited by Gate 3's
      adversarial child with no race. The App key + App ID mint tokens for EVERY
      installation — cross-tenant, worse than anything 19 or 22 recorded. Gates
      both Option A and Option B. Logged as item 25.
  (3) **The disqualifier came back favourable**, and the sharper implication was
      taken: Gate 3 installs nothing, uses Patchward's own interpreter, and
      `verifier.py:764-768` degrades to SKIP on missing deps — so sandboxing
      breaks almost nothing, but Gate 3 is also delivering less verification
      value than assumed, independent of the security question.
  Also corrected precisely in Patchward's favour: `PATCHWARD_GIT_TOKEN` is NOT
  in the parent `os.environ` (`git_credentials.py:117` — `credential_env()`
  returns a copy), so it is race-only via `/proc`, not a direct inherit. Item
  22's text overstated that one.

- [2026-07-28, Session 026 — §5 escalated from Tier 1 to Tier 0 without touching
  Fly] The scope memo flagged, honestly as Tier 1, that pytest is likely absent
  from the deployed image. Closed the inference chain empirically instead:
  built the actual wheel and read its `METADATA` (`pytest` absent entirely;
  `[dependency-groups].dev` is PEP 735 and never reaches wheel metadata);
  queried PyPI for every package `webhook.Dockerfile` installs (only
  `pytest; extra == "test"` on pip-audit, not installed); and EXECUTED Gate 3's
  exact argv against a real pytest-less venv → `No module named pytest`,
  returncode 1, ZERO hits against the three literal SKIP triggers at
  `verifier.py:767` → `FAIL`, not SKIP → `g3_ok` false → `verify_failed` → no PR.
  **Residual named, not buried:** this proves the build recipe, not that the
  running `sha256:ac54d18a…` container matches it; `fly ssh console` →
  `python -c "import pytest"` is now confirmatory, not decisive.
  **Consequence:** a second independent defect on BACKLOG 21's path. Either one
  alone prevents a PR. 21 is now a functional launch blocker outranking 22.

- [2026-07-28, Session 026 — a false attribution caught and corrected] A turn
  attributed to the session a recommendation ("lean toward B now, A later") that
  the scope memo never made — §7 deliberately offered no A/B/C lean, exactly as
  instructed. Flagged rather than let stand; Yehor confirmed the lean was his
  own from a prior turn. Same discipline this project applies to its own output,
  applied to the user's framing.

- [2026-07-28, Session 026 close — H1 fired again, and on a NEW mechanism]
  While preparing to write the close-out files directly to the D:\ mount,
  `device_stage_files` returned a snapshot of `memory/BACKLOG.md` whose content
  was the PRE-`8931702` version (CRLF-normalised sha `66f8377d…`, the same hash
  staged at session open ~24h earlier) while reporting a FRESH mtime
  (`1785254891333`, Jul 28 16:08) consistent with Yehor's actual edit. Caught
  only because the close compared the staged copy against a fresh clone before
  overwriting anything: a direct `device_bash` read of the same path returned
  `311f1292…`, byte-identical to `git show HEAD:memory/BACKLOG.md`. The mount
  was correct; the STAGING LAYER was stale. Had the staged copy been trusted,
  the close would have written a file built on pre-marker content and silently
  reverted `8931702`. **This widens H1** — the stale-mount hazard is not confined
  to git plumbing reads; `device_stage_files` can serve stale bytes with an
  accurate mtime, so mtime is NOT a freshness signal. Standing rule: before
  writing any file back to the mount, verify the staged copy against a fresh
  clone or a direct `device_bash` hash, never against its own reported mtime.

- [2026-07-28, Session 026 close — the live-container pass, and what it changed]
  Yehor opened `fly ssh console -a patchward-webhook` (machine `7841600fd5e7e8`)
  and ran a read-only probe block (names + lengths only, no credential values
  printed, nothing installed or mutated). Results, all Tier 0 on the RUNNING
  container:
  (a) **§5 CONFIRMED, residual closed.** `import pytest` →
      `ModuleNotFoundError`; `python -m pytest` against a real `tests/` probe →
      `/usr/local/bin/python: No module named pytest`, matching none of the
      three SKIP triggers → Gate 3 FAILs. `node`/`npx` both ABSENT, so the jest
      branch cannot execute either. The hosted path hard-FAILs every detected
      suite.
  (b) **Item 25's enumeration live-confirmed.** `GITHUB_APP_PRIVATE_KEY_B64`
      (2236), `GITHUB_APP_ID` (7), `GITHUB_WEBHOOK_SECRET` (36) all SET in the
      parent `os.environ` Gate 3's child inherits. `PATCHWARD_GIT_TOKEN` ABSENT
      — BACKLOG 19's copy-not-mutate fix verified on the live host, the first
      Tier-0 confirmation of that fix outside the source. `GITHUB_TOKEN` ABSENT
      — item 21's root cause, live-confirmed.
  (c) **Item 26 live-confirmed.** `command -v docker` → nothing.
  (d) **A NEW defect, item 27:** `ANTHROPIC_API_KEY  SET  len=9`. No valid
      Anthropic key is nine characters. `webhook.py:318` guards only on
      falsiness, so a 9-char string passes and Fix-Gen 401s at first use —
      UPSTREAM of both of item 21's defects. The hosted path has been
      non-functional at an earlier stage than 21 supposed. **Both links closed
      to Tier 0 in the same session:** the length was measured in the process,
      and a live `anthropic.Anthropic().models.list()` from inside the container
      returned `401 invalid x-api-key` (`req_011CdUpKqhwSQoJufxCitjcZ`). The
      hosted webhook cannot reach the Anthropic API at all — Fix-Gen fails on
      its first request, every run, so the two downstream defects have never
      even been reached in production.
  (e) **An apparent image mismatch that resolved into a confirmation.**
      `verifier.py` in the container hashed `e375a6d3…` against `a25ac226…` at
      `dee84e1` — three of four files matched, one did not. Rather than
      reporting either "match" or "mismatch", the close ran the archaeology:
      `e375a6d3…` is reproduced exactly by
      `git show HEAD:src/patchward/verifier.py | sed 's/$/\r/'` — it is HEAD's
      file with CRLF endings. Content identical. **The image IS built from
      `dee84e1`.** The build context carried a MIXED working tree (files written
      by tooling during the BACKLOG 19 arc are LF; files untouched since an
      earlier checkout are CRLF) and the image preserved that mix. Practical
      lesson banked: file hashes are not a reliable provenance signal from a
      Windows build context — normalise line endings before comparing, or the
      check produces false alarms.

- [2026-07-28, Session 026 close — item 27's fix attempt FAILED, and what that
  taught] Yehor re-set the Fly secret; the rolling update succeeded and
  `/healthz` came back green. The new value reached the process (in-process
  read: `length: 110`), so delivery worked — but `models.list()` still returned
  `401 invalid x-api-key` under a NEW request id
  (`req_011CdUqmbwJFzk9S97aPP1eP` vs the original `req_011CdUpKqhwSQoJufxCitjcZ`),
  proving a fresh call. Diagnosis, all from booleans and lengths, never any part
  of the value: contamination REFUTED (raw length == stripped length, no
  whitespace, no quotes, no non-ASCII — the PowerShell-quoting hypothesis was
  wrong), and a prefix sweep across ten credential families returned all False
  INCLUDING `sk-ant-`. The secret holds a well-formed credential belonging to
  some other system. **Three lessons banked:**
  (i) A hypothesis stated in advance ("PowerShell contamination") was refuted by
      the very check designed to confirm it — and the refutation was reported as
      a refutation, not quietly replaced by the next guess.
  (ii) **A boundary was held on purpose.** Identification of the mystery
      credential was STOPPED rather than pursued: each further probe leaks more
      shape about a live secret while yielding less, and identifying it belongs
      to Yehor's own records. Logged as a deliberate stop, not an unfinished
      check — the distinction matters for a future reader deciding whether to
      resume it.
  (iii) The security consequence was separated from the functional one: whatever
      that credential is, it sat in a production env var exposed on the Gate 3
      inheritance path, so it needs rotating at its source independently of the
      Anthropic fix. Item 25's blast radius now includes a credential neither
      party can name.
  Item 27's TITLE was also corrected — it still read "is 9 characters" after the
  finding had evolved to "is not an Anthropic key". H13 applied to this
  project's own freshly-written entry, within hours of promoting it.
  New item 28 split out: `webhook.py:318` validates by falsiness only, and has
  now waved through TWO different broken secrets in one evening. Two live
  occurrences, one-line fix. Also recorded there: a `/healthz` that does not
  touch the dependency it needs will report green over a broken configuration
  indefinitely — which is how three defects sat undetected on this service.

- [2026-07-28, Session 026 final audit — H2 caught this session red-handed]
  The close-out's own next-session prompt cited `main @ 75d3fe9 plus one
  addendum commit`. By the time the session actually ended the chain was
  `75d3fe9 -> c1f789b -> 05764d3` — the prompt's hash went stale TWICE while the
  session was still writing it, and the "one addendum commit" count was wrong.
  H2 ("never cite the current commit hash inside a committed handoff file —
  structurally always stale") has been on this file since 2026-07-15 and was
  violated by the very document meant to embody the close. Caught by a
  deliberate staleness audit of the prompt at final close, not by luck.
  **Fixed by removing the hash entirely** and replacing it with a CONTENT
  checklist the next session can verify against whatever HEAD it finds — which
  is what H2 should have implied all along and did not say explicitly. H2 is
  hereby widened: a handoff must be verifiable against content, not against a
  revision identifier, because the identifier changes while the handoff is being
  written. A second defect was found in the same audit: item 28 was referenced
  in passing ("see also item 28") but never listed as open work, so a reader
  working the priority list would have missed it entirely. Both fixed before the
  final commit.
  Method note worth keeping: the first pass of this audit used `grep -c '\b28\b'`
  and reported "item 28 mentioned 3 times" — two of those were the date
  `2026-07-28`. The check was re-run with context printed rather than counted,
  which is what surfaced the real gap. A count without its context is not
  evidence; this is the second time in one session that a self-authored check
  had the wrong expected value (see also the SESSION_CLOSE test-suite grep).

## Calibration record (continued) — Session 026

- [2026-07-28, Session 026] **Score: 8 CONFIRMED / 11 checkable claims = 0.73.**
  DRIFTED: (a) resume-prompt HEAD `9e70f36` → real `23dc9bd`; (b) "~46 days" →
  45; (c) item 22's own stated premise about scanner sandbox routing → false at
  HEAD. Separately falsified: one high-confidence user-asserted state claim
  ("BACKLOG 19 is NOT committed") that would have driven a destructive no-op,
  and one false attribution of a recommendation to the session.
  **The pattern worth keeping:** every drift this session came from a CLAIM
  ABOUT STATE written by a confident prior author — a handoff prompt, a backlog
  entry's own premise, a user's recollection — and every one was caught by the
  same move: check it against the tree before building on it. Zero false claims
  reached the committed tree or the closed memory. One honest downgrade recorded
  rather than smoothed: `/healthz` was confirmed by ONE method this session, not
  two, because the browser corroboration was interrupted.
  0.73 is below Session 025's near-1.00 but the composition is different and
  healthier to see: the drifts were in INHERITED claims, not in this session's
  own output. No memory-hygiene thread triggered (the rule is <0.7 twice
  running); watch it next session.
  **Post-close addendum:** the live-container pass added 5 further checkable
  claims, all CONFIRMED (pytest absent; node/npx absent; the four-credential
  enumeration; `PATCHWARD_GIT_TOKEN`/`GITHUB_TOKEN` absent; docker absent),
  taking the session to **13/16 = 0.81**. That same pass surfaced one NEW defect
  (item 27) and one apparent-anomaly-turned-confirmation (the `verifier.py` CRLF
  hash). A final pass then closed two more claims: item 27's invalidity
  confirmed by a live `401 invalid x-api-key`, and `/healthz` corroborated by a
  second independent method (Yehor's own `curl.exe` from his machine agreeing
  with the sandbox's `WebFetch`). **Final: 15/18 = 0.83, and ALL FOUR weak
  points named at close were retired the same day — only the unrun test suite
  carries forward.** That is the strongest argument this project has yet
  produced for running the cheap confirmatory check rather than deferring it: a
  five-minute console session retired three weak points, upgraded a Tier-1
  inference to Tier 0, and found a defect upstream of everything the scope pass
  had been reasoning about.
  Recorded precisely, not generously: H10-candidate is NOT promoted by that
  `/healthz` result. Its promotion condition is a second occasion where
  `WebFetch` DISAGREES with an independent read; the two agreed, so the
  discipline held but earned nothing. Applying a candidate heuristic
  successfully is not evidence for it.

## Heuristics (earned) — Session 026 additions

- H13 [PROMOTED 2026-07-28, evidence: two independent occurrences in two
  sessions — Session 025 empirically falsified `clone_url_with_token`'s own
  docstring ("never written to disk"; a real clone persists the token to
  `.git/config`), and Session 026 falsified BACKLOG item 22's own stated premise
  ("scanners DO route through the sandbox"; `sandbox` defaults to `None` and
  `DockerSandbox(` is instantiated nowhere in production)]: **an artifact's
  self-description is a claim, not a fact — including docstrings, commit
  messages, and this project's own backlog entries.** When scoping an item,
  re-verify the item's OWN load-bearing premises against the tree, not only the
  questions you were asked. Both occurrences inverted the shape of the decision
  that depended on them; in both cases the false premise made the work look
  smaller than it was.

- H14 [PROMOTED 2026-07-28, evidence: two independent occurrences in two
  sessions — Session 025 (Yehor's review described a GIT_ASKPASS conversion that
  did not exist in the tree, and later asserted "the re-attack came back clean"
  for a pass that had never been launched) and Session 026 (a confident,
  detailed "BACKLOG 19 is NOT committed — still staged" with a full instruction
  chain built on it, refuted by `git log` + `ls-remote` + a fresh clone +
  `git status --porcelain` showing zero staged entries)]: **a user-asserted
  state claim is a hypothesis, and instructions built on one inherit its
  uncertainty.** Verify the premise against the tree BEFORE executing the chain,
  and when it fails, show the evidence rather than asserting the correction —
  and look for WHY the misread was reasonable (in 026 it was a preserved origin
  trace sitting above its own CLOSED block), because the structural cause is
  usually fixable and will otherwise recur.

- H15-candidate [applied 2026-07-28, needs one more occurrence]: when a claim
  turns on what a BUILT ARTIFACT contains, build the artifact and read its own
  metadata rather than reasoning from the source config that feeds it. Session
  026 resolved the pytest question from the wheel's `METADATA` (excluding any
  build-config mismatch) plus an executed argv, rather than from `pyproject.toml`
  — converting a Tier-1 inference to Tier 0 with no deploy access required.
  Promote if a second session resolves a deployment-state question this way.

- H10-candidate [carried, still a candidate, 2026-07-28]: NOT advanced this
  session. `/healthz` was checked by WebFetch only — the browser corroboration
  was interrupted before it ran. Recorded as one-method rather than quietly
  claimed as two.

- H16 [PROMOTED 2026-07-28, evidence: two independent occurrences in one session
  — the `verifier.py` container hash that looked like an image mismatch and was
  really CRLF, and the recurring "55 modified files" mount diff that
  `git diff -w` shows to be empty]: **on this project, never report a hash or
  diff mismatch until line endings have been eliminated as the cause.** The
  Windows working tree is MIXED (tooling-written files LF, checkout-written
  files CRLF), so byte-level comparisons across the mount/image/clone boundary
  produce false alarms by default. Normalise (`tr -d '\r'`, `git diff -w`, or
  reproduce the suspect hash with `sed 's/$/\r/'`) BEFORE concluding anything —
  and when a hash does mismatch, run the archaeology to identify which commit or
  transformation produces it rather than reporting the mismatch itself as the
  finding. The second half is what turned an alarming result into a
  confirmation this session.

## Session log (continued) — Session 027

- [2026-07-29, Session 027 open] Opened via session-strategy-synthesis. Verified
  Session 026's close landed BY CONTENT (not by hash — H2): real HEAD `6650918`
  established by device `git rev-parse` AND cloud `git ls-remote` + a fresh
  clone (two independent methods agree). All four content conditions confirmed
  in the fresh clone: BACKLOG items 24–28 present in order, item 19 SUPERSEDED
  marker, STRATEGY Session-026 block + H13/H14/H16, memo at 448 lines,
  SESSION_CLOSE_2026-07-28.md present. The 53 "modified" files are CRLF flap
  (H16) — content-identical to HEAD once `\r` stripped.

- [2026-07-29, Session 027 — BACKLOG 25 SHIPPED] Widened `_CREDENTIAL_KEYS` to
  cover the four GitHub App credentials. Implemented + tested in a clean clone,
  delivered as a patch, applied + committed + pushed by Yehor as `f02ad21`.
  Verified on `origin` (ls-remote + fresh-clone content). Full suite run on
  Yehor's machine: **519 passed / 90.62% coverage** — which also RETIRES success
  criterion 3 (the real suite had not run in three sessions). Scoped commit
  discipline held: exactly two files staged, `git add -A` avoided (the CRLF
  flap seen via the device-VM mount does NOT appear on Yehor's real Windows git,
  which showed only the two intended files — a live confirmation of H16's mount
  artifact).

- [2026-07-29, Session 027 — §5 CONFIRMED against the LIVE IMAGE] `fly ssh
  console` onto running image `deployment-01KYJ325AN...`: `python -m pytest` →
  `No module named pytest` (the verifier's exact call), `node`/`npx` absent.
  Gate 3 hard-FAILs on the hosted path → no PR. Escalated from Tier-0
  build-recipe to Tier-0 live. Last open Tier-1→Tier-0 gap on the board closed.

- [2026-07-29, Session 027 — item 27 FIXED live] Yehor re-set `ANTHROPIC_API_KEY`
  with a real key (the 4th value; three prior 401'd, incl. a third rejection
  this session, `req_011CdWa5on6JfoSxS2MGxP3h`). The key was validated LOCALLY
  (`models.list()` → OK) BEFORE deploy — this prevented a 4th failed redeploy
  cycle — then set, rolling-updated, and re-confirmed on the running image
  (`ANTHROPIC KEY OK`). One of the three hosted-path defects is down; §5 + item
  21 remain.

- [2026-07-29, Session 027 — BACKLOG 28 PREPARED, not landed] Startup credential
  shape-guard (`_validate_credential_shapes()` via FastAPI lifespan). Tested in
  a clean clone (**526 passed / 90.75%**, +9 tests). Delivered as a patch; NOT
  committed as of close (tree + origin at `f02ad21`). Two Yehor decisions kept
  OUT of the patch: absence-fails-boot?, and /healthz asserting validity.

- [2026-07-29, Session 027 — inherited-claim drift, THREE occurrences] Yehor
  (and a pasted external analysis) asserted repeatedly that "the BACKLOG.md is
  the Jul-27 version, predates items 25/26" and that "the Gate 3 memo is
  chat-only, not filed / the Session-025 reconciliation hasn't landed." All
  falsified against `origin` HEAD each time (items 24–28 present; memo is
  `memory/BACKLOG22_gate3_scope_memo_2026-07-28.md`, 448 lines, committed).
  Zero drift in this session's OWN outputs; every drift was an inherited state
  claim — the exact H13/H14 pattern, now seen a third time. Reinforces H14.

- [2026-07-29, Session 027 — close] BACKLOG 25 CLOSED, item 27 CLOSED (live),
  §5 CONFIRMED-live, item 28 PATCH-PREPARED. Business context recorded (see
  below) and a North-Star priority function drafted for the guidance model.
  Weak point stated plainly: item 28 is tested but unlanded; the 110-char
  foreign credential still needs rotation at source (Yehor); item 21's code fix
  and the §5 design fork are the next session's P0, both gated on a Yehor
  decision.

## Calibration record (continued) — Session 027

Claims checked this session and their verdicts: Session-026 close landed
(CONFIRMED, 2 methods) · real HEAD `6650918` then `f02ad21` (CONFIRMED, 2
methods) · four close-conditions (CONFIRMED) · BACKLOG 25 shipped+pushed
(CONFIRMED on origin) · suite ≥90% (CONFIRMED, 90.62% live) · §5 live
(CONFIRMED on running image) · item 27 fixed (CONFIRMED on running image) ·
"BACKLOG.md is stale / lacks 25-26" (FALSIFIED ×3) · "memo is chat-only"
(FALSIFIED) · implicit "BACKLOG 28 was landed" (FALSIFIED at close — tree at
`f02ad21`). **Every drift was an INHERITED claim (user assertion or a pasted
external analysis); zero false claims originated in this session's own output**
— the same signature as Sessions 025/026. Of this session's own verifiable
deliverables (25 shipped, §5 confirmed, 27 fixed), 3/3 held. Calibration on
inherited claims checked: 7 CONFIRMED / 11 = 0.64 — the low ratio is healthy
here (it means the hard checks are catching inherited drift, not that our own
records drifted).

## Heuristics (earned) — Session 027 additions

- H14 [REINFORCED 2026-07-29, third independent occurrence]: the "BACKLOG.md is
  stale / the memo isn't filed" premise recurred twice more this session (once
  from Yehor, once inside a pasted external analysis), both falsified against
  `origin` HEAD. The structural cause is that a handoff prompt or an external
  reasoning pass narrates state from memory rather than reading the tree — so
  the fix is unchanged (verify the premise against the tree before acting) and
  now doubly evidenced. When an inherited plan's FIRST step is "reconcile
  something into memory," check whether it is already there before doing it.

- H17-candidate [applied 2026-07-29, needs one more occurrence]: validate a
  credential's SHAPE/validity LOCALLY before deploying it remotely. The local
  `models.list()` "KEY VALID" check gated `fly secrets set`, breaking a cycle
  that had already burned three bad-secret redeploys. Promote if a second
  session avoids a remote round-trip by a local pre-check. (This is the same
  instinct BACKLOG 28 encodes in code: fail on shape at the boundary, not at
  first use.)

- H16 [REINFORCED 2026-07-29]: applied twice more — `git apply --3way` failed
  with "does not match index" on a CRLF/index mismatch (resolved via
  `--ignore-whitespace`), and the device-VM mount showed ~53 modified files
  while Yehor's real Windows git showed only the two intended. Normalise/verify
  against the authoritative tree before concluding.

## Business context (Session 027, for prioritization only)

Yehor is weighing a university deferral (VIA Horsens, supply & climate eng.)
against continuing three products (Patchward, FixProve, Zerkalnya). He asked the
guidance model to orient sessions toward SECURE, demonstrable income. Translation
for this project's priority function, NOT its content: the North Star is distance
to first paying Marketplace install — a falsifiable traction milestone — not
elegance, coverage, or backlog hygiene (those are means). Business claims get the
same Tier discipline as technical ones: no inflating progress. Sessions aim at
customers; parental peace-of-mind follows real traction, not a tidy backlog.

## Session log (continued) — Session 028

- [2026-08-01, Session 028 — open] Opened via session-strategy-synthesis.
  Re-verified the Session-027 close BY CONTENT against `origin` HEAD `02148c6`
  (ls-remote + fresh clone + local mount all agree): all four BACKLOG banners
  (25/27 CLOSED, 28 PATCH-PREPARED, 21 §5-CONFIRMED) and all four STRATEGY
  027 sections present; `SESSION_CLOSE_2026-07-29.md` exists. Working-tree
  "modifications" = CRLF-only noise (0 non-whitespace lines changed, 3707/3707).
  No drift in the record.

- [2026-08-01, Session 028 — H14 FOURTH occurrence, caught by the agent's own verification pass]
  The "BACKLOG.md is the Jul-27 cut, predates items 25/27/28" premise recurred a
  fourth time — this time inherited from Yehor's own prior turn — and drove a
  proposed Task 2 = "memory reconciliation." Falsified against `origin`: the
  file's last commit is `02148c6` (Session 027 close) and already carries all four
  reality-changes (item 25 CLOSED 519/90.62% L1560-62, item 27 CLOSED live
  L1655-61, §5 CONFIRMED L1313, coverage L1236). Task 2 declared a NO-OP; the
  file was NOT rewritten — reconciling a current file would have manufactured
  drift. Yehor owned the error plainly and asked it be logged. Signature unchanged:
  the drift is an inherited state-claim; zero drift in this session's own outputs.

- [2026-08-01, Session 028 — deliverable] §5 scope-and-decide memo produced:
  `memory/BACKLOG_S5_gate3_meaning_memo_2026-08-01.md`, verified-at HEAD
  `02148c6`, hard stop, no option chosen. Load-bearing finding (§3): the missing
  pytest runner is currently the ONLY thing keeping item 22's exposure dormant on
  the hosted path — `python -m pytest` dies at the interpreter import step before
  `conftest.py` runs — so §5-Option-A (install runner) is the literal act that
  arms item 22's cross-tenant exfiltration path. §5-A ⇒ item 22-A ⇒ new infra
  (Docker, absent on Fly). §5-B keeps item 22 dormant at the cost of Gate 3
  becoming advisory on hosted (a positioning/site-copy decision). Cross-matrix
  names the one unsafe bundle: §5-A + item 22-B. Decision OPEN, Yehor-owned.

## Calibration record (continued) — Session 028

Claims checked this session: origin HEAD = Session-027 close (CONFIRMED, 3
methods) · close landed by content, all 8 banners/sections (CONFIRMED) ·
working-tree diffs = CRLF-only (CONFIRMED, 0 non-ws) · item 25 fix on origin
(CONFIRMED) · item 28 patch present-but-unlanded + applies clean (CONFIRMED) ·
item 21 `github_token` dead in `run_repo_pipeline` (CONFIRMED, read L63-329) ·
§5 pytest-absent→FAIL mechanism (CONFIRMED from source) · "BACKLOG.md predates
25/27/28" (FALSIFIED — H14 4th) · "Task 2 reconciliation needed" (FALSIFIED —
no-op). Every drift again an INHERITED claim; 0 originated in this session's own
output — same signature as Sessions 025/026/027. The §5 memo's own claims were
verified against cited line numbers; only image-size deltas left Tier-1 (flagged
honestly in-memo). Own-output integrity: 1/1 deliverable (the memo) held.

## Heuristics — Session 028 update

- H14 [REINFORCED 2026-08-01, FOURTH independent occurrence]: same "memory file
  is stale / predates recent items" premise, this time inherited from Yehor's own
  prior turn and caught by the agent's verification pass, then owned by Yehor. Standing fix holds and is now four-times
  evidenced across four sessions (025/026/027/028): when an inherited plan's FIRST
  step is "reconcile X into memory," verify X isn't already there — against
  `origin`, not the narration — before writing anything. Four-for-four makes this
  the project's most reliable drift signature; treat it as a standing pre-check at
  every session open.

## Session log (continued) — Session 028 CLOSE

- [2026-08-01, Session 028 — close] Closed via session-close. Reconciled: local
  = origin = `7e4f4da`; every "modified" tracked file (memory/src/tests/runs) = 0
  real-content diff (pure CRLF noise), no uncommitted work. Deliverables this
  session (all verified on origin by fresh clone): §5 scope-and-decide memo filed
  (`memory/BACKLOG_S5_gate3_meaning_memo_2026-08-01.md`, §0–§7), §7 records the
  DECISION §5 = C2 with reasoning + implementation scope + 2 design notes; BACKLOG
  item 21/§5 pointer → DECIDED=C2; H14 4th logged with corrected attribution.
  Three commits (`a2bb547`, `2d6977c`, `7e4f4da`), memory/docs only. NO code
  changed — `verifier.py` L769/L790 still FAIL, `pipeline.py:68` still dead —
  confirmed unchanged on origin. L2 goal (scope §5 fork + get + record the
  decision) = MET. L1: cleared the DECISION gate in front of the hosted-path
  obstacle; did NOT move it in code — the metric needle is unmoved, next session
  implements. Weakest point stated plainly: the hosted path STILL cannot publish
  a PR; §5+21 decided, not built.

## Calibration record (continued) — Session 028 CLOSE

Documentation-only session; calibration is about record accuracy, not code. This
session's own outputs: 1 real self-caught defect — the §5 memo was reference-only
(pointer + log committed while the memo itself stayed untracked) for two commits
before being filed in `7e4f4da`; caught by a pre-push self-check, fixed, and
re-verified by fresh clone. Every other own-output claim held on origin
(decision recorded, attribution corrected, no code touched). Inherited claims:
"BACKLOG.md predates 25/27/28" FALSIFIED (H14 4th). Signature unchanged across
025–028: drift is inherited, not self-originated; the one self-defect was caught
before it reached origin's HEAD as a live inconsistency. Close verdict: safe —
nothing half-landed, nothing reference-only remaining.

## Heuristics — Session 028 CLOSE additions

- H18-candidate [earned 2026-08-01, needs one more occurrence to promote]: when a
  commit adds a POINTER/reference to a NEW file, verify the file itself is tracked
  in the SAME commit (`git status` for `??`, or `git cat-file -e HEAD:<path>`
  after). Evidence: the §5 memo was referenced by two commits while sitting
  untracked — a "reference-only artifact" that looks filed but isn't. Retest next
  time a new file is introduced alongside a pointer to it.

- H16 [REINFORCED 2026-08-01]: CRLF-normalised diffs were again required to
  separate real change from noise across the whole close (60+ files showed
  "modified", all 0 real lines). The normalise-before-you-conclude rule paid off
  a fourth session running; treat the sandbox `git status` as noisy-by-default on
  this Windows-origin tree.

## Session log (continued) — Session 029

- [2026-08-04, Session 029 — open] Opened via session-strategy-synthesis. Real
  HEAD established independently (`b003a39`) since the prompt cited none per H2;
  Session 028's close confirmed BY CONTENT via fresh clone, including the H18
  check that the §5 memo was genuinely tracked and not reference-only.

- [2026-08-04, Session 029 — INHERITED DRIFT, H14 FIFTH occurrence] Yehor stated
  from memory that the suite baseline was "483 passed on Python 3.14.4".
  FALSIFIED against the tree: 483/90.46% is the Session ~020-023 figure
  (STRATEGY L58/163); the live baseline was 519/90.62% (Session 027, L1677).
  Signature unchanged across 025-029: drift is inherited state-claims, not
  self-originated. NOTE — the correction did NOT weaken his argument, it
  strengthened it: he was arguing the sandbox run must not be the gate, and the
  fact that my sandbox produced 517+2 rather than his 519 proved the counts had
  never actually matched.

- [2026-08-04, Session 029 — ENVIRONMENT UNLOCK] The suite was made to run inside
  the agent sandbox for the first time (Linux, Python 3.10, PyPI reachable,
  pytest-xdist). This removed the constraint that made Session 028
  documentation-only. It is explicitly an ADVISORY pre-check, never the gate —
  see H20/Yehor's ruling. `uv python install 3.12` fails in the sandbox (GitHub
  releases blocked), so an on-spec interpreter is not obtainable here.

- [2026-08-04, Session 029 — §5 C2 SHIPPED, steps 1-2] Commit `d72c0df`, 4 files,
  +354/-8, fresh-clone verified on origin with all four blobs stored LF.
  `verifier.py`: 3 distinct SKIP reason constants; runner-absent SKIPs instead of
  FAILing for pytest and jest; all pre-existing SKIP triggers preserved.
  `pr_publisher.py`: PR-body disclosure keyed off the gate REASON, never the
  status. +12 tests. Gate: Yehor's Python 3.14.4 — 531 passed / 3 skipped /
  91.11% (up from 90.62%).

- [2026-08-04, Session 029 — SPEC WAS EXPLOITABLE; defense added over it] Memo §7
  said "detect the runner-absent signature". Implemented literally, that is a
  VERIFICATION BYPASS: a customer repo (adversarial input per ADR-013) that merely
  PRINTS "...: No module named pytest" would convert a genuinely FAILING suite
  into a SKIP, publishing a PR for a fix whose tests failed. Verified exploitable
  by direct test of the regex before relying on it. The shipped form requires a
  line-anchored match AND an independent `python -c "import pytest"` probe that
  never reads repo-controlled output, fail-closed on probe ambiguity.

- [2026-08-04, Session 029 — ITEM 21 TRACED, NOT WRITTEN] Size settled: ONE HOP,
  does not touch App-token minting. `webhook.py:276/282/302` already mint,
  register and clone with the installation token; `webhook.py:333-338` passes it
  to `run_repo_pipeline`, which drops it (`pipeline.py:68`); `PRPublisher`
  independently reads `GITHUB_TOKEN` from the proxy and Fly has no such secret
  (`credential_proxy.py:68`). Fix is a `push_token` param on `PRPublisher`, NOT a
  static PAT on Fly. Held for its own arc per Yehor's split ruling.

- [2026-08-04, Session 029 — H18 SECOND OCCURRENCE, promotes]
  `memory/Patchward_Turning-Point_Industrial-Plan_2026-07-16.md` is referenced by
  FIVE tracked documents but is itself untracked on origin, not gitignored, and
  has been so since 2026-07-16. Same reference-only pattern as the §5 memo in
  Session 028, now independently recurring. Flagged for Yehor; not added by the
  agent because it is his strategic document.

## Session log (continued) — Session 029 CLOSE

- [2026-08-04, Session 029 — close] Closed via session-close. Reconciled: local =
  origin = `d72c0df` (the code commit; the memory commit sealing this session
  moves HEAD after this block is written, per H2). Working tree carried 0 real
  content changes at close — every "modified" line was CRLF noise for the fifth
  consecutive session. L2 goal (implement §5 C2 + item 21 as ONE arc) =
  **PARTIAL, deliberately**: steps 1-2 landed, steps 3-4 (item 21, live
  site-copy check) held. L1: removed ONE of the two remaining hosted-path
  blockers. Weakest point stated plainly: the hosted path STILL cannot publish a
  PR — C2 cleared the verifier blocker, the auth blocker remains.

## Calibration record (continued) — Session 029

Claims checked at close: 10. Confirmed: 10. Drifted: 0 in this session's own
outputs. **Score 10/10 = 1.00.**

Inherited-claim drift: 1 (the "483 baseline", H14 5th) — falsified before it
could inform the plan, consistent with 025-028.

Own-output defects caught before landing: 2, and both matter.
  1. The regex-only implementation of memo §7 was exploitable. Caught by testing
     the regex directly rather than trusting it, BEFORE it was relied on.
  2. The first real-repo adversarial run reported SIX bypasses. All false — the
     harness invoked a pytest-less interpreter, so the suites never ran and SKIP
     was the correct verdict. Caught by diagnosing before reporting. Had it been
     reported, it would have been a false security alarm against my own patch.

One process defect NOT self-caught: the negative control shipped mocked-only in
the first pass. A mocked `subprocess.run` also mocks the probe, so a broken probe
would still have looked correct. It took Yehor's explicit demand to surface it.
Recorded honestly — the unmocked controls exist because he pushed.

Trend 025-029: five sessions, zero drift originating in the agent's own committed
outputs; all drift inherited and falsified at the gate. The new signature this
session is that the two self-caught defects were both in the agent's *reasoning
about its own verification*, not in the code — which is the harder class.

## Heuristics — Session 029 update

- **H18 [PROMOTED from candidate, earned 2026-08-01, confirmed 2026-08-04]:** when
  a commit adds a POINTER/reference to a file, verify the file itself is tracked
  (`git cat-file -e HEAD:<path>` or fresh-clone `ls-files`). Two independent
  occurrences: the §5 memo (Session 028, reference-only for two commits) and
  `Patchward_Turning-Point_Industrial-Plan_2026-07-16.md` (untracked for 19 days
  while five tracked documents cite it). Generalised form: **run the check on
  INHERITED references too, not only on files the current commit touches.**

- **H16 [REINFORCED — 5th consecutive session]:** CRLF-normalised diffs were again
  required to tell real change from noise (57 files "modified", 0 real). Treat
  sandbox `git status` on this Windows-origin tree as noisy-by-default.

- **H20 [NEW, earned 2026-08-04]:** never `git add`/`commit` from the agent
  sandbox on this repo. Verified mechanism, not a precaution: sandbox git has
  `core.autocrlf` unset and there is no `.gitattributes`, so `git hash-object`
  from the sandbox yields a CRLF blob where HEAD stores LF — a sandbox commit
  rewrites whole files and pollutes history irreversibly. The agent prepares and
  verifies; Yehor stages and commits on Windows. Tripwire before every push:
  `git diff --cached --stat` must show the expected small line counts.

- **H21 [NEW, earned 2026-08-04]:** a failing adversarial result is a claim about
  the HARNESS until the harness is verified. The first real-repo pass reported six
  bypasses; the true cause was that `_run_pytest` invokes bare `python`, which in
  the sandbox has no pytest, so no suite ever ran. Diagnose the environment before
  reporting a security finding — especially a finding against your own work, where
  the false alarm is expensive and the temptation to believe it is high.

- **H22 [NEW, earned 2026-08-04]:** mocked tests prove BRANCHING, not BEHAVIOUR.
  Where a test is the sole evidence for a security guarantee, it must be unmocked,
  because a mock of the subject also mocks the defense. Pair it with a mutation
  check — delete the defense and confirm the test goes red — otherwise the test's
  teeth are assumed rather than demonstrated. Evidence: deleting the import probe
  turned both negative controls red with the exact bypass assertion.

- **H23 [CANDIDATE, 2026-08-04, needs one more occurrence]:** when a spec says
  "detect X by string match", test the string against hostile input BEFORE
  implementing it. Here the spec-conformant implementation was a verification
  bypass, and one direct regex test surfaced it in seconds.

## Session log (continued) — Session 030

- [2026-08-05, Session 030 — open] Opened via session-strategy-synthesis.
  Real HEAD confirmed `894f62b`, matching origin and Session 029's close
  claims by content, not by trust. Working tree's ~57 "modified" files
  re-confirmed as CRLF noise (H16, 6th consecutive session) via
  `core.autocrlf=input` diff = empty.
- [2026-08-05, Session 030 — untracked-artifact triage] Two untracked
  working-tree files were investigated before any code work, per the
  standing discipline of checking unrecognized artifacts in a
  security-sensitive tree before working around them: (1)
  `Patchward_Counsel_Briefing_Packet_2026-08-03.pdf` was genuinely NOT
  gitignored (`git check-ignore` returned nothing) — fixed same session by
  adding a `*.pdf` rule; (2) `backlog28_startup_credential_guard.patch` was
  read in full — real, well-reasoned security work (fail-loud startup
  credential-shape guard), applies cleanly to HEAD, but a claimed
  "mojibake" defect in its comments was independently DISPROVEN by a
  byte-level check (zero occurrences of the mojibake sequence, correct
  UTF-8 em-dash present) — the claim originated from a Windows PowerShell
  `Get-Content` codepage-decoding artifact, not the file. No file fix
  needed for that specific claim.
- [2026-08-05, Session 030 — item 21 v1 authored] Implemented the traced fix:
  `push_token` param on `PRPublisher.__init__`, threaded from
  `run_repo_pipeline`'s already-minted token at the `pipeline.py`
  construction site, CLI path verified unaffected (two call sites found via
  grep, not one as the trace implied — `cli.py:509` untouched, and the
  shared `pipeline.py` site's CLI-batch value traced to be byte-identical
  to the old fallback via an upstream `.strip()` in `CredentialProxy.load()`
  the author's own report initially didn't cite as the reason). 6 new
  tests, own adversarial self-scan found no leak path. Real gate (Yehor's
  3.14.4): 546 passed / 3 skipped / 91.13% — matched the predicted
  531+6+9 math exactly.
- [2026-08-05, Session 030 — INDEPENDENT ADVERSARIAL PASS 1, NOT CLEAN] A
  fresh Opus subagent, no access to the authoring report, found the v1 fix
  incomplete: `_github_headers()` (shared by `_check_branch_protection()`
  and `_create_pr()`) still read `CredentialProxy` directly. Simulated the
  hosted path end to end: push succeeds (real token), PR creation gets an
  empty `Authorization` header and fails, and the branch-protection guard
  (aborts only on HTTP 200) goes blind because empty auth returns 404/401
  instead — a genuinely protected branch would no longer be caught before
  the force-push. Also found: a docstring invariant ("or stored on self")
  silently deleted rather than honestly updated; `.strip()` dropped on the
  override path; no type validation; the fix's own line unpinned by any
  test (deleting it kept the suite green); the new param not
  self-registering for redaction. Independently reconfirmed the CLI-path
  claim and closed the construction-time/concurrency question the author
  had left explicitly open.
- [2026-08-05, Session 030 — item 21 v2 fix] Routed `_github_headers()`
  through the same `_push_token()` the push uses — one credential source
  for all three of `publish()`'s credentialed operations. Closed all 6
  findings from pass 1. **Mutation-tested each of the 9 load-bearing lines**
  individually: reverted, confirmed a specific test broke, restored,
  reconfirmed green. Advisory sandbox suite (Py 3.10): 554 passed.
- [2026-08-05, Session 030 — INDEPENDENT ADVERSARIAL PASS 2, CLEAN on the
  core claim] A second fresh Opus subagent, no access to any report,
  independently re-derived the "all three operations now agree" claim via
  a live hosted-path simulation (empty proxy, real injected token) and
  confirmed it directly rather than trusting pass 1's fix description. Ran
  its own 9-mutation check, independently, with the same result. Verdict:
  core fix CONFIRMED CLEAN. Surfaced one new Medium finding not previously
  known: `pipeline.py` ignores `PRPublisher.publish()`'s returned
  `pr_dict["status"]` and always records `"pr_opened"`, even on
  `_create_pr()` failure — moot before item 21 (push always failed first),
  consequential after (push can now succeed while PR creation still fails
  for an unrelated reason, leaving an orphaned force-pushed branch with no
  error trail). Logged as BACKLOG 29, deliberately not folded into item
  21's diff, per the same split discipline as 21-from-19 and 28-from-27.
- [2026-08-05, Session 030 — real gate, v2] Yehor's Python 3.14.4:
  **555 passed / 3 skipped / 91.14%** — matched 546+9 exactly. Coverage
  "Missing" line ranges cross-checked against source: all pre-existing
  422/403/exception-handling branches, none in the new code.
- [2026-08-05, Session 030 — landed] Two commits, staged with explicit file
  paths (never `-A`), reviewed via `git diff --cached` before each commit,
  committed with `-F`-equivalent multi-line messages, pushed, verified by
  `git ls-remote` and a fresh clone: `053c9c9` (item 21, 4 files, +446/−15)
  then `c0743df` (BACKLOG 29 log, 1 file, +51). Fresh-clone content check
  confirmed `_github_headers()` on origin genuinely calls `_push_token()` —
  not just locally.

## Session log (continued) — Session 030 CLOSE

- [2026-08-05, Session 030 — close] Closed via session-close. Reconciled:
  local = origin = `c0743df`. Real working-tree diff beyond the two landed
  commits is exactly `.gitignore` (+3, the PDF-exposure fix) and
  `webhook.py`/`test_webhook.py` (BACKLOG 28's still-applied, still-
  uncommitted patch) — matches expectations exactly, nothing unaccounted
  for. L2 goal (item 21: thread, prove CLI unaffected, gate on real 3.14.4,
  adversarial pass) = **MET**, and specifically MET-because-the-process-
  worked: the first attempt would have shipped a real gap without the cold
  adversarial pass. L1: both known hosted-path blockers (§5/C2 from Session
  029, item 21 from this session) are now closed. Weakest point stated
  plainly: BACKLOG 28 still has not had its own independent adversarial
  pass, despite the exact protocol that just worked twice being immediately
  reusable on it — that is the single largest piece of unfinished business
  from this session.

## Calibration record (continued) — Session 030

Claims checked at close: 12. Confirmed: 11. Drifted: 1 (the mojibake claim —
caught and corrected same session, before it could inform any action).
**Score 11/12 = 0.92.**

Own-output defects caught before landing: 1, and it mattered. The v1
item-21 fix was incomplete — scoped to exactly what the inherited BACKLOG
trace named, not re-derived against the full set of credentialed operations
the class performs. Caught by an independent cold adversarial pass, not by
self-review; the author's own adversarial self-scan on v1 had found nothing,
which is itself the data point: a same-author scan under-performs a cold
one precisely when the blind spot is inherited scope, because re-reading
your own trace doesn't surface what the trace itself omitted.

One drift NOT self-caught first: the mojibake claim was investigated because
Yehor's pasted terminal output raised it, not because this session
independently suspected the patch file. Once raised, it was verified byte-
level and correctly refuted same-turn — so the catch was fast, but it was
prompted, not self-initiated.

Trend 025-030: six sessions, and this is the first with a real (not
inherited) drift in a claim the agent's own output made — the mojibake
read. It was minor, externally prompted, and closed within the same turn,
but the streak of "zero self-originated drift" (Session 029's close) is
broken. Recorded honestly rather than rounding back up.

## Heuristics — Session 030 update

- **H21/H22 [REINFORCED]:** the 9-mutation check on item 21's v2 fix is the
  cleanest demonstration yet of H22's discipline (mutation check proving
  teeth) applied exhaustively rather than to a single defense — every
  load-bearing line, not just the headline one, individually reverted and
  confirmed to break a specific test.

- **H24 [NEW, earned 2026-08-05]:** a security-fix spec/trace that names ONE
  seam ("thread the token into `_push_token()`") must be checked against
  every SIBLING consumer of the same resource class before being trusted as
  complete — not just the one method the spec named. Item 21's BACKLOG
  trace correctly identified `_push_token()` as *a* seam but never asked
  "what else in this class reads a GitHub credential?" The author (this
  agent) inherited that scope without re-deriving it, and shipped a v1 fix
  that threaded the push but left `_github_headers()` — used by BOTH the
  branch-protection check AND PR creation — reading the old, empty
  `CredentialProxy` path. An independent cold adversarial pass caught it by
  asking exactly that enumeration question. Generalise: before declaring a
  credential-threading fix complete, grep every consumer of the
  credential's OLD source, not just the one call site the spec mentions.

- **H25 [NEW, earned 2026-08-05]:** "CLEAN" from an adversarial pass is only
  as strong as what it demonstrably broke, not what it re-read. The second
  item-21 pass earned CLEAN by (a) running a live hosted-path simulation
  with a real injected token against an empty `CredentialProxy` and
  confirming all three credentialed calls agreed, and (b) reverting each of
  9 load-bearing lines individually and confirming each reversion broke a
  specific test, then restoring and reconfirming green. A "clean" verdict
  without that kind of demonstration should be held to the same suspicion
  as an unverified "done."

- **H26 [NEW, earned 2026-08-05]:** a claim about file corruption/encoding
  seen through a terminal (PowerShell `Get-Content`, a shell `cat`, etc.)
  must be checked at the byte level before being acted on — terminals apply
  their own codepage/encoding assumptions that can render clean UTF-8 as
  mojibake without the underlying bytes being wrong. This session: a
  reported `вЂ"` mojibake sequence in a patch file's comments was
  disproven by a direct byte search (zero occurrences, correct UTF-8
  em-dash present) — the terminal, not the file, was wrong. Cheap check,
  avoids unnecessary churn on clean files and avoids missing a real defect
  when the terminal happens to render garbage as looking fine.
## Session log (continued) — Session 031

- [2026-08-07, Session 031 -- open] Opened via session-strategy-synthesis.
  Fresh clone + git ls-remote established real origin HEAD = b731fe2,
  matching local. Every claim in the opening prompt re-verified CONFIRMED
  by content (Session 030 close landed, item 21 fix present, .gitignore
  *.pdf rule live, BACKLOG 28 patch wired not inert, H18 citation count
  risen to 7 exactly as predicted, test baseline reconciled: 546 committed
  + 9 (BACKLOG 28, uncommitted) = 555). Zero drift at open -- first fully
  clean open in the sessions this ledger covers.

- [2026-08-07, Session 031 -- real gate #1, Windows discovery] Yehor's
  first `python -m pytest` attempt ran from the wrong directory then the
  wrong (global 3.14) interpreter -- 23 collection errors, all
  environmental. The project's own `.venv` (3.14.4, every dev dep
  installed) was sitting one directory over the whole time; the agent's
  own earlier `ls .venv/bin/python` probe (Linux path) had returned "not
  found" and the agent concluded no venv existed without checking the
  Windows-native `.venv/Scripts/python.exe`. Real gate once pointed at the
  right interpreter: 555 passed / 3 skipped / 91.14%, coverage floor
  enforced -- reconciles exactly with the pre-session arithmetic. Also
  surfaced ~20 stale `RepoMend`-path `.pyc` files under
  `tests/__pycache__` (gitignored, nothing tracked, purged, harmless but
  confusing tracebacks).

- [2026-08-07, Session 031 -- priority disagreement, resolved] Yehor's
  synthesis review argued BACKLOG 29 (hosted path silently reports
  "pr_opened" on PR-creation failure) is the strict P0 by the board's own
  definition, not BACKLOG 28 (startup credential guard) -- confirmed by
  code: webhook.py:412 -> pipeline.py, and publish() pushes the branch
  BEFORE calling _create_pr(), so a permissions failure leaves a
  force-pushed branch on the CUSTOMER's repo with no PR and no error
  trail. Agreed and re-prioritized; BACKLOG 28's cold pass deferred to
  next session.

- [2026-08-07, Session 031 -- BACKLOG 29 authored] pipeline.py now
  branches on pr_dict["status"] in {opened, already_open, else} exactly
  as cli.py already did (mirrored, no invented vocabulary): pr_opened /
  pr_already_open / pr_failed (fail-closed default, reason preserved in
  result["error"]). Repaired a phantom test
  (test_run_repo_pipeline_pr_opened was truncated mid-statement, called
  run_repo_pipeline zero times, asserted nothing, counted as passing) and
  corrected a sibling fixture (test_run_log_none_does_not_crash's mock
  publish() result had no "status" key -- a shape the real publish()
  cannot produce). 3 new tests added for the branches. 8/8 mutations
  caught on a scratch copy (full revert, fail-open default, dropped error
  reason, collapsed already_open, leaked url on failure, dropped url on
  success, typo'd literal) -- zero silent survivors, restored
  byte-identical after.

- [2026-08-07, Session 031 -- real gate #2] Yehor's 3.14.4, coverage floor
  enforced: 558 passed / 3 skipped / 91.20% -- reconciles exactly against
  prediction (+3 tests, +9 statements in pipeline.py, zero new uncovered
  lines). Committed `66680c0` (3 files, tripwire stat matched: pipeline.py
  +68/-7, test_async_pipeline.py +168/-2, test_orchestrator.py +11/-1 --
  agent's own +171 restaging-note prediction was off by 3, corrected same
  turn). Pushed; landed on origin verified by `git ls-remote` AND an
  independent fresh clone (content grep for the fix, zero CRLF in the
  committed blobs, clean-clone suite 545 passed / 4 skipped -- the new
  committed-only baseline, distinct from the 558 gate figure that still
  includes BACKLOG 28's uncommitted patch).

- [2026-08-07, Session 031 -- credential item, resolved not carried]
  Traced the "110-char foreign credential, N sessions running" line
  through every SESSION_CLOSE file back to its origin (BACKLOG.md item 27,
  2026-07-28, overwritten 2026-07-29) and confirmed the carry-forward
  pattern was real: 07-29 -> 08-01 -> 08-04 ("five") -> 08-05 ("six") ->
  would have been a 7th uncorrected mention today. Ran a full
  identification sweep (git history all 810 objects, local .env, both
  PowerShell history profiles, all sibling D:\Dev\Projects folders,
  .fly/.config, Windows Credential Manager target names) -- found
  nowhere, with two real bugs in the sweep script caught and fixed
  mid-investigation before trusting the negative (nested `$_` shadowing
  produced a false 415-hit signal with a blank Source field; traced to
  three compiled flyctl binaries' embedded string tables, not user data,
  once the bug was fixed). Independently reconfirmed via a live `fly ssh`
  into the running container: all 4 Fly secrets read by length+prefix,
  none 110 chars. COULD NOT FIND IT is the honest, exhaustively-checked
  conclusion -- origin most likely a clipboard/password-manager-only
  paste, outside programmatic reach. Board language corrected (see
  BACKLOG.md item 27).

- [2026-08-07, Session 031 -- deploy + live verification, Tier 0] Yehor
  built and deployed a fresh image from `66680c0`
  (`deployment-01KZECVHTM3QQ62Q32YBBXRA8F`, machine `7841600fd5e7e8`
  version 6). Confirmed by direct `fly ssh console` grep against the
  RUNNING container's own `/app/src/patchward/pipeline.py`: lines
  252/288/290/298 match the committed source exactly (`pr_status =
  pr_dict.get("status", "")` at line 288, identical to the git-blob
  check). Full chain independently verified end to end: authored -> tested
  -> committed -> pushed -> deployed -> live-and-correct, each link
  checked separately rather than assumed from the one before it. Also
  observed: the machine scales to zero when idle (first `ssh console`
  attempt failed with "no started VMs"); a real HTTP request to /healthz
  woke it automatically -- expected Fly behavior, not a defect, worth
  knowing so a future stopped-machine reading isn't misdiagnosed. Also
  noted for precision: the local `.env`'s ANTHROPIC_API_KEY
  (`sk-ant-api03-o...`) and Fly's deployed ANTHROPIC_API_KEY
  (`sk-ant-api03-m...`) are two DIFFERENT valid keys, both separately
  confirmed clean -- not the same value duplicated.

## Session log (continued) — Session 031 CLOSE

- [2026-08-07, Session 031 -- close] Closed via session-close. Reconciled:
  origin HEAD `66680c0` == local HEAD, working tree carries exactly one
  real (CRLF-normalised) content change -- `webhook.py`/`test_webhook.py`,
  the still-uncommitted BACKLOG 28 patch, unchanged this session -- plus
  five untracked root artifacts (one more than the six-session-running
  count implied: this session added
  `credential_identification_2026-08-07.md`). No `.git/index.lock`,
  nothing staged at close. `memo section 7 step 4` (live site-copy check)
  untouched again -- fourth session running at close, not fifth; the
  actual count was re-traced from source this session rather than trusted
  forward.

## Calibration record (continued) — Session 031

Claims checked at close: 15. Confirmed: 14. Drifted: 1 (the agent's own
`test_async_pipeline.py` +171 line-count prediction in the staging
instructions; actual was +168 -- caught and corrected the same turn,
before Yehor staged anything on the wrong expectation). **Score 14/15 =
0.93.**

This session had two verification chains running simultaneously -- the
code chain (BACKLOG 29) and the memory-hygiene chain (the credential
item) -- and both closed clean, with the memory-hygiene chain notably
NOT trusting its own first negative result: a 415-"hit" false alarm was
investigated rather than reported, found to be a real scripting bug
(nested `$_` shadowing), fixed, and only then was the true zero-result
trusted. That is the session's best evidence that "verify, don't report"
is holding as a working discipline rather than a slogan repeated at
opens.

One inherited-claim correction, caught before it could compound: the
"110-char credential, N sessions running" framing itself, which the
opening synthesis's own reading-focus surfaced and this session then
independently traced and confirmed via 9 distinct sources rather than
either accepting the correction or the original framing on say-so alone.

Trend 026-031: this is the first session in the ledger where the deploy
and live-production claims were backed by an ACTUAL pasted transcript at
close rather than resting on Yehor's narration alone -- noted explicitly
because the agent flagged the gap mid-session (properly) before the
transcript arrived, rather than either accepting or rejecting the claim
without evidence.

## Heuristics — Session 031 update

- **H27 [NEW, earned 2026-08-07]:** a script with nested pipelines --
  `Get-ChildItem | ForEach-Object { ... Select-String ... | ForEach-Object
  { ... } }` -- silently shadows the outer block's `$_` inside the inner
  block. Any field populated from the outer `$_` (e.g. `$_.FullName`)
  inside the inner block will be empty/wrong with NO error raised. This
  session: a credential-sweep script's `Source` field was blank for all
  415 "hits"; the blank field was initially misread as a display
  artifact rather than a data bug, and only traced correctly after a
  `Group-Object` on the (blank) field failed to explain the count.
  Generalise: capture any value needed from an outer loop into an
  explicitly named variable BEFORE entering a nested pipeline stage, and
  treat an unexpectedly uniform or empty grouping key as a script-bug
  hypothesis to rule out before trusting either a "concentrated in one
  source" or a "clean negative" reading.

- **H14 [REINFORCED]:** this session's opening synthesis independently
  traced the "110-char credential, N sessions running" line through five
  SESSION_CLOSE files back to its 2026-07-29 origin before accepting or
  rejecting the recalibration offered mid-session -- and separately, the
  session declined to record a "deployed and live" claim as Tier 0 until
  an actual transcript arrived (it initially had only narration). Both
  are H14 held correctly under pressure to just accept a plausible,
  confidently-stated claim.

- **[CANDIDATE, 2026-08-07, single occurrence, not yet promotable]:** when
  a tool-access probe for a platform-specific path (e.g. `.venv/bin/
  python`) returns "not found," check the platform-native variant (e.g.
  `.venv/Scripts/python.exe` on Windows) before concluding the resource
  doesn't exist. The agent made exactly this mistake this session on its
  own Linux-path assumption against a Windows project.

## Session log (continued) — Session 032

- [2026-08-08, Session 032 — open] Opened at HEAD `cd532c0` ("close
  Session 031"). Zero drift at open — the opening prompt's claims
  re-verified by content before any work.
- [2026-08-08, Session 032 — `.gitattributes` landed `132f47a`] First
  `.gitattributes` in the repo: `* text=auto eol=lf` + CRLF pins for
  `*.ps1/*.bat/*.cmd`, binary pins for `*.png/*.jpg/*.pdf`, `*.patch
  -text`. Byte-verified BOM-free (`git show 132f47a:.gitattributes` opens
  `2a 20 74 65`, no `EF BB BF`).
- [2026-08-08, Session 032 — self-corrected path error] One real
  mid-session error: an interpreter/path assumption was stated wrong and
  self-caught before it cost anything. The gate interpreter is
  `D:\Dev\Projects\Patchward\.venv\Scripts\python.exe` (see H20 path
  correction below) — reached only after three wrong guesses, hence the
  H26 promotion.
- [2026-08-08, Session 032 — BACKLOG 28 closed `f653e77`] Startup
  credential-shape guard. Three adversarial rounds: v1 (substring-only) →
  v2 (F1–F5: real PEM parse both branches, consumer-exact B64 decode,
  ANTHROPIC min-length, ASCII-digit App-ID, +3 tests + F1 exploit repro) →
  v3 (F-A RSA-specificity in both branches, F-B consumer raw-first
  precedence, F-C discriminating B64 junk-PEM test, M1 cosmetic).
  **Third independent adversarial pass CLEAN.** Verified on origin by
  content: `isinstance(..., rsa.RSAPrivateKey)` in both branches
  (≈159/195), `if raw_key: ... elif b64_key:` precedence (≈140/164),
  value-free RSA failure messages (≈161/197). Real gate (Yehor's Windows
  3.14.4 `.venv`): **565 passed / 3 skipped / 15 deselected / 91.20%** —
  reconciles with the Linux 3.10.12 advisory (566/2/15/91.33%) by the
  exact +3 test delta; ±1 baseline and coverage delta are the known
  interpreter difference.
- [2026-08-08, Session 032 — REAL byte-level regression found at close,
  NOT caught by the three rounds] The close pass byte-checked
  `f653e77:webhook.py` and found it committed with a leading UTF-8 BOM
  (`EF BB BF`) and 29 mojibake em-dashes (`D0 B2 D0 82 E2 80 9D` = a
  UTF-8 em-dash misdecoded through CP1251). Attribution unambiguous:
  parent `132f47a` had no BOM / 0 mojibake / 21 clean em-dashes
  (`E2 80 94`); `f653e77` has BOM / 0 clean / 29 mojibake — a whole-file
  re-encode that corrupted 21 pre-existing em-dashes on lines the diff
  never touched, plus ~8 new. The delivered patch is clean; corruption
  entered on the Windows save/commit. Cosmetic (comments + preamble; gate
  unaffected) but a genuine content regression on origin/main that
  defeats the same session's `.gitattributes` intent. **This is the H20
  whole-file-rewrite hazard realized on origin, and — unlike Session
  030's false alarm — a real H26 hit.** Carried forward as a P0-adjacent
  fix (strip BOM, restore em-dashes, one-line commit).

## Session log (continued) — Session 032 CLOSE

- [2026-08-08, Session 032 — close] Closed via session-close. Reconciled:
  local HEAD `f653e77` == `origin/main` by `git ls-remote`. Two commits
  landed (`132f47a`, `f653e77`); nothing staged/committed by the agent
  (H20). One stale `.git/index.lock` present in the mount, un-unlinkable
  (`Operation not permitted`) — a mount-permission artifact, not a live
  git op; status reads clean through it. L2 goal (close BACKLOG 28 with a
  verified three-round fix) = **MET on the security logic**, with the
  honest asterisk that a byte-level encoding regression escaped all three
  logic-focused rounds and reached origin — caught only at close. L1: the
  startup-credential-guard class from item 27/28 is now closed in code,
  though not yet exercised on Fly.

## Calibration record (continued) — Session 032

Claims checked at close: 8. Confirmed: 7. Failed: 1 — and the failure is
material, not a rounding artifact: "BACKLOG 28 landed clean on `f653e77`"
is FALSE at the byte level (BOM + 29 mojibake em-dashes), even though the
security logic it landed is correct and gate-verified. **Score 7/8 =
0.88.**

Honest reasoning, not rounded up: the security work itself is the
session's strongest — a genuine three-round adversarial fix where each
round closed the prior round's residue (substring bypass → parseable-≠-RSA
→ consumer-precedence), CLEAN on an independent third pass, reconciled to
the real gate. Opened with zero drift; the one mid-session path error was
self-corrected before cost. But the encoding regression is the counter-
weight: three consecutive adversarial reviews all scoped themselves to
logic and none looked at the file's bytes, so a real content regression
rode a security commit onto main and would have been recorded as "landed
clean" had the close not byte-checked it. The calibration system worked
(the close caught it); the session's own review discipline had a
blind spot (encoding was never in scope). Scored to reflect both: high
competence on the intended work, one real escaped defect.

Trend 030-032: the close-time byte check is now earning its keep in the
affirmative direction — Session 030 it prevented churn on a clean file
(false alarm), Session 032 it caught a real regression. Same discipline,
opposite outcome, both correct.

## Heuristics — Session 032 update

- **H20 [PATH CORRECTION, 2026-08-08]:** the standing "Yehor stages and
  commits on Windows" rule now carries the verified gate-interpreter path.
  It is **`D:\Dev\Projects\Patchward\.venv\Scripts\python.exe` (Python
  3.14.4, nested inside the repo, gitignored — NOT a sibling folder).
  Verified 2026-08-08 by direct filesystem check (three prior wrong
  guesses before this was checked — see H26).** Use this exact path in
  every handoff; never restate the venv as a sibling folder
  (`...\Patchward.venv`) or as "one directory over." The whole-file
  rewrite hazard H20 warns of was realized on origin this session (BOM +
  mojibake on `f653e77:webhook.py`) — the rule earned a live example.

- **H26 [PROMOTED — 3rd occurrence, standing]:** check terminal-rendered
  corruption/encoding at the byte level before acting on it. 3rd
  occurrence is the affirmative case: the close-out byte-checked
  `f653e77:webhook.py` and found REAL BOM + 29 mojibake em-dashes
  (`D0 B2 D0 82 E2 80 9D`), where Session 030's identical symptom was a
  terminal false alarm. The check cuts both ways — avoids churn on clean
  files AND catches genuine corruption a glance would rationalize away.
  Promote to standing: byte-verify any encoding claim, positive or
  negative, before recording it.

- **H29 [PROMOTED — earned 2026-08-08, 2 occurrences within one patch]:**
  a boot/shape guard must mirror the CONSUMER's exact contract, not a
  looser proxy — the specific key TYPE the consumer needs (RSA for RS256,
  not merely "parseable") AND the consumer's precedence/order (raw key
  first, B64 only if raw absent — not both fields independently). Two
  occurrences in the single v3 patch: F-A (accepted any parseable key →
  false-pass of an unusable EC/Ed25519 key) and F-B (validated B64
  unconditionally → false-boot of a valid raw + stale-B64 config).
  Sibling of H24: re-derive the consumer's real requirement from its
  source, don't infer it from the field's surface shape.

- **H28 [CANDIDATE — 2026-08-08, 2 occurrences, needs one more]:** a
  validation that matches a credential by structural resemblance (a
  substring like `"PRIVATE KEY"`, a prefix, "looks like a PEM") rather
  than by performing the consumer's real operation (parse / decode /
  type-check) is a bypass waiting for input that resembles-but-isn't. Two
  occurrences: v1's substring check accepted junk in the raw branch (F1)
  and the same proxy in the B64 branch accepted the same junk after
  decode (F1/F-C). Reinforces H23 with dual-site evidence.

## Session log (continued) — Session 033

- [2026-08-11, Session 033 — open] Resumed via session-strategy-synthesis,
  grounded fresh against this file. Scope expanded mid-session, at Yehor's
  direction, well beyond the Session 032 carry-forward items: a reusable
  multi-model research-synthesis method, a full brand/funnel redesign for
  Patchward (research prompt → 4-model synthesis → tiered build doc →
  lookbook → hero prototype), and — once scoped as its own domain-owning
  product — a brand-new sibling repo, `patchward-landing`
  (`D:\Dev\Projects\patchward-landing`), built, deployed, and DNS-fixed
  same session. Full detail: `memory/SESSION_CLOSE_2026-08-11.md`.
- [2026-08-11, Session 033 — P0(b) finally touched] The live site-copy
  check carried since Session 032 was done: found a real overclaim on
  `callmedai.com` (the Gate-3 disclosure implied it always runs/gates the
  PR). Corrected copy drafted, right-sized in severity once the
  pilot-delivery mechanism was independently resolved (CLI, not hosted) —
  **not yet applied to the live site; still open.**
- [2026-08-11, Session 033 — pilot-delivery mechanism resolved by
  forensic tracing] Not narration: git commit dates, GitHub API state, and
  the live `callmedai.com` CTA's own `href` together proved pilots are
  delivered CLI, run by Yehor directly against the customer's repo, not
  via any hosted webhook/App-install flow yet. This corrected a real
  assumption baked into earlier drafts and is now the canonical `/facts`
  and `/limits` entry on the new site.
- [2026-08-11, Session 033 — `patchward-landing` shipped] Astro 7 (stale
  "6.x current" guide-model claim independently corrected against
  `docs.astro.build` before scaffolding), single-source-of-truth
  `facts.yaml`, both light/dark palettes real-WCAG-computed (catching and
  fixing a genuine dark-mode accent/link contrast gap before it shipped).
  Sandbox build limitation (`esbuild`/Astro Rust compiler segfault here
  specifically) correctly diagnosed and reported as UNRUN rather than
  claimed passing — Yehor's own `npm run dev` and later
  `wrangler pages deploy` are the real build/deploy evidence.
- [2026-08-11, Session 033 — `patchward.dev` "Hello world" bug, root
  cause + fix] Two Cloudflare resources shared the name
  `patchward-landing`: the real Pages project (correct, deployed, no
  custom domain attached) and a stray, separately Git-connected, failing
  Worker that held the `patchward.dev` Custom Domain binding and was
  serving Cloudflare's placeholder content. First reattachment attempt
  silently reverted (caught by a fresh reload, not trusted from the same
  session's rendered state); the actual fix was deleting the broken
  Worker outright, then reattaching the domain — this time verified
  Active/SSL at close. Full forensic trail: SESSION_CLOSE_2026-08-11.md.
- [2026-08-11, Session 033 — GitHub profile README overclaim corrected]
  Flagged a false "PR merged" claim on the live profile's checkdmarc
  track-record row (it was actually closed-as-superseded, credited).
  Yehor applied his own further-evolved version of the README, not this
  agent's draft verbatim — the specific overclaim fix was confirmed live
  at close regardless.

## Session log (continued) — Session 033 CLOSE

- [2026-08-11, Session 033 — close] Closed via session-close. Patchward
  repo: HEAD `76274e4` == origin/main, unchanged this session, nothing
  staged/committed by the agent (H20). `patchward-landing` repo: HEAD
  `fcc0af4` == origin/main, working tree clean — Yehor staged, committed,
  and pushed it himself. L2 goal, as it crystallized mid-session
  ("we have to get a visible site patchward.dev today") = **MET**, with
  fresh Tier-0 evidence at close (Active/SSL status, live-fetched correct
  content, `/facts` rendering, single clean resource in the Cloudflare
  account). L1: real horizon progress — Patchward went from having no
  dedicated product site to a live, on-brand, WCAG-verified site with a
  canonical facts ledger that structurally prevents future staleness, plus
  a documented, non-obvious Cloudflare Workers-vs-Pages platform gotcha
  that would otherwise resurface. Also created `patchward-landing/memory/`
  at close, seeded with the cited research artifacts (build doc, lookbook,
  research prompt) — that repo's own README already cited these filenames
  and they would have dangled once this session's scratchpad cleared.

## Calibration record (continued) — Session 033

Claims checked at close: 9 (patchward.dev Active/SSL status; live content
match; /facts rendering; single clean Cloudflare resource; Patchward repo
git state; patchward-landing repo git state; GitHub README overclaim fix;
site-copy-check overclaim finding itself; pilot-delivery-CLI conclusion).
Confirmed: 9. **Score 9/9 = 1.00** — but read this honestly, not as a
perfect session: several claims from earlier in the session were
self-corrected mid-stream before they ever reached a "close" checkpoint
(a stale Astro-6 pin, a silently-reverted domain reattachment, an
unverified "npm run build passed" claim from a guide-model narrative that
was explicitly declined rather than recorded) — the 1.00 reflects that
close-time verification caught zero NEW drift, not that the session had
zero drift to catch. The real evidence of discipline is the mid-session
catches, not the clean final tally.

## Heuristics — Session 033 update

- **[NEW, CANDIDATE, 2026-08-11]:** Cloudflare Workers and Pages projects
  can share an identical name as fully independent resources with
  independent Custom Domain ownership — whichever holds the zone's
  binding wins regardless of which has the real content. Single
  occurrence; promote on a second sighting.
- **[NEW, CANDIDATE, 2026-08-11]:** a SaaS dashboard's in-session
  "success" state needs a fresh-reload re-check before being trusted,
  the same discipline H13/H16 already apply to git — generalizes beyond
  git specifically. Single occurrence (a domain-reattachment silently
  reverted); promote on a second sighting in a different platform.
- **[NEW, CANDIDATE, 2026-08-11]:** browser-automation screenshots can
  render blank/stale at specific scroll positions in virtualized-list
  dashboard UIs even when the underlying DOM/click targets are valid
  (`get_page_text` and ref-based clicks stayed reliable through it, raw
  coordinates and visual screenshot confirmation did not). On a
  reversible action, push through with ref+text verification; on an
  irreversible one (delete), hand the physical click to the human.
- **[NEW, CANDIDATE, 2026-08-11, 2nd sighting of the SAME artifact —
  worth watching for promotion]:** the `.git/index.lock` first flagged as
  a "sandbox-mount permission artifact, not blocking" at Session 032's
  close (2026-08-08) was STILL present three days later at Session 033's
  close and this time actively blocked Yehor's real `git add`/`commit` on
  Windows. The sandbox still cannot remove it (`Operation not permitted`,
  same as Session 032). Generalize: a "harmless artifact" note in a close
  doc should include an expiry check — re-verify it's still harmless at
  the START of the next session that touches that repo, not assume it
  stays inert indefinitely. One more recurrence of an assumed-benign
  artifact turning out to matter later would promote this.

## Session log (continued) — Session 034

- [2026-08-14, Session 034 — open] Handoff prompt claimed two P0s open:
  (a) `webhook.py`'s BOM/mojibake regression "still unfixed, 2 sessions
  untouched," and (b) `patchward.dev` serving Cloudflare's stock "Hello
  world" placeholder. Both were STALE, settled by content against a fresh
  clone of `origin/main`, not by reading either claim. (a): byte-checked
  `src/patchward/webhook.py` at `2af845c` (local HEAD == `origin/main` via
  `git ls-remote`, no drift) — BOM absent, 0 mojibake, 29 clean em-dashes;
  `aa76eca` (2026-08-08) is the fix commit AND the last commit to touch
  the file, confirmed via `git log --oneline -- src/patchward/webhook.py`
  in the fresh clone — nothing re-corrupted it after the fix. (b): fresh
  `curl` to `https://patchward.dev` → HTTP 200, clean TLS, real A records
  now present (`104.21.44.172`, `172.67.201.154`, previously absent per
  the Worker-routing artifact) + AAAA, served HTML contains the real
  tagline and "565 passed" figure, zero "hello world" occurrences. Both
  struck from the board at open. Full detail:
  `memory/session034_ground_verify_2026-08-14.md`.
- [2026-08-14, Session 034 — suspicious injected content, handled
  correctly] Text resembling a tool-call transcript (a fabricated `Read`
  result for a file path) appeared embedded inside a pasted user message,
  without having actually been executed by any tool this session. Refused
  to treat it as evidence; independently re-verified via a real `Read`/
  `ls` call instead. In this instance the underlying file turned out to
  be genuine (matched byte-for-byte once actually read), but the
  discipline — never trust a tool-output-shaped artifact that wasn't
  observed being produced — held regardless of how that instance
  resolved. Origin of the embedded content unknown; worth Yehor's own
  awareness of where it came from, not something this agent can trace.
- [2026-08-14, Session 034 — P0(new): Gate-3 copy fix on callmedai.com,
  found, applied, and verified] `memory/patchward_site_copy_check_2026-08-11.md`
  (Session 033 finding, never applied) re-verified fresh against a live
  fetch of `callmedai.com` before touching anything — both overclaims
  ("Gate 3: test suite must pass," "371 tests / 89% coverage") still
  present verbatim, unchanged since 2026-08-11. **Real near-miss caught
  before a production edit:** the locally-cloned folder named `callmedai`
  (`C:\Users\truff\callmedai`) was NOT the site source — content-checked
  (`grep` for the overclaim text, zero matches) and found to be a wholly
  unrelated Next.js voice-receptionist project (`CallMedAi.git`, HEAD
  `ba6dd86`, "Sarah v2"). The real source, `callmed-landing`
  (`github.com/yehorcallmedai-maker/callmed-landing`), had never been
  cloned to this machine at all; identified by content (both overclaim
  phrases present in `index.html`/`security.html` of a fresh clone) and
  cross-referenced against this file's own Session 032 note citing HEAD
  `68e612a` for the same repo — matched exactly. Applied Section 3's
  corrected copy to `index.html` (verbatim) and a hand-drafted equivalent
  correction to `security.html` (the report's literal "Finding 2" text
  did not match that file's actual wording — same substantive overclaim,
  different phrasing — so the fix was re-derived to fit the real sentence
  rather than force-pasted). Diff shown to Yehor before any git operation
  (2 files, 4 insertions/4 deletions — passed the H20-style
  whole-file-rewrite tripwire); Yehor reviewed, staged, committed
  (`7403348`), and pushed himself. Verified DONE, by content, on two
  independent surfaces after Cloudflare Pages' dashboard confirmed the
  deploy succeeded: `callmedai.com` and the `callmed-landing.pages.dev`
  deployment alias both show 0 "test suite must pass," 0 "371 tests," 1
  "565 passing tests." An intermediate re-fetch (immediately post-push,
  pre-deploy) showed the OLD content still live — correctly not treated
  as a failure, since `cf-cache-status: DYNAMIC` ruled out a caching
  explanation; resolved by checking the Cloudflare Pages dashboard
  directly (found the build genuinely still in flight) rather than
  guessing with a wait-and-retry.
- [2026-08-14, Session 034 — synthesis skill placed] The
  `multi-model-research-synthesis` skill (reviewed/amended earlier this
  session per the user, six gaps fixed) had never been written to disk
  anywhere — not in `patchward-landing`, not anywhere under
  `D:\Dev\Projects`, and `C:\Users\truff\.claude\skills\` did not exist
  at all prior to tonight. Re-materialized content (not re-authored)
  placed verbatim at
  `C:\Users\truff\.claude\skills\multi-model-research-synthesis\SKILL.md`
  — byte-count matched the source exactly (10691 = 10691) both
  immediately after placement and again at close.
  `patchward-landing/memory/patchward_brand_research_STEPS.md` (a
  legitimate secondary usage-guide referencing the skill) confirmed
  untouched, same mtime and byte count throughout. **Genuinely open, not
  swept under "done":** whether this environment auto-discovers a
  personal skill added mid-session could not be tested from inside the
  same running session (`ListSkills` queries a separate cloud registry;
  this session's own available-skills list was fixed at startup) —
  flagged as UNVERIFIED rather than asserted, carried to next session's
  opening prompt as a ten-second check.

## Session log (continued) — Session 034 CLOSE

- [2026-08-14, Session 034 — close] Closed via session-close. Patchward:
  local HEAD `2af845c` == `origin/main` (re-confirmed via `git ls-remote`
  at close), unchanged all session — the only diffs are this file
  (+63 lines, pure append, 0 deletions) and one new untracked memory file
  (`patchward_site_copy_check_2026-08-11.md`), neither staged nor
  committed by the agent (H20 standing rule). patchward-landing: HEAD
  `599ed04` == origin, working tree fully clean, zero changes this
  session. `webhook.py`, `patchward.dev`, and `callmedai.com` all
  re-verified a second time at close via methods independent of the
  open-of-session checks (fresh `git pull` on the standing verification
  clone; fresh `curl` to both live domains) — all three identical to
  their open/mid-session results, no regression. L2 goal ("verify
  session-open state, settle the contradicted claims by content, close
  whatever real P0s the verification surfaces") = **MET** — 2 stale P0
  claims struck with fresh Tier-0 evidence, 1 real previously-open P0
  (the `callmedai.com` Gate-3 overclaim) found, fixed, shipped, and
  verified live on two independent surfaces. L1: modest, real horizon
  progress — a live customer-facing overclaim corrected, and a reusable
  research-synthesis method given a permanent, product-agnostic home
  for the first time. Full detail: `memory/SESSION_CLOSE_2026-08-14.md`.

## Calibration record (continued) — Session 034

Claims checked at close: 17 (Patchward HEAD/drift, patchward-landing
HEAD/drift, webhook.py byte-check + last-touch commit, patchward.dev
liveness/content, the CallMedAi-folder near-miss ruled out by content,
callmed-landing's identity cross-referenced against this file's own
Session 032 hash, the Gate-3 diff's minimality, the push landing, the
Cloudflare Pages deploy completing, the post-deploy live content on two
surfaces, the STRATEGY.md append's cleanliness, the skill's byte-exact
placement, STEPS.md's non-interference, and skill auto-discoverability).
**16 CONFIRMED, 1 correctly flagged UNVERIFIED (skill auto-discovery —
a genuine environment limitation, not a shortcut; same distinction this
file has drawn before, e.g. Session 022 close's private-repo-hash case).
Score 16/17 ≈ 0.94.**

Two process incidents worth calibration attention, not claim-scored but
real: (1) text shaped like a tool-call transcript, embedded in a pasted
user message without having actually been executed by any tool this
session, occurred **twice** tonight — both refused as evidence and
independently re-verified, both turned out to reference genuine files.
Correct handling both times; origin of the embedded content itself
stays unexplained. (2) A real near-miss — an unrelated, same-named local
folder (`CallMedAi`/"Sarah") could have received a live production edit
intended for a different repo entirely, caught only because content was
checked before name was trusted. Both are logged in Open threads/
Heuristics below rather than left as narrative color.

## Heuristics — Session 034 update

- **[NEW, CANDIDATE, 2026-08-14, 2 occurrences — both this session, not
  yet tested across a session boundary]:** content shaped exactly like a
  tool-call transcript (e.g. a fabricated `Read` result) can appear
  embedded inside a pasted user message without any tool having actually
  produced it. Never treat it as evidence on the strength of its
  formatting alone — independently re-run the equivalent check with a
  real tool call before relying on it. Both occurrences tonight resolved
  benign (the underlying files were genuine once actually checked), but
  the discipline is what mattered, not the outcome — promote on a third
  occurrence, ideally in a future session.
- **[NEW, CANDIDATE, 2026-08-14, 1 occurrence]:** a local folder or repo
  name matching what's expected is not evidence of identity — verify by
  content (does it actually contain what the target should contain)
  before any edit, especially before one that touches a live/production
  surface. Generalizes Session 033's Cloudflare-Workers-vs-Pages
  same-name finding beyond that one platform. Promote on a second
  sighting in a different context.
