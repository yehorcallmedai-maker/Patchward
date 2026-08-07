# BACKLOG 29 — implementation report

**Date:** 2026-08-07 · **Session:** 031 · **HEAD at time of work:** `b731fe2` (confirmed identical to `git ls-remote origin main`)
**Item:** `pipeline.py` records `"pr_opened"` even when PR creation fails
**Status:** implemented + tested + mutation-proven. **Nothing staged, nothing committed, nothing pushed.**

---

## 0. Confirmation of constraints (H20)

| Constraint | Status |
|---|---|
| `git add` / `commit` / `push` from the sandbox | **NEVER RUN.** `git diff --cached --stat` is empty. |
| HEAD moved? | No — still `b731fe2660c40ac0cb4c85a42b25c752dd5c89ec`, matches origin. |
| `.git/index.lock` left behind | None. Checked before and after; all git calls used `--no-optional-instance-locks`-equivalent (`--no-optional-locks`). |
| CRLF introduced into any file | **Zero.** All three edited files were LF-only before and remain LF-only (`grep -c $'\r$'` = 0 each). |
| Tracked files edited outside scope | No. Diff limited to the three files listed below. |

**Interpreter caveat, stated plainly:** every test run in this report used a **sandbox Linux venv on Python 3.10.12**. Your `.venv` (3.14.4) is a Windows venv and is not executable from the sandbox. **These runs are advisory. The real gate is yours:** `.\.venv\Scripts\python.exe -m pytest -q` with the coverage floor.

---

## 1. Step 1 — the correct pattern, quoted verbatim (`cli.py:522-547`)

```python
                                    # BACKLOG 3c: pr_dict['status'] can be
                                    # "opened", "already_open" (idempotent —
                                    # see pr_publisher._create_pr), or
                                    # "api_error" (403/422/unexpected — url
                                    # is blank). Previously this printed
                                    # "[PR] Opened: " unconditionally, so a
                                    # 403 looked identical to success with a
                                    # blank URL. Confirmed in the 2026-07-13
                                    # Stage-1 E2E test.
                                    pr_status = pr_dict.get("status", "")
                                    if pr_status == "opened":
                                        typer.echo(
                                            f"  [PR] Opened: "
                                            f"{pr_dict['url']}"
                                        )
                                    elif pr_status == "already_open":
                                        typer.echo(
                                            f"  [PR] Already open: "
                                            f"{pr_dict['url']}"
                                        )
                                    else:
                                        typer.echo(
                                            f"  [PR] Failed to open "
                                            f"(status={pr_status!r})",
                                            err=True,
                                        )
```

Three outcomes; **fail-closed default** (`get("status", "")` → falls to `else`).

### Real return shape of `PRPublisher.publish()` — verified, not assumed

`publish()` (pr_publisher.py:107-166) returns:

```python
pr_record = {
    "url":       pr_data.get("url", ""),
    "number":    pr_data.get("number", ""),
    "status":    pr_data.get("status", "opened"),
    "pushed_at": pushed_at,
}
```

Every `return` in `_create_pr()` enumerated (pr_publisher.py:420-478) — the complete status vocabulary is exactly three values:

| Line | status | url |
|---|---|---|
| 423 | `"opened"` | real URL |
| 449 | `"opened"` | real URL |
| 451 | `"api_error"` | `""` |
| 462 | `"already_open"` | real URL |
| 466, 474, 478 | `"api_error"` | `""` |

**Ordering fact that sets the severity:** `publish()` calls `git_push_branch(...)` at line 151 — *before* `_create_pr()` at line 154. The branch is on the customer's remote before the PR call is even attempted.

---

## 2. Step 2 — the bug site, quoted verbatim (`pipeline.py:262-268`, before)

```python
                                finding_pr_url = pr_dict.get("url")
                                finding_status = "pr_opened"
                                logger.info(
                                    "[pipeline] %s → PR: %s",
                                    repo_label,
                                    finding_pr_url,
                                )
```

`pr_dict["status"]` never consulted. On `api_error` this recorded `status="pr_opened"`, `pr_url=""`, and logged `"→ PR: "` with an empty URL.

**Hosted-path confirmation (this is the customer-facing path, not just the CLI):**

```
src/patchward/webhook.py:69   from patchward.pipeline import run_repo_pipeline
src/patchward/webhook.py:412  result = await run_repo_pipeline(
src/patchward/webhook.py:419  logger.info("[webhook] scan finished for %s: %s", repo_full_name, result)
```

The webhook **logs `result` and does not branch on it** — so the status string was the only error trail, and it said success.

---

## 3. Step 3 — behaviour, before → after

| `publish()` returns | Before | After | Matches cli.py? |
|---|---|---|---|
| `status="opened"` | `pr_opened`, url recorded | `pr_opened`, url recorded | yes |
| `status="already_open"` | **`pr_opened`** (conflated) | `pr_already_open`, url recorded | yes — distinct third outcome |
| `status="api_error"` | **`pr_opened`, url `""`** | `pr_failed`, `error="pr_creation_failed: status='api_error'"`, url `None`, `logger.error` naming the pushed branch | yes |
| no `status` key | **`pr_opened`** | `pr_failed` (fail-closed) | yes — same `get(...,"")` + `else` |

### Naming rationale (no invented vocabulary)

`pipeline.py` already uses its own `<stage>_<outcome>` status set: `declined`, `fix_failed`, `verify_failed`, `pr_opened`, `rate_limited`, `error`. The two new values follow that convention exactly and map 1:1 onto cli.py's three branches — `pr_already_open` ← `already_open`, `pr_failed` ← the `else`. No new concept was introduced.

### H24 enumeration — who consumes these status values?

Grepped every consumer of `pr_opened` / `fix_failed` / `verify_failed` / `rate_limited` across `src/` and `tests/`:

- **No production code outside `pipeline.py` branches on the status.** `webhook.py` logs `result` verbatim; `run_log.append_batch_result()` stores it opaquely; `cli.py` has its own independent handling and never reads pipeline's value.
- Consumers are otherwise **tests only** (`test_async_pipeline.py`, `test_orchestrator.py`, `test_cli.py:351`, `test_run_log.py:155`).

Adding two status values therefore cannot break a production branch. This was checked, not assumed.

---

## 4. Step 4 — tests

### Added / repaired

| Test | Branch covered |
|---|---|
| `test_run_repo_pipeline_pr_opened` **(REPAIRED)** | `opened` → `pr_opened` + url |
| `test_pipeline_pr_already_open_is_not_reported_as_opened` (new) | `already_open` → `pr_already_open` |
| `test_pipeline_pr_api_error_is_not_reported_as_opened` (new) | `api_error` → `pr_failed` + reason, **not** `pr_opened` |
| `test_pipeline_pr_missing_status_fails_closed` (new) | missing status → `pr_failed`, no url |

All four drive the **real `run_repo_pipeline`** and mock only `PRPublisher`, so the status-handling block executes for real.

### ⚠️ Two things that need your eyes

**(a) `test_run_repo_pipeline_pr_opened` was a phantom test.** It was truncated mid-statement at `mock_pub_cls.return_value.publish.return_` — a bare attribute access on a MagicMock. It parsed, ran, called `run_repo_pipeline` **never**, and asserted **nothing**, while counting as a passing test. It was flagged in item 21's review as "out of scope to repair"; since it is the success branch of exactly this fix, I repaired it. Its fixture also lacked a `status` key.

**(b) I modified a third file — `tests/test_orchestrator.py` — and you should scrutinise this one.**
`TestRunLogThreaded::test_run_log_none_does_not_crash` failed after the fix. I did **not** weaken the fix to make it pass. Analysis:

- Its docstring subject is *"run_log=None must not raise AttributeError (defensive)"*; `assert result["status"] == "pr_opened"` is an incidental liveness proxy.
- Its mock returned `{"url": ...}` **with no `status` key** — a shape the real `publish()` **cannot produce** (pr_publisher.py:160 always sets one).
- It passed before only because the old code ignored `status` entirely.

I corrected the fixture to the realistic success shape (`status="opened"`). **The assertion is unchanged and the test's actual subject is untouched.** If you'd rather the fail-closed default were `"opened"` instead — making a status-less dict a success — say so and I'll flip it; I chose fail-closed because it mirrors cli.py and because the whole point of this item is that silent success is the dangerous direction.

### Sandbox run results (advisory — 3.10.12, NOT the gate)

```
tests/test_async_pipeline.py                       25 passed
test_cli + test_orchestrator + test_pr_publisher
  + test_run_log  (CLI-path regression)            80 passed
FULL SUITE  -m "not integration"                  557 passed, 4 skipped, 15 deselected
```

Baseline before this change on the same interpreter was **554 passed / 4 skipped**; net **+3** = 3 new tests (the 4th was already collected as the phantom). **Expected on your 3.14.4 gate: 555 → 558 passed, 3 skipped.**

---

## 5. Mutation check — 8/8 load-bearing lines proven (H25)

Performed on a **scratch copy** at `/tmp/mut`, never on the tracked tree. Each mutation applied individually, suite run, then restored.

| # | Mutation | Caught by |
|---|---|---|
| M1 | Revert the entire fix (restore the original two buggy lines) | `already_open`, `api_error`, `missing_status` — **3 tests** |
| M2 | `else:` branch reports `pr_opened` instead of `pr_failed` | `api_error`, `missing_status` |
| M3 | Drop `result["error"] = "pr_creation_failed: ..."` | `api_error` |
| M4 | Fail-**open** default: `.get("status", "opened")` | `missing_status` |
| M5 | Collapse `already_open` into `pr_opened` | `already_open` |
| M6 | Failure branch records a `pr_url` anyway | `missing_status` |
| M7 | Success branch stops recording `pr_url` | `pr_opened` |
| M8 | Success literal typo'd (`"OPENED"`) | `push_token`, `pr_opened`, `run_log_none` — **3 tests** |

**Zero silent survivors.** After the final restore, `pipeline.py` was byte-identical to its pre-mutation state and the suite reconfirmed **48 passed** on the scratch copy.

---

## 6. What I could NOT verify — gaps, not omissions

1. **The real gate.** Nothing here ran on Python 3.14.4 or with `--cov-fail-under=80`. My 557 is a Linux/3.10 number. **Your run is the gate.**
2. **Coverage delta.** `pipeline.py` was at **90%** (11 missed, lines 317-337) in your last gate. This adds ~50 statements of branching that the new tests exercise, so it should hold or rise — but I cannot produce your coverage number.
3. **No live/E2E proof.** No real GitHub API call was made. The `api_error` path is proven against publish()'s *contract* (its literal return values, read from source), not against a live 403. Consistent with how cli.py's equivalent was validated, but it is not an end-to-end proof.
4. **`already_open` semantics are inherited, not re-derived.** I mirrored cli.py's treatment of it as a distinct non-failure. Whether the hosted path should treat an idempotent re-run as success for billing/reporting is a **product question I did not decide.**
5. **The hosted image still unconfirmed since Session 027.** This fix is code-correct and test-proven; it says nothing about whether the deployed machine runs it.
6. **BACKLOG 28 remains uncommitted and unreviewed** in the same working tree (`webhook.py`, `test_webhook.py`). Untouched by me — but it means the tree now carries **two independent uncommitted changes.**

---

## 7. Staging instructions (your hands only — H20)

The tree has two unrelated changesets. **Do not `git add -A`.** BACKLOG 29 is these three paths and nothing else:

```powershell
cd D:\Dev\Projects\Patchward

# 1. THE REAL GATE FIRST — expect 558 passed, 3 skipped, coverage >= 80%
.\.venv\Scripts\python.exe -m pytest -q

# 2. Stage ONLY BACKLOG 29's three files, explicitly
git add src/patchward/pipeline.py tests/test_async_pipeline.py tests/test_orchestrator.py

# 3. TRIPWIRE — must show exactly 3 files and roughly these counts.
#    Thousands of lines = CRLF corruption; unstage and stop.
git diff --cached --stat
#    expected ≈  pipeline.py +68/-7 · test_async_pipeline.py +168/-2 · test_orchestrator.py +11/-1
```

Suggested message:

```
fix(hosted-path): honour PRPublisher status instead of reporting pr_opened unconditionally (BACKLOG 29)
```

`webhook.py` and `test_webhook.py` must stay **out** of that commit — they are BACKLOG 28 and still owe an adversarial pass.

---

## 8. Full diff

```diff
===== src/patchward/pipeline.py =====
@@ -259,13 +259,74 @@
                                         handle.worktree_path
                                     ),
                                 )
-                                finding_pr_url = pr_dict.get("url")
-                                finding_status = "pr_opened"
-                                logger.info(
-                                    "[pipeline] %s → PR: %s",
-                                    repo_label,
-                                    finding_pr_url,
-                                )
+                                # KS-TRACE: BACKLOG 29 — honour the
+                                # publisher's status instead of assuming
+                                # success.
+                                #
+                                # PRPublisher.publish() returns
+                                # status ∈ {"opened", "already_open",
+                                # "api_error"} (pr_publisher._create_pr;
+                                # "api_error" covers 403/422/unexpected
+                                # and carries a BLANK url). This block
+                                # previously set "pr_opened"
+                                # unconditionally, so a PR-creation
+                                # failure was recorded — and reported to
+                                # the caller — as success. On the hosted
+                                # path that is materially worse than a
+                                # bad status string: the fix branch has
+                                # ALREADY been force-pushed to the
+                                # customer's repository by the time
+                                # _create_pr runs, so the customer is
+                                # left with an unexplained branch, no
+                                # PR, and a tool reporting success.
+                                #
+                                # Mirrors the CLI's existing three-way
+                                # branch (cli.py, BACKLOG 3c) — same
+                                # outcomes, same fail-closed default:
+                                # any unrecognised or missing status is
+                                # treated as a failure, never success.
+                                pr_status = pr_dict.get("status", "")
+                                if pr_status == "opened":
+                                    finding_pr_url = pr_dict.get("url")
+                                    finding_status = "pr_opened"
+                                    logger.info(
+                                        "[pipeline] %s → PR: %s",
+                                        repo_label,
+                                        finding_pr_url,
+                                    )
+                                elif pr_status == "already_open":
+                                    finding_pr_url = pr_dict.get("url")
+                                    finding_status = "pr_already_open"
+                                    logger.info(
+                                        "[pipeline] %s → PR already "
+                                        "open: %s",
+                                        repo_label,
+                                        finding_pr_url,
+                                    )
+                                else:
+                                    # finding_pr_url stays None — on
+                                    # api_error publish() returns a
+                                    # blank url, and recording "" would
+                                    # read as "a PR exists somewhere".
+                                    finding_status = "pr_failed"
+                                    # pr_status is a controlled literal
+                                    # produced by _create_pr, never a
+                                    # credential or a verbatim API body,
+                                    # so it needs no scrub_text() (cf.
+                                    # BACKLOG 19 on the except paths).
+                                    result["error"] = (
+                                        "pr_creation_failed: "
+                                        f"status={pr_status!r}"
+                                    )
+                                    logger.error(
+                                        "[pipeline] %s → PR creation "
+                                        "FAILED (status=%r); branch %s "
+                                        "was already pushed but no PR "
+                                        "was opened",
+                                        repo_label,
+                                        pr_status,
+                                        fix_result.branch_name,
+                                    )
 
                 except anthropic.RateLimitError as exc:
                     finding_status = "rate_limited"

===== tests/test_async_pipeline.py =====
@@ -705,7 +705,15 @@
     good_verify = MagicMock()
     good_verify.verification_status = "verified"
     good_verify.gate_2.reason = ""
-    pr_result = {"url": "https://github.com/acme/repo-0/pull/1"}
+    # BACKLOG 29: this dict previously carried NO "status" key and the
+    # test body was truncated mid-statement, so nothing ever pinned the
+    # success branch. Publisher's real success shape includes
+    # status="opened" (pr_publisher._create_pr).
+    pr_result = {
+        "url": "https://github.com/acme/repo-0/pull/1",
+        "number": 1,
+        "status": "opened",
+    }
 
     with (
         patch(
@@ -736,7 +744,165 @@
         )
         mock_verifier_cls.return_value.verify.return_value = good_verify
         mock_proxy_cls.return_value.load.return_value = MagicMock()
-        mock_pub_cls.return_value.publish.return_
+        mock_pub_cls.return_value.publish.return_value = pr_result
+
+        result = await run_repo_pipeline(
+            cfg.repos[0], cfg, sem, "key", "ghs_token",
+        )
+
+    assert result["status"] == "pr_opened"
+    assert result["pr_url"] == "https://github.com/acme/repo-0/pull/1"
+    assert result.get("error") in (None, "")
+
+
+# ---------------------------------------------------------------------------
+# BACKLOG 29 — run_repo_pipeline must honour PRPublisher.publish()'s status
+# instead of reporting "pr_opened" unconditionally.
+#
+# Severity is about consequence, not code size: publish() pushes the fix
+# branch BEFORE it calls the PR-creation endpoint, so when PR creation fails
+# (e.g. the App installation lacks pull_requests:write) the branch is already
+# on the CUSTOMER's repository. Reporting success there leaves an unexplained
+# branch on someone else's infrastructure with no PR and no error trail.
+# The hosted path runs through this exact function
+# (webhook.py -> run_repo_pipeline), so this is the customer-facing path.
+#
+# These tests mock ONLY PRPublisher; the status-handling block under test
+# runs for real, so reverting it makes them fail.
+# ---------------------------------------------------------------------------
+
+def _pipeline_success_mocks(tmp_path: Path):
+    """Shared arrange-block for the BACKLOG 29 branch tests: a run that
+    reaches the PR-publish step with a verified fix, so the ONLY variable
+    is what publish() returns."""
+    from unittest.mock import MagicMock
+    from patchward.fix_gen import FixResult
+
+    cfg = _make_cfg(tmp_path, n_repos=1)
+    sem = asyncio.Semaphore(1)
+    sarif_run = _make_sarif_run([_fake_finding()])
+    good_fix = FixResult(
+        model="claude-sonnet-4-6",
+        finding_id="test",
+        success=True,
+        description="fixed shell=True",
+        branch_name="patchward/fix-test",
+    )
+    good_verify = MagicMock()
+    good_verify.verification_status = "verified"
+    good_verify.gate_2.reason = ""
+    return cfg, sem, sarif_run, good_fix, good_verify
+
+
+async def _run_with_publish_result(tmp_path: Path, publish_result: dict):
+    """Drive the real run_repo_pipeline to the publish step and hand it
+    ``publish_result`` as PRPublisher.publish()'s return value."""
+    from unittest.mock import MagicMock
+
+    cfg, sem, sarif_run, good_fix, good_verify = _pipeline_success_mocks(
+        tmp_path
+    )
+
+    with (
+        patch(
+            "patchward.pipeline.run_all_scanners",
+            return_value=[sarif_run],
+        ),
+        patch(
+            "patchward.pipeline.fix_worktree_context"
+        ) as mock_ctx,
+        patch(
+            "patchward.pipeline.FixGenSubagent"
+        ) as mock_agent_cls,
+        patch(
+            "patchward.pipeline.Verifier"
+        ) as mock_verifier_cls,
+        patch(
+            "patchward.pipeline.CredentialProxy"
+        ) as mock_proxy_cls,
+        patch(
+            "patchward.pipeline.PRPublisher"
+        ) as mock_pub_cls,
+    ):
+        handle = mock_ctx.return_value.__enter__.return_value
+        handle.worktree_path = tmp_path / "wt"
+        handle.branch = "patchward/fix-test"
+        mock_agent_cls.return_value.apply_fix = AsyncMock(
+            return_value=good_fix
+        )
+        mock_verifier_cls.return_value.verify.return_value = good_verify
+        mock_proxy_cls.return_value.load.return_value = MagicMock()
+        mock_pub_cls.return_value.publish.return_value = publish_result
+
+        return await run_repo_pipeline(
+            cfg.repos[0], cfg, sem, "key", "ghs_token",
+        )
+
+
+@pytest.mark.asyncio
+async def test_pipeline_pr_already_open_is_not_reported_as_opened(
+    tmp_path: Path,
+) -> None:
+    """status="already_open" (idempotent re-run) is a distinct outcome,
+    exactly as cli.py treats it — not collapsed into "pr_opened"."""
+    result = await _run_with_publish_result(
+        tmp_path,
+        {
+            "url": "https://github.com/acme/repo-0/pull/7",
+            "number": 7,
+            "status": "already_open",
+        },
+    )
+
+    assert result["status"] == "pr_already_open"
+    assert result["pr_url"] == "https://github.com/acme/repo-0/pull/7"
+
+
+@pytest.mark.asyncio
+async def test_pipeline_pr_api_error_is_not_reported_as_opened(
+    tmp_path: Path,
+) -> None:
+    """THE BACKLOG 29 REGRESSION TEST. publish() returning "api_error"
+    (403/422/unexpected — blank url) must NOT be recorded as success.
+
+    Before the fix this asserted-on value was "pr_opened" with pr_url="",
+    which is what would have reached a Marketplace customer as a silent
+    failure after their repo had already received the pushed branch."""
+    result = await _run_with_publish_result(
+        tmp_path,
+        {"url": "", "number": "", "status": "api_error"},
+    )
+
+    assert result["status"] != "pr_opened", (
+        "BACKLOG 29: a failed PR creation must never be reported as "
+        "success — the branch is already on the customer's repo"
+    )
+    assert result["status"] == "pr_failed"
+    # The reason must survive to the caller; the webhook logs
+    # result verbatim, so this is the only error trail that exists.
+    assert "api_error" in result["error"]
+    # No blank URL masquerading as a real PR.
+    assert not result["pr_url"]
+
+
+@pytest.mark.asyncio
+async def test_pipeline_pr_missing_status_fails_closed(
+    tmp_path: Path,
+) -> None:
+    """Fail-closed default: a publish() result with no "status" key at all
+    must be treated as failure, never silently as success. Mirrors
+    cli.py's ``pr_dict.get("status", "")`` + else-branch."""
+    result = await _run_with_publish_result(
+        tmp_path,
+        {"url": "https://github.com/acme/repo-0/pull/9"},
+    )
+
+    assert result["status"] == "pr_failed"
+    assert result["status"] != "pr_opened"
+    # A URL was present in the publish result, but the publish did not
+    # demonstrably succeed — recording it would imply a PR exists.
+    assert not result["pr_url"]
+
 
 # ── KS-P6-05: scanner uses config.models.scanner_model ───────────────────
 

===== tests/test_orchestrator.py =====
@@ -1062,8 +1062,18 @@
             mock_vfy_cls.return_value.verify.return_value = (
                 verify_ok
             )
+            # BACKLOG 29: this mock previously omitted "status", a shape
+            # the real PRPublisher.publish() cannot produce — it always
+            # sets status (pr_publisher.py, `pr_data.get("status",
+            # "opened")`). The omission was invisible while pipeline.py
+            # ignored status altogether; now that a missing status fails
+            # closed, the fixture is corrected to the realistic success
+            # shape. The assertion below is unchanged, and this test's
+            # actual subject (run_log=None must not raise) is untouched.
             mock_pr_cls.return_value.publish.return_value = {
-                "url": "https://github.com/o/r/pull/1"
+                "url": "https://github.com/o/r/pull/1",
+                "number": 1,
+                "status": "opened",
             }
             sem = asyncio.Semaphore(1)
             result = await run_repo_pipeline(

```
