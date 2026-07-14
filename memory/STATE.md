# STATE — verified project facts only
# Every line carries: (claim) — (evidence) — (tier) — (date checked) — (verified by)
# The agent may read this file freely. The agent does NOT write to it going
# forward without your review — this first version is a bootstrap draft from
# the 2026-07-13 State Reconstruction Audit and needs your sign-off like
# everything else the audit produces.

## Phase
Phase 8 — Reconciliation (State Reconstruction Audit) — **CLOSED**.
Tag `state-audit-2026-07` created and pushed, confirmed pointing at
`27d0ba3b5d00427ca473c660b9932c994d2a33b4` via `git ls-remote origin
refs/tags/state-audit-2026-07` (Tier 0) — 2026-07-13 — Yehor executed,
agent verified. **Correction, same day:** this line previously said the
tag was "not yet created" — that was true when first written, then went
stale the moment the tag actually landed and this file was never updated
to match. Left visible rather than silently fixed, per this project's
established correction convention (see ADR-029's amendment). Session 013
continued past the audit into Stage-1 E2E testing (see below) — Phase 9
work has not formally started; treat Phase 8's closure as "audit
artifacts landed," not "all Phase 8-adjacent questions answered."

## Repo
`main` @ `27d0ba3b5d00427ca473c660b9932c994d2a33b4` — confirmed via
`git ls-remote origin main`, matches the state-audit tag above — Tier 0 —
2026-07-13 — agent. (Supersedes the earlier `d4569d4...` line in this
file, which was the pre-audit-commit HEAD.) **Not yet current as of this
close-out pass** — this session's post-audit work (STATE.md/BACKLOG.md
updates, the Stage-1 report) is still uncommitted; see the session-close
document for the pending commit.

## Deployed services
`patchward-webhook.fly.dev` — `/healthz` → `{"status":"ok"}` — direct HTTPS
GET, not proxied — Tier 1 — 2026-07-13 — agent. Checked twice previously in
Session 012 (2026-07-10), also OK both times.

## Working-tree state (as of 2026-07-13, corrected)
**Correction, same day:** this section originally claimed `fly.toml` had
drifted from committed `HEAD` (evidence: `git diff HEAD -- fly.toml` run
in the agent sandbox, mis-labeled Tier 0). **That claim was false.**
Yehor ran `git status` and `git diff -- fly.toml` on his own machine
(2026-07-13) — both came back clean. `fly.toml` was never modified.
Re-running the same sandbox `git status` afterward now shows nearly the
entire `src/patchward/` tree as modified, which is definitely also false.
**Conclusion: the agent sandbox's `git status`/`git diff` against the
working tree cannot be trusted on this mount, independent of whether the
file was edited this session.** This is a stronger finding than the prior
"don't trust bash `cat`/`wc`/`diff` for files edited earlier this
session" rule (Session 012) — it now applies to files nobody touched at
all. `git log` / `git ls-remote` (ref/object reads) remain trustworthy;
`git status` / `git diff` (working-tree comparisons) do not, full stop,
on this mount. Only Yehor's own machine is authoritative for working-tree
state going forward — no exceptions, no "looks plausible so probably
fine."

Real state, confirmed on Yehor's machine 2026-07-13: only
`memory/architectural_decisions.md` (this session's ADR additions) and
`tests/fixture_repo` (pre-existing dirty submodule, unrelated, carried
from Session 012's "worth a look whenever convenient" list) show as
modified. `.dockerignore`, `docs/keystones/`, `memory/BACKLOG.md`,
`memory/SESSION_STRATEGY_2026-07-13.md`, `memory/STATE.md` are untracked
(new, as expected).

## Tests
**421 passed, 2 skipped, 15 deselected — 90.01% coverage** (threshold 80%,
reached) — `uv run pytest --cov`, run by Yehor on his own machine — Tier 0
(local exit code + output, not proxied) — 2026-07-13 — Yehor. Supersedes
the pre-rename "371 passed, 89%" figure in old memory files, which was a
historical fact about the 2026-06-23 state only.

**Environment defect found and fixed same day, worth carrying forward:**
the first `uv run pytest --cov` attempt failed with `error: uv trampoline
failed to canonicalize script path` — not a test failure. Root cause:
`.venv/` had last been built 2026-06-23, before both the RepoMend→Patchward
rename (`c27ea40`, 2026-07-07) and the outer project folder's rename to
`D:\Dev\Projects\Patchward`. uv's Windows console-script launchers embed
absolute paths at install time; the stale venv's launchers pointed at
paths that no longer existed. **Fix:** `Remove-Item -Recurse -Force .venv`
then `uv sync --all-extras` (the `--all-extras` flag matters — without it,
`test_webhook.py`/`test_github_app_auth.py`/`test_installations_db.py`
fail to collect, since the `webhook` optional-dependency group wouldn't be
installed). `uv.lock` is tracked, so the rebuild pinned the same versions,
not a different environment. **Action item for future sessions:** rebuild
`.venv` after any future project directory move/rename, before trusting a
`uv run` failure as a real code problem.

## Webhook security posture (`src/patchward/webhook.py`, commit `0bb0286`)
- HMAC signature validation on `/webhooks/github`: implemented,
  `hmac.compare_digest` (timing-safe), verified before payload parsing —
  read of `webhook.py` L70-87 — Tier 0 — 2026-07-13 — agent. Tested in
  `tests/test_webhook.py` (existence confirmed, contents not re-read
  line-by-line this session).
- Unrecognized webhook event types: acknowledged (HTTP 200,
  `{"status":"ignored"}`), not rejected — deliberate, per inline rationale
  comment (GitHub disables a webhook after repeated non-2xx responses) —
  read of `webhook.py` L241-244 — Tier 0 — 2026-07-13 — agent. Formalized
  as ADR-032 (see `memory/architectural_decisions.md`), approved by Yehor
  2026-07-13.
- Rate limiting / request body size limits: **not present** — grep of
  `webhook.py` — Tier 0 — 2026-07-13 — agent. Open item, see BACKLOG.md.
- Structured logging of `X-GitHub-Delivery` header: **not present** — logs
  `event`/`action` only — grep of `webhook.py` — Tier 0 — 2026-07-13 —
  agent. Open item, see BACKLOG.md.
- `pip-audit` scoped to the `webhook` optional-dependency group
  (`fastapi`, `uvicorn[standard]`, `pyjwt[crypto]`, `httpx` —
  `pyproject.toml` lines 25-29): **no evidence a scoped run has ever
  happened** — Tier 0 (absence confirmed by file read, no CI job found for
  it) — 2026-07-13 — agent. Open item, see BACKLOG.md.

## Known documentation gap — RESOLVED 2026-07-14 (scrubbed, not recreated)
`src/patchward/github_app_auth.py`, `installations_db.py`, `webhook.py`,
and `fly.toml` cited `docs/architecture/patchward-webhook-billing-design.md`
by path — five total citations across four files, not the three
originally counted (the earlier "three" figure missed `fly.toml`'s and
undercounted `installations_db.py`, which had two separate citations).
This file never existed in the repo — `docs/architecture/` directory is
absent — confirmed via `ls docs/architecture` (No such file or
directory) — Tier 0 — 2026-07-13 — agent.

**Decision (2026-07-14):** scrub, don't recreate. ADR-028 and ADR-030
each explicitly document that they were reconstructed from git
archaeology *because* no separate design doc was found — meaning the
ADRs already are the canonical, complete record of what this file would
have said. A recreated `docs/architecture/` file would just be a second
copy of the same facts, with no mechanism to stay in sync if either ADR
is later amended. All five citations rewritten to point at
`memory/architectural_decisions.md`'s ADR-029/ADR-030 instead of the
dead path. See `memory/BACKLOG.md` item 6 for full reasoning.

## PyPI Trusted Publisher CI
`.github/workflows/publish.yml` exists — triggers on GitHub Release
publish or manual dispatch, builds via `uv build`, publishes via
`pypa/gh-action-pypi-publish@release/v1` with OIDC (`id-token: write`,
no stored PyPI token) — read of file — Tier 0 — 2026-07-13 — agent.
**UNVERIFIED**: whether PyPI's own Trusted Publisher configuration for
the `patchward` project has actually been set up on PyPI's side (this is
an external, PyPI-side setting this session cannot check) and whether the
workflow has ever actually run. No release has been tagged as of
`d4569d4`.

## Local CLI config defect found and fixed (2026-07-13, pre-Stage-1 check)
`patchward.toml` (local, gitignored, not in git history) still had a
`[repomend]` top-level section header from before the rename.
`config.py`'s `load_config()` reads `raw.get("patchward", {})` — with the
old header, the entire section (`repo_path`, `semgrep_rules`, `db_path`,
langfuse settings) was silently dropped, and `repo_path` is a required
field with no default, so `patchward scan`/`patchward fix` would have
hard-failed at config load — confirmed by reading `config.py` directly
(Tier 0), not by running it and guessing. Also found: `repo_path` pointed
at `D:/Dev/Projects/RepoMend` (doesn't exist — the project directory
itself was renamed to Patchward), and `[github].repo` defaulted to
`"Patchward"` — meaning an unmodified run would have targeted this repo
itself for a PR, not an intended fixture. **Fixed directly** (safe — local
file, not tracked by git): section header corrected to `[patchward]`,
`repo_path` pointed at `tests/fixture_repo`, `[github].repo` set to
`repomend-fixture`. Also worth noting: `patchward.toml.example` (the
committed Phase 7 distribution deliverable, ADR-025) has the same
`[patchward]`-section gap — it has no `repo_path` documented at all, and
an unrelated `[anthropic]` section that doesn't match `config.py`'s
actual schema. Not fixed this session (doesn't block Stage-1, since
Stage-1 uses the real `patchward.toml`, not the example) — flagged in
`memory/BACKLOG.md` as a real, separate defect.

## Fixture repo vulnerability set — corrected from stale documentation
Old memory files (Session 002, `docs/intake_phase1.md`) document the
fixture's three planted vulnerabilities as subprocess-shell-true (L24),
insecure-hash-md5 (L30), ssl-wrap-socket-deprecated (L37). **The actual
committed content as of 2026-07-13** (`git show HEAD:vulnerable.py` in
`tests/fixture_repo`, Tier 0) is subprocess-shell-true (L24),
eval-on-untrusted-input (L30), hardcoded-password (L37) — a different
pair at lines 30/37, changed at some undocumented point after Session 002
(likely during the Phase 4 D-P4-02/D-P4-03 fixture repair, commit
`6e77570`, which the session log describes only as a line-position/
encoding fix, not a content change — the discrepancy itself wasn't
logged at the time). Session 002's own scanner probe found `eval` and
"hardcoded password assignment" as **non-firing** rules under `p/python`
— meaning it's not yet confirmed whether the current fixture actually
produces 3 semgrep findings or fewer. **Not asserting an answer either
way — this needs an actual `patchward scan` dry run to confirm**, not
another guess layered on top of the last one. `tests/fixture_repo`'s only
local uncommitted change is a one-line, non-functional docstring edit
("testing RepoMend" → "testing patchward") — confirmed via `git diff HEAD`
— which doesn't affect what a git-worktree-based scan would see (worktree
checkout reads from `HEAD`, not the dirty working copy).

## Stage-1 E2E test — run and documented, 2026-07-13
Full report: `docs/keystones/stage1_e2e_test_2026-07-13.md`. 3/5 findings
verified by Fix-Gen+Verifier; all 3 branches confirmed pushed to the real
`repomend-fixture` remote via `git ls-remote` (Tier 0); 0 PRs opened
(GitHub API 403 on PR creation — token permission gap). Of the 3
"verified" fixes, direct inspection of the pushed diffs (not just
Fix-Gen's self-reported description) confirmed 2 are correct and 1 is
objectively broken (deletes a needed import, function would raise
`NameError` at runtime) despite passing all 3 Verifier gates — a real,
structural gap in Gate 1/Gate 3 coverage, not a fixture-specific fluke.
See `memory/BACKLOG.md` items 3a-3d for the four concrete follow-ups this
produced. Pipeline itself (scan → Fix-Gen → Verifier → git push) is
confirmed working end-to-end post-rename; the PR-opening step and the
Verifier's correctness guarantee both need attention before Stage 2 or
wider exposure.

## Known UNVERIFIED (do not treat as fact until promoted)
- Full test suite count/coverage post-rename — needs Yehor to run on Windows
  (RESOLVED 2026-07-13/14: 421 then 439 passed on Yehor's real machine
  across this session and the next — see Tests section above and
  BACKLOG 3a/3c/3d)
- `fly.toml` restore — this line was stale: BACKLOG item 2 already
  closed this 2026-07-13 as a false positive (no restore was ever
  needed; Yehor's own `git status`/`diff` showed the file was never
  modified). Left uncorrected until now — caught while touching this
  section for an unrelated reason, not itself investigated fresh.
- `docs/architecture/patchward-webhook-billing-design.md` — RESOLVED
  2026-07-14: decision made to scrub references rather than recreate
  (see BACKLOG item 6). The "real loss vs. speculative reference"
  question is now moot either way, since the resolution doesn't depend
  on which explanation is true.
- PyPI-side Trusted Publisher configuration status
- ClinInsight/Databutton LinkedIn DM replies (carried from Session 012,
  still unconfirmed, no tool access to check)

---
**Handoff note on the audit tag — RESOLVED 2026-07-13:** the tag was
created and pushed by Yehor after reviewing and committing the audit's
file set, per the recommendation this note originally made. Verified via
`git ls-remote` (see "Repo" section above). Left in place as a record of
the recommendation that was followed, not as an open action item.
