# STATE — verified project facts only
# Every line carries: (claim) — (evidence) — (tier) — (date checked) — (verified by)
# The agent may read this file freely. The agent does NOT write to it going
# forward without your review — this first version is a bootstrap draft from
# the 2026-07-13 State Reconstruction Audit and needs your sign-off like
# everything else the audit produces.

## Phase
Phase 8 — Reconciliation (State Reconstruction Audit), in progress —
tag `state-audit-2026-07` not yet created (pending — see handoff note at
bottom of this file) — 2026-07-13 — Claude (agent), pending Yehor confirmation.

## Repo
`main` @ `d4569d40537b0f84d352a6ee25612a81a362a710` — confirmed via
`git ls-remote origin main` matching local `git rev-parse HEAD` — Tier 0 —
2026-07-13 — agent.

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
**UNVERIFIED as of 2026-07-13.** `uv run pytest --cov` has not been run this
session (requires Windows per RULE-4, sandbox has no network for `uv`). The
figure "371 passed, 89% coverage" in old memory files is a historical fact
about the pre-rename (2026-06-23) state only — do not treat as current.
**Action for Yehor:** run the suite and report count/coverage; this line
gets promoted once you do.

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

## Known documentation gap
`src/patchward/github_app_auth.py`, `installations_db.py`, and
`webhook.py` all cite `docs/architecture/patchward-webhook-billing-design.md`
by path in KS-TRACE header comments (e.g. "P1.3 in
docs/architecture/patchward-webhook-billing-design.md"). **This file does
not exist in the repo** — `docs/architecture/` directory is absent —
confirmed via `ls docs/architecture` (No such file or directory) — Tier 0 —
2026-07-13 — agent. Either the design doc was written outside version
control and never committed, or the KS-TRACE comments were written
speculatively and the doc never materialized. Not blocking — the code
itself is self-documenting enough to have reconstructed ADR-028/030 from
git archaeology alone — but worth a decision: recreate the doc from the
ADRs, or scrub the dead references. Flagged in BACKLOG.md.

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

## Known UNVERIFIED (do not treat as fact until promoted)
- Full test suite count/coverage post-rename — needs Yehor to run on Windows
- `fly.toml` restore — approved, not yet executed
- Whether the `docs/architecture/patchward-webhook-billing-design.md`
  gap is a real loss or a speculative reference that was never fulfilled
- PyPI-side Trusted Publisher configuration status
- ClinInsight/Databutton LinkedIn DM replies (carried from Session 012,
  still unconfirmed, no tool access to check)

---
**Handoff note on the audit tag:** `git tag state-audit-2026-07 HEAD` is a
git write and per standing project rule is not run from the agent sandbox.
Recommend Yehor create this tag once he's reviewed and committed this
audit's file set (STATE.md, the 6 new ADRs, the Consolidated Keystone
Report, BACKLOG.md) — tagging the resulting commit, not the current
`d4569d4`, so the tag actually marks "audit complete" rather than
"audit started."
