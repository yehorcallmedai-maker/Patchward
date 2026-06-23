# Phase 5 INTAKE Contract — KS-P5-01
**Date:** 2026-06-22
**Status:** SIGNED 2026-06-22

---

## ADR-009 Pre-Step — GitHub API Mechanics Ground Truth

Per ADR-009, concrete mechanics are confirmed before this contract is written.
All six questions from the Phase 5 research pass are answered and locked.

### Q1 — Endpoint and required fields for PR creation

**Endpoint:** `POST https://api.github.com/repos/{owner}/{repo}/pulls`

Required headers:
```
Accept: application/vnd.github+json
Authorization: Bearer <TOKEN>
X-GitHub-Api-Version: 2022-11-28
```

Required body fields:

| Field | Type | Description |
|-------|------|-------------|
| `head` | string | Source branch. Same-repo: just `branch-name`. Cross-repo / fork: `username:branch-name`. |
| `base` | string | Target branch to merge into (e.g. `main`). Must exist on the repo. |
| `title` | string | PR title. Required unless `issue` is provided. |

Optional body fields used by RepoMend:

| Field | Type | Description |
|-------|------|-------------|
| `body` | string | PR description — RepoMend structured template goes here. |
| `draft` | boolean | Open as draft PR (default: `false`). |
| `maintainer_can_modify` | boolean | Allow repo maintainers to push to the head branch. |

**Success response:** `201 Created` — body contains PR number, URL, and full PR object.

**Error responses:**

| Code | When it fires |
|------|--------------|
| `403 Forbidden` | Token lacks permission on this repo. |
| `422 Unprocessable Entity` | Validation failed — head branch not pushed to remote, base branch does not exist, PR already open for this head→base pair, or head and base are the same branch. The `errors[].code` field in the body identifies which condition triggered. |

The 422 is the primary runtime error to handle. The `errors[].message` field gives
the human-readable reason (e.g. `"A pull request already exists for..."`).

### Q2 — Head branch must exist on remote before PR API call

**Confirmed: yes.** The head branch must be pushed to the remote before
`POST .../pulls` is called. If the branch exists only locally, the API returns
`422` with `errors[].code: "invalid"` and a message indicating the branch was
not found. The push step (`git push origin <branch>`) is therefore a hard
prerequisite of the PR creation call, not an optional step.

Implication for Phase 5 sequencing:
```
git commit (ADR-017, done in pre-step)
  → git push origin <fix-branch>
    → POST /repos/{owner}/{repo}/pulls
```
All three steps are in-sequence. Any failure in step 1 or 2 aborts the PR step.

### Q3 — Token scopes required

**Classic PAT:**
- Private repos: `repo` scope (full control of private and public repos).
- Public repos only: `public_repo` scope is sufficient.
- Recommendation: require `repo` scope — RepoMend targets arbitrary repos and
  cannot know at runtime whether a given repo is private.

**Fine-grained PAT (preferred for new setups):**
- "Pull requests" repository permission → **Write**.
- "Contents" repository permission → **Write** (required for `git push`).
- Fine-grained PATs are scoped to specific repos; more secure than classic `repo`.

RepoMend will accept either. The config key is `GITHUB_TOKEN`; the code does
not inspect the token type. The user is responsible for granting the correct
scopes when generating the token.

### Q4 — Draft PR support

Draft PRs are supported via `"draft": true` in the request body. No special
header or API version is required beyond the standard `application/vnd.github+json`.

**Plan availability:**
- Public repos: available on all GitHub plans (Free, Pro, Team, Enterprise).
- Private repos: requires GitHub Team or GitHub Enterprise Cloud. GitHub Free
  private repos do NOT support draft PRs.

RepoMend defaults to `draft: true` for all automatically generated PRs. This
is a safety invariant: the human reviewer must explicitly mark the PR ready for
review before it can be merged. The config can override to `draft: false` for
users on plans that require it (or for public repos on any plan).

### Q5 — Error shapes for 409 / 422

GitHub's PR API does not return `409 Conflict`. The conflict case (PR already
exists for the same head→base pair) is surfaced as `422 Unprocessable Entity`
with a message like `"A pull request already exists for owner:branch"`.

Canonical 422 cases RepoMend must handle:

| Trigger | `errors[].message` (approximate) | Handling |
|---------|----------------------------------|----------|
| Head branch not pushed | `"Validation Failed"` with field `head` | Ensure `git push` succeeds before API call |
| PR already open | `"A pull request already exists for..."` | Log as `pr_status: already_open`; surface existing PR URL from error body; do not open duplicate |
| Head == base | `"A pull request already exists for..."` or validation error | Pre-check: abort if `fix_branch == base_branch` |
| Base branch not found | `"Invalid value for 'base'"` | Pre-check: confirm base branch exists in repo config |

### Q6 — Push credentials model

**Current architecture (from ADR Phase 2):** Credentials live outside the
sandbox boundary. `CredentialProxy` currently manages three keys:
`ANTHROPIC_API_KEY`, `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`.

**Phase 5 requirement:** `git push` to GitHub requires authentication. The
local CLI context has three authentication paths:

| Method | How it works | Phase 5 verdict |
|--------|-------------|-----------------|
| HTTPS + PAT (env var) | `git push https://oauth2:<TOKEN>@github.com/<owner>/<repo>.git <branch>` — token embedded in URL or via `GIT_ASKPASS`. | **Selected.** No new subprocess dependency. Token already loaded from env via CredentialProxy pattern. Avoids adding `gh` or SSH key management to the Phase 5 scope. |
| SSH key | Requires `~/.ssh/id_rsa` (or equivalent) on the machine. Push URL is `git@github.com:...`. | Deferred — SSH key lifecycle is out of RepoMend scope for Phase 5. |
| GitHub CLI (`gh auth`) | `gh` must be installed and authenticated. `git push` then resolves through gh's credential helper. | Deferred — adds a binary dependency. |

**Decision:** HTTPS + PAT via env var. The `GITHUB_TOKEN` env var is loaded by
`CredentialProxy` (extend `_CREDENTIAL_KEYS` to include it). A helper
`git_push_branch(worktree_path, remote_url_with_token, branch_name)` in
`worktree_common.py` performs the push. The token is never logged (existing
`CredentialProxy.scrub()` covers it automatically once the key is registered).

**No new credential-handling component is needed.** Phase 5 extends the
existing `CredentialProxy` with one new key (`GITHUB_TOKEN`) and one new
function in `worktree_common.py`. The sandbox boundary is unchanged.

The remote URL with token embedded follows the pattern:
```
https://oauth2:<GITHUB_TOKEN>@github.com/<owner>/<repo>.git
```
This URL is constructed at call time from the scrubbed env value and is never
written to disk or committed.

---

## 1. Client Goal

Build the PR Publisher: the component that takes a verified fix branch, pushes
it to GitHub, and opens a structured pull request describing the security fix.
Phase 5 is the human-in-the-loop handoff: after automated scanning, fixing, and
verification, the human reviewer receives a PR with enough context to evaluate
and merge the fix safely.

The PR body follows a structured five-section template: (1) what the finding
was, (2) what the fix does, (3) the risk class and evidence from the Verifier,
(4) the diff, (5) test output. The PR is always opened as a draft (safety
invariant) and is never auto-merged (ADR-003).

Phase 5 gate: the full pipeline (scan → fix → verify → push → PR open) must
succeed end-to-end on the `subprocess-shell-true` finding from `repomend-fixture`,
producing a real draft PR on the fixture repo that Yehor can inspect and close.

---

## 2. Constraints

| ID | Constraint |
|----|-----------|
| C-P5-01 | All Phase 5 PRs are opened as drafts (`draft: true`). Auto-merge is prohibited (ADR-003). A human must mark the PR ready-for-review. |
| C-P5-02 | `git push` is performed via HTTPS with a PAT embedded in the remote URL (`https://oauth2:<GITHUB_TOKEN>@...`). SSH and `gh` CLI are out of Phase 5 scope. |
| C-P5-03 | `GITHUB_TOKEN` is loaded exclusively through the extended `CredentialProxy`. It must never appear in logs, run log records, SARIF output, or CLI stdout. `CredentialProxy.scrub()` must cover it. |
| C-P5-04 | `git push` is called before the PR API call. If the push fails, the PR API call is not attempted. The run log records `pr_status: push_failed` with the git error (scrubbed). |
| C-P5-05 | If the GitHub API returns 422 with `"A pull request already exists"`, the publisher does NOT open a duplicate. It logs `pr_status: already_open` and records the existing PR URL from the error body. |
| C-P5-06 | The PR body uses a structured five-section template rendered from the Verifier result and the finding dict. The template sections are: **Finding**, **Fix**, **Verification Evidence**, **Diff**, **Test Output**. |
| C-P5-07 | The repo owner, repo name, and base branch are read from config (`repomend.toml` or env). They are not inferred from the git remote URL at runtime. |
| C-P5-08 | PR Publisher is invoked by the Orchestrator only when `verification_status == "verified"`. A `failed` or `false_positive_candidate` fix branch is never pushed. |
| C-P5-09 | `maintainer_can_modify` is set to `true` on all PRs opened by RepoMend. |
| C-P5-10 | `RepomendConfig` is extended with a `[github]` section containing three required fields: `owner` (str), `repo` (str), `base_branch` (str, default `"main"`). If any required field is absent when the `fix` command runs, the CLI exits 1 with an actionable error message naming the missing field. These fields are the sole source of truth for the push target — the git remote URL is never used. |
| C-P5-11 | Run log record is extended with a `pr` sub-object: `{url, number, status, pushed_at}`. `status` values: `opened`, `already_open`, `push_failed`, `api_error`. |

---

## 3. Acceptance Criteria

| ID | Criterion | How verified |
|----|-----------|-------------|
| AC-P5-01 | `CredentialProxy._CREDENTIAL_KEYS` includes `GITHUB_TOKEN`; `scrub()` redacts it from any string containing the token value | Unit: assert `GITHUB_TOKEN` in `_CREDENTIAL_KEYS`; assert `scrub("prefix <token> suffix")` returns `"prefix [REDACTED] suffix"` |
| AC-P5-02 | `git_push_branch(worktree_path, remote_url, branch_name)` added to `worktree_common.py`; calls `git push <remote_url> <branch>:<branch>` with `worktree_path` as cwd | Unit: mock subprocess; assert correct argv and cwd |
| AC-P5-03 | `git_push_branch` raises `subprocess.CalledProcessError` on non-zero exit; caller catches and logs `pr_status: push_failed` | Unit: mock subprocess raising `CalledProcessError`; assert run log record has `pr_status: push_failed` |
| AC-P5-04 | `PRPublisher.publish(fix_result, finding, run_log)` opens a draft PR via `POST /repos/{owner}/{repo}/pulls`; asserts `draft: true`, correct `head`, correct `base`, non-empty `title` and `body` | Unit: mock `httpx` (or `requests`) POST; assert request body contains `"draft": true` and required fields |
| AC-P5-05 | PR body contains all five template sections: Finding, Fix, Verification Evidence, Diff, Test Output | Unit: call template renderer with a synthetic `FixResult` + Verifier output; assert all five section headers present in output string |
| AC-P5-06 | 422 "already exists" → `pr_status: already_open`; existing PR URL extracted from error response body; no duplicate PR opened | Unit: mock API returning 422 with `errors[].message` containing "already exists"; assert `pr_status: already_open` in run log; assert no second POST call |
| AC-P5-07 | 403 → `pr_status: api_error`; error logged; exception propagated to CLI with user-readable message | Unit: mock API returning 403; assert `pr_status: api_error` and error message in run log |
| AC-P5-08 | `PRPublisher` is not invoked when `verification_status != "verified"` | Unit: mock Orchestrator with a `failed` Verifier result; assert `PRPublisher.publish` not called |
| AC-P5-09 | Run log record after successful PR open contains `pr.url`, `pr.number`, `pr.status == "opened"`, `pr.pushed_at` (ISO-8601 timestamp) | Unit: mock successful push + API 201; assert run log record shape |
| AC-P5-10 | End-to-end integration: scan → fix → verify → push → PR opened as draft on `repomend-fixture`; Yehor confirms PR visible on GitHub and marked draft | Integration: full pipeline on `subprocess-shell-true`; assert `pr.status == "opened"` in run log; manual inspection of PR on GitHub |
| AC-P5-11 | `GITHUB_TOKEN` value does not appear in any run log record, CLI stdout, or subprocess argv string (verified by `CredentialProxy.scrub()`) | Unit: assert `GITHUB_TOKEN` value absent from `repr(run_log_record)` after scrub applied |
| AC-P5-12 | `maintainer_can_modify: true` present in every PR creation request body | Unit: inspect mock POST request body; assert field present and true |
| AC-P5-13 | `repomend.toml` missing `[github]` section or any required field (`owner`, `repo`) → CLI exits 1 with message naming the missing field | Unit: load config without `[github]`; assert `SystemExit(1)` and field name in message |

---

## 4. Test Contract

### Inputs

| Input | Value |
|-------|-------|
| Fixture repo | `repomend-fixture` — Yehor's GitHub repo, accessible via `GITHUB_TOKEN` |
| Target finding | `subprocess-shell-true` at `vulnerable.py:24` (confirmed fixable, verified in Phase 4) |
| Base branch | `main` (repo default) |
| Head branch | `repomend/fix-subprocess-shell-true-<uuid4_short>` (created by Phase 3/4 components) |
| GITHUB_TOKEN | PAT with `repo` scope (classic) or "Pull requests: write" + "Contents: write" (fine-grained) |
| GitHub owner/repo | Read from `repomend.toml` `[github] owner` and `[github] repo` |

### Expected outputs (run log record, `pr` sub-object)

```json
{
  "pr": {
    "url": "https://github.com/<owner>/repomend-fixture/pull/<N>",
    "number": "<N>",
    "status": "opened",
    "pushed_at": "<ISO-8601>"
  }
}
```

### Sequencing invariants

1. `git push` must succeed before any GitHub API call is made.
2. PR API call is made only when `verification_status == "verified"`.
3. PR is always `draft: true`; auto-merge is never triggered (ADR-003).
4. Run log record is written whether the PR open succeeds or fails.
5. `GITHUB_TOKEN` is scrubbed from all logged output before the record is written.

### Adversarial / break cases

**Push fails (bad token or no write access):**
`git push` exits non-zero. Publisher logs `pr_status: push_failed` with the
stderr (scrubbed). No PR API call is made. Fix branch stays in the local
worktree (already committed — ADR-017 guarantees this).

**PR already open (idempotent re-run):**
Running RepoMend twice on the same finding produces the same fix branch name
(deterministic from finding ID). On the second run, the push succeeds (branch
already on remote) and the API returns 422 with "already exists". Publisher
logs `pr_status: already_open` with the existing PR URL. The run is not an
error — it is an expected idempotency case.

**Base branch does not exist:**
API returns 422 with `"Invalid value for 'base'"`. Publisher logs
`pr_status: api_error` with the message. Pre-check: before the push/PR
sequence, validate that `base_branch` exists in the repo config. If not
found, abort early with a clear error.

**Draft PR on GitHub Free private repo:**
API returns 422 because draft PRs are not available on GitHub Free for
private repos. Publisher catches this specific error (message contains "draft")
and retries with `draft: false` exactly once, logging a warning. If the retry
also fails, it propagates as `pr_status: api_error`.

---

## 5. Risk Areas

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Token in subprocess argv or git remote URL logged to disk | High | Remote URL is constructed in memory, passed directly to `subprocess.run()`; never written to disk, worktree config, or run log. `CredentialProxy.scrub()` applied before any string is logged. |
| `git push` leaves branch on remote if subsequent PR open fails | Medium | Acceptable: a pushed branch without a PR is safe. On retry, push is a no-op (already up-to-date) and PR creation resumes. |
| `httpx` not in project dependencies | Low | `httpx` is a transitive dependency of the `anthropic` SDK — confirmed available in the project venv (run `uv run python -c "import httpx; print(httpx.__version__)"` on Windows to verify). If confirmed, use `httpx` directly with no new `pyproject.toml` entry needed. If unexpectedly absent, add via `uv add httpx`. `urllib.request` fallback not recommended — verbose and error-prone for JSON POST with custom headers. |
| Fix branch name collision (same finding, different runs) | Low | Branch name is deterministic from finding ID (uuid4 generated once at Phase 3 worktree creation). Collision = same branch = idempotent push. |
| Draft PR unavailable for private repo on GitHub Free | Low–Medium | Handled in adversarial case above — retry once with `draft: false` and log warning. |
| `repomend-fixture` used for integration test creates real PRs on GitHub | Medium | Use a dedicated test branch (`repomend/integration-test-*`) and close/delete PRs after test run. Document in test setup. |

---

## 6. Known Limitations

1. **Single-repo only.** Phase 5 publishes one PR per finding per run, to the
   repo where the finding was discovered. Multi-repo batching is Phase 6 scope.

2. **No reviewer assignment.** PRs are opened without `reviewers` or `assignees`.
   GitHub notification defaults apply. Reviewer assignment is Phase 6 scope.

3. **PR template is static.** The five-section template is rendered from the
   Verifier result and finding dict. It does not adapt to risk class (the
   routing by risk class — low/medium/high — is the Phase 5 stretch goal, and
   is listed as KS-P5-05 which may slip to Phase 6 if complexity warrants).

4. **SSH and `gh` CLI auth not supported.** Only HTTPS + PAT via env var. Users
   who authenticate via SSH or `gh` must add a `GITHUB_TOKEN` to their env.
   A future ADR can extend credential resolution to SSH or `gh`'s token store.

5. **No auto-close of fix branch on PR merge.** The fix branch persists on the
   remote after the PR is merged. GitHub's "delete branch on merge" setting must
   be enabled by the user on the target repo. Automated branch cleanup is Phase 6.

6. **Gate 1 is per-rule, per-file — not full-repo re-scan.** Carried forward from
   Phase 4 §6. A fix that moves a vulnerability elsewhere will pass Gate 1 and
   reach the PR stage. Document in the PR body under Verification Evidence.

---

## 7. Architectural Decisions This Phase Introduces

**ADR-018 | 2026-06-22 | HTTPS + PAT for git push — no SSH or gh CLI in Phase 5**
Decision: `git push` in Phase 5 uses HTTPS with `GITHUB_TOKEN` embedded in the
remote URL (`https://oauth2:<token>@github.com/...`). SSH key management and
`gh` CLI are deferred out of Phase 5 scope.
Rationale: HTTPS + env-var token requires no new binary dependencies and fits
the existing `CredentialProxy` pattern. Adding SSH key lifecycle or a `gh`
dependency would introduce new trust-boundary questions that are out of scope
for the minimal Phase 5 build.
Status: Proposed — requires Yehor approval at sign.

**ADR-019 | 2026-06-22 | All RepoMend PRs open as draft — human must promote**
Decision: Every PR opened by RepoMend sets `draft: true`. The human reviewer
must explicitly mark it ready-for-review. This is a safety invariant, not a
configuration option. (The retry-on-GitHub-Free exception is an operational
workaround, not a policy exception — the intent is always draft.)
Rationale: Auto-merge is prohibited by ADR-003. Draft enforces the human gate
at the GitHub UI level in addition to the code-level invariant. A
non-draft PR could be merged immediately by automation (e.g. a merge queue or
a CI bot), bypassing the human review intent.
Status: Proposed — requires Yehor approval at sign.

---

## 8. Namespace

Base contract ACs: `AC-P5-XX`. Addendum ACs: `AC-P5A-XX`. No number reuse.

---

## 9. Accountability Statement

_I, Yehor, confirm this contract is complete, the acceptance criteria are
testable, and I authorize the Phase 5 build to begin once I sign below.
ADR-018 and ADR-019 are approved as written._

**Signed:** Yehor  **Date:** 2026-06-22

---

_This contract may not be modified after signing without a new INTAKE addendum
using the AC-P5A-XX namespace._
