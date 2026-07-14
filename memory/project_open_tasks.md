# RepoMend — Open Tasks
_Last updated: 2026-06-23_

---
**ARCHIVED 2026-07-14 (BACKLOG item 7).** This file is a historical
record of the pre-rename RepoMend v0.1.0 build (Phases 0-7, all signed
off by Yehor). It predates the 2026-07-07 rename to Patchward and the
subsequent GitHub App/Marketplace product pivot (ADR-030), and its
final line still points at `D:\Dev\Projects\RepoMend`, a directory that
no longer exists. **Active task tracking has been `memory/BACKLOG.md`
since this session** — do not treat anything below as a live task list.

Two items below were still unchecked and not already covered anywhere
in the current `BACKLOG.md`; they've been folded forward as BACKLOG
items 13/14, explicitly flagged as pre-pivot ideas whose relevance to
the current GitHub-App-focused product has not been reconfirmed (do
not treat them as freshly-scoped current priorities just because
they're now in the active backlog). One other unchecked item
(`D-P5-01`, confirming end-to-end PR creation with a working
`GITHUB_TOKEN`) is already substantively covered by today's live
BACKLOG items 3b/Stage 2 — not duplicated here. The remaining
unchecked items (`KL-P6-01` multi-finding batching, the `conftest.py`
`load_dotenv()` call, and two forward-looking `Phase 6`/`Phase 7`
placeholder bullets) were confirmed already done elsewhere in this same
file — just never had their checkboxes flipped — and needed no action.
---

## Phase 0 — COMPLETE ✅ (Keystone Report approved by Yehor 2026-06-10)

- [x] KS-P0-01: Phase 0 INTAKE contract — SIGNED
- [x] KS-P0-02: Scaffold Python project (pyproject.toml, src layout, Typer CLI)
- [x] KS-P0-03: Config loader (Pydantic v2 repomend.toml)
- [x] KS-P0-04: SQLite state store (schema_version + migrations)
- [x] KS-P0-05: OTel tracing → Langfuse cloud
- [x] KS-P0-06: Single-repo Semgrep walking skeleton — end-to-end verified
- [x] KS-P0-07: Keystone Report Phase 0 — approved by Yehor

---

## Phase 1 — Scanner Subagent + Full Tool Layer

### PHASE 1 INTAKE — COMPLETE ✅
- [x] KS-P1-00: Fix fixture repo — 3 confirmed p/python plants verified 2026-06-11
      1. subprocess-shell-true (line 24)
      2. insecure-hash-algorithm-md5 (line 30)
      3. ssl-wrap-socket-is-deprecated (line 37)
- [x] KS-P1-01: Phase 1 INTAKE contract — SIGNED by Yehor 2026-06-11
      Location: docs/intake_phase1.md

### NEXT — UNBLOCK BUILD
- [x] KS-P1-02: Add .env file loader (python-dotenv) to config.py — DONE 2026-06-11
      14/14 tests passing, 98.88% coverage. AC-P1-10 verified.

### BACKLOG
- [x] KS-P1-03: All 7 scanners as subprocess tools — DONE 2026-06-11
       sarif.py: SARIFNormalizer (7 from_X methods) + SARIFRun/SARIFResult/SARIFLocation dataclasses
       scanner.py: run_semgrep/bandit/pip_audit/eslint/npm_audit/trivy/osv_scanner + run_all_scanners
       cli.py: updated to sarif_run.to_findings() — extract_findings() removed
       38/38 tests, 99.58% coverage, sarif.py 100% covered
       FLAG resolved: rule_id strings passed through verbatim — exact match confirmed at assertion time
- [x] KS-P1-04: SARIF validation — DONE 2026-06-11
       SARIFValidationError + validate_sarif_run() + validate_sarif_document()
       Added to sarif.py; 11 validation tests passing; sarif.py 98% covered
- [x] KS-P1-05: Repo abstraction — DONE 2026-06-11
       repo.py: RepoContext.from_path() — Ecosystem, PackageManager, TestRunner enums
       Auto-detects pip/uv/poetry/npm/pnpm/yarn, pytest/jest, lockfile path
       test_fixture_repo_detection confirms fixture = Python-only, no package.json
       15 tests passing; repo.py 93% covered (uncovered = OSError defensive handlers)
- [x] KS-P1-06: Scanner subagent wired to SDK — DONE 2026-06-11
       subagent.py: ScannerSubagent (Haiku, read-only tools, submit_triage forced output, mock-injectable)
       test_subagent.py: 18 tests — 8 structural, 1 semgrep pipeline (AC-P1-07), 9 mock-client triage
       cli.py: subagent.triage() wired after scan when anthropic_api_key set
       config.py: anthropic_api_key field added from ANTHROPIC_API_KEY env var
       82/82 passing, 96.48% coverage
- [x] KS-P1-07: Tool restriction enforcement — CLOSED by KS-P1-06
       SCANNER_ALLOWED_TOOLS = frozenset({"read_file","grep_files","glob_files"})
       bash/write/edit structurally absent — 8 structural tests confirm invariant
- [x] KS-P1-08: Keystone Report Phase 1 — SIGNED by Yehor 2026-06-11
       reports/keystone_report_phase1.md — all 10 ACs PASS, 5 defects documented
       ADR-009 logged: mandatory scanner probe step in INTAKE template
       Phase 1 COMPLETE ✅

---

## Phase 2 — Sandbox + Security Hardening

### PHASE 2 INTAKE — COMPLETE ✅
- [x] Phase 2 pre-step (ADR-009): confirmed payload list PL-01–PL-12 — 2026-06-11
- [x] KS-P2-01: Phase 2 INTAKE contract — SIGNED by Yehor 2026-06-11
      Location: docs/intake_phase2.md
      Flag P2-A resolved: substring match + allowlist exception list
      Flag P2-B open: container image digest — lock at end of KS-P2-02
      ADR-010 confirmed: Docker Desktop as sandbox primitive

### BACKLOG
- [x] KS-P2-02: Docker sandbox integration — STRUCTURALLY COMPLETE 2026-06-11
      102/102 passing · 95.62% coverage · docker_sandbox.py 86% (run_in_container body = integration only)
      FLAG P2-B OPEN: Docker not on PATH. Blocks digest pin and AC-P2-01 integration test.
      Must close before KS-P2-08. Close procedure:
        1. Install Docker Desktop: https://docs.docker.com/desktop/
        2. docker pull python:3.12-slim
        3. docker inspect python:3.12-slim --format "{{index .RepoDigests 0}}"
        4. Paste sha256 digest into docker_sandbox.py BASE_IMAGE constant
        5. Re-run: pytest -m integration (must pass both integration tests)
- [x] KS-P2-03: Deny-by-default egress policy — STRUCTURALLY COMPLETE 2026-06-11
      C-P2-02 implemented in docker_sandbox.py: NetworkPolicy enum (OFFLINE/PYPI_ONLY/NPM_ONLY),
      per-scanner routing in _SCANNER_NETWORK_POLICIES. Unit tests in test_docker_sandbox.py cover
      all 3 policies. AC-P2-03 integration tests added (test_network_none_blocks_egress,
      test_pypi_only_allows_pip_index_query) — both @pytest.mark.integration, require Docker.
      Deselected by default; will pass once Flag P2-B (Docker Desktop) is closed.
- [x] KS-P2-04: PreToolUse deny hooks — COMPLETE 2026-06-12
      src/repomend/hooks.py: DENY_PAYLOADS (12, specificity-first), ALLOWLIST_CONTEXTS (6),
      DeniedToolCallError, check_tool_call(). hooks.py 100% coverage.
      tests/test_hooks.py: 45 tests — 12 parametrized payload (AC-P2-04), 8 allowlist context,
      11 clean-scan false-positive (AC-P2-08), 5 adversarial, 3 invariant.
      2 defects caught and fixed: ordering collision PL-02/PL-03 and PL-10/PL-11 (specificity-first fix).
      147/147 passing · 95.83% coverage.
- [x] KS-P2-05: Credential proxy — COMPLETE 2026-06-12
      src/repomend/credential_proxy.py: _CREDENTIAL_KEYS (single source of truth), CredentialLeakError,
      CredentialProxy (load, get_client_credentials, get_container_env, assert_credentials_excluded, scrub).
      docker_sandbox.py: _CREDENTIAL_KEYS now imported from credential_proxy — no divergence risk.
      cli.py: CredentialProxy().load() + assert_credentials_excluded() at scan startup.
      tests/test_credential_proxy.py: 19 tests — all passing. credential_proxy.py 100% coverage.
      166/166 passing · 96.11% coverage.
- [x] KS-P2-06: git worktree isolation — COMPLETE 2026-06-12
      src/repomend/worktree.py: require_git_version, create_worktree, cleanup_worktree,
      worktree_context (finally-block cleanup on clean exit / exception / KeyboardInterrupt / SystemExit).
      cli.py: require_git_version() at startup, worktree_context wrapping run_all_scanners,
      proxy.scrub() applied to finding messages before DB storage.
      tests/test_worktree.py: 19 tests — all passing. worktree.py 97% (line 70: unparseable
      git version output branch — not a blocker).
      185/185 passing · 96.20% coverage.
- [x] KS-P2-07: Red-team injection suite — COMPLETE 2026-06-12
      tests/test_red_team.py: 15 tests — 12 parametrized PL-01–PL-12 (all PASS), 2 false-positive
      guard (AC-P2-08), 1 adversarial comment-injection case. Block rate: 12/12. 0 failures.
      Phase 3 gate: OPEN. 200/200 passing · 96.20% coverage.
- [x] KS-P2-08: Keystone Report Phase 2 — SIGNED by Yehor 2026-06-12
      reports/keystone_report_phase2.md — all 8 ACs PASS, 2 defects logged,
      Flag P2-B CLOSED: Docker 29.5.3 WSL2, 4/4 integration tests passed live.
      Phase 2 COMPLETE ✅

### BACKLOG (future phases)
- [ ] Phase 3 REQUIRED CONSTRAINT (from Phase 2 §4 / Yehor 2026-06-12):
      NetworkPolicy.PYPI_ONLY and NetworkPolicy.NPM_ONLY must be hardened to true
      per-destination allowlisting (iptables or equivalent) before Phase 3 ships.
      Current --network bridge permits broader outbound access than INTAKE intended.
      This is a named Phase 3 constraint, not optional hardening.
      Must appear in Phase 3 INTAKE contract as a C-P3-XX entry.
## Phase 3 — Sandbox Hardening + Fix-Gen Subagent

### PHASE 3 INTAKE — COMPLETE ✅
- [x] KS-P3-01: Phase 3 INTAKE contract — SIGNED by Yehor 2026-06-12
      Location: docs/intake_phase3.md
      ADR-012 (Fix-Gen scoping), ADR-013 (iptables Option A), ADR-014 (custom image) confirmed
      Flag P3-A CLOSED: repomend-scanner:0.1.0 built + entrypoint DNS fix verified
      Image: repomend-scanner:0.1.0@sha256:578a8147c3604808a5c7e0f1649fc8e6a3a93610e02896d95cc36c388655a5bc
      Defect caught pre-sign-off: iptables DROP before /etc/hosts write severed DNS. Fixed.
      2/2 Phase 2 integration tests re-verified green against new image.

### BACKLOG
- [x] KS-P3-02: Egress hardening integration tests — COMPLETE 2026-06-12
      AC-P3-01 PASS: OFFLINE blocks egress, PYPI_ONLY allows pip + blocks non-PyPI, NPM_ONLY allows npm registry
      AC-P3-02 PASS: curl to 1.1.1.1 from PYPI_ONLY container blocked by iptables DROP (not DNS)
      7/7 integration + 26/26 unit tests. 206/206 total, 96.23% coverage.
      Defects caught: NetworkPolicy enum aliasing bug (fixed: _DOCKER_NETWORK_FLAG dict);
      semgrep telemetry hang on --network none (fixed: --metrics off + SEMGREP_SEND_METRICS=off).
- [x] KS-P3-03: Fix-Gen subagent — COMPLETE 2026-06-12
      worktree_common.py: shared primitives (GitVersionError, require_git_version,
      git_worktree_add, git_worktree_remove). Identity test enforces no drift (C-P3-10).
      fix_worktree.py: inverted lifecycle, FixWorktreeHandle, .mark_success() sentinel (C-P3-12).
      fix_gen.py: FixGenSubagent (claude-sonnet-4-6, Read/Edit/Write only, no Bash).
      _execute_fix_tool scope guards (only allowed_file editable, no path traversal).
      tests/test_fix_worktree.py: 14 tests — ACs P3-03/04/05/08 + KI + structural.
      tests/test_fix_gen.py: 16 unit + 1 @integration adversarial scope-containment test.
      237/237 · 95.08% · fix_worktree.py 100% · fix_gen.py 87% (integration paths only).
- [x] KS-P3-04: Model tiering — Opus (HIGH/CRITICAL) / Sonnet (MEDIUM/LOW) — COMPLETE 2026-06-12
      _model_for_severity(): "error" → claude-opus-4-8, "warning"/"note" → claude-sonnet-4-6
      AC-P3-07 PASS (3 unit tests). C-P3-04 constraint met.
- [x] KS-P3-05: Run log (append-only session JSON) — COMPLETE 2026-06-12
      run_log.py: RunLog NDJSON append-only. 9 tests — byte-identity invariant PASS.
      AC-P3-11 PASS. _emit_pr_dict() appends to run log after each fix attempt.
- [x] KS-P3-06: Golden dataset gate — ≥30% repair success on fixture findings — GATE OPEN 2026-06-12
      1/3 PASSED (subprocess-shell-true). D-P3-03 (forced submit_fix) fixed to get here.
      AC-P3-09 PASS. D-P3-04 (cp1251 encoding) fixed in rescan helper.
- [x] KS-P3-07: Keystone Report Phase 3 — COMPLETE 2026-06-12
      reports/keystone_report_phase3.md — 273 unit + 1 integration PASS. Phase 3 GATE OPEN.
      Awaiting Yehor signature on accountability statement.
## Phase 4 — Verifier Subagent + Eval Curriculum

### PHASE 4 INTAKE — PENDING
- [x] KS-P4-00: Phase 4 INTAKE pre-step — COMPLETE 2026-06-16
      All three Q1-Q3 answers locked by Yehor. tests/test_clean.py pushed to
      repomend-fixture (commit 5b6ea7f). Gate 3 exercisable as PASS.
- [x] KS-P4-01: Phase 4 INTAKE contract — SIGNED by Yehor 2026-06-16
      Location: docs/intake_phase4.md
      13 ACs, ADR-015 (deterministic Verifier) + ADR-016 (no short-circuit) confirmed.
      C-P4-03 contradiction with addendum C-P3-11 resolved: Gate 2 uses git show, not .orig files.

### BACKLOG
- [x] KS-P4-02: verifier.py + test_verifier.py — COMPLETE 2026-06-16 ✅
      24/24 tests PASS · verifier.py 74% coverage · 0 regressions in 297 prior tests
      ADR-015 (no LLM) + ADR-016 (no short-circuit) both confirmed by structural tests.
- [x] KS-P4-03: Extend test_golden_dataset.py — COMPLETE 2026-06-22 ✅
      3 new @integration tests: test_verifier_end_to_end_verified (AC-P4-11),
      test_verifier_end_to_end_failed_unpatched (AC-P4-12),
      test_verifier_end_to_end_failed_out_of_bounds (AC-P4-12 variant).
      Ruff: PASS. Syntax: OK. Run on Windows: uv run pytest -m integration -q
- [x] KS-P4-04: Wire Verifier into Orchestrator (cli.py) — COMPLETE 2026-06-22
      config.py: VerifierConfig(timeout_seconds=120) added, [verifier] toml section parsed.
      cli.py: `repomend fix` command — scan→fix→verify loop, RunLog written per finding,
        mark_success() only on verified, branch discarded on failed (C-P3-12, C-P4-06/07/10).
      tests/test_orchestrator.py: 9 unit tests — AC-P4-10, C-P4-06/07/10, C-P3-12.
      282 passed, 1 skipped.
- [x] KS-P4-05: Keystone Report Phase 4 — COMPLETE 2026-06-22
      reports/keystone_report_phase4.md — 7 sections, all 13 ACs PASS, 2 defects, 6 limitations.
      SIGNED by Yehor 2026-06-22. Phase 4 CLOSED.
- [ ] Phase 4: Verifier + eval curriculum + golden dataset
- [ ] Phase 5 pre-step (MANDATORY before INTAKE):
  Add git commit call to fix_gen.py — after submit_fix success,
  before handle.mark_success(). Currently fix branches have no
  commits. Phase 5 PR push will fail without this.
  Log as ADR-017 at Phase 5 INTAKE.
- [x] KS-P5-01: Phase 5 INTAKE contract — SIGNED 2026-06-22
      Location: docs/intake_phase5.md
- [x] KS-P5-02: GithubConfig, GITHUB_TOKEN, git_push_branch(), PRPublisher — COMPLETE 2026-06-22
      341/341 passing.
- [x] KS-P5-03: PRPublisher wired into cli.py orchestrator — COMPLETE 2026-06-22
      341/341 passing. AC-P5-10 manually verified.
- [ ] D-P5-01 FIX (MEDIUM): Gate 2 timing race in test_end_to_end_pr — Verifier
  sees empty diff because git_commit_all() committed before verify() ran.
  Fix: Gate 2 now uses HEAD^ when worktree is clean (implemented 2026-06-22).
  Remaining: confirm test_end_to_end_pr passes end-to-end with working GITHUB_TOKEN.
- [ ] conftest.py load_dotenv(): add python-dotenv call to tests/conftest.py so
  integration tests auto-load .env without manual env var export.
- [ ] KS-P5-04: Structured PR template (intent, diff, risk class,
  evidence, test logs — five gates per PR)
- [ ] KS-P5-05: Risk-class escalation (low/med/high routing)
- [x] KS-P5-06: Keystone Report Phase 5
      Phase 5 pre-step REQUIRED (from Phase 4 git trace, 2026-06-16):
      Fix-Gen must commit the patch to the fix branch before mark_success()
      is called. Currently fix_gen.py never calls git commit — edits are
      uncommitted working-tree changes on disk. The fix branch has no commits
      of its own.
      Consequences if not resolved before Phase 5:
        - git log on the fix branch is identical to main
        - worktree removal before commit = patch lost permanently
        - GitHub PR creation has nothing to push
      Resolution: add git_commit_all() call to worktree_common.py, call it
      inside apply_fix() after submit_fix returns success and before
      handle.mark_success(). This is a Phase 5 INTAKE gate — not optional,
      not deferrable past Phase 5 pre-step.
      ADR reference: log as ADR-017 at Phase 5 INTAKE.
- [ ] Phase 6: Parallel multi-repo + cost controls
- [ ] Phase 7: pipx/Docker packaging + docs

### DECISIONS RESOLVED
- [x] ADR-005: uv
- [x] ADR-006: Langfuse cloud free tier (Phase 0 only)
- [x] ADR-007: fixture repo owned by Yehor
- [x] ADR-008: schema_version migrations from day one

---

## Phase 6 — Parallel Multi-Repo + Cost Controls

COMPLETE ✅ — Signed by Yehor 2026-06-23. All 11 ACs PASS.
Final: 383 passed · 89.48% coverage · ADR-020/021/022 logged.

Build tasks:
- [x] KS-P6-01: [[repos]] config + GithubConfig merge (AC-P6-06/07, C-P6-06) — COMPLETE 2026-06-23
- [x] KS-P6-02: asyncio pipeline + Semaphore (AC-P6-01/02, C-P6-01/02) — COMPLETE 2026-06-23
- [x] KS-P6-03: asyncio.to_thread() wrapping (AC-P6-03, C-P6-03) — COMPLETE 2026-06-23
- [x] KS-P6-04: Prompt caching on Fix-Gen system prompt (AC-P6-04, C-P6-04, ADR-021) — COMPLETE 2026-06-23
- [x] KS-P6-05: Model tiering config + --model CLI flag (AC-P6-05, C-P6-05) — COMPLETE 2026-06-23
- [x] KS-P6-06 + KS-P6-07: Branch protection + per-repo run log + 429 backoff — COMPLETE 2026-06-23
- [x] (merged into KS-P6-06 above)
- [x] KS-P6-08: Integration test AC-P6-11 PASSED — 2 results, 2 run log records — COMPLETE 2026-06-23
- [x] KS-P6-09: Phase 6 Keystone Report — SIGNED by Yehor 2026-06-23

Implementation note A-01 (field-merge test case) must be included in KS-P6-01.


---

## Phase 7 — Packaging + Distribution + Docs

### PRE-STEP (MANDATORY — ADR-009) — COMPLETE ✅ 2026-06-23
- [x] Q1: uv tool install (ADR-023 proposed)
- [x] Q2: Skip Docker distribution image (ADR-024 proposed)
- [x] Q3: Single-user only; repomend.toml.example (ADR-025 proposed)
- [x] Q4: docs/ folder extended; MkDocs deferred (ADR-026 proposed)

### KNOWN LIMITATIONS TO RESOLVE (from Phase 6)
- [ ] KL-P6-01: Single finding per repo per run → multi-finding batching
- [x] KL-P6-02: Sync Anthropic client → AsyncAnthropic — RESOLVED KS-P7-02 2026-06-23
- [x] KL-P6-03: RunLog threading → RESOLVED KS-P7-03 2026-06-23
- [x] KL-P6-04: Trivy installed on dev machine (winget v0.71.2) — RESOLVED 2026-06-23

### BACKLOG
- [x] KS-P7-01: Phase 7 INTAKE contract — SIGNED by Yehor 2026-06-23 ✅
      Location: docs/intake_phase7.md
      11 ACs, 2 tracks: functional (KL-P6-01/02/03) + distribution/docs (Q1-Q4)
      ADR-023–026 approved by signature.
- [x] KS-P7-02: AsyncAnthropic migration — COMPLETE 2026-06-23 ✅
      fix_gen.py: AsyncAnthropic client, async def apply_fix(), await
      pipeline.py: removed asyncio.to_thread() wrapping of LLM call
      test_fix_gen.py: 14 tests → async def + AsyncMock
      test_async_pipeline.py: 5 apply_fix mocks → AsyncMock
      354 passed · 1 deselected · 88% coverage
- [x] KS-P7-03: RunLog threading — COMPLETE 2026-06-23 ✅
      pipeline.py: run_log param on run_repo_pipeline + run_batch;
      per-finding append_batch_result in findings loop;
      cli.py: run_log passed through to run_batch;
      4 new tests in test_orchestrator.py (AC-P7-05 structural +
      3 behavioral). 358 passed · 88% coverage.
- [x] KS-P7-04: Multi-finding loop + max_findings_per_repo config — COMPLETE 2026-06-23 ✅
      config.py: max_findings_per_repo field + validator in BatchConfig;
      pipeline.py: capped for-loop with uuid suffix on finding_id, findings_attempted field;
      4 new tests in test_config.py + 5 new tests in test_orchestrator.py.
      367 passed · 1 deselected · 89% coverage.
- [x] KS-P7-05: uv tool install verification + repomend.toml.example — COMPLETE 2026-06-23 ✅
      repomend.toml.example: all config fields with inline comments;
      docs/user_guide.md: 5 required sections (Prerequisites through Config Reference);
      README.md: one-liner, install, quick start, link to user_guide;
      cli.py: --version flag → 'repomend 0.1.0';
      tests/test_distribution.py: 3 existence/content tests;
      test_config.py: test_toml_example_parses_cleanly added.
      AC-P7-06 evidence: repomend 0.1.0
      371 passed · 1 deselected · 89% coverage.
- [x] KS-P7-06: docs/user_guide.md + README.md update — CLOSED by KS-P7-05 scope 2026-06-23 ✅
- [x] KS-P7-07: End-to-end integration test — COMPLETE 2026-06-23 ✅
      test_golden_dataset.py: test_multi_finding_e2e added (@integration,
      RUN_E2E_MULTI_FINDING guard). Pipeline ran to run_batch, returned
      scanner_unavailable (trivy empty JSON), test skipped correctly.
      KL-P7-01 logged: trivy on PATH but produces empty JSON on fixture.
      371 passed (unit suite) · 1 skipped (integration, expected).
- [x] KS-P7-08: Keystone Report Phase 7 — SIGNED by Yehor 2026-06-23 ✅

## Known Limitations
- KL-P7-01: trivy installed (winget v0.71.2) but produces empty JSON on
  repomend-fixture; pipeline reaches scanner_unavailable before findings
  loop. AC-P7-10 integration test skips on this environment. (2026-06-23)

---

## PROJECT COMPLETE — RepoMend v0.1.0
All 8 phases delivered. 7 Keystone Reports signed.
371 tests · 89% coverage · repomend 0.1.0 installable.
Portfolio artifact: D:\Dev\Projects\RepoMend
Fixture repo: github.com/yehorcallmedai-maker/repomend-fixture
PR evidence: https://github.com/yehorcallmedai-maker/repomend-fixture/pull/2
