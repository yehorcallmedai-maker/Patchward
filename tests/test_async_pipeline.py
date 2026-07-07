# KS-TRACE: AC-P6-01, AC-P6-02, AC-P6-03, C-P6-01, C-P6-02,
#           C-P6-03, ADR-020
# assumption: run_repo_pipeline skeleton returns immediately;
# real pipeline wired in KS-P6-03+; asyncio.gather with
# return_exceptions=True converts escaped exceptions to error dicts
# test: this file
from __future__ import annotations

import ast
import asyncio
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, patch

import anthropic
import pytest
from typer.testing import CliRunner

from patchward.cli import app
from patchward.config import (
    BatchConfig,
    GithubConfig,
    ModelsConfig,
    RepomendConfig,
    RepoConfig,
)
from patchward.pipeline import run_batch, run_repo_pipeline


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_cfg(
    tmp_path: Path,
    n_repos: int = 3,
    max_concurrent: int = 3,
) -> RepomendConfig:
    """Build a minimal RepomendConfig with n fake RepoConfig entries."""
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir(exist_ok=True)
    repos = [
        RepoConfig(
            path=repo_dir,
            owner="acme",
            repo=f"repo-{i}",
            base_branch="main",
        )
        for i in range(n_repos)
    ]
    cfg = RepomendConfig(
        repo_path=repo_dir,
        batch=BatchConfig(max_concurrent=max_concurrent),
        models=ModelsConfig(),
        github=GithubConfig(owner="acme", repo="repo-0"),
    )
    cfg.repos = repos
    return cfg


def _ok_dict(repo: RepoConfig) -> dict:
    return {
        "repo": f"{repo.owner}/{repo.repo}",
        "status": "ok",
        "pr_url": None,
        "error": None,
    }


# ---------------------------------------------------------------------------
# AC-P6-01 — run_batch produces N results for N repos
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_run_batch_produces_n_results(tmp_path: Path) -> None:
    """run_batch with 3 repos returns exactly 3 result dicts.
    (AC-P6-01)"""
    cfg = _make_cfg(tmp_path, n_repos=3)

    async def mock_pipeline(
        repo, cfg, sem, api_key, gh_token, run_log=None
    ):
        return _ok_dict(repo)

    with patch(
        "patchward.pipeline.run_repo_pipeline",
        side_effect=mock_pipeline,
    ):
        results = await run_batch(cfg, "key", "token")

    assert len(results) == 3
    assert all(r["status"] == "ok" for r in results)


# ---------------------------------------------------------------------------
# AC-P6-02 — semaphore bounds concurrency
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_semaphore_bounds_concurrency(tmp_path: Path) -> None:
    """With max_concurrent=2 and 4 repos, no more than 2 pipelines
    are in-flight simultaneously. (AC-P6-02)"""
    cfg = _make_cfg(tmp_path, n_repos=4, max_concurrent=2)
    max_observed = 0
    in_flight = 0

    async def counting_pipeline(repo, cfg, sem, api_key, gh_token):
        nonlocal in_flight, max_observed
        async with sem:
            in_flight += 1
            max_observed = max(max_observed, in_flight)
            await asyncio.sleep(0.01)
            in_flight -= 1
            return _ok_dict(repo)

    with patch(
        "patchward.pipeline.run_repo_pipeline",
        side_effect=counting_pipeline,
    ):
        await run_batch(cfg, "key", "token")

    assert max_observed <= 2, (
        f"Expected max in-flight <= 2, got {max_observed}"
    )


# ---------------------------------------------------------------------------
# AD-P6-01 — failure isolation: one error does not stop others
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_failure_isolation(tmp_path: Path) -> None:
    """One mock pipeline raises RuntimeError; the other two complete.
    Results has 3 entries. Failed entry has status='error'.
    Semaphore fully released. (AD-P6-01)"""
    cfg = _make_cfg(tmp_path, n_repos=3, max_concurrent=3)
    call_count = 0

    async def sometimes_raises(
        repo, cfg, sem, api_key, gh_token, run_log=None
    ):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise RuntimeError("intentional failure")
        return _ok_dict(repo)

    with patch(
        "patchward.pipeline.run_repo_pipeline",
        side_effect=sometimes_raises,
    ):
        results = await run_batch(cfg, "key", "token")

    assert len(results) == 3, (
        f"Expected 3 results, got {len(results)}"
    )
    statuses = [r["status"] for r in results]
    assert statuses.count("error") == 1
    assert statuses.count("ok") == 2

    error_entry = next(r for r in results if r["status"] == "error")
    assert "intentional failure" in (error_entry["error"] or "")


# ---------------------------------------------------------------------------
# AD-P6-02 — semaphore drain: no deadlock with max_concurrent=1
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_semaphore_drain_no_deadlock(tmp_path: Path) -> None:
    """max_concurrent=1, 5 repos, each sleeps 10ms.
    Completes within 5s timeout. (AD-P6-02)"""
    cfg = _make_cfg(tmp_path, n_repos=5, max_concurrent=1)

    async def slow_pipeline(repo, cfg, sem, api_key, gh_token):
        async with sem:
            await asyncio.sleep(0.01)
            return _ok_dict(repo)

    with patch(
        "patchward.pipeline.run_repo_pipeline",
        side_effect=slow_pipeline,
    ):
        results = await asyncio.wait_for(
            run_batch(cfg, "key", "token"),
            timeout=5.0,
        )

    assert len(results) == 5


# ---------------------------------------------------------------------------
# Invariant 2 — semaphore released on exception (async with guarantee)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_semaphore_released_on_exception(
    tmp_path: Path,
) -> None:
    """async with semaphore: releases permit even when body raises.
    Semaphore value returns to initial after gather. (§4.3 Invariant 2)
    """
    cfg = _make_cfg(tmp_path, n_repos=2, max_concurrent=2)
    semaphore = asyncio.Semaphore(2)

    async def raises_inside_sem(repo, cfg, sem, api_key, gh_token):
        async with sem:
            raise RuntimeError("body raises")

    # Call directly (bypassing run_batch mock) to test the real
    # semaphore release guarantee.
    results_raw = await asyncio.gather(
        raises_inside_sem(
            cfg.repos[0], cfg, semaphore, "k", "t"
        ),
        raises_inside_sem(
            cfg.repos[1], cfg, semaphore, "k", "t"
        ),
        return_exceptions=True,
    )

    # Both calls raised, but semaphore value should be back to 2.
    assert semaphore._value == 2, (  # noqa: SLF001
        f"Semaphore leaked: value={semaphore._value} (expected 2)"
    )
    assert all(isinstance(r, RuntimeError) for r in results_raw)


# ---------------------------------------------------------------------------
# CLI — batch exits 0 on all success
# ---------------------------------------------------------------------------

def test_batch_cli_exits_0_on_all_success(tmp_path: Path) -> None:
    """CLI batch command exits 0 when run_batch returns all-ok.
    (AC-P6-01 CLI layer)"""
    runner = CliRunner()
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    cfg_obj = _make_cfg(tmp_path, n_repos=2)
    ok_results = [_ok_dict(r) for r in cfg_obj.repos]

    with (
        patch("patchward.cli.load_config", return_value=cfg_obj),
        patch(
            "patchward.cli.CredentialProxy"
        ) as mock_proxy_cls,
        patch(
            "patchward.cli.run_batch",
            new=AsyncMock(return_value=ok_results),
        ),
    ):
        mock_proxy = mock_proxy_cls.return_value.load.return_value
        mock_proxy._creds = {"GITHUB_TOKEN": "tok"}
        cfg_obj.anthropic_api_key = "sk-ant-test"

        result = runner.invoke(app, ["batch"])

    assert result.exit_code == 0, (
        f"Expected exit 0, got {result.exit_code}.\n{result.output}"
    )


# ---------------------------------------------------------------------------
# CLI — batch exits 1 on any failure
# ---------------------------------------------------------------------------

def test_batch_cli_exits_1_on_any_failure(tmp_path: Path) -> None:
    """CLI batch command exits 1 when run_batch returns a failure
    entry. (AC-P6-01 CLI layer)"""
    runner = CliRunner()
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    cfg_obj = _make_cfg(tmp_path, n_repos=2)
    mixed_results = [
        _ok_dict(cfg_obj.repos[0]),
        {
            "repo": "acme/repo-1",
            "status": "error",
            "pr_url": None,
            "error": "scan failed",
        },
    ]

    with (
        patch("patchward.cli.load_config", return_value=cfg_obj),
        patch(
            "patchward.cli.CredentialProxy"
        ) as mock_proxy_cls,
        patch(
            "patchward.cli.run_batch",
            new=AsyncMock(return_value=mixed_results),
        ),
    ):
        mock_proxy = mock_proxy_cls.return_value.load.return_value
        mock_proxy._creds = {"GITHUB_TOKEN": "tok"}
        cfg_obj.anthropic_api_key = "sk-ant-test"

        result = runner.invoke(app, ["batch"])

    assert result.exit_code == 1, (
        f"Expected exit 1, got {result.exit_code}.\n{result.output}"
    )


# ---------------------------------------------------------------------------
# AC-P6-03 — structural: no bare subprocess.run in pipeline.py
# ---------------------------------------------------------------------------

def test_no_blocking_subprocess_in_async_pipeline() -> None:
    """AC-P6-03 structural test: pipeline.py contains no bare
    subprocess.run() calls outside asyncio.to_thread() context.

    In the KS-P6-02 skeleton, pipeline.py has no subprocess calls
    at all — this test asserts that and logs a note for KS-P6-03+
    when real calls are added.
    """
    pipeline_path = (
        Path(__file__).parent.parent
        / "src" / "patchward" / "pipeline.py"
    )
    source = pipeline_path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    bare_subprocess_calls: list[int] = []

    class _Visitor(ast.NodeVisitor):
        def visit_Call(self, node: ast.Call) -> None:  # noqa: N802
            # Detect subprocess.run(...)
            if (
                isinstance(node.func, ast.Attribute)
                and node.func.attr == "run"
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "subprocess"
            ):
                # Check if this Call is the argument to
                # asyncio.to_thread — walk parents.
                # Simple heuristic: source text of the surrounding
                # 3-line window must contain "to_thread".
                lineno = node.lineno
                lines = source.splitlines()
                window = lines[
                    max(0, lineno - 3): min(len(lines), lineno + 1)
                ]
                if not any("to_thread" in ln for ln in window):
                    bare_subprocess_calls.append(lineno)
            self.generic_visit(node)

    _Visitor().visit(tree)

    # Skeleton has no subprocess calls at all — assert clean.
    assert bare_subprocess_calls == [], (
        f"pipeline.py has bare subprocess.run() calls (not wrapped "
        f"in asyncio.to_thread) at lines: {bare_subprocess_calls}. "
        f"All subprocess calls in the async pipeline must use "
        f"asyncio.to_thread(subprocess.run, ...) — C-P6-03."
    )
    # Note: re-run this test after KS-P6-03 wires real pipeline
    # calls to confirm to_thread() wrapping is in place.


# ---------------------------------------------------------------------------
# KS-P6-03: Real pipeline path tests
# AC-P6-01, AC-P6-03, C-P6-01, C-P6-03, ADR-020, AD-P6-03
# ---------------------------------------------------------------------------

def _make_sarif_run(findings: list[dict]):
    """Return a minimal SARIF run mock with to_findings()."""
    from unittest.mock import MagicMock
    run = MagicMock()
    run.to_findings.return_value = findings
    return run


def _fake_finding() -> dict:
    return {
        "rule_id": "python.subprocess-shell-true",
        "file_path": "vulnerable.py",
        "line_start": 5,
        "line_end": 5,
        "severity": "warning",
        "message": "shell=True is unsafe",
        "fingerprint": "abc123",
    }


@pytest.mark.asyncio
async def test_run_repo_pipeline_no_findings(
    tmp_path: Path,
) -> None:
    """Scanner returns no findings → status='no_findings'.
    Semaphore released. (AC-P6-01)"""
    cfg = _make_cfg(tmp_path, n_repos=1)
    sem = asyncio.Semaphore(1)
    empty_run = _make_sarif_run([])

    with patch(
        "patchward.pipeline.run_all_scanners",
        return_value=[empty_run],
    ):
        result = await run_repo_pipeline(
            cfg.repos[0], cfg, sem, "key", "tok"
        )

    assert result["status"] == "no_findings"
    assert sem._value == 1  # noqa: SLF001 — released


@pytest.mark.asyncio
async def test_run_repo_pipeline_fix_failed(
    tmp_path: Path,
) -> None:
    """Fix-Gen returns success=False → status='fix_failed'."""
    from patchward.fix_gen import FixResult

    cfg = _make_cfg(tmp_path, n_repos=1)
    sem = asyncio.Semaphore(1)
    sarif_run = _make_sarif_run([_fake_finding()])
    failed_result = FixResult(
        model="claude-sonnet-4-6",
        finding_id="test",
        success=False,
        error="max_turns reached",
    )

    with (
        patch(
            "patchward.pipeline.run_all_scanners",
            return_value=[sarif_run],
        ),
        patch(
            "patchward.pipeline.fix_worktree_context"
        ) as mock_ctx,
        patch(
            "patchward.pipeline.FixGenSubagent"
        ) as mock_agent_cls,
    ):
        handle = mock_ctx.return_value.__enter__.return_value
        handle.worktree_path = tmp_path / "wt"
        handle.branch = "patchward/fix-test"
        mock_agent_cls.return_value.apply_fix = AsyncMock(
            return_value=failed_result
        )

        result = await run_repo_pipeline(
            cfg.repos[0], cfg, sem, "key", "tok"
        )

    assert result["status"] == "fix_failed"
    assert "max_turns" in (result["error"] or "")
    assert sem._value == 1  # noqa: SLF001


@pytest.mark.asyncio
async def test_run_repo_pipeline_verify_failed(
    tmp_path: Path,
) -> None:
    """Verifier returns status !='verified' → status='verify_failed'."""
    from unittest.mock import MagicMock
    from patchward.fix_gen import FixResult

    cfg = _make_cfg(tmp_path, n_repos=1)
    sem = asyncio.Semaphore(1)
    sarif_run = _make_sarif_run([_fake_finding()])
    good_fix = FixResult(
        model="claude-sonnet-4-6",
        finding_id="test",
        success=True,
        description="fixed",
    )
    bad_verify = MagicMock()
    bad_verify.verification_status = "failed"
    bad_verify.gate_2.reason = "vuln lines not modified"

    with (
        patch(
            "patchward.pipeline.run_all_scanners",
            return_value=[sarif_run],
        ),
        patch(
            "patchward.pipeline.fix_worktree_context"
        ) as mock_ctx,
        patch(
            "patchward.pipeline.FixGenSubagent"
        ) as mock_agent_cls,
        patch(
            "patchward.pipeline.Verifier"
        ) as mock_verifier_cls,
    ):
        handle = mock_ctx.return_value.__enter__.return_value
        handle.worktree_path = tmp_path / "wt"
        handle.branch = "patchward/fix-test"
        mock_agent_cls.return_value.apply_fix = AsyncMock(
            return_value=good_fix
        )
        mock_verifier_cls.return_value.verify.return_value = bad_verify

        result = await run_repo_pipeline(
            cfg.repos[0], cfg, sem, "key", "tok"
        )

    assert result["status"] == "verify_failed"
    assert "vuln lines" in (result["error"] or "")


@pytest.mark.asyncio
async def test_run_repo_pipeline_rate_limit(
    tmp_path: Path,
) -> None:
    """anthropic.RateLimitError → status='rate_limited'.
    Semaphore released. (AD-P6-03)"""
    cfg = _make_cfg(tmp_path, n_repos=1)
    sem = asyncio.Semaphore(1)
    sarif_run = _make_sarif_run([_fake_finding()])

    with (
        patch(
            "patchward.pipeline.run_all_scanners",
            return_value=[sarif_run],
        ),
        patch(
            "patchward.pipeline.fix_worktree_context"
        ) as mock_ctx,
        patch(
            "patchward.pipeline.FixGenSubagent"
        ) as mock_agent_cls,
    ):
        handle = mock_ctx.return_value.__enter__.return_value
        handle.worktree_path = tmp_path / "wt"
        handle.branch = "patchward/fix-test"
        # RateLimitError requires a real httpx.Response — use a
        # MagicMock with .request attribute to satisfy the SDK.
        from unittest.mock import MagicMock as _MM
        _fake_response = _MM()
        _fake_response.request = _MM()
        mock_agent_cls.return_value.apply_fix = AsyncMock(
            side_effect=anthropic.RateLimitError(
                message="rate limit",
                response=_fake_response,
                body=None,
            )
        )

        result = await run_repo_pipeline(
            cfg.repos[0], cfg, sem, "key", "tok"
        )

    assert result["status"] == "rate_limited"
    assert sem._value == 1  # noqa: SLF001 — released


@pytest.mark.asyncio
async def test_run_repo_pipeline_pr_opened(
    tmp_path: Path,
) -> None:
    """Full success path: verified fix → PR opened. (AC-P6-01)"""
    from unittest.mock import MagicMock
    from patchward.fix_gen import FixResult

    cfg = _make_cfg(tmp_path, n_repos=1)
    sem = asyncio.Semaphore(1)
    sarif_run = _make_sarif_run([_fake_finding()])
    good_fix = FixResult(
        model="claude-sonnet-4-6",
        finding_id="test",
        success=True,
        description="fixed shell=True",
        branch_name="patchward/fix-test",
    )
    good_verify = MagicMock()
    good_verify.verification_status = "verified"
    good_verify.gate_2.reason = ""
    pr_result = {"url": "https://github.com/acme/repo-0/pull/1"}

    with (
        patch(
            "patchward.pipeline.run_all_scanners",
            return_value=[sarif_run],
        ),
        patch(
            "patchward.pipeline.fix_worktree_context"
        ) as mock_ctx,
        patch(
            "patchward.pipeline.FixGenSubagent"
        ) as mock_agent_cls,
        patch(
            "patchward.pipeline.Verifier"
        ) as mock_verifier_cls,
        patch(
            "patchward.pipeline.CredentialProxy"
        ) as mock_proxy_cls,
        patch(
            "patchward.pipeline.PRPublisher"
        ) as mock_pub_cls,
    ):
        handle = mock_ctx.return_value.__enter__.return_value
        handle.worktree_path = tmp_path / "wt"
        handle.branch = "patchward/fix-test"
        mock_agent_cls.return_value.apply_fix = AsyncMock(
            return_value=good_fix
        )
        mock_verifier_cls.return_value.verify.return_value = good_verify
        mock_proxy_cls.return_value.load.return_value = MagicMock()
        mock_pub_cls.return_value.publish.return_

# ── KS-P6-05: scanner uses config.models.scanner_model ───────────────────

def test_scanner_subagent_uses_config_scanner_model():
    """
    ScannerSubagent with config param uses config.models.scanner_model
    instead of SCANNER_MODEL constant (AC-P6-05).
    """
    from unittest.mock import MagicMock
    from patchward.subagent import ScannerSubagent, SCANNER_MODEL

    cfg = MagicMock()
    cfg.models.scanner_model = "claude-custom-model"

    agent = ScannerSubagent(client=MagicMock(), config=cfg)
    assert agent._model == "claude-custom-model"
    assert agent._model != SCANNER_MODEL


def test_scanner_subagent_no_config_uses_constant():
    """
    ScannerSubagent without config falls back to SCANNER_MODEL constant.
    """
    from unittest.mock import MagicMock
    from patchward.subagent import ScannerSubagent, SCANNER_MODEL

    agent = ScannerSubagent(client=MagicMock())
    assert agent._model == SCANNER_MODEL


def test_batch_cli_model_flag_overrides_config(monkeypatch):
    """
    ``patchward batch --model <x>`` sets cfg.models.fix_model = x
    before run_batch is called (AC-P6-05).
    """
    import asyncio
    from typer.testing import CliRunner
    from unittest.mock import patch, MagicMock
    from patchward.cli import app

    runner = CliRunner()

    captured_model: list[str] = []

    async def fake_run_batch(  # noqa: ANN001
        cfg, api_key, token, run_log=None
    ):
        captured_model.append(cfg.models.fix_model)
        return []

    mock_cfg = MagicMock()
    mock_cfg.anthropic_api_key = "key"
    mock_cfg.repos = [MagicMock()]
    mock_cfg.batch.max_concurrent = 1
    mock_cfg.models.fix_model = "claude-sonnet-4-6"  # default

    with (
        patch("patchward.cli.load_config", return_value=mock_cfg),
        patch(
            "patchward.cli.CredentialProxy"
        ) as mock_proxy_cls,
        patch("patchward.cli.run_batch", side_effect=fake_run_batch),
    ):
        mock_proxy = MagicMock()
        mock_proxy._creds = {"GITHUB_TOKEN": "tok"}
        mock_proxy_cls.return_value.load.return_value = mock_proxy

        result = runner.invoke(
            app,
            ["batch", "--model", "claude-haiku-4-5-20251001"],
        )

    assert captured_model == ["claude-haiku-4-5-20251001"], (
        f"Expected flag to override config model; got {captured_model}"
    )


# ── KS-P6-07: _with_retry exponential backoff ─────────────────────────────

async def test_with_retry_succeeds_on_first_attempt():
    """_with_retry returns immediately when coro_fn succeeds."""
    from unittest.mock import AsyncMock
    from patchward.pipeline import _with_retry

    coro_fn = AsyncMock(return_value="ok")
    result = await _with_retry(coro_fn, max_retries=3, base_delay=0.0)
    assert result == "ok"
    assert coro_fn.call_count == 1


async def test_with_retry_retries_on_rate_limit():
    """
    _with_retry retries on RateLimitError and eventually returns
    the successful result. asyncio.sleep called with backoff delays.
    """
    from unittest.mock import AsyncMock, MagicMock, patch
    import anthropic
    from patchward.pipeline import _with_retry

    fake_response = MagicMock()
    fake_response.request = MagicMock()
    exc = anthropic.RateLimitError(
        message="rate limited", response=fake_response, body={}
    )

    call_count = 0

    async def coro_fn():
        nonlocal call_count
        call_count += 1
        if call_count <= 2:
            raise exc
        return "ok"

    sleep_calls: list[float] = []

    async def fake_sleep(delay):
        sleep_calls.append(delay)

    with patch("patchward.pipeline.asyncio.sleep", side_effect=fake_sleep):
        result = await _with_retry(
            coro_fn, max_retries=3, base_delay=1.0
        )

    assert result == "ok"
    assert call_count == 3
    assert sleep_calls == [1.0, 2.0]


async def test_with_retry_raises_after_max_retries():
    """
    _with_retry raises RateLimitError after max_retries+1 attempts.
    """
    from unittest.mock import MagicMock, patch
    import anthropic
    import pytest
    from patchward.pipeline import _with_retry

    fake_response = MagicMock()
    fake_response.request = MagicMock()
    exc = anthropic.RateLimitError(
        message="rate limited", response=fake_response, body={}
    )

    call_count = 0

    async def coro_fn():
        nonlocal call_count
        call_count += 1
        raise exc

    async def fake_sleep(_):
        pass

    with patch("patchward.pipeline.asyncio.sleep", side_effect=fake_sleep):
        with pytest.raises(anthropic.RateLimitError):
            await _with_retry(coro_fn, max_retries=2, base_delay=0.0)

    assert call_count == 3  # initial + 2 retries


async def test_run_repo_pipeline_rate_limited_after_retries(
    monkeypatch,
):
    """
    When apply_fix always raises RateLimitError (retries exhausted),
    run_repo_pipeline returns status='rate_limited' and semaphore
    is released.  (AD-P6-03 full path)
    """
    import asyncio
    import anthropic
    from unittest.mock import MagicMock, patch
    from patchward.pipeline import run_repo_pipeline

    fake_response = MagicMock()
    fake_response.request = MagicMock()
    rate_exc = anthropic.RateLimitError(
        message="429", response=fake_response, body={}
    )

    repo = MagicMock()
    repo.owner = "acme"
    repo.repo = "widget"
    repo.path = "/tmp/widget"

    cfg = MagicMock()
    cfg.semgrep_rules = "p/python"
    cfg.verifier.timeout_seconds = 30
    cfg.anthropic_api_key = "key"
    cfg.models.fix_model = "claude-sonnet-4-6"
    cfg.fix_gen.max_turns = 3
    cfg.batch.max_findings_per_repo = 5

    semaphore = asyncio.Semaphore(1)

    mock_sarif = MagicMock()
    mock_sarif.to_findings.return_value = [{
        "rule_id": "S001",
        "file_path": "foo.py",
        "line_start": 1,
        "line_end": 2,
        "severity": "warning",
        "message": "test",
        "fingerprint": "fp1",
    }]

    async def fake_sleep(_):
        pass

    with (
        patch(
            "patchward.pipeline.run_all_scanners",
            return_value=[mock_sarif],
        ),
        patch(
            "patchward.pipeline.fix_worktree_context"
        ) as mock_ctx,
        patch(
            "patchward.pipeline.asyncio.sleep",
            side_effect=fake_sleep,
        ),
    ):
        handle = MagicMock()
        handle.__enter__ = MagicMock(return_value=handle)
        handle.__exit__ = MagicMock(return_value=False)
        handle.worktree_path = MagicMock()
        handle.branch = "patchward/fix-S001"
        mock_ctx.return_value = handle

        with patch(
            "patchward.pipeline.FixGenSubagent"
        ) as MockAgent:
            MockAgent.return_value.apply_fix = AsyncMock(
                side_effect=rate_exc
            )
            result = await run_repo_pipeline(
                repo, cfg, semaphore, "key", "tok"
            )

    assert result["status"] == "rate_limited"
    assert result["repo"] == "acme/widget"
    # Semaphore released — can acquire immediately
    assert semaphore._value == 1
