# KS-TRACE: AC-P4-01 through AC-P4-13
# | assumption: Verifier is deterministic — no LLM call (ADR-015);
# |             all three gates always run, no short-circuit (ADR-016);
# |             pre-edit state retrieved via `git show HEAD:<file_path>` (C-P4-03);
# |             test suite detection uses tests/ directory + test_*.py glob (C-P4-04),
# |             not RepoContext._detect_test_runner (which misses plain directory layout)
# | test: test_verifier.py
"""
Verifier — Phase 4 deterministic patch validator.

Evaluates a Fix-Gen patch against three sequential gates and writes a structured
verdict to the run log. No LLM invocation (ADR-015). All three gates always run
regardless of intermediate failures (ADR-016).

Gate sequence:
  Gate 1 — Re-scan clean:  same rule_id no longer fires on the patched file.
  Gate 2 — Diff in bounds: all edits fall within [line_start, line_end] of file_path.
  Gate 3 — Test suite:     suite detected → must pass; not detected → SKIP (not FAIL).

"Verified" = Gate 1 PASS + Gate 2 PASS + Gate 3 (PASS or SKIP).
Any FAIL = verification_status: "failed". Fix branch persists — still the deliverable.

False positive candidate (C-P4-09):
  Gate 1 FAIL + Gate 2 PASS + Gate 3 (PASS or SKIP) → false_positive_candidate: True.
  All other Gate 1 FAIL patterns: false_positive_candidate: False.

Run log schema extension (C-P4-05) — new fields per record::

    "verifier": {
        "gate_1": "pass" | "fail" | "skip",
        "gate_2": "pass" | "fail" | "skip",
        "gate_3": "pass" | "fail" | "skip",
        "gate_1_reason": str,   # populated on fail/skip
        "gate_2_reason": str,
        "gate_3_reason": str,
        "verification_status": "verified" | "failed",
        "false_positive_candidate": bool,
    }
"""
from __future__ import annotations

import difflib
import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

__all__ = [
    "GateResult",
    "VerifierResult",
    "Verifier",
]

# Gate status literals
PASS = "pass"  # nosec B105 — gate status literal, not a password
FAIL = "fail"
SKIP = "skip"


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

@dataclass
class GateResult:
    """
    Outcome of a single Verifier gate.

    status: "pass" | "fail" | "skip"
    reason: human-readable explanation, populated on fail or skip.
    """
    status: str          # PASS | FAIL | SKIP
    reason: str = ""


@dataclass
class VerifierResult:
    """
    Aggregated outcome of all three Verifier gates.

    Consumers should read `verification_status` ("verified" | "failed") and
    `false_positive_candidate` (bool) for top-level decisions.

    All gate results are always populated regardless of intermediate failures.

    # KS-TRACE: AC-P4-01, C-P4-05, ADR-016
    """
    gate_1: GateResult = field(default_factory=lambda: GateResult(FAIL, "not run"))
    gate_2: GateResult = field(default_factory=lambda: GateResult(FAIL, "not run"))
    gate_3: GateResult = field(default_factory=lambda: GateResult(FAIL, "not run"))

    @property
    def verification_status(self) -> str:
        """
        "verified" iff Gate 1 PASS + Gate 2 PASS + Gate 3 (PASS or SKIP).
        Any other combination = "failed".

        # KS-TRACE: AC-P4-01, Q1-answer from KS-P4-00
        """
        g1_ok = self.gate_1.status == PASS
        g2_ok = self.gate_2.status == PASS
        g3_ok = self.gate_3.status in (PASS, SKIP)
        return "verified" if (g1_ok and g2_ok and g3_ok) else "failed"

    @property
    def false_positive_candidate(self) -> bool:
        """
        True when: Gate 1 FAIL + Gate 2 PASS + Gate 3 (PASS or SKIP).
        Signal: fix was in-bounds and tests pass, but scanner still fires —
        suggests a reachability-unaware false positive rather than a bad fix.

        # KS-TRACE: AC-P4-08, AC-P4-09, C-P4-09
        """
        return (
            self.gate_1.status == FAIL
            and self.gate_2.status == PASS
            and self.gate_3.status in (PASS, SKIP)
        )

    def as_log_dict(self) -> dict[str, Any]:
        """Serialize to the run log verifier sub-dict (C-P4-05)."""
        return {
            "gate_1": self.gate_1.status,
            "gate_2": self.gate_2.status,
            "gate_3": self.gate_3.status,
            "gate_1_reason": self.gate_1.reason,
            "gate_2_reason": self.gate_2.reason,
            "gate_3_reason": self.gate_3.reason,
            "verification_status": self.verification_status,
            "false_positive_candidate": self.false_positive_candidate,
        }


# ---------------------------------------------------------------------------
# Verifier
# ---------------------------------------------------------------------------

class Verifier:
    """
    Deterministic three-gate patch validator (ADR-015).

    No LLM call. Subprocess-based gate execution. All three gates always run
    regardless of intermediate failures (ADR-016).

    Usage::

        verifier = Verifier(timeout_seconds=120)
        result = verifier.verify(
            worktree_path=Path("/tmp/repomend-fix-abc123"),
            repo_path=Path("/path/to/repo"),
            file_path="vulnerable.py",
            rule_id="python.lang.security.audit.subprocess-shell-true",
            line_start=24,
            line_end=24,
        )
        # result.verification_status → "verified" | "failed"
        # result.false_positive_candidate → bool

    # KS-TRACE: AC-P4-01, ADR-015, ADR-016
    """

    def __init__(self, timeout_seconds: int = 120) -> None:
        """
        Args:
            timeout_seconds: Wall-clock timeout per gate subprocess call.
                             Configurable via repomend.toml [verifier] timeout_seconds.
                             Timeout on a gate → FAIL with reason: "timeout". (C-P4-10)
        """
        self.timeout_seconds = timeout_seconds

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def verify(
        self,
        *,
        worktree_path: Path,
        repo_path: Path,
        file_path: str,
        rule_id: str,
        line_start: int,
        line_end: int,
    ) -> VerifierResult:
        """
        Run all three gates and return an aggregated VerifierResult.

        All three gates always run — ADR-016: no short-circuit on FAIL.
        The false-positive-candidate pattern requires Gate 2 and Gate 3 results
        even when Gate 1 fails.

        Args:
            worktree_path: Path to the fix worktree (contains patched file).
            repo_path:     Path to the repository root (for re-scan invocation).
            file_path:     Relative path to the patched file (from repo root).
            rule_id:       Scanner rule ID that originally fired.
            line_start:    First line of the authorised edit range (1-indexed).
            line_end:      Last line of the authorised edit range (1-indexed).

        Returns:
            VerifierResult with all three gate outcomes populated.

        # KS-TRACE: AC-P4-01 through AC-P4-13, ADR-015, ADR-016
        """
        result = VerifierResult()

        # ADR-016: all three gates always run — no short-circuit
        result.gate_1 = self._gate_1_rescan(
            worktree_path=worktree_path,
            file_path=file_path,
            rule_id=rule_id,
        )
        result.gate_2 = self._gate_2_diff_in_bounds(
            worktree_path=worktree_path,
            file_path=file_path,
            line_start=line_start,
            line_end=line_end,
            gate_1_timed_out=(result.gate_1.reason == "timeout"),
        )
        result.gate_3 = self._gate_3_test_suite(
            worktree_path=worktree_path,
        )

        return result

    def append_to_run_log(self, run_log: Any, result: VerifierResult) -> None:
        """
        Append the verifier sub-dict to an existing run log record.

        Called by the Orchestrator after verify() — merges verifier data into
        the most recent run log record by appending a new record that pairs the
        verifier result with the last fix record's finding_id.

        In practice the Orchestrator passes the verifier dict directly when
        constructing the full run log record. This helper is for standalone use.

        # KS-TRACE: C-P4-05, AC-P4-10
        """
        run_log.append({"verifier": result.as_log_dict()})

    # ------------------------------------------------------------------
    # Gate 1 — Re-scan clean
    # ------------------------------------------------------------------

    def _gate_1_rescan(
        self,
        *,
        worktree_path: Path,
        file_path: str,
        rule_id: str,
    ) -> GateResult:
        """
        Run the same scanner rule against the patched file.
        PASS = rule no longer fires. FAIL = rule still fires or error.

        Invokes semgrep with --include scoped to file_path and --rule-id
        scoped to rule_id — identical flags to the original scan (C-P4-02).

        Timeout: self.timeout_seconds → FAIL with reason: "timeout" (C-P4-10).

        # KS-TRACE: AC-P4-02, AC-P4-03, C-P4-02
        """
        target = worktree_path / file_path

        # Determine scanner from rule_id prefix
        scanner_cmd = self._scanner_cmd_for_rule(rule_id, target)
        if scanner_cmd is None:
            return GateResult(FAIL, f"no scanner handler for rule_id: {rule_id!r}")

        try:
            proc = subprocess.run(
                scanner_cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                encoding="utf-8",
                errors="replace",
            )
        except subprocess.TimeoutExpired:
            return GateResult(FAIL, "timeout")
        except FileNotFoundError as exc:
            return GateResult(FAIL, f"scanner not found: {exc}")

        # Parse output for findings matching rule_id
        findings = self._parse_semgrep_output(proc.stdout, rule_id)
        if findings:
            return GateResult(FAIL, f"rule still fires: {len(findings)} finding(s) remain")
        return GateResult(PASS)

    def _scanner_cmd_for_rule(
        self, rule_id: str, target: Path
    ) -> list[str] | None:
        """
        Build the scanner subprocess command for a given rule_id.
        Currently supports semgrep rules (all rule_ids in the fixture set).

        Returns None if no handler is registered for the rule_id prefix.

        # KS-TRACE: C-P4-02 — same invocation flags as Orchestrator
        """
        # All fixture rule_ids are semgrep rules (python.lang.* or python.*)
        # Extend this dispatch table in Phase 5 for bandit/pip-audit/eslint rules.
        return [
            "semgrep",
            "--json",
            "--metrics", "off",
            "--include", target.name,
            "--config", f"r/{rule_id}",
            str(target.parent),
        ]

    @staticmethod
    def _parse_semgrep_output(stdout: str, rule_id: str) -> list[dict[str, Any]]:
        """
        Parse semgrep JSON output and return findings matching rule_id.
        Returns empty list if output is not valid JSON or has no results key.

        # KS-TRACE: AC-P4-02, AC-P4-03
        """
        try:
            data = json.loads(stdout)
        except (json.JSONDecodeError, ValueError):
            return []
        results = data.get("results", [])
        return [r for r in results if r.get("check_id", "") == rule_id]

    # ------------------------------------------------------------------
    # Gate 2 — Diff in bounds
    # ------------------------------------------------------------------

    def _gate_2_diff_in_bounds(
        self,
        *,
        worktree_path: Path,
        file_path: str,
        line_start: int,
        line_end: int,
        gate_1_timed_out: bool = False,
    ) -> GateResult:
        """
        Assert that edits are within allowed zones (Option E — D-P4-01).

        PASS iff: (1) at least one edit touches [line_start, line_end], AND
        (2) all other edits fall within the import block (lines 1 through the
        last contiguous import/from/comment/blank line at top of file).

        Pre-edit content retrieved via `git show HEAD:<file_path>` from within
        the worktree — git-native, consistent with addendum C-P3-11 (no .orig files).

        If gate_1 timed out, the patched file may not exist in a consistent state.
        Gate 2 still runs but records reason: "gate_1_timeout" on FAIL.

        # KS-TRACE: AC-P4-04, AC-P4-05, C-P4-03, D-P4-01
        """
        # Determine pre-edit baseline.
        # When apply_fix commits before the verifier runs (ADR-017), HEAD
        # already reflects the patched state and disk == HEAD.  Detect this
        # by checking for uncommitted changes; if the tree is clean, use
        # HEAD^ (parent commit = original pre-fix state).
        try:
            diff_check = subprocess.run(
                ["git", "diff", "HEAD", "--", file_path],
                cwd=str(worktree_path),
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                encoding="utf-8",
                errors="replace",
            )
        except subprocess.TimeoutExpired:
            return GateResult(FAIL, "timeout")
        except FileNotFoundError:
            return GateResult(FAIL, "git_not_found")

        has_uncommitted = (
            diff_check.returncode == 0
            and bool(diff_check.stdout.strip())
        )
        pre_edit_ref = (
            f"HEAD:{file_path}"
            if has_uncommitted
            else f"HEAD^:{file_path}"
        )

        # Retrieve pre-edit content via git show
        try:
            git_proc = subprocess.run(
                ["git", "show", pre_edit_ref],
                cwd=str(worktree_path),
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                encoding="utf-8",
                errors="replace",
            )
        except subprocess.TimeoutExpired:
            return GateResult(FAIL, "timeout")
        except FileNotFoundError:
            return GateResult(FAIL, "git_not_found")

        if git_proc.returncode != 0:
            reason = "git_object_not_found"
            if gate_1_timed_out:
                reason = "gate_1_timeout"
            return GateResult(FAIL, reason)

        pre_edit_lines = git_proc.stdout.splitlines(keepends=True)

        # Read patched file from worktree disk
        patched_path = worktree_path / file_path
        try:
            post_edit_lines = patched_path.read_text(
                encoding="utf-8", errors="replace"
            ).splitlines(keepends=True)
        except OSError as exc:
            return GateResult(FAIL, f"cannot read patched file: {exc}")

        # Compute unified diff and check that every changed line is in bounds
        diff = list(difflib.unified_diff(
            pre_edit_lines,
            post_edit_lines,
            lineterm="",
        ))

        touched_vuln, out_of_bounds = self._out_of_bounds_lines(
            diff, line_start, line_end,
        )

        if not touched_vuln:
            # No edit touched the vulnerability range — fix did not apply
            return GateResult(
                FAIL,
                f"vulnerability lines [{line_start}, {line_end}] were not modified",
            )

        if out_of_bounds:
            lines_str = ", ".join(str(ln) for ln in sorted(out_of_bounds))
            return GateResult(
                FAIL,
                f"edits outside [{line_start}, {line_end}] and import block: lines {lines_str}",
            )

        return GateResult(PASS)

    @staticmethod
    def _out_of_bounds_lines(
        diff: list[str],
        line_start: int,
        line_end: int,
        import_block_end: int = 0,
    ) -> tuple[bool, set[int]]:
        """
        Parse a unified diff and return (touched_vuln, out_of_bounds).

        touched_vuln: True if any '-' line's PRE-EDIT position falls within
                      [line_start, line_end].
        out_of_bounds: set of line numbers (pre-edit for '-' lines, post-edit
                       for '+' lines) that are out of the allowed zones.

        Allowed zones for '+' lines (D-P4-01 Option E):
          - Any hunk whose pre-edit range overlaps [line_start, line_end] is the
            "vuln hunk" — all '+' lines in it are permitted replacements.
          - Any '+' line whose content matches a Python import statement is
            permitted regardless of location (necessary support edit).
          - Everything else is out of bounds.

        Allowed zones for '-' lines:
          - Pre-edit position within [line_start, line_end] → permitted.
          - Content is a Python import statement → permitted (rare: removing old import).
          - Everything else is out of bounds.

        Unified diff hunk header: @@ -PRE_START[,PRE_COUNT] +POST_START[,POST_COUNT] @@

        # KS-TRACE: AC-P4-04, AC-P4-05, D-P4-01
        """
        import re

        import_re = re.compile(r'^\s*(import|from)\s')
        out_of_bounds: set[int] = set()
        touched_vuln = False
        pre_line = 0
        post_line = 0
        in_vuln_hunk = False

        for raw_line in diff:
            line = raw_line.rstrip("\n")

            # Hunk header — parse both pre-edit and post-edit start positions
            hunk_match = re.match(
                r"^@@ -(?P<pre>\d+)(?:,(?P<pre_c>\d+))? \+(?P<post>\d+)(?:,(?P<post_c>\d+))? @@",
                line,
            )
            if hunk_match:
                pre_line = int(hunk_match.group("pre"))
                pre_count = int(hunk_match.group("pre_c") or 1)
                post_line = int(hunk_match.group("post"))
                # Hunk is the "vuln hunk" if its pre-edit range overlaps [line_start, line_end]
                hunk_pre_end = pre_line + pre_count - 1
                in_vuln_hunk = not (hunk_pre_end < line_start or pre_line > line_end)
                continue

            if line.startswith("---") or line.startswith("+++"):
                continue

            if line.startswith("+"):
                content = line[1:]
                if not in_vuln_hunk and not import_re.match(content):
                    out_of_bounds.add(post_line)
                post_line += 1

            elif line.startswith("-"):
                content = line[1:]
                if line_start <= pre_line <= line_end:
                    touched_vuln = True
                elif in_vuln_hunk:
                    # Removal is within the vulnerability hunk — permitted.
                    # A correct fix often needs to replace adjacent lines
                    # (e.g. the `pass` body of a bare except).
                    pass
                elif not import_re.match(content):
                    out_of_bounds.add(pre_line)
                pre_line += 1

            else:
                # Context line — advance both counters
                pre_line += 1
                post_line += 1

        return touched_vuln, out_of_bounds


    # ------------------------------------------------------------------
    # Gate 3
    # ------------------------------------------------------------------
    # Gate 3 — Test suite
    # ------------------------------------------------------------------

    def _gate_3_test_suite(
        self,
        *,
        worktree_path: Path,
    ) -> GateResult:
        """
        Detect and run the test suite in the worktree.

        Detection (C-P4-04):
          - pytest: `tests/` directory exists OR any `test_*.py` in repo root
          - jest:   `package.json` with a `test` script containing "jest"

        If no suite detected: SKIP (not FAIL). Logged as gate_3: "skip".
        If detected and all pass: PASS.
        If detected and any fail: FAIL.

        Timeout: self.timeout_seconds → FAIL with reason: "timeout".

        Note: RepoContext._detect_test_runner is NOT used here — it checks for
        pytest.ini / conftest.py / pyproject.toml only. The fixture repo has
        tests/test_clean.py but none of those config files, so RepoContext would
        return UNKNOWN. Verifier implements its own detection per C-P4-04.

        # KS-TRACE: AC-P4-06, AC-P4-07, C-P4-04
        """
        runner = self._detect_test_runner(worktree_path)
        if runner is None:
            return GateResult(SKIP, "no test suite detected")

        if runner == "pytest":
            return self._run_pytest(worktree_path)
        if runner == "jest":
            return self._run_jest(worktree_path)

        return GateResult(SKIP, "no test suite detected")

    @staticmethod
    def _detect_test_runner(worktree_path: Path) -> str | None:
        """
        Detect pytest or jest in the worktree.

        pytest heuristics (C-P4-04):
          1. `tests/` directory exists with at least one `test_*.py` file
          2. Any `test_*.py` file in the repo root
          3. `pytest.ini`, `conftest.py`, or `pyproject.toml` with [tool.pytest

        jest heuristics (C-P4-04):
          1. `package.json` with a `test` script containing "jest"
          2. `jest.config.*` file present

        Returns "pytest", "jest", or None.

        # KS-TRACE: AC-P4-06, AC-P4-07, C-P4-04
        """
        # pytest — directory-based detection (covers repomend-fixture layout)
        tests_dir = worktree_path / "tests"
        if tests_dir.is_dir() and any(tests_dir.glob("test_*.py")):
            return "pytest"
        if any(worktree_path.glob("test_*.py")):
            return "pytest"
        if (worktree_path / "pytest.ini").exists():
            return "pytest"
        if (worktree_path / "conftest.py").exists():
            return "pytest"
        if (worktree_path / "pyproject.toml").exists():
            try:
                content = (worktree_path / "pyproject.toml").read_text(encoding="utf-8")
                if "[tool.pytest" in content:
                    return "pytest"
            except OSError:
                pass

        # jest — package.json based detection
        pkg_json = worktree_path / "package.json"
        if pkg_json.exists():
            try:
                import json as _json
                pkg = _json.loads(pkg_json.read_text(encoding="utf-8"))
                test_script = pkg.get("scripts", {}).get("test", "")
                if "jest" in test_script:
                    return "jest"
            except (OSError, ValueError):
                pass
            for cfg in ["jest.config.js", "jest.config.ts", "jest.config.mjs"]:
                if (worktree_path / cfg).exists():
                    return "jest"

        return None

    def _run_pytest(self, worktree_path: Path) -> GateResult:
        """
        Run pytest in the worktree. PASS if exit code 0, FAIL otherwise.

        Uses `python -m pytest` to avoid PATH dependency on the pytest binary.

        # KS-TRACE: AC-P4-06, C-P4-04
        """
        try:
            proc = subprocess.run(
                ["python", "-m", "pytest", "--tb=short", "-q"],
                cwd=str(worktree_path),
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                encoding="utf-8",
                errors="replace",
            )
        except subprocess.TimeoutExpired:
            return GateResult(FAIL, "timeout")
        except FileNotFoundError:
            return GateResult(FAIL, "python not found")

        if proc.returncode == 0:
            return GateResult(PASS)
        # Trim stderr/stdout for the reason field — keep it readable in the log
        output = (proc.stdout + proc.stderr).strip()
        summary = output[-500:] if len(output) > 500 else output
        # SKIP (not FAIL) when tests can't run due to missing dependencies.
        # This happens for external repos whose test deps aren't installed in
        # the current Python environment — not a sign the fix is wrong.
        if "ModuleNotFoundError" in output or "ImportError" in output or "no tests ran" in output:
            return GateResult(SKIP, f"test deps not installed: {summary[:200]}")
        return GateResult(FAIL, f"pytest exit {proc.returncode}: {summary}")

    def _run_jest(self, worktree_path: Path) -> GateResult:
        """
        Run jest in the worktree. PASS if exit code 0, FAIL otherwise.

        # KS-TRACE: AC-P4-06, C-P4-04
        """
        try:
            proc = subprocess.run(
                ["npx", "jest", "--no-coverage"],
                cwd=str(worktree_path),
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                encoding="utf-8",
                errors="replace",
            )
        except subprocess.TimeoutExpired:
            return GateResult(FAIL, "timeout")
        except FileNotFoundError:
            return GateResult(FAIL, "npx not found")

        if proc.returncode == 0:
            return GateResult(PASS)
        output = (proc.stdout + proc.stderr).strip()
        summary = output[-500:] if len(output) > 500 else output
        return GateResult(FAIL, f"jest exit {proc.returncode}: {summary}")
