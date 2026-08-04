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

## 5. Phase 9 Exposure Gate — FULLY CLOSED, committed and pushed through `3d1ec08`
**WSJF: high** (security-adjacent, small-medium job size, already-live
surface). Per Session 020's verification, HMAC signature validation is
already done — do not re-implement it. All four original sub-parts
implemented, tested, and confirmed on Yehor's real Python 3.14.4 venv
(`uv run pytest --cov` → 468 passed, 2 skipped, 15 deselected, 90.46%
coverage, threshold 80% reached, no regressions). **Committed and
pushed** — feature commit `0c6a742` (webhook.py + both test files),
docs commit `793a1d0` (this file + session log + strategy memory).
**Session 021 correction: this is not the end of the chain.** Two more
commits landed after `793a1d0`, both real security work, not docs:
`4b6a023` (3 defense-in-depth spy tests proving the post-read body-size
check actually rejects a missing/lying `Content-Length`) and `3d1ec08`
("harden(webhook): range-validate rate-limit/body-size env parsers" —
moves the rate limiter to run *after* `_verify_signature` so an
unauthenticated flood can't consume the rate-limit budget, and closes a
guard hole found in adversarial review of that reorder: the env-parser
helpers now reject non-finite (`inf`/`nan`/`-inf`) and out-of-range
(`<1`, `<=0`) overrides via `math.isfinite()` instead of a bare `except
ValueError`, with a negative-control test
(`test_infinite_window_env_still_expires_limiter_recovers`) proving the
guard actually discriminates guarded vs. unguarded behavior, not just
suppressing a 500). `origin/main` is now `3d1ec086972445373ac6a1eb7ac8abed238559a5`,
confirmed 2026-07-21 via `git ls-remote`, a fresh `git clone`, and a
direct `raw.githubusercontent.com` fetch + sha256 compare of
`webhook.py` against that clone (identical) — three independent methods,
none touching the local `D:\` mount. Test-count cross-check: 468 + 3
(`4b6a023`) + 12 (`3d1ec08`) = 483, matching the reported real-machine
figure exactly. **Note on citing hashes at all** (H2): re-run
`git ls-remote` fresh in any future session rather than trusting the
number above.
- Rate limiting / request body size limits on `/webhooks/github` —
  **IMPLEMENTED 2026-07-16 (Session 020), VERIFIED on Yehor's real
  machine same day.** Checked `fly.toml` first: single Fly
  machine, scale-to-zero, no shared store — same v0 constraints ADR-030
  already accepts elsewhere, so an in-memory approach is consistent
  scope, not a corner cut. Body-size default (25 MB) matches GitHub's
  own documented hard cap on webhook payloads (confirmed via
  `WebSearch`), so it never rejects a real delivery while still
  bounding worst-case memory per request; checked via `Content-Length`
  before the body is read, with a second post-read length check as
  defense-in-depth for a missing/lying header (chunked encoding) —
  documented as a real residual gap, not oversold as fully solved (true
  protection there needs a streaming ASGI-level limit, out of scope for
  this v0 pass). Rate limiting is a plain in-process sliding-window
  counter (60 req/60s default, both tunable via
  `PATCHWARD_WEBHOOK_RATE_LIMIT_MAX` /
  `PATCHWARD_WEBHOOK_RATE_LIMIT_WINDOW_SECONDS` env vars) — bounds a
  runaway/replay flood, not a per-installation fairness mechanism.
  6 new tests in `test_webhook.py` (threshold, window-slide,
  oversized-rejected, within-limit-still-works), plus an autouse
  fixture resetting the limiter's module-level state between tests.
  Sandbox pre-check (Python 3.10, ad hoc `pip install`) predicted 467
  passed (461 + 6); a real sandbox tooling bug was hit and fixed
  mid-session, not routed around: the bash mount served a stale/truncated
  copy of both `webhook.py` and `test_webhook.py` after editing (same
  documented class of bug as Sessions 016/017's `cli.py`/
  `test_orchestrator.py` truncations) — fixed by re-reading each file in
  full via the `Read` tool (trusted per this project's own rule) and
  rewriting it byte-for-byte through a bash heredoc to force the
  sandbox's view back in sync, verified via `ast.parse` before re-running
  tests. **Real confirmation, Yehor's own machine, same day (Python
  3.14.4):** `uv run pytest --cov` → 468 passed (461 baseline + 6 rate-
  limit/body-size tests + 1 pending_change test, combined with the other
  sub-items below), 2 skipped, 15 deselected, **90.46% coverage**,
  threshold 80% reached — exact match to every sandbox prediction, no
  regressions. Diff staged only, not yet committed.
- `X-GitHub-Delivery` header in structured logs — **IMPLEMENTED
  2026-07-16 (Session 020), VERIFIED on Yehor's real machine same day.**
  `webhook.py`'s `github_webhook` now takes an `x_github_delivery` header
  param and includes `delivery=%s` in the single `logger.info(...)` line
  at the top of the handler — since that line runs before the event-type
  dispatch, this covers every path (ping, installation,
  installation_repositories, marketplace_purchase, push, and the
  unrecognized/"ignored" fallback) with one change, not six. Missing
  header logs an empty string, never raises. Two new tests added to
  `tests/test_webhook.py` (`test_delivery_id_logged_for_every_handled_delivery`
  using `caplog.at_level(...)`, matching the existing convention in
  `test_pr_publisher.py`; `test_missing_delivery_header_does_not_crash`).
  Sandbox pre-check (Python 3.10, ad hoc pip install) predicted 463
  passed. **Real confirmation, Yehor's own machine, same day (Python
  3.14.4):** `uv run pytest --cov` → 468 passed (combined total across
  all of item 5's sub-items), 2 skipped, 15 deselected, 90.46% coverage
  — `webhook.py` correctly excluded from the coverage measurement itself
  (`pyproject.toml`'s `[tool.coverage.run].omit` list), consistent with
  the coverage % staying flat despite the new code. Changes staged only,
  not yet committed — diff to be reviewed line-by-line per BUILD_PLAN
  §2's security-boundary rule before Yehor's own commit.
- `pip-audit` run scoped to the `webhook` optional-dependency group —
  **CLOSED 2026-07-16 (Session 020).** Agent's sandbox attempt was
  blocked cleanly (no internet egress to download a matching Python
  3.12+ interpreter for `uv export`; details preserved in
  `project_session_log.md`'s Session 020 entry) — command handed to
  Yehor rather than a guessed verdict. **Yehor ran it for real, on his
  own machine, from the repo root:**
  ```
  uv export --no-emit-project --extra webhook > webhook-reqs.txt
  pip-audit -r webhook-reqs.txt --no-deps
  ```
  (`--no-deps` needed — without it, `pip-audit` tries to build its own
  resolution venv and re-resolve the whole tree, which is slow enough to
  look hung; `uv export` already emits every pinned transitive dependency
  from the lockfile, so there's nothing left to resolve.) **Result: "No
  known vulnerabilities found"** across all 77 resolved packages in the
  `webhook` extra (`fastapi==0.139.0`, `uvicorn==0.51.0`,
  `pyjwt==2.13.0`, `httpx==0.28.1`, and their full transitive tree) —
  Tier 0, Yehor's own terminal output. Re-run periodically as dependency
  versions drift; not a one-time clearance.
- Confirm `is_entitled()` correctly treats `cancelled`/`pending_change`
  Marketplace status as non-entitled — **CLOSED 2026-07-16 (Session
  020). Behavior confirmed correct as-is; Yehor confirmed the reversal
  above after independently checking GitHub's Marketplace docs
  himself** (cancellations/downgrades only take effect at the start of
  the next billing cycle; the current plan stays active until then).
  The session's own earlier "confirmed bug" framing was wrong — kept
  visible in this file rather than silently deleted, per this project's
  correction convention. **No production code changed.** Added
  `test_is_entitled_true_while_pending_change_not_yet_effective` to
  `tests/test_installations_db.py`, same style as the existing
  `is_entitled` tests, asserting `is_entitled()` stays `True` for a
  `pending_change` status and documenting why in its docstring — turns
  today's implicit behavior into an explicit, tested contract instead of
  an unexamined accident. Sandbox pre-check predicted 468 passed.
  **Real confirmation, Yehor's own machine, same day (Python 3.14.4):**
  `uv run pytest --cov` → **468 passed, 2 skipped, 15 deselected, 90.46%
  coverage**, threshold 80% reached, no regressions — exact match,
  `tests\test_installations_db.py` included in the run (11 tests in that
  file, matching). **All four of item 5's sub-parts are now real-machine
  confirmed; only Yehor's commit remains.** Still open, not itself
  resolved this session:
  whether `pending_change_cancelled` exists as a distinct action and
  needs the same reasoning applied — low priority, noted for whenever
  this area is revisited.
- **Session 021 (2026-07-21) addendum — item genuinely, fully closed.**
  `4b6a023` and `3d1ec08` (see header above) landed after this section
  was last edited, closing a real guard hole (non-finite/out-of-range env
  overrides) found in adversarial review of the post-HMAC rate-limiter
  reorder. 12 new tests in `3d1ec08` alone, including a negative-control
  test proving the fix actually changes behavior rather than just
  silencing an exception. Nothing left agent-actionable on this item;
  the only open sub-thread is `pending_change_cancelled` above (low
  priority, whenever revisited).
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

## 7a. Structured PR template (CLOSED 2026-07-14 — already substantively implemented)
**Correction to this item's own prior entry:** the 2026-07-14 note above
said direct reading of `pr_publisher.py` found this "never implemented."
A closer read this pass (full read of `_build_pr_body()`, not just a
grep) found that's wrong — `pr_publisher.py` already renders a
five-section PR body template (Finding / Fix / Verification Evidence /
Diff / Test Output, `_build_pr_body()` L228-286) per ADR-018/ADR-019 and
constraints C-P5-04 through C-P5-12. This satisfies the pre-rename ask
(intent, diff summary, evidence/test-log links) in substance, just not
labeled "risk class" as its own section. **Not a real gap — folded into
7b below**, since the one missing piece (`risk_class`) is the same data
gap that item already covers. No separate action needed.

## 7b. Surface `risk_class` in the PR body (CLOSED 2026-07-14, commit `53cd052`)
**Rescoped, then closed, same session.** Original folded item asked for
"risk-class escalation routing." Investigation found the classification
itself already existed (`fix_gen.py`'s `_risk_class_for_severity()`,
AC-P3-08 — `HIGH`/`MEDIUM`/`LOW` from SARIF severity, stored on
`FixResult.risk_class`), but was never displayed anywhere a human
reviewer would see it. Rescoped from vague "escalation routing" to the
concrete gap: display it.

**Done:** `pr_publisher.py`'s `_build_pr_body()` now includes a
`**Risk class:**` line in the Finding section (falls back to `unknown`
if unset). Two new tests in `test_pr_publisher.py`
(`test_build_pr_body_shows_risk_class`,
`test_build_pr_body_risk_class_falls_back_to_unknown`) cover both cases.
Full suite re-verified by Yehor: **441 passed, 2 skipped, 90.31%
coverage** (up from 439/90.30% — the 2 new tests fully account for the
delta, no regressions). Sandbox `py_compile` produced a false
`SyntaxError` on this just-edited file (same stale-mount pattern as
`cli.py` earlier this session) — resolved by trusting the Read tool's
view, confirmed correct, and verifying compile+tests on Yehor's real
machine instead.

**Deliberately not done:** no behavior gates on `risk_class` yet (e.g.,
blocking or extra review for HIGH-risk fixes) — that's a separate
product decision, not scheduled, Yehor's call if/when it matters.

## 7c. `.dockerignore` untracked (CORRECTED 2026-07-14 — claim was false, already tracked)
**Correction, same day:** this entry originally claimed `.dockerignore`
was untracked and decided to track it. That check was incomplete — it
confirmed the file's content and that `.gitignore` doesn't exclude it,
but never actually ran `git ls-files` to check whether it was tracked,
which is the one check that would have caught the real answer.
`git ls-files --error-unmatch .dockerignore` confirms it **is** tracked,
committed in `8b601e9` ("Stage-1 E2E test report + BACKLOG/STATE
updates, lock webhook extras") and unmodified since. There was no real
gap here — the `git add .dockerignore` run as part of this pass's
commit batch staged nothing, exactly as it should for an already-tracked,
unmodified file. Left visible rather than silently fixed, per this
project's established correction convention (see ADR-029's amendment,
BACKLOG item 2). **No action was actually needed.**

## 7d. `tests/fixture_repo` dirty submodule (2026-07-14 — decision: commit the one-liner, pending fresh Pass 2)
STATE.md's 2026-07-13 finding: the submodule's only local change is a
one-line, non-functional docstring edit ("testing RepoMend" → "testing
patchward"), confirmed harmless (worktree-based scans read from `HEAD`,
not the dirty working copy). That finding is a year — sorry, a session —
old and wasn't re-verified fresh this pass (sandbox `git diff` on this
mount is not trustworthy per standing rule). **Decision: commit it**
rather than leave it permanently dirty (a permanently-dirty submodule
makes every future `git status` check harder to audit — "is this the
known-harmless diff, or something new?" shouldn't require re-deriving
the answer each session) — **conditional on Yehor's fresh `git status`/
`git diff` inside `tests/fixture_repo` matching the prior claim exactly**
before committing. See commit instructions in `project_session_log.md`'s
Session 014 addendum 3.

## 8. callmed-landing rename — CLOSED 2026-07-22 (Session 022)
**Fully closed this session, Tier-0 verified.** `C:\Dev\Projects` connected
mid-session, making both `callmed-landing` and `Autonomous-Core` directly
reachable for the first time. Fresh direct read (not the prior Tier-2
Autonomous-Core secondhand record) confirmed: the `#381→#383` citation fix
and "9 PRs"→"11 PRs" proof-count update were already live in `index.html`
line 174 (upgraded Tier 2→Tier 0). The RepoMend→Patchward swap itself:
**45 real word-occurrences** across `index.html`(24)/`privacy.html`(7)/
`security.html`(14) — not 34 as previously estimated; that figure was a
`grep -c` line-count, not a word-count (several lines carry 2-3 instances).
Fixed via case-sensitive two-pass swap (`RepoMend`→`Patchward`,
`repomend`→`patchward`), verified 45→0 via `grep -o -i`.
**Investigation also caught 3 occurrences that weren't cosmetic** — the
page was giving visitors actively wrong instructions, not just an old
brand name: (a) index.html's CLI sample (`uv tool install repomend` /
`repomend fix --repo .`) — real entry point is `patchward`
(`pyproject.toml` `[project.scripts]`), fixed automatically by the plain
swap and cross-checked against `src/patchward/cli.py`'s real `fix --repo`
option; (b) security.html's branch-naming line (`repomend/fix-{id}`) —
real pattern per `src/patchward/fix_worktree.py`'s own docstring is
`patchward/fix-<finding-id>`, required a manual fix beyond the naive
swap (HTML-entity-encoded as `&lt;finding-id&gt;` so it renders as text,
not markup); (c) security.html's PyPI-namespace claim (`repomend`
namespace) — now correctly `patchward`, fixed by the plain swap and
Tier-0 confirmed via item 9's fresh publish this same session. Corrected
files delivered to Yehor and written to `C:\Dev\Projects\callmed-landing\`
**uncommitted** (not pushed, live site untouched) for his own `git diff`
review and commit — per standing process, no agent commits to a repo
without Yehor's own review pass first. **New backlog candidate surfaced,
not acted on:** the real Patchward codebase still has ~59 internal
"repomend" references across 15 files (e.g. `RepomendConfig` class in
`config.py`/`webhook.py`) — see item 16.
**Owner:** Yehor, for the `git diff` review + commit only; the actual
content work is done.

## 9. PyPI Trusted Publisher — CLOSED 2026-07-22 (Session 022), Tier-0 end-to-end
**Fully closed this session — the real publish happened and was verified
two independent ways, not inferred.** PyPI's pending-publisher UI showed
**Environment name: `(Any)`** (parenthesized italic — PyPI's own
placeholder for "no restriction," not a literal string "Any" someone
typed), which matches `publish.yml`'s `environment: pypi` claim without
issue — the risk this item flagged does not materialize. Yehor then
triggered `workflow_dispatch` on `main` @ `07f97d3` (the session's
verified HEAD) via GitHub's UI. Result, confirmed via two independent
methods: (1) the Actions run itself — `build` (10s) → `publish` (21s),
both green, 47s total; (2) the actual PyPI release page,
`pypi.org/project/patchward/0.1.0/` — live, uploaded 2026-07-22, both
`patchward-0.1.0.tar.gz` and `patchward-0.1.0-py3-none-any.whl` present,
explicitly stating **"uploaded using Trusted Publishing via GitHub
Actions from the repository `yehorcallmedai-maker/Patchward`"** — the
OIDC identity chain proven working end-to-end, not just "environment
field looks right." Minor non-blocking oddity: the bare
`pypi.org/project/patchward` (no version) 404'd twice via this session's
fetch tool while the version-pinned URL loaded fine — read as a
caching/propagation quirk on the fetch side, not a real problem; Yehor
can confirm with his own browser at his convenience. `patchward` v0.1.0
is now a real, live, public PyPI package. **Owner:** none — closed.

## 10. "Mirror Pass Tier 2" — REMOVED 2026-07-15 (Session 018, cross-project research) — never belonged in this file
**This was a category error carried in from `BUILD_PLAN_2026-07-10.md`,
not a Patchward feature at all.** Confirmed via `Autonomous-Core`
(`docs/architecture/competitive_analysis.md`,
`memory/symbiote-recurring-income-research-and-buildplan.md`): "Mirror
Pass" (also called Symbiote) is a completely separate product Yehor
runs — a $1,500 flat-fee PEP 484 type-annotation consulting service for
Python codebases, marketed on callmedai.com. "Tier 2" is a pricing/scope
upsell for that service (service layer + entities layer, $3,000–$4,000),
tracked as its own numbered backlog item **inside Autonomous-Core's own
tracker** (a different "#12" than this file's item 12 — pure numbering
coincidence, confirmed by content, not by number). It is a sales/outreach
task (find ICP-matched prospects per `competitive_analysis.md` §5c),
not an engineering task, and has zero code surface in this repo.
Removed here rather than silently reassigned, per this project's own
correction convention — same treatment as the ClinInsight/Databutton
item removed in Session 014. If Yehor wants to track it, it belongs in
Autonomous-Core's tracker, where it already lives.

## 11. Stage 2 — authorized third-party E2E test (COMPLETE 2026-07-14 — PR #1 on ssh-audit)
**Target selection:** `yehorcallmedai-maker/ssh-audit` (public fork, 1.4 MB,
real Python security tool) — chosen over `checkdmarc` and explicitly over
`django`/`langchain`/`twisted` (too large/complex for a first controlled
run) and over Yehor's private repos (real personal/business assets,
unnecessary risk vs. a disposable public fork). "Third-party" satisfied
via real, unplanted third-party *code* (someone else wrote ssh-audit)
with zero external-consent complexity (Yehor owns the fork outright).

**Dry-run scan:** 703 raw findings, 698 in test files (correctly excluded
by `patchward fix`'s test-path pre-filter, `cli.py` L317-337). 5
actionable, all in `ssh_socket.py`/`dheat.py`. Scanner-model triage
correctly assessed 4/5 as by-design (bind-to-all-interfaces ×2 + B104
duplicate — intentional for an SSH-auditing server; B311 — weak PRNG in
a DHEat attack *simulation*, not production crypto) and 1/5 as a clean,
real fix candidate (B110 — bare `except Exception: pass`).

**`patchward fix` result:** 4/5 correctly **not** force-fixed — Fix-Gen
exhausted its turn budget without calling `submit_fix` on the by-design
findings rather than fabricating unnecessary changes (a real, valuable
outcome: it didn't file bad PRs on non-issues, though "runs out of
turns" vs. an explicit "decline, not a real issue" path is worth
improving later — see new item 13 below). 1/5 **verified and shipped**:
`bandit.B110` fix (`except Exception:` → `except OSError:` in
`_close_socket()`) passed Gate 1 (pass), Gate 2 (pass), Gate 3 (**skip**
— no test suite detected in the fix worktree, expected and correct per
`verifier.py`'s own doc: `ssh-audit`'s test dependencies aren't installed
in Patchward's `.venv`, this is documented as SKIP-not-FAIL specifically
for this external-repo scenario, not a red flag).

**Verified independently, not from CLI self-report** (per BACKLOG 3c's
own history): `gh pr view` confirmed PR #1 is real, `state: OPEN`,
**`isDraft: true`** (ADR-019 satisfied), `baseRefName: master` (correct —
`ssh-audit` predates GitHub's "main" default, caught via `gh repo view`'s
`defaultBranchRef` before configuring). `gh pr diff` confirmed the actual
diff matches Fix-Gen's self-reported `diff_summary` exactly — 1 file,
+1/-1.

**New evidence for BACKLOG 3d's still-unconfirmed root cause:** the exact
anomalous `"requires login"` string recurred in `finding_id`/branch-name
construction for 2 of the 4 declined findings
(`avoid-bind-to-all-interfaces`) — a *different* semgrep rule than Stage
1's occurrence (`subprocess-shell-true`), in a *different* repo. Confirmed
via grep that this string is not hardcoded anywhere in Patchward's own
code (`worktree_common.py`'s only match is the comment describing the
phenomenon, not producing it) — it's genuinely scanner-sourced. Recurring
across different rules and repos shifts the working theory from "one
rule's message leaking into its own fingerprint" toward a more systemic
cause (e.g., a shared semgrep registry/auth response bleeding into
fingerprint generation broadly). The crash itself remains fixed
regardless (`sanitize_branch_component()` handled both occurrences
cleanly, no crash this run) — root cause still not conclusively
identified, but narrowed.

**Owner:** Yehor authorized, Claude executed — result reviewed together
with independent verification at each step.

**Post-close-out follow-up (same day):** PR #1 sat as a draft after the
Stage 2 run — per ADR-019/ADR-003 (always draft, never auto-merge),
merging is a deliberate human action, not something the pipeline does.
Re-verified the diff was still unchanged via a third, independent method
(`patch-diff.githubusercontent.com`, distinct from both `gh pr view` and
the GitHub API) before recommending merge — Yehor's own repo, no
external stakeholder, fix confirmed correct, no reason to leave it open
indefinitely. `gh pr merge` initially failed ("Pull Request is still a
draft" — expected, GitHub blocks merging drafts directly); resolved via
`gh pr ready` then `gh pr merge --squash --delete-branch`. Squash-merged,
branch deleted. Stage 2's full loop (scan → fix → verify → push → PR →
human review → merge) is now complete end to end, not just up through
PR creation.

**Unrelated housekeeping caught in the same pass:** a `future-agi-contribution/`
directory was found nested inside Patchward's folder tree (untracked by
this repo's git throughout the session — correctly isolated, never
staged). Verified via direct file read: it's a genuine, separate,
actively-managed project (an OSS contribution effort to
`future-agi/future-agi`, with its own `.strategy/STRATEGY.md` memory and
session history) that happened to be created inside Patchward's
directory rather than its own. Not a Patchward concern content-wise —
duplicating analysis of it here would risk exactly the
dual-source-of-truth problem this project's own conventions exist to
avoid (same pattern as `project_open_tasks.md` vs `BACKLOG.md`).
Relocated to `D:\Dev\Projects\future-agi-contribution` (verified via
`Test-Path`: gone from Patchward's tree, present with its memory intact
at the new location) — no other action taken, that project continues in
its own session.

**Correction, same day:** the relocation above was wrong and has been
reversed. The Future AGI session was still actively running, independent
of this one, with its own memory of the original nested path. After this
session moved the directory out, that other session found nothing at
its remembered path, treated it as data loss, and rebuilt its memory
file from scratch back at the original nested location — then kept
working there, producing a more complete, more current record
(including a `SESSION_CLOSE_2026-07-14.md` this pass's copy never saw).
Discovered when the directory reappeared in `git status` after the
move; confirmed via `Get-ChildItem` on both paths (nested copy: newer,
larger, includes the session-close file; relocated copy: frozen at the
pre-continuation state) and a direct read of the nested `STRATEGY.md`
confirming it matches the more recent, more detailed record. **Lesson:**
relocating a directory that might be a live dependency of a different,
concurrently-running session risks exactly this kind of silent fork —
should have flagged the possibility rather than treating the move as
purely a Patchward-side hygiene call. The stale duplicate at
`D:\Dev\Projects\future-agi-contribution` is being deleted; the nested
copy inside Patchward's tree is being kept and remains untracked by
this repo's git, as it was throughout.

## 13. Fix-Gen lacks an explicit "not a real issue, decline" path (CLOSED 2026-07-15)
**WSJF: low-medium — real gap, not urgent.** Stage 2 showed Fix-Gen
correctly avoiding bad fixes on 4 by-design findings, but the *mechanism*
was running out of `max_turns` without calling `submit_fix`, not an
explicit "I assessed this and it's not a real issue" decision.
Functionally safe (no bad fix shipped either way) but wastes the full
turn budget on every by-design finding and produces an ambiguous
`[SKIP]` reason ("max_turns reached") indistinguishable from Fix-Gen
genuinely struggling vs. correctly declining.

**Selected via `/session-strategy-synthesis`, 2026-07-15** — of the three
unscheduled options open at session start (this item, Mirror Pass Tier 2
/ item 10, or a no-op), item 10 was ruled out on its own WSJF terms: grep
across every memory file and `src/` found zero design spec anywhere
beyond its one-line BACKLOG/BUILD_PLAN entry (`Job Size: Large`,
`WSJF: lowest for now`) — its real first step would be a scoping
conversation with Yehor, not code, so it couldn't produce a testable
session outcome today. This item was concrete, scoped, and already had a
named mechanism and a named file, so it was chosen without re-asking.

**Implemented:** new `decline_fix` tool in Fix-Gen's schema (`fix_gen.py`)
— requires `reason` + `confidence`, and the system prompt now instructs
the model to call it (after at least one `read_file`) when a finding is
by-design/false-positive, instead of exhausting `max_turns` silently.
`FixResult` gained `declined: bool` and `decline_reason: str`.
`pipeline.py`'s batch status is now `"declined"` (not the generic
`"fix_failed"`) when `fix_result.declined` is true. `cli.py` prints
`[DECLINED] <reason>` instead of the ambiguous `[SKIP] ...max_turns
reached`, and logs `declined`/`decline_reason` in the run log record.

**Real bug caught and fixed during this same pass, not a separate
follow-up:** the first test run (448 total collected, 2 failed) hit the
*exact same failure class* this codebase already documented once
(2026-07-08, `project_open_tasks.md #25`, preserved verbatim in
`_make_fix_result()`'s own comment in `test_orchestrator.py`): an unset
`MagicMock` attribute auto-vivifies as a truthy, non-JSON-serializable
object. Two test mocks predating the new `declined`/`decline_reason`
fields — `_make_fix_result()` and one inline `MagicMock()` in
`TestRunLogThreaded.test_run_log_record_on_fix_failure` — hit it again.
Production was never affected (the real `FixResult` dataclass always
defaults `declined=False` correctly); only the test mocks needed the new
fields set explicitly. Fixed both. **Worth carrying forward as a
standing heuristic, now proven twice in the same codebase:** any new
field added to `FixResult` (or any dataclass mocked via a bare
`MagicMock()` in this test suite, not `spec=`'d) must be added explicitly
to every existing untyped mock construction site, not assumed safe by
default — grep for the class's mock-builder helpers and any inline
`MagicMock()` construction before considering a dataclass field addition
complete.

**Verified:** Yehor ran the real suite twice on his own machine (`.venv`,
Windows) — first run: 2 failed (the mock gap above), 446 passed; second
run after the fix: **448 passed, 2 skipped, 15 deselected, 90.46%
coverage** (up from 441/90.31% pre-session — the 7 new tests across
`test_fix_gen.py` and `test_async_pipeline.py` fully account for the
delta). Commits: `docs: correct stale SHA/lock claims in
NEXT_SESSION_START.md`, then `feat(fix-gen): add explicit decline_fix
tool path (BACKLOG 13)`.

**Not done, flagged rather than silently skipped:** `cli.py`'s new
`[DECLINED]` echo branch has no dedicated unit test — no `tests/test_cli.py`
file exists in this repo at all (checked via `Glob`, confirmed absent),
so there was no existing harness/convention to extend without building
one from scratch. `pipeline.py` and `fix_gen.py`'s decline logic are
both covered (now closed — see BACKLOG 15a). **`.claude/agents/*.md`
naming — CLOSED 2026-07-15, commit `7effbad`.** Widened during Session
016: all three templates (`scanner.md`, `fix-gen.md`, `verifier.md`),
not just `fix-gen.md`, still said "RepoMend"; grep across `src/`
confirmed zero runtime references to any of them (they're not the live
prompt — the real one is `_FIX_GEN_SYSTEM_PROMPT`, embedded directly in
`fix_gen.py`). The `Edit`/`Write` tools refused all three as a protected
path, so content was generated, base64-encoded, and handed to Yehor as
three `WriteAllText` PowerShell commands to run himself — verified via
the `Read` tool (not blocked) before handoff. All three now say
"Patchward"; `fix-gen.md`'s branch-naming line and its fictional
"ESCALATE signal" description now correctly describe the real
`decline_fix` mechanism (BACKLOG 13) and the real `patchward/fix-<id>`
branch prefix. **Not decided, deliberately left to Yehor:** whether these
three unreferenced files are worth keeping at all, versus deleting
outright — correcting content was the safe, reversible move; deletion is
a call only he should make.

## 12. Regulatory flags — CRA / GDPR classification — BRIEFING PACKET READY, AWAITING COUNSEL ENGAGEMENT (2026-07-24, Session 024)
**WSJF: low urgency now, high cost if skipped before Phase 10.** Get
Patchward's CRA Annex III classification and a lightweight GDPR
DPIA/TTL policy on `installations_db.py` confirmed by someone qualified
before any paid Marketplace listing — not after.

**Session 024 update:** this item is NOT closed — it is still genuinely
blocked on finding and engaging qualified counsel, same as every prior
session. What changed: the previously indivisible "needs counsel" label has
been split into the actual legal determination (not agent-startable) and
the technical briefing packet counsel needs before they can even answer
(fully agent-startable, and the real reason this sat still for 3+ weeks —
nobody had written it). That packet now exists:
`memory/BACKLOG12_counsel_briefing_packet_2026-07-24.md`. It contains,
strictly separated from any legal conclusion: (1) a field-by-field data
inventory of `installations_db.py` read directly from source, including a
confirmed retention gap (see new item 18 below); (2) a product-facts sheet
covering all three real deployment models (CLI/PyPI, Docker sandbox,
Fly-hosted webhook), the commercial model, jurisdiction, and third-party
processors; (3) a corrected data-flow fact, verified against
`fix_gen.py`/`credential_proxy.py` at HEAD `3e63587` — the "only the fix
prompt reaches the Anthropic API, scrubbed of credentials" description is
not accurate as stated (real repository source code is sent via the
Fix-Gen subagent's `read_file` tool results, and `CredentialProxy.scrub()`
is only ever called on CLI/log output in `cli.py`, never on anything
actually sent to Anthropic); (4) a precise question list for counsel
(manufacturer status, open-source exemption vs. a paid Marketplace
listing, Annex III class, controller/processor role, DPIA need, DPA need);
(5) a DRAFT (unpublished, not reviewed) pre-distribution disclaimer; (6) a
freshly re-verified CRA timeline — the previously-cited 24h/72h/14-day
reporting deadline, binding 2026-09-11, was confirmed again via the
European Commission's own CRA pages (not just re-asserted from
`BUILD_PLAN`'s original secondary-sourced figure), with one nuance the
prior memory didn't carry explicitly: 2026-09-11 is specifically the
Article 14 *reporting*-obligation date, not the CRA's full
conformity-assessment applicability date (2027-12-11) — Yehor's launch
window (2026-09-08 to 2026-09-11) lands directly on the earlier,
reporting-obligation date regardless of how the harder Annex III
classification question resolves.
**Owner:** Yehor (external legal input required — not something the agent
can resolve; the packet above is the agent-startable part, now done).

---

## 14. Stray pre-rename branches on `ssh-audit` — RESOLVED 2026-07-15 (Session 018, cross-project research), origin confirmed
**Origin fully confirmed, not "Yehor-only" anymore.** Cross-referenced
against `Autonomous-Core/memory/symbiote-recurring-income-research-and-
buildplan.md` §1.5: on **2026-06-29**, two RepoMend PRs were opened
against **`jtesta/ssh-audit`** (the real upstream, 4.2k stars/221
forks — not Yehor's fork) — **#359** (bare `except` clause, Bandit
B110) and **#360** (`random.randint`→`secrets.randbelow`, Bandit B311).
The stray branches `repomend/fix-bandit.B110-1fdaef` and
`repomend/fix-bandit.B311-6323af` on Yehor's fork are the local source
branches for those two PRs. **Both PRs were closed by the upstream
owner on 2026-07-03** with review comments reading, in full: *"This is
AI slop."* and *"More AI slop."* — then tagged with a project-level "AI
slop" label. No technical engagement with the actual diffs; the fixes
themselves were narrow and correct. This incident is the single piece
of evidence that most directly drove Autonomous-Core's Patchward
Marketplace pivot recommendation (self-serve GitHub App, not unsolicited
open-source outreach — see `docs/architecture/patchward-marketplace-
buildplan.md` §1).

**Reconciled against Stage 2 (item 11):** Session 014's later reuse of
"ssh-audit" as a Stage 2 target was a separate, independently-reasoned
decision (Yehor's own fork specifically, chosen to avoid external-consent
complexity) made without cross-referencing this incident — but it
happens to be compatible with it: both agree the real upstream
`jtesta/ssh-audit` should never be targeted again. Current
`patchward.toml` confirmed (`[github].owner = "yehorcallmedai-maker"`)
to target only the fork, not upstream — no live conflict.

**Notable data point, not just housekeeping:** the `B311` branch shows a
real fix was produced historically for the exact finding Stage 2's own
2026-07-14 run declined (Fix-Gen exhausted `max_turns` without
`submit_fix` — see item 13). Not asserted as a regression — could be a
prompt/model change, version difference, or non-determinism — but
evidence Fix-Gen *can* produce a fix for this exact finding, so
"declined" isn't necessarily "unfixable."

**Recommended, not decided:** the two stale branches on Yehor's fork are
now dead weight from rejected PRs — safe to delete, or safe to leave as
a historical record. Genuinely low-stakes either way; still Yehor's
call, but now a fully-informed one rather than an open mystery.

## 15. No dedicated `tests/test_cli.py` — CLI coverage is scattered and partial (NEW, triaged 2026-07-15)
**WSJF: split into two honestly different-sized pieces — do not treat as
one blind "add CLI tests" task.** Confirmed via `Glob` (no
`tests/test_cli.py` exists) and a grep of `runner.invoke(app, [...])`
call sites: `cli.py`'s 4 commands (`version`, `scan`, `fix`, `batch`) are
698 lines total; only `fix` is exercised via `CliRunner`, and only inside
`test_orchestrator.py` (not a dedicated CLI test file) — `version`,
`scan`, and `batch` have zero `CliRunner` coverage anywhere.

**15a — `[DECLINED]` echo branch (BACKLOG 13 follow-up) — IMPLEMENTED
2026-07-15, pending Yehor's real test-suite confirmation.** Added
`test_run_log_fix_gen_declined_writes_declined_echo_and_record` to
`test_orchestrator.py`'s `TestFixCommandRunLog` class, same established
`CliRunner` + `_make_fix_result()` pattern as its `[SKIP]` sibling.
Asserts `[DECLINED]` appears in CLI output (not `[SKIP]`), the reason
text is printed, and the run log record carries `declined=True` +
`decline_reason`. Not yet verified on Yehor's real machine — the
sandbox's `ast.parse` reported a false truncation at line 1401 (the
mount served a stale, incomplete copy — confirmed via the `Read` tool
that the real file is 1505 lines and well-formed; same class of
mount-truncation quirk previously seen with `cli.py`). Needs a real
`uv run pytest --cov` before this is trusted.

**15b — `version`/`scan`/`batch` CliRunner coverage — CLOSED 2026-07-15,
Session 017.** Self-corrected mid-session: the initial "needs its own
scoping pass, same as item 10" call was wrong — unlike item 10 (zero
spec anywhere), everything needed to size and build this was already
available (`cli.py`'s full source, this codebase's own established
`CliRunner`/`MagicMock` mocking conventions). Built `tests/test_cli.py`
from scratch: 12 tests across `version` (3, including a check that
`_VERSION` and `patchward.__version__` — two independent version
strings in `cli.py` — haven't drifted apart), `scan` (3: clean repo,
findings stored+printed, exception → exit 1), `batch` (5: missing API
key, missing GitHub token, no `[[repos]]`, happy path, failed-repo
path).

**Two real bugs caught while writing the tests, not after:** (1) first
draft of the "any repo failed" batch test assumed exit code 0 without
reading `cli.py` to its actual last line (698) —
`raise typer.Exit(code=1 if any_failed else 0)` — corrected before the
test ever ran, left visible in the test's own docstring. (2) `RunLog()`
called with no `--log` flag defaults to a real
`runs/session_<timestamp>.json` relative to cwd (`run_log.py`'s
`_default_session_path()`) — two tests would have written a real file
into this repo's `runs/` directory as a side effect of running the test
suite; both now pass `--log` pointed at `tmp_path`.

**Verified:** Yehor ran the real suite — **461 passed** (449 + 12 new,
exactly as predicted), 2 skipped, 15 deselected, 90.46% coverage
(flat — CLI-layer tests mostly exercise already-covered lines). Commit
pending (drafted, not yet confirmed landed as of this entry).

## Deferred, not forgotten
- **[REMOVED 2026-07-14]** ClinInsight/Databutton LinkedIn DM replies —
  carried in this list since Session 012 (2026-07-10). Decision this
  pass: this has no relationship to Patchward's code or repo — it's a
  personal/business follow-up that was drifting into an engineering
  backlog with no mechanism to ever resolve it here (no tool access to
  check LinkedIn from this project). Removed visibly, per this project's
  own correction convention (nothing is silently deleted) — it belongs
  in Yehor's own task tracking, not `BACKLOG.md`.
- `tests/fixture_repo` dirty submodule and `.dockerignore` untracked —
  both promoted out of this deferred list and given real decisions this
  session: see items 7c and 7d above.
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

## 16. Internal `Repomend`-naming debt in the real Patchward codebase — TRIAGED AND EXECUTED 2026-07-23 (Session 023), staged uncommitted for Yehor's review
Surfaced 2026-07-22 (Session 022) as a side effect of closing item 8. This
session (023) did the full triage the prior entry called for, then executed
the safe part of the rename. **Triage (independently re-verified against a
fresh clone, not just trusted from this file):** of the original 59
occurrences / 15 files (`src/`, `tests/`), a full literal-quoted-string grep
(not just the identifier grep) found exactly ONE occurrence that crosses a
process/serialization boundary — `REPOMEND_NETWORK_POLICY`, an env var set by
`docker_sandbox.py` and read by `docker/entrypoint.sh` (itself outside the
original 15-file scope, since that grep was `src/`+`tests/`-only). The other
58 are pure Python identifiers (the `RepomendConfig` class name, its
imports, type hints, and docstrings) with no `__all__` export, no
`README`/`docs` exposure beyond one internal design doc, and no top-level
`from patchward import RepomendConfig` pattern anywhere — confirmed
non-breaking. A second env var, `REPOMEND_FIXTURE_REPO` (test-only, read via
`os.environ.get` with a hardcoded fallback default, not referenced in any CI
workflow or doc), was also found and included.

**Executed this session:**
- `RepomendConfig` → `PatchwardConfig` across all 12 files (6 `src/`, 6
  `tests/`) — find-usages based, not a blind string swap; verified via
  fresh grep that zero case-insensitive "repomend" references remain in any
  of those 12 files.
- `test_repomend_toml_example_exists` → `test_patchward_toml_example_exists`
  (`tests/test_distribution.py`) and `test_repomend_config_has_verifier` →
  `test_patchward_config_has_verifier` (`tests/test_orchestrator.py`) — pure
  internal test-function-name renames.
- `REPOMEND_FIXTURE_REPO` → `PATCHWARD_FIXTURE_REPO` in `tests/test_golden_dataset.py`
  and `tests/test_fix_gen.py`. **Flag for Yehor:** if you have this env var
  set anywhere in your own shell profile/CI (not found in this repo's CI
  configs or docs, but that doesn't rule out a personal setup), it needs
  updating there too — otherwise those two test files just silently fall
  back to their hardcoded default path, not a hard failure.
- `REPOMEND_NETWORK_POLICY` (the security-relevant one, controls the
  scanner sandbox's egress policy — BUILD_PLAN §2's line-by-line review
  class): kept BOTH names live, transitionally, rather than a straight
  rename. Traced two things directly from source before deciding this: (1)
  `docker/entrypoint.sh` applies `iptables -P OUTPUT DROP` unconditionally
  and only adds ACCEPT rules on an exact `PYPI_ONLY`/`NPM_ONLY` string
  match — confirmed **fail-closed**, a name mismatch degrades to
  more-restrictive, never opens egress. (2) `docker_sandbox.py`'s
  `BASE_IMAGE` is a digest-pinned, manually-built local image
  (`patchward-scanner:0.1.0@sha256:...`, built 2026-06-12, comment says
  "update after deliberate image rebuild only") — so editing
  `docker/entrypoint.sh` in the repo does **not** reach that already-built
  image until a deliberate rebuild; skew during that window is real, just
  safe-direction. Given that, `docker_sandbox.py` now sets both
  `PATCHWARD_NETWORK_POLICY` (canonical) and `REPOMEND_NETWORK_POLICY`
  (legacy) to the same value; `entrypoint.sh` reads the new name with a
  fallback to the old one, iptables logic itself untouched;
  `docker/scanner.Dockerfile`'s comments updated to mention both names.
  `tests/test_docker_sandbox.py` updated to assert both env vars are
  present (3 tests) plus docstring/comment updates (4 more lines) — same
  480/2/15 pass count as baseline, nothing broken.
- Deliberately **NOT** touched this pass: the Docker image tag name
  (`repomend-scanner:0.1.0` in `docker/scanner.Dockerfile`'s build
  instructions) and the installed entrypoint binary name
  (`/usr/local/bin/repomend-entrypoint`) — both only take effect on a
  future deliberate image rebuild anyway, so bundling their rename with
  that rebuild (not with this internal-identifier pass) avoids mixing a
  naming cleanup with an image-rebuild decision. See new item 17.
- Also deliberately not touched: `.bandit` and `.env.example` comment-level
  "RepoMend"/"repomend-fixture" mentions — the former is old-product-name
  branding (same category as item 8, but internal comments, not user-facing
  product copy — low priority, optional, not scoped into item 16), the
  latter (`repomend-fixture`) is the *actual name* of Yehor's real external
  GitHub fork used for E2E testing (see item 11/14) — renaming the string
  in a comment would misdocument a real external repo, not clean anything
  up. Left alone on purpose, not missed.

**Verification:** full `uv run --python 3.13 --extra webhook pytest --cov`
in the sandbox after all edits → `480 passed, 2 skipped, 15 deselected,
90.60% coverage` — identical pass/skip/deselect counts to this session's
own pre-edit baseline (see `.strategy/STRATEGY.md` Session 023 open entry),
confirming the rename broke nothing. Diff: 17 files changed, 97
insertions, 59 deletions — delivered to Yehor as a patch file plus the
full corrected files, written **uncommitted** to the D:\ working tree for
his own line-by-line review and commit, per standing process (items 8/9's
same pattern). No git commits made from the sandbox.
**Owner:** Yehor, for the `git diff` review + commit only; the actual
content work is done for the non-deferred scope.

## 17. Rebuild `patchward-scanner` image, re-pin its digest, then drop the legacy `REPOMEND_NETWORK_POLICY` (NEW, surfaced 2026-07-23, Session 023) — not started, not agent-startable
Deferred scope split off from item 16's execution. Two things bundled
together because they're the same event: (1) the Docker image tag
(`repomend-scanner:0.1.0`, `docker/scanner.Dockerfile`) and the installed
entrypoint binary name (`/usr/local/bin/repomend-entrypoint`) still carry
the old name — renaming them only matters at image-build time, so there's
no point doing it except as part of a real rebuild; (2) `docker_sandbox.py`
currently sets both `PATCHWARD_NETWORK_POLICY` and legacy
`REPOMEND_NETWORK_POLICY` to the same value specifically because the
currently-pinned image (`patchward-scanner:0.1.0@sha256:...`, built
2026-06-12) bakes in the OLD `entrypoint.sh` that only reads the legacy
name — that dual-set only needs to exist until this item lands.
**Why this is a Directing-Engineer action, not agent-startable:** rebuilding
the image pulls whatever `python:3.12-slim` base and `semgrep`/`bandit`/
`pip-audit`/`eslint`/node-20 versions are current at rebuild time — per
`docker_sandbox.py`'s own comment, those are pinned versions
(`semgrep==1.165.0`, `bandit==1.9.4`, `pip-audit==2.10.1`, `eslint@8.57.1`),
so a rebuild is a real dependency-version event with its own before/after
scan-result verification needs, not something to trigger as a side effect
of a naming cleanup. **Steps for whoever does this (Yehor, or an agent
explicitly asked to do just this, later):** rebuild
(`docker build -f docker/scanner.Dockerfile -t patchward-scanner:0.1.0 .`,
updating the tag in that same command to drop "repomend" if renaming the
tag too), re-pin the digest in `docker_sandbox.py`'s `BASE_IMAGE` constant
(`docker inspect ... --format "{{.Id}}"`), sanity-check scan results
before/after on the fixture repo, then remove `REPOMEND_NETWORK_POLICY`
from `docker_sandbox.py`, `docker/entrypoint.sh`'s fallback, and the
transitional assertions in `tests/test_docker_sandbox.py`.
**Owner:** Yehor (or agent, once explicitly asked — this is a scoped,
well-understood follow-up, just not something to bundle into item 16).

---

## 18. `marketplace_purchases` has no retention/TTL policy — no deletion path exists at all (NEW, surfaced 2026-07-24, Session 024, during BACKLOG 12 triage)
Confirmed by reading `src/patchward/installations_db.py` and every call site
of it in `webhook.py`: `installations` and `installation_repos` rows are
genuinely deleted via `delete_installation()` when GitHub sends
`installation`/`action=deleted` (App uninstalled) — that path is real and
correct. `marketplace_purchases` has no equivalent path anywhere — a
`cancelled` status only ever updates the `status` column via
`upsert_marketplace_purchase()`; the row itself is never removed by any
code in this repository, even after the same account's `installations` row
is deleted on uninstall. No TTL, no scheduled purge job, no
data-minimization policy exists for this table. Practical effect: a GitHub
account login plus its full historical plan/billing-cycle metadata is
retained indefinitely.
**Why this matters regardless of how BACKLOG 12's legal questions resolve:**
"don't keep customer billing metadata forever with no policy" is good
practice independent of the CRA/GDPR classification outcome, and this is
also the exact factual gap that a GDPR DPIA (see item 12) would need
covered.
**Proposed fix, agent-startable whenever Yehor wants it scheduled:** add a
retention policy — e.g. delete or anonymize a `marketplace_purchases` row N
days after `status = "cancelled"` with no subsequent re-purchase for that
`account_login` — plus a test asserting the purge actually happens. Small,
isolated to `installations_db.py` and a new scheduled task in `webhook.py`
or a standalone cron script; does not touch the CRA/GDPR legal questions
themselves.
**Owner:** unassigned — not urgent, but cheap to fix once prioritized.

## 19. `GITHUB_TOKEN` reaches disk (webhook path) and unfiltered logs (both paths) — NEW, surfaced 2026-07-24, Session 024, during security.html copy verification
**Origin:** Yehor asked for a bounded, read-only trace of `_build_remote_url()`'s
output before publishing a security.html sentence describing it. The sentence
itself checked out; the trace surfaced a real, separate code gap.

**Confirmed, not persisted via `git remote add`/`set-url` anywhere in the
codebase** (grepped `worktree_common.py`, `pr_publisher.py`,
`github_app_auth.py`, `webhook.py` — zero matches). The token-bearing URL is
used two ways:
1. `worktree_common.py:295` — `["git", "push", "--force", remote_url, ...]`,
   passed inline as an argv element to `git push`. Ephemeral, argv-only,
   never touches `.git/config`. This is the CLI/worktree path (Yehor's own
   machine) — clean.
2. `webhook.py:278` — `["git", "clone", "--depth", "1", clone_url, ...]`.
   Git's own default behavior writes the clone source URL — including the
   embedded `x-access-token:<token>@github.com` — into the freshly cloned
   repo's `.git/config` as the `origin` remote. Nothing in `webhook.py`
   rewrites or strips it afterward. `tmp_dir` (and therefore that
   `.git/config`) is only removed in the outer `finally: shutil.rmtree(...)`
   — i.e. the token sits in plaintext on the Fly.io host's disk for the
   full duration of the scan → fix-gen → verify → publish run, not just the
   clone step. Cleanup does run on both success and exception paths
   (Python `finally`), so this is not a permanent leak, but it is a real,
   avoidable exposure window on the hosted path specifically — the CLI path
   has no equivalent because the user already owns the local clone.

**Also confirmed: no scrubbing on two log paths, either.** `scrub()` is
never called on git subprocess output.
- `webhook.py:283` — `logger.error("[webhook] clone failed for %s: %s",
  repo_full_name, proc.stderr)` logs raw `git clone` stderr verbatim. Git is
  well known to echo the full remote URL (credentials included) in several
  of its own failure modes (e.g. `fatal: unable to access '<url>'`,
  auth/connection errors) — whether it does so for this exact failure case
  was not empirically tested this session, but the code applies zero
  filtering regardless of what git prints.
- `worktree_common.py:294-308`'s `git_push_branch()` raises
  `RuntimeError(f"...stdout: {proc.stdout!r}\nstderr: {proc.stderr!r}")` on
  a failed push — same unfiltered pattern. This propagates to two more
  unfiltered sinks: `cli.py:544-548`'s `except Exception as pr_exc:
  typer.echo(f"  [PR] Publish failed: {pr_exc}", err=True)` (CLI stderr),
  and, on the webhook path, `pipeline.py:266-274`'s `err_str = str(exc) or
  repr(exc)` → `result["error"] = err_str` + `logger.error("[pipeline]
  error for %s: %s", repo_label, err_str)`, and that same `result` dict is
  then logged again in full by `webhook.py:311`'s
  `logger.info("[webhook] scan finished for %s: %s", repo_full_name,
  result)`. **The run log itself (NDJSON, `run_log.py`) is not affected** —
  `pipeline.py`'s `run_log.append_batch_result()` only ever writes the
  `finding_status` string, never `err_str`, so this is specifically an
  application-log (Fly.io `logger.*`) and CLI-stderr exposure, not a
  run-log-artifact exposure.

**Not acted on, deliberately — this is a code fix, not a copy question.**
The security.html sentence this trace was checking ("embedded in the HTTPS
remote URL passed as a command argument") remains accurate as written and
was not changed further; it describes the delivery mechanism honestly
without claiming a safety property this finding would contradict. This item
tracks the actual gap for a future code fix: (a) strip credentials from the
webhook path's cloned `.git/config` immediately after clone (or avoid
embedding the token in the clone URL at all, e.g. via a short-lived
credential helper), and (b) route git subprocess `stdout`/`stderr` through
`CredentialProxy.scrub()` (or an equivalent token-aware redaction) before
any of the four log/echo sites above.
**Owner:** unassigned — **SUPERSEDED, see `STATUS: CLOSED` below ↓** — not urgent enough to block tonight's site-copy
commit (the sentence is accurate), but real, and on the hosted path, not
just theoretical. Yehor's call on priority/timing.

---

**STATUS: CLOSED 2026-07-27 (Session 025).** Fix committed, pushed, deployed,
and `/healthz`-confirmed on the new image. Verification chain, each step
independent of the last:
- Base fix committed+pushed as `37b3bfd`; five-finding follow-up committed+
  pushed as `dee84e1`. Both verified via fresh `git ls-remote` + a fresh
  `git clone` byte-compared against the authored trees (zero drift).
- Deployed to Fly image `sha256:ac54d18a802e4db6d35d6574ad1188b90797630ca3cceb39c507490b06d6a8e3`
  on machine `7841600fd5e7e8`, built from the `dee84e1` working tree
  (`fly image show` digest matches the build manifest).
- `/healthz` → `200 {"status":"ok"}` confirmed by TWO methods: WebFetch AND
  a real Chrome browser read (Claude-in-Chrome), per this project's own
  H10-candidate (WebFetch alone is not trusted for a closing gate). The
  deploy emitted a transient "not listening on 0.0.0.0:8000" warning during
  the rolling restart; the green `/healthz` on the new image proves the app
  bound and the warning did not persist.

**What the remediation actually covered.** This trace named two surfaces
(.git/config persistence + unfiltered logs). Adversarial review of the fix
surfaced three more, all closed:
- (this trace) `.git/config` token persistence on the webhook clone →
  closed: tokenless clone URL + inline env-reading credential helper; the
  token never enters the URL, so git has nothing to persist.
- (this trace) unfiltered git stderr/exception text at four log/echo sites →
  closed: `scrub_text()` (pattern + register-at-mint layers) at all four.
- (review #1) token in argv / `/proc/<pid>/cmdline` → closed: credential
  travels via the subprocess environment + helper, never argv; empirically
  confirmed token-free via a live `/proc` poll on Linux and a real
  authenticated clone on Windows.
- (review #1) `subprocess.TimeoutExpired` captures stdout/stderr AND argv on
  the exception object → closed: handler scrubs `exc.stdout`/`exc.stderr`/
  `exc.cmd` at source before re-raising argv-free.
- (review #1) cross-thread race: `scrub_text()` iterating the live
  `_RUNTIME_CREDENTIALS` set while another thread registered could raise
  `Set changed size during iteration` FROM INSIDE the `except` block,
  surfacing the original UNSCRUBBED exception via `__context__` — a scrubber
  that leaks the token it exists to redact, reachable only under the hosted
  webhook's real threading model. Closed: `for val in tuple(...)` GIL-atomic
  snapshot. **This fix is review-verified / correct-by-construction, NOT
  test-proven** — the race is not deterministically reproducible through the
  public API, so the accompanying `test_scrub_text_concurrent_smoke` is an
  honestly-labeled non-discriminating smoke test, not a red-on-revert proof.
- (review #1) token regex leading `\b` defeated by a preceding word char
  (e.g. percent-encoded `%3Aghs_...`) → closed: de-anchored; negative-control
  test confirms the `{16,255}` floor still protects legitimate prose.
- (review #3) `#3` the credential-helper reset was inside `if token:`, so the
  tokenless webhook push borrowed ambient host credentials and issued
  `erase` against them → closed: `credential_reset_args()` on every path,
  fails loud with no credential.

**Adversarial review: three passes, NOT "clean."** Pass 1 found the five
findings above (plus items later split to 21/22/23). Pass 2 found two
non-blocking issues in the fix itself (F1: `exc.cmd` unscrubbed + an
over-claiming docstring; F2: a non-discriminating test) — both fixed. Pass 3
(re-attack on the final tree) returned **0 leaks / 0 blockers**, and found
**three robustness items** — logged as BACKLOG 22 (Gate 3 unsandboxed
credential inheritance — the single largest pre-launch exposure, see item 22),
23 (remaining unscrubbed error sinks), 24 (unbounded `_RUNTIME_CREDENTIALS`
growth). The empty-of-leaks final pass was the convergence signal to ship;
the three robustness spin-offs are honestly recorded, not swept into "clean."

**Suite at close:** 505 passed / 3 skipped / 15 deselected, coverage 90.62%,
Python 3.14.4 (Yehor's machine); reproduced 503/2/15 in-sandbox.

**Spun off, still open:** 21 (dead `github_token` param — webhook may not push
a PR at all), 22 (Gate 3 credential inheritance — NEXT security priority), 23,
24. BACKLOG 19's credential-DELIVERY boundary is closed; item 22 is the
credential-INHERITANCE boundary the same review found adjacent to it.

**Owner:** CLOSED — no further action on item 19 itself.


## 20. `callmed-landing`'s corrected copy appeared not to be live at the plain URLs — CLOSED same day, FALSE ALARM (surfaced 2026-07-24 close, resolved 2026-07-24, same session)
**WSJF: highest — this is the actual state of the item this whole session
treated as its top priority.** Session 024's close-out claimed the
data-flow corrections were "confirmed live in production," based on one
fetch of `callmedai.com/privacy` (which happened to be current) and one
fetch of `callmedai.com` for an unrelated check (RepoMend absence only —
never checked for the actual false-claim strings). A second, more
thorough double-check found this was wrong as a general claim:

- `https://callmedai.com/` (bare root, no extension) — still serves the
  OLD copy. Confirmed twice, independently, several minutes apart (ruling
  out this tool's own 15-minute fetch cache as the explanation): "your
  code never leaves your infrastructure" and "fully auditable on-premise"
  are both still present.
- `https://callmedai.com/security` (bare, no extension) — serves an even
  older stub, dated May 2026 (predates even the June 2026 v1.1 revision,
  let alone tonight's July 2026 v1.2).
- `https://callmedai.com/index.html` and `https://callmedai.com/security.html`
  (explicit `.html` extension) — both serve the fully current, corrected
  copy. A cache-busting query string on the bare URLs also returns current
  content.

**Working diagnosis, not confirmed from this sandbox (no header/DNS access
— `curl`/`dig` to arbitrary hosts blocked here, consistent with H4):** a
CDN/edge cache is serving a stale cached response for the exact clean
URLs (`/`, `/security`) while `.html`-suffixed and cache-busted requests
bypass that cache key and reach current origin content. This is Yehor's
to diagnose and fix — likely a dashboard cache-purge or a fresh deploy
trigger on whichever platform serves the site (Vercel/Netlify/Cloudflare —
not yet identified from this sandbox).

**Why this matters more than anything else on this list:** the homepage
and the security page's clean URL are exactly what a real visitor types
or clicks — not the `.html` form. The false "code never leaves your
infrastructure" / "fully auditable" claims that this entire session's
urgent-priority site fix was meant to remove are, right now, still being
shown to anyone who visits the plain URLs.

**RESOLVED, same session, false alarm — root cause was this session's own
tooling, not production.** Yehor's own diagnostics (real `curl.exe -sIL`
from his machine) showed `cf-cache-status: DYNAMIC` on both `/` and
`/index.html` — Cloudflare is NOT caching these responses at all, passing
every request straight to origin — which already contradicted the CDN-
cache hypothesis above. Yehor's own Cloudflare Pages dashboard screenshot
then showed the `callmed-landing` project's latest deployment (21 minutes
old at the time, matching commit `68e612a`'s message exactly) already live
in production. **Final, decisive check: a real Chrome browser (via
Claude-in-Chrome), navigated fresh to both `callmedai.com/` and
`callmedai.com/security` and read the actual rendered page content —** the
homepage shows the corrected "default-deny iptables" / two-stage Anthropic
language; `/security` shows "Last updated: July 2026 · Version 1.2" with
every corrected section present (`Credential isolation — Patchward`,
`Three-gate verifier — Patchward`, `Transport security`, `Supply chain`,
all current). **The site was never stale. The "stale" finding was an
artifact of this session's own `WebFetch` tool** — which fetches a page
and summarizes it through a small, fast model rather than returning raw
bytes — reporting "not found" for strings that were, per the real browser,
actually present. Root cause of the tool's error not fully determined
(possibly its own internal cache, possibly the summarization step
under/over-reporting on a long page) — not chased further since the
underlying question (is the site correct?) is now answered definitively.
See new heuristic candidate in `.strategy/STRATEGY.md`.
**Owner:** none — closed. No action needed from Yehor.

## 21. CONFIRMED hosted-path breakage: `run_repo_pipeline` ignores its `github_token` param — the webhook cannot push a PR at all (surfaced 2026-07-27, Session 025, during BACKLOG 19 trace; TRACED + CONFIRMED 2026-08-04, Session 029)

**TRACE 2026-08-04 (Session 029) — size settled: ONE HOP, does NOT touch App-token minting.** The GitHub App machinery already works end to end: `webhook.py:276` mints an installation access token via `exchange_for_installation_token`, `webhook.py:282` registers it for redaction, and `webhook.py:302` uses it for the clone (`credential_env(token)`) — that path is fine. `webhook.py:333-338` correctly passes `github_token=token` into `run_repo_pipeline`, which then DROPS it (`pipeline.py:68`, signature only, unused in the body). Meanwhile `PRPublisher._push_token()` (`pr_publisher.py:149-160`) reads `GITHUB_TOKEN` from `CredentialProxy._creds`, which `load()` fills from `os.environ` only — and per the comment at `credential_proxy.py:68` the Fly deployment has NO `GITHUB_TOKEN` secret at all. So `_push_token()` returns `""` and the push has no credential. **The fix is NOT to add a static `GITHUB_TOKEN` secret to Fly** — that would put a PAT where an App installation token belongs. The seam is a `push_token` parameter on `PRPublisher.__init__` taking precedence over the proxy lookup, passed at the construction site (`pipeline.py:234`); the CLI path keeps its env-based token unchanged. Deliberately NOT written in Session 029 — its own arc, pending Yehor's bundle-or-split call.


**§5 UPDATE 2026-07-29 (Session 027): CONFIRMED against the LIVE IMAGE** (was
Tier-0 at build-recipe level only). On running image `deployment-01KYJ325AN...`,
the verifier's exact call `python -m pytest` → `/usr/local/bin/python: No module
named pytest`, which matches none of the three SKIP triggers → Gate 3 returns
FAIL (not SKIP) → `g3_ok` false → no PR. `node`/`npx` also absent → the jest
branch cannot run either. The last Tier-1→Tier-0 gap on the board is closed.
Item 21 itself (the dead `github_token` param + absent push credential) remains
OPEN — this and §5 are the two remaining hosted-path blockers now that 27 is
fixed. Original entry preserved below. ↓

**§5 FORK MEMO (2026-08-01, Session 028):** the *what-does-Gate-3-mean* fork — install the test runner into the webhook image (Gate 3 executes customer tests) vs. SKIP gracefully when the runner is absent (Gate 3 becomes advisory on hosted) — is scoped in `memory/BACKLOG_S5_gate3_meaning_memo_2026-08-01.md`. Key entanglement (memo §3): the missing runner is currently the only thing keeping item 22 dormant on hosted, so §5-Option-A is the act that arms item 22 — §5-A ⇒ item 22-A ⇒ new infra. **DECISION 2026-08-01 (Session 028): §5 = C2** (SKIP-and-disclose) — implementation scoped in the memo §7 (verifier SKIP-not-FAIL + PR-body disclosure + item 21 token threading + live site-copy check); item 22 stays deferred/dormant. **IMPLEMENTED 2026-08-04 (Session 029), steps 1-2 only, commit `d72c0df`:** verifier SKIP-not-FAIL on runner-absent (distinct `RUNNER_ABSENT_REASON`, all pre-existing SKIP triggers preserved) + PR-body disclosure keyed off the gate REASON. Hardened beyond the memo spec with a forged-signature injection defense (independent import probe, fail-closed) after the naive string-match form was tested and found exploitable. Gate: full suite on Yehor's Python 3.14.4 — 531 passed / 3 skipped / 91.11%. STILL OPEN from memo §7: step 3 (item 21 token threading) and step 4 (live site-copy check).

**Status:** OPEN — logged only, deliberately NOT bundled into BACKLOG 19's
security diff per the §2 keep-security-diffs-clean rule. Yehor's own
framing at logging time: "this isn't cosmetic dead code... potentially a
'the hosted product doesn't work' bug that deserves its own focused
investigation, not a rider on a security commit."

**The trace (all source-verified at HEAD `1132815`, Session 025):**
- `run_repo_pipeline` accepts `github_token: str` (`pipeline.py:68`) and
  never references it anywhere in its body — the only other occurrences
  are `run_batch`'s own signature (`pipeline.py:325`) and its
  pass-through (`pipeline.py:342`). Dead parameter.
- The PR publisher instead builds its credential from a fresh
  `CredentialProxy().load()` (`pipeline.py:233`) — i.e. the process
  environment's `GITHUB_TOKEN`.
- The Fly deployment sets no `GITHUB_TOKEN` secret: `fly.toml`'s own
  secrets documentation lists `GITHUB_APP_ID`, `GITHUB_WEBHOOK_SECRET`,
  `ANTHROPIC_API_KEY`, `GITHUB_APP_PRIVATE_KEY_B64` only.
- Therefore on the webhook path: the freshly minted Installation Access
  Token passed at `webhook.py` (`github_token=token`) goes nowhere, the
  publisher's push credential is empty, and the push fails auth. The
  webhook can clone and scan, but almost certainly cannot open a PR —
  the hosted product's core output step.

**What is verified vs. not:** the code path is unambiguous
(source-verified, three files). NOT verified end-to-end — no live
webhook run has been observed failing at push. First step of the
investigation: reproduce (or refute) with a real webhook-triggered run
against a test installation, then decide the fix — most plausibly
threading the minted token through `run_repo_pipeline` into
`PRPublisher`/`git_push_branch(token=...)`, whose BACKLOG 19 signature
(`token` parameter, ephemeral credential helper) was designed to accept
exactly this handoff without reintroducing any URL/argv embedding.

**Note:** BACKLOG 19's fix deliberately preserved this behavior
(empty token on the webhook path → same auth failure as before, now via
a tokenless URL) so the two changes stay separately reviewable and
separately revertable.

**SECOND, INDEPENDENT DEFECT ON THE SAME PATH [2026-07-28, Session 026 —
surfaced by the BACKLOG 22 scope pass, filed here because it belongs to 21's
path, not to 22's security boundary]:** even if the token handoff above were
fixed, Gate 3 hard-FAILs on the hosted path for every pytest-detecting repo,
so `verification_status != "verified"` and no PR is ever published. Chain,
each link checked independently (Tier 0 unless noted):
- The `webhook` extra cannot carry pytest. Built the actual wheel from
  `pyproject.toml` at HEAD and read its `METADATA` (not the source TOML, so a
  build-config mismatch is excluded): `Provides-Extra: webhook` with exactly
  four `Requires-Dist` lines (fastapi, httpx, pyjwt[crypto], uvicorn[standard]);
  the string `pytest` does not occur anywhere in `METADATA`.
  `[dependency-groups].dev` is PEP 735 and never reaches wheel metadata, so
  `uv pip install --system --no-cache .[webhook]` cannot install it.
- No transitive route. `docker/webhook.Dockerfile`'s only other installs are
  `uv` and `semgrep bandit pip-audit`. PyPI metadata for all four: `uv` 0
  runtime reqs, `semgrep` 27, `bandit` 17, `pip-audit` 23 — the only pytest
  mention anywhere is `pytest; extra == "test"` on pip-audit, which a plain
  `pip install pip-audit` does not install.
- The output string matches none of the SKIP triggers. Executed Gate 3's exact
  argv against a real pytest-less venv: returncode 1, output
  `…/bin/python: No module named pytest`. Checked against the three literal
  triggers at `verifier.py:767` (`ModuleNotFoundError` / `ImportError` /
  `no tests ran`) — zero hits → `GateResult(FAIL, ...)`, not SKIP.
- `verifier.py:110` (`g3_ok = self.gate_3.status in (PASS, SKIP)`) is therefore
  false → `pipeline.py:220-227` sets `finding_status = "verify_failed"` → the
  PR-publisher block is never reached.

**RESIDUAL CLOSED — CONFIRMED ON THE LIVE CONTAINER [2026-07-28, Session 026
close]:** `fly ssh console -a patchward-webhook` on machine `7841600fd5e7e8`:
`python -c "import pytest"` → `ModuleNotFoundError: No module named 'pytest'`,
and `python -m pytest --tb=short -q` inside a probe directory containing a real
`tests/test_probe.py` → `/usr/local/bin/python: No module named pytest`. That
string matches NONE of the three SKIP triggers at `verifier.py:767`, so Gate 3
returns FAIL. **Tier 0 on the running container, not merely on the build
recipe.** Also confirmed in the same session: `node` and `npx` are both ABSENT
(`command -v` → nothing), so the jest branch cannot execute either — every
detected suite hard-FAILs on the hosted path.
(Method note: the `echo "exit=$?"` in that probe reported the exit status of the
`tail` at the end of the pipeline, not of pytest — it is not evidence and was
not treated as any.)

**PROVENANCE OF THE RUNNING IMAGE — CONFIRMED [2026-07-28]:** sha256 of four
source files inside the container compared against the same files at `dee84e1`:
`git_credentials.py`, `credential_proxy.py` and `webhook.py` matched exactly
(`ea5791a5…`, `e6a2ec86…`, `a6b9099941…`). `verifier.py` initially appeared to
MISMATCH (`e375a6d3…` vs `a25ac226…`) — resolved: `e375a6d3…` is HEAD's
`verifier.py` with CRLF line endings (reproduced exactly by
`git show HEAD:src/patchward/verifier.py | sed 's/$/\r/'`). Content identical,
line endings differ, Python indifferent. **The image IS built from `dee84e1`'s
code.** This also independently corroborates the long-standing CRLF story from a
new angle: the build context carried a MIXED working tree — files recently
written by tooling during the BACKLOG 19 arc are LF, files untouched since an
earlier checkout are CRLF — and the deployed image preserves that mix.
Informational, not a defect; worth knowing that image hashes are not a reliable
provenance signal from a Windows build context.

**Why this changes 21's priority:** THREE independent defects now sit on the
same hosted PR-publish path (see also item 27, found in the same live check and
upstream of both others), any one sufficient to prevent a PR. Fixing one
without the other ships nothing. 21 should be investigated as ONE unit covering
both, and it outranks item 22 — 22 is a pre-launch security item on a code path
that may not currently execute at all.

**Owner:** agent-startable (investigation + fix proposal); the live
webhook-run verification and the `fly ssh console` confirmation need Yehor's
test installation / deploy access.

## 22. Gate 3 (verifier test-suite gate) runs the cloned adversarial repo's OWN test suite unsandboxed, with inherited credentials in the environment (NEW, surfaced 2026-07-27, Session 025, BACKLOG 19 adversarial pass)

**Status:** OPEN — pre-launch security item. Pre-existing (not introduced by
BACKLOG 19); the adversarial re-attack on `37b3bfd` surfaced it. Distinct
unit from BACKLOG 19 — deliberately NOT folded into the 19 follow-up, to
keep that a clean credential-boundary diff (same §2 discipline that split
21).

**The finding (source-verified at `37b3bfd`, and demonstrated by the
adversarial reviewer):**
- `Verifier._gate_3_test_suite` (`verifier.py:745,778`) runs the cloned
  repo's own tests via `subprocess.run(["python","-m","pytest",...])` and
  `["npx","jest",...]` with **no `docker_sandbox`** (grep: zero references
  in `verifier.py`) and **no `env=`** override — so the child inherits the
  full parent `os.environ`.
- **PREMISE CORRECTION [2026-07-28, Session 026].** This item originally read
  "…while scanners DO route through the sandbox via
  `pipeline.py`→`run_all_scanners`". **That is FALSE at HEAD.**
  `run_all_scanners`' `sandbox` parameter defaults to `None`
  (`scanner.py:320-324`), and every production call site omits it:
  `pipeline.py:126-130`, `cli.py:124-126`, `cli.py:290-292`, `worktree.py:29`.
  Exhaustive `grep -rn "DockerSandbox(" src/` returns docstrings only — the
  class is instantiated nowhere in production code (tests only).
  **Consequence for the decision:** Option A below is NOT "extend the
  sandboxing the scanners already have to Gate 3" — there is no production
  sandboxing to extend. Option A means the FIRST production use of
  `DockerSandbox`, on a Fly host with no Docker CLI or daemon
  (`docker/webhook.Dockerfile` installs only `git` + `ca-certificates`):
  new infrastructure, not a wiring change. This raises Option A's honest cost
  estimate. The wider gap (the sandbox mechanism was never wired in at all)
  is logged separately as item 26. Full trace:
  `memory/BACKLOG22_gate3_scope_memo_2026-07-28.md`.
- The cloned repo is adversarial by design (ADR-013: prompt-injection in
  scope; a `conftest.py` / jest config is arbitrary code execution). So
  adversarial repo code runs as the same uid as the pipeline.
- Two exposures for that code: (a) `PATCHWARD_GIT_TOKEN` is in the
  concurrent git subprocess's environment — reviewer demonstrated a
  same-uid poller recovering it from `/proc/<pid>/environ` while the real
  clone ran (owner-only 0400, so strictly better than the pre-BACKLOG-19
  world-readable `/proc/cmdline` + `.git/config`, but not closed); (b)
  `CredentialProxy.load()` leaves `ANTHROPIC_API_KEY`/Langfuse keys in
  `os.environ`, which Gate 3's child inherits directly — reviewer
  demonstrated the adversarial child printing `INHERITED_ANTHROPIC=sk-ant-…`.
  On the CLI path the long-lived `GITHUB_TOKEN` PAT is inherited the same
  way, no race needed.

**Why this is NOT a reason to change BACKLOG 19's credential mechanism:**
a token in the subprocess *environment* is inherent to ANY env-based
credential passing (GIT_ASKPASS included — it reads the token from an env
var too). The mechanism is sound. The fix is at the Gate 3 boundary, not
the credential layer: run Gate 3 inside the same `docker_sandbox` the
scanners use (repo mounted read-only, credentials stripped via
`get_container_env()`), OR at minimum spawn Gate 3 with an explicit
`env=` scrubbed of all `_CREDENTIAL_KEYS` and never overlap it in time
with a token-bearing git process. This is a design change with its own
before/after behavior check (does sandboxing Gate 3 break legitimate test
suites that need network / build tools?), so it is NOT a same-session
side edit.

**Blast-radius note:** this is the single largest pre-launch exposure
found so far — it is the actual path by which adversarial repo content can
reach a live credential, and it is worse than (and different from) the
`.git/config` path BACKLOG 19's commit message named. Prioritize before
Marketplace listing.

**Owner:** agent-startable scoping; the sandbox-vs-env design decision and
the "what does Gate 3 legitimately need" question are Yehor's.

## 23. Unscrubbed error sinks, two of which persist to disk/DB (NEW, surfaced 2026-07-27, Session 025, BACKLOG 19 adversarial pass)

**Status:** OPEN — low urgency, defense-in-depth. No token-bearing string
is demonstrated reaching any of these post-BACKLOG-19 (the demonstrated
leak surfaces were closed in `37b3bfd` + its follow-up); this tracks the
remaining sinks of the same class the commit scrubbed, for completeness.

**Sites (verified present at `37b3bfd`):** `pipeline.py:198-203/226/259/305`,
`webhook.py:341` (logs the whole `result` dict), `cli.py:556-561`, and the
two that PERSIST rather than just log: `cli.py:577`
`finish_run(...error=str(exc))` → SQLite runs DB (`db.py`), and
`cli.py:676` `run_log.append_batch_result(r)` → `runs/session_*.json` on
disk (`run_log.py:90`). Proposed fix: route these through `scrub_text`
before they hit a log stream or disk, same as the four sites BACKLOG 19
already covers. Cheap, mechanical, but spread across unrelated functions —
its own commit, not a rider.

**Owner:** agent-startable.

## 24. `_RUNTIME_CREDENTIALS` grows unbounded on the long-lived webhook → O(n) `scrub_text` (NEW, surfaced 2026-07-27, Session 025, BACKLOG 19 third adversarial re-attack)

**Status:** OPEN — robustness, non-blocking, NOT a credential leak. Deliberately
NOT folded into the BACKLOG 19 security commit (that diff had just passed a
clean-of-leaks adversarial pass; adding a design change to it would expand the
re-review surface for a non-security concern — same discipline that split 21/22/23).

**The finding (demonstrated on the patched tree by the re-attack):**
`credential_proxy._RUNTIME_CREDENTIALS` is a process-global, append-only set.
`webhook.py:282` registers one minted installation token per run and never
evicts; `cli.py:653` adds a second registration site. `scrub_text`
(`credential_proxy.py:127`) iterates the whole snapshot doing `val in text`
per call. Measured: registry 1k→41µs, 50k→4.4ms, 200k→21ms per scrub call
(linear). A long-lived webhook process therefore (a) grows memory without
bound and (b) slows every log/exception scrub over time. Mild self-DoS, no
exposure. The docstring at `credential_proxy.py:99-101` calls the registry
"append-only … harmless" — true for correctness/staleness, silent on this
growth cost; update it as part of the fix.

**Proposed approach (design decision, hence not a rider):** installation
tokens expire server-side in ~1 hour, so an unbounded lifetime registry is
overkill. Options: (a) bound the set with an LRU/size cap; (b) store
(value, expiry) and evict expired entries on registration; (c) scope the
registry per-run rather than process-global (the webhook already has a
natural per-delivery boundary in `trigger_scan_for_installation`). (c) is the
cleanest — it also shrinks the scrub cost to O(tokens-in-this-run). Needs a
before/after check that scrubbing still covers every path within a run.

**Owner:** agent-startable once the eviction/scoping policy is chosen.

### Notes from the same re-attack (logged, no action — not reachable in this deployment)
- `exc.cmd` scrub in `git_push_branch` (`worktree_common.py:365`) skips non-str
  (bytes) elements. Theoretical only: `git_push_branch` always builds an
  all-`str` cmd, so a real `TimeoutExpired.cmd` is fully scrubbed. No fix
  unless a future caller passes bytes argv.
- The inline credential helper (`git_credentials.py:52`) is host-unconditional
  (`echo password=$PATCHWARD_GIT_TOKEN` for whatever host git asks about). All
  three adversarial-repo vectors to reach a non-github host were checked and
  found NOT reachable: clone is not `--recurse-submodules` (`webhook.py:298`),
  git-lfs is absent from `docker/webhook.Dockerfile`, and clone does not
  transfer/execute repo hooks. Revisit only if any of those change (e.g. lfs
  added to the image, or submodule fetching enabled).

## 25. `_CREDENTIAL_KEYS` omits four credentials that ARE in `os.environ` on the hosted path (NEW, surfaced 2026-07-28, Session 026, BACKLOG 22 scope pass)

**STATUS: CLOSED 2026-07-29 (Session 027)** — shipped as commit `f02ad21`, pushed
to `origin/main`, verified on the remote by fresh clone. Full suite 519 passed /
90.62% on Yehor's machine; `credential_proxy.py` at 100%. All four GitHub App
credentials are now in `_CREDENTIAL_KEYS` (excluded from `get_container_env()`
and scrubbed). Follow-up flagged, not blocking: `GITHUB_APP_ID` (7-char,
non-secret) is now also scrubbed — a documented, conservative over-redaction.
Original entry preserved below. ↓

**Status:** OPEN — pre-launch security item, agent-startable, and the sequencing
note matters: it gates BOTH Option A and Option B of item 22, so it should ship
STANDALONE and FIRST, independent of which way the Gate 3 decision goes.

**The finding (source-verified at `8931702`):** `_CREDENTIAL_KEYS`
(`credential_proxy.py:39-45`) covers only `ANTHROPIC_API_KEY`,
`LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `GITHUB_TOKEN`. Four further
credentials are read from `os.environ` and are covered by nothing:

| Variable | Read at | Set on Fly |
|---|---|---|
| `GITHUB_APP_PRIVATE_KEY_B64` | `github_app_auth.py:50` | `fly.toml:14` |
| `GITHUB_APP_PRIVATE_KEY` (raw PEM alternative) | `github_app_auth.py:47` | alternative to the above |
| `GITHUB_APP_ID` | `github_app_auth.py:75` | `fly.toml:13` |
| `GITHUB_WEBHOOK_SECRET` | `webhook.py:238` | `fly.toml:13` |

**Blast radius — worse than anything item 19 or item 22 records.** The App
private key plus the App ID mints installation access tokens for EVERY
installation of the GitHub App, not just the repo under scan. That is a
cross-tenant credential in plain `os.environ`, inherited directly by Gate 3's
adversarial child (item 22), with no race required. `GITHUB_WEBHOOK_SECRET`
separately allows an attacker to forge signed webhook deliveries.

**Why it gates both 22 options:** `_build_docker_cmd`'s structural exclusion
(`docker_sandbox.py:174-178`) and `get_container_env()`
(`credential_proxy.py:190-197`) both filter on `_CREDENTIAL_KEYS` and nothing
else. Option A would forward the App private key straight into the container;
Option B would strip the Anthropic key and leave the App private key behind.
Neither option closes the exposure until this list is widened.

**Proposed fix:** add the four names to `_CREDENTIAL_KEYS`. Check first whether
any legitimate consumer requires them downstream of a filtered env (the App
auth path reads `os.environ` directly, so most likely not). Note `GITHUB_APP_ID`
is not secret on its own but is useless to withhold separately.

**LIVE CONFIRMATION [2026-07-28, Session 026 close]:** read from the running
container's own `os.environ` (names + lengths only, no values printed) —
`GITHUB_APP_PRIVATE_KEY_B64` SET (len 2236), `GITHUB_APP_ID` SET (len 7),
`GITHUB_WEBHOOK_SECRET` SET (len 36), `ANTHROPIC_API_KEY` SET. All four are
present in the parent environment Gate 3's child would inherit. Confirmed
ABSENT, as predicted: `PATCHWARD_GIT_TOKEN` (BACKLOG 19's copy-not-mutate fix
holds on the live host — `credential_env()` never mutates `os.environ`),
`GITHUB_TOKEN` (item 21's root cause), and both Langfuse keys. The enumeration
in this item is therefore live-confirmed, not merely source-traced.

**Owner:** agent-startable.

## 26. `DockerSandbox` has never been wired into production on either path (NEW, surfaced 2026-07-28, Session 026, BACKLOG 22 scope pass)

**Status:** OPEN — infrastructure gap, not a live-leak finding. Natural
successor to / companion of BACKLOG 17 (scanner image rebuild). Directing-
Engineer scope, not a same-session side edit.

**The finding (source-verified at `8931702`):** `run_all_scanners`' `sandbox`
parameter defaults to `None` → host subprocess (`scanner.py:320-328`, and the
same `sandbox is not None` branch in every individual runner). Every production
call site omits the argument:

| Call site | Args passed | Effective sandbox |
|---|---|---|
| `pipeline.py:126-130` (webhook + batch) | `repo_path, cfg.semgrep_rules` | `None` |
| `cli.py:124-126` (`patchward scan`) | `scan_path, cfg.semgrep_rules` | `None` |
| `cli.py:290-292` (`patchward fix`) | `scan_path, cfg.semgrep_rules` | `None` |
| `worktree.py:29` (docstring example) | `scan_path` | `None` |

`grep -rn "DockerSandbox(" src/` returns only docstring occurrences
(`docker_sandbox.py:109`, `scanner.py:106`, `scanner.py:328`); every real
instantiation is in `tests/test_docker_sandbox.py`. **ADR-013's container
isolation is therefore not in force on either path today** — the mechanism is
built, unit-tested, digest-pinned, and unused.

**LIVE CONFIRMATION [2026-07-28]:** `command -v docker` inside the running
webhook container returns nothing — no Docker CLI, and Fly machines expose no
daemon. Option A of item 22 therefore requires an execution-host decision, not
a code change. Confirmed on the live host, not inferred from the Dockerfile.

**Compounding constraints:** (a) `BASE_IMAGE` still pins
`patchward-scanner:0.1.0@sha256:578a8147…` with the legacy
`repomend-entrypoint` — BACKLOG 17's un-rebuilt image; (b) the Fly host has no
Docker CLI or daemon (`docker/webhook.Dockerfile` installs only `git` and
`ca-certificates`), so wiring the sandbox in on the hosted path needs an
execution-host decision, not just a code change.

**Owner:** Directing-Engineer decision (scope + host), then agent-startable.

## 27. Hosted `ANTHROPIC_API_KEY` is not an Anthropic key — Fix-Gen 401s before Gate 3 is ever reached (surfaced 2026-07-28, Session 026 close, live container read; TWO values rejected the same evening — a 9-char stub, then a 110-char credential from a different service)

**STATUS: CLOSED 2026-07-29 (Session 027)** — Yehor re-set the secret with a real
Anthropic key (a 4th value; the prior three all 401'd — a 9-char stub, a 110-char
foreign credential, and a third rejected on 2026-07-29, `req_011CdWa5on6JfoSxS2MGxP3h`).
The new key was validated LOCALLY before deploy (`models.list()` → OK), then set
via `fly secrets set`, rolling-updated on machine `7841600fd5e7e8`, and
re-confirmed on the RUNNING image: `python -c "...models.list(); print('ANTHROPIC
KEY OK')"` → `ANTHROPIC KEY OK`. Fix-Gen can now authenticate on the hosted path.
STILL OPEN AND YEHOR-OWNED (tracked here, does not block 27's closure): rotate the
unidentified 110-char credential at its source. Original entry preserved below. ↓

**Status:** OPEN — **CONFIRMED Tier 0**, functional launch blocker, UPSTREAM of
both of item 21's defects. Belongs to the same investigation unit as 21.
The fix is a Fly secret re-set (Yehor only), not a code change.

**The finding:** a credential-presence read inside the running container
(`fly ssh console -a patchward-webhook`, machine `7841600fd5e7e8`) reported
`ANTHROPIC_API_KEY  SET  len=9`. No value was printed or observed. A valid
Anthropic API key is ~100+ characters and begins `sk-ant-api03-`; nine
characters cannot be one.

**CONFIRMED BY LIVE API CALL [2026-07-28, same session]:** inside the running
container, `python -c "import anthropic; anthropic.Anthropic().models.list()"`
→ `anthropic.AuthenticationError: Error code: 401 - {'type': 'error', 'error':
{'type': 'authentication_error', 'message': 'invalid x-api-key'}, 'request_id':
'req_011CdUpKqhwSQoJufxCitjcZ'}`. Both links are now Tier 0: the length
(measured in the process) and the invalidity (rejected by Anthropic's own API
from the deployment itself). No inference remains in this item.

**Therefore, established as fact:** the hosted webhook cannot call the Anthropic
API at all. Fix-Gen fails on its FIRST request, every run, for every repo. This
is the earliest failure on the hosted path — earlier than the dead
`github_token` param and earlier than Gate 3's pytest FAIL, both of which sit
downstream of a Fix-Gen result that never arrives.

**Why it outranks the other two defects on this path:** `webhook.py:318` guards
only on falsiness (`if not ANTHROPIC_API_KEY: logger.error(...)`), and a 9-char
string is truthy, so the guard passes. The pipeline then constructs
`FixGenSubagent(api_key=...)` and the first Anthropic call fails
authentication. Fix-Gen never produces a fix → verify is never reached → Gate 3
never runs → no PR. It fires BEFORE the pytest defect, which means the hosted
path has been non-functional at an even earlier stage than item 21 supposed.

**FIX ATTEMPT 1 — DELIVERED BUT DID NOT FIX [2026-07-28, same evening]:** Yehor
ran `flyctl secrets set ANTHROPIC_API_KEY=…`; the rolling update reported
`Machine 7841600fd5e7e8 [app] update succeeded` and `/healthz` returned
`{"status":"ok"}` on the restarted machine. The new value DID reach the process
— an in-process read returned `length: 110`, so delivery is not the problem —
but `models.list()` still returned `401 invalid x-api-key`, with a NEW request
id (`req_011CdUqmbwJFzk9S97aPP1eP`, distinct from the original
`req_011CdUpKqhwSQoJufxCitjcZ`), proving a fresh call rather than a cached
result.

**Diagnosis — the secret does not contain an Anthropic key at all.** Checks run
in-process, printing only booleans and lengths, never any part of the value:
- Contamination RULED OUT: raw length == stripped length (110), no leading or
  trailing whitespace, no whitespace anywhere, no quote at either end, no
  non-ASCII. The PowerShell-quoting hypothesis is refuted.
- Prefix sweep against ten credential families — Anthropic (`sk-ant-`), OpenAI
  project/legacy, GitHub PAT/classic/app, Langfuse public/secret, Fly, Slack —
  **all False**, including `sk-ant-`. Every Anthropic key begins `sk-ant-api…`
  or `sk-ant-admin…`; this does not.
- Shape: 110 chars, 0 dots (not a JWT), not all-hex, not base64url-only,
  contains both `-` and `_` plus at least one character outside that alphabet.

**Conclusion:** a well-formed credential belonging to some OTHER system was
placed in this secret. The 401 is not Anthropic rejecting an Anthropic key; it
is Anthropic being handed a credential that was never theirs.

**Identification deliberately NOT pursued further.** Each additional probe
leaks more shape about a live credential while yielding less, and identifying
it belongs to Yehor's own records, not to character-by-character narrowing from
a session. Logged as a boundary held on purpose, not an unfinished check.

**SECURITY CONSEQUENCE, independent of the Anthropic fix:** whatever that
credential is, it has been sitting in a production environment variable and is
therefore exposed on the Gate 3 inheritance path (items 22 and 25). It should
be treated as compromised-by-exposure and ROTATED AT ITS SOURCE. This also
widens item 25's blast radius to include a credential neither party can name —
worth stating plainly rather than filing as an Anthropic-key problem.

**Fix (still open, Yehor only):** `flyctl secrets set ANTHROPIC_API_KEY=…` with
a genuine `sk-ant-api03-…` key, then re-run the `models.list()` check. Also
worth tracing where the mystery value came from — if it was pasted from
somewhere, the same paste may have reached another secret.

**Owner:** Yehor — secret re-set, plus rotation of the unidentified credential.
The startup guard is a separate unit: see item 28.

## 28. `webhook.py:318` validates the Anthropic credential by FALSINESS ONLY — two different broken secrets passed startup in one evening (NEW, surfaced 2026-07-28, Session 026 close)

**STATUS: PATCH PREPARED 2026-07-29 (Session 027), NOT YET LANDED** — implemented
and tested in a clean clone (full suite 526 passed / 90.75%; +9 tests). Delivered
as `backlog28_startup_credential_guard.patch` (in repo root). Adds
`_validate_credential_shapes()` wired via a FastAPI `lifespan`, failing the boot
loudly on a present-but-malformed secret (validates `sk-ant-` prefix, numeric
App ID, PEM/base64 key shape; absent → warn only; no value ever logged). Existing
webhook tests use `TestClient` WITHOUT a context manager, so they never trigger
the lifespan → zero regressions. NOT committed as of close: working tree +
`origin` both at `f02ad21`. TWO YEHOR DECISIONS deliberately excluded from the
patch: (a) should ABSENCE of a required credential also fail the boot (I only
fail on present-but-malformed); (b) should `/healthz` assert credential validity.
Original entry preserved below. ↓

**Status:** OPEN — agent-startable, one-line core fix, and it has **two live
occurrences** rather than a hypothetical justification. Split from item 27
deliberately: 27 is a secret to be re-set (Yehor), 28 is code to be changed
(agent) — same §2 discipline that split 21 from 19.

**The finding:** the guard reads, in substance,
`if not os.environ.get("ANTHROPIC_API_KEY"): logger.error(...)`. It rejects
exactly one value — the empty string — which is the one failure mode nobody
actually hits. Everything else passes startup and fails later, at the first
API call, inside a pipeline run, where the failure is attributed to Fix-Gen
rather than to configuration.

**The two occurrences, both observed on the live deployment on 2026-07-28:**
1. A **9-character** value (item 27's original finding). Truthy → passed.
2. A **110-character credential from a different service** (item 27's failed
   fix attempt). Truthy → passed.

Both would have been rejected at startup by a single predicate:

```python
if not key.startswith("sk-ant-"):
    raise RuntimeError("ANTHROPIC_API_KEY is not an Anthropic API key")
```

**Why this matters beyond tidiness:** the hosted webhook has been deployed and
"healthy" — `/healthz` green throughout — while holding an unusable credential.
A liveness probe that does not touch the dependency it needs will report green
over a broken configuration indefinitely. That is precisely how three
independent defects sat undetected on this service (see item 21).

**Proposed scope (keep it small and separately reviewable):**
- Prefix/shape validation at startup for `ANTHROPIC_API_KEY`, failing loudly.
- Consider the same treatment for the other required secrets
  (`GITHUB_APP_ID`, `GITHUB_APP_PRIVATE_KEY_B64`, `GITHUB_WEBHOOK_SECRET`) —
  each currently has the same falsiness-only or absent guard.
- Do NOT log any part of a credential value in the failure message. The
  message names the variable and the expected shape, never the observed value.
- Open question for Yehor, not decided here: should `/healthz` also assert
  credential validity (a startup-time probe result cached, not a per-request
  API call), so a green health check means "can actually work" rather than
  "process is running"? That is a design choice with cost, not an obvious yes.

**Owner:** agent-startable for the guard; the `/healthz` semantics question is
Yehor's.
