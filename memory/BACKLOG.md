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

## 3. Stage 1 — E2E pipeline test against an owned repo
**WSJF: highest** (risk-reduction, small job size, the entire product
thesis is unproven end-to-end since the rename). Run scan→fix→verify→PR
against a repo Yehor owns (fixture repo or a controlled fork). Zero
third-party exposure, bounded API-credit cost. If the GitHub App is
installed on that repo too, this single test also partially validates the
webhook trigger path.
**Owner:** Claude (agent, with Yehor authorizing the run and any real PR).
**Precondition:** confirm current test suite passes first (see item 4) —
don't validate the pipeline against a codebase whose own test baseline is
unknown.
**Gate:** falsifiable either way — a Stage 1 failure is the cheapest place
to find the biggest problem.

## 4. Re-verify test suite on current `main`
**WSJF: high, trivially small, blocks item 3.** `uv run pytest --cov` on
Windows. The "371 passed / 89%" figure is pre-rename and must not be
trusted as current. Promote the real number into `memory/STATE.md` once run.
**Owner:** Yehor (Windows-only per RULE-4).

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
