# §5 — What Gate 3 MEANS on the hosted path (the runner fork)

## SCOPE-AND-DECIDE MEMO — no fix code, nothing chosen, nothing staged

**Verified at:** `main` @ `02148c628fa0f33b07bfdb49267e65bb9efd62b5`
(local mount HEAD, `git ls-remote origin main`, and a fresh `git clone` all
three agree).
**Date:** 2026-08-01 (Session 028)
**Status of this document:** scope only, hard stop. §2 boundary. No option is
chosen here; the install-runners-vs-skip-gracefully call is Yehor's and is
deliberately left open. Companion to `BACKLOG22_gate3_scope_memo_2026-07-28.md`
(the *sandbox-vs-strip* fork). This memo is the *what-does-the-gate-mean* fork.
They are entangled; §3 states exactly how.

---

## 0. What this fork is, and why it is not the item 22 fork

Item 22's memo decides **how safely** Gate 3 runs customer code (sandbox vs.
env-strip). This memo decides **whether Gate 3 runs customer code at all** on the
hosted path, and therefore **what the word "verified" means** in the product's
core claim. These are different decisions with different owners' concerns
(security vs. positioning) — but §3 shows that picking "run it" here forces item
22's hand, so they must be settled in the same sitting.

The fork exists because §5 is now confirmed live (BACKLOG item 21, §5 UPDATE
2026-07-29, machine `7841600fd5e7e8` / `deployment-01KYJ325AN…`): on the deployed
image a customer repo that *has* a pytest suite makes Gate 3 return **FAIL**, not
SKIP, so `verification_status` is never "verified" and no PR is published.

---

## 1. The mechanism, from source at HEAD — why a detected suite FAILs

Three facts, each source-verified:

1. **Gate 3 detects a suite, then shells the runner.** `_gate_3_test_suite`
   (`verifier.py:647`) calls `_detect_test_runner` (`verifier.py:684`). Detection
   is directory/config based — `tests/` with a `test_*.py`, a root `test_*.py`,
   `pytest.ini`, `conftest.py`, or `[tool.pytest` in `pyproject.toml`
   (`verifier.py:701-717`). None of these require the pytest *package* to be
   installed. So detection says "pytest" on the customer's repo regardless of
   whether the image can actually run pytest.

2. **The runner is invoked as a module of Patchward's own interpreter.**
   `_run_pytest` (`verifier.py:736`) runs `["python","-m","pytest","--tb=short","-q"]`
   in the worktree. `_run_jest` (`verifier.py:771`) runs `["npx","jest","--no-coverage"]`.

3. **The deployed image has neither runner.** `pyproject.toml` puts pytest in
   `[dependency-groups].dev` (`pyproject.toml:36-39`), *not* in
   `[project.optional-dependencies].webhook` (`pyproject.toml:25`), and
   `docker/webhook.Dockerfile:37` installs only `.[webhook]` (plus semgrep/bandit/
   pip-audit at line 46, plus `git`+`ca-certificates` at line 26-29). **No pytest
   module. No node/npm/npx.**

**Result on the hosted image:**
- pytest branch: `python -m pytest` → `No module named pytest`. That string
  contains **none** of the three SKIP triggers at `verifier.py:766`
  (`ModuleNotFoundError` / `ImportError` / `no tests ran`) → falls through to
  `return GateResult(FAIL, …)` (`verifier.py:769`).
- jest branch: `npx` absent → `FileNotFoundError` → `return GateResult(FAIL,
  "npx not found")` (`verifier.py:789-790`).

Either way `gate_3.status == FAIL` → `g3_ok` false (`verifier.py:110`) →
`verification_status == "failed"` → `pipeline.py` marks `verify_failed` and
publishes nothing. **For any customer repo with a detected suite, the hosted path
fails verification and opens no PR.** This converges with item 21 from an
independent direction (21 is the dead `github_token`; §5 is the FAIL upstream of
it — both must clear for a PR to ship).

**One subtlety that is decision-relevant (see §3):** because pytest is *absent*,
`python -m pytest` fails at the `runpy` import step **before pytest ever imports
the repo's `conftest.py`**. So today the hosted path detects-but-does-not-execute
adversarial Python test code. The missing runner is, by accident, the only thing
currently keeping item 22's exposure dormant on the hosted path.

---

## 2. What "verified" is designed to mean vs. what it means today

Designed (verifier.py:15-27 docstring): "Verified" = Gate 1 (re-scan clean) PASS
+ Gate 2 (diff in bounds) PASS + Gate 3 (suite PASS **or** SKIP). Gate 3 is
explicitly allowed to SKIP when no suite is detected — the product never promised
to run tests that don't exist. What it *does* imply, when a suite exists, is that
the fix was checked against it.

Today on hosted: a suite that exists returns FAIL, so nothing is "verified" and
nothing ships. The gate is neither running tests nor gracefully skipping them —
it is hard-failing on its own missing tooling. That is the defect. The fork is
about which *correct* behaviour to replace it with.

---

## 3. THE ENTANGLEMENT — §5-Option-A activates item 22 as live (stated plainly)

This is the single most important line in the memo.

Item 22's exposure (adversarial `conftest.py` / jest config executes as the
pipeline uid with credentials in `os.environ`) is **not currently live on the
hosted path** — precisely because §1 shows no runner exists to execute that code.
Installing a runner (§5 Option A) is exactly the act that makes item 22's
exploit live for every repo carrying a `conftest.py` or a jest config.

Therefore:

- **§5 Option A ⟹ item 22 must be resolved in the same change.** You cannot
  "just install pytest to make Gate 3 work" without simultaneously deciding item
  22's sandbox-vs-strip call — because the day pytest lands is the day untrusted
  test code runs next to `ANTHROPIC_API_KEY`, `GITHUB_APP_PRIVATE_KEY_B64`, the
  App ID, and `GITHUB_WEBHOOK_SECRET` (the cross-tenant set catalogued in item
  22 §2a). And item 22's Option A (real sandbox) needs Docker, which the Fly host
  does not have (item 22 §4.5, item 26). So the honest cost chain is:
  **§5-A ⟹ item 22-A ⟹ new execution infrastructure.**
- **§5 Option B (skip gracefully) keeps item 22 dormant on hosted** — no runner,
  no untrusted execution — at the price of the gate's meaning (§4B).

---

## 4. Options — laid out, NOT chosen

For each: what ships, what it costs, what it does to the product claim, whether it
entangles item 22.

### Option A — install the runners into the webhook image

Add pytest (and, for jest, node/npm) so Gate 3 executes as designed.

- **What ships:** in `docker/webhook.Dockerfile`, pytest via the existing pip
  layer (≈ `pip install … pytest pytest-asyncio`, small — order of a few MB);
  node/npm via `apt-get install -y nodejs npm` (large — order of +150–250 MB;
  **estimate, Tier-1 — confirm with a real build**, per §2 discipline this memo
  does not run one).
- **What it costs beyond image size:** the entanglement in §3 — this is the
  trigger that makes item 22 live, so its true cost includes item 22-A's new
  infra, not just the Dockerfile lines. Also: per item 22 §4.1-4.2 Gate 3
  installs no per-repo deps and uses Patchward's own interpreter, so **even with
  pytest present, the majority of customer repos still SKIP** (their test deps
  aren't in the image → `ModuleNotFoundError` → the existing SKIP heuristic
  fires). Option A therefore buys *real* Gate-3 execution for only the thin slice
  of repos whose suites have zero extra deps, while opening the item-22 exposure
  for *all* repos with a `conftest.py`/jest config. Poor trade unless paired with
  item 22-A.
- **What it does to the claim:** upholds "we verify the fix against your test
  suite" — but only honestly for that thin slice; for the rest it is still SKIP,
  so marketing "we run your tests" would overstate the common case.
- **Entangles item 22:** **yes, hard.** Decide together.

### Option B — make Gate 3 SKIP gracefully when the runner is absent

Treat "runner not available in this environment" the same as "no suite detected":
SKIP, not FAIL.

- **What ships:** a scoped change in `verifier.py` — in `_run_pytest`, detect the
  runner-absent signature (`No module named pytest` / non-zero with no collected
  tests) and `return GateResult(SKIP, …)`; in `_run_jest`, turn the
  `FileNotFoundError` branch (`verifier.py:789-790`) from FAIL into SKIP. Small,
  no infra. (Exact diff belongs to the eventual implementation, not this memo.)
- **What it costs:** the gate's meaning. Gate 1 PASS + Gate 2 PASS + Gate 3 SKIP
  = "verified" — so on hosted, "verified" would mean *the scanner no longer fires
  and the diff is in bounds*, with tests **not run**. That is a real downgrade
  from the designed meaning.
- **What it does to the claim:** Gate 3 becomes **advisory on the hosted path**.
  Any site/marketplace copy asserting a *deterministic test-suite verification*
  for hosted users would be inaccurate and should be corrected to something like
  "we confirm the fix removes the finding and stays in-bounds; your CI runs your
  tests." (Note: the public copy has already required accuracy corrections twice
  — BACKLOG 20 and the callmed-landing fix — so this is a known-sensitive
  surface.)
- **Entangles item 22:** **no** — keeps it dormant on hosted (no execution).

### Option C — hybrids

- **C1 — pytest only, no node.** Python repos get real Gate 3; jest stays SKIP.
  Small image delta, avoids the +150-250 MB node layer. **Still entangles item
  22** for Python (`conftest.py` executes), just with a smaller blast radius —
  so still decide with item 22, but the sandbox scope is Python-only.
- **C2 — Option B now, with a visible caveat in the PR body.** Ship the graceful
  SKIP, and have the webhook include a line in the opened PR (or check-run) such
  as "Automated test suite was not executed in the hosted environment; please run
  your CI." Converts B's silent downgrade into *disclosed* behaviour, keeps item
  22 dormant, ships fast, and is cleanly upgradable to A once item 22-A's infra
  exists. Positioning stays honest without a code claim you can't back.
- **C3 — Option B now, but log a distinct gate_3 reason** ("runner unavailable in
  hosted image") separate from "no suite detected," so run-logs stay honest and
  you can *measure* how often a real suite was skipped before committing to the
  A/infra path. Cheapest way to buy the data that would later justify (or kill)
  Option A.

---

## 5. What item 22's A/B/C choice implies for each §5 option (the cross-matrix Yehor asked for)

| If item 22 →  | …then §5-A means | …then §5-B means |
|---|---|---|
| **22-A (sandbox)** | Coherent target state: runners execute untrusted code inside an offline, credential-stripped container. Needs Docker-capable host (absent on Fly) — real infra. This is the only combination where "we run your tests" is both true *and* safe. | Over-built: you'd have sandbox infra but nothing executing in it on hosted. Only sensible as staging toward a later A. |
| **22-B (env-strip)** | **Unsafe** — adversarial test code still runs same-uid with filesystem+network access (item 22 §6B residual risk); env-strip only hides credentials from the child, it does not contain execution. Do **not** pair A with 22-B. | Consistent and cheap: nothing executes, so strip's residual risk is moot on hosted. |
| **22-C (B-now, A-later)** | A rides on whenever 22's sandbox lands; until then A is unsafe (see 22-B cell). | Fine — both are "mitigate now, harden later." |

Read-out: **§5-A is only safe under 22-A.** §5-B is safe under any item-22 choice.
So the fast path (§5-B / C2) and the full-verification path (§5-A + 22-A + infra)
are the two internally-coherent bundles; mixing §5-A with 22-B is the trap.

---

## 6. HARD STOP

Nothing implemented. No option chosen. Nothing staged. No adversarial pass run on
this memo (that belongs to the eventual diff, not the scope).

**Decisions that are Yehor's, in the order they gate each other:**

1. **§5 fork: A, B, or a C-hybrid** — does Gate 3 *run* customer tests on hosted,
   or *skip-and-disclose*? This sets what "verified" means for hosted users.
2. **If A (or C1): item 22 A/B/C must be decided in the same change** — §3 proves
   A without item 22-A ships untrusted execution beside cross-tenant secrets.
3. **If B/C2/C3: a positioning/site-copy check** — confirm no public claim says
   hosted fixes are test-suite-verified; correct if it does.

The one honest warning (carried from the session brief): item 21's own fix is
trivial (thread the `github_token` param through `run_repo_pipeline`), so there is
a standing temptation to ship §5-B + item 21 next session and declare the hosted
path "fixed." That is fine **only if the §5-B positioning downgrade is a decision
made on purpose here**, not a side-effect of taking the easy path. Decide the
meaning deliberately; then the implementation is small either way.

---

## 7. DECISION — 2026-08-01 (Session 028): §5 = C2

The scope pass above hard-stopped without choosing (§6). This section is the
dated decision addendum; the scope is unchanged, the choice is now made.

**Decision: §5 Option C2** — graceful SKIP on runner-absent, WITH a visible
disclosure line in the PR body. Made deliberately, in writing, by Yehor.

**Reasoning (Yehor's, condensed):**
1. C2 is the only option that ships item 21's fix without touching item 22 —
   which is itself a two-decision, new-infrastructure project (no Docker-capable
   host on Fly today). Forcing item 22 now, under "the hosted path must work"
   pressure, is the wrong condition to decide it under. C2 lets the hosted path
   start working this week; item 22 gets decided on its own timeline.
2. The disclosure clause is the load-bearing part. Plain B stops doing what the
   docstring calls "verified" with nobody outside the codebase knowing. C2's
   PR-body caveat makes it visible and actionable — an honest, specific
   statement, deciding the positioning downgrade on purpose rather than shipping
   it silently.
3. Cheaply upgradable to A once item 22-A infra exists; forecloses nothing. Per
   the §5 cross-matrix, C2 is internally coherent under ANY item-22 choice.

**Item 22:** NOT touched. Stays correctly deferred, dormant, and undecided.

**Implementation scope (one arc, for the implementation session — run on a
machine where the full suite executes; §2 line-by-line + adversarial-pass
discipline, same as BACKLOG 19):**

1. `verifier.py` — SKIP-not-FAIL on runner-absent signature:
   - `_run_pytest`: detect "No module named pytest" / equivalent runner-absent
     signature → `GateResult(SKIP, ...)` instead of falling through to FAIL.
   - `_run_jest`: turn the `FileNotFoundError` branch (`verifier.py:789-790`)
     from FAIL into SKIP.
   - Keep existing SKIP triggers (`ModuleNotFoundError`/`ImportError`/"no tests
     ran") intact — this ADDS a case, does not replace them.
2. C2 disclosure clause — when Gate 3 SKIPs specifically because the runner was
   absent (not because no suite was detected), include a visible line in the
   opened PR body: "Automated test suite was not executed in the hosted
   environment; please run your CI." Distinguish from a plain "no suite detected"
   SKIP.
3. Item 21 — thread `github_token` through `run_repo_pipeline` so the PR
   publisher has a credential to push with (same arc/commit family; both must
   clear together).
4. Site-copy check (§6.3) — grep the live callmed-landing site for any claim that
   hosted fixes are test-suite-verified. If found, correct to e.g. "we confirm
   the fix removes the finding and stays in-bounds; when we can't run your suite,
   your CI does." If none found, say so explicitly rather than skip the check.

Full suite as gate. Item 22 is NOT touched.

**Two design notes surfaced this session (for the implementer, not new
decisions):**
- Steps 1+2 interact: reliably distinguishing a *runner-absent* SKIP from a
  *no-suite-detected* SKIP (both carry `gate_3.status == SKIP`) means keying the
  PR-body line off the gate_3 REASON, not the status. A distinct reason constant
  (C3's idea) is the robust way to do it and keeps run-logs measurable — worth
  adopting even under C2.
- Step 4 is a browser/live-web task (Chrome tools), not a repo grep — the "site"
  is the deployed callmed-landing page, not a file in this tree.

