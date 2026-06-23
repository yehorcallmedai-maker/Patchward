# Phase 7 INTAKE — Multi-Finding + AsyncAnthropic + Distribution
**Project:** RepoMend — Local-First Multi-Repo Security Agent
**Phase:** 7
**Contract date:** 2026-06-23
**Status:** SIGNED — 2026-06-23
**Namespace:** AC-P7-XX (base) · AC-P7A-XX (addenda)
**Blocked by:** Phase 6 closed ✅ 2026-06-23

---

## 0. ADR-009 Pre-Step — Architecture Decisions Locked Before Build

Per ADR-009, the following four questions were resolved before the
INTAKE contract was written. Answers are locked and become binding
constraints in §2.

### Q1 — Distribution: pipx or uv tool install?

**Decision: `uv tool install` as primary distribution method.**

Rationale:
- The project uses `uv` throughout — dependency management, venv,
  and test execution (`uv run pytest`). Introducing `pipx` adds a
  second tool with no benefit.
- `pyproject.toml` already declares
  `[project.scripts] repomend = "repomend.cli:app"`.
  `uv tool install .` and `uv tool install repomend` both respect
  this entry directly.
- `uv tool` produces an isolated environment identical to `pipx
  install`, but without requiring users to install pipx separately.
- Development workflow (`uv run`, `uv sync`) and install workflow
  (`uv tool install`) share a single tool — lower onboarding
  friction.

**ADR-023 (proposed)**

---

### Q2 — Docker image: bundle scanners, runtime only, or skip?

**Decision: Skip Docker distribution image.**

Rationale:
- `repomend-scanner:0.1.0` already exists as the sandbox runtime
  primitive (Phase 2). That image is not a distribution artifact.
- Distributing RepoMend itself as a Docker image would require
  Docker-in-Docker or volume-mount orchestration to share the target
  repo between the two containers — not a viable distribution
  pattern at Phase 7.
- Scanners (semgrep, bandit, pip-audit, Trivy) are installed
  natively on the dev machine. `repomend.toml.example` documents
  required scanner versions.
- `uv tool install` (Q1) is sufficient for the target user profile.
  A Docker distribution image is Phase 8+ scope.

**ADR-024 (proposed)**

---

### Q3 — Shared config: git repo, template, or single-user only?

**Decision: Single-user only. Ship `repomend.toml.example`.**

Rationale:
- RepoMend is a solo project. No team config sharing is needed in
  Phase 7.
- `repomend.toml` contains machine-local fields (`path` under
  `[[repos]]`) that cannot be shared across machines without
  substitution tooling.
- `repomend.toml.example` with full inline comments on every field
  covers the template need: `cp repomend.toml.example repomend.toml`
  and fill in values.
- Git-tracked shared config or dotfiles pattern deferred to Phase 8.

**ADR-025 (proposed)**

---

### Q4 — Docs: README only, docs/ folder, or MkDocs?

**Decision: docs/ folder extended with user-facing guides.
README for quick start.**

Rationale:
- `docs/` already exists with intake contracts for Phases 1–6.
  Extending it is the zero-friction path.
- `docs/user_guide.md` covers installation, config reference, quick
  start, and scanner setup — the minimum viable docs for a tool
  this complex.
- README.md updated with a concise install + quick start section
  that links to `docs/user_guide.md` for detail.
- MkDocs adds site-generation overhead and a deployment pipeline.
  For a solo local-first tool at Phase 7 this is unjustified.
  MkDocs deferred to Phase 8+.

**ADR-026 (proposed)**

---

## 1. Client Goal

Phase 7 has two tracks.

**Track A — Functional (resolves KL-P6-01/02/03):**
- Multi-finding per repo: the pipeline processes all findings in a
  scan run, up to `max_findings_per_repo` (configurable, default 5).
  One failed finding does not abort the rest.
- AsyncAnthropic direct: all Claude API calls inside the async
  pipeline use `AsyncAnthropic` natively. No `asyncio.to_thread()`
  wrapping of LLM calls.
- RunLog threading: `RunLog` is passed as an argument into
  `run_repo_pipeline()` rather than constructed via cli state. Each
  finding appends its own run log record.

**Track B — Distribution + Docs (resolves Q1–Q4 pre-step):**
- `uv tool install` packaging verified end-to-end.
- `repomend.toml.example` with inline comments on every field.
- `docs/user_guide.md` with installation, quick start, and config
  reference.
- `README.md` updated.

---

## 2. Constraints

### C-P7-01 — Multi-finding loop
`run_repo_pipeline()` iterates over all findings returned by the
scanner for a given repo. Findings are processed **sequentially**
within a repo (not concurrently). The loop exits early only when
the total PRs opened for that repo reaches `max_findings_per_repo`.
One finding's Fix-Gen failure or Verifier rejection does not abort
remaining findings.

### C-P7-02 — max_findings_per_repo config
`[batch].max_findings_per_repo` (integer, default 5) caps findings
processed per repo per run. Added to `BatchConfig` in `config.py`.
Enforced before Fix-Gen is called for a finding. Value of 0 is
invalid — raise `ValueError` at load time.

### C-P7-03 — AsyncAnthropic direct in FixGenSubagent
`FixGenSubagent` uses `anthropic.AsyncAnthropic` as its client.
`apply_fix()` is `async def`. No `asyncio.to_thread()` wraps the
LLM call. Structurally asserted by AST test (AC-P7-03).

### C-P7-04 — RunLog parameter threading
`RunLog` is constructed at the CLI layer and passed as an argument
to `run_repo_pipeline()`. It is not a module-level singleton or
global. `run_repo_pipeline()` appends one record per finding
processed (verified or not).

### C-P7-05 — uv tool install produces working binary
`uv tool install .` from the project root installs `repomend` into
an isolated uv-managed environment. `repomend --version` and
`repomend scan --help` must both exit with code 0 after install.

### C-P7-06 — repomend.toml.example
`repomend.toml.example` at project root documents every supported
config field with an inline comment on each line. Sections: 
`[anthropic]`, `[github]`, `[batch]` (including `max_concurrent`
and `max_findings_per_repo`), `[models]`, `[verifier]`, `[[repos]]`.

### C-P7-07 — docs/user_guide.md
`docs/user_guide.md` must include at minimum:
1. Prerequisites (Python 3.12+, uv, scanners, Docker Desktop)
2. Installation (`uv tool install`)
3. Configuration (`repomend.toml` walkthrough)
4. Quick start (one-repo scan + fix)
5. Config reference table (every field, type, default, description)

### C-P7-08 — README.md updated
`README.md` includes: one-line description, prerequisites, install
command, quick start (≤5 lines), link to `docs/user_guide.md`.

---

## 3. Acceptance Criteria

| AC | Description | Test location |
|----|-------------|---------------|
| AC-P7-01 | Multi-finding: fixture repo with 3 findings → 3 run log records in a single `repomend fix` run (mocked Fix-Gen + Verifier) | `test_orchestrator.py` |
| AC-P7-02 | Multi-finding isolation: Fix-Gen mock raises on finding 2 of 3 → findings 1 and 3 complete; run log has 3 records (one with `fix_status=failed`) | `test_orchestrator.py` |
| AC-P7-03 | Structural: no `asyncio.to_thread` call wraps an `Anthropic` or `AsyncAnthropic` client call — AST inspection of `fix_gen.py` and `pipeline.py` | `test_async_pipeline.py` |
| AC-P7-04 | `max_findings_per_repo = 2` with 3 findings → only 2 run log records written; third finding not processed | `test_orchestrator.py` |
| AC-P7-05 | RunLog threading: `run_repo_pipeline()` signature includes `run_log: RunLog` parameter; no module-level `RunLog()` in `pipeline.py` — structural assertion | `test_orchestrator.py` |
| AC-P7-06 | `uv tool install .` succeeds; `repomend --version` exits 0 (manual verification — logged in §4.2) | Manual |
| AC-P7-07 | `repomend.toml.example` exists at project root; contains all 7 sections; parses without error when loaded through `Config.load()` with dummy secrets | `test_config.py` |
| AC-P7-08 | `docs/user_guide.md` exists; contains the 5 required section headings | file-existence + grep |
| AC-P7-09 | `README.md` contains the string `uv tool install` and a link to `docs/user_guide.md` | file-content grep |
| AC-P7-10 | End-to-end integration: 3-finding fixture → 3 run log records; if all verified, 3 draft PRs opened. Skip guard: `ANTHROPIC_API_KEY` + `GITHUB_TOKEN` + `RUN_E2E_MULTI_FINDING` | `test_golden_dataset.py` |
| AC-P7-11 | `BatchConfig.max_findings_per_repo`: default=5, parsed from `[batch].max_findings_per_repo`, propagated to pipeline | `test_config.py` |

---

## 4. Test Contract

### 4.1 Inputs

| Input | Value |
|-------|-------|
| Fixture repo | `repomend-fixture` — 3 findings (subprocess-shell-true, md5, ssl-wrap-socket) |
| `repomend.toml` (multi-finding) | `max_findings_per_repo = 3`, `max_concurrent = 1` |
| `repomend.toml` (cap test) | `max_findings_per_repo = 2` |
| Env vars | `ANTHROPIC_API_KEY`, `GITHUB_TOKEN`, `RUN_E2E_MULTI_FINDING` |

### 4.2 Expected outputs

| Scenario | Expected output |
|----------|-----------------|
| 3 findings, all verified | 3 run log records · 3 draft PRs |
| 3 findings, finding 2 Fix-Gen failure | 3 run log records · 2 PRs · record 2 `fix_status=failed` |
| `max_findings_per_repo = 2` | 2 run log records · third finding skipped |
| `uv tool install .` | `repomend --version` exits 0 (log exact version string in KS-P7-09) |

### 4.3 Invariants

1. Each finding produces exactly one run log record, regardless of
   outcome.
2. `max_findings_per_repo` is enforced before Fix-Gen is called —
   the cap applies to findings attempted, not PRs opened.
3. `GITHUB_TOKEN` must not appear in any run log record (carried
   from AC-P5-11/P6 invariant 3).
4. `FixGenSubagent.apply_fix()` must be `async def` — no sync
   client path.
5. `RunLog` is a parameter, not a global — invariant confirmed by
   absence of module-level `RunLog()` in `pipeline.py`.
6. A single `AsyncAnthropic` client instance is created once per
   repo pipeline invocation, not once per finding.

### 4.4 Adversarial cases

**AD-P7-01 — All findings unverifiable.**
Mock Verifier to return `verification_status="failed"` for all 3
findings. Assert 3 run log records written (all failed), 0 PRs
opened, pipeline exits without crash.

**AD-P7-02 — max_findings_per_repo = 0.**
Assert `ValueError` raised at `Config.load()` time. Pipeline must
never reach `run_repo_pipeline()` with a zero cap.

**AD-P7-03 — Single AsyncAnthropic client per repo.**
Assert `AsyncAnthropic()` constructor is called exactly once for
a 3-finding repo run (mock spy on constructor). Re-instantiating
per finding would create N connections — a resource leak.

---

## 5. Risk Areas

| Risk | Severity | Mitigation |
|------|----------|------------|
| AsyncAnthropic migration breaks existing sync mock patterns | HIGH | All `Anthropic` sync mocks in `test_fix_gen.py` must be migrated to `AsyncAnthropic` async mocks. Plan this as first build task (KS-P7-02). |
| Multi-finding loop opens too many PRs | MEDIUM | `max_findings_per_repo` cap (C-P7-02, default 5). Document in user guide. |
| uv tool install not tested in CI | LOW | Manual verification (AC-P7-06). Exact commands logged in Keystone Report. |
| repomend.toml.example field drift | LOW | AC-P7-07 includes a parse check via `Config.load()`. |
| Not all 3 fixture findings fixable by Fix-Gen | MEDIUM | AC-P7-10 skip guard. End-to-end test skips (not fails) if Fix-Gen non-deterministic. |

---

## 6. Known Limitations (Deferred to Phase 8)

1. **Batch API deferred.** Anthropic's fire-and-forget Batch API is
   incompatible with the synchronous scan→fix→verify→PR pipeline.
   Phase 8 scope.
2. **Partial-batch resume.** No checkpoint/resume across Ctrl-C or
   crash. Phase 8.
3. **Auto-tuned concurrency ceiling.** `max_concurrent` is static
   config; no dynamic back-pressure. Phase 8.
4. **Progress TUI.** Concurrent repos produce interleaved log lines.
   Phase 8.
5. **Docker distribution image.** Shipping RepoMend as a container
   image is Phase 8+ (Q2 decision: skip for Phase 7).
6. **MkDocs site.** Full documentation site deferred (Q4 decision:
   docs/ folder only for Phase 7).
7. **Team config sharing.** Git-tracked shared config deferred to
   Phase 8 (Q3 decision: single-user only for Phase 7).

---

## 7. Proposed Architectural Decisions

### ADR-023 (proposed) — uv tool install as primary distribution
`uv tool install` (not pipx) for CLI distribution. Consistent with
existing uv stack. No new tool dependency for users already using uv.

### ADR-024 (proposed) — Skip Docker distribution image at Phase 7
No RepoMend application Docker image in Phase 7. The scanner sandbox
image (`repomend-scanner:0.1.0`) is an internal runtime primitive,
not a distribution artifact. `uv tool install` is sufficient for the
target user.

### ADR-025 (proposed) — Single-user config; repomend.toml.example
`repomend.toml` is machine-local. No git-tracked shared config or
dotfiles pattern in Phase 7. `repomend.toml.example` with inline
comments covers the template use case.

### ADR-026 (proposed) — docs/ folder extended; MkDocs deferred
`docs/user_guide.md` and updated `README.md` are the Phase 7
documentation deliverables. MkDocs and a public docs site are
Phase 8+ scope.

---

## 8. Out of Scope for Phase 7

- Anthropic Batch API
- Partial-batch resume / checkpointing
- Docker distribution image for the RepoMend application
- MkDocs / public documentation site
- Multi-user / team config sharing
- Auto-tuned concurrency ceiling
- Progress TUI
- Reviewer assignment on PRs
- SSH or gh CLI auth

---

## 9. Accountability Statement

_I, Yehor, confirm that this Phase 7 INTAKE contract accurately
captures the client goal, constraints, acceptance criteria, test
contract, risk areas, and known limitations for the Multi-Finding +
AsyncAnthropic + Distribution phase of RepoMend. By signing below I
authorise build work to begin. No implementation may start before
this signature._

**Signed:** Yehor  **Date:** 2026-06-23

---

_End of Phase 7 INTAKE contract._
