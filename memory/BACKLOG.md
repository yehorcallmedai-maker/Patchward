# BACKLOG — priority-ordered
Seeded 2026-07-13 from `memory/BUILD_PLAN_2026-07-10.md` §6 (WSJF
resolution, approved by Yehor 2026-07-13) plus this session's narrowed
Phase 9 Exposure Gate findings. Re-scored weekly per BUILD_PLAN §7 cadence
once that cadence actually starts — this is the seed, not a steady-state
process yet.

Framework: WSJF (Cost of Delay ÷ Job Size) + an explicit irreversibility
check, per BUILD_PLAN §6.

---

## 1. State Reconstruction Audit close-out — CLOSED, full history archived
See `memory/BACKLOG_RETROSPECTIVE.md`.

## 2. `fly.toml` drift resolution — CLOSED, false positive — full history archived
See `memory/BACKLOG_RETROSPECTIVE.md`.

## 3a. Verifier gate gap — broken fix passed all 3 gates — CLOSED 2026-07-14, commit `b2559a5` — full history archived
See `memory/BACKLOG_RETROSPECTIVE.md`.

## 3b. `GITHUB_TOKEN` cannot create PRs — CLOSED 2026-07-14, token permission fixed — full history archived
See `memory/BACKLOG_RETROSPECTIVE.md`.

## 3c. CLI misreports failed PR creation as success — CLOSED 2026-07-14, commit `190fb01` — full history archived
See `memory/BACKLOG_RETROSPECTIVE.md`.

## 3d. "requires login" invalid branch name — crash CLOSED 2026-07-14 (upstream root cause still unconfirmed) — full history archived
See `memory/BACKLOG_RETROSPECTIVE.md`.

## 3. Stage 1 — E2E pipeline test against an owned repo — COMPLETE — full history archived
See `memory/BACKLOG_RETROSPECTIVE.md`.

## 4. Re-verify test suite on current `main` — CLOSED 2026-07-13 — full history archived
See `memory/BACKLOG_RETROSPECTIVE.md`.

## 5. Phase 9 Exposure Gate — FULLY CLOSED, committed and pushed through `3d1ec08` — full history archived
See `memory/BACKLOG_RETROSPECTIVE.md`.

## 6a. Fix `patchward.toml.example` — CLOSED 2026-07-14 — full history archived
See `memory/BACKLOG_RETROSPECTIVE.md`.

## 6. `docs/architecture/patchward-webhook-billing-design.md` decision — CLOSED 2026-07-14, scrubbed not recreated — full history archived
See `memory/BACKLOG_RETROSPECTIVE.md`.

## 7. `project_open_tasks.md` reconciliation — CLOSED 2026-07-14, folded and archived — full history archived
See `memory/BACKLOG_RETROSPECTIVE.md`.

## 7a. Structured PR template — CLOSED 2026-07-14, already substantively implemented — full history archived
See `memory/BACKLOG_RETROSPECTIVE.md`.

## 7b. Surface `risk_class` in the PR body — CLOSED 2026-07-14, commit `53cd052` — full history archived
See `memory/BACKLOG_RETROSPECTIVE.md`.

## 7c. `.dockerignore` untracked — CORRECTED 2026-07-14, claim was false, already tracked — full history archived
See `memory/BACKLOG_RETROSPECTIVE.md`.

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

## 8. callmed-landing rename — CLOSED 2026-07-22 (Session 022) — full history archived
See `memory/BACKLOG_RETROSPECTIVE.md`. New backlog candidate surfaced
there, not acted on: the real Patchward codebase's own ~59 internal
"repomend" references — see item 16.

## 9. PyPI Trusted Publisher — CLOSED 2026-07-22 (Session 022), Tier-0 end-to-end — full history archived
See `memory/BACKLOG_RETROSPECTIVE.md`.

## 10. "Mirror Pass Tier 2" — REMOVED 2026-07-15 (Session 018) — never belonged in this file — full history archived
See `memory/BACKLOG_RETROSPECTIVE.md`.

## 11. Stage 2 — authorized third-party E2E test (COMPLETE 2026-07-14 — PR #1 on ssh-audit) — full history archived
See `memory/BACKLOG_RETROSPECTIVE.md`.

## 13. Fix-Gen lacks an explicit "not a real issue, decline" path — CLOSED 2026-07-15 — full history archived
See `memory/BACKLOG_RETROSPECTIVE.md`. `.claude/agents/*.md` naming
sub-item also CLOSED same day, commit `7effbad`, archived together.

## 12. Regulatory flags — CRA / GDPR classification — PAUSED BY YEHOR (BUDGET/TIMING, PRE-REVENUE) — REOPENS ON HIS OWN INITIATIVE, NO FIXED DATE (2026-07-24, Session 024; settled 2026-09-02, Session 044) — COMPRESSED 2026-09-02, full session-by-session history moved to `memory/BACKLOG_RETROSPECTIVE.md`
**WSJF: no longer urgent — paused, not abandoned.** Original goal: get
Patchward's CRA Annex III classification and a lightweight GDPR
DPIA/TTL policy on `installations_db.py` confirmed by someone qualified
before any paid Marketplace listing.

**Settled status (Session 044, 2026-09-02):** NJORD Law Firm (Nis Peter
Dall) was engaged, met, and quoted a narrowly-scoped Article 14
step-1 assessment (price filed privately, not tracked in this public
repo). NJORD directly answered this item's open sufficiency question:
**2026-09-11 is not a filing/documentation deadline — it is the date
Article 14's reporting *rules* begin to apply.** An actual reporting
obligation (with its own 24h/72h/14-day sub-deadlines) would only
arise if Patchward becomes aware, after that date, of an actively
exploited vulnerability or serious security incident. Full verbatim
Danish quotes + EN gloss for both NJORD's scope answer and this
sufficiency answer: `memory/BACKLOG_RETROSPECTIVE.md`.

**Yehor's own decision, same day (thread `1a062be715af4ce6`, verified
via `get_thread`, 2026-09-02 17:39 CPH):** both offered workstreams
(FixProve terms/privacy Fase 1, and this item's Article 14 step-1
assessment) are **paused indefinitely** — timing/economics in a
pre-revenue phase, explicitly not dissatisfaction with NJORD's offer
(called "fair and well-scoped"). He'll return "when the foundation is
in place," assuming (his own stated assumption, not NJORD's
commitment) the same estimates will still apply. No fixed revisit
date — reopens on Yehor's own initiative, tied to revenue/funding.

**What stands on record regardless of the pause:** the technical
briefing packet (`memory/BACKLOG12_counsel_briefing_packet_2026-07-24.md`)
remains Yehor's own preliminary, good-faith self-assessment — **not a
substitute for qualified legal review**, just a documented starting
position for whenever counsel is re-engaged. NJORD's Article 14
timeline clarification above is the most current qualified-source
information this project has on the question, short of full formal
advice.

**Also on record from NJORD's same email, out of this item's scope but
logged so the three-offer email isn't misread as CRA-only if
revisited:** FixProve privacy policy/terms quote, and an unprompted
ApS company-structuring recommendation — both prices filed privately.

**Full history** (NJORD vetting, the meeting, the original briefing
packet's 6-part contents, every intermediate email exchange session by
session, the two-thread-split correction, and the H40 redaction
lessons this item's back-and-forth produced): `memory/
BACKLOG_RETROSPECTIVE.md`.

**Owner: Yehor**, for whenever he chooses to reopen this — no
agent-startable work remains on BACKLOG 12 at this time.

---

## 14. Stray pre-rename branches on `ssh-audit` — RESOLVED 2026-07-15, origin confirmed — full history archived
See `memory/BACKLOG_RETROSPECTIVE.md`. Recommendation left to Yehor:
the two stale branches on his fork are safe to delete or safe to leave.

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

## 16. Internal `Repomend`-naming debt in the real Patchward codebase — TRIAGED AND EXECUTED 2026-07-23 (Session 023), pushed as commit `e4f3cca` (corrected: header previously said "staged uncommitted" — stale, per `.strategy/STRATEGY.md`'s own Session 023 close record) — full history archived
`RepomendConfig`→`PatchwardConfig` rename across 12 files, test-function renames, transitional dual-naming kept for the security-relevant `REPOMEND_NETWORK_POLICY`/`PATCHWARD_NETWORK_POLICY` env var (fail-closed egress policy, traced source-level). 480/2/15 pytest pass count unchanged. Docker image tag rename deferred to item 17 on purpose. See `memory/BACKLOG_RETROSPECTIVE.md`.

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

## 19. `GITHUB_TOKEN` reaches disk (webhook path) and unfiltered logs (both paths) — CLOSED 2026-07-27 (Session 025) — full history archived
Trace found token persisted in cloned `.git/config` on the hosted webhook
path + unfiltered git stderr/exception text at four log/echo sites. Fixed:
tokenless clone URL + credential helper, `scrub_text()` at all sinks. Three
adversarial review passes found and closed five more findings (argv/proc
leak, `TimeoutExpired` capture, cross-thread scrub race, regex boundary
bug, credential-helper reset gap); Pass 3 returned 0 leaks. Spun off items
21-24. See `memory/BACKLOG_RETROSPECTIVE.md`.


## 20. `callmed-landing`'s corrected copy appeared not to be live at the plain URLs — CLOSED same day, FALSE ALARM — full history archived
Suspected CDN staleness at bare URLs (`/`, `/security`) turned out to be a
`WebFetch` tool artifact, not a production issue. Real Chrome browser read
+ Cloudflare `cf-cache-status: DYNAMIC` + dashboard deployment timestamp
all confirmed the corrected copy was live the whole time. Root cause of
the tool's false "stale" report not fully determined. See
`memory/BACKLOG_RETROSPECTIVE.md`.

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

## 25. `_CREDENTIAL_KEYS` omits four credentials that ARE in `os.environ` on the hosted path — CLOSED 2026-07-29 (Session 027) — full history archived
GitHub App private key/ID + webhook secret were readable from `os.environ`
and unscrubbed — cross-tenant blast radius, gated both options of item 22.
Shipped commit `f02ad21`: all four added to `_CREDENTIAL_KEYS`. Live
container read confirmed the finding before the fix and confirmed the fix
after. See `memory/BACKLOG_RETROSPECTIVE.md`.

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

## 27. Hosted `ANTHROPIC_API_KEY` is not an Anthropic key — Fix-Gen 401s before Gate 3 is ever reached — CLOSED 2026-07-29 (Session 027) — full history archived
Live container read + API call proved the hosted secret held a 9-char stub,
then an unidentified 110-char foreign credential — both 401'd. Yehor
re-set with a real, locally-validated Anthropic key; confirmed working on
the running image. Unidentified credential exhaustively searched for
(2026-08-07) and not found anywhere reachable — treated as
compromised-by-exposure, rotate at source only if ever recognized. See
`memory/BACKLOG_RETROSPECTIVE.md`.

## 28. `webhook.py:318` validates the Anthropic credential by FALSINESS ONLY — two different broken secrets passed startup in one evening — CLOSED 2026-08-08 (Session 032) — full history archived
Shape/prefix validation at startup, wired via FastAPI `lifespan`, so a
present-but-malformed credential (item 27's two occurrences) now fails
boot loudly instead of surfacing later as a Fix-Gen failure. Shipped
commit `f653e77` after three adversarial review rounds, real gate
565/3/91.20%. Known cosmetic follow-up (BOM/mojibake, comments-only) —
not a reopen. Absence-fails-boot and `/healthz` depth questions deferred
to Yehor, never decided. See `memory/BACKLOG_RETROSPECTIVE.md`.

## 29. `pipeline.py` records "pr_opened" even when PR creation fails (status != "opened") — FIXED AND DEPLOYED 2026-08-07 (Session 031) — full history archived
Surfaced by adversarial review of item 21's fix: a successful push could
be followed by a silent PR-creation failure, leaving a force-pushed
branch on the customer's repo with no error trail anywhere. Fixed to
mirror `cli.py`'s three-way status handling (`pr_opened`/`pr_already_open`/
`pr_failed`), commit `66680c0`, 8/8 mutations caught, live-verified on the
deployed container's own source. See `memory/BACKLOG_RETROSPECTIVE.md`.
