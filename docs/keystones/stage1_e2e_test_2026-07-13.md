# Stage-1 E2E Test Report — 2026-07-13

**Report ID:** KS-STAGE1-01
**Covers:** BACKLOG item 3 — scan→fix→verify→PR against an owned repo
**Target:** `tests/fixture_repo` (`github.com/yehorcallmedai-maker/repomend-fixture`)
**Command:** `uv run patchward fix --repo tests\fixture_repo`, run by Yehor
**Log:** `runs/session_20260713T142942Z.json`
**Status:** COMPLETE — result is a clean, informative outcome per BUILD_PLAN's
own framing ("a Stage 1 failure is the cheapest place to find the biggest
problem"). One HIGH-severity product defect found. Recommend: do not
proceed to Stage 2 or Mirror Pass Tier 2 until it's addressed.

---

## 1. Headline result

3 of 5 findings reached Fix-Gen+Verifier "verified" status; all 3 branches
pushed successfully to the real remote (confirmed via `git ls-remote`,
Tier 0 — this is not just trusting the CLI's own report). Zero PRs
actually opened, blocked by a `GITHUB_TOKEN` permission gap (Defect 2,
below) — separate from the "verified" pipeline result. **Of the 3
"verified" fixes, only 2 are actually correct.** The third was inspected
directly on its pushed branch (not just its self-reported description)
and is objectively broken — see Defect 1.

| Finding | Fix-Gen | Verifier | Actual fix (verified by reading the real diff) |
|---|---|---|---|
| semgrep subprocess-shell-true @ L24 | crashed (invalid branch name) | n/a | — |
| bandit B404 (bare import) @ L14 | produced a fix | **VERIFIED (gates 1/2/3 pass)** | **BROKEN** — see Defect 1 |
| bandit B602 (same subprocess vuln) @ L24 | produced a fix | VERIFIED | Correct — `shlex.split(cmd)` + `shell=False` |
| bandit B307 (eval) @ L30 | failed cleanly (max_turns) | n/a — no branch persisted | — |
| bandit B105 (hardcoded password) @ L37 | produced a fix | VERIFIED | Correct — `os.getenv("SERVICE_PASSWORD")` |

---

## 2. Defect 1 (HIGH) — Verifier passed a broken fix

**What happened:** Fix-Gen "fixed" the B404 finding (a bare `import
subprocess` with no direct vulnerability of its own — see §5) by deleting
the import and adding an unused `import shlex` instead. `run_command()` on
that same branch **still calls `subprocess.run(cmd, shell=True)` at line
24** — with the import gone, calling this function raises `NameError` at
runtime. The Verifier reported `gate_1=pass gate_2=pass gate_3=pass` and
`verification_status=VERIFIED`.

**Confirmed by direct inspection of the real pushed branch, not by
trusting Fix-Gen's self-reported `diff_summary`:**
```
git diff main origin/patchward/fix-bandit.B404-225171 -- vulnerable.py
-import subprocess
+import shlex
```
`run_command()` unchanged on that branch — `subprocess.run(...)` still
present, `subprocess` no longer imported.

**Why the gates missed it:**
- Gate 1 (rescan) almost certainly reports clean because removing the
  import breaks the semgrep pattern's type resolution — the rule stops
  matching, which looks identical to "vulnerability fixed" even though
  the underlying dangerous call is untouched.
- Gate 3 (test suite) passes because nothing in the fixture's test suite
  (`tests/test_clean.py`) exercises `run_command()` — there's no test
  that would actually execute the broken code path and surface the
  `NameError`.

**Why this matters beyond this one fixture:** this is not a fixture
quirk — it's a structural gap. Any finding whose "fix" can be satisfied
by deleting the offending import (rather than fixing the offending call)
will pass Gate 1 the same way, and any repo whose test suite doesn't
happen to cover the affected function will pass Gate 3 the same way. This
is the kind of defect that costs nothing to find here and would cost a
real user's CI pipeline if found in production.

**Recommend:** treat this as a blocker for Stage 2 (third-party repo) and
Mirror Pass Tier 2, consistent with BUILD_PLAN §6's own logic — feature
work or wider exposure on top of an unvalidated core is inventory risk.
Concrete fix directions worth considering (not yet decided, needs your
input): Gate 1 could additionally confirm the specific dangerous call
site no longer exists (not just that the rule doesn't fire), or Gate 3
could require the modified file's defining tests to include the changed
function name, or Fix-Gen's prompt could be constrained to never remove
an import that's still referenced elsewhere in the file (a static,
cheap, pre-Verifier check).

---

## 3. Defect 2 (MEDIUM) — `GITHUB_TOKEN` can push but cannot open PRs

All 3 branches pushed successfully (`git push` via the embedded token in
the remote URL succeeded silently — confirmed via `git ls-remote origin`
showing all 3 branches live on the real remote). The subsequent REST call
to `POST /repos/.../pulls` returned 403 all three times. This is the
classic signature of a token that has repo/contents write access but
lacks pull-request-creation permission — for a fine-grained PAT, that's
the "Pull requests: Read and write" permission specifically; for a
classic PAT, it should already be covered by `repo` scope, so if it's a
classic PAT the more likely cause is expiry or revocation since Phase 5
(2026-06-22, when PR #1/#2 last worked).

**Action for Yehor:** check `GITHUB_TOKEN`'s type and permissions
(GitHub Settings → Developer settings → Personal access tokens). If
fine-grained, confirm "Pull requests: Read and write" and "Contents: Read
and write" are both granted for `repomend-fixture`. If classic, confirm
it hasn't expired.

---

## 4. Defect 3 (LOW, confirmed by direct code read) — CLI misreports failed PR creation as success

`src/patchward/cli.py` L496-499:
```python
typer.echo(f"  [PR] Opened: {pr_dict['url']}")
```
This runs unconditionally after `publisher.publish()` returns — it does
not check `pr_dict['status']`. When `_create_pr()` in `pr_publisher.py`
returns `{"url": "", "number": "", "status": "api_error"}` (the 403 case,
confirmed in `pr_publisher.py` L369-375), the CLI still prints
`[PR] Opened: ` with a blank URL instead of a clear failure message. This
is exactly what was observed in the real run output. Cheap to fix: check
`pr_dict['status'] == 'opened'` before printing success.

---

## 5. Lower-severity / informational

- **B307 (eval) failure ("max_turns reached without submit_fix call")**
  is a clean, expected failure — Fix-Gen simply couldn't produce a fix
  within budget for this one. No branch was persisted (C-P3-12 inverted
  lifecycle held correctly). Not a defect, just a capability limit worth
  knowing about.
- **B404 itself is a low-value finding to "fix" at all** — bandit's B404
  flags the bare fact that `subprocess` is imported, not a specific
  dangerous call. The real, fixable issue at that location is B602
  (`shell=True`), which was separately and correctly fixed. Worth
  considering whether `patchward fix` should skip purely-informational
  findings like B404 rather than let Fix-Gen attempt a "fix" for
  "you imported a module" — flagged in BACKLOG, not decided here.
- **Semgrep subprocess-shell-true crash** — the branch name for this one
  finding literally contained the string "requires login"
  (`patchward/fix-requires login-9b336c`), an invalid git ref (contains a
  space), causing `git worktree add` to exit 255. Root cause **not yet
  confirmed** — plausible explanation is that semgrep's `p/python`
  registry ruleset attempted a login-gated request and an auth-related
  message leaked into the fingerprint/finding-id pipeline, but this is a
  hypothesis, not a verified finding. Needs investigation before being
  treated as understood.

---

## 6. What's NOT been done

- The 3 pushed branches (`patchward/fix-bandit.B404-225171`,
  `.../fix-bandit.B602-dc3625`, `.../fix-bandit.B105-a202b8`) are live on
  the real `repomend-fixture` remote and have not been cleaned up —
  Yehor's call whether to delete them or leave them for reference.
  **No PRs exist** (all 3 blocked at the API-403 step), so there's
  nothing to close on GitHub, only branches to optionally delete.
- Defect 1 (the Verifier gap) has not been fixed — this report documents
  it, doesn't resolve it.
- Defect 4 (the "requires login" root cause) has not been investigated.

---

_Author:_ Claude (agent), verified against real pushed branches, not
self-reported tool output. _Date:_ 2026-07-13. _Awaiting Yehor's review
and prioritization decision._
