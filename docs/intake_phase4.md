# Phase 4 INTAKE Contract — KS-P4-01
**Date:** 2026-06-16
**Status:** SIGNED 2026-06-16

---

## ADR-009 Pre-Step — Verifier Mechanics Ground Truth

Per ADR-009, concrete verification mechanics are confirmed before this contract is written.
All three questions from KS-P4-00 are answered and locked by Yehor 2026-06-16.

### Q1 — What does "verified" mean?

Three sequential gates, evaluated and logged individually. All must be recorded in the
run log regardless of outcome.

| Gate | Name | Pass condition | Fail condition | Skip condition |
|------|------|----------------|----------------|----------------|
| 1 | Re-scan clean | Same `rule_id` no longer fires on patched file | Rule still fires | Never — mandatory |
| 2 | Diff in bounds | All edits fall within `[line_start, line_end]` of `file_path` | Any edit outside range | Never — mandatory |
| 3 | Test suite green | Test suite exists AND all tests pass | Test suite exists AND any test fails | No test suite detected (logged as SKIP, not FAIL) |

**"Verified"** = Gate 1 PASS + Gate 2 PASS + Gate 3 (PASS or SKIP).

Any single FAIL = `verification_status: failed`. Fix branch persists. All three gate
results logged individually in the run log entry for that fix attempt.

### Q2 — Fixture and golden dataset

Reuse `test_golden_dataset.py` harness from Phase 3 (AC-P3-09). Extend to add a second
pass: after Fix-Gen produces a fix branch, Verifier runs all three gates on that branch.
The integration test chain becomes:

```
finding → Fix-Gen → fix branch exists → Verifier → verification_status in run log
```

`repomend-fixture` now has `tests/test_clean.py` (commit `5b6ea7f`, 2026-06-16).
Gate 3 is exercisable as PASS on the clean fixture. The three planted findings
(subprocess-shell-true, insecure-hash-md5, ssl-wrap-socket) are unchanged from Phase 3.

`subprocess-shell-true` is the confirmed fixable finding (Phase 3 AC-P3-09, 1/3 PASS).
It is the primary integration target for the end-to-end Verifier chain.

### Q3 — False positive handling

False positive signal pattern: Gate 1 FAIL + Gate 2 PASS + Gate 3 (PASS or SKIP).
Interpretation: the fix was in-bounds and tests pass, but the scanner still fires —
the rule may be flagging semantically safe code (reachability-unaware rule).

Response:
- `verification_status: failed` (Gate 1 FAIL — no special case)
- `false_positive_candidate: true` added to run log entry when the above pattern matches
- Fix branch persists, labelled
- No automated resolution in Phase 4
- Surfaces in Phase 5 HITL PR as `risk_class: false_positive_candidate`
- Automated suppression is Phase 6 scope at earliest

### Namespace rule (from Phase 3 §7)

Base contract ACs: `AC-P4-XX`. Addendum ACs: `AC-P4A-XX`. No number reuse across base
and addenda within Phase 4.

---

## 1. Client Goal

Build the Verifier subagent: a deterministic (non-agentic) component that runs after
Fix-Gen produces a patch and evaluates it against three sequential gates. The Verifier
does not generate code. It runs tools, reads results, and writes a structured verdict
to the run log. "Verified" has a precise, testable definition locked in KS-P4-00.

Phase 4 gate: Verifier must correctly classify ≥1 finding from the golden dataset as
`verification_status: verified`, and correctly detect the false-positive-candidate
pattern on at least one adversarial case constructed for this purpose.

This phase also extends the eval curriculum: the golden dataset harness grows from a
repair-success check (Phase 3) to a full Fix-Gen → Verifier pipeline check. Coverage
of the verification path is required before Phase 5 (HITL PR generation) begins.

---

## 2. Constraints

| ID | Constraint |
|----|-----------|
| C-P4-01 | Verifier is a deterministic component, not an LLM agent. It executes three fixed gates in sequence using subprocess calls and file I/O. No model invocation inside Verifier. |
| C-P4-02 | Gate 1 (re-scan): Verifier calls the same scanner that produced the original finding, scoped to `file_path` only, using the same `rule_id`. No full-repo re-scan — per-file, per-rule invocation only. |
| C-P4-03 | Gate 2 (diff in bounds): Verifier computes the unified diff between the pre-edit file state and the patched file on the fix branch. Pre-edit state is retrieved via `git show HEAD:<file_path>` on the fix branch's parent commit (the clean worktree state at `fix_worktree_context` entry) — git-native, consistent with addendum C-P3-11 which retired `.orig` file-copy checkpointing. Every `+`/`-` line in the diff must fall within `[line_start, line_end]` from the SARIF finding. Any line outside that range is a FAIL. |
| C-P4-04 | Gate 3 (test suite): Verifier detects test suite presence by checking for `pytest` (`tests/` directory or `test_*.py` files in repo root) or `jest` (`package.json` with a `test` script). If detected, runs the suite. If not detected, logs `gate_3: skip`. |
| C-P4-05 | Run log schema extended (append-only, no mutation of prior records). New fields per fix attempt: `verifier: {gate_1, gate_2, gate_3, verification_status, false_positive_candidate}`. Gate values: `pass`, `fail`, or `skip`. `false_positive_candidate` is boolean. |
| C-P4-06 | Verifier is invoked by the Orchestrator after Fix-Gen returns. Verifier receives: fix branch name, `file_path`, `rule_id`, `line_start`, `line_end`. It does not receive the full finding dict or Fix-Gen's internal state. |
| C-P4-07 | Verifier result is written to the run log before the fix branch is returned to the caller. The branch is never surfaced to the caller without a `verification_status` entry. |
| C-P4-08 | Verifier has no write access to the fix branch. It reads the patched file and the checkpoint. It does not edit, commit, or modify any file in the worktree. |
| C-P4-09 | False positive candidate detection: if Gate 1 = FAIL and Gate 2 = PASS and Gate 3 = PASS or SKIP, set `false_positive_candidate: true` in the run log entry. All other Gate 1 FAIL cases: `false_positive_candidate: false`. |
| C-P4-10 | maxTurns does not apply to Verifier (it is not an agent loop). Verifier must complete within a wall-clock timeout: 120 seconds default, configurable via `repomend.toml` `[verifier] timeout_seconds`. Timeout = FAIL on the gate that was running when the timeout fired. |
| C-P4-11 | The eval curriculum in `test_golden_dataset.py` is extended to cover the full Fix-Gen → Verifier chain. The harness must assert `verification_status` in the run log after each end-to-end run, not just repair success rate. |

---

## 3. Acceptance Criteria

| ID | Criterion | How verified |
|----|-----------|-------------|
| AC-P4-01 | Verifier subagent built as deterministic component (no LLM call inside) | Unit: assert no `anthropic` client instantiation in `verifier.py`; no model param in any call |
| AC-P4-02 | Gate 1: re-scan of `subprocess-shell-true` finding on unpatched file returns FAIL (rule still fires) | Unit: run Verifier Gate 1 on original `vulnerable.py`; assert `gate_1: fail` |
| AC-P4-03 | Gate 1: re-scan of `subprocess-shell-true` finding on Fix-Gen-patched file returns PASS (rule no longer fires) | Integration: run full Fix-Gen → Verifier chain on `subprocess-shell-true`; assert `gate_1: pass` |
| AC-P4-04 | Gate 2: diff containing only in-bounds edits returns PASS | Unit: synthetic diff touching only lines within `[line_start, line_end]`; assert `gate_2: pass` |
| AC-P4-05 | Gate 2: diff containing any out-of-bounds edit returns FAIL — this is the named AC closing the Phase 3 §5 line-range validation gap | Unit: synthetic diff with one line outside `[line_start, line_end]`; assert `gate_2: fail` |
| AC-P4-06 | Gate 3: test suite detected (`tests/test_clean.py` present in `repomend-fixture`) and all tests pass; gate returns PASS | Integration: Verifier runs `pytest` on `repomend-fixture`; assert `gate_3: pass`; 3/3 tests pass |
| AC-P4-07 | Gate 3: no test suite present; gate returns SKIP (not FAIL); logged as `gate_3: skip` | Unit: Verifier against a tmpdir with no `tests/` and no `test_*.py`; assert `gate_3: skip` |
| AC-P4-08 | False positive candidate detection: Gate 1 FAIL + Gate 2 PASS + Gate 3 PASS → `false_positive_candidate: true` | Unit: mock Gate 1 = fail, Gate 2 = pass, Gate 3 = pass; assert `false_positive_candidate: true` |
| AC-P4-09 | False positive candidate NOT set when Gate 2 also fails: Gate 1 FAIL + Gate 2 FAIL → `false_positive_candidate: false` | Unit: mock Gate 1 = fail, Gate 2 = fail; assert `false_positive_candidate: false` |
| AC-P4-10 | Run log extended: after Fix-Gen → Verifier chain, run log entry contains `verifier.gate_1`, `verifier.gate_2`, `verifier.gate_3`, `verifier.verification_status`, `verifier.false_positive_candidate` | Integration: end-to-end run; assert all five fields present and correctly typed in NDJSON record |
| AC-P4-11 | Verifier has no write access: no file in the fix branch worktree is mutated by Verifier execution | Integration: hash all files in fix branch before and after Verifier run; assert byte-identical |
| AC-P4-12 | Eval harness (`test_golden_dataset.py`) extended: end-to-end run on `subprocess-shell-true` produces `verification_status: verified` in run log | Integration: full pipeline; assert `verification_status == "verified"` for subprocess-shell-true |
| AC-P4-13 | Verifier timeout fires correctly: mock a gate that stalls beyond `timeout_seconds`; assert gate marked FAIL with `reason: timeout` | Unit: mock subprocess call that sleeps 200s; set timeout to 1s; assert FAIL + reason |

---

## 4. Test Contract

### Inputs

| Input | Value |
|-------|-------|
| Fixture repo | `repomend-fixture` — `tests/test_clean.py` present (commit `5b6ea7f`), 3 planted findings |
| Primary integration target | `subprocess-shell-true` at line 24 of `vulnerable.py` (confirmed fixable, Phase 3 AC-P3-09) |
| Fix-Gen model | `claude-sonnet-4-6` (`warning`-level finding → Sonnet per C-P3-04) |
| Gate 2 pre-edit source | `git show HEAD:vulnerable.py` on fix branch parent commit |
| Gate 2 bounds | `line_start: 24`, `line_end: 24`, `file_path: vulnerable.py` |
| Gate 3 detection | `tests/test_clean.py` present — pytest suite, 3 tests |
| Timeout | 120s default |

### Expected outputs

```json
{
  "fix_gen": {
    "branch": "repomend/fix-subprocess-shell-true-<uuid4_short>",
    "checkpoint_written": true
  },
  "verifier": {
    "gate_1": "pass",
    "gate_2": "pass",
    "gate_3": "pass",
    "verification_status": "verified",
    "false_positive_candidate": false
  }
}
```

### Invariants

- Gate 2 always reads the pre-edit file state via `git show HEAD:<file_path>` on the
  fix branch's parent commit. If the git object is not found or the worktree is detached
  from the expected commit, Gate 2 = FAIL with `reason: git_object_not_found`.
- All three gates are always evaluated and logged, even if Gate 1 fails.
  Verifier does not short-circuit after the first failure — all gates run to completion
  so the false-positive-candidate pattern can be detected.
- Verifier never commits to the fix branch. Any write attempt from Verifier code is a
  defect, not a limitation.
- Run log record written by Verifier is append-only. If Verifier runs twice on the same
  fix branch, two separate records are written.

### Adversarial / break cases

**False positive candidate — synthetic case:**
Construct a patched file where the `subprocess-shell-true` rule still fires (e.g. the
fix is incomplete — `shell=True` replaced with `shell=1`). Diff is in-bounds. Tests pass.
Verifier must produce: `gate_1: fail`, `gate_2: pass`, `gate_3: pass`,
`verification_status: failed`, `false_positive_candidate: true`.

**Out-of-bounds edit:**
Construct a diff where Fix-Gen also edited a comment two lines above `line_start`.
Gate 2 must return FAIL even though the fix itself is correct. This tests that Gate 2
is a strict boundary check, not a heuristic.

**Git object not found:**
Detach the fix branch worktree from its parent commit before Verifier runs Gate 2
(simulate by checking out an orphan branch or corrupting the ref).
Verifier must: return `gate_2: fail`, `reason: git_object_not_found`, not raise an
uncaught exception, and still run Gate 3.

**Verifier timeout:**
Mock Gate 1 subprocess to stall for 200 seconds with `timeout_seconds: 1` in config.
Verifier must terminate the subprocess, mark `gate_1: fail`, `reason: timeout`,
continue to Gate 2 (which now has no patched file to diff — Gate 2 = FAIL,
`reason: gate_1_timeout`), and complete without hanging the process.

---

## 5. Risk Areas

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Gate 2 diff parsing brittle on context lines | Medium | Use `difflib.unified_diff` directly; assert only `+`/`-` line numbers, not context lines |
| Gate 1 scanner invocation differs from original scan (env, cwd, flags) | Medium | Verifier must invoke scanner with identical flags as Orchestrator; extract scanner call into shared helper |
| `pytest` not on PATH inside Verifier subprocess | Medium | Verifier uses `uv run pytest` consistent with project toolchain; fallback: `python -m pytest` |
| False positive candidate pattern generates noise on all FAIL cases | Low | Pattern requires Gate 2 PASS explicitly; standard bad-fix (out-of-bounds or broken tests) does not trigger it |
| subprocess-shell-true fix produces new vulnerability (unfixed string concat) | Medium | Known Phase 3 limitation; Gate 1 confirms the original rule no longer fires but does not guarantee no new findings — document explicitly in §6 Known Limitations |
| `git show` fails if fix branch is not yet committed | Low | Fix-Gen commits before returning the branch name; Verifier is invoked after commit — ordering enforced by Orchestrator |

---

## 6. Known Limitations

1. **Gate 1 scope is per-rule, per-file — not full-repo re-scan.** A fix that moves a
   vulnerability to a different file or introduces a new rule violation elsewhere will
   pass Gate 1. Full-repo re-scan is Phase 5+ scope.

2. **Gate 3 does not assert test coverage — only pass/fail.** A test suite that passes
   but does not exercise the patched code will still return Gate 3 PASS. Coverage-gated
   verification is Phase 6+ scope.

3. **False positive candidate detection is pattern-matching, not semantic analysis.**
   The pattern (Gate 1 FAIL + Gate 2 PASS + Gate 3 PASS-or-SKIP) is a signal, not a
   determination. A bad fix that happens to produce code the scanner doesn't flag (e.g.
   rule evasion) will look like a false positive candidate. Human review is required.

4. **`repomend-fixture/tests/test_clean.py` tests `clean.py`, not `vulnerable.py`.**
   Gate 3 PASS on the `subprocess-shell-true` fix branch means the test suite passes —
   it does not mean the patched code is tested. A second fixture with tests targeting
   the vulnerable patterns is Phase 5+ scope.

5. **No multi-file fix support.** Phase 4 Verifier assumes one fix, one file, per
   finding. The `pending_submit` heuristic in Fix-Gen (Phase 3) is also single-file.
   Multi-file fix verification requires architectural revision in Phase 5.

---

## 7. Architectural Decisions This Phase Introduces

**ADR-015 | 2026-06-16 | Verifier as deterministic subprocess wrapper, not LLM agent**
Decision: Verifier is not a Claude SDK agent. It is a plain Python class that calls
subprocess tools and applies deterministic rules. No model invocation.
Rationale: Verification correctness must be auditable without model variance. A
non-deterministic verifier introduces an untestable component into the trust chain.
LLM judgment is inappropriate for a gate that is supposed to catch LLM errors.
Status: Proposed — requires Yehor approval at sign.

**ADR-016 | 2026-06-16 | All three gates always run — no short-circuit on FAIL**
Decision: Verifier evaluates all three gates regardless of intermediate failures.
Rationale: Short-circuiting after Gate 1 FAIL would prevent false-positive-candidate
detection (which requires Gate 2 and Gate 3 results). The cost of running Gate 2 and
Gate 3 after a Gate 1 FAIL is negligible; the benefit (false positive signal) is
load-bearing for Phase 5 HITL.
Status: Proposed — requires Yehor approval at sign.

---

## 8. Accountability Statement

_I, Yehor, confirm this contract is complete, the acceptance criteria are testable,
and I authorize the Phase 4 build to begin once I sign below. ADR-015 and ADR-016
are approved as written. The Verifier is a deterministic component — this is a
locked architectural decision, not open for revision within Phase 4._

**Signed:** Yehor  **Date:** 2026-06-16

---

_This contract may not be modified after signing without a new INTAKE addendum
using the AC-P4A-XX namespace._
