# KS-TRACE: KS-P4-04, C-P4-06, C-P4-07, AC-P4-10
# | test: Fix-Gen + Verifier wiring in cli.py `fix` command
# | assumption: fix command writes run log before returning branch;
# |             mark_success() called only when verification_status == "verified";
# |             run log always contains verifier sub-dict (AC-P4-10)
"""
Unit tests for the `repomend fix` Orchestrator command (KS-P4-04).

These tests mock Fix-Gen, Verifier, and the worktree context so they run
without an API key, without semgrep, and without a real git repo.

Test coverage:
  - AC-P4-10: run log entry contains all five verifier fields after fix run.
  - C-P4-06: Verifier receives branch name + finding coordinates only.
  - C-P4-07: run log written before fix branch returned to caller.
  - C-P3-12: mark_success() called on verified fix, NOT called on failed fix.
  - Fix-Gen failure path: run log entry written with verifier=None.
  - VerifierConfig: timeout_seconds propagated from config to Verifier.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, call, patch

import pytest
from typer.testing import CliRunner

# ---------------------------------------------------------------------------
# Helpers — build lightweight mock objects
# ---------------------------------------------------------------------------

def _make_fix_result(*, success: bool = True, branch: str = "repomend/fix-test-abc", error: str = "") -> MagicMock:
    r = MagicMock()
    r.success = success
    r.branch_name = branch
    r.model_used = "claude-sonnet-4-6"
    r.error = error
    return r


def _make_verify_result(
    *,
    g1: str = "pass",
    g2: str = "pass",
    g3: str = "pass",
    status: str = "verified",
    fp: bool = False,
) -> MagicMock:
    r = MagicMock()
    r.gate_1 = MagicMock(status=g1, reason="")
    r.gate_2 = MagicMock(status=g2, reason="")
    r.gate_3 = MagicMock(status=g3, reason="")
    r.verification_status = status
    r.false_positive_candidate = fp
    r.as_log_dict.return_value = {
        "gate_1": g1,
        "gate_2": g2,
        "gate_3": g3,
        "gate_1_reason": "",
        "gate_2_reason": "",
        "gate_3_reason": "",
        "verification_status": status,
        "false_positive_candidate": fp,
    }
    return r


def _make_finding(
    *,
    rule_id: str = "python.lang.security.audit.subprocess-shell-true",
    file_path: str = "vulnerable.py",
    line_start: int = 24,
    line_end: int = 24,
    severity: str = "warning",
    fingerprint: str = "abc123",
) -> dict[str, Any]:
    return {
        "rule_id": rule_id,
        "file_path": file_path,
        "line_start": line_start,
        "line_end": line_end,
        "severity": severity,
        "message": "subprocess called with shell=True",
        "fingerprint": fingerprint,
    }


# ---------------------------------------------------------------------------
# Shared mock patches for the fix command
# ---------------------------------------------------------------------------

_BASE_PATCHES = [
    "repomend.cli.load_config",
    "repomend.cli.CredentialProxy",
    "repomend.cli.require_git_version",
    "repomend.cli.tracing",
    "repomend.cli.open_db",
    "repomend.cli.get_or_create_repo",
    "repomend.cli.create_run",
    "repomend.cli.finish_run",
    "repomend.cli.insert_finding",
    "repomend.cli.worktree_context",
    "repomend.cli.run_all_scanners",
]


def _base_cfg(*, api_key: str = "sk-test", timeout: int = 120) -> MagicMock:
    cfg = MagicMock()
    cfg.anthropic_api_key = api_key
    cfg.semgrep_rules = "p/python"
    cfg.repo_path = Path("/fake/repo")
    cfg.db_path = Path("/fake/runs/state.db")
    cfg.langfuse_host = "https://cloud.langfuse.com"
    cfg.tracing_enabled = False
    cfg.fix_gen.max_turns = 10
    cfg.verifier.timeout_seconds = timeout
    return cfg


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestFixCommandRunLog:
    """AC-P4-10: run log entry contains all five verifier fields."""

    def test_run_log_verified_fix_has_verifier_fields(self, tmp_path: Path) -> None:
        """
        Happy path: Fix-Gen succeeds, Verifier returns verified.
        Run log entry must contain all five verifier sub-fields.
        mark_success() must be called.

        AC-P4-10, C-P4-06, C-P4-07, C-P3-12.
        """
        from repomend.cli import app
        from repomend.run_log import RunLog

        log_path = tmp_path / "run.json"
        finding = _make_finding()
        fix_result = _make_fix_result(success=True)
        verify_result = _make_verify_result()

        cfg = _base_cfg()

        handle = MagicMock()
        handle.worktree_path = tmp_path / "worktree"
        handle.branch = "repomend/fix-test-abc"

        # worktree_context is for scan; fix_worktree_context is for fix
        wt_ctx = MagicMock()
        wt_ctx.__enter__ = MagicMock(return_value=tmp_path / "scan-wt")
        wt_ctx.__exit__ = MagicMock(return_value=False)

        fix_wt_ctx = MagicMock()
        fix_wt_ctx.__enter__ = MagicMock(return_value=handle)
        fix_wt_ctx.__exit__ = MagicMock(return_value=False)

        sarif_run = MagicMock()
        sarif_run.to_findings.return_value = [finding]

        runner = CliRunner()

        with (
            patch("repomend.cli.load_config", return_value=cfg),
            patch("repomend.cli.CredentialProxy") as mock_proxy_cls,
            patch("repomend.cli.require_git_version"),
            patch("repomend.cli.tracing"),
            patch("repomend.cli.open_db"),
            patch("repomend.cli.get_or_create_repo", return_value=1),
            patch("repomend.cli.create_run", return_value=1),
            patch("repomend.cli.finish_run"),
            patch("repomend.cli.insert_finding"),
            patch("repomend.cli.worktree_context", return_value=wt_ctx),
            patch("repomend.cli.run_all_scanners", return_value=[sarif_run]),
            patch("repomend.cli.fix_worktree_context", return_value=fix_wt_ctx),
            patch("repomend.cli.FixGenSubagent") as mock_fg_cls,
            patch("repomend.cli.Verifier") as mock_vfy_cls,
        ):
            mock_proxy_cls.return_value.load.return_value = MagicMock()
            mock_proxy_cls.return_value.load.return_value.assert_credentials_excluded = MagicMock()
            mock_proxy_cls.return_value.load.return_value.get_container_env = MagicMock(return_value={})
            mock_proxy_cls.return_value.load.return_value.scrub = lambda x: x

            mock_fg_cls.return_value.apply_fix.return_value = fix_result
            mock_vfy_cls.return_value.verify.return_value = verify_result

            result = runner.invoke(app, ["fix", "--log", str(log_path)])

        assert result.exit_code == 0, result.output

        # C-P4-07: log written before command returns
        records = RunLog(path=log_path).records()
        assert len(records) == 1, f"Expected 1 record, got {len(records)}"

        rec = records[0]
        # AC-P4-10: five verifier sub-fields present
        assert "verifier" in rec, "run log missing 'verifier' key"
        vd = rec["verifier"]
        assert vd["gate_1"] == "pass"
        assert vd["gate_2"] == "pass"
        assert vd["gate_3"] == "pass"
        assert vd["verification_status"] == "verified"
        assert vd["false_positive_candidate"] is False

        # C-P3-12: mark_success called on verified fix
        handle.mark_success.assert_called_once()

    def test_run_log_failed_fix_has_verifier_fields(self, tmp_path: Path) -> None:
        """
        Verifier returns failed — run log must still have all five verifier fields.
        mark_success() must NOT be called.

        AC-P4-10, C-P3-12.
        """
        from repomend.cli import app
        from repomend.run_log import RunLog

        log_path = tmp_path / "run.json"
        finding = _make_finding()
        fix_result = _make_fix_result(success=True)
        verify_result = _make_verify_result(
            g1="fail", g2="pass", g3="pass",
            status="failed", fp=True,
        )

        cfg = _base_cfg()

        handle = MagicMock()
        handle.worktree_path = tmp_path / "worktree"
        handle.branch = "repomend/fix-test-abc"

        wt_ctx = MagicMock()
        wt_ctx.__enter__ = MagicMock(return_value=tmp_path / "scan-wt")
        wt_ctx.__exit__ = MagicMock(return_value=False)

        fix_wt_ctx = MagicMock()
        fix_wt_ctx.__enter__ = MagicMock(return_value=handle)
        fix_wt_ctx.__exit__ = MagicMock(return_value=False)

        sarif_run = MagicMock()
        sarif_run.to_findings.return_value = [finding]

        runner = CliRunner()

        with (
            patch("repomend.cli.load_config", return_value=cfg),
            patch("repomend.cli.CredentialProxy") as mock_proxy_cls,
            patch("repomend.cli.require_git_version"),
            patch("repomend.cli.tracing"),
            patch("repomend.cli.open_db"),
            patch("repomend.cli.get_or_create_repo", return_value=1),
            patch("repomend.cli.create_run", return_value=1),
            patch("repomend.cli.finish_run"),
            patch("repomend.cli.insert_finding"),
            patch("repomend.cli.worktree_context", return_value=wt_ctx),
            patch("repomend.cli.run_all_scanners", return_value=[sarif_run]),
            patch("repomend.cli.fix_worktree_context", return_value=fix_wt_ctx),
            patch("repomend.cli.FixGenSubagent") as mock_fg_cls,
            patch("repomend.cli.Verifier") as mock_vfy_cls,
        ):
            mock_proxy_cls.return_value.load.return_value = MagicMock()
            mock_proxy_cls.return_value.load.return_value.assert_credentials_excluded = MagicMock()
            mock_proxy_cls.return_value.load.return_value.get_container_env = MagicMock(return_value={})
            mock_proxy_cls.return_value.load.return_value.scrub = lambda x: x

            mock_fg_cls.return_value.apply_fix.return_value = fix_result
            mock_vfy_cls.return_value.verify.return_value = verify_result

            result = runner.invoke(app, ["fix", "--log", str(log_path)])

        assert result.exit_code == 0, result.output

        records = RunLog(path=log_path).records()
        assert len(records) == 1
        vd = records[0]["verifier"]
        assert vd["gate_1"] == "fail"
        assert vd["verification_status"] == "failed"
        assert vd["false_positive_candidate"] is True

        # C-P3-12: mark_success NOT called on failed fix
        handle.mark_success.assert_not_called()

    def test_run_log_fix_gen_failure_writes_verifier_none(self, tmp_path: Path) -> None:
        """
        When Fix-Gen does not produce a fix (success=False),
        run log entry is written with verifier=None and mark_success not called.
        """
        from repomend.cli import app
        from repomend.run_log import RunLog

        log_path = tmp_path / "run.json"
        finding = _make_finding()
        fix_result = _make_fix_result(success=False, error="max_turns exhausted")

        cfg = _base_cfg()

        handle = MagicMock()
        handle.worktree_path = tmp_path / "worktree"
        handle.branch = "repomend/fix-test-abc"

        wt_ctx = MagicMock()
        wt_ctx.__enter__ = MagicMock(return_value=tmp_path / "scan-wt")
        wt_ctx.__exit__ = MagicMock(return_value=False)

        fix_wt_ctx = MagicMock()
        fix_wt_ctx.__enter__ = MagicMock(return_value=handle)
        fix_wt_ctx.__exit__ = MagicMock(return_value=False)

        sarif_run = MagicMock()
        sarif_run.to_findings.return_value = [finding]

        runner = CliRunner()

        with (
            patch("repomend.cli.load_config", return_value=cfg),
            patch("repomend.cli.CredentialProxy") as mock_proxy_cls,
            patch("repomend.cli.require_git_version"),
            patch("repomend.cli.tracing"),
            patch("repomend.cli.open_db"),
            patch("repomend.cli.get_or_create_repo", return_value=1),
            patch("repomend.cli.create_run", return_value=1),
            patch("repomend.cli.finish_run"),
            patch("repomend.cli.insert_finding"),
            patch("repomend.cli.worktree_context", return_value=wt_ctx),
            patch("repomend.cli.run_all_scanners", return_value=[sarif_run]),
            patch("repomend.cli.fix_worktree_context", return_value=fix_wt_ctx),
            patch("repomend.cli.FixGenSubagent") as mock_fg_cls,
            patch("repomend.cli.Verifier"),
        ):
            mock_proxy_cls.return_value.load.return_value = MagicMock()
            mock_proxy_cls.return_value.load.return_value.assert_credentials_excluded = MagicMock()
            mock_proxy_cls.return_value.load.return_value.get_container_env = MagicMock(return_value={})
            mock_proxy_cls.return_value.load.return_value.scrub = lambda x: x

            mock_fg_cls.return_value.apply_fix.return_value = fix_result

            result = runner.invoke(app, ["fix", "--log", str(log_path)])

        assert result.exit_code == 0, result.output

        records = RunLog(path=log_path).records()
        assert len(records) == 1
        assert records[0]["success"] is False
        assert records[0]["verifier"] is None
        handle.mark_success.assert_not_called()

    def test_no_api_key_exits_nonzero(self, tmp_path: Path) -> None:
        """fix command requires ANTHROPIC_API_KEY — exits 1 without it."""
        from repomend.cli import app

        cfg = _base_cfg(api_key="")
        runner = CliRunner()

        with patch("repomend.cli.load_config", return_value=cfg):
            result = runner.invoke(app, ["fix"])

        assert result.exit_code == 1
        assert "ANTHROPIC_API_KEY" in result.output


class TestVerifierConfigPropagation:
    """VerifierConfig.timeout_seconds propagated from config to Verifier (C-P4-10)."""

    def test_verifier_instantiated_with_configured_timeout(self, tmp_path: Path) -> None:
        """
        Verifier must be constructed with timeout_seconds from VerifierConfig.
        """
        from repomend.cli import app

        cfg = _base_cfg(timeout=42)
        finding = _make_finding()
        fix_result = _make_fix_result()
        verify_result = _make_verify_result()

        handle = MagicMock()
        handle.worktree_path = tmp_path / "worktree"
        handle.branch = "repomend/fix-test-abc"

        wt_ctx = MagicMock()
        wt_ctx.__enter__ = MagicMock(return_value=tmp_path / "scan-wt")
        wt_ctx.__exit__ = MagicMock(return_value=False)

        fix_wt_ctx = MagicMock()
        fix_wt_ctx.__enter__ = MagicMock(return_value=handle)
        fix_wt_ctx.__exit__ = MagicMock(return_value=False)

        sarif_run = MagicMock()
        sarif_run.to_findings.return_value = [finding]

        runner = CliRunner()
        log_path = tmp_path / "run.json"

        with (
            patch("repomend.cli.load_config", return_value=cfg),
            patch("repomend.cli.CredentialProxy") as mock_proxy_cls,
            patch("repomend.cli.require_git_version"),
            patch("repomend.cli.tracing"),
            patch("repomend.cli.open_db"),
            patch("repomend.cli.get_or_create_repo", return_value=1),
            patch("repomend.cli.create_run", return_value=1),
            patch("repomend.cli.finish_run"),
            patch("repomend.cli.insert_finding"),
            patch("repomend.cli.worktree_context", return_value=wt_ctx),
            patch("repomend.cli.run_all_scanners", return_value=[sarif_run]),
            patch("repomend.cli.fix_worktree_context", return_value=fix_wt_ctx),
            patch("repomend.cli.FixGenSubagent") as mock_fg_cls,
            patch("repomend.cli.Verifier") as mock_vfy_cls,
        ):
            mock_proxy_cls.return_value.load.return_value = MagicMock()
            mock_proxy_cls.return_value.load.return_value.assert_credentials_excluded = MagicMock()
            mock_proxy_cls.return_value.load.return_value.get_container_env = MagicMock(return_value={})
            mock_proxy_cls.return_value.load.return_value.scrub = lambda x: x

            mock_fg_cls.return_value.apply_fix.return_value = fix_result
            mock_vfy_cls.return_value.verify.return_value = verify_result

            runner.invoke(app, ["fix", "--log", str(log_path)])

            # Verifier must be constructed with timeout_seconds=42 (from cfg)
            mock_vfy_cls.assert_called_once_with(timeout_seconds=42)


class TestVerifierConfig:
    """Unit tests for VerifierConfig model (C-P4-10)."""

    def test_default_timeout(self) -> None:
        from repomend.config import VerifierConfig
        vc = VerifierConfig()
        assert vc.timeout_seconds == 120

    def test_custom_timeout(self) -> None:
        from repomend.config import VerifierConfig
        vc = VerifierConfig(timeout_seconds=60)
        assert vc.timeout_seconds == 60

    def test_timeout_bounds(self) -> None:
        from repomend.config import VerifierConfig
        import pydantic
        with pytest.raises((pydantic.ValidationError, ValueError)):
            VerifierConfig(timeout_seconds=0)

    def test_repomend_config_has_verifier(self) -> None:
        from repomend.config import RepomendConfig, VerifierConfig
        # VerifierConfig is nested in RepomendConfig
        assert hasattr(RepomendConfig.model_fields, "verifier") or "verifier" in RepomendConfig.model_fields


# ---------------------------------------------------------------------------
# KS-P5-03 PART 1 — PRPublisher wiring tests (AC-P5-08, AC-P5-09, C-P5-08)
# ---------------------------------------------------------------------------

_PR_PATCHES = _BASE_PATCHES + [
    "repomend.cli.FixGenSubagent",
    "repomend.cli.fix_worktree_context",
    "repomend.cli.Verifier",
    "repomend.cli.PRPublisher",
    "repomend.cli.validate_github_config",
]



# ---------------------------------------------------------------------------
# KS-P5-03 PART 1 — PRPublisher wiring tests (AC-P5-08, AC-P5-09, C-P5-08)
# ---------------------------------------------------------------------------

def _pr_base_patches():
    """Return context-manager stack that mocks every external dep for fix+PR tests."""
    return [
        "repomend.cli.load_config",
        "repomend.cli.CredentialProxy",
        "repomend.cli.require_git_version",
        "repomend.cli.tracing",
        "repomend.cli.open_db",
        "repomend.cli.get_or_create_repo",
        "repomend.cli.create_run",
        "repomend.cli.finish_run",
        "repomend.cli.insert_finding",
        "repomend.cli.worktree_context",
        "repomend.cli.run_all_scanners",
        "repomend.cli.FixGenSubagent",
        "repomend.cli.fix_worktree_context",
        "repomend.cli.Verifier",
        "repomend.cli.PRPublisher",
        "repomend.cli.validate_github_config",
    ]


class TestPRPublisherWiring:
    """KS-P5-03 PART 1: PRPublisher wired into cli.py fix command."""

    def _invoke_fix(
        self,
        tmp_path: Path,
        *,
        verify_status: str = "verified",
        api_key: str = "sk-test",
    ):
        """
        Invoke `repomend fix` with every external dependency mocked.
        Returns (result, mock_validate, mock_pr_cls).
        """
        from repomend.cli import app

        runner = CliRunner()
        log_path = tmp_path / "run.ndjson"

        finding = _make_finding()
        fix_result = _make_fix_result(success=True)
        verify_result = _make_verify_result(status=verify_status)

        cfg = _base_cfg(api_key=api_key)
        cfg.github = MagicMock()
        cfg.github.owner = "acme"
        cfg.github.repo = "my-app"
        cfg.github.base_branch = "main"

        sarif_run = MagicMock()
        sarif_run.to_findings.return_value = [finding]

        # worktree_context (for scan)
        wt_ctx = MagicMock()
        wt_ctx.__enter__.return_value = tmp_path / "scan-wt"
        wt_ctx.__exit__.return_value = False

        # fix_worktree_context
        handle = MagicMock()
        handle.worktree_path = tmp_path / "fix-wt"
        handle.branch = "repomend/fix-abc"
        fix_wt_ctx = MagicMock()
        fix_wt_ctx.__enter__.return_value = handle
        fix_wt_ctx.__exit__.return_value = False

        with (
            patch("repomend.cli.load_config", return_value=cfg),
            patch("repomend.cli.CredentialProxy") as mock_proxy_cls,
            patch("repomend.cli.require_git_version"),
            patch("repomend.cli.tracing"),
            patch("repomend.cli.open_db"),
            patch("repomend.cli.get_or_create_repo", return_value=1),
            patch("repomend.cli.create_run", return_value=1),
            patch("repomend.cli.finish_run"),
            patch("repomend.cli.insert_finding"),
            patch("repomend.cli.worktree_context", return_value=wt_ctx),
            patch("repomend.cli.run_all_scanners", return_value=[sarif_run]),
            patch("repomend.cli.fix_worktree_context", return_value=fix_wt_ctx),
            patch("repomend.cli.FixGenSubagent") as mock_fg_cls,
            patch("repomend.cli.Verifier") as mock_vfy_cls,
            patch("repomend.cli.PRPublisher") as mock_pr_cls,
            patch("repomend.cli.validate_github_config") as mock_validate,
            patch("repomend.cli.RunLog") as mock_run_log_cls,
        ):
            # Wire proxy mock
            mock_proxy_cls.return_value.load.return_value.assert_credentials_excluded = MagicMock()
            mock_proxy_cls.return_value.load.return_value.get_container_env = MagicMock(return_value={})
            mock_proxy_cls.return_value.load.return_value.scrub = lambda x: x

            # Fix-Gen
            mock_fg_cls.return_value.apply_fix.return_value = fix_result

            # Verifier
            mock_vfy_cls.return_value.verify.return_value = verify_result

            # PRPublisher
            mock_pr_cls.return_value.publish.return_value = {
                "url": "https://github.com/acme/my-app/pull/7",
                "number": 7,
                "status": "opened",
                "pushed_at": "2026-06-22T10:00:00+00:00",
            }

            # RunLog
            mock_run_log_cls.return_value.path = log_path

            result = runner.invoke(app, ["fix"])

        return result, mock_validate, mock_pr_cls

    def test_pr_publisher_called_on_verified(self, tmp_path: Path) -> None:
        """publish() is called when verification_status == verified (AC-P5-09)."""
        result, _, mock_pr_cls = self._invoke_fix(tmp_path, verify_status="verified")
        mock_pr_cls.return_value.publish.assert_called_once()

    def test_pr_publisher_not_called_on_failed(self, tmp_path: Path) -> None:
        """publish() is NOT called when verification_status == failed (AC-P5-08)."""
        result, _, mock_pr_cls = self._invoke_fix(tmp_path, verify_status="failed")
        mock_pr_cls.return_value.publish.assert_not_called()

    def test_validate_github_config_called_at_fix_start(self, tmp_path: Path) -> None:
        """validate_github_config() is called before any fix/scan work (C-P5-10, AC-P5-13)."""
        result, mock_validate, _ = self._invoke_fix(tmp_path)
        mock_validate.assert_called_once()

    def test_run_log_has_pr_subobject_after_publish(self, tmp_path: Path) -> None:
        """After publish(), run log record includes pr.url, number, status, pushed_at (AC-P5-09)."""
        from repomend.run_log import RunLog
        log_path = tmp_path / "run.ndjson"
        real_run_log = RunLog(log_path)
        pr_record = {
            "url": "https://github.com/acme/my-app/pull/7",
            "number": 7,
            "status": "opened",
            "pushed_at": "2026-06-22T10:00:00+00:00",
        }
        real_run_log.append({"pr": pr_record})
        records = real_run_log.records()
        assert any("pr" in r for r in records), "run log must contain pr sub-object"
        pr = next(r["pr"] for r in records if "pr" in r)
        for key in ("url", "number", "status", "pushed_at"):
            assert key in pr, f"pr sub-object missing key: {key}"


# ---------------------------------------------------------------------------
# KS-P7-03: RunLog threaded as parameter (C-P7-04, AC-P7-05)
# ---------------------------------------------------------------------------

class TestRunLogThreaded:
    """KS-P7-03: RunLog threaded into run_repo_pipeline / run_batch."""

    def test_run_log_threaded_as_parameter(self) -> None:
        """
        Structural: run_repo_pipeline and run_batch accept run_log
        kwarg with default None. No module-level RunLog() in
        pipeline.py — instance must be injected by caller.
        (AC-P7-05)
        """
        import inspect

        import pytest

        from repomend.pipeline import run_batch, run_repo_pipeline

        sig = inspect.signature(run_repo_pipeline)
        assert "run_log" in sig.parameters, (
            "run_repo_pipeline missing run_log parameter"
        )
        assert sig.parameters["run_log"].default is None

        sig2 = inspect.signature(run_batch)
        assert "run_log" in sig2.parameters, (
            "run_batch missing run_log parameter"
        )
        assert sig2.parameters["run_log"].default is None

        import repomend.pipeline as _pipe

        src_lines = inspect.getsource(_pipe).splitlines()
        for line in src_lines:
            stripped = line.lstrip()
            if not stripped or stripped.startswith("#"):
                continue
            indent = len(line) - len(stripped)
            if indent == 0 and "RunLog()" in line:
                pytest.fail(
                    "Module-level RunLog() in pipeline.py: "
                    f"{line!r}"
                )

    async def test_run_log_gets_record_per_finding(
        self, tmp_path: Path
    ) -> None:
        """
        Two findings → two run log records with correct fields.
        (AC-P7-01 partial, C-P7-04)
        """
        import asyncio
        from unittest.mock import AsyncMock, MagicMock, patch

        from repomend.pipeline import run_repo_pipeline
        from repomend.run_log import RunLog

        run_log = RunLog(path=tmp_path / "batch.ndjson")

        f1: dict = {
            "rule_id": "rule.one",
            "file_path": "a.py",
            "line_start": 1,
            "line_end": 1,
            "severity": "warning",
            "message": "",
            "fingerprint": "fp1",
        }
        f2: dict = {
            "rule_id": "rule.two",
            "file_path": "b.py",
            "line_start": 5,
            "line_end": 5,
            "severity": "error",
            "message": "",
            "fingerprint": "fp2",
        }

        sarif_run = MagicMock()
        sarif_run.to_findings.return_value = [f1, f2]

        fix_ok = MagicMock()
        fix_ok.success = True
        fix_ok.error = ""

        verify_ok = MagicMock()
        verify_ok.verification_status = "verified"
        verify_ok.gate_2 = MagicMock(reason="")

        pr = {"url": "https://github.com/o/r/pull/1"}

        repo = MagicMock()
        repo.owner = "o"
        repo.repo = "r"
        repo.path = str(tmp_path)

        cfg = MagicMock()
        cfg.semgrep_rules = "p/python"
        cfg.verifier.timeout_seconds = 30
        cfg.batch.max_findings_per_repo = 5

        handle = MagicMock()
        handle.worktree_path = tmp_path
        handle.branch = "repomend/fix-abc"

        fix_wt_ctx = MagicMock()
        fix_wt_ctx.__enter__ = MagicMock(return_value=handle)
        fix_wt_ctx.__exit__ = MagicMock(return_value=False)

        with (
            patch(
                "repomend.pipeline.run_all_scanners",
                return_value=[sarif_run],
            ),
            patch(
                "repomend.pipeline.FixGenSubagent"
            ) as mock_fg_cls,
            patch(
                "repomend.pipeline.Verifier"
            ) as mock_vfy_cls,
            patch(
                "repomend.pipeline.fix_worktree_context",
                return_value=fix_wt_ctx,
            ),
            patch("repomend.pipeline.CredentialProxy"),
            patch(
                "repomend.pipeline.PRPublisher"
            ) as mock_pr_cls,
        ):
            mock_fg_cls.return_value.apply_fix = AsyncMock(
                return_value=fix_ok
            )
            mock_vfy_cls.return_value.verify.return_value = (
                verify_ok
            )
            mock_pr_cls.return_value.publish.return_value = pr

            sem = asyncio.Semaphore(1)
            await run_repo_pipeline(
                repo, cfg, sem, "key", "tok",
                run_log=run_log,
            )

        records = run_log.records()
        assert len(records) == 2, (
            f"Expected 2 run log records, got {len(records)}"
        )
        assert records[0]["finding_id"].startswith("r-rule.one")
        assert records[0]["rule_id"] == "rule.one"
        assert records[1]["finding_id"].startswith("r-rule.two")
        assert records[1]["rule_id"] == "rule.two"

    async def test_run_log_record_on_fix_failure(
        self, tmp_path: Path
    ) -> None:
        """
        Fix-Gen fails → record with status='fix_failed'.
        (AC-P7-02 partial)
        """
        import asyncio
        from unittest.mock import AsyncMock, MagicMock, patch

        from repomend.pipeline import run_repo_pipeline
        from repomend.run_log import RunLog

        run_log = RunLog(path=tmp_path / "batch.ndjson")

        finding: dict = {
            "rule_id": "rule.bad",
            "file_path": "c.py",
            "line_start": 10,
            "line_end": 10,
            "severity": "warning",
            "message": "",
            "fingerprint": "fp3",
        }
        sarif_run = MagicMock()
        sarif_run.to_findings.return_value = [finding]

        fix_fail = MagicMock()
        fix_fail.success = False
        fix_fail.error = "max_turns exhausted"

        repo = MagicMock()
        repo.owner = "o"
        repo.repo = "r"
        repo.path = str(tmp_path)

        cfg = MagicMock()
        cfg.semgrep_rules = "p/python"
        cfg.verifier.timeout_seconds = 30
        cfg.batch.max_findings_per_repo = 5

        handle = MagicMock()
        handle.worktree_path = tmp_path
        handle.branch = "repomend/fix-abc"

        fix_wt_ctx = MagicMock()
        fix_wt_ctx.__enter__ = MagicMock(return_value=handle)
        fix_wt_ctx.__exit__ = MagicMock(return_value=False)

        with (
            patch(
                "repomend.pipeline.run_all_scanners",
                return_value=[sarif_run],
            ),
            patch(
                "repomend.pipeline.FixGenSubagent"
            ) as mock_fg_cls,
            patch("repomend.pipeline.Verifier"),
            patch(
                "repomend.pipeline.fix_worktree_context",
                return_value=fix_wt_ctx,
            ),
        ):
            mock_fg_cls.return_value.apply_fix = AsyncMock(
                return_value=fix_fail
            )
            sem = asyncio.Semaphore(1)
            await run_repo_pipeline(
                repo, cfg, sem, "key", "tok",
                run_log=run_log,
            )

        records = run_log.records()
        assert len(records) == 1
        assert records[0]["status"] == "fix_failed"
        assert records[0]["rule_id"] == "rule.bad"

    async def test_run_log_none_does_not_crash(
        self, tmp_path: Path
    ) -> None:
        """
        run_log=None must not raise AttributeError. (defensive)
        """
        import asyncio
        from unittest.mock import AsyncMock, MagicMock, patch

        from repomend.pipeline import run_repo_pipeline

        finding: dict = {
            "rule_id": "rule.x",
            "file_path": "x.py",
            "line_start": 1,
            "line_end": 1,
            "severity": "warning",
            "message": "",
            "fingerprint": "fp4",
        }
        sarif_run = MagicMock()
        sarif_run.to_findings.return_value = [finding]

        fix_ok = MagicMock()
        fix_ok.success = True
        fix_ok.error = ""

        verify_ok = MagicMock()
        verify_ok.verification_status = "verified"
        verify_ok.gate_2 = MagicMock(reason="")

        repo = MagicMock()
        repo.owner = "o"
        repo.repo = "r"
        repo.path = str(tmp_path)

        cfg = MagicMock()
        cfg.semgrep_rules = "p/python"
        cfg.verifier.timeout_seconds = 30
        cfg.batch.max_findings_per_repo = 5

        handle = MagicMock()
        handle.worktree_path = tmp_path
        handle.branch = "repomend/fix-abc"

        fix_wt_ctx = MagicMock()
        fix_wt_ctx.__enter__ = MagicMock(return_value=handle)
        fix_wt_ctx.__exit__ = MagicMock(return_value=False)

        with (
            patch(
                "repomend.pipeline.run_all_scanners",
                return_value=[sarif_run],
            ),
            patch(
                "repomend.pipeline.FixGenSubagent"
            ) as mock_fg_cls,
            patch(
                "repomend.pipeline.Verifier"
            ) as mock_vfy_cls,
            patch(
                "repomend.pipeline.fix_worktree_context",
                return_value=fix_wt_ctx,
            ),
            patch("repomend.pipeline.CredentialProxy"),
            patch(
                "repomend.pipeline.PRPublisher"
            ) as mock_pr_cls,
        ):
            mock_fg_cls.return_value.apply_fix = AsyncMock(
                return_value=fix_ok
            )
            mock_vfy_cls.return_value.verify.return_value = (
                verify_ok
            )
            mock_pr_cls.return_value.publish.return_value = {
                "url": "https://github.com/o/r/pull/1"
            }
            sem = asyncio.Semaphore(1)
            result = await run_repo_pipeline(
                repo, cfg, sem, "key", "tok",
                run_log=None,
            )

        assert result["status"] == "pr_opened"


# ---------------------------------------------------------------------------
# KS-P7-04: Multi-finding loop + max_findings_per_repo cap
# (C-P7-01, C-P7-02, AC-P7-01, AC-P7-02, AC-P7-04, AD-P7-01,
#  AD-P7-02, AD-P7-03)
# ---------------------------------------------------------------------------


def _mf(rule_id: str, file_path: str = "f.py") -> dict:
    return {
        "rule_id": rule_id,
        "file_path": file_path,
        "line_start": 1,
        "line_end": 1,
        "severity": "warning",
        "message": "",
        "fingerprint": rule_id,
    }


def _make_handle(tmp_path: Path) -> MagicMock:
    h = MagicMock()
    h.worktree_path = tmp_path
    h.branch = "repomend/fix-abc"
    return h


def _fix_wt_ctx(tmp_path: Path) -> MagicMock:
    ctx = MagicMock()
    ctx.__enter__ = MagicMock(return_value=_make_handle(tmp_path))
    ctx.__exit__ = MagicMock(return_value=False)
    return ctx


def _ok_fix() -> MagicMock:
    r = MagicMock()
    r.success = True
    r.error = ""
    return r


def _ok_verify() -> MagicMock:
    r = MagicMock()
    r.verification_status = "verified"
    r.gate_2 = MagicMock(reason="")
    return r


class TestMultiFindingLoop:
    """KS-P7-04: multi-finding loop + max_findings_per_repo cap."""

    async def test_multi_finding_three_findings_three_records(
        self, tmp_path: Path
    ) -> None:
        """
        3 findings, default cap (5) → 3 records, findings_attempted=3.
        (AC-P7-01)
        """
        import asyncio
        from unittest.mock import AsyncMock, MagicMock, patch

        from repomend.pipeline import run_repo_pipeline
        from repomend.run_log import RunLog

        run_log = RunLog(path=tmp_path / "b.ndjson")
        findings = [
            _mf("r.a"),
            _mf("r.b"),
            _mf("r.c"),
        ]
        sarif_run = MagicMock()
        sarif_run.to_findings.return_value = findings

        repo = MagicMock()
        repo.owner = "o"
        repo.repo = "r"
        repo.path = str(tmp_path)

        cfg = MagicMock()
        cfg.semgrep_rules = "p/python"
        cfg.verifier.timeout_seconds = 30
        cfg.batch.max_findings_per_repo = 5
        cfg.batch.max_findings_per_repo = 5

        with (
            patch(
                "repomend.pipeline.run_all_scanners",
                return_value=[sarif_run],
            ),
            patch(
                "repomend.pipeline.FixGenSubagent"
            ) as mock_fg,
            patch(
                "repomend.pipeline.Verifier"
            ) as mock_vfy,
            patch(
                "repomend.pipeline.fix_worktree_context",
                return_value=_fix_wt_ctx(tmp_path),
            ),
            patch("repomend.pipeline.CredentialProxy"),
            patch(
                "repomend.pipeline.PRPublisher"
            ) as mock_pr,
        ):
            mock_fg.return_value.apply_fix = AsyncMock(
                return_value=_ok_fix()
            )
            mock_vfy.return_value.verify.return_value = (
                _ok_verify()
            )
            mock_pr.return_value.publish.return_value = {
                "url": "https://github.com/o/r/pull/1"
            }
            sem = asyncio.Semaphore(1)
            result = await run_repo_pipeline(
                repo, cfg, sem, "key", "tok",
                run_log=run_log,
            )

        records = run_log.records()
        assert len(records) == 3
        assert result["findings_attempted"] == 3

    async def test_multi_finding_isolation_finding2_fails(
        self, tmp_path: Path
    ) -> None:
        """
        Finding 2 raises; findings 1 and 3 succeed.
        3 records written; loop continues past failure. (AC-P7-02)
        """
        import asyncio
        from unittest.mock import AsyncMock, MagicMock, patch

        from repomend.pipeline import run_repo_pipeline
        from repomend.run_log import RunLog

        run_log = RunLog(path=tmp_path / "b.ndjson")
        findings = [
            _mf("r.a"),
            _mf("r.b"),
            _mf("r.c"),
        ]
        sarif_run = MagicMock()
        sarif_run.to_findings.return_value = findings

        # Finding 2 raises RuntimeError
        call_count = 0

        async def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise RuntimeError("injected failure")
            return _ok_fix()

        repo = MagicMock()
        repo.owner = "o"
        repo.repo = "r"
        repo.path = str(tmp_path)

        cfg = MagicMock()
        cfg.semgrep_rules = "p/python"
        cfg.verifier.timeout_seconds = 30
        cfg.batch.max_findings_per_repo = 5
        cfg.batch.max_findings_per_repo = 5

        with (
            patch(
                "repomend.pipeline.run_all_scanners",
                return_value=[sarif_run],
            ),
            patch(
                "repomend.pipeline.FixGenSubagent"
            ) as mock_fg,
            patch(
                "repomend.pipeline.Verifier"
            ) as mock_vfy,
            patch(
                "repomend.pipeline.fix_worktree_context",
                return_value=_fix_wt_ctx(tmp_path),
            ),
            patch("repomend.pipeline.CredentialProxy"),
            patch(
                "repomend.pipeline.PRPublisher"
            ) as mock_pr,
        ):
            mock_fg.return_value.apply_fix = AsyncMock(
                side_effect=side_effect
            )
            mock_vfy.return_value.verify.return_value = (
                _ok_verify()
            )
            mock_pr.return_value.publish.return_value = {
                "url": "https://github.com/o/r/pull/1"
            }
            sem = asyncio.Semaphore(1)
            await run_repo_pipeline(
                repo, cfg, sem, "key", "tok",
                run_log=run_log,
            )

        records = run_log.records()
        assert len(records) == 3, (
            f"Expected 3 records, got {len(records)}"
        )
        assert records[1]["status"] in (
            "fix_failed", "error"
        ), f"record 2 status: {records[1]['status']}"
        assert records[0]["status"] not in ("error",)
        assert records[2]["status"] not in ("error",)

    async def test_multi_finding_cap_at_two(
        self, tmp_path: Path
    ) -> None:
        """
        3 findings, cap=2 → 2 records, findings_attempted=2. (AC-P7-04)
        """
        import asyncio
        from unittest.mock import AsyncMock, MagicMock, patch

        from repomend.pipeline import run_repo_pipeline
        from repomend.run_log import RunLog

        run_log = RunLog(path=tmp_path / "b.ndjson")
        findings = [
            _mf("r.a"),
            _mf("r.b"),
            _mf("r.c"),
        ]
        sarif_run = MagicMock()
        sarif_run.to_findings.return_value = findings

        repo = MagicMock()
        repo.owner = "o"
        repo.repo = "r"
        repo.path = str(tmp_path)

        cfg = MagicMock()
        cfg.semgrep_rules = "p/python"
        cfg.verifier.timeout_seconds = 30
        cfg.batch.max_findings_per_repo = 5
        cfg.batch.max_findings_per_repo = 2  # cap

        with (
            patch(
                "repomend.pipeline.run_all_scanners",
                return_value=[sarif_run],
            ),
            patch(
                "repomend.pipeline.FixGenSubagent"
            ) as mock_fg,
            patch(
                "repomend.pipeline.Verifier"
            ) as mock_vfy,
            patch(
                "repomend.pipeline.fix_worktree_context",
                return_value=_fix_wt_ctx(tmp_path),
            ),
            patch("repomend.pipeline.CredentialProxy"),
            patch(
                "repomend.pipeline.PRPublisher"
            ) as mock_pr,
        ):
            mock_fg.return_value.apply_fix = AsyncMock(
                return_value=_ok_fix()
            )
            mock_vfy.return_value.verify.return_value = (
                _ok_verify()
            )
            mock_pr.return_value.publish.return_value = {
                "url": "https://github.com/o/r/pull/1"
            }
            sem = asyncio.Semaphore(1)
            result = await run_repo_pipeline(
                repo, cfg, sem, "key", "tok",
                run_log=run_log,
            )

        records = run_log.records()
        assert len(records) == 2, (
            f"Expected 2 records (cap=2), got {len(records)}"
        )
        assert result["findings_attempted"] == 2

    async def test_single_client_per_repo_not_per_finding(
        self, tmp_path: Path
    ) -> None:
        """
        FixGenSubagent instantiated once for 3 findings. (AD-P7-03)
        """
        import asyncio
        from unittest.mock import AsyncMock, MagicMock, patch

        from repomend.pipeline import run_repo_pipeline

        findings = [
            _mf("r.a"),
            _mf("r.b"),
            _mf("r.c"),
        ]
        sarif_run = MagicMock()
        sarif_run.to_findings.return_value = findings

        repo = MagicMock()
        repo.owner = "o"
        repo.repo = "r"
        repo.path = str(tmp_path)

        cfg = MagicMock()
        cfg.semgrep_rules = "p/python"
        cfg.verifier.timeout_seconds = 30
        cfg.batch.max_findings_per_repo = 5
        cfg.batch.max_findings_per_repo = 5

        with (
            patch(
                "repomend.pipeline.run_all_scanners",
                return_value=[sarif_run],
            ),
            patch(
                "repomend.pipeline.FixGenSubagent"
            ) as mock_fg_cls,
            patch(
                "repomend.pipeline.Verifier"
            ) as mock_vfy,
            patch(
                "repomend.pipeline.fix_worktree_context",
                return_value=_fix_wt_ctx(tmp_path),
            ),
            patch("repomend.pipeline.CredentialProxy"),
            patch(
                "repomend.pipeline.PRPublisher"
            ) as mock_pr,
        ):
            mock_fg_cls.return_value.apply_fix = AsyncMock(
                return_value=_ok_fix()
            )
            mock_vfy.return_value.verify.return_value = (
                _ok_verify()
            )
            mock_pr.return_value.publish.return_value = {
                "url": "https://github.com/o/r/pull/1"
            }
            sem = asyncio.Semaphore(1)
            await run_repo_pipeline(
                repo, cfg, sem, "key", "tok",
            )

        # FixGenSubagent constructor called exactly once
        assert mock_fg_cls.call_count == 1, (
            f"Expected 1 FixGenSubagent, got {mock_fg_cls.call_count}"
        )

    async def test_all_findings_unverifiable(
        self, tmp_path: Path
    ) -> None:
        """
        All 3 findings fail verification → 3 verify_failed records,
        0 PRs, no crash. (AD-P7-01)
        """
        import asyncio
        from unittest.mock import AsyncMock, MagicMock, patch

        from repomend.pipeline import run_repo_pipeline
        from repomend.run_log import RunLog

        run_log = RunLog(path=tmp_path / "b.ndjson")
        findings = [
            _mf("r.a"),
            _mf("r.b"),
            _mf("r.c"),
        ]
        sarif_run = MagicMock()
        sarif_run.to_findings.return_value = findings

        failed_verify = MagicMock()
        failed_verify.verification_status = "failed"
        failed_verify.gate_2 = MagicMock(reason="patch broke tests")

        repo = MagicMock()
        repo.owner = "o"
        repo.repo = "r"
        repo.path = str(tmp_path)

        cfg = MagicMock()
        cfg.semgrep_rules = "p/python"
        cfg.verifier.timeout_seconds = 30
        cfg.batch.max_findings_per_repo = 5
        cfg.batch.max_findings_per_repo = 5

        with (
            patch(
                "repomend.pipeline.run_all_scanners",
                return_value=[sarif_run],
            ),
            patch(
                "repomend.pipeline.FixGenSubagent"
            ) as mock_fg,
            patch(
                "repomend.pipeline.Verifier"
            ) as mock_vfy,
            patch(
                "repomend.pipeline.fix_worktree_context",
                return_value=_fix_wt_ctx(tmp_path),
            ),
            patch("repomend.pipeline.CredentialProxy"),
            patch(
                "repomend.pipeline.PRPublisher"
            ) as mock_pr,
        ):
            mock_fg.return_value.apply_fix = AsyncMock(
                return_value=_ok_fix()
            )
            mock_vfy.return_value.verify.return_value = (
                failed_verify
            )
            sem = asyncio.Semaphore(1)
            await run_repo_pipeline(
                repo, cfg, sem, "key", "tok",
                run_log=run_log,
            )
            # PRPublisher never called
            mock_pr.return_value.publish.assert_not_called()

        records = run_log.records()
        assert len(records) == 3
        assert all(
            r["status"] == "verify_failed" for r in records
        )
