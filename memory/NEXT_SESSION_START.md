# Patchward — Next Session Start Prompt
Generated at close of Session 012 (2026-07-10), updated same session after
the docs commit was pushed and one more hard-verification pass was run.
Paste this whole file as your opening message to start the next session
with full context restored.

---

**Resume Patchward.** Read `memory/CONTEXT.md` and `memory/project_session_log.md`
(Session 012 entry + addendum) first, in full. Do not assume anything below is
still true without re-checking — verify, don't trust memory, per standing
project rules.

## Housekeeping — confirm these before anything else

1. **Confirm the git lock is actually gone.** It was deleted once already
   this session (`Remove-Item .git\index.lock -Force`), but a follow-up
   check from the sandbox side gave an inconsistent read (briefly reported
   both "not found" and "still present" in the same check — almost
   certainly sandbox-mount staleness, not a real re-appearance, but
   unconfirmed). Run `Test-Path D:\Dev\Projects\Patchward\.git\index.lock`
   on your own machine before your first git command of the session. If
   it's `True`, delete it again.
2. **Re-confirm Fly health and `main`'s SHA fresh** — don't trust this file.
   `patchward-webhook.fly.dev/healthz` and `git ls-remote origin main` on
   your machine are both cheap, both authoritative.
3. **After any future `flyctl deploy`, check `git diff fly.toml` before
   committing anything.** Found this session: Fly's CLI silently
   regenerates fly.toml on deploy, stripping the hand-written setup
   walkthrough and `KS-TRACE` documentation and replacing it with a bare
   auto-generated version — same functional config, zero docs. Caught and
   discarded via `git restore fly.toml` this session; nothing was lost, but
   it'll happen again on the next deploy if unwatched.

## Progress list — where things stand (verified fresh, not carried over from memory)

- [x] Item #27 (webhook/billing commit `0bb0286` reachable from `main`) —
      CLOSED. Confirmed by three independent Tier-0/1 sources at the time,
      then re-confirmed a fourth time after the follow-up docs push.
- [x] Fly deployment (`patchward-webhook.fly.dev`) — alive, healthz OK,
      checked three times across the session, most recently just now.
- [x] External PR/issue tracker re-checked live — all still open as of
      2026-07-10 (Future AGI #1283, smolagents #2467, tablib #642, twisted
      #12663/#12676/#12687).
- [x] **Session 012 documentation is committed AND pushed** — commit
      `222b018` on `main`, confirmed via Yehor's own push transcript (real
      object transfer, not just a claim), `git ls-remote`
      (`222b0189d203c6f27371b322a31212994a2ce375`), and `git log` showing
      `HEAD -> main, origin/main` in agreement. This closes the loop that
      was still open at the literal end of Session 012 — the docs existed
      on disk but hadn't been pushed yet; they have been now. Includes:
      `memory/CONTEXT.md` (record-gap flag + item #27 writeup),
      `memory/project_session_log.md` (Session 012 entry + addendum),
      `memory/deep_research_prompt_org_buildplan.md`,
      `memory/BUILD_PLAN_2026-07-10.md`.
- [ ] **`memory/BUILD_PLAN_2026-07-10.md` — safely in git history now, but
      still awaiting your review and sign-off.** Being committed is not the
      same as being approved — nothing in the plan has been executed. Read
      it, edit anything you disagree with (the role name, the WSJF scoring,
      the phase numbering — all of it is a proposal), then say go. First
      concrete action in the plan is the half-day "State Reconstruction
      Audit" (Part 3 of the plan).
- [ ] `memory/project_open_tasks.md` — still NOT reconciled against the
      Patchward rename or the Phase 1.3-1.5 webhook/billing work. Either do
      this as part of the audit above, or explicitly decide it's not worth
      doing and say so.
- [ ] ClinInsight / Databutton LinkedIn DM replies — still unconfirmed as of
      2026-07-10. Answer directly, no tool check possible.
- [ ] **Backlog decision pending** — three-way tension: (a) authorized
      end-to-end pipeline test (scan→fix→verify→PR, costs API credits, may
      open a real PR), (b) Mirror Pass Tier 2, (c) callmed-landing rename.
      `BUILD_PLAN_2026-07-10.md` §6 proposes: (a) staged — fixture/owned
      repo first, real third-party second — then (c) opportunistically,
      then (b) once (a) passes. Not yet approved by you.
- [ ] Two small pre-existing items noticed but not investigated this
      session, both unrelated to today's work: `tests/fixture_repo` shows
      as a dirty git submodule, and `.dockerignore` is untracked. Neither
      is urgent; worth a look whenever convenient.

## Standing rules (unchanged, still binding)

- Verify before reporting anything as done — re-fetch/re-check live state,
  never trust a prior session's cached belief. (This exact mistake was
  caught and corrected multiple times in this project already: item #27
  itself, which reads count as ground truth during that investigation, and
  — refined further this session — which *sandbox git commands specifically*
  can be trusted, see below.)
- **Never run git writes against Patchward from the bash sandbox** — hand
  git writes to Yehor to run on his own machine.
- **Never paste or forward API keys/secrets through terminal output into
  chat.**
- Apply the trust-tier logic from `BUILD_PLAN_2026-07-10.md` Appendix B for
  any external-state claim: unauthenticated/proxied reads (e.g.,
  `api.github.com` from this sandbox) are Tier 2 and are NOT sufficient
  alone for a gating decision — corroborate with a Tier 0/1 source
  (`git ls-remote` on Yehor's machine, the authenticated GitHub web UI, a
  push transcript, or a content-addressed hash match) before treating a
  claim as confirmed. Re-confirmed again this session: `api.github.com`
  was still serving a 3-commits-stale SHA even after a real, verified push
  — this is a stable, repeatable unreliability, not a one-off.
- **Refined finding on the sandbox's own git, tested this session:**
  `git log` / `git ls-remote` (reading refs and objects) proved reliable —
  they picked up Yehor's real commit correctly. `git status` / `git diff`
  / `cat` / `wc` (reading working-tree state and file content) proved
  **unreliable and did not self-correct**, even hours later and even after
  a real commit landed — `memory/CONTEXT.md` still read as 73 stale lines
  and still showed as "modified" via sandbox `git status` long after Yehor
  had already committed and pushed it cleanly. **Practical rule: trust the
  sandbox's `git log`/`git ls-remote` output; do not trust its `git
  status`/`git diff`/`cat`/`wc` output for anything — always defer to
  Yehor's own machine for those.**

## Suggested first move

Ask directly: "Have you had a chance to read `BUILD_PLAN_2026-07-10.md`? Do
you want to authorize the State Reconstruction Audit (Part 3), or should we
start with the backlog item instead (E2E test / Mirror Pass Tier 2 /
callmed-landing)?" — don't assume; the plan explicitly hasn't been signed off.
