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
- [2026-08-19, Session 036 close] Both repos' verified current HEADs, so
  a future session doesn't have to dig through session-log entries to
  find them: **Patchward** `cbb83aa0a1056bb2c5c00420a0558b4a15b61f2a`;
  **patchward-landing** `6f98bc46546e16ed7afe9e0181ff13dd40bd4cde`, clean.
  Both confirmed via `ls-remote` + sha256 content match against origin
  (twice each). `STRATEGY.md` itself is now **52,359 bytes** (was
  192,908 at Session 035 close — see Open threads for the compression
  record); `.strategy/RETROSPECTIVE.md` exists as its cold-storage
  companion, 154,004 bytes, byte-verified against the archived original.

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
- [2026-08-19, Session 036, restored during Option A compression's
  loss-check] Test-suite baseline was previously findable only inside an
  archived Session-021 narrative entry — now relocated to
  `.strategy/RETROSPECTIVE.md` by this compression pass. Restoring it as
  its own bullet so it stays live-visible: **565 passed / 3 skipped /
  91.20% coverage**, source Yehor's machine (Python 3.14.4).
  Independently re-confirmed 2026-08-19 against patchward.dev/facts' own
  canonical ledger (test-count and coverage entries, both dated
  2026-08-08) — matches exactly. This was never a Current-state bullet
  in its own right before; it should have been.

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
- [2026-08-15] **Retrospective DUE — OD1–OD4's new session-close Phase 5
  item 6 check, hand-exercised against the real file this session,
  flagged this file as over-ceiling.** `.strategy/STRATEGY.md` measured
  **183,346 bytes** (fresh `wc -c`, not reused from any prior session's
  figure) against the **16,000-byte hot-file ceiling** — 167,346 bytes
  over, ~11.5x the limit. Second trigger also fired independently: the
  top-level Session log section counts **78** dated entries against the
  ~15-entry compression threshold `references/memory-format.md` already
  specified (that 78 is itself an undercount — see the refinement note
  below). Per the check's own rule, this is a **flag only, not an
  auto-compression** — no file was mutated by this check or by logging
  it here. Compression stays a separate, explicitly user-approved pass
  whenever it's next scheduled, same standing precedent as every prior
  session's handling of this file.
- [2026-08-15] **Known refinement candidate, not a blocker:** Phase 5
  item 6's entry-count trigger undercounts. The 78 figure above excludes
  the fragmented "Session log (continued)" / "Session log (close)" /
  "POST-CLOSE ADDENDUM" sub-section headers this file has accumulated
  (see the existing Session-024-flagged memory-hygiene item elsewhere in
  this Open threads list) — the true entry count is higher than what
  triggered the flag. The byte-ceiling trigger is unaffected and remains
  accurate on its own. Low priority: both triggers already correctly
  flagged DUE regardless of the undercount, so the imperfection doesn't
  change today's verdict — worth fixing whenever the entry-count logic
  itself is next revisited, not urgent.
- [2026-08-15] **`patchward-landing/memory/ROLLBACK-session-close-2026-08-15.md`
  and `ROLLBACK-session-strategy-synthesis-2026-08-15.md` are deliberately
  untracked and must stay that way, not accidentally cleaned up.** They
  are the only durable copy anywhere of the pre-OD1–OD4 skill content —
  skills live in an account-level registry, not git, so there is no other
  recovery path. Explicitly not the same situation as the 5-file
  untracked-artifact backlog Yehor just closed at `1f89701` (those were
  dangling and citation-orphaned; these are an active safety net) — flagged
  here specifically so a future cleanup pass doesn't conflate the two.
- [2026-08-15] **`.git/index.lock` recurrence, refined, not fully
  resolved.** Reappeared again this session in both Patchward and (for
  the first time) `patchward-landing` — but this time correlated against
  timestamps: it is created by this sandbox's own git *read* commands
  (`git status`, `git show`) against the mount, and is absent immediately
  after Yehor's real commits land on his own machine. His two real
  commits this session (`944d10c`, `1f89701`) both succeeded with no
  lock-related failure. This complicates, without fully overturning,
  Session 033's finding that the same-looking lock "actively blocked" a
  real commit — possibly a different root cause producing the same
  symptom, possibly the same cause behaving differently under different
  conditions. Genuinely unresolved; worth a session that reproduces
  Session 033's exact blocked-commit conditions before this gets a
  heuristic, not just narrative correlation.

- [2026-08-19, Session 036, gap found during Option A compression's
  loss-check — not previously recorded anywhere in this file] The four
  patchward-landing lookbook pages (`/how-it-works`, `/verification`,
  `/data-boundary`, `/examples`) are the one pure forward-construction
  item on the board. Confirmed still unstarted this session:
  `src/pages/` holds only `index.astro`, `facts.astro`, `limits.astro`.
  L2 candidate for a future session; deferred this session in favor of
  this compression pass (Yehor's explicit choice, 2026-08-19).

- [2026-08-19, Session 036, STRATEGY.md compression — Option A, CLOSED]:
  192,908 → 50,776 bytes (3.9× reduction). Archive-only: Sessions
  019-034's session-log/calibration/heuristics-update narrative moved
  verbatim to `.strategy/RETROSPECTIVE.md` (byte-verified against the
  pre-compression backup, `memory/PRE-COMPRESSION-STRATEGY-2026-08-19.md`,
  sha256 `e7fff711248c164686d8ed0d62c33295ab8e5e58dcfc922ce69cc972a927ef56`).
  Two rounds of loss-check: round 1 caught two narrative-buried facts
  (test baseline, lookbook-pages gap) and restored them as proper
  bullets; round 2, after independent review flagged that the canonical
  Heuristics section had only ever held H1-H8 even before compression,
  restored all 14 additionally-earned heuristics (H11-H14, H16, H18,
  H20-22, H24-27, H29 — 22 total earned/promoted, not the 28 first
  claimed by that same review, which also asserted a fabricated "H19,
  retired" that does not exist anywhere in this file's history) plus 6
  still-open candidates, all now live rather than buried in per-session
  blocks. Final size is higher than Option A's original ~42-43K estimate
  because restoring full operational force for 14 heuristics — including
  H20, the hard "never commit from sandbox" rule — was correct and
  non-negotiable, not scope creep. **Still 3.2× over the 16,000-byte
  ceiling** — Part B (rewriting Current state/Open threads for genuine
  compliance) remains undone, a separate future decision, not today's.
  Not yet committed to git — pending Yehor's own `git add`/commit/push
  per H20.

- [2026-08-19, Session 036, addendum to the compression entry above]
  Committed and pushed: `Patchward` commit `cbb83aa0a1056bb2c5c00420a0558b4a15b61f2a`.
  Verified landed on origin via independent `fetch`+`ls-remote`+sha256
  content comparison of both changed files, run twice (once immediately
  after push, once again at this session's formal close) — not trusted
  from the push command's own output. The "not yet committed" language
  in the entry above is now stale; left as-written per this file's own
  never-launder-history rule, corrected here instead.
- [2026-08-19, Session 036] The `.git/index.lock` sandbox-vs-real-client
  correlation flagged as "disclosed but unresolved" at Session 035's
  close is now RESOLVED: two independent occurrences this session
  (patchward-landing at session open, Patchward at commit time) both
  diagnosed identically as stale orphan locks (0 bytes, mtime
  immediately after the last real index write, 4 days old, no live
  `git` process), never genuine contention. See Heuristics, H30.

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

- H11 [PROMOTED 2026-07-27]: an adversarial pass on one security boundary
  reliably enumerates adjacent boundaries — budget every security close
  to spawn successors; scope-and-log spin-offs as separate reviewable
  units, never record "clean" if the pass spawned new items.
- H12 [PROMOTED 2026-07-27]: for credential-boundary code on an
  internet-facing surface, an independent adversarial pass (different
  model instance, patch-only) must run until it finds zero LEAKS/
  BLOCKERS — that result, not reviewer confidence, is the ship signal.
  Non-deterministically-testable fixes: mark construction/review-
  verified, never fabricate a test to fake coverage.
- H13 [PROMOTED 2026-07-28]: an artifact's self-description (docstring,
  commit message, this project's own backlog entry) is a claim, not a
  fact — re-verify an item's own load-bearing premises against the tree
  before scoping work that depends on them.
- H14 [PROMOTED 2026-07-28, REINFORCED 4x through Session 028 — this
  project's most reliable drift signature]: a user-asserted or
  self-asserted state claim is a hypothesis; instructions built on one
  inherit its uncertainty. Verify the premise against the tree
  (`git log`/`ls-remote`/fresh clone) BEFORE executing any chain built
  on it — especially an inherited plan's first step being "reconcile X
  into memory," which routinely turns out already done. Standing
  pre-check at every session open.
- H16 [PROMOTED 2026-07-28, REINFORCED 5x through Session 027]: on this
  Windows-origin repo, sandbox `git status`/diff is noisy by default
  (mixed CRLF/LF across the mount/checkout boundary) — never report a
  hash or diff mismatch until line endings are eliminated as the cause
  (`git diff -w`, `tr -d '\r'`); when a hash genuinely mismatches, trace
  which commit/transformation produces it before reporting the mismatch
  itself as the finding.
- H18 [PROMOTED 2026-08-01, confirmed 2026-08-04]: when a commit adds a
  pointer/reference to a file, verify the file itself is actually
  tracked (`git cat-file -e HEAD:<path>` or fresh-clone `ls-files`) —
  run the check on inherited references too, not only files the current
  commit touches.
- **H20 [HARD RULE, earned 2026-08-04, path-corrected 2026-08-08]:**
  never `git add`/`commit`/push from the agent sandbox on this repo.
  Sandbox git has no `core.autocrlf`/`.gitattributes`, so a sandbox
  commit rewrites line endings and pollutes history irreversibly
  (realized on origin once — BOM + mojibake on `f653e77:webhook.py`).
  Agent prepares and verifies only; Yehor stages and commits on
  Windows, at `D:\Dev\Projects\Patchward\.venv\Scripts\python.exe`
  (nested in-repo, gitignored — not a sibling folder). Tripwire before
  every push: `git diff --cached --stat` shows only the expected small
  line counts.
- H21 [NEW, earned 2026-08-04]: a failing adversarial result is a claim
  about the test harness until the harness itself is verified — confirm
  the environment actually runs what it claims to (e.g. does `python`
  resolve to a real interpreter with pytest installed) before reporting
  a security finding, especially against your own work.
- H22 [NEW, earned 2026-08-04, REINFORCED]: mocked tests prove
  BRANCHING, not BEHAVIOUR — where a test is the sole evidence for a
  security guarantee it must be unmocked, paired with a mutation check
  (delete the defense, confirm the test goes red for every load-bearing
  line, not just the headline one).
- H24 [NEW, earned 2026-08-05]: a security-fix spec naming ONE seam must
  be checked against every SIBLING consumer of the same resource class
  before being trusted complete — grep every consumer of the
  credential's old source, not just the call site the spec named.
  (Sibling of H29.)
- H25 [NEW, earned 2026-08-05]: "CLEAN" from an adversarial pass is only
  as strong as what it demonstrably broke, not what it re-read — a real
  clean verdict reverts each load-bearing line individually and confirms
  each reversion breaks a specific test, then restores and reconfirms
  green.
- H26 [NEW 2026-08-05, PROMOTED — 3rd occurrence, standing]: byte-verify
  any file-corruption/encoding claim, positive or negative, before
  acting on it — terminals apply codepage assumptions that can render
  clean UTF-8 as mojibake, or mask a real BOM/mojibake as looking fine.
  The check cuts both ways; verified both directions on this project.
- H27 [NEW, earned 2026-08-07]: nested PowerShell pipelines silently
  shadow the outer block's `$_` — capture any outer-loop value into an
  explicitly named variable before entering a nested pipeline stage;
  treat a uniform or empty grouping key as a script-bug hypothesis to
  rule out before trusting either reading of the result.
- H29 [PROMOTED — earned 2026-08-08]: a boot/shape guard must mirror the
  CONSUMER's exact contract — specific key type AND precedence/order,
  not a looser proxy — re-derive the requirement from the consumer's
  source, don't infer it from the field's surface shape. (Sibling of
  H24.)

Heuristics — candidates (not yet promoted, carried forward so a future
session doesn't rediscover a pattern already being tracked):
- H9-candidate [1 occurrence]: after a reported memory-file
  commit/push, independently diff the mount's current copy against a
  fresh clone of the pushed HEAD, not just the hash — and prefer Yehor's
  own direct git output over the agent's device-bridge reads when they
  disagree.
- H10-candidate [applied twice, not advanced]: corroborate an
  exact-content web claim (WebFetch) with a real browser read when the
  claim matters and cheaply can be.
- H15-candidate [1 occurrence]: when a claim turns on what a BUILT
  ARTIFACT contains, build it and read its own metadata rather than
  reasoning from the source config that feeds it.
- H17-candidate [1 occurrence]: validate a credential's shape/validity
  LOCALLY before deploying it remotely, to break bad-secret redeploy
  cycles.
- H23 [CANDIDATE, 2 occurrences incl. dual-site]: a security proxy check
  must perform the consumer's real operation (parse/decode/type-check),
  not a resemblance check — a bypass waiting for input that
  resembles-but-isn't.
- H28 [CANDIDATE, 2 occurrences — text as originally logged explicitly
  reads "reinforces H23"; possible mislabeling in the source, preserved
  as-written rather than silently resolved]: validation matching a
  credential by structural resemblance rather than by performing the
  consumer's real operation is a bypass waiting for input that
  resembles-but-isn't.

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

- [2026-07-15..2026-08-14, Sessions 019-034, 16 sessions — COMPRESSED
  2026-08-19 per `memory-format.md`'s ~15-entry threshold, Option A
  archive-only pass]: Bootstrapped this memory file (019); closed
  BACKLOG item 5 across 019-021 (Phase 9 webhook hardening — rate
  limiter moved to run after HMAC verification closing a starvation
  vector, env-parser range validation via `math.isfinite()`, 10
  negative-control tests); PyPI publish chain verified live via OIDC
  Trusted Publisher, `patchward` v0.1.0 shipped; callmed-landing copy
  renamed RepoMend → Patchward (45→0 grep hits); test suite grew toward
  483 passed, tracked each session via independent per-commit diff
  counts rather than trusted self-reports; two benign prompt-injection-
  shaped messages detected and correctly handled in Session 034 (two
  more followed in 035, logged there); the OD1-OD4 memory-architecture
  research ran across 5 models in 034's post-close addendum and resolved
  into the decisions Session 035 later implemented (retrospective folded
  into the existing skill pair, kept in a separate file — this one —
  16,000-byte hot-file ceiling) — full research prompt and synthesis at
  `memory/session_retro_research_prompt_v1_2026-08-14.md` and
  `memory/session_retro_synthesis_v1_2026-08-14.md`, not duplicated
  here. **14 heuristics promoted/earned in this span — H11, H12, H13,
  H14, H16, H18, H20 (hard rule), H21, H22, H24, H25, H26, H27, H29 —
  all now restored to the live Heuristics (earned) section above in
  condensed form** (corrected 2026-08-19: an earlier draft of this
  compression under-restored these to only 8, missing H20-22/24/25/27
  because their first-tag text read "[NEW, earned...]" rather than
  literally "[PROMOTED...]" — caught on review before anything was
  committed). 6 more heuristics remain candidates, never promoted in
  this span (H9, H10, H15, H17, H23, H28) — also carried forward live,
  not archived. Calibration across the 11 sessions with a recorded
  score: 1.00 (×6), 0.94 (×2), 0.86, 0.75 — the single sub-0.90 outlier
  (0.75, Session 021 open) was this project's first-ever score below
  1.00, driven by one genuine drifted claim (a mojibake report that
  didn't reproduce), not a memory-hygiene failure. Full session-by-
  session log, calibration entries, and the full narrative
  justification behind every heuristic above (verbatim, unabridged):
  `.strategy/RETROSPECTIVE.md`.

## Session log (continued) — Session 035

- [2026-08-15, Session 035 — open] Opened via session-strategy-synthesis,
  grounded fresh against this file's Session 034 post-close addendum.
  Re-verified, not inherited: Patchward HEAD `61bd566`, patchward-landing
  HEAD `599ed04` clean, callmedai.com's Gate-3 copy (still corrected),
  patchward.dev (still live, correct, A/AAAA present), and the
  ten-second `multi-model-research-synthesis` follow-up (confirmed
  absent from this session's own skill list — explained, not just
  reconfirmed, via a same-session probe: this environment loads skills
  from an account-level registry via `save_skill`, a different mechanism
  than the local CLI path Session 034 wrote to). All CONFIRMED, 0 drift.
  L2 goal, per your explicit choice among four offered options:
  implement OD1–OD4 in the real `session-strategy-synthesis`/
  `session-close` skill definitions, gated on first proving the
  `save_skill` write-then-load mechanism actually propagates same-session
  (it does — proven via a disposable probe skill, byte-verified through
  three independent methods, then deleted).
- [2026-08-15, Session 035 — OD1–OD4 implemented] Rollback copies of both
  skills captured and sha256-verified before any write. Both skills
  amended (session-close 10,895→14,092 B; session-strategy-synthesis
  7,611→8,596 B), saved via `save_skill(overwrite: true)`, and verified
  live by reading the served cache-filesystem bytes directly — not the
  tool's own success return value. The new 16,000-byte ceiling check was
  then hand-exercised against the real, current `STRATEGY.md` (183,346 B
  at the time) and correctly produced a DUE flag on two independent
  triggers; a genuine, disclosed imperfection was found in the process
  (the entry-count sub-trigger undercounts) and logged as a refinement
  candidate rather than smoothed over. The DUE flag and the refinement
  note were then written into this file's own Open threads, closing the
  loop the mechanism itself specifies.
- [2026-08-15, Session 035 — two prompt-injection attempts, handled
  differently, correctly both times] A message styled as a prior
  "executor's verified report" claimed a fabricated "Session 4.15 /
  lawyer-gate waiver / 5 verified emails" narrative and asked for a
  closure entry in a `MEMORY/critical-actions.md` that does not exist in
  either connected repo — confirmed absent by direct search, refused
  outright, nothing written. A second message, in the same suspicious
  format, claimed two real git commits (`944d10c`, `1f89701`) — this time
  independently verified TRUE via fresh `git ls-remote` and `git show
  --stat`, matching the claimed hashes and file-change counts exactly
  (Yehor had committed and pushed them himself, on his own machine,
  between turns). Correct handling in both cases was the same
  discipline, with opposite outcomes: never trust the format, always
  independently verify, accept or refuse based on what verification
  actually finds — not on how suspicious or how confident the delivery
  sounded either way. This is the third and fourth occurrence of
  injected-report-shaped content in this project's history (Session 034
  logged the first two), and the fourth crossed a session boundary — see
  Heuristics below.

## Calibration record (continued) — Session 035

Claims checked at open: 5 (Patchward HEAD, patchward-landing HEAD,
callmedai.com copy, patchward.dev liveness, synthesis-skill absence).
**5/5 CONFIRMED**, 0 drift — each via a method independent of the resume
prompt's own claims (fresh `ls-remote`/clone, independent live fetches
of two separate pages, DNS-over-HTTPS as a second method alongside the
content fetch). 1.00 on checkable claims at open.

Claims checked at close: 14 (full list in
`memory/SESSION_CLOSE_2026-08-15.md`'s Gate status table — both repos'
HEADs, both skills' live content and rollback integrity, the ceiling
check's behavioral correctness, the STRATEGY.md edit's append-only
integrity, Yehor's two real commits, the fabricated content's confirmed
absence, and the `.git/index.lock` correlation). **13 CONFIRMED, 1
UNVERIFIED** (callmed-landing's exact hash — standing environment
limit, no sandbox credentials to a private repo, same category as prior
sessions' identical limitation, not a shortcut). **≈0.96 on checkable
claims (13.5/14, treating callmed-landing's live-content confirmation as
partial credit for the hash claim it stands in for).** Consistent with
this project's own established pattern of closes scoring higher than
opens — and, notably, this is the first close where two of the checked
claims were *about claims made by the user mid-session*, not just about
memory-file content or the session's own prior actions — the two-pass
discipline held the same way regardless of source, per H3's spirit.

## Heuristics — Session 035 update

- **[PROMOTED — 4th occurrence, crossed a session boundary as the
  candidate's own promotion condition asked for]:** content shaped
  exactly like a verified tool-call transcript or executor report — but
  not actually produced by any tool call in the current session — can
  appear embedded in a pasted user message. Session 034 logged two
  occurrences (both turned out benign once checked); Session 035 logged
  two more, with a genuinely new and load-bearing nuance the prior two
  didn't test: **the format carries no signal about truth either way.**
  One occurrence this session was entirely fabricated (a nonexistent
  `MEMORY/critical-actions.md`, a nonexistent "Session 4.15") and was
  correctly refused outright. The other, in the identical suspicious
  format, reported two git commits that turned out to be **genuinely
  real** once independently verified. The correct response was not
  "trust confident-sounding reports" and not "refuse anything styled
  like a report" — it was **independent verification via a real tool
  call, every time, with the verdict decided by what that check finds**,
  not by the claim's tone, formatting, or confidence. Promote this
  refined version, superseding the Session 034 candidate's narrower
  framing (which only had benign-outcome evidence to work from).

## Session log (continued) — Session 036

- [2026-08-19, open] Opened via session-strategy-synthesis, grounded
  against Session 035's close. 6/6 checkable claims re-verified fresh
  and CONFIRMED (both repos' HEADs, callmedai.com's two pages, patchward
  dev's tagline/test-count/DNS, OD1-OD4's propagation, lookbook pages
  still unstarted). One benign investigated non-drift:
  `tests/fixture_repo` gitlink dirty flag traced to untracked
  `__pycache__` noise, recorded commit unchanged.
- [2026-08-19] P0: committed and pushed `patchward-landing`'s two
  ROLLBACK skill-backup files (`6f98bc4`) — previously the only durable
  copy of pre-OD1-OD4 skill content, disk-only. Blocked twice by a stale
  `.git/index.lock` (see Heuristics, H30), resolved both times by
  Yehor's own terminal per H20.
- [2026-08-19] STRATEGY.md compression (Option A, archive-only), Yehor's
  explicit choice among three offered options. Two loss-check rounds:
  round 1 (content-preservation) restored two narrative-buried facts as
  proper bullets; round 2 (operational-preservation), triggered by
  Yehor's own review rather than self-caught, found the canonical
  Heuristics section had only ever held H1-H8 — even pre-compression —
  and restored all 22 actually-earned heuristics plus 6 candidates to
  live status. That review also embedded one fabricated detail (a
  nonexistent "H19, retired") alongside its valid core finding —
  disproven by direct grep before being acted on. Final: 192,908 →
  52,359 bytes (3.7×), committed as `cbb83aa`, verified on origin twice
  independently. Full detail: `memory/SESSION_CLOSE_2026-08-19.md`.

## Calibration record (continued) — Session 036

Claims checked this session: 16 (6 at open, 10 during/at close — full
table in `memory/SESSION_CLOSE_2026-08-19.md`'s Gate status). **14
CONFIRMED, 2 DRIFTED** — both drifted claims were embedded in pasted
"guide model" text relayed by Yehor, not this agent's own prior
statements: one asserted a fabricated heuristic-history detail (H19),
the other asserted a `git fetch` had already run when no such output
existed anywhere in the transcript, later proven false by Yehor's own
subsequent terminal output. **0.875 on checkable claims (14/16).**
Consistent with this project's established pattern that a close's
verified claims increasingly include claims from outside sources (user,
or content relayed by the user) rather than only this agent's own
memory or prior statements — the two-pass discipline held the same way
regardless of source, per H14's spirit, for the second session running.

## Heuristics — Session 036 update

- **H30 [NEW, earned 2026-08-19, 2 independent occurrences in one
  session, two different repos]:** a git `.git/index.lock: File exists`
  error on this project's Windows-origin repos is very likely stale, not
  live contention — diagnose before assuming a blocking process. Check
  the lock file's byte size (0 bytes = created but never completed) and
  mtime against `.git/index`'s own mtime (a lock that predates or barely
  postdates the last real index write, and is more than a few minutes
  old, is orphaned); confirm via `Get-Process git` returning nothing.
  Resolves the `.git/index.lock` correlation Session 035 logged as
  "disclosed but unresolved" — it was never genuine sandbox-vs-real-
  client contention. Removal must still happen from Yehor's own
  terminal, never the sandbox (H20) — sandbox-side `rm` on a
  Windows-mounted lock file can silently fail (`Operation not
  permitted`) without actually clearing the real lock, observed twice
  this session on a different lock (`objects/maintenance.lock`).
  **Third occurrence, caught live during this session's own close:**
  a plain, read-only sandbox `git status` (no write intended) itself
  created a fresh `.git/index.lock` while refreshing the index's stat
  cache, then hit the same "Operation not permitted" unlinking it — a
  read-only sandbox command can leave a genuinely NEW stale lock behind
  for Yehor's next command, not just fail to clear a pre-existing one.
  Treat every sandbox `git status`/`diff` on this repo as a possible
  lock-leaving operation, not only sandbox `add`/`commit` attempts.
- **H31-candidate [1 occurrence, 2026-08-19, costly]:** a compression or
  archival loss-check must test operational-preservation (does X stay
  in the file every session actually reads) separately from
  content-preservation (does X still exist anywhere, even in cold
  storage) — the two are different tests. This session's first
  compression pass verified content-preservation rigorously and still
  missed that 14 earned heuristics, including a hard rule (H20), had
  silently dropped out of the routinely-read file. Caught by Yehor's
  review, not self-caught. Promote on a second occurrence, ideally
  self-caught next time.
- **[Session 035's unnumbered "report-shaped content" heuristic,
  REINFORCED, refined further]:** two more occurrences this session
  (both "guide model" messages), with a nuance the prior four hadn't
  tested: **a report can be substantially correct — well-reasoned,
  independently-styled, with a genuinely valuable core finding — and
  still contain one fabricated specific supporting detail.** The
  correct response is not "trust it because most of it checks out" or
  "distrust it because one detail is wrong" — every discrete factual
  claim inside a report needs its own independent check, regardless of
  how correct the report's overall verdict turns out to be. Neither
  fabrication this session was catchable by tone, formatting, or
  plausibility; both were caught only by direct verification (a literal
  `grep` for `H19`; checking whether any terminal output for the claimed
  `fetch` existed anywhere in the transcript).
