# KS-TRACE: AC-P5-04..AC-P5-12, ADR-019
# | assumption: httpx.Client injected — no live network; GITHUB_TOKEN monkeypatched
# | test: this file
"""
PRPublisher unit tests — KS-P5-02 STEP 4.

All tests inject a mock httpx.Client so no real HTTP calls are made.
git_push_branch is patched to avoid real git calls.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import httpx
import pytest

from patchward.config import GithubConfig, PatchwardConfig
from patchward.credential_proxy import CredentialProxy
from patchward.fix_gen import FixResult
from patchward.pr_publisher import PRPublisher
from patchward.verifier import GateResult, VerifierResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_config(tmp_path: Path) -> PatchwardConfig:
    repo = tmp_path / "repo"
    repo.mkdir(exist_ok=True)
    return PatchwardConfig(
        repo_path=repo,
        github=GithubConfig(owner="acme", repo="my-app", base_branch="main"),
    )


def _make_proxy(token: str = "ghp_fake_token_abc123") -> CredentialProxy:
    proxy = CredentialProxy()
    proxy._creds["GITHUB_TOKEN"] = token
    return proxy


def _make_verified_fix() -> FixResult:
    return FixResult(
        model="claude-sonnet-4-6",
        finding_id="test-abc12345",
        success=True,
        description="Replace subprocess shell=True with explicit args list",
        files_modified=["vulnerable.py"],
        branch_name="patchward/fix-subprocess-abc12345",
    )


def _make_verifier_result(status: str = "verified") -> VerifierResult:
    from patchward.verifier import PASS, FAIL
    vr = VerifierResult()
    if status == "verified":
        vr.gate_1 = GateResult(PASS, "")
        vr.gate_2 = GateResult(PASS, "")
        vr.gate_3 = GateResult(PASS, "")
    else:
        vr.gate_1 = GateResult(FAIL, "rule still fires")
        vr.gate_2 = GateResult(PASS, "")
        vr.gate_3 = GateResult(PASS, "")
    return vr


def _make_finding() -> dict[str, Any]:
    return {
        "rule_id": "python.lang.security.audit.subprocess-shell-true",
        "file_path": "vulnerable.py",
        "line_start": 24,
        "line_end": 24,
        "severity": "warning",
        "message": "subprocess called with shell=True",
    }


def _mock_201_response(pr_number: int = 42) -> MagicMock:
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = 201
    resp.json.return_value = {
        "html_url": f"https://github.com/acme/my-app/pull/{pr_number}",
        "number": pr_number,
    }
    return resp


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestPRPublisher:

    @patch("patchward.pr_publisher.git_push_branch")
    def test_publish_raises_if_not_verified(
        self, mock_push: MagicMock, tmp_path: Path
    ) -> None:
        """publish() raises ValueError when verification_status != verified (AC-P5-08)."""
        cfg = _make_config(tmp_path)
        proxy = _make_proxy()
        publisher = PRPublisher(cfg, proxy, http_client=MagicMock())
        fix = FixResult(model="claude-sonnet-4-6", finding_id="test-abc", success=True, branch_name="patchward/fix-abc")
        vr = _make_verifier_result("failed")
        with pytest.raises(ValueError, match="unverified fix"):
            publisher.publish(fix, vr, _make_finding())
        mock_push.assert_not_called()

    def test_build_pr_body_has_five_sections(self, tmp_path: Path) -> None:
        """_build_pr_body() renders all five ## sections (AC-P5-05, C-P5-06)."""
        cfg = _make_config(tmp_path)
        proxy = _make_proxy()
        publisher = PRPublisher(cfg, proxy, http_client=MagicMock())
        body = publisher._build_pr_body(
            _make_verified_fix(), _make_verifier_result(), _make_finding()
        )
        for section in ("## Finding", "## Fix", "## Verification Evidence",
                        "## Diff", "## Test Output"):
            assert section in body, f"Missing section: {section}"

    def test_build_pr_body_shows_risk_class(self, tmp_path: Path) -> None:
        """_build_pr_body() surfaces FixResult.risk_class in the Finding
        section (BACKLOG 7b) — the value is already computed by fix_gen.py
        (AC-P3-08) but was never displayed to a human reviewer before."""
        cfg = _make_config(tmp_path)
        proxy = _make_proxy()
        publisher = PRPublisher(cfg, proxy, http_client=MagicMock())
        fix = _make_verified_fix()
        fix.risk_class = "HIGH"
        body = publisher._build_pr_body(
            fix, _make_verifier_result(), _make_finding()
        )
        assert "**Risk class:** HIGH" in body

    def test_build_pr_body_risk_class_falls_back_to_unknown(
        self, tmp_path: Path
    ) -> None:
        """An unset (empty-string default) risk_class renders as
        'unknown' rather than a blank field."""
        cfg = _make_config(tmp_path)
        proxy = _make_proxy()
        publisher = PRPublisher(cfg, proxy, http_client=MagicMock())
        fix = _make_verified_fix()
        assert fix.risk_class == ""
        body = publisher._build_pr_body(
            fix, _make_verifier_result(), _make_finding()
        )
        assert "**Risk class:** unknown" in body

    @patch("patchward.pr_publisher.git_push_branch")
    def test_create_pr_draft_true(
        self, mock_push: MagicMock, tmp_path: Path
    ) -> None:
        """PR creation request body must contain draft=True (ADR-019, C-P5-01)."""
        cfg = _make_config(tmp_path)
        proxy = _make_proxy()
        mock_http = MagicMock(spec=httpx.Client)
        mock_http.post.return_value = _mock_201_response()
        publisher = PRPublisher(cfg, proxy, http_client=mock_http)

        publisher.publish(_make_verified_fix(), _make_verifier_result(), _make_finding())

        call_kwargs = mock_http.post.call_args.kwargs
        assert call_kwargs["json"]["draft"] is True, (
            "draft must be True — ADR-019 safety invariant"
        )

    @patch("patchward.pr_publisher.git_push_branch")
    def test_create_pr_maintainer_can_modify(
        self, mock_push: MagicMock, tmp_path: Path
    ) -> None:
        """PR request body must set maintainer_can_modify=True (AC-P5-12)."""
        cfg = _make_config(tmp_path)
        proxy = _make_proxy()
        mock_http = MagicMock(spec=httpx.Client)
        mock_http.post.return_value = _mock_201_response()
        publisher = PRPublisher(cfg, proxy, http_client=mock_http)

        publisher.publish(_make_verified_fix(), _make_verifier_result(), _make_finding())

        call_kwargs = mock_http.post.call_args.kwargs
        assert call_kwargs["json"]["maintainer_can_modify"] is True

    @patch("patchward.pr_publisher.git_push_branch")
    def test_create_pr_already_open_422(
        self, mock_push: MagicMock, tmp_path: Path
    ) -> None:
        """422 with already-exists message → pr_status: already_open, no duplicate POST (AC-P5-06)."""
        cfg = _make_config(tmp_path)
        proxy = _make_proxy()
        mock_http = MagicMock(spec=httpx.Client)
        error_resp = MagicMock(spec=httpx.Response)
        error_resp.status_code = 422
        error_resp.json.return_value = {
            "message": "Validation Failed",
            "errors": [{"message": "A pull request already exists for acme:patchward/fix-abc"}],
        }
        error_resp.text = "Validation Failed"
        mock_http.post.return_value = error_resp
        publisher = PRPublisher(cfg, proxy, http_client=mock_http)

        result = publisher._create_pr("patchward/fix-abc", "body", "title")

        assert result["status"] == "already_open", f"Expected already_open, got {result}"
        assert mock_http.post.call_count == 1, "Must not open duplicate PR"

    @patch("patchward.pr_publisher.git_push_branch")
    def test_create_pr_403_api_error(
        self, mock_push: MagicMock, tmp_path: Path
    ) -> None:
        """403 response → pr_status: api_error in returned dict (AC-P5-07)."""
        cfg = _make_config(tmp_path)
        proxy = _make_proxy()
        mock_http = MagicMock(spec=httpx.Client)
        forbidden = MagicMock(spec=httpx.Response)
        forbidden.status_code = 403
        mock_http.post.return_value = forbidden
        publisher = PRPublisher(cfg, proxy, http_client=mock_http)

        result = publisher._create_pr("fix-branch", "body", "title")

        assert result["status"] == "api_error"

    @patch("patchward.pr_publisher.git_push_branch")
    def test_github_token_not_in_run_log(
        self, mock_push: MagicMock, tmp_path: Path
    ) -> None:
        """GITHUB_TOKEN value must not appear in run log record repr (AC-P5-11)."""
        from patchward.run_log import RunLog
        cfg = _make_config(tmp_path)
        secret_token = "ghp_SUPERSECRET99999"
        proxy = _make_proxy(secret_token)
        mock_http = MagicMock(spec=httpx.Client)
        mock_http.post.return_value = _mock_201_response()
        publisher = PRPublisher(cfg, proxy, http_client=mock_http)

        log_path = tmp_path / "run.ndjson"
        run_log = RunLog(log_path)

        publisher.publish(
            _make_verified_fix(), _make_verifier_result(), _make_finding(), run_log
        )

        records = run_log.records()
        log_repr = repr(records)
        assert secret_token not in log_repr, (
            "GITHUB_TOKEN must not appear in run log record"
        )

    @patch("patchward.pr_publisher.git_push_branch")
    def test_correct_head_base_title_in_request(
        self, mock_push: MagicMock, tmp_path: Path
    ) -> None:
        """PR request: head=fix_branch, base=cfg.github.base_branch, title contains rule_id."""
        cfg = _make_config(tmp_path)
        proxy = _make_proxy()
        mock_http = MagicMock(spec=httpx.Client)
        mock_http.post.return_value = _mock_201_response()
        publisher = PRPublisher(cfg, proxy, http_client=mock_http)
        fix = _make_verified_fix()

        publisher.publish(fix, _make_verifier_result(), _make_finding())

        body = mock_http.post.call_args.kwargs["json"]
        assert body["head"] == fix.branch_name
        assert body["base"] == "main"
        assert "subprocess-shell-true" in body["title"]


# ---------------------------------------------------------------------------
# KS-P6-04 — Branch protection check (AC-P6-08, AC-P6-09, AC-P6-10,
#             C-P6-07, C-P6-08)
# ---------------------------------------------------------------------------

def _make_publisher_with_mock_http(mock_http, tmp_path):
    """Build a PRPublisher with injectable mock HTTP client."""
    from patchward.config import PatchwardConfig, GithubConfig
    from patchward.credential_proxy import CredentialProxy
    from patchward.pr_publisher import PRPublisher
    from unittest.mock import MagicMock

    repo_dir = tmp_path / "repo"
    repo_dir.mkdir(exist_ok=True)
    cfg = PatchwardConfig(
        repo_path=repo_dir,
        github=GithubConfig(
            owner="acme", repo="my-app", base_branch="main"
        ),
    )
    proxy = MagicMock(spec=CredentialProxy)
    proxy._creds = {"GITHUB_TOKEN": "tok"}
    return PRPublisher(config=cfg, credential_proxy=proxy,
                       http_client=mock_http)


def test_check_branch_protection_200_raises(tmp_path) -> None:
    """200 → RuntimeError with 'protected' in message. (AC-P6-08)"""
    from unittest.mock import MagicMock
    mock_http = MagicMock()
    mock_http.get.return_value.status_code = 200

    publisher = _make_publisher_with_mock_http(mock_http, tmp_path)
    with pytest.raises(RuntimeError, match="protected"):
        publisher._check_branch_protection("main")


def test_check_branch_protection_404_returns_unprotected(
    tmp_path,
) -> None:
    """404 → returns 'unprotected', no exception. (C-P6-07)"""
    from unittest.mock import MagicMock
    mock_http = MagicMock()
    mock_http.get.return_value.status_code = 404

    publisher = _make_publisher_with_mock_http(mock_http, tmp_path)
    result = publisher._check_branch_protection("patchward/fix-abc")
    assert result == "unprotected"


def test_check_branch_protection_403_logs_warning(
    tmp_path, caplog
) -> None:
    """403 → returns 'unknown' + logs warning. (AC-P6-09)"""
    import logging
    from unittest.mock import MagicMock
    mock_http = MagicMock()
    mock_http.get.return_value.status_code = 403

    publisher = _make_publisher_with_mock_http(mock_http, tmp_path)
    with caplog.at_level(logging.WARNING, logger="patchward.pr_publisher"):
        result = publisher._check_branch_protection("patchward/fix-abc")

    assert result == "unknown"
    assert any("403" in rec.message for rec in caplog.records), (
        f"Expected '403' in a warning log record. Got: "
        f"{[r.message for r in caplog.records]}"
    )


def test_publish_aborts_push_on_protected_branch(tmp_path) -> None:
    """_check_branch_protection raises → git_push_branch NOT called.
    (AC-P6-10)"""
    from unittest.mock import MagicMock, patch
    mock_http = MagicMock()
    publisher = _make_publisher_with_mock_http(mock_http, tmp_path)

    with (
        patch.object(
            publisher,
            "_check_branch_protection",
            side_effect=RuntimeError("branch 'main' is protected"),
        ),
        patch(
            "patchward.pr_publisher.git_push_branch"
        ) as mock_push,
    ):
        with pytest.raises(RuntimeError, match="protected"):
            from patchward.fix_gen import FixResult
            from unittest.mock import MagicMock as MM
            fix = FixResult(
                model="claude-sonnet-4-6",
                finding_id="t",
                success=True,
                branch_name="main",
            )
            vr = MM()
            vr.verification_status = "verified"
            vr.gate_1.status = "pass"
            vr.gate_2.status = "pass"
            vr.gate_3.status = "pass"
            vr.false_positive_candidate = False
            publisher.publish(
                fix_result=fix,
                verifier_result=vr,
                finding={
                    "rule_id": "r", "file_path": "f.py",
                    "line_start": 1, "line_end": 1,
                    "severity": "warning", "message": "m",
                },
            )

    assert mock_push.call_count == 0, (
        "git_push_branch must NOT be called when branch is protected"
    )


def test_publish_proceeds_on_unprotected_branch(tmp_path) -> None:
    """_check_branch_protection returns 'unprotected' →
    git_push_branch IS called. (C-P6-07)"""
    from unittest.mock import MagicMock, patch
    mock_http = MagicMock()
    publisher = _make_publisher_with_mock_http(mock_http, tmp_path)
    mock_http.post.return_value.status_code = 201
    mock_http.post.return_value.json.return_value = {
        "html_url": "https://github.com/acme/my-app/pull/5",
        "number": 5,
    }

    with (
        patch.object(
            publisher,
            "_check_branch_protection",
            return_value="unprotected",
        ),
        patch(
            "patchward.pr_publisher.git_push_branch"
        ) as mock_push,
    ):
        from patchward.fix_gen import FixResult
        from unittest.mock import MagicMock as MM
        fix = FixResult(
            model="claude-sonnet-4-6",
            finding_id="t",
            success=True,
            branch_name="patchward/fix-abc",
            description="fixed",
        )
        vr = MM()
        vr.verification_status = "verified"
        vr.gate_1.status = "pass"
        vr.gate_2.status = "pass"
        vr.gate_3.status = "pass"
        vr.false_positive_candidate = False
        publisher.publish(
            fix_result=fix,
            verifier_result=vr,
            finding={
                "rule_id": "r", "file_path": "f.py",
                "line_start": 1, "line_end": 1,
                "severity": "warning", "message": "m",
            },
        )

    assert mock_push.call_count == 1, (
        "git_push_branch must be called on unprotected branch"
    )


def test_publish_proceeds_on_unknown_protection(tmp_path) -> None:
    """_check_branch_protection returns 'unknown' (403) →
    git_push_branch IS called. (AC-P6-09)"""
    from unittest.mock import MagicMock, patch
    mock_http = MagicMock()
    publisher = _make_publisher_with_mock_http(mock_http, tmp_path)
    mock_http.post.return_value.status_code = 201
    mock_http.post.return_value.json.return_value = {
        "html_url": "https://github.com/acme/my-app/pull/6",
        "number": 6,
    }

    with (
        patch.object(
            publisher,
            "_check_branch_protection",
            return_value="unknown",
        ),
        patch(
            "patchward.pr_publisher.git_push_branch"
        ) as mock_push,
    ):
        from patchward.fix_gen import FixResult
        from unittest.mock import MagicMock as MM
        fix = FixResult(
            model="claude-sonnet-4-6",
            finding_id="t",
            success=True,
            branch_name="patchward/fix-abc",
            description="fixed",
        )
        vr = MM()
        vr.verification_status = "verified"
        vr.gate_1.status = "pass"
        vr.gate_2.status = "pass"
        vr.gate_3.status = "pass"
        vr.false_positive_candidate = False
        publisher.publish(
            fix_result=fix,
            verifier_result=vr,
            finding={
                "rule_id": "r", "file_path": "f.py",
                "line_start": 1, "line_end": 1,
                "severity": "warning", "message": "m",
            },
        )

    assert mock_push.call_count == 1, (
        "git_push_branch must be called when protection is unknown"
    )
