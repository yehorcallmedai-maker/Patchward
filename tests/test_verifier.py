# KS-TRACE: AC-P4-01 through AC-P4-13
# | assumption: Verifier is deterministic — no LLM mocking required;
# |             git / subprocess calls mocked via monkeypatch / tmp_path;
# |             all gate logic is pure-Python testable in isolation
# | test: this file
"""
Tests for patchward.verifier (Phase 4 — KS-P4-02).

Test organisation:
  Structural (AC-P4-01)         — 2 tests
  Gate 1 unit (AC-P4-02/03)     — 4 tests
  Gate 2 unit (AC-P4-04/05)     — 8 tests
  _removed_import_still_referenced unit (BACKLOG 3a) — 8 tests
  Gate 3 unit (AC-P4-06/07)     — 5 tests
  False positive (AC-P4-08/09)  — 3 tests
  Run log dict (AC-P4-10)       — 2 tests
  No write access (AC-P4-11)    — 1 test
  Timeout (AC-P4-13)            — 2 tests
  ADR-016 no short-circuit      — 1 test
"""
from __future__ import annotations

import json
import subprocess
import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from patchward.verifier import (
    FAIL,
    PASS,
    SKIP,
    GateResult,
    Verifier,
    VerifierResult,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_semgrep_json(rule_id: str, path: str, line: int) -> str:
    """Build minimal semgrep JSON output with one finding."""
    return json.dumps({
        "results": [{
            "check_id": rule_id,
            "path": path,
            "start": {"line": line, "col": 1},
            "end": {"line": line, "col": 1},
            "extra": {"message": "test finding"},
        }],
        "errors": [],
    })


def _empty_semgrep_json() -> str:
    return json.dumps({"results": [], "errors": []})


def _write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# AC-P4-01 — Structural: no Anthropic client instantiated in verifier.py
# ---------------------------------------------------------------------------

class TestStructural:
    def test_no_anthropic_import_in_verifier(self):
        """AC-P4-01: verifier.py must not import anthropic."""
        import ast
        import importlib.util

        spec = importlib.util.find_spec("patchward.verifier")
        source = Path(spec.origin).read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports = [
            node.names[0].name if isinstance(node, ast.Import) else node.module
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
        ]
        assert "anthropic" not in imports, (
            "verifier.py must not import anthropic — Verifier is deterministic (ADR-015)"
        )

    def test_verifier_result_always_has_all_three_gates(self):
        """AC-P4-01: VerifierResult default state populates all three gates."""
        vr = VerifierResult()
        assert vr.gate_1 is not None
        assert vr.gate_2 is not None
        assert vr.gate_3 is not None


# ---------------------------------------------------------------------------
# Gate 1 — Re-scan (AC-P4-02, AC-P4-03)
# ---------------------------------------------------------------------------

class TestGate1Rescan:
    RULE = "python.lang.security.audit.subprocess-shell-true.subprocess-shell-true"

    def test_gate1_fail_when_rule_still_fires(self, tmp_path):
        """AC-P4-02: Gate 1 FAIL when semgrep reports a finding for rule_id."""
        target = tmp_path / "vulnerable.py"
        _write_file(target, "import subprocess\nsubprocess.run('ls', shell=True)\n")

        semgrep_output = _make_semgrep_json(self.RULE, str(target), 2)
        mock_proc = MagicMock(returncode=0, stdout=semgrep_output, stderr="")

        with patch("subprocess.run", return_value=mock_proc):
            v = Verifier()
            result = v._gate_1_rescan(
                worktree_path=tmp_path,
                file_path="vulnerable.py",
                rule_id=self.RULE,
            )

        assert result.status == FAIL
        assert "still fires" in result.reason

    def test_gate1_pass_when_no_findings(self, tmp_path):
        """AC-P4-03: Gate 1 PASS when semgrep returns no findings for rule_id."""
        target = tmp_path / "fixed.py"
        _write_file(target, "import subprocess\nsubprocess.run(['ls'])\n")

        mock_proc = MagicMock(returncode=0, stdout=_empty_semgrep_json(), stderr="")

        with patch("subprocess.run", return_value=mock_proc):
            v = Verifier()
            result = v._gate_1_rescan(
                worktree_path=tmp_path,
                file_path="fixed.py",
                rule_id=self.RULE,
            )

        assert result.status == PASS

    def test_gate1_fail_on_unknown_rule_prefix(self, tmp_path):
        """Gate 1 FAIL when no scanner handler registered for rule_id."""
        v = Verifier()
        result = v._gate_1_rescan(
            worktree_path=tmp_path,
            file_path="file.py",
            rule_id="unknowntool.some.rule",
        )
        # unknowntool is not in the dispatch table — but semgrep is tried for all rules
        # This test verifies the FAIL path when scanner_cmd returns None
        # (currently all rules fall through to semgrep, so patch scanner_cmd_for_rule)
        with patch.object(Verifier, "_scanner_cmd_for_rule", return_value=None):
            result = v._gate_1_rescan(
                worktree_path=tmp_path,
                file_path="file.py",
                rule_id="unknowntool.some.rule",
            )
        assert result.status == FAIL
        assert "no scanner handler" in result.reason

    def test_gate1_fail_on_timeout(self, tmp_path):
        """AC-P4-13: Gate 1 FAIL with reason 'timeout' when subprocess times out."""
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("semgrep", 1)):
            v = Verifier(timeout_seconds=1)
            result = v._gate_1_rescan(
                worktree_path=tmp_path,
                file_path="vulnerable.py",
                rule_id=self.RULE,
            )
        assert result.status == FAIL
        assert result.reason == "timeout"


# ---------------------------------------------------------------------------
# Gate 2 — Diff in bounds (AC-P4-04, AC-P4-05)
# ---------------------------------------------------------------------------

class TestGate2DiffInBounds:
    def _make_worktree(self, tmp_path: Path, pre_content: str, post_content: str) -> Path:
        """Set up a minimal worktree with pre-edit state in git HEAD and post-edit on disk."""
        wt = tmp_path / "worktree"
        wt.mkdir()
        (wt / "file.py").write_text(post_content, encoding="utf-8")
        return wt

    def _mock_git_show(self, pre_content: str):
        """Return a mock for subprocess.run that returns pre_content for git show."""
        return MagicMock(returncode=0, stdout=pre_content, stderr="")

    def test_gate2_pass_when_edits_in_bounds(self, tmp_path):
        """AC-P4-04: Gate 2 PASS when all edits fall within [line_start, line_end]."""
        pre = "line1\nshell=True\nline3\n"
        post = "line1\nsubprocess.run(['ls'])\nline3\n"
        wt = self._make_worktree(tmp_path, pre, post)

        with patch("subprocess.run", return_value=self._mock_git_show(pre)):
            v = Verifier()
            result = v._gate_2_diff_in_bounds(
                worktree_path=wt,
                file_path="file.py",
                line_start=2,
                line_end=2,
            )
        assert result.status == PASS

    def test_gate2_fail_when_edit_out_of_bounds(self, tmp_path):
        """AC-P4-05: Gate 2 FAIL when any edit falls outside [line_start, line_end]."""
        pre = "line1\nshell=True\nline3\n"
        post = "line1_modified\nsubprocess.run(['ls'])\nline3\n"  # line 1 also changed
        wt = self._make_worktree(tmp_path, pre, post)

        with patch("subprocess.run", return_value=self._mock_git_show(pre)):
            v = Verifier()
            result = v._gate_2_diff_in_bounds(
                worktree_path=wt,
                file_path="file.py",
                line_start=2,
                line_end=2,
            )
        assert result.status == FAIL
        assert "outside" in result.reason or "1" in result.reason

    def test_gate2_fail_git_object_not_found(self, tmp_path):
        """Adversarial: git show fails (worktree detached) → Gate 2 FAIL git_object_not_found."""
        wt = tmp_path / "worktree"
        wt.mkdir()
        (wt / "file.py").write_text("content\n", encoding="utf-8")
        mock_fail = MagicMock(returncode=1, stdout="", stderr="fatal: path not found")

        with patch("subprocess.run", return_value=mock_fail):
            v = Verifier()
            result = v._gate_2_diff_in_bounds(
                worktree_path=wt,
                file_path="file.py",
                line_start=1,
                line_end=1,
            )
        assert result.status == FAIL
        assert result.reason == "git_object_not_found"

    def test_gate2_fail_gate1_timeout_propagates(self, tmp_path):
        """Adversarial: gate_1_timeout flag → Gate 2 reason is gate_1_timeout."""
        wt = tmp_path / "worktree"
        wt.mkdir()
        (wt / "file.py").write_text("content\n", encoding="utf-8")
        mock_fail = MagicMock(returncode=1, stdout="", stderr="")

        with patch("subprocess.run", return_value=mock_fail):
            v = Verifier()
            result = v._gate_2_diff_in_bounds(
                worktree_path=wt,
                file_path="file.py",
                line_start=1,
                line_end=1,
                gate_1_timed_out=True,
            )
        assert result.status == FAIL
        assert result.reason == "gate_1_timeout"

    def test_gate2_fail_on_timeout(self, tmp_path):
        """AC-P4-13: Gate 2 FAIL with reason 'timeout'."""
        wt = tmp_path / "worktree"
        wt.mkdir()
        (wt / "file.py").write_text("content\n", encoding="utf-8")

        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("git", 1)):
            v = Verifier(timeout_seconds=1)
            result = v._gate_2_diff_in_bounds(
                worktree_path=wt,
                file_path="file.py",
                line_start=1,
                line_end=1,
            )
        assert result.status == FAIL
        assert result.reason == "timeout"

    def test_out_of_bounds_lines_pure(self):
        """Unit: _out_of_bounds_lines returns (touched_vuln, oob_set) — D-P4-01."""
        diff = [
            "--- a/file.py",
            "+++ b/file.py",
            "@@ -1,3 +1,3 @@",
            " line1",
            "-shell=True",
            "+subprocess.run(['ls'])",
            " line3",
        ]
        # In bounds [2, 2]: touched_vuln=True, oob=empty
        touched, oob = Verifier._out_of_bounds_lines(diff, line_start=2, line_end=2)
        assert touched is True, "Expected touched_vuln=True"
        assert oob == set(), f"Expected empty oob set, got {oob}"

        # Out of bounds — line 1 is outside [2, 2] and not in import block
        diff_oob = [
            "--- a/file.py",
            "+++ b/file.py",
            "@@ -1,3 +1,3 @@",
            "-line1",
            "+line1_modified",
            " shell=True",
            " line3",
        ]
        touched_oob, oob_set = Verifier._out_of_bounds_lines(diff_oob, line_start=2, line_end=2)
        assert touched_oob is False, "Line 2 not touched"
        assert 1 in oob_set

    def test_gate2_import_addition_passes(self, tmp_path):
        "D-P4-01 Option E: import added in separate hunk + vuln fixed -> Gate 2 PASS."
        # Vuln at pre-edit line 8; import at line 2 is in a separate hunk (>3 lines away)
        pre = "import os\n\n\n\n\n\n\nshell=True\n"  # line 8 = vuln
        post = "import os\nimport shlex\n\n\n\n\n\n\nsubprocess.run(['ls'])\n"
        wt = self._make_worktree(tmp_path, pre, post)

        with patch("subprocess.run", return_value=self._mock_git_show(pre)):
            v = Verifier()
            result = v._gate_2_diff_in_bounds(
                worktree_path=wt,
                file_path="file.py",
                line_start=8,
                line_end=8,
            )
        assert result.status == PASS, f"Expected PASS, got {result.status}: {result.reason}"

    def test_gate2_no_vuln_touch_fails(self, tmp_path):
        "D-P4-01 Option E: vuln line untouched -> Gate 2 FAIL."
        # Pre-edit line 8 is the vuln. Only line 1 is changed (non-import).
        # Gate 2: no '-' at pre-edit line 8 -> touched_vuln=False -> FAIL
        pre = "# header\n\n\n\n\n\n\nshell=True\n"
        post = "# MODIFIED header\n\n\n\n\n\n\nshell=True\n"
        wt = self._make_worktree(tmp_path, pre, post)

        with patch("subprocess.run", return_value=self._mock_git_show(pre)):
            v = Verifier()
            result = v._gate_2_diff_in_bounds(
                worktree_path=wt,
                file_path="file.py",
                line_start=8,
                line_end=8,
            )
        assert result.status == FAIL

    def test_gate2_fail_when_removed_import_still_referenced(self, tmp_path):
        """
        BACKLOG 3a regression — reproduces the 2026-07-13 Stage-1 defect:
        Fix-Gen deleted `import subprocess` (the flagged bandit B404 line)
        while `subprocess.run(...)` remained live elsewhere in the same
        file. Gate 2 previously PASSED this outright because the deleted
        line fell inside the nominal vuln range ([1, 1]) and any import-
        statement removal was unconditionally exempted. Must now FAIL.
        """
        pre = "import subprocess\n\n\n\nsubprocess.run(cmd, shell=True)\n"
        post = "import shlex\n\n\n\nsubprocess.run(cmd, shell=True)\n"
        wt = self._make_worktree(tmp_path, pre, post)

        with patch("subprocess.run", return_value=self._mock_git_show(pre)):
            v = Verifier()
            result = v._gate_2_diff_in_bounds(
                worktree_path=wt,
                file_path="file.py",
                line_start=1,
                line_end=1,
            )
        assert result.status == FAIL, (
            "Gate 2 must reject an import removal whose bound name is "
            "still referenced elsewhere in the post-edit file, even when "
            "the removal happens on the flagged vulnerability line itself "
            f"(got {result.status}: {result.reason})"
        )

    def test_gate2_pass_when_removed_import_genuinely_unused(self, tmp_path):
        """
        Contrast case for the BACKLOG 3a fix: removing an import that has
        zero remaining references anywhere in the post-edit file is a
        legitimate fix (the true-positive B404 case) and must still PASS —
        the new check must not reject every import removal, only unsafe ones.
        """
        pre = "import subprocess\nx = 1\n"
        post = "x = 1\n"
        wt = self._make_worktree(tmp_path, pre, post)

        with patch("subprocess.run", return_value=self._mock_git_show(pre)):
            v = Verifier()
            result = v._gate_2_diff_in_bounds(
                worktree_path=wt,
                file_path="file.py",
                line_start=1,
                line_end=1,
            )
        assert result.status == PASS, (
            f"Genuinely-unused import removal should still PASS, got "
            f"{result.status}: {result.reason}"
        )


# ---------------------------------------------------------------------------
# _removed_import_still_referenced — BACKLOG 3a unit tests
# ---------------------------------------------------------------------------

class TestRemovedImportStillReferenced:
    """
    Direct unit tests for the AST-based helper added to close BACKLOG 3a.
    Covers the conservative fallback paths as well as the common cases,
    since a false "not referenced" verdict here is exactly the failure
    mode this fix exists to prevent.
    """

    def test_returns_false_when_name_unused(self):
        assert Verifier._removed_import_still_referenced(
            "import subprocess", "x = 1\n"
        ) is False

    def test_returns_true_when_name_still_used(self):
        assert Verifier._removed_import_still_referenced(
            "import subprocess", "subprocess.run(['ls'])\n"
        ) is True

    def test_respects_alias_bound_name_not_original(self):
        """`import subprocess as sp` binds `sp`, not `subprocess`."""
        assert Verifier._removed_import_still_referenced(
            "import subprocess as sp", "sp.run(['ls'])\n"
        ) is True
        assert Verifier._removed_import_still_referenced(
            "import subprocess as sp", "subprocess.run(['ls'])\n"
        ) is False

    def test_from_import_multiple_names(self):
        assert Verifier._removed_import_still_referenced(
            "from os import path, sep", "print(path.join('a'))\n"
        ) is True
        assert Verifier._removed_import_still_referenced(
            "from os import path, sep", "x = 1\n"
        ) is False

    def test_star_import_is_conservative(self):
        """Bound names can't be enumerated -> assume still referenced."""
        assert Verifier._removed_import_still_referenced(
            "from os import *", "x = 1\n"
        ) is True

    def test_unparseable_import_line_is_conservative(self):
        assert Verifier._removed_import_still_referenced(
            "not a valid import (((", "x = 1\n"
        ) is True

    def test_unparseable_post_file_is_conservative(self):
        assert Verifier._removed_import_still_referenced(
            "import subprocess", "def broken(:\n"
        ) is True

    def test_non_import_statement_is_conservative(self):
        """Defensive: if the "import line" isn't actually one, don't guess."""
        assert Verifier._removed_import_still_referenced(
            "x = 1", "x = 1\n"
        ) is True


# ---------------------------------------------------------------------------
# Gate 3 — Test suite (AC-P4-06, AC-P4-07)
# ---------------------------------------------------------------------------

class TestGate3TestSuite:
    def test_gate3_skip_when_no_tests(self, tmp_path):
        """AC-P4-07: Gate 3 SKIP when no test suite detected."""
        wt = tmp_path / "worktree"
        wt.mkdir()
        (wt / "main.py").write_text("x = 1\n", encoding="utf-8")

        v = Verifier()
        result = v._gate_3_test_suite(worktree_path=wt)

        assert result.status == SKIP
        assert "no test suite" in result.reason

    def test_gate3_detects_tests_directory(self, tmp_path):
        """AC-P4-06: tests/ directory with test_*.py detected as pytest."""
        wt = tmp_path / "worktree"
        (wt / "tests").mkdir(parents=True)
        (wt / "tests" / "test_clean.py").write_text("def test_x(): pass\n", encoding="utf-8")

        runner = Verifier._detect_test_runner(wt)
        assert runner == "pytest"

    def test_gate3_detects_root_level_test_file(self, tmp_path):
        """Gate 3 detects test_*.py at repo root as pytest."""
        wt = tmp_path / "worktree"
        wt.mkdir()
        (wt / "test_main.py").write_text("def test_x(): pass\n", encoding="utf-8")

        runner = Verifier._detect_test_runner(wt)
        assert runner == "pytest"

    def test_gate3_pass_when_pytest_succeeds(self, tmp_path):
        """AC-P4-06: Gate 3 PASS when pytest exits 0."""
        wt = tmp_path / "worktree"
        wt.mkdir()
        mock_proc = MagicMock(returncode=0, stdout="3 passed", stderr="")

        with patch("subprocess.run", return_value=mock_proc):
            v = Verifier()
            result = v._run_pytest(wt)

        assert result.status == PASS

    def test_gate3_fail_when_pytest_fails(self, tmp_path):
        """Gate 3 FAIL when pytest exits non-zero."""
        wt = tmp_path / "worktree"
        wt.mkdir()
        mock_proc = MagicMock(returncode=1, stdout="FAILED tests/test_x.py", stderr="")

        with patch("subprocess.run", return_value=mock_proc):
            v = Verifier()
            result = v._run_pytest(wt)

        assert result.status == FAIL
        assert "pytest exit 1" in result.reason


# ---------------------------------------------------------------------------
# False positive candidate detection (AC-P4-08, AC-P4-09)
# ---------------------------------------------------------------------------

class TestFalsePositiveDetection:
    def test_false_positive_candidate_true_pattern(self):
        """AC-P4-08: Gate1 FAIL + Gate2 PASS + Gate3 PASS → false_positive_candidate True."""
        vr = VerifierResult(
            gate_1=GateResult(FAIL, "rule still fires"),
            gate_2=GateResult(PASS),
            gate_3=GateResult(PASS),
        )
        assert vr.false_positive_candidate is True
        assert vr.verification_status == "failed"

    def test_false_positive_candidate_true_gate3_skip(self):
        """AC-P4-08: Gate1 FAIL + Gate2 PASS + Gate3 SKIP → false_positive_candidate True."""
        vr = VerifierResult(
            gate_1=GateResult(FAIL, "rule still fires"),
            gate_2=GateResult(PASS),
            gate_3=GateResult(SKIP, "no test suite detected"),
        )
        assert vr.false_positive_candidate is True

    def test_false_positive_candidate_false_when_gate2_fails(self):
        """AC-P4-09: Gate1 FAIL + Gate2 FAIL → false_positive_candidate False."""
        vr = VerifierResult(
            gate_1=GateResult(FAIL, "rule still fires"),
            gate_2=GateResult(FAIL, "edits outside [24, 24]"),
            gate_3=GateResult(PASS),
        )
        assert vr.false_positive_candidate is False
        assert vr.verification_status == "failed"


# ---------------------------------------------------------------------------
# Run log dict (AC-P4-10)
# ---------------------------------------------------------------------------

class TestRunLogDict:
    def test_as_log_dict_contains_all_required_fields(self):
        """AC-P4-10: as_log_dict() returns all five required verifier fields."""
        vr = VerifierResult(
            gate_1=GateResult(PASS),
            gate_2=GateResult(PASS),
            gate_3=GateResult(PASS),
        )
        d = vr.as_log_dict()
        required = {
            "gate_1", "gate_2", "gate_3",
            "gate_1_reason", "gate_2_reason", "gate_3_reason",
            "verification_status", "false_positive_candidate",
        }
        assert required.issubset(d.keys())

    def test_verified_result_has_correct_status(self):
        """AC-P4-10: verified result serialises verification_status as 'verified'."""
        vr = VerifierResult(
            gate_1=GateResult(PASS),
            gate_2=GateResult(PASS),
            gate_3=GateResult(SKIP, "no test suite detected"),
        )
        d = vr.as_log_dict()
        assert d["verification_status"] == "verified"
        assert d["false_positive_candidate"] is False


# ---------------------------------------------------------------------------
# No write access invariant (AC-P4-11)
# ---------------------------------------------------------------------------

class TestNoWriteAccess:
    def test_verifier_does_not_write_to_worktree(self, tmp_path):
        """AC-P4-11: Verifier must not mutate any file in the worktree."""
        wt = tmp_path / "worktree"
        wt.mkdir()
        target = wt / "file.py"
        original_content = "import subprocess\nsubprocess.run(['ls'])\n"
        _write_file(target, original_content)
        original_mtime = target.stat().st_mtime

        # Gate 1: mock semgrep — no findings
        # Gate 2: mock git show — pre-edit same as post-edit (no changes → PASS)
        # Gate 3: no tests dir → SKIP
        mock_semgrep = MagicMock(returncode=0, stdout=_empty_semgrep_json(), stderr="")
        mock_git = MagicMock(returncode=0, stdout=original_content, stderr="")

        call_count = 0
        def mock_run(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            cmd = args[0] if args else kwargs.get("args", [])
            if isinstance(cmd, list) and "git" in cmd:
                return mock_git
            return mock_semgrep

        with patch("subprocess.run", side_effect=mock_run):
            v = Verifier()
            v.verify(
                worktree_path=wt,
                repo_path=tmp_path,
                file_path="file.py",
                rule_id="python.lang.security.audit.subprocess-shell-true",
                line_start=2,
                line_end=2,
            )

        # File must be byte-identical after Verifier run
        assert target.read_text(encoding="utf-8") == original_content, (
            "Verifier must not write to the worktree (AC-P4-11)"
        )
        assert target.stat().st_mtime == original_mtime, (
            "Verifier must not touch (mtime change) any file in the worktree"
        )


# ---------------------------------------------------------------------------
# ADR-016 — No short-circuit: all three gates always run
# ---------------------------------------------------------------------------

class TestNoShortCircuit:
    def test_all_gates_run_even_when_gate1_fails(self, tmp_path):
        """ADR-016: Gate 2 and Gate 3 must be evaluated even when Gate 1 FAIL."""
        wt = tmp_path / "worktree"
        wt.mkdir()
        target = wt / "file.py"
        content = "import subprocess\nsubprocess.run('ls', shell=True)\n"
        _write_file(target, content)

        # Gate 1: semgrep still finds the rule → FAIL
        semgrep_output = _make_semgrep_json(
            "python.lang.security.audit.subprocess-shell-true",
            str(target),
            2,
        )
        # Gate 2: git show returns same content → no diff → PASS
        call_responses: list[MagicMock] = []

        def mock_run(*args, **kwargs):
            cmd = args[0] if args else kwargs.get("args", [])
            if isinstance(cmd, list) and "git" in cmd:
                return MagicMock(returncode=0, stdout=content, stderr="")
            return MagicMock(returncode=0, stdout=semgrep_output, stderr="")

        with patch("subprocess.run", side_effect=mock_run):
            v = Verifier()
            result = v.verify(
                worktree_path=wt,
                repo_path=tmp_path,
                file_path="file.py",
                rule_id="python.lang.security.audit.subprocess-shell-true",
                line_start=2,
                line_end=2,
            )

        # Gate 1 must FAIL (rule still fires)
        assert result.gate_1.status == FAIL, "Gate 1 should FAIL when rule still fires"
        # Gate 2 must have run — status is not the default "not run"
        assert result.gate_2.reason != "not run", "Gate 2 must run even when Gate 1 FAIL"
        # Gate 3 must have run — no tests dir → SKIP
        assert result.gate_3.status == SKIP, "Gate 3 must run even when Gate 1 FAIL"
        # Overall: failed
        assert result.verification_status == "failed"
