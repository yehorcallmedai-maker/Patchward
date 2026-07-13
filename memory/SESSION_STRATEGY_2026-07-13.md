# Patchward — Session 013 Strategy & Verification Synthesis

**Generated:** 2026-07-13, session opening pass
**Author:** Claude (agent)
**Status:** proposal — decision points in §3 need Yehor's sign-off before any execution begins. Nothing in §4 has been run.

---

## 0. Purpose

A hard-verification double-check of the Session 012 handoff, cross-referenced
against `memory/BUILD_PLAN_2026-07-10.md`, followed by one sequenced,
checkable progress list for this session. Every claim in §1 carries an
evidence tuple — `(claim, evidence, tier, result)` — per the trust-tier
protocol BUILD_PLAN proposes (§4.3 / Appendix B), applied here even though
`VERIFICATION.md` doesn't formally exist yet.

**Tier key:** 0 = deterministic/content-addressed (git hashes, `git
ls-remote`, direct file read). 1 = authenticated direct read (direct HTTPS,
not proxied). 2 = proxied/unauthenticated — not used below; nothing here
rests on a Tier-2 source.

---

## 1. Hard-verification pass — results

| # | Claim | Evidence | Tier | Result |
|---|---|---|---|---|
| 1 | `.git/index.lock` is gone | `ls -la .git/index.lock` → No such file | 0 | CONFIRMED |
| 2 | `main` HEAD | `git rev-parse HEAD` = `d4569d4…`; `git ls-remote origin main` = same SHA | 0 | CONFIRMED — one commit ahead of the `222b018` cited in the handoff doc (`d4569d4`, "docs: update next-session prompt…"), consistent with the doc's own note that it was amended post-push |
| 3 | Fly deployment alive | `GET https://patchward-webhook.fly.dev/healthz` → `{"status":"ok"}` | 1 | CONFIRMED |
| 4 | `project_open_tasks.md` reconciled against rename/webhook work | Read in full | 0 | **NOT RECONCILED** — file still ends "PROJECT COMPLETE — RepoMend v0.1.0", last updated 2026-06-23, zero mention of Patchward, `webhook.py`, or Fly. Matches CONTEXT.md's own flag. |
| 5 | ADR log reflects rename/webhook decisions | Grepped ADR-017 through ADR-026 | 0 | **NOT PRESENT** — log stops at ADR-026 (Phase 7, 2026-06-23). No ADR exists for the rename, the FastAPI/webhook stack, Fly deployment, or Marketplace billing. This is the concrete gap BUILD_PLAN's retroactive-ADR deliverable is meant to close. |
| 6 | `fly.toml` working-tree state | `git diff HEAD -- fly.toml` | 0 | **NEW FINDING — see §2** |
| 7 | Webhook HMAC signature check | Read `src/patchward/webhook.py` L70-87 | 0 | **Already implemented** — `hmac.compare_digest`, timing-safe, tested (`tests/test_webhook.py` exists). Phase 9 Exposure Gate item 1 is effectively done, not outstanding. |
| 8 | Deny-by-default for unrecognized webhook events | Read `src/patchward/webhook.py` L241-244 | 0 | **Deliberately not deny-by-default** — code returns 200 `{"status":"ignored"}` for unrecognized events, with an inline rationale (GitHub disables a webhook after enough consecutive non-2xx responses). Contradicts BUILD_PLAN's checklist as literally written — this is a real design decision that was made and never written down, not a silent gap. |
| 9 | Rate limiting / body-size limits on `/webhooks/github` | Grepped file | 0 | **NOT PRESENT** — confirmed gap |
| 10 | `X-GitHub-Delivery` structured logging | Grepped file | 0 | **NOT PRESENT** — logs `event`/`action` only — confirmed gap |
| 11 | `pip-audit` scoped to the `webhook` extra | Found the extra group in `pyproject.toml` (fastapi/uvicorn/pyjwt/httpx) | 0 | Extra group exists; no evidence a scoped run has happened |
| 12 | Test suite count / coverage | — | — | **NOT RE-VERIFIED THIS SESSION** — `uv run pytest` needs Windows (RULE-4), only runnable by you. Do not treat "371 passed / 89%" as current — it predates the rename. |

---

## 2. New finding: `fly.toml` has uncommitted drift right now

`git diff HEAD -- fly.toml` shows the working tree currently holds the bare,
`flyctl`-regenerated version — the hand-written KS-TRACE comment block and
setup walkthrough that Session 012 restored via `git restore fly.toml` are
**not present in the working copy**, even though they're intact in committed
`HEAD` (`d4569d4`). Functionally identical config either way, but this is
exactly the failure mode your own housekeeping rule #3 warned about: either a
`flyctl deploy` ran again after the last commit and stripped it a second
time, or the restore never landed on disk on this mount.

**Needs your own-machine confirmation before anything else touches
`fly.toml`.** Run `git status` / `git diff -- fly.toml` yourself. If it
confirms the stripped version is sitting uncommitted, either `git restore
fly.toml` again or accept the stripped version and re-add the docs by hand
once — but don't let it drift silently a third time.

**Addendum, same day:** Yehor ran the above. Both came back clean —
`fly.toml` was never modified. This §2 finding was a false positive
produced by an unreliable sandbox `git diff` read, not a real drift. Full
correction and the resulting broader tool-reliability finding are in
`memory/STATE.md`'s "Working-tree state" section — the short version is
that this session's sandbox `git status`/`git diff` cannot be trusted for
working-tree comparisons on this mount at all, not just for files edited
earlier in the same session. No `fly.toml` action is needed.

---

## 3. Decision points still open — your call

1. **BUILD_PLAN sign-off** — proposed, not authorized. Nothing in it has executed.
2. **Backlog sequencing** — State Reconstruction Audit vs. Stage-1 E2E pipeline test vs. Mirror Pass Tier 2 vs. callmed-landing.
3. **`fly.toml` drift (§2)** — restore, or accept and re-document.
4. **Exposure Gate scope** — given finding #8, do you want unrecognized-event handling changed to reject, or is "acknowledge + log" the accepted design? Either answer is fine, but it should become an ADR instead of staying implicit in a code comment.

---

## 4. Recommended step-by-step progress list for this session

Sequenced so each step is small and checkable, and nothing touches the real
remote, spends API credits, or opens a real PR until you explicitly say go.

1. [ ] **Confirm `fly.toml` drift (§2)** on your own machine — cheap, time-sensitive, blocks nothing else but should go first.
2. [ ] **Answer the four items in §3** — even one line each unblocks everything below.
3. [ ] **State Reconstruction Audit** (BUILD_PLAN Part 3, if authorized) — capped 5-artifact deliverable:
   - [ ] Tag `state-audit-2026-07` at current HEAD
   - [ ] `memory/STATE.md`, evidence-tupled — most of the legwork is already done in §1 above
   - [ ] 4-6 retroactive ADRs: RepoMend→Patchward rename, FastAPI/Uvicorn/PyJWT webhook stack, Fly.io deployment, Marketplace billing shift, PyPI Trusted Publisher scaffold, plus one covering the unrecognized-webhook-event decision (finding #8)
   - [ ] One Consolidated Keystone Report (`docs/keystones/`) for 2026-06-23 → 2026-07-09
   - [ ] `memory/BACKLOG.md`, seeded from BUILD_PLAN §6
4. [ ] **Reconcile `project_open_tasks.md`** — fold into the audit's STATE/BACKLOG split, or explicitly archive it as RepoMend-era and stop maintaining it. Your call either way, just make it a decision, not a drift.
5. [ ] **Phase 9 Exposure Gate — narrowed scope** (per §1, HMAC is already done; remaining real gaps only):
   - [ ] Rate limiting / body-size limits on `/webhooks/github`
   - [ ] `X-GitHub-Delivery` header added to structured logs
   - [ ] `pip-audit` run scoped to the `webhook` extra
   - [ ] ADR on unrecognized-event handling (finding #8)
6. [ ] **Stage 1 E2E test** (scan→fix→verify→PR against a repo you own) — only after steps 3-5, per BUILD_PLAN's own convergent sequencing logic: don't build more on an unvalidated core.
7. [ ] **Session close** — WORKLOG/session-log entry with commit hashes for whatever actually got done this session, plus a regenerated next-session start prompt.

---

## 5. What this session has NOT done

Did not run `uv run pytest`, did not touch `fly.toml`, did not create ADRs,
tags, or `STATE.md`. All of §4 is proposed and sequenced, none executed —
pending your answers in §3.
