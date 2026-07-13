# BACKLOG — priority-ordered
Seeded 2026-07-13 from `memory/BUILD_PLAN_2026-07-10.md` §6 (WSJF
resolution, approved by Yehor 2026-07-13) plus this session's narrowed
Phase 9 Exposure Gate findings. Re-scored weekly per BUILD_PLAN §7 cadence
once that cadence actually starts — this is the seed, not a steady-state
process yet.

Framework: WSJF (Cost of Delay ÷ Job Size) + an explicit irreversibility
check, per BUILD_PLAN §6.

---

## 1. State Reconstruction Audit close-out
**WSJF: highest (in progress).** Tag `state-audit-2026-07`, get
`memory/STATE.md`, ADR-027 through ADR-032, the Consolidated Keystone
Report, and this file all reviewed and committed as one unit. Everything
below this line is easier to prioritize correctly once this lands, because
right now the backlog itself is partly built on a reconstructed-not-verified
foundation.
**Owner:** Yehor (review + commit + tag — all git writes run on his
machine, not the sandbox).
**Blocks:** nothing downstream is hard-blocked, but doing this first is the
whole point of the audit — see BUILD_PLAN §1's operating principle.

## 2. `fly.toml` drift resolution — CLOSED, false positive
**Resolved 2026-07-13, no action needed.** The claimed drift was a
sandbox `git diff` misread, not a real working-tree change — Yehor's own
`git status`/`git diff` came back clean. See `memory/STATE.md` and the
correction appended to ADR-029. Retained here (rather than deleted) as a
record that this line item was opened and closed same-day, not silently
dropped.

## 3a. Verifier gate gap — broken fix passed all 3 gates (NEW, HIGH)
**WSJF: highest — this blocks everything downstream.** Stage-1 E2E
(below) found a Fix-Gen output that deletes a needed import while the
code that uses it is untouched — objectively broken (`NameError` at
runtime) — and the Verifier marked it `VERIFIED` with all 3 gates
passing. Full writeup: `docs/keystones/stage1_e2e_test_2026-07-13.md`
§2. This is a structural gap, not a fixture quirk: Gate 1 misses it
because removing an import can silence a semgrep rule without fixing the
underlying call; Gate 3 misses it because the fixture's test suite
doesn't exercise the affected function. Recommend blocking Stage 2
(third-party repo) and Mirror Pass Tier 2 until this is addressed, per
BUILD_PLAN §6's own "don't build on an unvalidated core" logic.
**Owner:** needs Yehor's decision on approach (stronger Gate 1 call-site
check vs. stronger Gate 3 coverage requirement vs. constraining Fix-Gen's
prompt to never remove a still-referenced import) before implementation.

## 3b. `GITHUB_TOKEN` cannot create PRs (NEW, MEDIUM)
Branches push successfully; `POST /pulls` returns 403 three times in the
Stage-1 run. Classic signature of a token with contents-write but not
pull-request-write permission (fine-grained PAT) or an expired/revoked
classic PAT. **Owner:** Yehor — check/regenerate `GITHUB_TOKEN`
permissions. See `docs/keystones/stage1_e2e_test_2026-07-13.md` §3.

## 3c. CLI misreports failed PR creation as success (NEW, LOW)
`cli.py` L496-499 prints `[PR] Opened: {url}` unconditionally, without
checking `pr_dict['status']` — a 403/422 failure prints as if it
succeeded, just with a blank URL. Confirmed by direct code read. Cheap
fix. **Owner:** Claude (agent), straightforward one-condition fix.

## 3d. Investigate "requires login" invalid branch name (NEW, unconfirmed root cause)
One finding (semgrep subprocess-shell-true) produced a branch name
containing the literal text "requires login", an invalid git ref
(contains a space), crashing `git worktree add`. Hypothesis (not yet
confirmed): semgrep's `p/python` registry pack triggered a login-gated
request whose message leaked into the fingerprint/finding-id pipeline.
Needs investigation before being treated as understood. **Owner:** TBD.

## 3. Stage 1 — E2E pipeline test against an owned repo — COMPLETE, result documented
Full report: `docs/keystones/stage1_e2e_test_2026-07-13.md`. Headline:
3/5 findings reached "verified" status, all 3 branches pushed to the real
remote (confirmed via `git ls-remote`, not just trusting CLI output), 0
PRs opened (blocked by item 3b), and of the 3 "verified" fixes only 2 are
actually correct (item 3a). This is exactly the outcome BUILD_PLAN
predicted was possible and valuable — a cheap Stage-1 failure surfaced
the biggest problem before Stage 2 or wider exposure. Superseded-text
below kept for record of what was planned going in:
**WSJF: highest** (risk-reduction, small job size, the entire product
thesis is unproven end-to-end since the rename). Precondition (item 4)
satisfied 2026-07-13. Pre-flight complete same day:
- `patchward.toml` config defect found and fixed (see `memory/STATE.md`)
- Live dry-run `patchward scan --repo tests\fixture_repo` confirmed 5
  actionable findings (semgrep subprocess-shell-true, bandit
  B602/B307/B105/B404) — two-pass verified against `git show
  HEAD:vulnerable.py`, see Session Strategy brief 2026-07-13
- Decision: run `patchward fix` against all 5 findings unmodified (no
  CLI-level single-finding filter exists; narrowing further would mean
  unproven bespoke engineering on the thing being validated)
**Owner:** Yehor runs `patchward fix` on his own machine (real git push +
PR creation — never from the agent sandbox, per standing rule).
**Still unverified going in:** `GITHUB_TOKEN` push/PR path — `scan`
never exercises it; first real test is this run itself. Treated as an
acceptable unknown, not a blocker — a credential failure here is still a
clean, informative Stage-1 result.
**Gate:** falsifiable either way — a Stage 1 failure is the cheapest place
to find the biggest problem.

## 4. Re-verify test suite on current `main` — CLOSED 2026-07-13
**Result: 421 passed, 2 skipped, 15 deselected, 90.01% coverage.**
Confirmed by Yehor on his own machine, promoted into `memory/STATE.md`.
Found and fixed a real environment defect along the way (stale `.venv`
Windows trampoline launchers, left over from before the project
directory's rename — see `memory/STATE.md`'s Tests section for the fix).
Item 3's precondition is now satisfied.

## 5. Phase 9 Exposure Gate — narrowed scope
**WSJF: high** (security-adjacent, small-medium job size, already-live
surface). Per this session's verification, HMAC signature validation is
already done — do not re-implement it. Real remaining items:
- Rate limiting / request body size limits on `/webhooks/github`
- `X-GitHub-Delivery` header in structured logs (needed for any future
  incident report or GitHub support ticket)
- `pip-audit` run scoped to the `webhook` optional-dependency group
- Confirm `is_entitled()` correctly treats `cancelled`/`pending_change`
  Marketplace status as non-entitled (test gap identified in the
  Consolidated Keystone Report §5 — may already be correct, just unconfirmed)
**Owner:** Claude (agent) for implementation, Yehor reviews line-by-line
per BUILD_PLAN §2's security-boundary rule.

## 6a. Fix `patchward.toml.example` (Phase 7 distribution deliverable)
**WSJF: medium — real defect in a committed, user-facing artifact, cheap
to fix.** The example config that shipped in ADR-025/Phase 7 has no
`[patchward]` section and no `repo_path` field at all (the single most
critical required field for single-repo mode), plus a nonfunctional
`[anthropic]` section that doesn't match `config.py`'s actual schema
(`anthropic_api_key` comes from the env var, not a toml section). A new
user following this template would hit the exact same hard config-load
failure this session found and fixed in the real `patchward.toml`. Found
2026-07-13 while preparing the Stage-1 E2E test; see `memory/STATE.md`.
**Owner:** Claude (agent) to rewrite, Yehor to review.

## 6. `docs/architecture/patchward-webhook-billing-design.md` decision
**WSJF: low, but cheap to resolve.** Three KS-TRACE code comments cite this
file by path; it does not exist in the repo. Either recreate it from the
now-written ADR-028/ADR-030 content, or scrub the dead references so future
readers don't go looking for a file that isn't there.
**Owner:** Claude (agent), Yehor picks which option.

## 7. `project_open_tasks.md` reconciliation
**WSJF: low.** File still ends "PROJECT COMPLETE — RepoMend v0.1.0",
last updated 2026-06-23, no mention of the rename or webhook work. Two
options: fold remaining open items into this BACKLOG.md and archive the
old file as RepoMend-era history, or keep maintaining it separately. Needs
an explicit decision, not further drift.
**Owner:** Yehor to decide, Claude to execute either way.

## 8. callmed-landing rename
**WSJF: low-medium, near-zero job size, zero downstream dependency.**
Slot into any gap while blocked on items 1-5.
**Owner:** Claude (agent).

## 9. PyPI Trusted Publisher — confirm live
**WSJF: low for now** (not blocking anything until a release is actually
cut). Confirm PyPI-side Trusted Publisher registration for the `patchward`
project exists, and that `.github/workflows/publish.yml` has been
exercised at least once via `workflow_dispatch` before relying on it for a
real release.
**Owner:** Yehor (PyPI account access required).

## 10. Mirror Pass Tier 2
**WSJF: lowest for now — contingent, not low-value.** Its value depends on
item 3 (Stage 1 E2E) confirming the pipeline actually works post-rename.
Feature work built on an unvalidated core is inventory risk, per BUILD_PLAN
§6. Begin only after Stage 1's Keystone confirms the walking skeleton.
**Owner:** TBD.

## 11. Stage 2 — authorized third-party E2E test
**WSJF: contingent on item 3 passing cleanly.** Real draft PR on a
third-party repo, per Yehor's original framing. Only after Stage 1 passes.
**Owner:** Yehor authorizes; Claude executes.

## 12. Regulatory flags — CRA / GDPR classification
**WSJF: low urgency now, high cost if skipped before Phase 10.** Get
Patchward's CRA Annex III classification and a lightweight GDPR
DPIA/TTL policy on `installations_db.py` confirmed by someone qualified
before any paid Marketplace listing — not after. See BUILD_PLAN §5 for the
confirmed mechanics (24h/72h/14-day CRA reporting timeline, binding
2026-09-11) and what's explicitly NOT yet confirmed (Patchward's own
classification).
**Owner:** Yehor (external legal input required — not something the agent
can resolve).

---

## Deferred, not forgotten
- ClinInsight/Databutton LinkedIn DM replies — unconfirmed since
  2026-07-10, no tool access to check, answer directly with Yehor.
- Two pre-existing housekeeping items, low urgency: `tests/fixture_repo`
  shows as a dirty git submodule; `.dockerignore` is untracked.
- Sandbox git lock quirk (watch-only, no action needed unless it starts
  blocking something): `.git/index.lock` (Session 012) and
  `.git/objects/maintenance.lock` (Session 013) have both appeared and
  self-resolved without intervention — same root cause both times
  ("unable to unlink ... Operation not permitted" — a mount permission
  boundary between the agent sandbox and the real filesystem, not a real
  git corruption). WSJF: near-zero cost of delay, undefined job size, no
  actual fix to build. If a future session finds a lock file that *does*
  block a real git command, the fix is `Remove-Item <path> -Force` on
  Yehor's own machine — same pattern as Session 012, not worth a design
  discussion.
