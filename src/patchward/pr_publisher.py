# KS-TRACE: AC-P5-04..AC-P5-12, C-P5-01..C-P5-09, ADR-018, ADR-019
# | assumption: publish() only called when verification_status=="verified" (C-P5-08);
# |             GITHUB_TOKEN loaded via CredentialProxy before publish() is called;
# |             httpx.Client injectable for all unit tests — no live network in tests
# | test: test_pr_publisher.py
"""
PR Publisher — Phase 5 component.

Pushes a verified fix branch to GitHub and opens a structured draft PR.
The five-section PR body template is rendered from FixResult + VerifierResult.

Trust invariants enforced here:
  C-P5-01  All PRs opened as draft=True (ADR-019).
  C-P5-03  GITHUB_TOKEN never appears in logs or run log records.
  C-P5-08  publish() raises ValueError if called on an unverified fix.
  ADR-003  Auto-merge is never triggered.
"""
from __future__ import annotations

import datetime
import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

import httpx

from patchward.credential_proxy import CredentialProxy
from patchward.worktree_common import git_push_branch

if TYPE_CHECKING:
    from patchward.config import PatchwardConfig
    from patchward.fix_gen import FixResult
    from patchward.run_log import RunLog
    from patchward.verifier import VerifierResult

logger = logging.getLogger(__name__)

_GITHUB_API_BASE = "https://api.github.com"
_GITHUB_API_VERSION = "2022-11-28"


class PRPublisher:
    """
    Pushes verified fix branches and opens draft PRs on GitHub.

    Inject ``http_client`` in tests to avoid live network calls::

        publisher = PRPublisher(cfg, proxy, http_client=mock_client)
    """

    def __init__(
        self,
        config: "PatchwardConfig",
        credential_proxy: CredentialProxy,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._cfg = config
        self._proxy = credential_proxy
        self._http = http_client or httpx.Client(timeout=30.0)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def publish(
        self,
        fix_result: "FixResult",
        verifier_result: "VerifierResult",
        finding: dict[str, Any],
        run_log: "RunLog | None" = None,
        worktree_path: "Path | None" = None,
    ) -> dict[str, Any]:
        """
        Push the fix branch and open a draft PR.  Returns the ``pr``
        sub-object dict that is appended to the run log.

        Raises:
            ValueError: ``verification_status != "verified"`` (AC-P5-08).
            subprocess.CalledProcessError: git push failed.

        # KS-TRACE: AC-P5-04, AC-P5-08, AC-P5-09, AC-P5-10, AC-P5-11, C-P5-08
        """
        if not (fix_result.success and
                verifier_result.verification_status == "verified"):
            raise ValueError(
                "PRPublisher.publish() called on unverified fix — "
                f"fix.success={fix_result.success}, "
                f"verification_status={verifier_result.verification_status!r}. "
                "C-P5-08: publisher must only be invoked on verified fixes."
            )

        branch = fix_result.branch_name
        remote_url = self._build_remote_url()

        # Push — use worktree_path when provided (branch is checked out
        # there); fall back to repo_path for callers that don't have it.
        # CalledProcessError propagates; caller logs pr_status: push_failed
        pushed_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
        push_from = (
            Path(worktree_path)
            if worktree_path is not None
            else Path(self._cfg.repo_path)
        )
        # Pre-push: branch protection check (C-P6-07, C-P6-08).
        # RuntimeError on 200 propagates to caller — not caught here.
        self._check_branch_protection(branch)
        # If we reach here, branch is unprotected (404) or
        # unknown/403 — proceed with push.
        git_push_branch(push_from, remote_url, branch)

        pr_title = self._build_pr_title(fix_result, finding)
        pr_body = self._build_pr_body(fix_result, verifier_result, finding)
        pr_data = self._create_pr(branch, pr_body, pr_title)

        pr_record: dict[str, Any] = {
            "url": pr_data.get("url", ""),
            "number": pr_data.get("number", ""),
            "status": pr_data.get("status", "opened"),
            "pushed_at": pushed_at,
        }

        if run_log is not None:
            run_log.append({"pr": pr_record})

        return pr_record

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_remote_url(self) -> str:
        """
        Construct https://x-access-token:<token>@github.com/<owner>/<repo>.git

        Token is fetched fresh from CredentialProxy on each call.
        The returned URL must NEVER be logged or stored on self.

        # KS-TRACE: ADR-018, C-P5-03
        """
        creds = self._proxy._creds  # noqa: SLF001 — intentional internal access
        token = creds.get("GITHUB_TOKEN", "")
        owner = self._cfg.github.owner
        repo = self._cfg.github.repo
        return f"https://x-access-token:{token.strip()}@github.com/{owner}/{repo}.git"

    def _github_headers(self) -> dict:
        """
        Build GitHub API request headers with Bearer token.

        Shared by _create_pr() and _check_branch_protection().
        Token is read fresh from CredentialProxy on each call.

        # KS-TRACE: C-P5-03, C-P6-07
        """
        token = self._proxy._creds.get(  # noqa: SLF001
            "GITHUB_TOKEN", ""
        )
        return {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": _GITHUB_API_VERSION,
        }

    def _check_branch_protection(
        self,
        branch_name: str,
    ) -> str:
        """
        Check GitHub branch protection status before push.

        Returns ``"unprotected"`` (404) or ``"unknown"`` (403 or
        other unexpected status).  Raises ``RuntimeError`` when
        the branch is protected (200) — caller must not catch this,
        so the push is aborted and the error propagates to the run
        log as ``pr_status: push_aborted``.

        Response codes:
          200 → protected  → RuntimeError (push aborted, C-P6-08)
          404 → unprotected → "unprotected"  (proceed)
          403 → no read permission → "unknown" + warning (proceed)
          other → "unknown" + warning  (proceed conservatively)

        # KS-TRACE: AC-P6-08, AC-P6-09, AC-P6-10, C-P6-07, C-P6-08
        """
        url = (
            f"https://api.github.com/repos/"
            f"{self._cfg.github.owner}/{self._cfg.github.repo}"
            f"/branches/{branch_name}/protection"
        )
        resp = self._http.get(url, headers=self._github_headers())

        if resp.status_code == 200:
            raise RuntimeError(
                f"branch '{branch_name}' is protected — "
                f"push aborted. Merge into a non-protected "
                f"branch or disable branch protection for "
                f"patchward fix branches."
            )
        elif resp.status_code == 404:
            return "unprotected"
        elif resp.status_code == 403:
            logger.warning(
                "Branch protection status unknown for '%s' — "
                "no read permission (403). Proceeding with push.",
                branch_name,
            )
            return "unknown"
        else:
            logger.warning(
                "Branch protection check returned unexpected "
                "status %d for '%s'. Proceeding with push.",
                resp.status_code,
                branch_name,
            )
            return "unknown"

    def _build_pr_title(

        self,
        fix_result: "FixResult",
        finding: dict[str, Any],
    ) -> str:
        rule_id = finding.get("rule_id", "unknown")
        short_desc = fix_result.description[:60].rstrip()
        return f"fix({rule_id}): {short_desc} [patchward]"

    def _build_pr_body(
        self,
        fix_result: "FixResult",
        verifier_result: "VerifierResult",
        finding: dict[str, Any],
    ) -> str:
        """
        Render the five-section PR body template (AC-P5-05, C-P5-06).

        Sections: Finding | Fix | Verification Evidence | Diff | Test Output
        """
        rule_id = finding.get("rule_id", "unknown")
        file_path = finding.get("file_path", "unknown")
        line_start = finding.get("line_start", "?")
        line_end = finding.get("line_end", "?")
        severity = finding.get("severity", "unknown")
        message = finding.get("message", "")

        vr = verifier_result
        gate_1 = vr.gate_1.status
        gate_2 = vr.gate_2.status
        gate_3 = vr.gate_3.status
        vs = vr.verification_status
        fpc = getattr(vr, "false_positive_candidate", False)

        diff_summary = (
            ", ".join(fix_result.files_modified)
            if fix_result.files_modified else "no files recorded"
        )

        risk_class = getattr(fix_result, "risk_class", "") or "unknown"

        sections = [
            "## Finding",
            f"- **Rule:** `{rule_id}`",
            f"- **File:** `{file_path}` lines {line_start}–{line_end}",
            f"- **Severity:** {severity}",
            f"- **Risk class:** {risk_class}",
            f"- **Message:** {message}",
            "",
            "## Fix",
            fix_result.description or "_No description provided._",
            f"- **Files modified:** {diff_summary}",
            "",
            "## Verification Evidence",
            f"- Gate 1 (re-scan clean): **{gate_1}**",
            f"- Gate 2 (diff in bounds): **{gate_2}**",
            f"- Gate 3 (test suite): **{gate_3}**",
            f"- **Verification status:** {vs}",
            f"- False positive candidate: {fpc}",
            "",
            "## Diff",
            "_Diff attached via fix branch — review the Files Changed tab._",
            "",
            "## Test Output",
            "_Gate 3 ran the project test suite. See Verification Evidence above._",
            "",
            "---",
            "_Opened automatically by [patchward](https://github.com). "
            "Human review required before merging._",
        ]
        return "\n".join(sections)

    def _create_pr(
        self,
        head_branch: str,
        pr_body: str,
        pr_title: str,
    ) -> dict[str, Any]:
        """
        POST to GitHub API to create the pull request.

        Returns a dict with keys: url, number, status.
        Handles: 201 (opened), 422-already-open, 403, 422-draft-unavailable.

        # KS-TRACE: AC-P5-04, AC-P5-06, AC-P5-07, AC-P5-12, C-P5-01, C-P5-09, ADR-019
        """
        owner = self._cfg.github.owner
        repo = self._cfg.github.repo
        base = self._cfg.github.base_branch

        headers = self._github_headers()
        payload: dict[str, Any] = {
            "title": pr_title,
            "head": head_branch,
            "base": base,
            "body": pr_body,
            "draft": True,               # ADR-019: always draft
            "maintainer_can_modify": True,  # AC-P5-12
        }
        url = f"{_GITHUB_API_BASE}/repos/{owner}/{repo}/pulls"

        response = self._http.post(url, headers=headers, json=payload)

        if response.status_code == 201:
            data = response.json()
            return {
                "url": data.get("html_url", ""),
                "number": data.get("number", ""),
                "status": "opened",
            }

        # 422 — inspect error to distinguish cases
        if response.status_code == 422:
            try:
                body = response.json()
                errors = body.get("errors", [])
                messages = [e.get("message", "") for e in errors]
                combined = " ".join(messages) + body.get("message", "")
            except Exception:
                combined = response.text

            # Draft unavailable (GitHub Free private repo) — retry once
            if "draft" in combined.lower():
                logger.warning(
                    "Draft PRs unavailable on this repo/plan — "
                    "retrying with draft=False (ADR-019 operational workaround)."
                )
                payload["draft"] = False
                retry = self._http.post(url, headers=headers, json=payload)
                if retry.status_code == 201:
                    data = retry.json()
                    return {
                        "url": data.get("html_url", ""),
                        "number": data.get("number", ""),
                        "status": "opened",
                    }
                return {"url": "", "number": "", "status": "api_error"}

            # PR already exists — idempotent case (AC-P5-06)
            if "already exists" in combined.lower():
                existing_url = ""
                for e in errors:
                    if "already exists" in e.get("message", "").lower():
                        existing_url = e.get("resource", "")
                return {
                    "url": existing_url,
                    "number": "",
                    "status": "already_open",
                }

            # Other 422
            return {"url": "", "number": "", "status": "api_error"}

        # 403 — forbidden (AC-P5-07)
        if response.status_code == 403:
            logger.error(
                "GitHub API 403 Forbidden — check GITHUB_TOKEN scopes and "
                "repo permissions."
            )
            return {"url": "", "number": "", "status": "api_error"}

        # Any other unexpected status
        logger.error("GitHub API unexpected status %s", response.status_code)
        return {"url": "", "number": "", "status": "api_error"}
