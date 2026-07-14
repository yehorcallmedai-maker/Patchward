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

## 3b. `GITHUB_TOKEN` cannot create PRs (CLOSED 2026-07-14 — token permission fixed, no code change)
Branches push successfully; `POST /pulls` returned 403 three times in the
Stage-1 run. Classic signature of a token with contents-write but not
pull-request-write permission.

**Root cause confirmed:** the `GITHUB_TOKEN` is a fine-grained PAT
(`github_pat_...`, 93 chars) named "RepoMend", scoped to
`yehorcallmedai-maker/repomend-fixture`. `GET /user` returned 200 (token
live, not expired/revoked). Its Repository permissions had **Contents:
Read and write** and **Metadata: Read-only**, but no **Pull requests**
permission at all — verified visually at
`github.com/settings/tokens?type=beta`, screenshot inspected directly
(not self-reported).

**Fix:** Yehor added **Pull requests: Read and write** to the existing
token via the GitHub UI (Edit → Add permissions → Update). No token
regeneration needed — editing permissions in place does not change the
token string, so `.env` required no change.

**Verified:** a live `POST /repos/.../pulls` call with `head=main,
base=main` (deliberately no diff, to avoid creating a real PR) returned
`422 "No commits between main and main"` — the correct validation
failure for a *permitted* request with no content, as opposed to the
`403` a permissions failure would produce. This confirms the token can
now reach PR-creation logic. Full end-to-end confirmation (an actual fix
branch producing a real PR) is deferred to item 18 (Stage 2 E2E test),
which this item was blocking.

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

## 3d. Investigate "requires login" invalid branch name (crash CLOSED 2026-07-14; upstream root cause still unconfirmed)
One finding (semgrep subprocess-shell-true) produced a branch name
containing the literal text "requires login", an invalid git ref
(contains a space), crashing `git worktree add`.

**Root cause still unconfirmed** — traced as far as `sarif.py`'s SARIF
normalization reading semgrep's `partialFingerprints`/`fingerprints`
fields verbatim into `finding_id` (`cli.py`/`pipeline.py`), but couldn't
reproduce the actual semgrep behavior without live network access to
the `p/python` registry pack. The original hypothesis (a login-gated
registry request's message leaking into the fingerprint) remains
plausible but unverified.

**The crash itself is fixed regardless of that root cause.** Neither
`cli.py` nor `pipeline.py` validated that `finding_id` (built from
scanner-provided fingerprint/rule_id text) was safe to embed in a git
branch name before calling `git worktree add`. Added
`sanitize_branch_component()` to `worktree_common.py` (this project's
designated single source of truth for shared git primitives, per its
own docstring) — strips/replaces characters git-check-ref-format
forbids (space, `~^:?*[]\`), strips leading/trailing `.`/`-`, collapses
`..` sequences, caps length, and falls back to a safe placeholder if
sanitization would produce an empty string (callers always append a
uuid suffix after, so the fallback only needs to be non-empty). Wired
into both `cli.py`'s and `pipeline.py`'s `finding_id` construction.
8 new unit tests in `test_worktree.py` (`TestSanitizeBranchComponent`
section), including a direct regression test reproducing the exact
"requires login" string. Full suite re-verified by Yehor: 439 passed,
2 skipped, 90.30% coverage, 0 failures.

**Also found and fixed along the way:** `test_config.py`'s
`test_toml_example_parses_cleanly` had to be updated — its own design
prepended a second `[patchward]` block on the (correct) assumption
that the example file had none, which was true before BACKLOG 6a's fix
landed. Against the now-fixed example (which correctly has its own
`[patchward]` section), that produced a duplicate-TOML-table error.
This was the test being stale relative to 6a's fix, not a new defect —
updated to substitute the placeholder `repo_path` value instead of
injecting a second section. Worth noting: this test's original
docstring asserted the missing `[patchward]` section was "intentional
— users set repo_path via CLI flag or scan command," which directly
contradicted this project's own BACKLOG 6a/STATE.md finding that it
was a real, harmful defect. Caught here because running the full suite
after a fix is exactly how a stale test's wrong assumption surfaces.

**Owner:** Claude (agent) implemented and verified via Yehor's full
suite run; root-cause investigation of the semgrep-side anomaly itself
remains TBD if it recurs.

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

## 6. `docs/architecture/patchward-webhook-billing-design.md` decision (CLOSED 2026-07-14 — scrubbed, not recreated)
**Decision: scrub, don't recreate.** ADR-028 and ADR-030 (the two
decisions this phantom file would have covered — FastAPI/Uvicorn/PyJWT
webhook stack, and the GitHub App + Marketplace billing model) each
explicitly state they were "reconstructed... no separate design doc
found in the repo" — meaning the ADRs already are the complete,
canonical record of the facts this file would have contained. Writing
a new `docs/architecture/` file with the same information would create
a second source of truth for the same decisions, with no mechanism to
keep them in sync if either is amended later — exactly the kind of
drift this project's ADR-immutability convention and the State
Reconstruction Audit exist to prevent. Recreating the doc would also
just be citation-satisfying theater: it produces no new information,
only a second copy of what ADR-028/029/030 already say.

**Done:** all three KS-TRACE comments citing the dead path
(`installations_db.py` L1-4, `github_app_auth.py` L9-10, `fly.toml`
L2) rewritten to point at the correct ADR in
`memory/architectural_decisions.md` instead. Note on `fly.toml`
specifically: ADR-029 already documents that `flyctl deploy`
regenerates this file and strips hand-written comments unless manually
restored — this fix may not be durable across the next deploy, same
known fragility as the rest of that file's comments, not a new risk
introduced here.

**Owner:** Claude (agent) decided and implemented, pending Yehor's
review/commit like everything else this session.

## 7. `project_open_tasks.md` reconciliation (CLOSED 2026-07-14 — folded and archived)
**Decision: fold + archive**, not keep maintaining separately.
Rationale: the file is ~95% a fully-signed-off historical record
(Phases 0-7, all `[x]`), ends "PROJECT COMPLETE — RepoMend v0.1.0", and
points at `D:\Dev\Projects\RepoMend` — a directory that no longer
exists post-rename. `BACKLOG.md` has already functioned as this
project's sole active task tracker all session; maintaining two
parallel tracking files with no clear boundary between them is exactly
the dual-source-of-truth risk the State Reconstruction Audit exists to
eliminate.

**Done:** archive banner added to the top of `project_open_tasks.md`
marking it historical, pointing to `BACKLOG.md` as the active tracker.
Of its unchecked items: `D-P5-01` (confirm end-to-end PR creation with
a working `GITHUB_TOKEN`) is already substantively covered by items 3b
and 18 below — not duplicated. `KL-P6-01`, the `conftest.py`
`load_dotenv()` call, and two forward-looking Phase 6/7 placeholder
bullets were all confirmed already implemented elsewhere in that same
file (checkboxes just never flipped) — no action needed. Two items had
no equivalent anywhere in current `BACKLOG.md` and are folded forward
as 7a/7b below, explicitly flagged as pre-pivot ideas rather than
freshly-scoped priorities.
**Owner:** Claude (agent) decided and executed; Yehor reviews per usual.

## 7a. Structured PR template (folded from `project_open_tasks.md` KS-P5-04)
**WSJF: unscored — relevance not reconfirmed.** Pre-rename RepoMend-era
idea (2026-06-22): PR body should carry intent, diff summary, risk
class, and evidence/test-log links — five gates per PR. Never
implemented; not superseded by anything found in the current codebase
during this session's reading of `pr_publisher.py`. Whether this still
matters given the product's pivot toward a GitHub App/Marketplace model
(ADR-030) rather than the original CLI-first roadmap is an open
question — flagged here rather than silently dropped, not asserted as
still a priority. **Owner:** Yehor to decide if/when to prioritize.

## 7b. Risk-class escalation routing (folded from `project_open_tasks.md` KS-P5-05)
**WSJF: unscored — relevance not reconfirmed.** Same provenance and
same caveat as 7a: pre-rename idea (low/medium/high risk-class routing
for fixes), never implemented, not found superseded elsewhere, relevance
to the current product direction unconfirmed. **Owner:** Yehor to decide
if/when to prioritize.

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
