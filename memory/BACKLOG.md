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

## 3a. Verifier gate gap — broken fix passed all 3 gates (CLOSED 2026-07-14, commit `b2559a5`)
**WSJF: highest — this blocks everything downstream.** Stage-1 E2E
(below) found a Fix-Gen output that deletes a needed import while the
code that uses it is untouched — objectively broken (`NameError` at
runtime) — and the Verifier marked it `VERIFIED` with all 3 gates
passing. Full writeup: `docs/keystones/stage1_e2e_test_2026-07-13.md` §2.

**Decision (2026-07-14):** direct code inspection of `verifier.py`
(not just the Stage-1 report's summary) showed the real mechanism is
Gate 2, not Gate 1: `_out_of_bounds_lines` unconditionally exempted any
removed import-statement line, whether inside the nominal vuln range
(bandit B404's flagged line *is* the import statement itself, so this is
where the actual defect lived) or outside it — with zero check for
whether the removed name was still referenced anywhere else in the
post-edit file. Implemented: `_removed_import_still_referenced()`
(AST-based, not regex/substring — parses the removed import and the
post-edit file, checks `Name`/`Attribute` references; conservative on
any ambiguity: unparseable line, star import, or unparseable post-edit
file all count as "still referenced," i.e. rejected). Gate 2 now only
permits an import removal — in-range or out-of-range — when this
returns False.

**Why Gate 2 and not the other two candidates:** Gate 1 rescanning the
same rule_id can't distinguish "vulnerability fixed" from "the rule's
own trigger condition was deleted" for a rule like B404 whose entire
definition is "this import exists" — broadening Gate 1 would need a
bigger, riskier redesign (rescanning beyond the single rule_id). Gate 3
(require coverage of the changed function) was deferred: real third-party
Stage 2 targets will have uneven test coverage, and making it a hard
gate risks blocking legitimate fixes to exactly the neglected code that
most needs patching — better as a future confidence signal than a
blocking gate. A Fix-Gen prompt constraint alone was rejected as the
primary fix because it's advisory, not enforced — an LLM can still
ignore it; the Gate 2 static check is enforced regardless of what
Fix-Gen produces.

**Status: CLOSED.** Code change + regression test (reproducing the exact
Stage-1 shape) + 8 new unit tests for the helper first verified in an
isolated sandbox venv (36/36 `test_verifier.py` tests pass), then
re-verified by Yehor against the real `.venv` on his own machine: full
suite **431 passed, 2 skipped, 15 deselected, 90.25% coverage** (up
from 90.01% pre-fix; the 10 new tests fully account for the delta, no
regressions elsewhere). Committed `b2559a5` and pushed to `origin/main`
— confirmed via `git ls-remote origin main` matching local HEAD exactly.
See `memory/project_session_log.md` Session 014 entry for the full
walkthrough, including a mid-session PowerShell heredoc/BOM detour
(commit initially landed with a stray UTF-8 BOM character in the
subject line from `Set-Content -Encoding utf8`; fixed via
`git commit --amend` using a base64-encoded, single-line-paste-safe
message after two consecutive heredoc-paste corruptions on this
terminal — worth carrying forward as a standing note, see below).

**Deferred, not forgotten (separate follow-ups, not bundled into this
fix):** excluding purely-informational bandit rules like B404 (whose
only possible "fix" is deleting the thing it flags) from Fix-Gen's
candidate findings at the pipeline level — no existing filter mechanism
was found in `pipeline.py`, so this is a real feature addition, not a
one-liner; broadening Gate 1's rescan; converting Gate 3 to a
confidence signal rather than a blocking gate.

## 3b. `GITHUB_TOKEN` cannot create PRs (NEW, MEDIUM)
Branches push successfully; `POST /pulls` returns 403 three times in the
Stage-1 run. Classic signature of a token with contents-write but not
pull-request-write permission (fine-grained PAT) or an expired/revoked
classic PAT. **Owner:** Yehor — check/regenerate `GITHUB_TOKEN`
permissions. See `docs/keystones/stage1_e2e_test_2026-07-13.md` §3.

## 3c. CLI misreports failed PR creation as success (CLOSED 2026-07-14, commit `190fb01`)
`cli.py` L496-499 printed `[PR] Opened: {url}` unconditionally, without
checking `pr_dict['status']` — a 403/422 failure printed as if it
succeeded, just with a blank URL. Confirmed by direct code read.

**Fix:** now branches on `pr_dict['status']`: `"opened"` → `[PR]
Opened: {url}`; `"already_open"` (idempotent case from
`pr_publisher._create_pr`) → `[PR] Already open: {url}`; anything else
(`"api_error"` or any future unexpected value) → `[PR] Failed to open
(status=...)`, printed to stderr. `cli.py` is excluded from this
project's unit-coverage requirement (`pyproject.toml` `omit` list —
integration-tested only, no `test_cli.py`), so no new unit test was
added; verified by direct code read plus a real `py_compile` on
Yehor's machine.

**Notable this session:** the sandbox's bash mount served a
byte-for-byte stale copy of `cli.py` (file `stat` showed a
2026-07-07 mtime — days before today's edit, and the file was
truncated mid-statement at line 624 of 677) when asked to verify the
edit, producing a false `SyntaxError`. `verifier.py` synced correctly
earlier the same session, so this isn't a universal mount failure —
likely file-specific caching. Resolved by trusting the Read tool
(already an established rule for `git status`/`diff`; this extends it
to plain file reads too) and having Yehor run the real compile check
directly. Worth carrying forward: **don't assume a sandbox-side
compile/test failure on a just-edited file is real without an
independent check on the real machine** — same spirit as the existing
"don't trust a tool's self-report" rule, one layer earlier in the
pipeline.

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

## 6a. Fix `patchward.toml.example` (CLOSED 2026-07-14, pending commit)
**WSJF: medium — real defect in a committed, user-facing artifact, cheap
to fix.** The example config that shipped in ADR-025/Phase 7 had no
`[patchward]` section and no `repo_path` field at all (the single most
critical required field for single-repo mode), plus a nonfunctional
`[anthropic]` section that doesn't match `config.py`'s actual schema
(`anthropic_api_key` comes from the env var, not a toml section). A new
user following this template would hit the exact same hard config-load
failure Session 013 found and fixed in the real `patchward.toml`. Found
2026-07-13 while preparing the Stage-1 E2E test.

**Rewritten 2026-07-14.** Direct read of `config.py` surfaced a third,
previously uncatalogued defect in the same file: the old example
documented `max_out_of_bounds_lines` under `[verifier]`, a field that
does not exist on `VerifierConfig` at all — pydantic's default
`extra='ignore'` behavior means this was always silently dropped, a
phantom option that looked configurable but did nothing. New version:
adds the required `[patchward]` section with `repo_path` front and
center and a clear "REQUIRED, no default" comment; removes the bogus
`[anthropic]` section, replacing it with an in-context comment on
`anthropic_api_key` (env var recommended, toml override documented);
removes `max_out_of_bounds_lines`; adds the previously-undocumented
`[fix_gen]` section (`max_turns`, real schema, has a default but worth
surfacing). Top-level section structure (`[patchward]`, `[github]`,
`[batch]`, `[models]`, `[verifier]`, `[fix_gen]`, `[[repos]]` — none
nested) now matches `config.py`'s actual `load_config()` exactly.

**Verified, not just eyeballed:** copied `config.py` and the new
example into an isolated sandbox venv, filled in only `repo_path` (the
one edit the file's own instructions ask a new user to make), and ran
the real `load_config()` against it end to end — every field resolved
correctly, including the `[[repos]]` single-repo fallback list, no
`ValidationError`. **Owner:** Claude (agent) rewrote; Yehor to review
before commit.

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
