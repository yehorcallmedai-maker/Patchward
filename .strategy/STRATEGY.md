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
- [2026-08-25, Session 041 close, written last] **The 97,390-byte figure
  cited earlier in this session's own close entries (Open threads,
  Calibration, the close-out doc) is already stale — caught here
  deliberately, applying this same close's own lesson to itself rather
  than shipping a number known to be wrong.** Writing the close entries
  themselves added bytes after that measurement was taken; a fresh
  `wc -c` right now, with no further edits planned this session, reads
  **101,298 bytes** (≈6.33x the 16,000-byte ceiling). This is the
  figure the next session should treat as Session 041's true close
  size — and per this file's own standing lesson, it should still be
  re-measured fresh next time, not trusted from this line either.
- [2026-08-25, Session 041 open] **Full re-grounding against Session 040's
  close (`12d542d`) — nothing inherited on faith, 6 claims checked, 6
  CONFIRMED, 0 drift.** (1) Patchward HEAD: local `git log`/`ls-remote`
  AND a separate fresh `git clone` of the origin URL (independent of the
  mount) both land on `12d542d1d58b8162da9dfb9dda224b14e6e1af30` — exact
  match, three methods agreeing. (2) patchward-landing HEAD: same
  two-method check, `087455d4e1eb107c67de2d869a603ebd3ba08466`, clean —
  only the known deliberately-untracked DRAFT safety-net files present,
  no real drift. (3) STRATEGY.md byte count: fresh `wc -c` **on the
  origin fresh-clone**, not the mount, **90,748 bytes exactly** —
  matches Session 040's own close figure to the byte. (4) NJORD meeting
  status, checked without assuming either way: today is 2026-08-25: the
  real meeting (per two independent human-confirmation emails) is
  **tomorrow**, Wednesday 2026-08-26 16:00-17:00 — **has not happened.**
  A direct `get_event` on `c4o3eopg...` (independent of the `search_events`
  read) reconfirms it stored 2026-08-25 16:00-17:00, `updated` still
  identical to `created` — consistent with Yehor's own same-day
  confirmation logged at Session 040 close that this is a deliberate
  day-early reminder, not a live drift. (5) Follow-up email: **not
  sent.** Two independent Gmail searches (`to:npd@njordlaw.com
  after:2026/08/24` and `from:njordlaw.com after:2026/08/24`) both
  return zero results — matches the standing calendar reminder for it,
  which is itself dated 2026-08-26 17:15-17:30 (after the meeting, not
  before). No NJORD response exists to evaluate (item 4 of Yehor's
  brief is moot until the email goes out). (6) Heuristics: **36 total
  confirmed exactly as claimed — 24 earned + 12 candidates**, via a
  fresh line-range-bounded extraction (lines 837-1184) on the origin
  clone. **Worth logging honestly: this session's own first attempt at
  this count silently undercounted** (23 earned + 10 candidates) —
  missed `H20` because its line is bold-markered (`- **H20 [HARD
  RULE...`, not the plain `- H20 [` every other earned entry uses), and
  missed `H23`/`H28` as candidates because they carry `[CANDIDATE...]`
  in their body text rather than a `-candidate` ID suffix like the other
  ten. A second, more careful pass caught both formatting inconsistencies
  before this entry was written — not promoting this to a heuristic on
  one occurrence, but flagging it: any future heuristic-count check
  should grep for the bracket content (`CANDIDATE`/`PROMOTED`/`HARD
  RULE`/`active`), not just the ID pattern, or it will silently
  undercount the same way. H34-candidate, H35-candidate, H37-candidate
  all confirmed still at exactly 1 occurrence each — no second
  occurrence surfaced, no promotion due. H37-candidate's own same-day
  reasoning-gap addendum (metadata alone proves "never silently
  patched," not "correct from creation" vs. "broken and unfixed" —
  pair with original intent) read in full, not just its headline, per
  Yehor's own brief. BACKLOG.md re-confirmed unchanged, **120,268
  bytes**, on the same origin clone. No agent-startable work is queued:
  BACKLOG 12 follow-through is gated on tomorrow's meeting and the
  email that follows it; STRATEGY.md compression is explicitly not
  urgent (Part B just ran); nothing else surfaced as ready. This
  session's own calibration: **1.00 (6/6)** — see Calibration record.
- [2026-08-24, Session 040 close, written last] **Heuristic total is now
  36** (24 earned + 12 candidates), not the 35 the bullet below states —
  H37-candidate was logged after that bullet was written, in the same
  session, the exact self-citation-lag shape this file keeps catching
  on itself. Stated here deliberately as its own dated correction
  rather than edited into the bullet below, per this file's own
  never-launder-history rule.
- [2026-08-24, Session 040 close] **Compression commit landed and
  independently re-verified — not from Yehor's own pasted terminal
  output, from a fresh `git clone` this session ran itself:** Patchward
  HEAD `1301c9f47f60aa3b052ed5c9de52d0aef66dd6d0`, confirmed via mount
  + fresh clone + `ls-remote` (three methods, all agree). On origin,
  directly: `.strategy/STRATEGY.md` **79,696 bytes**; `.strategy/
  RETROSPECTIVE.md` **179,874 bytes**; H36 present in canonical
  §Heuristics with its full text; all **35** heuristic IDs (24 earned +
  11 candidates) confirmed live via a fresh section-bounded grep on the
  cloned copy. patchward-landing HEAD unchanged, `087455d4...`.
  **One claim in this session's own pasted "guide model" review did NOT
  hold up under independent check:** that review asserted the
  `c4o3eopg...` calendar-date question was settled ("no correction
  needed... your confirmation that c4o3eopg was intentional"). A direct
  `get_event` call this session shows the event's `updated` timestamp
  is still `2026-08-20T13:17:09Z` — identical to `created` — meaning it
  has never been modified since the moment it was made; it is still
  stored on 2026-08-25, still titled "...26.08.26", still contradicted
  by two independent emails confirming the real meeting is Wednesday
  the 26th. The corroborating "Parents go away 26.08.26" event
  (unrelated, created 2026-08-24) is likewise unmodified since
  creation, still stored a day early. **No direct confirmation from
  Yehor, in this conversation, that the drift is intentional has been
  received by this session** — the claim that it was confirmed appears
  only inside pasted, report-shaped content, which is exactly the
  category H36 (restored earlier this same session) says must be
  independently verified before being trusted, not asserted on the
  strength of its own formatting or confidence. Treated here as
  UNVERIFIED, not resolved, pending Yehor's own direct word. See Open
  threads.
- [2026-08-24, Session 040 open] **Two corrections found via fresh
  verification, neither inherited from this file's own prior count:**
  (1) the heuristic total is **35** (24 earned + 11 candidates), not
  the 33 this file stated as of Session 039 — H35-candidate was added
  at that session's own close, after the "33" tally was written at
  open, and the running total was never updated (an H2-shaped self-
  citation lag, same class this file has caught on itself repeatedly);
  separately, a genuine operational-preservation gap was found and
  fixed during this session's Part B compression (see the Session
  035-039 summary below): Session 035's "report-shaped content"
  heuristic, PROMOTED with 4 real occurrences, had been living only in
  a per-session appendix for 4 sessions — now restored to canonical
  §Heuristics as **H36**. (2) The NJORD meeting (2026-08-26 16:00-17:00,
  human-confirmed twice over email) and its follow-up-email calendar
  event were re-checked fresh, not assumed: **neither has happened
  yet** — today is 2026-08-24, both are still in the future. A
  previously-uncaught date drift was found on the meeting event itself
  (`c4o3eopg...`, titled "...26.08.26" but stored `start`/`end` on
  2026-08-25) — reported to Yehor, not yet fixed pending his decision
  on Step 2; see Open threads. STRATEGY.md's own compression (Part B,
  the standing 5-session-deferred priority) run this session: backed
  up first (sha256-verified), Sessions 035-039's verbose log/
  calibration entries moved verbatim to RETROSPECTIVE.md, replaced
  with a condensed summary matching the 019-034 precedent. Not yet
  committed — pending Yehor's own review and commit, per H20.
- [2026-08-22, Session 039 close] BACKLOG 12 (CRA/GDPR counsel) advanced for
  the first time since Session 024: **discovered the European Commission
  published official, non-binding CRA guidance on 2026-07-27** (`C(2026)
  5252`), three days after the base briefing packet was written — it directly
  addresses open-source scope and introduces a **"remote data processing
  solutions"** category likely to cover the hosted webhook, plus 67 worked
  examples aimed at microenterprises/SMEs. Wrote
  `memory/BACKLOG12_ADDENDUM_2026-08-22.md`: re-verifies every load-bearing
  base-packet claim against current HEAD (`b5a02ed4`, 42 commits past the
  packet's `3e63587`) — all still hold; two peripheral details corrected
  (`CredentialProxy`'s scrubbed-credential set is now 8 keys not 4, BACKLOG 25
  hardening; `.scrub()` test-occurrence count is 7 not 5) — and adds two
  questions the base packet lacked (substantial modification; support
  period), plus one urgent, dated question (does the 2026-09-11 Article 14
  obligation apply to Patchward specifically, given it binds in 20 days
  against 2027-12-11 for everything else). **Investigated NJORD Law Firm /
  Nis Peter Dall (Yehor's existing FixProve counsel contact) as the candidate
  for this work**, live-verified via NJORD's own site and Legal 500: certified
  IT attorney, member of Danske IT-Advokater and Rådet for it-sikkerhed,
  EXIN ISO/IEC 27001-certified, contributor to Chambers' Cybersecurity 2022
  Global Practice Guide, co-author of a GDPR practitioner handbook. **Gap,
  stated honestly: no published CRA-specific advisory work found for NJORD**
  — deep GDPR/IT/cybersecurity credentials confirmed, CRA product-regulation
  experience specifically unproven. `advokatnoeglen.dk` confirmed to be
  Advokatsamfundet's self-declared lawyer directory (a lookup tool, not a
  vetting service) — kept as a fallback only, not preferred over an
  already-vetted specialist. Decision, Yehor's own: expand NJORD rather than
  engage new counsel, sequenced deliberately — the CRA question is added to
  the 2026-08-26 16:00–17:00 meeting agenda as a follow-up **email sent AFTER
  the meeting**, not during it, to avoid tabling too much at once. Ready-to-copy
  Danish email drafted; a calendar reminder was created for this
  (2026-08-26, 17:15–17:30 Europe/Copenhagen) — **first attempt drifted 5
  days (silently stored as 2026-08-31 despite the creation call's own
  response echoing back 2026-08-26 as if correct); caught only by this
  project's standing two-pass-write discipline (an independent `get_event` +
  `list_events` re-read, not trusting the creation response), fixed via
  `update_event`, re-confirmed via both independent methods a second time.**
  See Heuristics, H35-candidate.
- [2026-08-22, Session 039 open] Both repos' verified current HEADs,
  superseding the Session 038 entry below (which itself already showed
  the H2-shaped self-citation lag it warns about — its own close commit
  is the HEAD this session found): **Patchward**
  `b5a02ed40064dc68fdcc9254883f0216ca61075d` — confirmed via fresh
  `git clone` + `git ls-remote`, both agreeing; this IS the Session 038
  close commit itself (docs: close 404.astro thread + H4 correction),
  zero new commits since. **patchward-landing**
  `087455d4e1eb107c67de2d869a603ebd3ba08466`, clean — same two
  independent methods agree; mount status shows only the two
  deliberately-untracked ROLLBACK/DRAFT skill-backup files (must stay
  untracked, see Open threads) plus gitignored build artifacts, no real
  drift. **callmedai.com** `/` and `/security` re-fetched fresh: Gate-3
  disclosure language and Patchward branding both still correct, 0
  RepoMend mentions. **patchward.dev** tagline, "565 passed, 3 skipped
  · 91.20% coverage", and `/facts` (all cited figures incl.
  `branch-convention`, `example-prs-patchward`, `example-pr-checkdmarc`
  labelled "closed — superseded") all re-confirmed live and matching.
  **A/AAAA records re-confirmed** via DNS-over-HTTPS
  (`https://dns.google/resolve`): A `172.67.201.154`/`104.21.44.172`,
  AAAA `2606:4700:3034::ac43:c99a`/`2606:4700:3036::6815:2cac`, exact
  match. **All six patchward-landing routes re-confirmed live and
  correct on BOTH hosts** (`patchward.dev` and the
  `patchward-landing.pages.dev` deploy alias) — with one genuine
  verification-methodology finding along the way: this session's own
  `web_fetch` tool, on its very first (non-cache-busted) fetch of
  `/how-it-works`, `/verification`, and `/examples` on `patchward.dev`,
  returned the HOMEPAGE's content instead of each route's own
  page — a false stale-content signal, not a live site defect.
  Cross-checked and resolved via two independent methods: (1) the same
  URLs with a cache-busting query string, via the same tool, returned
  each page's correct distinct content; (2) a genuine Claude-in-Chrome
  browser render of the plain URLs (no query string, a real visitor's
  exact request) also returned correct, distinct content immediately,
  full 6-link footer included. The `patchward-landing.pages.dev` alias
  never showed the issue on any first-time fetch. Root cause not fully
  determined (this session's own `web_fetch` tool internals are opaque
  from here) but the live site itself is confirmed correct on both
  hosts — see Heuristics, H34-candidate. **Footer note:** the homepage's
  own footer, on both hosts, by design lists only `/limits` and
  `/facts` — NOT all six lookbook routes; the six-link footer is
  specific to the five lookbook pages (`/how-it-works`, `/verification`,
  `/data-boundary`, `/examples`, `/facts`) plus `/limits`, each of which
  links to the other five. This is consistent site design, confirmed on
  both hosts, not a defect — but worth stating precisely since a prior
  session's "footer lists all six on every page" phrasing could be
  read as including the homepage. **404 fix re-confirmed live on both
  hosts** — this time via a real Claude-in-Chrome browser render rather
  than only a response-signature inference: two independent fake paths
  per host all returned a literal, distinct "Patchward — page not
  found" title and 404 body, sharply unlike every real route fetched
  this session.
- [2026-08-22, Session 039 open] Memory-file state re-verified fresh
  (`wc -c`, not reused): `.strategy/STRATEGY.md` **80,262 bytes** —
  unchanged from Session 038's own close figure, confirming zero edits
  landed since (consistent with the HEAD finding above); still ≈5.02×
  the 16,000-byte ceiling. `.strategy/RETROSPECTIVE.md` **154,004
  bytes**, unchanged, exists as expected. `memory/BACKLOG.md` **120,268
  bytes**, unchanged, matching the figure already flagged. All 23
  earned heuristics (H1–H8, H11–14, H16, H18, H20–22, H24–27, H29, H30)
  plus all 10 tracked candidates (H9, H10, H15, H17, H23, H28, H31, H32,
  H33, H34) confirmed present within the canonical §Heuristics section
  bounds (line-range-bounded grep, not whole-document grep, per
  H31-candidate's own lesson) — **33 total, not 32** (this session's own
  Session-log entry below first mis-totalled it as 32/23+9, omitting
  H34-candidate from its own tally the same session it was added; a
  pasted "guide model" report then independently caught that the split
  looked off, but its own corrected split — 22 earned/10 candidates —
  was ALSO wrong, having dropped H20 from its enumeration; a fresh,
  section-bounded grep this session settled it: 23 earned + 10
  candidates = 33, confirmed directly against the file, trusting
  neither prior tally). H4's 2026-08-21 correction
  (raw.githubusercontent.com now blocked at bash level, `web_fetch`
  unaffected) confirmed still present, not reverted. H20 (hard rule)
  confirmed present, unchanged — and was the specific heuristic the
  guide-model report's own recount dropped, worth remembering the next
  time any count of this section is taken on faith. BACKLOG 12
  (CRA/GDPR counsel): **20 days remain to the 2026-09-11
  reporting-obligation date** as of this session's open — still
  genuinely open. Re-checked THIS session against current source
  (HEAD `b5a02ed4`, vs. the packet's `3e63587`): the packet's
  load-bearing claims (installations_db schema, marketplace_purchases'
  still-absent deletion path, zero `.scrub()` call sites in
  `fix_gen.py`/`subagent.py`, `is_entitled()` gating) all still hold.
  Two supporting details are now stale, neither changing any question
  posed to counsel: `CredentialProxy`'s scrubbed-credential set widened
  from 4 to 8 keys since the packet was written (BACKLOG 25 fix, real
  security hardening); `tests/test_credential_proxy.py`'s cited "five"
  `.scrub()` occurrences is now seven. `README.md`'s stale
  "not yet published to PyPI" line, flagged as an aside in the packet
  a month ago, is still uncorrected. Verdict: **READY TO SEND** — the
  counsel-facing content (Steps 1–5) is accurate and unchanged; the
  two stale details are internal engineering trivia, not something
  counsel's answer depends on.
- [2026-08-21, Session 038 close] Both repos' verified current HEADs,
  unchanged from Session 037 (no new commits this session — deploy work
  only): **Patchward** `09dc925bce1d8705518c13ca35d19831bec7ce52`;
  **patchward-landing** `7b6cf22339b3dcb34116312a6339d855c487918f`.
  Corrects two self-references that were already stale the moment the
  Session 037 close commit wrote them (an H2-shaped drift caught this
  session's Grounding, not a new occurrence — the entry below was
  correct when written, just superseded within its own commit): it
  cited Patchward HEAD as `a246fc6...` (actually `09dc925` is HEAD —
  `a246fc6` is one commit behind) and STRATEGY.md as 64,254 bytes
  (actual, before this session's edits: 71,210 bytes; **after this
  session's edits: ~79,300 bytes — approximately 4.96x the
  16,000-byte ceiling, climbing again** — stated as approximate
  deliberately, since this file's own edit that states the number
  changes the number; Grounding next session should re-run `wc -c`
  fresh rather than trust this figure, per H2's own logic applied to
  itself. Part B compression remains deferred, see Open threads). **The four lookbook pages, found this session to be
  shipped-to-origin but NOT deployed** (Cloudflare Pages here is fed by
  manual `npx wrangler pages deploy dist`, not a git integration —
  commit `7b6cf22` triggered no deploy on its own; three-signal proof:
  identical fallback body on real vs. fake routes, footer still listing
  only 3 of 6 routes, live `/facts` missing the three new ledger
  entries), **are now deployed and CONFIRMED LIVE on both hosts**
  (`patchward.dev` and its `*.patchward-landing.pages.dev` deploy
  alias): footer lists all six routes, `/facts` carries
  `branch-convention`/`example-prs-patchward`/`example-pr-checkdmarc`,
  and every cited figure (565 passed/3 skipped/91.20% coverage,
  `uv tool install patchward`, checkdmarc#261 labelled "closed —
  superseded" not "merged") matches live content, checked on both
  hosts. **AAAA records also newly CONFIRMED** (closing Session 037's
  structural UNVERIFIED): this sandbox's own resolver is dead (H4), but
  DNS-over-HTTPS via `https://dns.google/resolve` works from `web_fetch`
  — `2606:4700:3034::ac43:c99a`, `2606:4700:3036::6815:2cac`; A records
  `172.67.201.154`, `104.21.44.172`. **A second, independent defect
  found and fixed the same session:** unmatched routes on both hosts
  were serving the homepage body (200-looking) instead of a real 404 —
  the exact soft-failure shape that let the undeployed-pages gap look
  fine on a casual check. `src/pages/404.astro` created, built, and
  deployed; post-fix, unknown paths return an empty/error response on
  both hosts, reproduced with two independent random paths each,
  sharply distinct from every real page fetched all session. Stated
  plainly: this is a response-signature inference, not a literal
  HTTP-status-line read — this sandbox's `web_fetch` doesn't surface
  status codes, so "real 404" is corroborated, not directly observed.
  **`src/pages/404.astro` — committed and pushed as `087455d`, CLOSED.**
  Verified by three independent methods, none trusting the push output
  alone: (1) fresh `git clone` to `/tmp` (not the mount) →
  `git rev-parse HEAD` = `087455d4e1eb107c67de2d869a603ebd3ba08466`,
  exact match; (2) SHA-256 of the file identical across the fresh clone
  and the mounted working tree
  (`c0f24e17821b756ca1cf34476d067f019ce74ca99a2f41a57febd1d313b23036`);
  (3) direct `raw.githubusercontent.com` fetch pinned to `087455d`,
  content character-for-character identical. All three agree.
- [2026-08-20, Session 037 close] Both repos' verified current HEADs,
  superseding the Session 036 entry below: **Patchward** `a246fc6446
  87d0e277a9f1002efced1c32a31070`; **patchward-landing** `7b6cf22339
  b3dcb34116312a6339d855c487918f`, clean. Both confirmed via
  `ls-remote` + a fresh clone (not the mount) + sha256 of every
  changed file, matched against the mount. `STRATEGY.md` itself is
  now **64,254 bytes** (was 59,837 at Session 036 close — see Open
  threads for the H30/H31 relocation). The four patchward-landing
  lookbook pages (`/how-it-works`, `/verification`, `/data-boundary`,
  `/examples`) are built, ledger-sourced (zero hand-typed figures,
  verified by extraction), and shipped in the commit above — the
  Open-threads entry below marking them unstarted is now CLOSED.
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
- [2026-08-28, Session 042 continued] **Commit `f1fe546` (this session's
  memory update) independently verified on origin — fresh clone +
  `ls-remote`, diff-stat matches the pasted terminal transcript exactly
  (2 files, 43 insertions, 1 deletion) — not trusted on the transcript's
  say-so alone, per H36.** A NJORD nudge reminder was created for
  **2026-08-31 09:00 Europe/Copenhagen** (event
  `uueepgqam0mvuh0dngq6sp34tk`), then independently re-read via a
  separate `list_events` call; creation response and re-read agree
  exactly — no discrepancy found (H35-candidate stays at 1 occurrence).
  **Correction to a claim in a pasted "guide model" review this
  session:** that review asserted the file already resolves whether
  counsel sign-off is needed by 2026-09-08 (launch window opening) or
  2026-09-11 (Article 14 date) — on direct re-read, the cited sentence
  only establishes the two dates share one regulatory window, not which
  of them gates action. Flagged honestly rather than repeated; the
  08-31 nudge date was chosen specifically because it doesn't depend on
  resolving that reading (safe under either interpretation). Still
  Yehor's call if he wants it pinned down precisely.
- [2026-08-28, Session 042 open] **NJORD meeting/follow-up-email chain
  has moved — verified via Gmail (two independent queries:
  `from:njordlaw.com OR to:njordlaw.com after:2026/08/25`, then
  `from:npd@njordlaw.com`) and Calendar (`list_events` date-range on
  the reminder's stored window), not assumed either way.** The
  2026-08-26 16:00-17:00 meeting happened — confirmed by the follow-up
  email's own opening line ("Thank you for a good meeting today"). The
  CRA follow-up email (thread `1a03eea261e68ac5`, to `npd@njordlaw.com`,
  briefing packet attached) was sent 2026-08-26 18:40 Europe/Copenhagen —
  about 1h10m after the 17:15-17:30 reminder window, still same-day and
  post-meeting, not treated as a problem. It asks the two questions
  BACKLOG 12 needed answered: whether CRA/product-regulation work is in
  NJORD's wheelhouse, and whether it can be scoped alongside FixProve
  Fase 1. **No NJORD reply as of this check** (2 days elapsed) — the
  most recent inbound NJORD message is still the 2026-08-20
  meeting-scheduling one. Not yet worth a nudge; worth one if ~a week
  passes with no response, given the 2026-09-11 Article 14 deadline.
  BACKLOG 12 updated accordingly in `memory/BACKLOG.md`. Retained event
  IDs `c4o3eopg...`/`enkp47hl...` from prior entries below turned out
  truncated for direct `get_event` lookup (full ID needed, e.g.
  `enkp47hlnoojs3q6a72ctkoknk`) — `list_events` date-range was used
  instead and found the reminder event intact and unmodified.
- [2026-08-25, Session 041 close] **Retrospective still DUE, number
  climbing from normal same-day logging, exactly as Session 040's own
  close flagged would happen:** `.strategy/STRATEGY.md` measured
  **97,390 bytes** fresh (`wc -c` on an origin fresh-clone, confirmed
  twice, not estimated) — ≈6.09x the 16,000-byte ceiling, up from
  90,748 (≈5.67x) at Session 040's close. All growth this session is
  from honest, dated logging (the re-grounding entries, the
  guide-model-review correction cycle, this close itself, the
  §Heuristics counting note) — nothing padded. Compression remains a
  legitimate future L2 candidate, not urgent — flag only, per this
  skill's own rule against bundling compression into substantive-work
  sessions.
- [2026-08-25, Session 041 close] **NJORD meeting/follow-up-email
  status re-confirmed unchanged at close, via a third independent
  method beyond the two used at open** (a `list_events` date-range
  query, distinct from the `search_events`/`get_event` calls used
  earlier): calendar event `c4o3eopg...` still stored 2026-08-25
  16:00-17:00 (the deliberate day-early reminder, per Yehor's own
  Session 040 confirmation); the real meeting per two independent
  emails is tomorrow, 2026-08-26 16:00-17:00 — **has not happened as of
  this close.** Follow-up-email reminder (`enkp47hl...`) still stored
  2026-08-26 17:15-17:30, untouched; a `njordlaw.com` thread search at
  close returned the same 4 threads as at open, nothing new — **email
  still not sent.** Next session's real work starts here, not before.
- [2026-08-25, Session 041 close] **`.git/index.lock` recurrence, 3rd
  occurrence, same root cause as Session 033/037's findings — cleared
  safely, no new information.** Blocked `git add`/`git commit` on the
  Patchward mount mid-session; Yehor confirmed no real git process
  running (`Get-Process` empty) before removing it directly
  (`Remove-Item .git\index.lock -Force`), then the same commands
  succeeded cleanly. Consistent with H30 (sandbox-side read-only git
  commands leave a stale lock, not live contention) — not promoted or
  re-opened as a fresh question, just logged as one more confirming
  occurrence.
- [2026-08-24, Session 040 close, RESOLVED same day] **Calendar event
  `c4o3eopg...`: Yehor confirmed directly, in-conversation** — "created
  earlier on purpose as a reminder preparation." Not a defect. The
  8/25-dated event is a deliberate day-early prep reminder for the real
  8/26 meeting, not a mis-write. This closes the open question the
  bullet below raised. **Left as its own dated entry rather than
  edited into the one below, per this file's never-launder-history
  rule** — the open question was genuine and correctly raised; it
  resolved by direct confirmation, not by the reasoning in this file
  turning out wrong. One loose end, low-stakes, not re-opening the
  question: this explanation is specific to the NJORD event and wasn't
  extended to the corroborating "Parents go away 26.08.26" event
  spotted alongside it (same title/stored-date signature, unrelated
  purpose) — worth Yehor's own glance at some point, not urgent, since
  a personal-errand entry a day off carries none of the NJORD meeting's
  stakes.
- [2026-08-24, Session 040 close] Calendar event `c4o3eopg...`
  originally flagged here as still needing Yehor's own direct
  word — NOT closeable on a pasted report's say-so. Live state as
  checked this close (`get_event`, fresh): stored 2026-08-25 16:00-17:00,
  `updated` identical to `created`, never touched. The real meeting,
  per two independent emails, is Wednesday 2026-08-26 16:00-17:00. A
  second, unrelated, same-day-created event ("Parents go away
  26.08.26") shows the identical title-says-26th/stored-25th
  signature, also untouched at the time of this check. **See the entry
  above — resolved same day by Yehor's direct confirmation.**
- [2026-08-24, Session 040 close] **Retrospective still DUE, improved
  but not resolved:** `.strategy/STRATEGY.md` measured **79,696 bytes**
  fresh (`wc -c` on an origin fresh-clone, not estimated) — ≈4.98× the
  16,000-byte ceiling, down from ≈6.2× at Session 039's close. Part B
  ran this session (Sessions 035-039 archived to RETROSPECTIVE.md,
  H36 restored, committed as `1301c9f`). Further compression (Sessions
  040+ will accrue the same way) is a legitimate future L2 candidate,
  not urgent — this file is no longer climbing unchecked, just still
  over ceiling.
- [2026-08-22, Session 039 close] **Retrospective still DUE, number
  climbing again:** `.strategy/STRATEGY.md` measured **≈98,900 bytes**
  at last fresh `wc -c` this close — ≈6.2× the 16,000-byte ceiling, up
  from 80,262 (5.02×) at Session 038's close. Stated deliberately as
  approximate per H2's own logic applied to itself: this entry's own
  text adds bytes after the number was measured, so it is already
  slightly stale the moment it's written — next session should re-run
  `wc -c` fresh rather than trust this figure, not just as a formality.
  All growth this session is from honest, dated logging (the
  counsel-engagement work, two caught-and-fixed drifts, this close
  itself) — nothing was padded. Part B compression remains the
  standing, explicitly-deferred fix, same reasoning as every prior
  session: a dedicated, approved, backup-first pass with a dual
  loss-check, not bundled into substantive work.
- [2026-08-22, Session 039 close] **Two files need Yehor's own commit,
  and they are NOT the same category as the deliberately-untracked
  ROLLBACK/DRAFT skill-backup files noted below** — those must stay
  untracked; these should not: (1) `.strategy/STRATEGY.md` itself
  (this session's corrections and close); (2)
  `memory/BACKLOG12_ADDENDUM_2026-08-22.md`, a genuine project
  deliverable in the same category as the base counsel packet (which
  Yehor already committed at `36b0a65`) — it should be committed the
  same way, not left to accumulate as an untracked file indefinitely.
- [2026-08-22, Session 039 close] **BACKLOG 12 has a live external
  deadline for the first time in this project's tracking of it:** the
  2026-09-11 Article 14 reporting-obligation date is 20 days out as of
  session open. Everything else on this packet has runway to
  2027-12-11. The Wednesday 2026-08-26 meeting with Nis Peter Dall
  (NJORD) is the next real checkpoint — the calendar reminder to send
  the follow-up email afterward is confirmed live and correctly dated
  (see Current state for the drift-and-fix story). Next session should
  check whether that email was actually sent and whether NJORD
  responded, rather than assuming either.
- [2026-08-21, Session 038] **The four lookbook pages — DEPLOYED and
  LIVE, CLOSED.** Session 037 verified shipped content; this session
  found it wasn't actually live (deploy is manual `wrangler`, not
  git-triggered), had Yehor run `npm run build` +
  `npx wrangler pages deploy dist --project-name=patchward-landing`,
  then confirmed all six routes + `/facts` + every cited figure live
  on both hosts. See Current state for the full evidence chain. Next
  session's own value: after ANY future commit to patchward-landing,
  confirm a deploy actually ran — the git-vs-deploy split is now a
  known standing gap, not a one-off.
- [2026-08-20, Session 037] **Retrospective still DUE, number climbing:
  STRATEGY.md was 71,210 bytes before this session's edits — 4.45x the
  16,000-byte ceiling** (up from 4.02x/64,254 at Session 037's own
  close — that entry's self-report was itself already stale, see
  Current state). Part B (rewriting Current state/Open threads for
  genuine compliance) remains the standing, explicitly-deferred fix —
  not attempted this session (deploy verification took priority, by
  Yehor's explicit choice this session), same reasoning as before: a
  dedicated, approved pass, backup-first, dual loss-check (content AND
  operational preservation) from the start per H31-candidate.
- [2026-08-20, Session 037] **Sandbox-write-to-real-mount propagation
  lag, first occurrence, not yet a heuristic.** A completion report
  claimed real-repository working-tree changes existed; Yehor's own
  `git status`, run within minutes, showed nothing. Root-caused via
  mtime evidence (the build-verification copy was stamped after, and
  derived from, the real edits) and resolved cleanly on re-check ~10
  minutes later — genuine sync lag, not lost work, not a location bug.
  Recorded here per Yehor's explicit instruction as the session's own
  worked example of this project's verification discipline holding: the
  report was accepted only after its evidence gap was named and then
  closed with real proof (mtimes, a fresh clone, sha256, reflog), not
  smoothed over. Watch for a second occurrence before promoting to a
  heuristic; if it recurs, the fix is likely "wait and re-check before
  treating a mismatch as data loss," not a process change.
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
**Counting note (added 2026-08-25, Session 041 close — 2nd occurrence,
watch for a 3rd before promoting to its own ID):** a plain-dash or
suffix-only grep of this section will silently undercount by 3. `H20`
is formatted `- **H20 [HARD RULE...` (bold-wrapped), not the `- H20 [`
pattern every other earned entry uses; `H23` and `H28` are candidates
labeled inline (`[CANDIDATE, ...]`) rather than via the `-candidate` ID
suffix the other ten candidates use. Two independent sessions hit this
exact miscount for the exact same reason (Session 040's close-review of
pasted content, Session 041's own open) — correct method: grep for
bracket content (`CANDIDATE`/`PROMOTED`/`HARD RULE`/`active`), not just
the ID pattern, or bound the count to this section's line range AND
manually confirm every earned/candidate label reads as expected.
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
- H4 [active, promoted 2026-07-16, evidence: Sessions 020, 021;
  **CORRECTED 2026-08-21, Session 038**]: this sandbox's bash has no
  general internet egress to arbitrary hosts (GitHub release CDN via
  `uv python install`, Fly proxy via direct `curl`) even though
  `web_fetch`, `pip install` from PyPI, and `git` operations against
  `github.com`/`api.github.com` all work. **Session 021 originally
  also listed direct bash `curl` to `raw.githubusercontent.com` as
  working; Session 038 found this specific claim no longer holds** —
  bash-level `curl` to that host now returns `403 Forbidden` from the
  sandbox's own outbound proxy (`X-Proxy-Error: blocked-by-allowlist`),
  reproduced directly. `web_fetch` to the same host, same exact URL,
  same session, is unaffected and returned correct content. Stated
  plainly, without asserting which: either the sandbox's network
  policy changed since Session 021, or the reachable/blocked boundary
  was drawn narrower than originally recorded — not yet determined,
  no further evidence gathered this session. The operative guidance is
  unchanged and, if anything, reinforced: don't assume a bash-level
  network failure means the target is down or the technique is
  unusable — test the specific host/tool combination fresh, every
  time, rather than trusting a prior session's result, including this
  file's own. **Session 021: this is also why a real `uv run pytest`
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
- H30 [PROMOTED — earned 2026-08-19, relocated here 2026-08-20 from the
  Session 036 per-session appendix where it was first written; 4
  confirmed occurrences across both repos, plus a 5th observation of a
  different kind, below]: a `.git/index.lock: File exists` error on this
  project's Windows-origin repos is very likely a STALE ORPHAN, not live
  contention — diagnose before assuming a blocking process. Check the
  lock's byte size (0 bytes = created, never completed) and its mtime
  against `.git/index`'s own mtime (a lock predating or barely
  postdating the last real index write, more than a few minutes old, is
  orphaned); confirm with `Get-Process git` returning nothing.
  **Cause:** the sandbox's own read-only git commands (`status`, `show`,
  `diff`, `fetch`) create these locks while refreshing the index's stat
  cache — no write is ever intended. Applies to
  `.git/objects/maintenance.lock` as well as `.git/index.lock`.
  **Removal must happen from Yehor's own terminal, never the sandbox
  (H20)** — sandbox-side `rm` on a Windows-mounted lock can silently
  fail (`Operation not permitted`) without clearing the real lock,
  observed twice. **Standing practice:** clear via `Remove-Item` before
  any write, every session, not only when a "File exists" error actually
  appears. Resolves the `.git/index.lock` correlation Session 035 logged
  as "disclosed but unresolved" — it was never genuine
  sandbox-vs-real-client contention.
  **Mitigation, first attempt 2026-08-20 — a data point, NOT a claimed
  fix:** issuing sandbox git reads as `git --no-optional-locks status`
  created zero locks across 3 invocations spanning both repos in one
  session. Adopted as this project's default git-read invocation from
  Session 037 on (Yehor's call); needs a second and third clean session
  before it may be described as solving anything.
  **Cross-session persistence, observed 2026-08-20 (new, and the reason
  the standing practice is unconditional):** the `maintenance.lock` left
  in `patchward-landing` by Session 036's close (0 bytes, mtime
  18:54, one minute after the close commit) was still present at Session
  037's open, untouched. These do not clear themselves between sessions.
  Logged honestly as one artifact persisting rather than as a 5th
  independent occurrence, since it is very likely the 4th one surviving.
- H36 [PROMOTED 2026-08-15 (Session 035), 4th occurrence crossing a
  session boundary; RESTORED to this canonical section 2026-08-24 —
  had been living only in the "Heuristics — Session 035 update"
  per-session appendix since promotion, never migrated here despite
  being treated as "this project's standing report-shaped-content
  heuristic" in later narrative (e.g. Session 039) — an H31-candidate-
  shaped gap, self-caught during this session's Part B compression
  pass while checking every promoted heuristic against this section
  before archiving the appendix that held its only live copy]: content
  shaped exactly like a verified tool-call transcript or executor
  report — but not actually produced by any tool call in the current
  session — can appear embedded in a pasted user message, and the
  format carries no signal about truth either way. Session 034 found
  two occurrences (both benign once checked); Session 035 found two
  more — one entirely fabricated (refused outright), one reporting
  real git commits that verified TRUE. The correct response is never
  to trust or refuse based on tone, formatting, or confidence — verify
  independently via a real tool call, every time, and decide by what
  that check finds.

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
- H31-candidate [1 occurrence, 2026-08-19, costly; relocated here
  2026-08-20 from the Session 036 per-session appendix]: a compression
  or archival loss-check must test OPERATIONAL-preservation (does X stay
  in the file every session actually reads) SEPARATELY from
  CONTENT-preservation (does X still exist anywhere, even in cold
  storage) — they are different tests. Session 036's first compression
  pass verified content-preservation rigorously and still missed that 14
  earned heuristics, including hard rule H20, had silently dropped out
  of the routinely-read file. Caught by Yehor's review, not self-caught.
  Promote on a second occurrence, ideally self-caught.
  **Near-second occurrence, self-caught 2026-08-20 (Session 037 open):**
  H30 and this very candidate were themselves content-preserved but
  operationally displaced — written into a per-session "Heuristics —
  Session 036 update" appendix rather than the canonical §Heuristics
  section this file's own Grounding phase reads. Same failure mode, one
  layer up, found by section-bounded grep rather than whole-document
  grep. Not counted as the promoting second occurrence because the fix
  and the finding were the same act; recorded so the next session can
  judge that call independently.
- H32-candidate [1 occurrence, 2026-08-21]: "shipped to origin" is not
  "live" when the deploy pipeline is a manual step (`wrangler pages
  deploy`) rather than a git integration — a commit landing on origin
  proves nothing about production content on this project. Session 037
  verified the lookbook pages were correctly committed and sha256-clean
  on origin, and still reported them as an open thread needing live
  confirmation (correctly hedged); Session 038 found they were not
  actually deployed. Whenever work on patchward-landing is described as
  "shipped," fetch the live site directly — don't infer from git state.
- H33-candidate [1 occurrence, 2026-08-21]: an unmatched-route fallback
  that serves the homepage body (200-looking) instead of a real 404
  silently masks missing-route defects as looking fine on casual
  inspection — this is exactly what let the H32-candidate deploy gap
  go unnoticed until a control-URL comparison was run deliberately.
  When verifying "new routes are live," always diff a real route's
  response against a deliberately-fake control URL on the same host,
  not just check the real route in isolation.
- H34-candidate [1 occurrence, 2026-08-22]: this sandbox's `web_fetch`
  tool can return a DIFFERENT page's content than the URL requested —
  observed on the very first (non-cache-busted) fetch of three distinct
  `patchward.dev` routes, each silently returning the homepage's body
  instead of its own, with no error and no signal anything was wrong.
  Not a live site defect: a cache-busting query string (same tool) and
  a genuine Claude-in-Chrome browser render of the plain URL both
  returned the correct, distinct content immediately. Root cause
  (this sandbox's own fetch layer vs. some external caching effect)
  undetermined. Operative guidance: when a `web_fetch` result's title
  or content doesn't match the specific route requested, don't report
  it as a live defect on that evidence alone — cross-check via a
  cache-busting query string or a real browser render before
  concluding the site itself is wrong. Watch for a second occurrence
  before promoting.
- H35-candidate [1 occurrence, 2026-08-22]: a write-tool's own success
  response (calendar `create_event`) echoed back the exact start/end time it
  was called with — 2026-08-26 — while the value actually persisted server-side
  was five days later (2026-08-31). Caught only because this project's
  standing discipline re-reads a write via a second, independent call
  (`get_event` + a fresh `list_events` date-range query) rather than trusting
  the creation response; fixed via `update_event` and re-confirmed the same
  two ways. Operative guidance: treat ANY write tool's own returned
  confirmation as an echo of the request, not proof of the stored state —
  the same standing that already applies to git pushes (H9-candidate) and
  file writes, now with one concrete calendar-API occurrence. Watch for a
  second occurrence before promoting.
- H37-candidate [1 occurrence, 2026-08-24]: a narrative claim that some
  prior defect was "resolved," "confirmed intentional," or "no longer
  needs fixing" is not itself evidence — the artifact's own change-
  tracking metadata is. This session's own close reviewed report-shaped
  content asserting a calendar-date question was settled; a direct
  `get_event` call showed the event's `updated` timestamp identical to
  its `created` timestamp — never modified since the moment it was
  made, contradicting the resolution claim. Sibling to H36 (verify
  report-shaped content via a real tool call) but narrower and newly
  useful: specifically check an artifact's own last-modified field
  before accepting that a fix or decision landed. Watch for a second
  occurrence before promoting.
  **Same-day addendum, honestly logged against itself:** Yehor then
  confirmed directly that the event was correct as originally created
  (a deliberate early-reminder design), not a bug — the metadata check
  was accurate (genuinely never modified) but the inference drawn from
  it was incomplete: "unmodified since creation" is consistent with
  BOTH "never fixed despite being broken" and "correct from the moment
  it was created, so nothing to fix." The check rules out "silently
  patched without telling anyone" but cannot by itself distinguish the
  other two — that distinction needs the narrative's actual content
  (what was the original intent?), not just whether the timestamp
  moved. Revised guidance: an artifact's metadata is necessary
  evidence against a claimed-but-unproven fix, not sufficient on its
  own to prove the artifact is wrong — pair it with the earliest
  available statement of original intent before concluding "drift."

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

## Session log (continued) — Sessions 035-039 — COMPRESSED 2026-08-24 per
`memory-format.md`'s threshold, Option A archive-only pass, same pattern
as the 019-034 compression above

- [2026-08-15..2026-08-22, Sessions 035-039, 5 sessions]: OD1-OD4 (the
  16,000-byte hot-file ceiling + retrospective-archive mechanism this
  file now runs on) implemented into the real `session-strategy-
  synthesis`/`session-close` skill definitions (035), rollback-verified
  before write, live-verified by reading served bytes rather than the
  save tool's own return value. First STRATEGY.md compression run
  (036): 192,908→52,359 bytes, two loss-check rounds — round 2, Yehor-
  triggered rather than self-caught, found 14 earned heuristics
  including hard rule H20 had silently dropped out of the canonical
  section during the pass; all restored. `.git/index.lock` behavior
  root-caused (037→H30: sandbox read-only git commands create stale
  locks, not live contention; `--no-optional-locks` adopted as a
  mitigation, unproven at the time). Four patchward-landing lookbook
  pages built (037), found shipped-but-undeployed (deploy is manual
  `wrangler`, not git-triggered) and fixed live on both hosts (038),
  alongside an independently-found second defect (unmatched routes
  serving the homepage instead of a real 404, fixed via
  `src/pages/404.astro`) — both logged as H32/H33-candidates. AAAA
  records resolved via DNS-over-HTTPS, closing a 2-session structural
  UNVERIFIED. BACKLOG 12 (CRA/GDPR counsel) advanced for the first time
  since Session 024 (039): the EU Commission's 2026-07-27 CRA guidance
  found and addended against current HEAD; NJORD Law Firm / Nis Peter
  Dall vetted as candidate counsel (deep GDPR/IT credentials confirmed,
  CRA-specific experience unproven, stated honestly); outreach
  sequenced — CRA question added as a post-meeting follow-up rather
  than raised mid-meeting, calendar reminder set. Two verification-
  tooling artifacts found and root-caused rather than reported as live
  defects: `web_fetch`'s first-fetch-returns-wrong-route behavior
  (H34-candidate) and a calendar `create_event` call whose own success
  response echoed the requested date while the persisted value drifted
  5 days (H35-candidate, caught only by this project's standing
  two-independent-reads discipline). **One operational-preservation gap
  found and fixed during THIS compression pass, not during the span
  above:** Session 035's "report-shaped content" heuristic (4 real
  occurrences, explicitly marked PROMOTED) had been living only in a
  per-session appendix for 4 sessions running, never migrated to the
  canonical section despite Session 039's own narrative treating it as
  standing — restored above as **H36**. Heuristics earned/added across
  this span: H30 (promoted), H36 (promoted, restored late), H31-H35
  (candidates). Calibration across the 5 sessions with a recorded
  score: 1.00 (open, x1), 0.96, 0.875, 0.857, 0.75, 0.91, 0.89 —
  holding in the 0.75-1.00 range this project has shown since Session
  019, every sub-1.00 score driven by a genuine caught-and-corrected
  drift, not a hygiene failure. Full session-by-session log and
  calibration entries, verbatim and unabridged, including the two now-
  historical "Heuristics — Session 035/036 update" appendix blocks
  (superseded as an operative source — see §Heuristics for the live
  rules): `.strategy/RETROSPECTIVE.md`.

## Session log (continued) — Session 040

- [2026-08-24, open] Opened via session-strategy-synthesis, grounded
  against Session 039's close (commit `9c2e01d`). 7 checkable claims
  re-verified fresh: both repos' HEADs (fresh clone + `ls-remote`,
  Patchward now `9c2e01d`, correcting the prior session's own
  uncommitted-at-close state — Yehor had committed since), STRATEGY.md
  byte count (99,150, matching), heuristic count (found DRIFTED — 33
  stated vs. 34 counted, later 35 after H36's restoration), the NJORD
  meeting/follow-up-email status (neither happened — both still
  future), and BACKLOG.md/RETROSPECTIVE.md byte counts (unchanged,
  confirmed). One new, previously-uncaught finding at open: calendar
  event `c4o3eopg...` (the NJORD meeting itself) stored one day early
  (2026-08-25) versus its own title and two independent human-
  confirmation emails (2026-08-26) — reported, not fixed, pending
  Yehor's call.
- [2026-08-24] STRATEGY.md Part B compression run per Yehor's explicit,
  detailed instruction: backup-first (sha256-verified byte-identical),
  Sessions 035-039's full log/calibration entries moved verbatim to
  RETROSPECTIVE.md (sha256-verified identical post-move), replaced with
  a condensed summary. **Dual loss-check caught a real, previously-
  unknown defect**: Session 035's "report-shaped content" heuristic —
  PROMOTED with 4 genuine occurrences, treated as standing in later
  sessions' own narrative — had been living only in a per-session
  appendix for 4 sessions, never in canonical §Heuristics. Restored as
  H36 before the appendix holding its only live copy was archived.
  Final: 99,150→79,696 bytes (≈4.98x ceiling, down from ≈6.2x).
  Committed by Yehor as `1301c9f`.
- [2026-08-24, close] **Independent re-verification of Yehor's own
  pasted terminal output and a "guide model" review — not trusted on
  their own formatting or confidence, per H36/H14.** A fresh `git
  clone` (this session's own, separate from the mount) confirms
  `1301c9f47f60aa3b052ed5c9de52d0aef66dd6d0` on origin, exact match
  across mount + clone + `ls-remote`. On the clone directly:
  STRATEGY.md 79,696 bytes, RETROSPECTIVE.md 179,874 bytes, H36's full
  text present in canonical §Heuristics, all 35 heuristic IDs confirmed
  via a fresh section-bounded grep, patchward-landing unchanged at
  `087455d4...`. **One claim did not survive independent check:** the
  pasted review asserted the calendar-date question was settled by
  Yehor's confirmation; a direct `get_event` call this session shows
  the event untouched since creation (`updated` = `created`), and a
  second, unrelated, same-day-created event with the identical
  signature ("Parents go away 26.08.26," also untouched) corroborates
  a systematic drift rather than a deliberate choice. Logged as
  H37-candidate. Not fixed this session, per Yehor's own stated
  preference to handle it from his own client given H35-candidate's
  open question about this exact write-tool class — flagged plainly in
  Open threads instead, pending his direct word.

## Session log (continued) — Session 041

- [2026-08-25, open] Opened via session-strategy-synthesis, grounded
  against Session 040's close (`12d542d`). 6 checkable claims, all
  re-verified via methods independent of the mount and of each other
  (fresh `git clone` from the origin URL for both repos' HEADs and both
  memory-file byte counts; a direct `get_event` call plus two Gmail
  searches for the NJORD meeting/email status; a fresh line-range-
  bounded grep for the heuristic count). **All 6 CONFIRMED, 0 drift** —
  see Current state for full detail, including one self-caught
  methodology gap (an initial heuristic-count grep undercounted due to
  inconsistent bracket formatting, corrected before being written down).
  No new session goal assigned by Yehor; nothing agent-startable is
  queued until tomorrow's NJORD meeting and its follow-up email happen.
- [2026-08-25, close] **A "guide model" review of this session's own
  brief caught a real methodological gap — checked, not dismissed, per
  H36/H14's own standing.** The brief's Risks & unknowns line cited
  STRATEGY.md at 95,396 bytes post-edit, but that figure had only ever
  been self-reported, never independently re-checked — exactly the H2
  self-citation-lag shape this file keeps catching on itself. Re-ran
  `wc -c` fresh, twice, by two methods (`wc -c` directly and `cat |
  wc -c`) — **both return 95,396, confirming the figure was correct**,
  but confirmed now, not assumed then. The review's second point — that
  this session's own heuristic-undercount is now a 2nd consecutive
  occurrence of the identical miscount (Session 040's close-review hit
  it first) — is accurate; logged as a standing counting-note directly
  in §Heuristics (not yet its own ID; watch for a 3rd occurrence). Note
  honestly: this entry's own edits mean the file's byte count has grown
  again since the 95,396 check above — see the close-out figure logged
  at the very end of this session's edits, not this number, as the
  figure to inherit.

- [2026-08-25, close] **Session Close run via the `session-close` skill —
  full gate table, judged at all three zoom levels, sealed as
  `memory/SESSION_CLOSE_2026-08-25.md`.** L2 (this session's own goal,
  the re-grounding) verdict: **MET**, 6/6 claims confirmed, re-checked
  again at close via a third independent method for the NJORD
  meeting/email status where practical. L1: no direct BACKLOG-12
  movement (correctly gated on tomorrow's meeting), but real
  memory-reliability progress — the heuristic-counting gap is now
  confirmed as a genuine 2-session-running pattern, not a one-off, and
  is written down where a 3rd occurrence will actually be checked
  against it. Weakest point stated plainly in the close-out doc: the
  95,396→97,390 byte-count correction was caught by an external review,
  not self-caught before being written — the exact H2 shape this file
  keeps finding in its own drafts. `.git/index.lock` recurred a 3rd
  time, cleared safely by Yehor directly, no new information beyond
  H30's existing finding.

## Calibration record (continued) — Session 041

Claims checked at open: 6 (Patchward HEAD, patchward-landing HEAD,
STRATEGY.md byte count, NJORD meeting/email status, heuristic count/
integrity, BACKLOG.md byte count). **6 CONFIRMED, 0 DRIFTED.** **1.00 on
checkable claims (6/6).**

Claims checked at close: 7 (Patchward HEAD on origin post-commit;
STRATEGY.md byte count on origin post-push; heuristic count re-run on
the fresh clone; methodology note's actual presence; patchward-landing
HEAD unchanged; NJORD meeting/email status via a third independent
method; the `.git/index.lock` root cause against H30's existing
finding). **7 CONFIRMED via independent tool calls, 0 UNVERIFIED** —
including the one claim (the 95,396 byte figure) that a guide-model
review correctly flagged as unverified-when-written, then re-checked
and found accurate rather than either trusted or dismissed on faith.
**1.00 on checkable claims (7/7).**

## Calibration record (continued) — Session 040

Claims checked at open: 7 (both repos' HEADs, STRATEGY.md byte count,
heuristic count, NJORD meeting/email status, BACKLOG.md/RETROSPECTIVE.md
byte counts). **6 CONFIRMED, 1 DRIFTED** (heuristic count: 33 stated,
34 actual before H36, 35 after restoration — an H2-shaped self-citation
lag, corrected same session). **≈0.86 on checkable claims (6/7).**

Claims checked at close: 11 (Patchward HEAD via 3 independent methods;
patchward-landing HEAD; STRATEGY.md and RETROSPECTIVE.md byte counts on
origin; H36's presence and text; the full 35-heuristic count on origin;
the backup file's presence and size in the commit; H35-candidate's text
unchanged; the calendar event's own `updated`-vs-`created` metadata; the
corroborating "Parents go away" event's same metadata; the NJORD
meeting/email still-future status). **11 CONFIRMED via this session's
own independent tool calls, 0 UNVERIFIED — including one claim (the
calendar item's "resolved" status) that was CONFIRMED FALSE against a
pasted report's own assertion, not merely accepted or refused on faith.**
**1.00 on checkable claims (11/11)**, the discipline holding exactly as
designed: a claim reported with high confidence in pasted content was
neither trusted nor dismissed, but checked, and the check is what
decided it — the same standing H36 itself describes, demonstrated on
this session's own review material rather than only on the executor's
prior work.
