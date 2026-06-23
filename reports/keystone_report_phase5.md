# Keystone Report — Phase 5: PR Publisher
**Project:** RepoMend — Local-First Multi-Repo Security Agent  
**Phase:** 5 (PR Publisher)  
**Session IDs:** KS-P5-01 · KS-P5-02 · KS-P5-03 · KS-P5-06  
**Report date:** 2026-06-22  
**Model:** claude-sonnet-4-6  
**Status:** PHASE 5 GATE — OPEN (pending Yehor sign-off)

---

## 1. Provenance

| Artifact | AI-generated | Human-edited | Notes |
|----------|-------------|--------------|-------|
| `src/repomend/config.py` (`GithubConfig`, `validate_github_config`) | Yes | No | `GithubConfig` Pydantic model; `[github]` toml section; missing-field exit-1 guard |
| `src/repomend/credential_proxy.py` (`GITHUB_TOKEN`) | Yes | No | Added `GITHUB_TOKEN` to `_CREDENTIAL_KEYS` frozenset |
| `src/repomend/worktree_common.py` (`git_push_branch`) | Yes | No | HTTPS + PAT push; `--force` flag; `worktree_path` as cwd |
| `src/repomend/pr_publisher.py` | Yes | No | `PRPublisher`: five-section PR body, draft invariant, 422 handling, run log record |
| `src/repomend/cli.py` (Phase 5 wiring) | Yes | No | `validate_github_config`, `PRPublisher` block after `mark_success()` |
| `src/repomend/verifier.py` (Gate 2 HEAD^ fix) | Yes | No | D-P5-01b: HEAD^ baseline when worktree is clean post-commit |
| `src/repomend/fix_gen.py` (pending_submit fix + prompt) | Yes | No | D-P5-01a: range-aware `pending_submit`; strengthened user prompt |
| `tests/test_config.py` (Phase 5 tests) | Yes | No | 4 tests: GithubConfig load, defaults, missing-owner exit, missing-repo exit |
| `tests/test_credential_proxy.py` (Phase 5 tests) | Yes | No | 3 tests: GITHUB_TOKEN in keys, scrubbed, single source of truth |
| `tests/test_fix_worktree.py` (`TestGitPushBranch`) | Yes | No | 3 tests: correct argv (with `--force`), raises on nonzero, timeout param |
| `tests/test_pr_publisher.py` | Yes | No | 8 tests: unverified guard, five-section body, draft=True, maintainer_can_modify, 422 already-open, 403 api_error, token not in run log, correct head/base/title |
| `tests/test_orchestrator.py` (`TestPRPublisherWiring`) | Yes | No | 4 tests: publisher called on verified, not called on failed, run log pr sub-object, validate_github_config called |
| `tests/test_golden_dataset.py` (`test_end_to_end_pr`) | Yes | No | AC-P5-10 integration test; skip guards for API keys + semgrep |
| `tests/conftest.py` | Yes | No | `load_dotenv()` at collection time — eliminates manual env-var setup |
| `.env.example` | Yes | No | Added `GITHUB_TOKEN` line with scope documentation |
| `docs/intake_phase5.md` | No | Yes — Yehor | Phase 5 contract; signed 2026-06-22 |
| `memory/architectural_decisions.md` | Yes | No | ADR-017, ADR-018, ADR-019 logged |
| `reports/keystone_report_phase5.md` | Yes | — | This document |

All code AI-generated. AC-P5-10 manually verified by Yehor (PR #2 on `repomend-fixture`, 2026-06-22).

---

## 2. Acceptance Criteria Status

| AC | Description | Status | Evidence |
|----|-------------|--------|----------|
| AC-P5-01 | `GITHUB_TOKEN` in `CredentialProxy._CREDENTIAL_KEYS`; `scrub()` redacts it | PASS | `test_github_token_in_credential_keys`, `test_github_token_scrubbed` in `test_credential_proxy.py` |
| AC-P5-02 | `git_push_branch(worktree_path, remote_url, branch_name)` in `worktree_common.py`; correct argv and cwd | PASS | `test_git_push_branch_correct_argv` in `test_fix_worktree.py` |
| AC-P5-03 | `git_push_branch` raises on non-zero exit | PASS | `test_git_push_branch_raises_on_nonzero` in `test_fix_worktree.py` |
| AC-P5-04 | `PRPublisher.publish()` POSTs to `/repos/{owner}/{repo}/pulls` with `draft: true`, correct `head`/`base`/`title` | PASS | `test_publish_draft_true`, `test_publish_correct_head_base_title` in `test_pr_publisher.py` |
| AC-P5-05 | PR body contains all five sections: Finding, Fix, Verification Evidence, Diff, Test Output | PASS | `test_publish_pr_body_five_sections` in `test_pr_publisher.py` |
| AC-P5-06 | 422 "already exists" → `pr_status: already_open`; no duplicate PR | PASS | `test_publish_422_already_open` in `test_pr_publisher.py` |
| AC-P5-07 | 403 → `pr_status: api_error`; exception propagated | PASS | `test_publish_403_api_error` in `test_pr_publisher.py` |
| AC-P5-08 | `PRPublisher` not invoked when `verification_status != "verified"` | PASS | `test_publisher_not_called_on_failed_verify` in `test_orchestrator.py` |
| AC-P5-09 | Run log `pr` sub-object: `url`, `number`, `status == "opened"`, `pushed_at` | PASS | `test_run_log_pr_sub_object` in `test_orchestrator.py` |
| AC-P5-10 | End-to-end: scan → fix → verify → push → draft PR opened on `repomend-fixture` | PASS | `test_end_to_end_pr` passed 2026-06-22; PR #2: https://github.com/yehorcallmedai-maker/repomend-fixture/pull/2; manually inspected by Yehor: draft=true, five sections confirmed, 1 commit, 1 file changed |
| AC-P5-11 | `GITHUB_TOKEN` absent from run log records | PASS | `test_token_not_in_run_log` in `test_pr_publisher.py` |
| AC-P5-12 | `maintainer_can_modify: true` in every PR creation request | PASS | `test_publish_maintainer_can_modify` in `test_pr_publisher.py` |
| AC-P5-13 | Missing `[github]` config field → CLI exits 1 with field name in message | PASS | `test_missing_github_owner_exits`, `test_missing_github_repo_exits` in `test_config.py` |

**All 13 ACs: PASS.**

---

## 3. Verification Summary

### Unit test suite

```
341 passed, 13 deselected
Command: uv run pytest -x -q
Coverage: 90.07% (threshold: 80%)
Date: 2026-06-22
```

### Integration test (AC-P5-10)

```
1 passed
Command: uv run pytest tests\test_golden_dataset.py
         --override-ini="addopts=" -q -k "end_to_end_pr" -s
Date: 2026-06-22
Output:
  [AC-P5-10] Verifier result: gate_1=pass gate_2=pass gate_3=pass
  [AC-P5-10] PR result: url=https://github.com/.../pull/2
                        number=2 status=opened
  *** AC-P5-10 PASS — PR opened ***
```

### Manual PR inspection (Yehor, 2026-06-22)

| Check | Result |
|-------|--------|
| PR visible on GitHub | ✅ PR #2 at https://github.com/yehorcallmedai-maker/repomend-fixture/pull/2 |
| `draft: true` | ✅ Confirmed — "This pull request is still a work in progress" badge visible |
| Five-section body | ✅ Finding / Fix / Verification Evidence / Diff / Test Output all present |
| 1 commit, 1 file changed | ✅ `vulnerable.py` — `subprocess.run(cmd, shell=True)` → `subprocess.run(shlex.split(cmd), shell=False)` |
| Auto-merge possible | ✅ Blocked — draft status prevents merge queue |
| ADR-003 (no auto-merge) | ✅ Holding |
| ADR-019 (draft-always) | ✅ Holding |
| PR closed without merging | ✅ Closed after inspection (test artifact) |

---

## 4. Defects Found During Phase 5

### D-P5-01a (MEDIUM) — `pending_submit` armed on import edit, not vulnerability edit

**Observed:** `test_end_to_end_pr` failed Gate 2 with "vulnerability lines [24, 24] were not modified." Fix-Gen added `import shlex` but never edited line 24 because `pending_submit=True` was set after the import edit, forcing `submit_fix` on the next turn before line 24 was patched.

**Root cause:** In `fix_gen.py`, `pending_submit` was armed after *any* successful `edit_file` call — including import-only edits. The model was then forced to call `submit_fix` before completing the vulnerability fix.

**Fix:** `pending_submit` is now only armed when `edit_file`'s range overlaps `[line_start, line_end]` (the vulnerability range). Import-only edits (`edit_file` at import block lines) no longer preempt the main fix turn. `write_file` (full-file rewrite) still arms `pending_submit` unconditionally.

**File:** `src/repomend/fix_gen.py` — `apply_fix()` tool-result loop.

**Also:** Strengthened the Fix-Gen system prompt and user prompt to make explicit that the vulnerability line(s) *must* be edited directly, not just surrounded by import additions.

---

### D-P5-01b (HIGH) — Gate 2 used HEAD (post-commit) instead of HEAD^ as pre-edit baseline

**Observed:** Gate 2 always returned "vulnerability lines [X, Y] were not modified" for any run where `git_commit_all` was called inside `apply_fix()`. Gate 1 and Gate 3 both passed (the fix was correct), but Gate 2's diff was empty.

**Root cause:** ADR-017 added `git_commit_all` to `apply_fix()` before returning. Gate 2's implementation used `git show HEAD:<file>` to get the pre-edit baseline. After `git_commit_all`, HEAD *is* the committed fix — so `git show HEAD:<file>` returned the fixed file, not the original. Comparing fixed-vs-fixed produces an empty diff → `touched_vuln=False`.

**Fix:** Gate 2 (`_gate_2_diff_in_bounds` in `verifier.py`) now detects whether the worktree has uncommitted changes via `git diff HEAD -- <file>`. If the output is empty (tree is clean — fix was committed), it uses `HEAD^:<file>` as the pre-edit baseline. If uncommitted changes exist, it uses `HEAD:<file>` (original behavior, compatible with existing unit tests).

**File:** `src/repomend/verifier.py` — `_gate_2_diff_in_bounds()`.

**Existing unit tests:** All 26 verifier unit tests continued to pass because mock `subprocess.run` returns non-empty content for both the `git diff HEAD` check and the `git show HEAD:` call, keeping unit tests on the `HEAD:` path.

---

### D-P5-02 (LOW) — `git push` from wrong repo root: "src refspec does not match any"

**Observed:** Push failed with "src refspec repomend/fix-p5-e2e-pr does not match any" when `PRPublisher` called `git_push_branch(Path(self._cfg.repo_path), ...)`.

**Root cause:** `self._cfg.repo_path` is the fixture repo's main working tree at `C:/Dev/Projects/repomend-fixture`. The fix branch `repomend/fix-p5-e2e-pr` was checked out in the temporary worktree at `C:\Users\...\Temp\repomend-fix-p5-e2e-pr`. Git could not resolve the local branch ref by name when pushing from the main repo.

**Fix:** Added `worktree_path: Path | None = None` parameter to `PRPublisher.publish()`. When provided, the push runs from the worktree path (where the branch is checked out and the commit lands). Falls back to `self._cfg.repo_path` for callers that do not have the worktree path, preserving backward compatibility with unit tests.

The integration test and the `fix` CLI command pass `worktree_path=handle.worktree_path`.

**File:** `src/repomend/pr_publisher.py` — `publish()` signature and `git_push_branch` call.

---

### D-P5-03 (LOW) — Remote URL used `oauth2:` prefix; fine-grained PATs require `x-access-token:`

**Observed:** Push returned HTTP 403 ("Permission denied to yehorcallmedai-maker") when using a fine-grained PAT with the URL scheme `https://oauth2:<token>@github.com/...`.

**Root cause:** The `oauth2:` URL username works for OAuth Apps and classic PATs. Fine-grained PATs (`github_pat_11...`) require `x-access-token:` as the username in the HTTPS URL.

**Fix:** `_build_remote_url()` in `pr_publisher.py` changed to `https://x-access-token:{token.strip()}@...`. Added `.strip()` as a defensive measure against newline-contaminated env vars (see D-P5-04).

**File:** `src/repomend/pr_publisher.py` — `_build_remote_url()`.

---

### D-P5-04 (LOW) — Newline in `GITHUB_TOKEN` caused git URL parse failure

**Observed:** Push failed with "url contains a newline in its password component" when the token was set via PowerShell multi-line input, embedding `\n` in the token string.

**Root cause:** PowerShell heredoc / continuation (`>>`) appended a newline to the token value when set interactively across two prompt lines.

**Fix (two-part):**
1. `_build_remote_url()` now calls `.strip()` on the token before embedding it in the URL (D-P5-03 fix above).
2. `tests/conftest.py` created with `load_dotenv()` so integration tests read from `.env` instead of requiring manual `$env:VAR = "..."` each session — eliminating the interactive-input error class.

---

## 5. Architectural Decisions This Phase

### ADR-017 — `git_commit_all` in `apply_fix()` before returning (Phase 5 pre-step)
Phase 5 requires at least one commit on the fix branch before `git push`. `git_commit_all(worktree_path, message)` was added to `worktree_common.py` and called inside `apply_fix()` after `_emit_pr_dict()` and before `return result`. Commit message format: `fix(<rule_short>): <description[:60]> [repomend/<id[:8]>]`. Status: **CONFIRMED 2026-06-22**.

### ADR-018 — HTTPS + PAT for git push; no SSH or `gh` CLI in Phase 5
`git push` uses HTTPS with `GITHUB_TOKEN` embedded in the remote URL as `https://x-access-token:<token>@github.com/<owner>/<repo>.git`. The token is never written to disk. `CredentialProxy.scrub()` covers it. SSH and `gh` CLI are deferred. Status: **CONFIRMED 2026-06-22**.

### ADR-019 — All RepoMend PRs open as `draft: true`; human must promote
Every PR opened by RepoMend sets `draft: true`. The human reviewer must explicitly mark it ready-for-review before it can be merged. Exception: if GitHub returns 422 indicating draft PRs are unavailable (GitHub Free private repos), the publisher retries once with `draft: false` and logs a warning. Status: **CONFIRMED 2026-06-22**.

---

## 6. Known Limitations (Carried Forward + New)

1. **Single-repo only.** One PR per finding per run. Multi-repo batching is Phase 6 scope.
2. **No reviewer assignment.** PRs open without `reviewers` or `assignees`. Phase 6 scope.
3. **PR template is static.** Template does not adapt to risk class. Risk-class routing (KS-P5-05) deferred to Phase 6.
4. **SSH and `gh` CLI auth not supported.** HTTPS + PAT only. Users must set `GITHUB_TOKEN`.
5. **No auto-close of fix branch on PR merge.** GitHub's "delete branch on merge" must be enabled by the user.
6. **Gate 1 is per-rule, per-file — not full-repo re-scan.** A fix that moves a vulnerability elsewhere passes Gate 1. (Carried from Phase 4 §6.)
7. **`git_commit_all` before `verify()` requires HEAD^ baseline in Gate 2.** The HEAD^-detection logic in `_gate_2_diff_in_bounds` assumes exactly one commit on the fix branch. If multiple commits are made (unusual), the pre-edit baseline is still `HEAD^` (the most recent parent), which remains correct as long as each commit represents one atomic fix. No multi-commit fix scenario is currently tested.
8. **`--force` push is always used.** `git_push_branch` uses `--force` to handle re-runs where the branch already exists on the remote. This is safe for single-use fix branches but would be unsafe on protected branches. RepoMend currently makes no check that the push target is not a protected branch.

---

## 7. Phase 5 Complete — Handoff Checklist

| Item | Status |
|------|--------|
| 13/13 ACs: PASS | ✅ |
| Unit suite: 341 passed, 0 failures, 90% coverage | ✅ |
| Integration test `test_end_to_end_pr`: PASS | ✅ |
| PR #2 on `repomend-fixture` manually inspected | ✅ |
| `draft: true` confirmed on live PR | ✅ |
| Five-section body confirmed | ✅ |
| ADR-017, ADR-018, ADR-019 logged | ✅ |
| `tests/conftest.py` with `load_dotenv()` | ✅ |
| `.env.example` updated with `GITHUB_TOKEN` | ✅ |
| All defects (D-P5-01a through D-P5-04) fixed and closed | ✅ |
| Phase 5 Keystone Report written | ✅ |

---

## 8. Accountability Statement

_I, Yehor, confirm that Phase 5 is complete as described in this report.
All 13 acceptance criteria pass. PR #2 was manually inspected on GitHub and
confirmed to meet the draft, five-section, and no-auto-merge requirements.
The four defects found during AC-P5-10 integration testing were fixed and
confirmed by re-running the test to green. I authorize Phase 5 to be marked
CLOSED and Phase 6 planning to begin._

**Signed:** Yehor  **Date:** 2026-06-22

---

_End of Phase 5 Keystone Report._
