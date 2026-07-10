# Patchward — Next Session Start Prompt
Generated at close of Session 012 (2026-07-10). Paste this whole file as your
opening message to start the next session with full context restored.

---

**Resume Patchward.** Read `memory/CONTEXT.md` and
`memory/project_session_log.md` (Session 012 entry) first, in full. Do not
assume anything below is still true without re-checking — verify, don't trust
memory, per standing project rules.

## Housekeeping — do these two things before anything else
1. **On your own machine, delete the stale git lock:**
   `Remove-Item D:\Dev\Projects\Patchward\.git\index.lock -Force` (if it still
   exists — check first with `Test-Path`). It was left behind by a read-only
   `git status` call during Session 012 and could block your next real git
   command if not cleared.
2. **Re-confirm Fly health** (`patchward-webhook.fly.dev/healthz`) and
   **re-confirm `main` via `git ls-remote origin main` on your machine** —
   both were last verified 2026-07-10, re-check fresh rather than trusting
   this file.

## Progress list — where things stand

- [x] Item #27 (webhook/billing commit `0bb0286` reachable from `main`) —
      CLOSED, confirmed 2026-07-10, three independent checks.
- [x] Fly deployment (`patchward-webhook.fly.dev`) — alive, healthz OK.
- [x] External PR/issue tracker re-checked live — all still open as of
      2026-07-10 (Future AGI #1283, smolagents #2467, tablib #642, twisted
      #12663/#12676/#12687).
- [x] `memory/CONTEXT.md` rewritten to flag the record gap and log the
      verification lesson from the item #27 incident.
- [x] Deep-research brief written and used to commission 3 independent
      research runs → synthesized into `memory/BUILD_PLAN_2026-07-10.md`.
- [ ] **`memory/BUILD_PLAN_2026-07-10.md` — awaiting your review and
      sign-off.** Nothing in it has been executed. Read it, edit anything
      you disagree with (the role name, the WSJF scoring, the phase
      numbering — all of it is a proposal), then say go. First concrete
      action in the plan is the half-day "State Reconstruction Audit"
      (Part 3 of the plan).
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

## Standing rules (unchanged, still binding)

- Verify before reporting anything as done — re-fetch/re-check live state,
  never trust a prior session's cached belief. (This exact mistake was
  caught and corrected twice in this project already: once re: item #27
  itself, once re: which reads count as ground truth during that
  investigation.)
- **Never run git writes against Patchward from the bash sandbox** — hand
  git writes to Yehor to run on his own machine. This includes things that
  look read-only but touch `.git` state under load (see the index.lock
  finding above).
- **Never paste or forward API keys/secrets through terminal output into
  chat.**
- When verifying live external state, apply the trust-tier logic from
  `BUILD_PLAN_2026-07-10.md` Appendix B: unauthenticated/proxied reads
  (e.g., `api.github.com` from this sandbox) are Tier 2 and are NOT
  sufficient alone for a gating decision — corroborate with a Tier 0/1
  source (`git ls-remote` on Yehor's machine, the authenticated GitHub web
  UI, or a content-addressed hash match) before treating a claim as
  confirmed.
- If editing a file this session and later checking it via bash (`cat`,
  `wc`, `diff`), be aware the bash sandbox's view of that file can be stale
  relative to the Read tool's view, with no observed self-correction on
  retry (found and confirmed in Session 012). **Verify file integrity via
  Read, not bash, for anything just written in the same session.**

## Suggested first move

Ask directly: "Have you had a chance to read `BUILD_PLAN_2026-07-10.md`? Do
you want to authorize the State Reconstruction Audit (Part 3), or should we
start with the backlog item instead (E2E test / Mirror Pass Tier 2 /
callmed-landing)?" — don't assume; the plan explicitly hasn't been signed off.
