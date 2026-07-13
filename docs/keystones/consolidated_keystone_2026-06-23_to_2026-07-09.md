# Consolidated Keystone Report — 2026-06-23 → 2026-07-09
## (RepoMend → Patchward rename, Webhook + Marketplace Billing, Fly.io Deployment)

**Report ID:** KS-AUDIT-01
**Covers:** the 16-day gap window with no session log, ADR, or task-file entry
**Date written:** 2026-07-13 (State Reconstruction Audit, Session 013)
**Author:** Claude (agent), reconstructed from git archaeology per
`memory/BUILD_PLAN_2026-07-10.md` Part 3
**Status:** RECONSTRUCTED, DRAFT — pending Yehor review and sign-off. This is
not a normal Keystone Report: **no INTAKE contract was signed for this work**
(that absence is the whole reason this document exists). Nothing below
should be read as "gate passed" — it's an honest as-built snapshot with
explicit unverified items called out, not a pass/fail ceremony.

---

## 1. Why this report exists

Phase 7 closed 2026-06-23 with RepoMend v0.1.0 declared "PROJECT COMPLETE."
The next logged session was 2026-07-10 (Session 012), which discovered that
substantial, real, shipped work had happened in between — a rename, a new
product surface (GitHub App webhook + Marketplace billing), and a live
deployment — with zero session log entries, zero ADRs, and zero INTAKE
contracts written for any of it. Session 012 re-verified that the work was
real (item #27, see `memory/project_session_log.md`) but did not produce the
retroactive documentation itself. This report is that documentation,
written from `git log`, direct file reads, and a live `/healthz` probe —
not from anyone's memory of what happened.

---

## 2. Work-stream clusters (from `git log a67df355^..d4569d40 --stat`)

| Cluster | Commits | Date range |
|---|---|---|
| Rename RepoMend → Patchward | `a67df35`, `c27ea40`, `e6bb75e`, `6ebe135` | 2026-07-07 – 2026-07-08 |
| Fix-Gen/Verifier correctness (unrelated to rename/webhook, opportunistic) | `9bbe496` | 2026-07-08 |
| GitHub App webhook + Marketplace billing | `0bb0286` | 2026-07-09 |
| Session 012 documentation (produced this cycle, included for completeness) | `222b018`, `d4569d4` | 2026-07-10 |

**Not in this window but relevant:** `.github/workflows/publish.yml` (PyPI
Trusted Publisher scaffold) was created earlier, in `4a211a0`, and only
touched (one line, repomend→patchward URL) inside this window by `0bb0286`.
See ADR-031.

---

## 3. What was built — evidence table

| Component | Evidence | What it does |
|---|---|---|
| `src/patchward/` (renamed from `src/repomend/`) | commit `c27ea40`, 135 files | Mechanical rename, no logic change (diff is renames + import path updates only — confirmed by reading the diff, not assumed) |
| `src/patchward/github_app_auth.py` | commit `0bb0286`, 141 lines | JWT signing (PyJWT, RS256) + Installation Access Token exchange. Private key read from env var only, never written to disk (confirmed by reading the module — no file I/O for the key). |
| `src/patchward/installations_db.py` | commit `0bb0286`, 188 lines | SQLite store: `installations`, `installation_repos`, `marketplace_purchases` tables, `SCHEMA_VERSION = 1` migrations pattern matching existing `db.py` style |
| `src/patchward/webhook.py` | commit `0bb0286`, 249 lines | FastAPI receiver at `POST /webhooks/github`: HMAC-SHA256 signature verification (`hmac.compare_digest`, timing-safe — confirmed by direct read), handles `ping`/`installation`/`installation_repositories`/`marketplace_purchase`/`push` events, triggers `run_repo_pipeline` as a background task on `push` |
| `docker/webhook.Dockerfile`, `fly.toml` | commit `0bb0286` | Deployment artifacts for the receiver, separate from the CLI's own packaging |
| `patchward-webhook.fly.dev` | live probe, 2026-07-13: `GET /healthz` → `{"status":"ok"}` (Tier 1, direct HTTPS) | Confirms the deployment is not just committed but actually running |
| `tests/test_github_app_auth.py`, `test_installations_db.py`, `test_webhook.py` | commit `0bb0286`, 113 + 127 + 112 lines | Test coverage shipped in the same commit as the feature (good practice, worth naming explicitly since it's the exception rather than the rule for this gap window — no ADR or session log accompanied it) |

---

## 4. ADR decisions recorded (written this session, not at build time)

| ADR | Title |
|---|---|
| ADR-027 | Rename RepoMend to Patchward |
| ADR-028 | FastAPI + Uvicorn + PyJWT for the webhook receiver |
| ADR-029 | Fly.io as the webhook deployment target |
| ADR-030 | GitHub App + Marketplace billing as the product shift |
| ADR-031 | PyPI Trusted Publisher (OIDC) for release distribution |
| ADR-032 | Unrecognized webhook events are acknowledged, not rejected |

Full text in `memory/architectural_decisions.md`. All six are marked
"Accepted (retroactive, reconstructed from git archaeology, 2026-07-13)"
except ADR-032, which documents a decision actively reviewed and approved
by Yehor today rather than reconstructed from silence.

---

## 5. What was NOT verified — known debt

This section is the point of the report. Do not read §3's evidence table as
"therefore everything works" — it confirms the code exists and does what it
appears to do on inspection, not that it has been independently tested
end-to-end this session.

| Item | Status |
|---|---|
| Full test suite count/coverage on current `main` | **Not re-run.** `uv run pytest --cov` requires Windows (RULE-4); the "371 passed / 89%" figure predates the rename and should not be cited as current until re-run. |
| PyPI Trusted Publisher — registered on PyPI's side | **Cannot verify from here** — PyPI-side configuration, no release tagged yet as of `d4569d4`. |
| `is_entitled()` correctly excludes `cancelled`/`pending_change` Marketplace status | **Not confirmed.** No test found that specifically asserts a cancelled purchase is treated as non-entitled; the code path exists but wasn't traced end-to-end this session. |
| Rate limiting / request body size limits on `/webhooks/github` | **Confirmed absent** (not "unverified" — this one's a real gap, grep-confirmed). |
| `X-GitHub-Delivery` structured logging | **Confirmed absent.** |
| `pip-audit` scoped to the `webhook` extra | **No evidence it has ever run.** |
| `docs/architecture/patchward-webhook-billing-design.md` | **Confirmed does not exist**, despite being cited by path in three separate KS-TRACE code comments as the source design doc. Either written outside version control and lost, or referenced speculatively and never produced. Not blocking (this report reconstructs the same ground from the code itself) but worth a decision — see `memory/BACKLOG.md`. |
| `fly.toml` working-tree state | **Drifted from committed `HEAD` as of 2026-07-13** — see ADR-029's operational-risk note and `memory/STATE.md`. Restore approved by Yehor 2026-07-13, execution pending (git write, runs on his machine). |

---

## 6. Report status

- [x] Work-stream clusters identified from `git log --stat`, not memory
- [x] Evidence table cites commit hashes and direct file reads for every claim
- [x] Live deployment re-confirmed today, not carried from a prior session's claim
- [x] Six retroactive ADRs written and cross-referenced
- [x] Known-debt section names every item this report could NOT confirm, rather than omitting them
- [ ] **Not done:** independent test-suite re-run (needs Yehor, Windows)
- [ ] **Not done:** Yehor's review and sign-off

**This report does not close a phase gate.** Its purpose is narrower: turn
16 days of undocumented work into something a future session — or a future
you — can trust without re-deriving it from `git log` again. Phase 8
(Reconciliation) closes when this report, `memory/STATE.md`, the six ADRs,
and `memory/BACKLOG.md` are all reviewed and tagged as one unit
(`git tag state-audit-2026-07`, applied to the commit that lands this file
set — not to today's starting `HEAD`).

---

_Author:_ Claude (agent) _Date:_ 2026-07-13 _Awaiting signature:_ Yehor
