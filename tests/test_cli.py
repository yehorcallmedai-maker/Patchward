# KS-TRACE: BACKLOG 15b
# | assumption: no dedicated tests/test_cli.py existed before this file —
# |             confirmed via Glob (2026-07-14) and grep of
# |             runner.invoke(app, [...]) call sites (2026-07-15), which
# |             found only the `fix` command exercised, and only inside
# |             test_orchestrator.py. `version`, `scan`, `batch` had zero
# |             CliRunner coverage anywhere. This file closes that gap.
# | test: this file
"""
Dedicated CLI command tests — BACKLOG 15b.

Covers the three `patchward` commands that had no `CliRunner` coverage
before this file: `version`, `scan`, `batch`. The `fix` command already
has extensive `CliRunner` coverage in `test_orchestrator.py` (including
the [DECLINED]/[SKIP] paths, BACKLOG 13/15a) and is intentionally not
duplicated here.

Mock-patch targets mirror the established convention in
test_orchestrator.py's TestFixCommandRunLog class — patch symbols at
their `patchward.cli.<name>` import site, not their defining module.
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from typer.testing import CliRunner

from patchward.cli import app, _VERSION


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _scan_cfg(*, api_key: str = "") -> MagicMock:
    """
    Minimal config for `scan`. api_key="" by default so the
    ScannerSubagent triage branch (which needs its own separate mocking)
    is skipped — triage is a `scan`-only side path, not part of the
    core scan→store flow this file is scoping.
    """
    cfg = MagicMock()
    cfg.anthropic_api_key = api_key
    cfg.semgrep_rules = "p/python"
    cfg.repo_path = Path("/fake/repo")
    cfg.db_path = Path("/fake/runs/state.db")
    cfg.langfuse_host = "https://cloud.langfuse.com"
    cfg.tracing_enabled = False
    return cfg


def _batch_cfg(*, api_key: str = "sk-test", repos: list | None = None) -> MagicMock:
    cfg = MagicMock()
    cfg.anthropic_api_key = api_key
    cfg.repos = repos if repos is not None else [MagicMock(owner="o", repo="r")]
    cfg.batch.max_concurrent = 3
    cfg.models.fix_model = "claude-sonnet-4-6"
    return cfg


def _empty_sarif_run() -> MagicMock:
    run = MagicMock()
    run.to_findings.return_value = []
    return run


def _sarif_run_with_findings(findings: list[dict]) -> MagicMock:
    run = MagicMock()
    run.to_findings.return_value = findings
    return run


# ---------------------------------------------------------------------------
# 1. `version` — both mechanisms (subcommand + eager --version/-V flag)
# ---------------------------------------------------------------------------

def test_version_subcommand_prints_version() -> None:
    """`patchward version` exits 0 and prints 'patchward <version>'."""
    runner = CliRunner()
    result = runner.invoke(app, ["version"])

    assert result.exit_code == 0, result.output
    assert "patchward" in result.output


def test_version_flag_prints_version_and_exits() -> None:
    """`patchward --version` (eager callback) exits 0 without needing a subcommand."""
    runner = CliRunner()
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0, result.output
    assert "patchward" in result.output


def test_version_short_flag_prints_version_and_exits() -> None:
    """`patchward -V` is the documented shorthand for --version."""
    runner = CliRunner()
    result = runner.invoke(app, ["-V"])

    assert result.exit_code == 0, result.output
    assert "patchward" in result.output


def test_version_subcommand_and_flag_agree() -> None:
    """
    cli.py carries two independent version strings: the module-level
    `_VERSION` constant (used by the eager --version/-V callback) and
    `patchward.__version__` (used by the `version` subcommand). They
    happen to agree today (both "0.1.0") but nothing enforces that —
    this test exists specifically to catch future drift between the
    two, which the CliRunner output-string tests above cannot detect.
    """
    from patchward import __version__

    assert _VERSION == __version__, (
        f"cli.py's _VERSION ({_VERSION!r}) and patchward.__version__ "
        f"({__version__!r}) have drifted apart — the `version` subcommand "
        f"and the `--version`/`-V` flag will report different strings."
    )


# ---------------------------------------------------------------------------
# 2. `scan`
# ---------------------------------------------------------------------------

class TestScanCommand:
    def test_scan_no_findings_exits_0(self, tmp_path: Path) -> None:
        """Clean repo: exit 0, 'Findings: 0', finish_run(status='success')."""
        cfg = _scan_cfg()
        wt_ctx = MagicMock()
        wt_ctx.__enter__ = MagicMock(return_value=tmp_path / "scan-wt")
        wt_ctx.__exit__ = MagicMock(return_value=False)

        runner = CliRunner()
        with (
            patch("patchward.cli.load_config", return_value=cfg),
            patch("patchward.cli.CredentialProxy") as mock_proxy_cls,
            patch("patchward.cli.require_git_version"),
            patch("patchward.cli.tracing"),
            patch("patchward.cli.open_db"),
            patch("patchward.cli.get_or_create_repo", return_value=1),
            patch("patchward.cli.create_run", return_value=1),
            patch("patchward.cli.finish_run") as mock_finish,
            patch("patchward.cli.insert_finding") as mock_insert,
            patch("patchward.cli.worktree_context", return_value=wt_ctx),
            patch(
                "patchward.cli.run_all_scanners",
                return_value=[_empty_sarif_run()],
            ),
        ):
            mock_proxy_cls.return_value.load.return_value = MagicMock()
            mock_proxy_cls.return_value.load.return_value.assert_credentials_excluded = MagicMock()
            mock_proxy_cls.return_value.load.return_value.get_container_env = MagicMock(return_value={})

            result = runner.invoke(app, ["scan"])

        assert result.exit_code == 0, result.output
        assert "Findings: 0" in result.output
        mock_insert.assert_not_called()
        mock_finish.assert_called_once()
        assert mock_finish.call_args.kwargs.get("status") == "success"

    def test_scan_with_findings_stores_and_prints_each(self, tmp_path: Path) -> None:
        """Findings present: each is inserted via insert_finding and echoed."""
        cfg = _scan_cfg()
        wt_ctx = MagicMock()
        wt_ctx.__enter__ = MagicMock(return_value=tmp_path / "scan-wt")
        wt_ctx.__exit__ = MagicMock(return_value=False)

        finding = {
            "rule_id": "python.lang.security.audit.subprocess-shell-true",
            "file_path": "vulnerable.py",
            "line_start": 24,
            "line_end": 24,
            "severity": "error",
            "message": "subprocess called with shell=True",
            "fingerprint": "fp1",
        }

        runner = CliRunner()
        with (
            patch("patchward.cli.load_config", return_value=cfg),
            patch("patchward.cli.CredentialProxy") as mock_proxy_cls,
            patch("patchward.cli.require_git_version"),
            patch("patchward.cli.tracing"),
            patch("patchward.cli.open_db"),
            patch("patchward.cli.get_or_create_repo", return_value=1),
            patch("patchward.cli.create_run", return_value=1),
            patch("patchward.cli.finish_run"),
            patch("patchward.cli.insert_finding") as mock_insert,
            patch("patchward.cli.worktree_context", return_value=wt_ctx),
            patch(
                "patchward.cli.run_all_scanners",
                return_value=[_sarif_run_with_findings([finding])],
            ),
        ):
            proxy_load = mock_proxy_cls.return_value.load.return_value
            proxy_load.assert_credentials_excluded = MagicMock()
            proxy_load.get_container_env = MagicMock(return_value={})
            proxy_load.scrub = lambda x: x

            result = runner.invoke(app, ["scan"])

        assert result.exit_code == 0, result.output
        assert "Findings: 1" in result.output
        assert "subprocess-shell-true" in result.output
        mock_insert.assert_called_once()
        assert mock_insert.call_args.kwargs["fingerprint"] == "fp1"

    def test_scan_scanner_exception_exits_1_and_marks_run_error(
        self, tmp_path: Path
    ) -> None:
        """
        An unexpected exception during scanning must exit 1 and mark the
        run as failed (finish_run status='error'), not exit 0 silently.
        """
        cfg = _scan_cfg()
        wt_ctx = MagicMock()
        wt_ctx.__enter__ = MagicMock(return_value=tmp_path / "scan-wt")
        wt_ctx.__exit__ = MagicMock(return_value=False)

        runner = CliRunner()
        with (
            patch("patchward.cli.load_config", return_value=cfg),
            patch("patchward.cli.CredentialProxy") as mock_proxy_cls,
            patch("patchward.cli.require_git_version"),
            patch("patchward.cli.tracing"),
            patch("patchward.cli.open_db"),
            patch("patchward.cli.get_or_create_repo", return_value=1),
            patch("patchward.cli.create_run", return_value=1),
            patch("patchward.cli.finish_run") as mock_finish,
            patch("patchward.cli.worktree_context", return_value=wt_ctx),
            patch(
                "patchward.cli.run_all_scanners",
                side_effect=RuntimeError("semgrep crashed"),
            ),
        ):
            mock_proxy_cls.return_value.load.return_value = MagicMock()
            mock_proxy_cls.return_value.load.return_value.assert_credentials_excluded = MagicMock()
            mock_proxy_cls.return_value.load.return_value.get_container_env = MagicMock(return_value={})

            result = runner.invoke(app, ["scan"])

        assert result.exit_code == 1
        mock_finish.assert_called_once()
        assert mock_finish.call_args.kwargs.get("status") == "error"


# ---------------------------------------------------------------------------
# 3. `batch`
# ---------------------------------------------------------------------------

class TestBatchCommand:
    def test_batch_no_api_key_exits_1(self) -> None:
        cfg = _batch_cfg(api_key="")
        runner = CliRunner()
        with patch("patchward.cli.load_config", return_value=cfg):
            result = runner.invoke(app, ["batch"])

        assert result.exit_code == 1
        assert "ANTHROPIC_API_KEY" in result.output

    def test_batch_no_github_token_exits_1(self) -> None:
        cfg = _batch_cfg()
        runner = CliRunner()
        with (
            patch("patchward.cli.load_config", return_value=cfg),
            patch("patchward.cli.CredentialProxy") as mock_proxy_cls,
        ):
            mock_proxy_cls.return_value.load.return_value._creds = {}

            result = runner.invoke(app, ["batch"])

        assert result.exit_code == 1
        assert "GITHUB_TOKEN" in result.output

    def test_batch_no_repos_exits_1(self) -> None:
        cfg = _batch_cfg(repos=[])
        runner = CliRunner()
        with (
            patch("patchward.cli.load_config", return_value=cfg),
            patch("patchward.cli.CredentialProxy") as mock_proxy_cls,
        ):
            mock_proxy_cls.return_value.load.return_value._creds = {
                "GITHUB_TOKEN": "ghp_test"
            }

            result = runner.invoke(app, ["batch"])

        assert result.exit_code == 1
        assert "[[repos]]" in result.output

    def test_batch_happy_path_prints_summary_and_exits_0(
        self, tmp_path: Path
    ) -> None:
        """
        All preconditions met, run_batch returns results → exit 0,
        summary table printed with repo/status/pr_url, log path echoed.
        """
        cfg = _batch_cfg()
        log_path = tmp_path / "batch.ndjson"

        results = [
            {
                "repo": "o/r",
                "status": "ok",
                "pr_url": "https://github.com/o/r/pull/1",
                "error": None,
            }
        ]

        runner = CliRunner()
        with (
            patch("patchward.cli.load_config", return_value=cfg),
            patch("patchward.cli.CredentialProxy") as mock_proxy_cls,
            patch(
                "patchward.cli.run_batch",
                new=AsyncMock(return_value=results),
            ) as mock_run_batch,
        ):
            mock_proxy_cls.return_value.load.return_value._creds = {
                "GITHUB_TOKEN": "ghp_test"
            }

            result = runner.invoke(app, ["batch", "--log", str(log_path)])

        assert result.exit_code == 0, result.output
        assert "o/r" in result.output
        assert "ok" in result.output
        assert "pull/1" in result.output
        assert str(log_path) in result.output
        mock_run_batch.assert_called_once()

    def test_batch_any_failed_exits_1_and_reports_status(
        self, tmp_path: Path
    ) -> None:
        """
        A failed repo in the results still prints the full summary table
        (all repos, not just the failed one) but exits 1, not 0 — cli.py's
        `any_failed` flag gates the final `raise typer.Exit(code=1 if
        any_failed else 0)`. Caught on first draft: an earlier version of
        this test assumed exit 0 without reading the function's actual
        last line — corrected before it was ever run, but worth noting as
        exactly the kind of assumption this file exists to catch instead
        of make.
        """
        cfg = _batch_cfg()
        log_path = tmp_path / "batch-failed.ndjson"
        results = [
            {"repo": "o/r", "status": "fix_failed", "pr_url": None, "error": "boom"},
        ]

        runner = CliRunner()
        with (
            patch("patchward.cli.load_config", return_value=cfg),
            patch("patchward.cli.CredentialProxy") as mock_proxy_cls,
            patch(
                "patchward.cli.run_batch",
                new=AsyncMock(return_value=results),
            ),
        ):
            mock_proxy_cls.return_value.load.return_value._creds = {
                "GITHUB_TOKEN": "ghp_test"
            }

            # --log is required here, not just tidiness: RunLog() with no
            # path defaults to a real runs/session_<timestamp>.json
            # relative to cwd (see run_log.py's _default_session_path()).
            # Omitting --log in a test would write a real file into this
            # repo's actual runs/ directory as a side effect of running
            # the test suite.
            result = runner.invoke(app, ["batch", "--log", str(log_path)])

        assert result.exit_code == 1
        assert "fix_failed" in result.output
        assert "boom" in result.output
