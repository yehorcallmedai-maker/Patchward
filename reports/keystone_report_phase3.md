# Keystone Report — Phase 3: Fix-Gen Subagent
**Project:** RepoMend — Local-First Multi-Repo Security Agent  
**Phase:** 3 (Fix-Gen Subagent)  
**Session IDs:** KS-P3-02 · KS-P3-03 · KS-P3-04 · KS-P3-05 · KS-P3-06  
**Report date:** 2026-06-12  
**Model:** claude-sonnet-4-6 (orchestration / generation)  
**Status:** PHASE 3 GATE — OPEN

---

## 1. Provenance

| Artifact | AI-generated | Human-edited | Notes |
|----------|-------------|--------------|-------|
| `src/repomend/fix_gen.py` | Yes | No | All logic: model tiering, PR dict, deny hook wiring, pending_submit loop, config wiring |
| `src/repomend/fix_worktree.py` | Yes | No | `FixWorktreeHandle`, `fix_worktree_context`, git-native lifecycle |
| `src/repomend/run_log.py` | Yes | No | Append-only NDJSON RunLog |
| `src/repomend/config.py` (fix_gen section) | Yes | No | `FixGenConfig` nested model, `[fix_gen]` toml section wiring |
| `src/repomend/hooks.py` (existing) | AI (Phase 2) | No | Unchanged this phase; deny hook and `DENY_PAYLOADS` consumed |
| `tests/test_fix_gen.py` | Yes | No | All 14 new tests for AC-P3-07/08/10/12; fix to prior severity assertion |
| `tests/test_run_log.py` | Yes | No | 9 tests; byte-identity invariant test |
| `tests/test_config.py` (fix_gen section) | Yes | No | 3 tests for AC-P3-10 |
| `tests/test_golden_dataset.py` | Yes | No | AC-P3-09 integration gate; `_rescan_for_rule` helper |
| `docs/intake_phase3.md` | No | Yes — Yehor | Phase 3 base contract; signed by Yehor |
| `docs/intake_phase3_addendum_p3-03.md` | Yes (drafted) | Yes — Yehor signed | Addendum signed 2026-06-12 |
| `tests/fixture_repo/` | No | External | `github.com/yehorcallmedai-maker/repomend-fixture`; cloned, not modified |

All code AI-generated. No file was merged to main. Fixes land on `repomend/fix-<id>` branches only (C-P3-01 / Operational Invariant 1 — confirmed by `fix_worktree_context` design and golden dataset test run).

---

## 2. Acceptance Criteria Status

### Base contract (`docs/intake_phase3.md`) ACs

| AC | Description | Status | Evidence |
|----|-------------|--------|----------|
| AC-P3-01 | Fix-Gen subagent uses only Read, Edit, Write tools | PASS | `FIX_GEN_ALLOWED_TOOLS` structural test in `test_fix_gen.py` |
| AC-P3-02 | Worktree named `repomend/fix-<finding-id>`, persists on success | PASS | `fix_worktree_context` integration test; golden dataset confirms branch presence |
| AC-P3-03 | Fix-Gen receives only the finding dict (C-P3-01 trust boundary) | PASS | `apply_fix()` signature: only `finding: dict`, `repo_path: Path`, `finding_id`, `branch_name` |
| AC-P3-04 | Verifier subagent re-scans after fix | DEFERRED to Phase 4 | Re-scan in golden dataset uses direct subprocess call; Verifier subagent not yet implemented |
| **AC-P3-05** | `.orig` checkpoint file exists after Fix-Gen run | **SUPERSEDED** | Retired by addendum (C-P3-11). Git-native checkpoint replaces file-copy approach |
| **AC-P3-06** | Restore from checkpoint via `cp` | **SUPERSEDED** | Retired by addendum (C-P3-11). Rollback = worktree + branch deletion |
| AC-P3-07 | Severity-based model routing: "error" → Opus, "warning"/"note" → Sonnet | PASS | `test_model_for_severity_error`, `test_model_for_severity_warning`, `test_model_for_severity_note` in `test_fix_gen.py` |
| AC-P3-08 | `apply_fix()` returns PR dict `{branch_name, finding_id, file_path, diff_summary, risk_class, test_status}` | PASS | `test_apply_fix_returns_pr_dict`, `test_as_pr_dict_all_keys_present` in `test_fix_gen.py` |
| AC-P3-09 | Fix-Gen achieves ≥30% (≥1/3) repair success on golden fixture dataset | PASS | `test_golden_dataset_repair_rate`: 1/3 PASSED (subprocess-shell-true); gate threshold met |
| AC-P3-10 | `fix_gen_max_turns` in `RepomendConfig` via `[fix_gen]` toml section | PASS | `test_fix_gen_max_turns_from_toml`, `test_fix_gen_max_turns_default_when_section_absent`, `test_fix_gen_config_standalone_default` |
| AC-P3-11 | Append-only NDJSON run log at `runs/session_<timestamp>.json` | PASS | 9 tests in `test_run_log.py`; byte-identity invariant test |
| AC-P3-12 | `check_tool_call()` from `hooks.py` wired into `_execute_fix_tool`; 12/12 deny payloads blocked | PASS | `test_execute_fix_tool_blocks_deny_payload` — 12 parametrizations (PL-01–PL-12) all `result.startswith("DENIED")` and file unchanged |

### Addendum (`docs/intake_phase3_addendum_p3-03.md`) ACs

| AC | Description | Status | Evidence |
|----|-------------|--------|----------|
| AC-P3-03 (addendum) | One SARIF finding → one Fix-Gen invocation; branch persists after `mark_success()` | PASS | `test_fix_worktree_context_persists_on_mark_success`; golden dataset loop |
| AC-P3-04 (addendum) | Exception during patch → worktree and branch removed | PASS | `test_fix_worktree_context_cleans_up_on_exception` |
| AC-P3-05 (addendum) | Two findings → two distinct non-colliding branches, both coexist | PASS | `test_fix_worktree_context_two_distinct_branches` |
| AC-P3-06 (addendum) | Fix-Gen default model is `claude-sonnet-4-6` | PASS | `test_fix_gen_default_model` in `test_fix_gen.py` |
| AC-P3-07 (addendum) | Fix-Gen tool restrictions: Read, Edit, Write only — no Bash | PASS | `test_fix_gen_allowed_tools_no_bash` |
| AC-P3-08 (addendum) | Clean exit WITHOUT `mark_success()` → worktree and branch removed (fail-safe default) | PASS | `test_fix_worktree_context_cleans_up_without_mark_success` |

---

## 3. Verification Summary

### Unit test suite

```
273 passed, 8 deselected
Coverage: 95.54%
Command: uv run pytest -x -q --cov=src/repomend --cov-report=term-missing
```

Coverage reflects the Phase 3 additions. No untested branches that relate to shipped acceptance criteria. Deselected = 8 integration tests that require `ANTHROPIC_API_KEY + semgrep on PATH`.

### Integration (golden dataset gate — AC-P3-09)

```
Command: uv run pytest tests/test_golden_dataset.py -m integration -v -s --no-cov
Result:  1 passed (1/3 findings repaired — subprocess-shell-true)
Threshold: ≥1/3  →  GATE OPEN
Run time: ~74 seconds for subprocess-shell-true finding
```

Per-finding breakdown:

| Finding | Rule | Severity | Model | Result |
|---------|------|----------|-------|--------|
| subprocess-shell-true | `subprocess-shell-true` | error | claude-opus-4-8 | **PASS — re-scan clean** |
| insecure-hash-algorithm-md5 | `insecure-hash-algorithm-md5` | warning | claude-sonnet-4-6 | FAIL — rule still fires |
| ssl-wrap-socket-is-deprecated | `ssl-wrap-socket-is-deprecated` | warning | claude-sonnet-4-6 | FAIL — rule still fires |

Gate condition ≥1/3 = 33% is met. The two remaining failures are not regressions; they are known limitations of Phase 3 scope (no Verifier subagent, no retry logic).

### Security: deny hook parametrized test

```
12/12 DENY_PAYLOADS blocked (PL-01–PL-12)
File unchanged in all 12 cases (original content asserted post-call)
```

---

## 4. Defects Caught and Fixed

### D-P3-01 — NetworkPolicy enum aliasing (KS-P3-02, Phase 2 carryover)

**Severity:** MEDIUM  
**Root cause:** `NetworkPolicy.DENY` aliased to `NetworkPolicy.BLOCK` in `hooks.py` due to identical integer values in the enum definition. `NetworkPolicy.DENY is NetworkPolicy.BLOCK` evaluated True; callers expecting `DENY` received `BLOCK` behavior (functionally equivalent but semantically incorrect — risk of future divergence).  
**Fix applied:** Added `_ignore_ = "BLOCK"` to the enum class to prevent aliasing. `NetworkPolicy.DENY is NetworkPolicy.BLOCK` now evaluates False.  
**Verified by:** `test_network_policy_deny_and_block_are_distinct` (new test added in KS-P3-02).

### D-P3-02 — Semgrep `--metrics` flag causing hang (KS-P3-02)

**Severity:** LOW  
**Root cause:** `semgrep` CLI version on test machine required `--metrics off` (not `--metrics=off`). Space-separated form caused semgrep to hang waiting for stdin.  
**Fix applied:** Changed all semgrep subprocess invocations from `--metrics=off` to `--metrics`, `off` (separate list entries).  
**Verified by:** Scanner integration tests no longer hang; re-scan in golden dataset completes within 120s timeout.

### D-P3-03 — Fix-Gen never calls submit_fix (KS-P3-04 / KS-P3-05)

**Severity:** HIGH  
**Symptom:** Golden dataset 0/3. All 3 findings ran 10 turns each (~31s/finding) without calling `submit_fix`. Loop exited on `max_turns` exhausted, `success=False`.  
**Root cause:** `tool_choice={"type": "any"}` allows the model to continue calling `read_file` and `edit_file` indefinitely without transitioning to `submit_fix`. The model never received a signal that it should close the fix.  
**Fix applied:**

```python
# In apply_fix() loop — fix_gen.py
pending_submit = False
for _ in range(max_turns):
    tool_choice = (
        {"type": "tool", "name": "submit_fix"}
        if pending_submit
        else {"type": "any"}
    )
    ...
    # After successful edit_file / write_file:
    if block.name in ("edit_file", "write_file") and result_text.startswith("OK"):
        pending_submit = True
```

After any successful file write, the next API call forces `submit_fix`. The model cannot loop further once it has made a change.  
**Verified by:** Golden dataset re-run: 1/3 PASSED. subprocess-shell-true finding fixed and re-scan clean in ~74 seconds.

### D-P3-04 — cp1251 UnicodeDecodeError in semgrep stderr reader (KS-P3-05)

**Severity:** LOW  
**Symptom:** Two `UnicodeDecodeError: 'cp1251' codec can't decode byte` warnings during golden dataset integration run. semgrep stderr contains UTF-8 characters outside the cp1251 Windows codepage.  
**Root cause:** `subprocess.run(..., text=True)` without explicit `encoding=` uses the OS locale default (cp1251 on this Windows machine). Same root cause as the cp1251 fix applied to the scanner in Phase 1.  
**Fix applied:** Added `encoding="utf-8", errors="replace"` to `_rescan_for_rule` subprocess call in `test_golden_dataset.py`.  
**Verified by:** Golden dataset re-run produced no encoding warnings. `errors="replace"` ensures scan output is parseable even if semgrep emits non-UTF-8 bytes.

---

## 5. Known Limitations

**No Verifier subagent yet.** The re-scan in AC-P3-09 (golden dataset) is a direct subprocess call in the test harness — not a Verifier subagent routing call. Re-scan is necessary but not sufficient: the test suite for the patched file is not re-run. A fix that silences the semgrep rule by commenting it out would pass re-scan. Phase 4 closes this via the Verifier subagent + test-suite re-run gate.

**Golden dataset 1/3 pass rate (33%).** The two failing findings (MD5, ssl.wrap_socket) are not fixed by the current Fix-Gen prompt. They received `success=True` from `submit_fix` calls but the rule still fired on re-scan. This is consistent with the AC-P3-09 gate minimum (≥30%) and is not a regression. The failure modes are: MD5 → model replaced `md5` with `sha256` but semgrep still matched on an alias; ssl.wrap_socket → model added `SSLContext` but retained the `wrap_socket` call path. Improving repair rate beyond 30% is a Phase 4 / eval curriculum target.

**No retry logic on Fix-Gen failure.** If `apply_fix()` returns `success=False`, the worktree is discarded and no second attempt is made. The Orchestrator currently has no retry-with-different-prompt path. Retry escalation is scoped to Phase 4.

**`pending_submit` flag fires on any `edit_file` / `write_file` success.** The current heuristic forces `submit_fix` after the first successful file write. If a finding requires edits to multiple files, the first edit terminates the loop before subsequent files are patched. This is intentional for Phase 3 (single-file scope per C-P3-09), but will need revision in Phase 4 when multi-file fixes are introduced.

**AC-P3-05/06 (`.orig` file checkpointing) retired.** The base contract specified file-copy checkpointing. The addendum superseded this with git-native rollback. Teams reading only `docs/intake_phase3.md` without the addendum will see incorrect ACs. See methodology note.

**No diff validation against `[line_start, line_end]`.** The adversarial scope-containment check (addendum §3) — asserting that the patch touches only the specified line range — is documented as a pass condition but is not currently asserted in a test. The denial hook blocks prompt injection at the tool-call level (PL-01–PL-12 all blocked), but line-range validation of the resulting diff is not yet automated.

---

## 6. Accountability Statement

_I, Yehor, have reviewed this Keystone Report. The Phase 3 acceptance criteria as verified above accurately represent the build completed in KS-P3-02 through KS-P3-06. The defects caught (D-P3-01 through D-P3-04) are documented with their exact fixes. The known limitations are stated without softening. The golden dataset gate (≥1/3 findings repaired, re-scan clean) is confirmed OPEN. The Phase 3 gate is open and Phase 4 (Verifier subagent + eval curriculum) may proceed._

**Signed:** Yehor  **Date:** 2026-06-16

---

## 7. Methodology Note — Suggested Improvement

**AC numbering collision between base contract and addendum must be caught at intake.**

Both `docs/intake_phase3.md` and `docs/intake_phase3_addendum_p3-03.md` use AC-P3-05, AC-P3-06, AC-P3-07, and AC-P3-08 for different items. The addendum correctly notes which base ACs are superseded, but the collision is not visible until both documents are read side-by-side. In this phase, the AI co-pilot identified the collision during test writing and flagged it — but a reader auditing only the base contract would see incorrect pass/fail status.

**Suggested fix for Phase 4:** Addendum ACs should use a distinct namespace — for example `AC-P3A-01` through `AC-P3A-06` (where `A` = addendum) — so there is no ambiguity between base and addendum acceptance criteria. The base contract ACs it retires should be explicitly struck through in `docs/intake_phase3.md` with a forward reference to the addendum AC that replaces them. This eliminates the need for verbal disambiguation in Keystone Reports and makes the audit trail machine-readable.

---

## Appendix — File Inventory

| File | Change | AC covered |
|------|--------|------------|
| `src/repomend/fix_gen.py` | Major rewrite (model tiering, PR dict, hooks, config, submit_fix loop) | AC-P3-07, AC-P3-08, AC-P3-10, AC-P3-12 |
| `src/repomend/fix_worktree.py` | New | AC-P3-03/04/05/06/07/08 (addendum) |
| `src/repomend/run_log.py` | New | AC-P3-11 |
| `src/repomend/config.py` | `FixGenConfig` added | AC-P3-10 |
| `tests/test_fix_gen.py` | 14 new tests | AC-P3-07, AC-P3-08, AC-P3-10, AC-P3-12 |
| `tests/test_fix_worktree.py` | New | AC-P3-03/04/05/06/07/08 (addendum) |
| `tests/test_run_log.py` | New (9 tests) | AC-P3-11 |
| `tests/test_config.py` | 3 new tests | AC-P3-10 |
| `tests/test_golden_dataset.py` | New (@integration) | AC-P3-09 |
| `tests/fixture_repo/` | Cloned (unmodified) | AC-P3-09 |
| `docs/intake_phase3_addendum_p3-03.md` | New | Addendum ACs above |
| `reports/keystone_report_phase3.md` | This document | — |
