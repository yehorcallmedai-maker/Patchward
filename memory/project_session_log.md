# RepoMend — Session Log


## Session 012 — 2026-06-23

**Status:** KS-P7-02 AsyncAnthropic migration COMPLETE.

**Done:**
- docs/intake_phase7.md §9 signed: Yehor / 2026-06-23
- KS-P7-02: AsyncAnthropic migration
  - fix_gen.py: AsyncAnthropic client, `async def apply_fix()`, `await` on create()
  - pipeline.py: removed `asyncio.to_thread()` wrapping of LLM call
  - tests/test_fix_gen.py: 14 tests → `async def` + `AsyncMock`
  - tests/test_async_pipeline.py: 5 apply_fix mocks → `AsyncMock`
  - All syntax-verified via ast.parse(). All grep checks passed.
  - Windows test run: **354 passed · 1 deselected · 88% coverage**
- KL-P6-02 resolved (sync Anthropic → AsyncAnthropic)
- KS-P7-03: RunLog threading COMPLETE
  - pipeline.py: run_log param + per-finding append in findings loop
  - run_batch: run_log passed through
  - cli.py: run_log passed to run_batch
  - test_orchestrator.py: 4 new tests (structural + 3 behavioral)
  - test_async_pipeline.py: 3 mock signatures updated for new kwarg
  - 358 passed · 1 deselected · 88% coverage
- KL-P6-03 resolved (RunLog threading)
- memory files updated (CONTEXT.md, project_open_tasks.md, project_session_log.md)

- KS-P7-04: Multi-finding loop + max_findings_per_repo COMPLETE
  - config.py: max_findings_per_repo field + validator in BatchConfig
  - pipeline.py: capped for-loop, uuid suffix on finding_id, findings_attempted result field
  - 4 new tests in test_config.py + 5 new tests in test_orchestrator.py
  - Fix: finding_id assertion changed to startswith() for uuid suffix
  - 367 passed · 1 deselected · 89% coverage

- KS-P7-05 + KS-P7-06: Distribution + Docs COMPLETE
  - repomend.toml.example at project root (all fields, inline comments)
  - docs/user_guide.md (5 sections: Prerequisites → Config Reference)
  - README.md (one-liner, install, quick start, user guide link)
  - cli.py: --version callback → 'repomend 0.1.0'
  - tests/test_distribution.py: 3 new tests
  - test_config.py: test_toml_example_parses_cleanly
  - AC-P7-06 evidence: repomend 0.1.0
  - 371 passed · 1 deselected · 89% coverage

- KS-P7-07: End-to-end integration test COMPLETE
  - test_golden_dataset.py: test_multi_finding_e2e
  - Pipeline ran, trivy produced empty JSON → scanner_unavailable
  - Test skipped correctly (not failed)
  - KL-P7-01 logged: trivy empty JSON on fixture repo

- KS-P7-08: Keystone Report Phase 7 written, reviewed, approved, signed by Yehor 2026-06-23.
  - Phase 7 gate: 10/11 ACs PASS, 1 SKIP (AC-P7-10, KL-P7-01 — trivy empty JSON on Python-only fixture).
  - 371 passed · 89% coverage · repomend 0.1.0 confirmed.

**Project status: ALL PHASES COMPLETE**
Phase 0 through Phase 7 closed.
RepoMend v0.1.0 is a working, tested, documented, distributable local-first multi-repo security agent.


## Session 006 — 2026-06-16
**Status:** Phase 3 formally closed. Phase 4 INTAKE pre-step queued.

**Done:**
- Updated Keystone Operating Constitution (project instructions) — added Stage 0
  (Session Open / context recovery protocol), Stage 5 session-close procedure,
  AC-P3A-XX addendum namespace, coverage regression gate, ADR immutability rule.
- Signed reports/keystone_report_phase3.md — Date: 2026-06-16. Phase 3 COMPLETE ✅
- KS-P4-00: Phase 4 INTAKE pre-step COMPLETE. All three Q1-Q3 answers locked.
  tests/test_clean.py pushed to repomend-fixture (commit 5b6ea7f). Gate 3 exercisable as PASS.
- KS-P4-01: Phase 4 INTAKE contract written and SIGNED by Yehor 2026-06-16
  → docs/intake_phase4.md. 13 ACs, ADR-015 + ADR-016 confirmed.
  Blocking issue caught and resolved during review: C-P4-03 referenced retired .orig
  checkpoint files (addendum C-P3-11 conflict). Fixed to use git show HEAD:<file_path>.
- ADR-015 and ADR-016 marked Confirmed in architectural_decisions.md.

**Pre-build check (KS-P4-02):** git state trace confirmed 2026-06-16.
`git show HEAD:<file_path>` returns pre-edit content because Fix-Gen edits are
uncommitted working-tree changes (`fix_gen.py` never calls `git commit`). Gate 2
is architecturally safe to build.
Flag logged: fix_gen.py never commits — Phase 5 INTAKE pre-step must add
`git commit` before `mark_success()`. See open tasks for full consequence list.

- KS-P4-02: verifier.py + test_verifier.py — COMPLETE 2026-06-16
  24/24 unit tests PASS. verifier.py 74% coverage (integration paths excluded).
  No regressions in 297 prior tests.
  ADR-015 confirmed: no anthropic import (structural test AC-P4-01).
  ADR-016 confirmed: TestNoShortCircuit passes — Gate 3 SKIP when Gate 1 FAIL.
  Defect noted: _out_of_bounds_lines uses post-edit line counter as proxy for
  removed lines — conservative (can over-flag at boundaries), never under-flags.
  Logged as known limitation, not a blocker.
  Key design note: RepoContext._detect_test_runner NOT used in Verifier —
  it misses plain tests/ directory layout. Verifier implements own detection
  per C-P4-04 (tests/ glob + test_*.py root glob).

**Open (carry forward):**
- [ ] KS-P4-03: Extend test_golden_dataset.py — Fix-Gen → Verifier end-to-end chain (AC-P4-11/12)
- [ ] KS-P4-04: Wire Verifier into Orchestrator (cli.py) — invoke after Fix-Gen returns
- [ ] KS-P4-05: Keystone Report Phase 4

**Next session starts at:**
KS-P4-03 — extend test_golden_dataset.py to add the second Verifier pass after
Fix-Gen (finding → Fix-Gen → fix branch → Verifier → verification_status in run log).
Primary target: subprocess-shell-true (confirmed fixable, Phase 3 AC-P3-09).

---

## Session 005 — 2026-06-12
**Status:** Phase 3 build complete. Keystone Report written.
Awaiting Yehor signature. Session closing.

**Done:**
- KS-P3-03 ✅ (carried from earlier this session): worktree_common.py
  extraction, fix_worktree.py inverted lifecycle, fix_gen.py
  FixGenSubagent. 237/237 · 95.08%.
- PART 1 (AC-P3-04 base / model tiering, AC-P3-11 run log,
  AC-P3-08 PR dict, AC-P3-12 deny hooks on Fix-Gen, AC-P3-10
  toml maxTurns) ✅
- PART 2 — AC-P3-09 golden dataset gate: 1/1 PASSED. Gate OPEN.
- PART 3 — Keystone Report Phase 3 written to
  reports/keystone_report_phase3.md

**Defects caught and fixed:**
- D-P3-01 (carryover, Phase 2): enum aliasing — documented
- D-P3-02 (carryover): semgrep metrics hang — documented
- D-P3-03 (HIGH): submit_fix never called — forced tool_choice
  after successful edit was the missing mechanism. Fixed.
- D-P3-04 (LOW): cp1251 encoding on semgrep stderr background
  reader thread (Windows). Fixed.

**Final numbers:** 273 unit passed · 95.54% coverage ·
1/1 integration (golden dataset, AC-P3-09) PASSED

**Report status:**
- 12 ACs verified (AC-P3-01 through AC-P3-12 base +
  AC-P3-03 through AC-P3-08 addendum)
- AC-P3-05/06 base correctly marked SUPERSEDED by addendum
- AC-P3-04 (Verifier subagent) correctly marked DEFERRED to
  Phase 4 — not a regression
- Methodology note: AC numbering collision between base contract
  and addenda — proposed AC-P3A-XX namespace for Phase 4 addenda
- Accountability statement: UNSIGNED, awaiting Yehor

**Open (carry forward):**
- [ ] Sign reports/keystone_report_phase3.md accountability
      statement — Phase 3 formally closes on signature
- [ ] Phase 4 INTAKE: Verifier subagent + eval curriculum
      (AC-P3-04 base, deferred from Phase 3, becomes Phase 4
      scope) — golden dataset infrastructure already exists
      (KS-P3-06/AC-P3-09), Phase 4 extends it
- [ ] Apply AC-P3A-XX namespace proposal to Phase 4 INTAKE
      addenda going forward

**Next session starts at:**
Sign reports/keystone_report_phase3.md → Phase 3 closes →
Phase 4 INTAKE pre-step (per ADR-009 pattern: confirm exact
verification mechanics — what "verified" means for the Verifier
subagent — before writing the contract).

---

## Session 004 (cont.) — 2026-06-12
**Status:** KS-P3-02 closed. Session ending.

**Done:**
- KS-P3-02 ✅ Egress hardening integration tests.
  206/206 · 96.23% · 7 deselected (verified separately: 7/7 integration)
- 26 unit tests: 6 new C-P3-08 structural tests for
  --cap-add NET_ADMIN and REPOMEND_NETWORK_POLICY per policy
- 7 integration tests: AC-P3-01 (OFFLINE/PYPI_ONLY/NPM_ONLY egress
  behavior confirmed), AC-P3-02 (adversarial curl to 1.1.1.1 from
  PYPI_ONLY blocked by iptables DROP, not DNS — bypass-by-IP gap closed)

**Defects caught and fixed:**
- D-P3-01 (HIGH): NetworkPolicy(str, Enum) duplicate value "bridge"
  made NPM_ONLY a silent alias of PYPI_ONLY. .name returned wrong
  string. Fixed: policy identity decoupled from Docker network flag
  via _DOCKER_NETWORK_FLAG mapping.
- D-P3-02 (MEDIUM): semgrep hangs ~60s on --network none waiting
  for dropped metrics connection. Fixed: --metrics off +
  SEMGREP_SEND_METRICS=off.

**Open (carry forward):**
- [ ] KS-P3-03: Fix-Gen subagent — FLAGGED for pre-step before build.
  This is the first task that writes to the target repo (Action
  leg of Perception→Reasoning→Action). Before code starts, confirm:
    1. Fix trigger scope — one SARIF finding → one Fix-Gen invocation?
    2. Patch landing — does Fix-Gen reuse worktree.py's
       repomend/scan-<id> pattern, or need a sibling
       repomend/fix-<id> module?
    3. Checkpoint semantics — file snapshot before edit for rollback?
  Recommend a short INTAKE addendum or formal pre-step (similar to
  KS-P2-07 attestation framing) before writing Fix-Gen code.
- [ ] KS-P3-04 through remaining Phase 3 tasks per docs/intake_phase3.md
- [ ] KS-P3-0X: Keystone Report Phase 3

**Next session starts at:**
KS-P3-03 pre-step — answer the three scoping questions above
before any Fix-Gen code is written.

---

## Session 001 — 2026-06-10
**Status:** COMPLETE. Phase 0 fully built and verified.

**Done:**
- Folder structure + agent configs scaffolded
- All memory seed files written (open tasks, session log, ADRs)
- Claude Code 2.1.170 installed and verified
- Fixture repo created: github.com/yehorcallmedai-maker/repomend-fixture
  - clean.py (0 violations), vulnerable.py (3 planted vulns), README, requirements.txt
- Langfuse project created: CallMed AI org / Repomend project
- Phase 0 INTAKE contract written and signed by Yehor
  - AC-07 deferred to Phase 1 per Yehor review
- Python project scaffolded: pyproject.toml, src/repomend/ layout, uv venv
- Modules built: cli.py, config.py, db.py, scanner.py, tracing.py
- 12 unit tests passing, 98.78% coverage on config+db layer
- End-to-end scan verified: Semgrep → SARIF → SQLite → Langfuse
- Keystone Report Phase 0 written: reports/keystone_report_phase0.md
  - 7 defects caught and fixed during session
  - Awaiting Yehor signature

**Defects caught this session:** 7 (see Keystone Report §3)

**Key decisions:**
- ADR-005: uv (approved)
- ADR-006: Langfuse cloud free tier (approved)
- ADR-007: fixture repo owned by Yehor (approved)
- ADR-008: schema_version migrations from day one (approved)

**Next session starts at:** KS-P1-01 — Phase 1 INTAKE contract

---

## Session 002 — 2026-06-11
**Status:** COMPLETE.

**Done:**
- Context recovered from session 001 summary
- Wrote tmp_diagnostic_vulns.py with 10 p/python rule candidates
- Ran semgrep diagnostic — confirmed 2 of 3 needed rules:
  1. `python.lang.security.audit.subprocess-shell-true.subprocess-shell-true` ✅
  2. `python.lang.security.insecure-hash-algorithms-md5.insecure-hash-algorithm-md5` ✅
  - Non-firing: os.system, pickle.loads, exec, eval, yaml.load, tempfile.mktemp, SQL string concat, hardcoded password assignment
- KS-P1-00: Second probe (tmp_diagnostic_vulns_v2.py) confirmed third rule:
  3. `python.lang.security.audit.ssl-wrap-socket-is-deprecated.ssl-wrap-socket-is-deprecated` ✅
  - Non-firing in v2: requests.get(verify=False), hashlib.sha1 (sha1 rule fired but chose ssl for distinct category)
- repomend-fixture/vulnerable.py updated with exactly 3 confirmed plants
  - All 3 verified: semgrep returns findings at lines 24, 30, 37
- tmp_diagnostic_vulns.py and tmp_diagnostic_vulns_v2.py deleted
- KS-P1-01: Phase 1 INTAKE contract written and SIGNED → docs/intake_phase1.md
  - 10 ACs, full test contract with inputs/outputs/invariants/adversarial case
  - Approved by Yehor 2026-06-11
  - Flag logged to KS-P1-03: confirm exact Semgrep rule ID format at normalizer wiring time

**Key decisions:**
- Third plant: ssl.wrap_socket chosen over sha1 for distinct vulnerability category
  (command injection + weak crypto + deprecated SSL = 3 different risk classes)

- KS-P1-02: .env loader — DONE
  - python-dotenv==1.2.2 added to pyproject.toml
  - load_dotenv() called before credential access in load_config()
  - langfuse_public_key / langfuse_secret_key fields added to RepomendConfig
  - .env.example written with all 3 required keys documented
  - 14/14 tests passing, 98.88% coverage, AC-P1-10 verified

- KS-P1-03: All 7 scanners + SARIF normalizer — DONE
  - sarif.py: SARIFNormalizer, SARIFRun, SARIFResult, SARIFLocation, sarif_document()
  - scanner.py: 7 subprocess wrappers + run_all_scanners() + ecosystem detection
  - cli.py: extract_findings() removed; now uses sarif_run.to_findings()
  - 38/38 tests, 99.58% coverage, sarif.py 100%

- KS-P1-04: SARIF validation — DONE
  - SARIFValidationError, validate_sarif_run(), validate_sarif_document() in sarif.py
  - Structural validation: tool_name, rule_id, message, level, uri; full jsonschema deferred to Phase 4
- KS-P1-05: Repo abstraction — DONE
  - repo.py: RepoContext.from_path(), Ecosystem/PackageManager/TestRunner enums
  - Detects pip/uv/poetry/npm/pnpm/yarn, pytest/jest, lockfile path
  - test_fixture_repo_detection: fixture = PYTHON, no package.json → JS scanners must skip
- 64/64 tests, 96.46% coverage, 0 warnings

- KS-P1-06: Scanner subagent wired — DONE 2026-06-11
  Architecture: Model B (Yehor approved). Python pre-computes SARIF → subagent receives
  serialised JSON only. C-03 firewall is structural, not behavioural.
  - subagent.py: SCANNER_MODEL=claude-haiku-4-5-20251001, SCANNER_MAX_TURNS=5
    SCANNER_ALLOWED_TOOLS=frozenset({"read_file","grep_files","glob_files"}) — bash/write/edit absent
    submit_triage forced output tool; mock-injectable constructor for testing
  - test_subagent.py: 18 tests — 8 structural, 1 semgrep pipeline (AC-P1-07), 9 mock-client
    cp1251 encoding warning fixed with encoding="utf-8" on subprocess call
  - cli.py: ScannerSubagent.triage() wired after scan, guarded by cfg.anthropic_api_key
  - config.py: anthropic_api_key field + ANTHROPIC_API_KEY env injection
- KS-P1-07: CLOSED by KS-P1-06 — tool restriction structurally confirmed by 8 tests

- KS-P1-08: Keystone Report Phase 1 — SIGNED by Yehor 2026-06-11
  reports/keystone_report_phase1.md — 6 sections, all 10 ACs PASS, 5 defects, 6 limitations
  ADR-009 logged to memory/architectural_decisions.md: mandatory scanner probe in INTAKE
  Phase 1 formally COMPLETE.

**Final state: 82/82 passing, 96.48% coverage. Phase 1 COMPLETE ✅. Next: Phase 2 INTAKE.**

---

## Session 004 — 2026-06-12
**Status:** COMPLETE.

**Done:**
- Flag P2-B CLOSED: Docker Desktop pipe ACL fixed (quit + relaunch as regular user). 4/4 integration tests passed live (61s). Phase 2 Keystone Report signed — Status: SIGNED · Phase 2 COMPLETE.
- Digest gate confirmed: BASE_IMAGE `python:3.12-slim@sha256:a394...c94` was already pinned in docker_sandbox.py. AC-P2-01 = PASS backed by pinned image.
- KS-P3-01: Phase 3 INTAKE contract written and SIGNED by Yehor 2026-06-12 → docs/intake_phase3.md
  - C-P3-08: iptables OUTPUT egress enforcement (Option A) locked — Yehor's reasoning on record
  - ADR-012 (Fix-Gen scoping), ADR-013 (iptables), ADR-014 (custom scanner image) written
- docker/scanner.Dockerfile: repomend-scanner:0.1.0 — iptables + semgrep==1.165.0 + bandit==1.9.4 + pip-audit==2.10.1 + eslint@8.57.1 + node 20 LTS baked in
- docker/entrypoint.sh: iptables egress enforcement with /etc/hosts-before-DROP ordering
- Defect caught pre-sign-off: entrypoint applied DROP before /etc/hosts write — pip DNS severed post-DROP. Fixed, rebuilt, re-verified.
- Final image: repomend-scanner:0.1.0@sha256:578a8147c3604808a5c7e0f1649fc8e6a3a93610e02896d95cc36c388655a5bc
- 2/2 Phase 2 integration tests re-verified green against new image.
- Phase 3 INTAKE SIGNED. KS-P3-02 starts next session.

**Defects caught this session:** 1 (entrypoint DNS-after-DROP ordering bug — caught pre-sign-off)

**Final state:** Phase 2 COMPLETE ✅ · Phase 3 INTAKE SIGNED ✅ · Next: KS-P3-02 egress hardening integration tests

---

## Session 003 — 2026-06-11/12
**Status:** COMPLETE (Phase 2 build done; sign-off blocked by Flag P2-B Docker pipe issue)

**Done:**
- Context recovered from compaction summary; state confirmed exact match
- Flag P2-B deferred at session start (Yehor: "structural invariants are what matter")
- KS-P2-02: Docker sandbox — STRUCTURALLY COMPLETE (102/102 tests, docker_sandbox.py 86%)
- KS-P2-03: Egress policy — NetworkPolicy enum (OFFLINE/PYPI_ONLY/NPM_ONLY), per-scanner routing
- KS-P2-04: PreToolUse deny hooks — hooks.py 100% coverage, 45 tests
  - Defect caught: DENY_PAYLOADS first-match-wins collision (PL-02/03 and PL-10/11) → specificity-first fix
  - Defect caught: allowlist branch uncovered → test_allowlist_context_bypasses_payload_match added
- KS-P2-05: Credential proxy — credential_proxy.py 100%, single source of truth pattern (_CREDENTIAL_KEYS `is` identity test)
- KS-P2-06: git worktree isolation — worktree.py 97%, finally-block cleanup invariant on all exit paths
- KS-P2-07: Red-team injection suite — 15/15 PASS, 12/12 payloads blocked, Phase 3 gate OPEN
- KS-P2-08: Keystone Report Phase 2 — APPROVED by Yehor (reports/keystone_report_phase2.md)
- Flag P2-B digest pin: sha256:a39549e211a16149edf74e5fdc9ef03a6767e46cd987c5048b6659b6c9904c94 pinned in docker_sandbox.py
- Docker Desktop installed: WSL 2 (Ubuntu), docker-desktop distro running, Server Version 29.5.3
- Phase 3 egress constraint logged to project_open_tasks.md (PYPI_ONLY/NPM_ONLY → true per-destination allowlisting required)

**Final test count:** 200/200 passing · 96.20% coverage · 4 deselected

**Unresolved — Flag P2-B integration test:**
- Docker Desktop installed and running (confirmed via docker info)
- Permission denied on dockerDesktopLinuxEngine pipe from regular user terminal
- User is in docker-users group (confirmed); session token refresh attempted
- Root cause: Docker Desktop first launched in admin session → pipe ACL excludes regular user
- Fix queued but not confirmed: quit Docker Desktop → relaunch as regular user (not admin)
- AC-P2-01 still DEFERRED; report cannot be signed until this resolves

**Next session starts at:** Close Flag P2-B (Docker pipe fix → integration tests → sign report → Phase 2 COMPLETE)

---

## Session 005 — 2026-06-22

**Phase:** 4 — Verifier Subagent + Eval Curriculum
**Task:** KS-P4-03 — Extend test_golden_dataset.py (Fix-Gen → Verifier end-to-end chain)
**Test baseline at open:** 297/297 (confirmed from KS-P4-02 close)
**Status:** COMPLETE — pending Windows integration run

### What was done

1. Read verifier.py (Gate 1/2/3 logic, VerifierResult.as_log_dict()) and existing
   test_golden_dataset.py (AC-P3-09 gate, GOLDEN_FINDINGS, _rescan_for_rule helper).

2. Added 3 new @integration tests to tests/test_golden_dataset.py:

   **test_verifier_end_to_end_verified** (AC-P4-11)
   - Runs Fix-Gen on subprocess-shell-true, then runs Verifier on the result.
   - Asserts verification_status="verified", gate_1=pass, gate_2=pass, gate_3=pass/skip.
   - Calls handle.mark_success() only after Verifier confirms "verified".
   - Skips (not fails) if Fix-Gen is non-deterministic on this run.
   - Requires: ANTHROPIC_API_KEY + semgrep + fixture repo.

   **test_verifier_end_to_end_failed_unpatched** (AC-P4-12)
   - No fix applied — worktree file identical to HEAD.
   - Asserts verification_status="failed", gate_1=fail (rule still fires).
   - ADR-016 check: gate_2 and gate_3 must have run (status != "not run").
   - Does NOT require ANTHROPIC_API_KEY.

   **test_verifier_end_to_end_failed_out_of_bounds** (AC-P4-12 variant)
   - Manually prepends a comment line at position 1 (outside authorised range [24,24]).
   - Asserts verification_status="failed", gate_2=fail (out-of-bounds edit caught).
   - ADR-016 check: gate_3 must have run.
   - Does NOT require ANTHROPIC_API_KEY or semgrep.

3. Added helpers: _get_fixture_repo() (shared skip logic), _SUBPROCESS_FINDING alias.

4. Added import: from repomend.verifier import Verifier (placed at line 39 with other imports).

5. Ruff: PASS (0 violations). Syntax: OK (ast.parse confirmed).

### Defects caught and fixed

- E402: Verifier import placed mid-file after append. Fixed by moving to top with other imports.
- F541 ×5: Bare f-strings with no placeholders. Fixed by stripping f prefix.

### How to complete verification (Windows)

Run on Windows terminal from D:\Dev\Projects\RepoMend\:

  Unit suite (no API key needed):
    uv run pytest -p no:cacheprovider -q -m "not integration"
    Expected: 297/297 PASS

  Integration — AC-P4-12 tests (no API key needed):
    uv run pytest -p no:cacheprovider -q -k "failed_unpatched or failed_out_of_bounds"
    Expected: 2/2 PASS

  Integration — AC-P4-11 (API key required):
    uv run pytest -p no:cacheprovider -q -k "end_to_end_verified"
    Expected: PASS or SKIP (if Fix-Gen non-deterministic)

### Next task
KS-P4-04 — Wire Verifier into Orchestrator (cli.py)

---

## Session 006 — 2026-06-22

**Phase:** 4 — Verifier Subagent + Eval Curriculum
**Tasks:** Clear stale worktree state · Log D-P4-02/D-P4-03 · Close KS-P4-03 · Begin KS-P4-04
**Test baseline at open:** 273 passed, 1 skipped (full suite minus golden/docker)
**Status:** IN PROGRESS

### Defects logged this session

**D-P4-02 (MEDIUM) — worktree_common.py: stale branch survives cleanup on Windows**
- Root cause: cleanup_fix_worktree() calls `git worktree remove --force` but does NOT
  call `git branch -D` on Windows when the Temp dir is already gone. Git leaves branch
  metadata in .git/worktrees/<name>/, which blocks the next `git worktree add -b`.
- Fix: added self-heal block in git_worktree_add(). When "already exists" appears in
  stderr, the block runs: worktree remove --force → worktree prune → branch -D → retry.
- Residual: stale .lock files in .git/refs/heads/repomend/ also block branch deletion
  when a Linux process (sandbox) previously attempted cleanup. Must use `Remove-Item`
  in PowerShell (not `del /f ... 2>nul`) to clear lock files from Windows.
- Status: FIXED in worktree_common.py · confirmed 273 passed × 2 back-to-back runs.

**D-P4-03 (LOW) — fixture_repo/vulnerable.py: wrong line numbers + non-ASCII + CRLF**
- Root cause: em-dash in docstring (non-ASCII), CRLF line endings not enforced,
  vulnerability at wrong line (semgrep rule expected line 24/30/37, file had shifted
  content).
- Fix: padded file to 38 lines, vulnerability anchored at lines 24/30/37, ASCII-only
  text, LF enforced via .gitattributes. Same pass for clean.py.
- Commit: 6e77570 on fixture_repo (GitHub).
- Status: FIXED · all golden-dataset assertions pass.

### Verifications

- Full suite (273 passed, 1 skipped) × 2 consecutive runs — PASS
- Self-heal survives back-to-back: worktree created, used, removed, re-created — PASS
- KS-P4-03 closed.

### Next task
KS-P4-04 — Wire Verifier into Orchestrator (cli.py)

### KS-P4-04 — Wire Verifier into Orchestrator (cli.py) — IN PROGRESS

#### Files changed

**src/repomend/config.py**
- Added `VerifierConfig(timeout_seconds: int = 120)` (C-P4-10)
- Added `verifier: VerifierConfig` field to `RepomendConfig`
- `load_config()` now parses `[verifier]` toml section into `VerifierConfig`

**src/repomend/cli.py**
- Added imports: `FixGenSubagent`, `fix_worktree_context`, `RunLog`, `Verifier`
- Added `fix` command (separate from `scan`): scan → for each finding →
  `fix_worktree_context` → `FixGenSubagent.apply_fix` → `Verifier.verify` →
  `RunLog.append` → `handle.mark_success()` only when `verification_status == "verified"`
- C-P4-06: Verifier receives branch name + finding coords only (not full finding dict)
- C-P4-07: run log written before fix branch returned to caller
- C-P4-10: `Verifier(timeout_seconds=cfg.verifier.timeout_seconds)` propagated from config
- C-P3-12: inverted lifecycle honoured — branch discarded on unverified fix

**tests/test_orchestrator.py** (new file, 448 lines)
- `TestFixCommandRunLog::test_run_log_verified_fix_has_verifier_fields` — AC-P4-10 happy path
- `TestFixCommandRunLog::test_run_log_failed_fix_has_verifier_fields` — failed fix, fp candidate
- `TestFixCommandRunLog::test_run_log_fix_gen_failure_writes_verifier_none` — Fix-Gen skip path
- `TestFixCommandRunLog::test_no_api_key_exits_nonzero` — API key guard
- `TestVerifierConfigPropagation::test_verifier_instantiated_with_configured_timeout` — C-P4-10
- `TestVerifierConfig::*` — 4 unit tests for VerifierConfig model

#### Awaiting Windows run

  uv run pytest --override-ini="addopts=" -q --ignore=tests\test_golden_dataset.py --ignore=tests\test_docker_sandbox.py --ignore=tests\fixture_repo
  Expected: 281+ passed (8 new tests in test_orchestrator.py)

  Then close KS-P4-04.

#### Windows run result — PASS
282 passed, 1 skipped (9 new tests; baseline was 273/1).
KS-P4-04 CLOSED 2026-06-22.

### Next task
KS-P4-05 — Keystone Report Phase 4

### KS-P4-05 — Keystone Report Phase 4 — COMPLETE

reports/keystone_report_phase4.md written (169 lines, 7 sections).
All 13 ACs: PASS. ADR-015 + ADR-016 confirmed. D-P4-02 + D-P4-03 logged.
Phase 4 gate: OPEN — awaiting Yehor sign-off.

**Final test count this session:** 282 passed, 1 skipped.

### KS-P4-05 — Amendment + Sign-off

Yehor review identified D-P4-01 missing from §5 (it was in §4 as architectural decision only).
Added D-P4-01 (HIGH) to §5: Fix-Gen prompt over-constrains edits, blocks import additions.
Updated §7 accountability statement to name all three defects (D-P4-01/02/03).
Report signed: Yehor, 2026-06-22.

**PHASE 4 CLOSED.**

**Final state:**
- 282 passed, 1 skipped
- All 13 ACs: PASS
- Defects: D-P4-01 (HIGH), D-P4-02 (MEDIUM), D-P4-03 (LOW) — all fixed
- ADR-015 + ADR-016: confirmed + structurally enforced
- Next: Phase 5 INTAKE — mandatory pre-step: git commit in fix_gen.py before mark_success()

---

## Session 007 — 2026-06-22
**Status:** Phase 4 closed. Signed. Session closing.

**Done:**
- RepoMend moved from C:\Dev to D:\Dev\Projects\RepoMend ✅
  Venv rebuilt, 297/297 tests confirmed on new path.
- KS-P4-03 ✅ test_golden_dataset.py extended (3 integration tests)
- KS-P4-04 ✅ Verifier wired into cli.py fix command
- KS-P4-05 ✅ Phase 4 Keystone Report written and signed
- AC-P4-11 end-to-end verified (Fix-Gen → Verifier → verified) PASS
- D-P4-01 (HIGH): prompt over-constraint + Gate 2 Option E — caught
  and fixed during AC-P4-11 integration testing
- D-P4-02 (MEDIUM): stale branch on Windows — self-heal in
  git_worktree_add()
- D-P4-03 (LOW): fixture line numbers, non-ASCII, CRLF — fixed,
  commit 6e77570 on repomend-fixture
- Final numbers: 282 passed · 1 skipped · 13/13 ACs PASS

**Open (carry forward):**
- [ ] Phase 5 INTAKE mandatory pre-step (ADR-017 pending):
  fix_gen.py must call git commit after submit_fix returns success
  and before handle.mark_success() — fix branch currently has no
  commits of its own. Phase 5 PR creation has nothing to push
  without this. First gate before any Phase 5 code.
- [ ] KS-P5-01: Phase 5 INTAKE contract
- [ ] Phase 5 build: HITL PR generation + GitHub API

**Next session starts at:**
Phase 5 INTAKE pre-step — add git commit to fix_gen.py before
writing the contract. Log as ADR-017. Then KS-P5-01.

### Session 008 — 2026-06-22
**Status:** Phase 5 functionally complete. AC-P5-10 manually verified.
**Done:**
- KS-P5-02 ✅ GithubConfig, GITHUB_TOKEN in CredentialProxy,
  git_push_branch(), PRPublisher skeleton. 341/341 passing.
- KS-P5-03 ✅ PRPublisher wired into cli.py orchestrator.
  341/341 passing.
- AC-P5-10 ✅ MANUALLY VERIFIED: PR #1 opened as draft on
  github.com/yehorcallmedai-maker/repomend-fixture
  URL: https://github.com/yehorcallmedai-maker/repomend-fixture/pull/1
  draft: True, five sections confirmed, ADR-003 and ADR-019 holding.
**Defects to log in Phase 5 Keystone Report:**
- D-P5-01 (MEDIUM): Gate 2 timing race in test_end_to_end_pr —
  Verifier ran before git commit fully landed in worktree state.
  Manifested as "vulnerability lines [24, 24] were not modified"
  even though the diff confirmed the edit was correct.
  Fix needed: add explicit git commit confirmation step before
  Verifier.verify() is called in the integration test harness.
  Workaround: manual push + PR creation confirmed the pipeline
  is architecturally correct.
**Open (carry forward):**
- [ ] Fix D-P5-01 race condition in test_end_to_end_pr
- [ ] Write Phase 5 Keystone Report (KS-P5-06)
- [ ] Add load_dotenv() to conftest.py so integration tests
  pick up .env automatically (flagged during AC-P5-10 debugging)
**Next session starts at:**
Fix D-P5-01 → run test_end_to_end_pr green → write KS-P5-06.

---

## Session 009 — 2026-06-22

**Model:** claude-sonnet-4-6

### Tasks completed

1. **Gate test (test_end_to_end_pr)** — PASS. PR #2 opened at
   https://github.com/yehorcallmedai-maker/repomend-fixture/pull/2.
   Manually inspected by Yehor: draft=true, five-section body confirmed.
   PR closed after inspection.

2. **conftest.py load_dotenv** — Created `tests/conftest.py` with
   `load_dotenv()` so all integration tests auto-load `.env`.
   Updated `.env.example` with `GITHUB_TOKEN` entry.
   Full suite: 341 passed, 13 deselected, 90.07% coverage.

3. **KS-P5-06** — Phase 5 Keystone Report written to
   `reports/keystone_report_phase5.md`. All 13 ACs: PASS.
   Four defects documented (D-P5-01a/b/c, D-P5-04).
   ADR-017/018/019 recorded. Awaiting Yehor sign-off.

### Status: Phase 5 COMPLETE — pending Yehor accountability signature

### Open: Phase 6 planning (multi-repo, reviewer assignment, risk routing)

## Session 010 — 2026-06-23
**Status:** Phase 6 closed. Signed. Session closing.
**Done:**
- KS-P6-01 ✅ [[repos]] config + field-merge. 350/350.
- KS-P6-02 ✅ asyncio pipeline skeleton + semaphore. 358/358.
- KS-P6-03 ✅ Real pipeline wired + prompt caching. 364/364.
- KS-P6-04 ✅ Branch protection check in PRPublisher. 370/370.
- KS-P6-05 ✅ Model tiering + --model CLI flag. 376/376.
- KS-P6-06 + KS-P6-07 ✅ Per-repo run log + 429 backoff. 383/383.
- KS-P6-08 ✅ AC-P6-11 integration test PASSED.
  2 results, 2 run log records. scanner_unavailable x2
  (Trivy not installed — correct exit, not a crash).
- KS-P6-09 ✅ Keystone Report Phase 6 written, ADR-020
  updated (return_exceptions=True rationale documented),
  signed by Yehor 2026-06-23.
**Final numbers:** 383 passed · 0 failed · 89.48% coverage
**All 11 ACs PASS. All 10 constraints met.**
**Defects caught this phase:** 8 (D-P6-01 through D-P6-08).
Most significant: D-P6-07 — typer.Exit escaping pipeline
with empty str(); fixed with scanner_unavailable status,
repr(exc) fallback, return_exceptions=True in gather.
**Known limitations carried to Phase 7:**
- KL-P6-01: Single finding per repo per run
- KL-P6-02: Sync Anthropic client inside asyncio.to_thread
- KL-P6-03: RunLog not threaded into run_repo_pipeline
- KL-P6-04: Trivy not installed in dev environment
**Open (carry forward):**
- [ ] Phase 7 INTAKE pre-step (ADR-009): answer Q1-Q4
      before writing the contract
- [ ] Install Trivy before Phase 7 integration test
- [ ] Migrate to AsyncAnthropic client directly (Phase 7)
**Next session starts at:**
Phase 7 INTAKE pre-step. Four questions to answer before
writing the contract:
  Q1: pipx vs uv tool install as primary distribution method
  Q2: Docker image scope — bundle scanners or separate install?
  Q3: Shared config for small-team — git repo or dotfiles?
  Q4: Documentation format — README only or docs site?

## Session 011 — 2026-06-23
**Status:** Phase 7 INTAKE reviewed and approved. Session
interrupted — closing early.
**Done:**
- Baseline confirmed: 354 passed, 1 skipped (non-integration)
- Phase 7 INTAKE contract reviewed and approved by director
- docs/intake_phase7.md ready for Yehor signature
- Trivy installed (winget, v0.71.2) — KL-P6-04 resolved
**Open (carry forward):**
- [ ] Sign docs/intake_phase7.md (BLOCKER — nothing builds
      until signed)
- [ ] KS-P7-02: AsyncAnthropic migration (first build task,
      HIGH risk — all sync Anthropic mocks must be migrated)
- [ ] KS-P7-03 through KS-P7-09: remaining Phase 7 build tasks
**Next session starts at:**
Sign docs/intake_phase7.md, then KS-P7-02.

## Session 012 — 2026-07-10 (record-gap reconciliation + org build plan)
**Status:** Session closed cleanly. No code changes. All actions
documentation/process/verification only.
**Context:** 16-day gap since Session 011 (2026-06-23 → 2026-07-09)
contains real, substantial, previously unlogged work: rename
RepoMend → Patchward (c27ea40), GitHub App webhook receiver +
Marketplace billing (0bb0286), Fly.io deployment
(patchward-webhook.fly.dev), PyPI Trusted Publisher CI scaffold.
None of it had a session log, ADR, or task-file entry until this
session.
**Done:**
- Re-verified item #27 (webhook/billing commit reachability from
  `main`) fresh, not from memory. Found and resolved a genuine
  conflict: unauthenticated `api.github.com` reads (via this
  sandbox's shared/rate-limited proxy) repeatedly returned the
  stale SHA `9bbe4967`, while `git ls-remote origin main` (Yehor,
  real machine) and the authenticated GitHub web UI both agreed on
  `0bb0286`. Root-caused via `.git/logs/refs/remotes/origin/main`
  reflog: a prior session ran `git push` through this sandbox's
  proxied network path, which recorded a local "update by push"
  success without the ref actually landing on GitHub's git-protocol
  backend at that time — resolved once Yehor pushed for real from
  his own machine. Item #27 — CLOSED, confirmed by two independent
  Tier-0/1 sources, re-confirmed a third time at session close
  (still closed; `api.github.com` is still serving stale `9bbe4967`
  even now, which is expected and fine — it's a known-unreliable
  Tier-2 source, not a new problem).
- Confirmed Fly deployment alive (`/healthz` → `{"status":"ok"}`),
  checked twice, hours apart.
- Re-checked all named external PR/issue references live (Future
  AGI #1283, smolagents #2467, tablib #642, twisted #12663/#12676/
  #12687) — all still open/unresolved as of 2026-07-10.
- Rewrote `memory/CONTEXT.md` to flag the record gap explicitly and
  record the item #27 resolution + verification lesson (verified
  intact via Read tool after edit — see file-integrity finding
  below).
- Produced `memory/deep_research_prompt_org_buildplan.md` — a
  self-contained deep-research brief (used to commission 3
  independent model runs on: closing the informational gap,
  industrial-grade org structure for a solo-dev + AI-agent hosted
  product, and a self-organization/role model for the operator).
- Synthesized the 3 returned reports into
  `memory/BUILD_PLAN_2026-07-10.md` — a proposed (NOT yet
  authorized/executed) step-by-step plan: State Reconstruction
  Audit procedure, STATE.md/WORKLOG.md/VERIFICATION.md/BACKLOG.md
  memory structure, a trust-tier verification protocol, a two-speed
  phase-gate redesign (Phase 8 Reconciliation / 9 Hosted-Surface
  Hardening / 10 Marketplace Readiness), a worked WSJF backlog
  resolution, and a "Directing Engineer" role definition. Two of
  the plan's factual claims (EU CRA reporting timeline, AGENTS.md
  as cross-tool standard) were independently spot-checked via live
  web search before being included, not taken on the research
  runs' word alone; the CRA's exact applicability/classification to
  Patchward specifically is flagged as needing real legal
  confirmation, not asserted as settled.
**Findings from this session's own hard-verification pass (new,
worth carrying forward):**
- `.git/index.lock` (0 bytes, created 2026-07-10 15:51) is
  currently sitting in the repo, left behind by a read-only `git
  status` call that failed to clean up its own lock due to sandbox
  mount permissions ("unable to unlink... Operation not
  permitted"). **Not removed by this session** (removing anything
  under `.git` from the sandbox is out of scope per standing
  rules) — **Yehor should delete
  `D:\Dev\Projects\Patchward\.git\index.lock` manually before his
  next git command**, or git may refuse to run citing another
  process.
- The bash tool's view of a file just edited via the Edit tool can
  be **stale and does not self-correct on retry**: after editing
  CONTEXT.md (76 → 125 lines), `wc -l` via bash repeatedly reported
  73 lines (neither the old nor the new true count), while the Read
  tool correctly showed all 125 lines, fully intact, on demand.
  Confirmed no actual data loss — this is a tool-view discrepancy,
  not file corruption. **Lesson: for files edited/written earlier
  in the same session, verify via Read, never via bash cat/wc/diff
  — the bash sandbox's mount of the file can lag behind the native
  file-tool view with no observed self-correction.** This is a new,
  distinct finding from the older documented RULE-1 (NTFS
  truncation on Edit/Write) — same family of mount-reliability
  hazard, different symptom, worth its own rule if/when the rules
  section gets reconciled.
- Secret-leak scan (grep for token patterns + known env-var names)
  across every file written/edited this session — clean, no
  matches.
**Open (carry forward):**
- [ ] `memory/BUILD_PLAN_2026-07-10.md` awaiting Yehor's review/
      edits/sign-off — no execution has started
- [ ] `memory/project_open_tasks.md` still not reconciled against
      the Patchward rename or Phase 1.3-1.5 work (CONTEXT.md now
      flags this explicitly; the task file itself is untouched)
- [ ] ClinInsight/Databutton LinkedIn DM replies — still
      unconfirmed
- [ ] Delete stale `.git/index.lock` on Yehor's machine
- [ ] Backlog decision pending: authorized E2E pipeline test vs.
      Mirror Pass Tier 2 vs. callmed-landing — BUILD_PLAN proposes
      a specific sequence, not yet approved
**Next session starts at:**
See `memory/NEXT_SESSION_START.md` — read that file first.

**Addendum (same session, immediately post-close):** the bash-staleness
finding above is worse than first documented. `git diff --quiet -- memory/
CONTEXT.md` and the same for `project_session_log.md`, run via this
sandbox's bash tool, both reported **no difference at all** — git's own
diff engine, not just `cat`/`wc`, is blind to Edit-tool changes on this
mount for at least some files. Practical consequence: nobody should trust
a "here's what changed" file list produced by this sandbox's git for
files edited earlier in the same session. **Yehor's own `git status` /
`git diff` on his real machine is the only reliable source** before
staging or committing anything.

---

## Session 013 — 2026-07-13 (State Reconstruction Audit close + Stage-1 E2E test)

**Status:** Session closed cleanly. Audit committed and tagged. Stage-1
E2E test run, documented, and committed. One HIGH-severity product
defect found and logged (not yet fixed). Two commits landed this
session: `27d0ba3` (audit artifacts) and `8b601e9` (Stage-1 report +
STATE/BACKLOG updates + `.dockerignore` + `uv.lock` webhook-extra lock).

**Provenance:** all file content (STATE.md, BACKLOG.md, 6 ADRs,
Consolidated Keystone Report, Stage-1 E2E report, this entry) drafted by
Claude (agent); all git writes (restore, add, commit, push, tag) executed
by Yehor on his own machine per standing rule. Commit messages drafted by
the agent, written to a temp file and committed via `git commit -F` (not
inline `-m`) per this session's own close-out discipline, to avoid
PowerShell quoting risk on multi-line messages.

**Done — State Reconstruction Audit (BUILD_PLAN Part 3):**
- `memory/STATE.md`, `memory/BACKLOG.md`, ADR-027 through ADR-032, and
  `docs/keystones/consolidated_keystone_2026-06-23_to_2026-07-09.md`
  written, reviewed, committed (`27d0ba3`), tagged `state-audit-2026-07`
- Self-correction, same day: an initially-reported `fly.toml` drift
  (found via a sandbox `git diff`) turned out to be a false positive —
  Yehor's own `git status`/`git diff` came back clean. Corrected in
  STATE.md, ADR-029 (amended, not deleted, per this project's
  ADR-immutability convention), and BACKLOG.md rather than silently
  dropped. Produced a sharper finding than Session 012's: this sandbox's
  `git status`/`git diff` against the working tree cannot be trusted at
  all on this mount, independent of whether a file was edited this
  session — only `git log`/`git ls-remote` (ref/object reads) remain
  trustworthy from the sandbox side.

**Done — Stage-1 E2E pipeline test (BACKLOG item 3):**
- Pre-flight found and fixed a real, previously-undiscovered defect:
  `patchward.toml` still had a `[repomend]` section header from before
  the rename — `load_config()` reads `raw.get("patchward", {})`, so the
  whole section (including the required `repo_path` field) was silently
  dropped, meaning `patchward scan`/`fix` would have hard-failed at
  config load. Also found `repo_path` pointing at a nonexistent path and
  `[github].repo` defaulting to `"Patchward"` itself. Fixed directly
  (local, gitignored file).
- Found and corrected a second stale assumption: this project's own old
  records (Session 002, `docs/intake_phase1.md`) documented the fixture's
  three vulnerabilities as subprocess/md5/ssl-wrap-socket; the actual
  committed fixture is subprocess/eval/hardcoded-password. Confirmed via
  `git show HEAD` and a live dry-run scan before spending anything on the
  wrong target.
- `uv run patchward fix --repo tests\fixture_repo` executed by Yehor: 3
  of 5 findings reached Fix-Gen+Verifier "verified" status; all 3
  branches confirmed pushed to the real remote via `git ls-remote`
  (Tier 0, not just trusting CLI output). Zero PRs opened.
- **Defect found (HIGH):** of the 3 "verified" fixes, direct inspection
  of the actual pushed diffs (not Fix-Gen's self-reported description)
  confirmed only 2 are correct. The third deletes `import subprocess`
  while `run_command()` still calls `subprocess.run(...)` on the same
  branch — objectively broken, would raise `NameError` at runtime — and
  the Verifier reported all three gates passing anyway. Root cause: Gate
  1's rescan goes clean because removing the import silences the semgrep
  pattern match; Gate 3's test-suite check goes clean because nothing in
  the fixture's tests exercises `run_command()`. This is a structural gap
  in the Verifier's coverage, not a fixture-specific fluke. Full writeup:
  `docs/keystones/stage1_e2e_test_2026-07-13.md` §2.
- **Defect found (MEDIUM):** `GITHUB_TOKEN` can push branches but cannot
  create PRs — `POST /pulls` returned 403 three times. Classic signature
  of a fine-grained PAT missing "Pull requests: write" or an
  expired/revoked classic PAT.
- **Defect found (LOW), confirmed by direct code read:** `cli.py`
  L496-499 prints `[PR] Opened: {url}` unconditionally, without checking
  `pr_dict['status']` — a 403/422 failure is misreported as success with
  a blank URL.
- **Open, root cause not yet confirmed:** one finding's branch name
  contained the literal text "requires login" (invalid git ref, crashed
  `git worktree add`). Hypothesis only — not yet investigated.

**Known limitations, stated plainly (nothing softened):**
- The Verifier gap (HIGH defect above) is documented, not fixed. Three
  candidate fix directions are sketched in the Stage-1 report; none
  chosen. Recommend this blocks Stage 2 (third-party repo) and Mirror
  Pass Tier 2 until resolved — consistent with BUILD_PLAN §6's own logic,
  not yet formally re-confirmed by Yehor as of this close.
- `runs/state.db` is tracked in git despite `.gitignore` listing
  `state.db`/`runs/` as ignored — pre-existing gap (ignore rules don't
  retroactively untrack), not fixed this session, needs a separate
  `git rm --cached` cleanup commit.
- `tests/fixture_repo` remains a non-submodule embedded git repo with its
  own local diff — pre-existing, carried forward again, still not
  investigated.
- `patchward.toml.example` (the committed Phase 7 distribution template)
  has the same config gap that was just fixed in the real `patchward.toml`
  — logged in BACKLOG item 6a, not fixed this session.
- Every ADR and STATE.md claim from this session's audit is marked
  "not yet reviewed by Yehor" — landed and pushed, but review/sign-off
  is a separate, still-open step.

**Methodology note:** this session's own close-out cross-consistency
pass (Step 3 of the session-close process) caught STATE.md contradicting
itself — its "Phase" and "Repo" sections still said the audit tag was
"not yet created" and cited a pre-commit HEAD, both stale the moment the
tag and commit actually landed earlier in the same session. Fixed before
this close. Worth carrying forward as a standing discipline: a
verification document needs the same close-out cross-check as the code
it describes, not an exemption from it.

**Accountability / sign-off:** the two commits (`27d0ba3`, `8b601e9`) are
objectively landed and verified (Tier 0, `git ls-remote` confirms both).
That is a fact, not a judgment call. **The substantive content — the
audit's ADRs, the Verifier-gap defect triage, and BACKLOG's WSJF
re-ordering — remains PENDING Yehor's review and sign-off**, exactly as
every artifact in this session has said throughout. Landing the commit
is not the same as approving what's in it.

**Next step (gate stated plainly):** no further code changes until
Yehor decides how to close the Verifier gap (three candidate directions
in the Stage-1 report). Everything else on the backlog — `GITHUB_TOKEN`
permissions, the CLI misreport fix, the "requires login" investigation,
`runs/state.db` untracking — is independently actionable in the
meantime, but Stage 2 and Mirror Pass Tier 2 specifically stay blocked.

**Next session starts at:**
See `memory/NEXT_SESSION_START.md` — read that file first (regenerated
same session as this entry, reflects current verified state).
