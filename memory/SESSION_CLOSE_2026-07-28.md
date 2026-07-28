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

## Addendum — live-container verification (same day, post-close)

Run by Yehor inside `fly ssh console -a patchward-webhook`, machine
`7841600fd5e7e8`. Read-only; no values printed, nothing installed or mutated.

| Claim | Result | Verdict |
|---|---|---|
| §5: pytest absent from the RUNNING container | `ModuleNotFoundError: No module named 'pytest'`; `python -m pytest` against a real `tests/` probe → `/usr/local/bin/python: No module named pytest` — matches none of the three SKIP triggers | **CONFIRMED, Tier 0** — residual closed |
| jest branch dead on the hosted path | `node` ABSENT, `npx` ABSENT | CONFIRMED |
| Item 25's four uncovered credentials | `GITHUB_APP_PRIVATE_KEY_B64` (2236), `GITHUB_APP_ID` (7), `GITHUB_WEBHOOK_SECRET` (36), `ANTHROPIC_API_KEY` — all SET in the inherited `os.environ` | **CONFIRMED live** |
| BACKLOG 19's copy-not-mutate fix holds | `PATCHWARD_GIT_TOKEN` ABSENT from the parent environment | **CONFIRMED live** — first Tier-0 confirmation outside the source |
| Item 21's root cause | `GITHUB_TOKEN` ABSENT | CONFIRMED |
| Item 26: no Docker on the host | `command -v docker` → nothing | CONFIRMED live |
| Running image built from `dee84e1` | 3/4 source hashes matched exactly; `verifier.py` resolved to HEAD's file with CRLF (`git show HEAD:… \| sed 's/$/\r/'` reproduces `e375a6d3…`) | **CONFIRMED** — replaces the UNVERIFIED image-digest row with a stronger byte-level proof |
| **NEW: `ANTHROPIC_API_KEY` is 9 characters** | `webhook.py:318` guards on falsiness only, so it passes; live `models.list()` from inside the container → `401 invalid x-api-key` (`req_011CdUpKqhwSQoJufxCitjcZ`) | **NEW DEFECT → item 27, CONFIRMED Tier 0**, upstream of both of item 21's |
| `/healthz` second method | Yehor's `curl.exe` from his own machine → `{"status":"ok"}`, agreeing with the sandbox's `WebFetch`; `fly status` → machine `started`, 1 check passing | **CONFIRMED, two methods** — final weak point retired |

Method note, recorded rather than quietly dropped: the probe's `echo "exit=$?"`
reported the exit status of the trailing `tail`, not of pytest. It was not
treated as evidence.

### Second addendum — item 27's fix attempt failed

Yehor re-set the Fly secret. The rolling update succeeded, `/healthz` returned
green, and the new value reached the process (`length: 110`) — but the call
still returned `401 invalid x-api-key` under a new request id
(`req_011CdUqmbwJFzk9S97aPP1eP`). Contamination was refuted (raw length ==
stripped length, no whitespace, quotes or non-ASCII), and a prefix sweep across
ten credential families returned all False **including `sk-ant-`**. The secret
holds a well-formed credential from some other system.

Identification was **deliberately stopped** — each further probe leaks more
shape about a live credential while yielding less, and identifying it belongs
to Yehor's records. Recorded as a boundary held on purpose, not an unfinished
check.

Two consequences, kept separate: item 27 stays OPEN and its fix is still a
Yehor action; and whatever that credential is, it has been exposed on the Gate 3
inheritance path and should be rotated at its source regardless. New **item 28**
splits out the code half — `webhook.py:318` validates by falsiness only and has
now passed two different broken secrets in one evening; a one-line
`startswith("sk-ant-")` rejects both at startup.

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

- ~~`/healthz` confirmed by one method, not two~~ — **RETIRED.** Corroborated by
  Yehor's own `curl.exe` from a different machine and network, agreeing exactly.
  Note precisely: this does NOT promote H10-candidate, whose condition is a
  second `WebFetch` DISAGREEMENT. The two agreed; the candidate stands.
- ~~The running Fly image is UNVERIFIED~~ — **RETIRED by the addendum above.**
  Replaced by a stronger check than the digest: byte-level source-hash
  comparison against `dee84e1`, all four files accounted for.
- ~~§5 proves the recipe, not the container~~ — **RETIRED by the addendum
  above.** Confirmed Tier 0 on the running container.
- **NEW, and worse than what it replaced:** item 27 — the hosted
  `ANTHROPIC_API_KEY` is invalid. **Both links Tier 0**: 9 characters measured
  in the process, and a live `401 invalid x-api-key` from the deployment itself.
  The hosted path fails at Fix-Gen's first API call, upstream of everything
  item 21 describes.
- **The only weak point carried forward:** the real test suite has not been run
  for three sessions, so success criterion 3 (green at ≥90% coverage) stays
  UNVERIFIED. It needs Yehor's machine, not the container.
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
.strategy/STRATEGY.md — re-verify fresh, do not trust as-is. Per H13/H14/H16
that includes this prompt's own claims, the backlog entries' own stated
premises, anything I assert from memory, and any hash or diff mismatch you see
(normalise line endings FIRST — this repo's Windows working tree is mixed).

Session 026 closed clean. Per H2 this prompt deliberately cites NO closing hash:
the hash written here went stale TWICE while the session was still writing it
(75d3fe9 -> c1f789b -> 05764d3), which is H2's whole point. Establish the real
HEAD yourself via git ls-remote + a fresh clone, then confirm the close landed
BY CONTENT rather than by hash — all four must hold:
  - memory/BACKLOG.md contains items 24, 25, 26, 27, 28 in that order, and the
    "SUPERSEDED, see STATUS: CLOSED below" marker on item 19's origin trace;
  - .strategy/STRATEGY.md contains the "Session log (continued) - Session 026"
    block and heuristics H13, H14, H16;
  - memory/BACKLOG22_gate3_scope_memo_2026-07-28.md exists (448 lines);
  - memory/SESSION_CLOSE_2026-07-28.md is this file.
If any is missing, the close did not fully land and that is the first thing to
settle before any other work.

BACKLOG 19 is CLOSED — committed (37b3bfd + dee84e1), deployed, and its fix is
now Tier-0 confirmed ON THE LIVE HOST (PATCHWARD_GIT_TOKEN absent from the
webhook's os.environ). Do NOT reopen it. The concurrency-scrub fix (#4) is
review-verified, NOT test-proven — do not re-label it.

THE HOSTED PATH DOES NOT WORK. This is the headline, and it is now confirmed on
the running container, not inferred. THREE independent defects sit on the
hosted PR-publish path, each alone sufficient to prevent a PR. Treat them as
ONE investigation unit under BACKLOG 21 — fixing any one ships nothing:

  27 (FIRST — it fires earliest, CONFIRMED Tier 0, and ONE FIX ATTEMPT HAS
     ALREADY FAILED): the ANTHROPIC_API_KEY secret does not contain an Anthropic
     key. Two values were rejected on 2026-07-28 — a 9-char stub
     (req_011CdUpKqhwSQoJufxCitjcZ) and, after Yehor re-set the secret, a
     110-char well-formed credential from a DIFFERENT service
     (req_011CdUqmbwJFzk9S97aPP1eP). Delivery is not the problem; the value
     reached the process both times. A prefix sweep across ten credential
     families returned all False including sk-ant-. Whatever that second
     credential is, it also needs ROTATING AT ITS SOURCE — it sat exposed on
     the Gate 3 inheritance path. See also item 28 (the startup guard).
     webhook.py:318 guards on falsiness only, so the malformed secret passes
     startup and Fix-Gen fails on its FIRST request — before verify, before
     Gate 3. The two defects below have therefore never even been reached in
     production. FIRST ACTION NEXT SESSION: ask Yehor whether he has re-set the
     secret (flyctl secrets set ANTHROPIC_API_KEY=… — HIS action, never the
     agent's), and re-run the models.list() check to confirm. Only then do the
     other two defects become observable. The guard hardening (validate
     shape/length, fail loudly at startup rather than silently at first use) is
     agent-startable and should ship with 21's fix.
  21 (the original): run_repo_pipeline ignores its github_token param
     (pipeline.py:68, dead) and GITHUB_TOKEN is confirmed ABSENT from the
     deployment, so the PR publisher's credential is empty and the push cannot
     authenticate.
  §5 (filed under 21): Gate 3 hard-FAILs because pytest is absent from the
     image — confirmed live: ModuleNotFoundError, and python -m pytest emits
     "No module named pytest" which matches NONE of the three SKIP triggers at
     verifier.py:767 → FAIL not SKIP → g3_ok false → verify_failed. node and
     npx are also absent, so the jest branch cannot run either.

  28 (SHIPS WITH 21's FIX, not separately): webhook.py:318 validates the
     Anthropic credential by FALSINESS ONLY, and has now passed TWO different
     broken secrets in one evening — the 9-char stub and the 110-char foreign
     credential. A one-line startswith("sk-ant-") at startup rejects both. Worth
     the same treatment for GITHUB_APP_ID / GITHUB_APP_PRIVATE_KEY_B64 /
     GITHUB_WEBHOOK_SECRET, which have the same guard or none. Never log any
     part of a credential value in the failure message. OPEN QUESTION FOR YEHOR,
     deliberately NOT decided: should /healthz also assert credential validity
     (a cached startup probe, not a per-request API call) so that green means
     "can actually work" rather than "process is running"? A green /healthz over
     an unusable credential is exactly how these defects stayed invisible.

ALSO YEHOR'S, and independent of all the above: ROTATE the unidentified 110-char
credential at its source. It sat in a production env var, exposed on the Gate 3
inheritance path, and neither party could name what it grants. If it was pasted
from somewhere, check whether the same paste reached another secret.

BACKLOG 25 NEXT, standalone — widen _CREDENTIAL_KEYS (credential_proxy.py:39-45)
to cover GITHUB_APP_PRIVATE_KEY_B64, GITHUB_APP_PRIVATE_KEY, GITHUB_APP_ID and
GITHUB_WEBHOOK_SECRET. All four are LIVE-CONFIRMED present in the webhook's
os.environ (lengths 2236 / 7 / 36), inherited by Gate 3's adversarial child with
no race. The App key + App ID mint tokens for EVERY installation — cross-tenant
blast radius. It gates BOTH Option A and Option B of item 22, so it is not
blocked by the Gate 3 design decision. Small, unambiguous, agent-startable.

BACKLOG 22 AFTER THAT — scoped and hard-stopped; memo at
memory/BACKLOG22_gate3_scope_memo_2026-07-28.md. STILL AWAITING YEHOR'S
DECISION: Option A (docker_sandbox), B (scrubbed env=), or C (hybrid). Do NOT
choose on his behalf and do NOT record a lean — Session 026 caught a false
attribution of exactly that kind. Option A is now confirmed to need new
infrastructure: command -v docker inside the running container returns nothing.

Also open, lower priority: 26 (DockerSandbox never wired into production —
live-confirmed, companion to 17), 23 (unscrubbed error sinks), 24 (unbounded
_RUNTIME_CREDENTIALS growth), 18 (marketplace_purchases retention gap), 17
(scanner image rebuild — deferred, needs Yehor's explicit trigger). BACKLOG 12
(CRA/GDPR) still awaits qualified counsel — 44 days to the 2026-09-11
reporting-obligation date as of 2026-07-29, the only hard external deadline.

Known-UNVERIFIED, now exactly ONE item: the real test suite has not been run for
three sessions (success criterion 3, >=90% coverage). It needs Yehor's machine.
Every other weak point named at Session 026 close was retired the same day by
the live-container pass. Consider closing this one early rather than carrying it
a fourth session.

Expect a BACKLOG 21/27 pass to spawn its own successors per H11 — budget for it.
Ask Yehor what he wants this session before starting.
```
