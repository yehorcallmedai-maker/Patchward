# Keystone Report — Phase 0: Foundations
_Project: RepoMend — Local-First Multi-Repo Security Agent_
_Date: 2026-06-10 | Session: 001_

---

## 1. Provenance

| File | Origin |
|------|--------|
| `pyproject.toml` | AI-generated |
| `repomend.toml` | AI-generated |
| `src/repomend/__init__.py` | AI-generated |
| `src/repomend/cli.py` | AI-generated |
| `src/repomend/config.py` | AI-generated |
| `src/repomend/db.py` | AI-generated |
| `src/repomend/scanner.py` | AI-generated |
| `src/repomend/tracing.py` | AI-generated |
| `tests/test_config.py` | AI-generated |
| `tests/test_db.py` | AI-generated |
| `.claude/agents/scanner.md` | AI-generated |
| `.claude/agents/fix-gen.md` | AI-generated |
| `.claude/agents/verifier.md` | AI-generated |
| `memory/intake_phase0.md` | AI-generated, signed by Yehor |
| `memory/architectural_decisions.md` | AI-generated, decisions approved by Yehor |
| `repomend-fixture/` (GitHub) | AI-specified, Yehor executed |

Human edits: zero. All code AI-generated within the signed INTAKE contract.

---

## 2. Verification Summary

| AC | Criterion | Result | Evidence |
|----|-----------|--------|----------|
| AC-01 | `repomend scan` exits 0 on clean file | ✅ PASS | `clean.py` in fixture returns 0 findings |
| AC-02 | ≥1 finding written to SQLite on vulnerable file | ✅ PASS | SQLite query confirmed 1 finding, status=success |
| AC-03 | Findings match Semgrep raw output | ✅ PASS | rule_id, file_path, line 9, severity, message all match |
| AC-04 | OTel trace appears in Langfuse per scan run | ✅ PASS | 8 spans confirmed in Langfuse UI (2 scan runs) |
| AC-05 | `repomend.toml` controls repo, rules, db_path | ✅ PASS | `--repo` flag override tested manually |
| AC-06 | CLI rejects missing/malformed config with exit 1 | ✅ PASS | 5 config tests pass including missing and malformed |
| AC-07 | Scanner subagent tool restriction enforced | ⏸ DEFERRED | Requires SDK subagent wiring — moved to Phase 1 per Yehor |
| AC-08 | ≥80% coverage on config + DB layer | ✅ PASS | `config.py` 98%, `db.py` 100%, total 98.78% |

**Test run:** `uv run pytest` — 12 passed, 0 failed, 0 warnings.
**Tool:** pytest 9.0.3 + pytest-cov 7.1.0, Python 3.14.4.

---

## 3. Defects Caught and Fixed

| # | Defect | Severity | Fix Applied |
|---|--------|----------|-------------|
| D-01 | `typer.Exit` is not a subclass of `SystemExit` — tests catching `SystemExit` missed it | Medium | Changed `config.py` to raise `SystemExit(1)` directly; utility functions must not use Typer exceptions |
| D-02 | Coverage at 38% — `cli.py`, `scanner.py`, `tracing.py` have 0% unit coverage | Low | Scoped coverage to config+db per AC-08; integration-layer modules require live I/O and are out of unit scope |
| D-03 | `[tool.uv.dev-dependencies]` deprecation warning in uv 0.11.20 | Low | Migrated to `[dependency-groups]` per uv spec |
| D-04 | Single Typer command drops subcommand routing — `repomend scan` failed | Medium | Added `version` command; Typer requires ≥2 commands for subcommand routing |
| D-05 | `BatchSpanProcessor` loses spans on CLI process exit | High | Switched to `SimpleSpanProcessor` (synchronous); added `force_flush()` before exit |
| D-06 | Raw OTel spans not surfacing in Langfuse UI (10-min delay assumed) | Low | Not a code defect — Langfuse free tier has ingestion delay. Confirmed resolved: spans visible after ~5 min |
| D-07 | `langfuse==4.7.1` drops `.trace()` method — wrong package version assumed | Medium | Removed `langfuse` SDK dependency; raw OTel confirmed working. No SDK needed |

---

## 4. Known Limitations

- **1 finding, not 3:** `p/python` ruleset does not include `eval` or hardcoded-password rules. Only `subprocess-shell-true` fires on the fixture. AC-02 passes (≥1), but the fixture spec said "exactly 3." To be corrected in Phase 1 with rulesets or plants that match confirmed `p/python` rules.

- **AC-07 deferred:** Scanner subagent tool restriction enforcement requires the Claude Agent SDK to be wired up. Not testable in Phase 0's walking skeleton. Will gate Phase 1 INTAKE.

- **Langfuse free tier latency:** Traces appear in Langfuse UI with 5–10 minute delay. Not a defect, but worth noting for Phase 2 when real-time observability may be required.

- **semgrep pip install damaged system Python OTel packages:** Installing `semgrep` globally downgraded `opentelemetry-sdk` from 1.42.1 → 1.37.0 in system Python. The uv venv is isolated and unaffected. Noted for environment hygiene.

- **Env vars not persisted for Langfuse keys:** `SetEnvironmentVariable` writes to registry but not current session. In practice, keys must be set per-session with `$env:`. To be addressed with a `.env` file approach in Phase 1.

- **No sandbox isolation:** Phase 0 runs Semgrep in the host process. No sandbox-runtime boundary. This is by design — Phase 2 adds sandboxing.

---

## 5. Accountability Statement

> I, Yehor, have reviewed this Keystone Report. The build matches the signed INTAKE contract (with the approved AC-07 deferral). The defects listed in §3 were caught during this session and fixed before delivery. The limitations in §4 are stated accurately and I am aware of them.
>
> I authorize Phase 1 to begin when the Phase 1 INTAKE contract is written and signed.

**Signed:** Yehor **Date:** 2026-06-10

---

## 6. Methodology Note — Suggested Improvement

**The "set env vars in a new session" friction cost us ~30 minutes.** For Phase 1, add a `.env` file loader (via `python-dotenv`) to `config.py` so Langfuse keys and any other secrets are loaded automatically at startup. Document the `.env.example` file with all required vars. This eliminates per-session setup and removes a class of "why isn't tracing working" bugs.

---

_End of Keystone Report — Phase 0_
