# Session Close — Patchward — 2026-07-28 (Session 026)

## Gate status

| Claim | Pass 1 | Pass 2 | Verdict |
|---|---|---|---|
| Resume prompt: `main @ 9e70f36` | mount `git log` → `23dc9bd` | cloud `git ls-remote` + fresh clone → `23dc9bd` | **DRIFTED** (benign: docs-only child commit) |
| Session 025 pushed clean | mount `main [origin/main]`, no ahead/behind | remote ref == local HEAD | CONFIRMED |
| Working tree clean | mount shows 55 ` M` | `git diff --stat -w` → empty; 5798 ins = 5798 del | CONFIRMED (known CRLF artifact) |
| BACKLOG 19 committed + closed | `37b3bfd` (+574/−57) and `dee84e1` (+228/−20) in `git log`, real diffs | fresh-clone `BACKLOG.md` → `**STATUS: CLOSED 2026-07-27**`, `**Owner:** CLOSED`; `git status --porcelain` → zero staged entries | CONFIRMED |
| User claim: "BACKLOG 19 is NOT committed, still staged" | contradicted by `git log` + `BACKLOG.md` at HEAD | contradicted by `ls-remote` + `git status --porcelain` | **FALSIFIED** |
| Memory files match HEAD (H8) | 6 files staged from `D:\` mount | CRLF-normalised sha256 vs fresh clone → all identical | CONFIRMED |
| Fly `/healthz` green | WebFetch → `{"status":"ok"}` | **not run** (browser check interrupted) | CONFIRMED, **one method only** |
| Fly image `sha256:ac54d18a…` running | — | — | **UNVERIFIED** (no flyctl auth in sandbox) |
| Hygiene fix pushed as `8931702` | cloud `git ls-remote origin main` → `8931702c370bbb…` | fresh clone `rev-parse HEAD` == same; `git diff --stat 23dc9bd 8931702` → 1 file, +1/−1 | CONFIRMED |
| Item 22 premise: "scanners DO route through the sandbox" | `scanner.py:320-324` — `sandbox` defaults to `None`; 4/4 production call sites omit it | `grep -rn "DockerSandbox(" src/` → docstrings only | **DRIFTED (false)** → item 26 |
| Item 22: `PATCHWARD_GIT_TOKEN` inherited by Gate 3 | `git_credentials.py:111-120` — `credential_env()` returns a copy, `os.environ` never mutated | — | **DRIFTED** — race-only via `/proc`, not direct inherit (correction in Patchward's favour) |
| Memo §5: pytest absent from hosted image → Gate 3 hard-FAILs | built the wheel, read `METADATA`: `pytest` absent; PyPI graph for `uv`/`semgrep`/`bandit`/`pip-audit` → only `pytest; extra == "test"`, not installed | executed Gate 3's exact argv against a pytest-less venv → `No module named pytest`, rc 1, **zero** hits vs the three SKIP triggers at `verifier.py:767` → FAIL | **CONFIRMED at build-recipe level (Tier 0)** |
| …that the *running* container matches its recipe | — | — | **UNVERIFIED** — `fly ssh console` → `python -c "import pytest"` still pending (confirmatory, not decisive) |
| Session 025's fix #4 = review-verified, not test-proven | `STRATEGY.md` L1320 | — | CONFIRMED (not relabelled) |
| Days to 2026-09-11 CRA date | recomputed → 45 | — | DRIFTED (prompt said ~46) |

**Calibration: 8 CONFIRMED / 11 checkable claims = 0.73.** Every drift was in an
*inherited* claim (handoff prompt, backlog entry's own premise, user
recollection), none in this session's own output. Zero false claims reached the
committed tree or the closed memory.

## Session judgment

**L3 · Artifacts (verified to exist).**
- `8931702` — item 19's origin-trace Owner line marked `SUPERSEDED`, committed
  and pushed, independently verified. One line, nothing else touched.
- `memory/BACKLOG22_gate3_scope_memo_2026-07-28.md` — 448-line scope memo,
  source-verified at HEAD, hard stop honoured (no code, no option chosen,
  nothing staged, no adversarial pass on the memo).
- BACKLOG items **25** and **26** logged; item **22**'s inverted premise
  corrected; item **21** extended with the Tier-0 §5 evidence.
- `.strategy/STRATEGY.md` — Session 026 log, calibration 0.73, heuristics
  **H13** and **H14** promoted (each on two independent occurrences),
  **H15-candidate** opened.

**L2 · Session goal.** Recorded at open: *BACKLOG 22 scope-only — source-verified
trace, credential enumeration per path, options laid out without choosing, the
disqualifier answered.* → **MET**, and exceeded on the disqualifier (Yehor's
completeness bar — "what does Gate 3 legitimately need to run" — was answered
from source: nothing extra, because Gate 3 already installs nothing and degrades
to SKIP). Not diluted: the hard stop held.

**L1 · Horizon.** Real progress, and of an uncomfortable kind. The project's
biggest obstacle was believed to be the credential boundary on the hosted path
before a Marketplace listing. This session established, at Tier 0 for the build
recipe, that **the hosted path likely cannot deliver a PR at all** — two
independent defects (item 21's dead `github_token` param, and Gate 3's
pytest-absence hard-FAIL), either sufficient alone. That reorders the board: a
functional launch blocker now outranks the security item, and the urgency of the
Gate 3 sandbox-vs-strip decision is itself contingent on whether that path
executes. This is progress by subtraction — the horizon did not move closer, but
the map got correct, which is worth more than a fix built on the old map.

## Decisions made this close

1. **Reprioritised the board**: 21+§5 as one investigation → 25 standalone → 22
   implementation. Recorded, not merely proposed.
2. **Item 25 ships standalone and first** — it gates both Option A and Option B
   of item 22, so it is not blocked by the A/B/C decision.
3. **The A/B/C Gate 3 call stays OPEN.** No lean recorded by the session,
   deliberately.
4. The scope memo is filed into `memory/` as a repo artifact, not left in chat.

## Weakest points, stated plainly

- **`/healthz` was confirmed by one method, not two.** The browser corroboration
  (H10-candidate's own discipline) was interrupted before it ran. Recorded as
  one-method rather than smoothed into a two-method claim.
- **The running Fly image is UNVERIFIED.** Its digest was not re-checked this
  session (no flyctl auth in the sandbox). The §5 finding proves the *recipe*,
  not the *container*. This is the single named gap between "very likely" and
  "confirmed" on the most consequential finding of the session.
- **The test suite was not re-run.** Success criterion 3 (green at ≥90% coverage)
  remains UNVERIFIED for the third consecutive session.
- **A destructive no-op came within one turn of being executed** on a confident
  user-asserted premise. It was caught, but the near-miss is the honest reading,
  and it is why H14 was promoted rather than logged as a one-off.
- **Item 22's own text was wrong in two places** (the sandbox-routing premise;
  the `PATCHWARD_GIT_TOKEN` inherit). Both are now corrected in `BACKLOG.md`, but
  a backlog entry written during an adversarial pass carried two false load-
  bearing claims for a full session — that is what H13 exists to catch next time.
- **BACKLOG 12 (CRA/GDPR) had zero movement.** 45 days to 2026-09-11 and it
  still awaits qualified counsel — the only hard external deadline on the board,
  and not agent-solvable.

## File manifest

**Committed and pushed this session:** `memory/BACKLOG.md` (one line) → `8931702`.

**Delivered as unstaged patches for Yehor's review — NOT committed by the session:**
- `session026-memory.patch` — `memory/BACKLOG.md` (item 22 premise correction,
  item 21 §5 evidence, items 25 + 26) and the new
  `memory/BACKLOG22_gate3_scope_memo_2026-07-28.md`.
- `session026-closeout.patch` — `.strategy/STRATEGY.md` (Session 026 log,
  calibration, H13/H14/H15-candidate) and this file.

Both verified with `git apply --check` against a pristine clone of `8931702`.
They touch disjoint files and apply in either order.

**Deliberately excluded:** any code change (§2 discipline — the session was
scope-only); any Gate 3 design choice; the `fly ssh console` confirmation (needs
Yehor's deploy access).

**Housekeeping for Yehor:** a stale empty `.git/index.lock` was left in the mount
by this session's own read-only `git status` — `del D:\\Dev\\Projects\\Patchward\\.git\\index.lock`
before the next local git write.

## Next-session opening prompt

```
Resume Patchward. Open via the session-strategy-synthesis skill, grounding in
.strategy/STRATEGY.md — re-verify fresh, do not trust as-is (claims can go
stale between sessions, and per H13/H14 that includes this prompt's own claims,
the backlog entries' own stated premises, and anything I assert from memory).

Session 026 closed clean at main @ 8931702 ("docs(memory): mark item 19's
origin-trace Owner line as superseded"), verified via cloud git ls-remote +
fresh clone + a 1-file/+1/-1 diff against 23dc9bd. Two close-out patches were
delivered unstaged (session026-memory.patch, session026-closeout.patch) —
CHECK FIRST whether I promoted them; if BACKLOG.md has no items 25/26 and no
memory/BACKLOG22_gate3_scope_memo_2026-07-28.md exists, they are still pending
and that is the first thing to settle.

BACKLOG 19 is CLOSED — committed (37b3bfd + dee84e1), deployed to Fly image
sha256:ac54d18a, /healthz green. Do NOT reopen it: Session 026 lost a turn to a
confident claim that 19 was "still staged", falsified by git log + ls-remote +
git status --porcelain. Item 19's preserved origin trace now carries a
SUPERSEDED marker so that misread cannot recur. The concurrency-scrub fix (#4)
is review-verified, NOT test-proven — do not re-label it.

THE BOARD WAS REPRIORITISED at Session 026 close. It is no longer numerical:

BACKLOG 21 FIRST — and it is now ONE investigation covering TWO independent
defects on the same hosted PR-publish path, either sufficient alone to prevent
a PR: (a) run_repo_pipeline ignores its github_token param (pipeline.py:68,
dead), and (b) Gate 3 hard-FAILs on the hosted path because pytest is absent
from the deployed image — proven at Tier 0 for the BUILD RECIPE (wheel METADATA
carries no pytest; PEP 735 dependency-groups never reach wheel metadata; no
transitive route via uv/semgrep/bandit/pip-audit; and Gate 3's exact argv
executed against a pytest-less venv yields "No module named pytest", which
matches NONE of the three SKIP triggers at verifier.py:767 → FAIL not SKIP →
g3_ok false → verify_failed → no PR). This is a FUNCTIONAL LAUNCH BLOCKER and
it outranks the security work. First step is the one unrun confirmatory
command: fly ssh console -a patchward-webhook → python -c "import pytest".
It needs Yehor's deploy access. Expect ModuleNotFoundError.

BACKLOG 25 NEXT, standalone — widen _CREDENTIAL_KEYS (credential_proxy.py:39-45)
to cover GITHUB_APP_PRIVATE_KEY_B64, GITHUB_APP_PRIVATE_KEY, GITHUB_APP_ID and
GITHUB_WEBHOOK_SECRET. It gates BOTH Option A and Option B of item 22, so it is
not blocked by the Gate 3 design decision, and the App key + App ID mint tokens
for EVERY installation — cross-tenant blast radius, worse than anything 19 or 22
recorded. Small, unambiguous, agent-startable.

BACKLOG 22 AFTER THAT — scoped and hard-stopped at Session 026; the memo is
memory/BACKLOG22_gate3_scope_memo_2026-07-28.md. STILL AWAITING YEHOR'S
DECISION: Option A (Gate 3 inside docker_sandbox), B (explicit scrubbed env=),
or C (hybrid). Do NOT choose on his behalf and do NOT record a lean — Session
026 caught a false attribution of exactly that kind. Note the memo's finding
that Option A is the FIRST production use of DockerSandbox on a host with no
Docker, not an extension of existing routing. Its urgency is contingent on
whether the hosted path executes at all, which is what 21 settles.

Also open, lower priority: 26 (DockerSandbox never wired into production —
infrastructure gap, companion to 17), 23 (remaining unscrubbed error sinks),
24 (unbounded _RUNTIME_CREDENTIALS growth), 18 (marketplace_purchases retention
gap), 17 (scanner image rebuild — deferred, needs Yehor's explicit trigger).
BACKLOG 12 (CRA/GDPR) still awaits qualified counsel — 44 days to the
2026-09-11 reporting-obligation date as of 2026-07-29, and it is the only hard
external deadline on the board.

Known-UNVERIFIED and worth closing early if cheap: the running Fly image digest
(not re-checked since Session 025); /healthz confirmed by ONE method at Session
026 close, not two; and the real test suite has not been run for three sessions
(success criterion 3, ≥90% coverage, still unverified).

Expect a BACKLOG 21 pass to spawn its own successors per H11 — budget for it.
Ask Yehor what he wants this session before starting.
```
