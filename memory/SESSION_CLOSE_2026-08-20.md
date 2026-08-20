# Session Close — Patchward — 2026-08-20 (Session 037)

## Gate status

| Claim | Pass 1 | Pass 2 | Verdict |
|---|---|---|---|
| Patchward HEAD `b78d6cb` (as inherited at open) | `.git/HEAD` + `refs/heads/main` | reflog tail + `log -2` | CONFIRMED |
| patchward-landing HEAD `6f98bc4` (as inherited), clean | `refs/heads/main` | `status --porcelain` tracked-clean | CONFIRMED |
| callmedai.com Gate-3 corrected copy, `/` + `/security` | live fetch of `/security` | independent live fetch of `/` | CONFIRMED |
| patchward.dev live, tagline, "565 passed", `/facts` | live fetch of `/` | independent live fetch of `/facts` | CONFIRMED |
| A/AAAA records | — | sandbox has no DNS resolver at all; DoH blocked | **UNVERIFIED** |
| STRATEGY.md ~59,837 bytes (at open) | `ls -la` | section map, 15 headings, no regrowth | CONFIRMED |
| RETROSPECTIVE.md 154,004 bytes | `ls -la` | — | CONFIRMED |
| 22 earned heuristics content-present | grep across whole file | H20 body read in full, correct | CONFIRMED |
| H30 operationally live in canonical §Heuristics (at open) | grep whole document (found H30) | section-bounded grep, lines 476–722 only (H30 absent from bounds) | **DRIFTED** — present but displaced, same failure class as H31-candidate |
| Lookbook pages unstarted (at open) | `src/pages/` directory listing | — | CONFIRMED |
| BACKLOG.md 120,268 bytes | `ls -la` | — | CONFIRMED |
| "H30 has 5 confirmed occurrences" (carried into an executor instruction) | — | independent recount from the file's own history: 4 substantiated; the apparent 5th was the 4th persisting across the session boundary, not a new event | **DRIFTED** — corrected same turn, before being written into the permanent record |
| H30/H31 relocated into canonical §Heuristics | Edit applied, text read back | section-bounded grep on a **fresh clone of origin** (not the mount), post-commit | CONFIRMED |
| STRATEGY.md new size 64,254 bytes | `Read` + `wc -c` on the mount | sha256 match against a fresh clone of origin (`9b78ae53…`) | CONFIRMED |
| `astro build` clean, 4 new routes | build log, exit 0 | `find dist -name '*.html'` lists all 4 | CONFIRMED |
| Zero hand-typed figures on the 4 new pages | Python HTML-strip + digit extraction | every surviving number cross-checked against `facts.yaml` by hand | CONFIRMED |
| Executor's Block 2 report: real-repo working-tree changes present | sandbox mount `git status` (self-consistent, but never checked against Yehor's own view) | Yehor's own `git status` at the time showed **nothing** | **DRIFTED** — the claim was true but was asserted before the one check that actually mattered was run |
| — same claim, re-investigated | mtime ordering (edits at 15:20–15:23, build-copy `cp` stamped 15:23:28, later) | Yehor's own re-run `git status`/`git diff --stat`, ~10 minutes later, now matching exactly | CONFIRMED (RESOLVED — sync-propagation lag, not lost or misplaced work) |
| No sandbox-issued `git add`/`commit`/`push` against either repo | reconstructed this session's own bash call history (status/diff/ls-remote/clone only) | reflog on both repos shows exactly one new commit each, both authored `Yehor <yehor.callmedai@gmail.com>` | CONFIRMED |
| patchward-landing commit `7b6cf22` landed on origin | `ls-remote origin main` | fresh clone + sha256 of all 6 changed files, matched against the mount | CONFIRMED |
| Patchward commit `a246fc6` landed on origin | `ls-remote origin main` | fresh clone + sha256 of `STRATEGY.md`, matched against the mount | CONFIRMED |
| Cited figures (565, 91.20, 3.12, #261, B110, 5.17.3) genuinely present in shipped content | — | grepped directly out of the fresh clone's `facts.yaml`, not inferred from the sha256 match alone | CONFIRMED |
| Both working trees clean at this close, only known scratch untracked | fresh `git status --porcelain`, both repos | `git log -1 --stat` on both matches the hashes above; no lockfiles present | CONFIRMED |

**22 claims checked this session** (11 at open/synthesis, 11 during/at close). **18 CONFIRMED, 3 DRIFTED, 1 UNVERIFIED** (unverifiable by design — no DNS resolver in this sandbox, not a gap in method). **0.857 on checkable claims (18/21, excluding the one structurally-unverifiable claim).**

## Session judgment

**L3 Artifacts:**
- Patchward commit `a246fc6` — H30 (earned, 4 confirmed occurrences) and H31-candidate relocated from a per-session appendix into the canonical §Heuristics section, where the Grounding phase of every future open actually reads. `--no-optional-locks` logged as H30's first attempted mitigation (1 clean session, not yet a claimed fix). `.strategy/STRATEGY.md`: 59,837 → 64,254 bytes, sha256-verified on origin against a fresh clone.
- patchward-landing commit `7b6cf22` — the four lookbook pages (`/how-it-works`, `/verification`, `/data-boundary`, `/examples`) built from the tracked lookbook spec, three new ledger entries added to `facts.yaml` (`branch-convention`, `example-prs-patchward`, `example-pr-checkdmarc`), `Layout.astro` footer wired to the new routes. `astro build` clean, zero hand-typed figures, sha256-verified file-by-file against a fresh clone of origin.
- A genuine chain-of-custody investigation, triggered by Yehor catching a real discrepancy between an executor report and his own terminal, resolved with mtime evidence, re-run git status, and — on a second, more rigorous challenge — full sha256 verification of all six changed files plus direct confirmation that no sandbox process ever issued a git write command against this repository.

**L2 Goal:** Two goals, both set explicitly at open (via `AskUserQuestion`, Yehor's own selection) — fold H30/H31 into canonical §Heuristics with the lock-mitigation logged honestly, and build the four lookbook pages ledger-sourced and uncommitted for review. **MET, both**, evidenced by the two independently-verified commits above.

**L1 Horizon:** Real movement on "prospect → pilot request has no supporting surface" — the one item this project's own memory has repeatedly named as the strongest lever, now shipped. Separately, a smaller but real reduction of a second, compounding obstacle: Session 036's own H31-candidate (operational vs. content preservation) came within one layer of recurring inside this very session — caught before promotion, and the memory system is measurably more reliable for it. The CRA/GDPR deadline (2026-09-11, now 22 days out) remains untouched, correctly — outside this project's agent-startable scope.

## Decisions made this close

- H30 promoted to the canonical earned list (4 confirmed occurrences, past this project's threshold); H31-candidate placed in the candidates subsection (1 full occurrence plus 1 near-second, not yet promoted). The old Session-036 appendix text is left in place with a relocation notice, per this file's own never-launder-history rule.
- `--no-optional-locks` adopted as this project's default sandbox git-read invocation from Session 037 forward — explicitly logged as unproven (1 clean session; needs 2 more before it may be called a fix).
- Three new `facts.yaml` entries added rather than hand-typing the corresponding page copy; the mpfb2 PR count is stated without individual links, since no available source distinguishes which two of nine merged PRs are Patchward's — the non-attribution is itself the verified finding, not a gap papered over.
- Both commits staged, committed, and pushed by Yehor from his own terminal, per H20. No sandbox git write was ever issued against either repository this session.

## Weakest points, stated plainly

- **The Block 2 completion report claimed the real repository's working tree matched what had been built, without first checking the one thing that actually settles that question — Yehor's own terminal.** It reasoned from the sandbox mount's internal self-consistency (files present, git status agreeing with itself) and presented that as equivalent to "your repo has these changes." It does not, structurally, prove that — and in this case Yehor's own `git status`, run within the same few minutes, showed nothing. He declined to accept the report on trust and named the gap directly. The investigation that followed found real, checkable evidence (mtime ordering showing the build-copy was made *from* the real edits, not the reverse; a clean re-run of `git status` once sync caught up) that this was a propagation lag, not lost work — but the report itself was issued before that check, not after. This is the session's own worked example of the discipline this project runs on: a claim was not accepted until its gap was named, investigated, and closed with actual proof — sha256 hashes, a fresh clone, reflog history — not with reassurance. Recording it here in full, per Yehor's explicit instruction, rather than letting it fold quietly into "resolved."
- **The first resolution of that gap was correct but underspecified.** Yehor had to ask a second, more rigorous round of questions — the full chain-of-custody breakdown, confirmation that no sandbox process ever wrote to git, sha256 of every changed file against a fresh clone — before the matter was genuinely closed. The first answer reached the right conclusion without the rigor that made a second challenge unnecessary. Worth naming as its own lesson, separate from the underlying gap: closing an evidence question needs to anticipate the skeptical follow-up, not just answer the question as asked.
- **A number nearly entered the permanent record unverified.** Yehor's own executor instruction stated "H30 has 5 confirmed occurrences." This session's own check could substantiate only 4; the apparent 5th was the 4th occurrence persisting across the session boundary, not a new event. It was caught and corrected in the same turn, before being written into `STRATEGY.md` — but it is a direct instance of exactly the kind of uncritical-carry-forward this project's heuristics (H2, H14) exist to prevent, this time originating from a user-provided instruction rather than a "guide model" message. Recorded as a reminder that the discipline applies uniformly to the source, not selectively.
- **Self-report checklist (Phase 5.8):**
  - Anything reported "done" without an independent check this session? Yes, once — the Block 2 working-tree claim above — and it is the weak point already named, not softened.
  - Content shaped like a tool-call transcript without an actual tool call producing it? No — every transcript-shaped block this session was Yehor's own pasted PowerShell output, and each was cross-checked against `ls-remote`/fresh-clone/reflog evidence rather than trusted at face value.
  - Any file/skill edited without a rollback/verification step available? No skill files touched. `STRATEGY.md` was edited additively (relocation plus a superseding notice, nothing deleted from live content) and verified immediately after via section-bounded grep on a fresh clone — but unlike Session 036's Part-A compression, no explicit pre-edit backup file was written first. The edit's lower blast radius (additive-only, not a rewrite) makes this a materially smaller risk, but the step itself was skipped; naming it rather than covering it.
  - Did this close-out's own draft soften or omit a weak point a skeptical read would catch? The Block 2 gap is the obvious candidate for softening and is stated above at full length, including the "first resolution wasn't rigorous enough" point, which is the easiest part of this story to leave out.

## File manifest

**Committed, `Patchward`:** `.strategy/STRATEGY.md` (modified, H30/H31 relocation) — commit `a246fc6`.

**Committed, `patchward-landing`:** `src/data/facts.yaml`, `src/layouts/Layout.astro`, `src/pages/how-it-works.astro`, `src/pages/verification.astro`, `src/pages/data-boundary.astro`, `src/pages/examples.astro` — commit `7b6cf22`.

**Deliberately excluded / left for Yehor:**
- `memory/DRAFT-STRATEGY-COMPRESSED-2026-08-19.md` (Patchward) — superseded Session 036 scratch copy, fully absorbed into the committed `STRATEGY.md`; harmless if deleted or committed, Yehor's call, not acted on this session.
- `memory/DRAFT-session-close-2026-08-15.md`, `memory/DRAFT-session-strategy-synthesis-2026-08-15.md` (patchward-landing) — pre-existing scratch, untouched, not this session's concern.
- `tests/fixture_repo` gitlink dirty flag (Patchward) — known cosmetic noise from an untracked `__pycache__` inside a nested gitlink, unchanged.

## Next-session opening prompt

```
Open this session via the session-strategy-synthesis skill, grounding in
D:\Dev\Projects\Patchward\.strategy\STRATEGY.md (Session 037's close is
the most recent entry). Re-verify — don't inherit:

1. Patchward HEAD (expect `a246fc644687d0e277a9f1002efced1c32a31070`).
2. patchward-landing HEAD (expect `7b6cf22339b3dcb34116312a6339d855c487918f`,
   clean).
3. callmed-landing — content check on callmedai.com (Gate-3 corrected copy,
   both `/` and `/security`); exact commit hash stays UNVERIFIED by design.
4. patchward.dev still live and correct (real tagline, "565 passed",
   A/AAAA records, `/facts` content matching what's cited here).
5. The four new patchward-landing pages are actually live and correct:
   fetch `/how-it-works`, `/verification`, `/data-boundary`, `/examples`
   on whatever host serves this site's deploy, confirm all four render,
   and spot-check that the cited figures (565, 91.20%, uv tool install
   patchward, checkdmarc#261 labelled "closed — superseded" not "merged")
   match `/facts` rather than looking hand-typed. This is the first
   session where these pages are checkable as shipped, not as source.
6. STRATEGY.md's own state: confirm it is genuinely ~64,254 bytes (not
   silently regrown), confirm .strategy/RETROSPECTIVE.md still exists
   (154,004 bytes), and confirm all 22 earned heuristics plus H30
   (23 total) are present WITHIN THE CANONICAL §HEURISTICS SECTION
   BOUNDS specifically (grep between "## Heuristics (earned)" and
   "## Failed approaches (ledger)"), not just present anywhere in the
   file — Session 037 found that whole-document grep had missed exactly
   this distinction once already. Spot-check H20 and H30 specifically.

L2 candidates, roughly in order of readiness:

* STRATEGY.md Part B compression — rewriting Current state/Open threads
  for genuine <=16,000-byte compliance. Now 4.02x over (64,254 bytes),
  up from 3.7x at Session 036's close — the overage grows every session
  this is deferred. Same discipline as before: backup-first, loss-check
  BOTH content and operational preservation from the start (per
  H31-candidate), review before commit.
* BACKLOG.md's 120,268 bytes — flagged, not yet mechanism-covered.
* Bringing multi-model-research-synthesis into this environment's own
  account registry — needs its content pasted fresh into save_skill;
  confirmed not recoverable from either connected repo.
* --no-optional-locks mitigation (H30): needs 2 more clean sessions
  (1 down) before it can be described as more than a data point.

New this session, worth watching for a second occurrence:
* Sandbox-write-to-real-mount propagation can lag behind a same-session
  git status check on Yehor's own machine by roughly 10 minutes under
  load (observed once, Session 037, resolved via mtime evidence and a
  clean re-check — not yet a heuristic, needs a second occurrence before
  promotion). If a future session sees a real-repo git status appear to
  disagree with a just-completed file-tool write, re-check after a short
  wait before treating it as lost work.

Standing, not blocking anything: sandbox git status/diff/fetch on either
repo can leave a fresh stale .git/index.lock or objects/maintenance.lock
behind — confirmed persisting across the Session 036->037 boundary
untouched (H30). Clear via Remove-Item from Yehor's own terminal before
any write, every time. `--no-optional-locks` is now this project's
default sandbox git-read invocation (see H30, mitigation note) — one
clean session so far, unproven, watch for continued zero-lock results.
Full detail: memory/SESSION_CLOSE_2026-08-20.md.
```
