# Session Close — Patchward — 2026-07-29 (Session 027)

Opened via session-strategy-synthesis; closed via session-close. This file is the
handoff for Session 028. Per H2 it deliberately cites NO closing hash (the memory
commit that seals this session moves HEAD after this file is written); the close
is verified BY CONTENT below.

## Gate status

| Claim | Pass 1 | Pass 2 | Verdict |
|---|---|---|---|
| Session 026 close landed | device `git rev-parse` → `6650918` | cloud `ls-remote` + fresh clone; 4 content conditions | **CONFIRMED** |
| Real HEAD after 25 | device `git rev-parse` → `f02ad21` | cloud `ls-remote` + fresh-clone content (4 App keys present) | **CONFIRMED** |
| BACKLOG 25 shipped | Yehor `git commit`/`push` → `6650918..f02ad21` | `ls-remote` origin = `f02ad21`; fresh clone has the keys | **CONFIRMED** |
| Full suite ran ≥90% | Yehor `uv run --extra webhook pytest` → 519 passed | coverage line → 90.62%; `credential_proxy.py` 100% | **CONFIRMED** (retires success-criterion 3) |
| §5 (no pytest on hosted image) | `fly ssh` → `python -m pytest` = `No module named pytest` | `import pytest` ModuleNotFoundError; `node`/`npx` absent | **CONFIRMED (live image)** |
| Item 27 (Anthropic key) fixed | local `models.list()` → KEY VALID before deploy | running image → `ANTHROPIC KEY OK` | **CONFIRMED (live image)** |
| BACKLOG 28 landed | tree `git rev-parse` = `f02ad21`; `_validate_credential_shapes` absent | origin has 0 occurrences of `StartupCredentialError` | **FALSIFIED → PATCH PREPARED, not landed** |
| "BACKLOG.md is stale / lacks 25-26" (inherited) | `origin` BACKLOG.md items 24–28 present | fresh clone identical | **FALSIFIED ×3** |
| 110-char foreign credential rotated | — | — | **UNVERIFIED / OPEN (Yehor)** |

## Session judgment

**L3 Artifacts (verified):** commit `f02ad21` (BACKLOG 25, +70 lines, on origin);
a valid `ANTHROPIC_API_KEY` deployed and live-confirmed on `patchward-webhook`;
§5 proven against the running image; `backlog28_startup_credential_guard.patch`
(tested 526/90.75%, in repo root, unlanded); this close-out + memory
reconciliation.

**L2 Goal (emergent — "ship the agent-startable security work and unblock the
hosted path where possible"):** **MET.** The one fully agent-startable item (25)
shipped and is verified on origin; item 27, the only hosted-path defect Yehor
could clear this session, is fixed and live-confirmed; §5's last verification gap
is closed. Item 28 is prepared and tested but not landed — carried, not claimed.

**L1 Horizon (distance to first paying Marketplace install):** Reduced, honestly.
One of three hosted-path blockers (27) is down; the remaining two (§5 Gate-3 FAIL,
item 21 push credential) are now precisely characterized and live-confirmed rather
than suspected — the work is de-risked even though the hosted path still does not
publish a PR. This was progress, not motion: every claim is backed by a live probe
or an origin read.

## Decisions made this close

- Record item 28 as PATCH-PREPARED, not CLOSED — because the tree is at `f02ad21`
  and the guard is absent from the committed `webhook.py`. Honesty over tidiness.
- Do NOT decide item 28's two open questions (absence-fails-boot; /healthz
  assertion) or the §5 design fork or item 22's A/B/C — all remain Yehor's.
- Orient the guidance model around a North-Star priority function (distance to
  first paying Marketplace install), delivered separately for Yehor to install.

## Weakest points, stated plainly

1. **Item 28 is tested but unlanded.** If Session 028 opens assuming it shipped,
   it will be wrong — verify the tree first (the content checklist below does).
2. **The 110-char foreign credential is still unrotated** and its origin unknown.
   It sat in a production env var. Yehor-owned, unresolved.
3. **Item 27's live confirmation rests on Yehor's terminal paste**, not a probe I
   ran myself (no Fly auth in the sandbox). High-trust, single-operator; recorded
   as live-confirmed but via one operator.
4. **The hosted path still cannot publish a PR** (§5 + 21). The headline defect of
   the whole investigation is not yet fixed — only better understood.

## File manifest

- Committed already (Session 027): `f02ad21` — `credential_proxy.py`,
  `test_credential_proxy.py` (BACKLOG 25).
- To be committed by this close: `memory/BACKLOG.md` (status banners on 21/25/27/
  28), `.strategy/STRATEGY.md` (Session 027 log/calibration/heuristics/business
  context), `memory/SESSION_CLOSE_2026-07-29.md` (this file).
- Deliberately NOT committed: `backlog25_credential_keys.patch`,
  `backlog28_startup_credential_guard.patch` (working artifacts in repo root —
  delete or ignore), the CRLF-flapped files (device-VM mount artifact; do not
  stage).

## Next-session opening prompt (copy-paste into Session 028)

```
Resume Patchward. Open via the session-strategy-synthesis skill, grounding in
.strategy/STRATEGY.md — re-verify fresh, do not trust as-is. Per H13/H14/H16 that
includes this prompt's own claims, the backlog entries' own premises, anything I
assert from memory, and any hash/diff mismatch (normalise line endings FIRST —
mixed CRLF tree). NOTE the recurring inherited-claim trap (H14, now 3×): the
BACKLOG.md in the repo is CURRENT — do not accept any assertion that it "predates"
items 25/26/27/28 or that the Gate 3 memo is "chat-only"; verify against origin.

Session 027 closed. Per H2 this prompt cites NO closing hash. Establish real HEAD
yourself (git ls-remote + fresh clone), then confirm the close landed BY CONTENT —
all must hold:
* memory/BACKLOG.md carries "STATUS: CLOSED 2026-07-29 (Session 027)" banners on
  items 25 AND 27, a "PATCH PREPARED ... NOT YET LANDED" banner on item 28, and a
  "§5 UPDATE 2026-07-29 ... CONFIRMED against the LIVE IMAGE" banner on item 21;
* .strategy/STRATEGY.md contains "Session log (continued) — Session 027", the
  Session-027 calibration block, H17-candidate, and "Business context (Session 027";
* memory/SESSION_CLOSE_2026-07-29.md exists (this file).
If any is missing, the close did not fully land — settle that first.

VERIFIED STATE at close (re-verify, don't trust):
- BACKLOG 25 CLOSED — committed f02ad21, pushed, verified on origin. Suite 519
  passed / 90.62% on Yehor's machine (success-criterion 3 RETIRED this session).
- Item 27 CLOSED (live) — ANTHROPIC_API_KEY is now a valid Anthropic key,
  confirmed on the running image (ANTHROPIC KEY OK). Do NOT reopen.
- §5 CONFIRMED on the live image — Gate 3 hard-FAILs (no pytest; node/npx absent).
- BACKLOG 28 PATCH PREPARED, NOT LANDED — backlog28_startup_credential_guard.patch
  is in the repo root, tested 526/90.75%. FIRST agent-startable action if still
  unlanded: apply + suite + scoped-commit + push (same flow as 25), then flip its
  BACKLOG banner to CLOSED. Two Yehor decisions gate its stricter form: should
  absence of a required credential also fail the boot; should /healthz assert
  validity.

PRIORITY (North-Star = distance to first paying Marketplace install; see the
Session-027 priority function):
- P0 — hosted path cannot publish a PR: §5 + item 21 as ONE arc. GATED by a YEHOR
  DECISION (the §5 fork): install pytest/node runners into the Gate-3 image so it
  actually verifies, vs. make the verifier SKIP gracefully when the runner is
  absent — this changes what Gate 3 MEANS. Open Session 028 with a short
  scope-and-decide memo on that fork (cost + meaning of each option, and what item
  22's sandbox choice implies for each), get Yehor's call, THEN ship §5 + 21
  together. Item 21's code half (run_repo_pipeline ignores its github_token param,
  pipeline.py:68 dead) is agent-preparable now; its push credential is Yehor-set.
- P1 — launch-gating: item 22 A/B/C (Yehor's call, still pending; Option A needs
  new infra — docker absent from the container); item 12 CRA/GDPR counsel
  (calendar-driven, ~2026-09-11, ~44 days from 2026-07-29).
- P2 — small shippable hardening: land 28 if unlanded; items 18, 24.
- P3 — infra debt, no live exposure: 17, 26.

YEHOR-OWNED, independent of all the above:
- ROTATE the unidentified 110-char credential at its source (sat in a prod env
  var; origin unknown). Check whether the same paste reached another secret.
- The §5 design fork and item 22 A/B/C decisions above.

Known-UNVERIFIED: none newly. The real suite ran this session (90.62%). Ask Yehor
what he wants this session before starting.
```
