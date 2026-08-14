# Patchward — Live Site-Copy Check (memo §7 step 4)

**Date:** 2026-08-11 (Session 033)
**Status:** DONE — found a real overclaim, corrections drafted here.
**Method:** live browser read of the rendered `https://callmedai.com`, not a repo grep.
**Note (2026-08-14):** this file was originally produced and reviewed entirely
within the guidance chat and was never saved to disk by any executor session —
it is being re-materialized here, verbatim from the original analysis, so a
real file exists to work from. No content has changed from the original.

---

## 1. What the check was for

Memo §7 step 4, from `memory/BACKLOG_S5_gate3_meaning_memo_2026-08-01.md`:

> Site-copy check (§6.3) — grep the live callmed-landing site for any claim that hosted fixes are test-suite-verified. If found, correct to e.g. "we confirm the fix removes the finding and stays in-bounds; when we can't run your suite, your CI does." If none found, say so explicitly rather than skip the check.

Background: the §5 fork was decided as Option C2 on 2026-08-01 — Gate 3 SKIPs gracefully when the test runner is absent in the hosted environment, with a disclosure line in the PR body. Implemented 2026-08-04 in `d72c0df`. That decision deliberately downgraded what "verified" means for hosted users. The site-copy check exists to confirm the public claims were downgraded to match.

**They were not, at the time of this check.**

---

## 2. Findings — two overclaims

### Finding 1 — the "Three-gate verifier" card (Patchward product section)

Live copy at time of check:

> **Three-gate verifier**
> Gate 1: re-scan confirms the rule no longer fires. Gate 2: diff bounds check confirms the edit is within the authorised lines. **Gate 3: test suite must pass. A fix that fails any gate is discarded — never pushed.**

Under C2, when the runner is absent Gate 3 returns SKIP, not FAIL. The fix is not discarded — it proceeds to PR with a disclosure line. So both halves of that sentence were false on the hosted path.

### Finding 2 — the FAQ answer

> Patchward runs five static analysis scanners (…), triages findings with an AI analyst, generates fixes, and **validates each one through a three-gate deterministic pipeline — re-scan, diff bounds, test suite — before opening a draft PR.**

Same overclaim, softer phrasing — asserts the suite ran unconditionally.

---

## 3. Proposed corrections (copy-ready — VERIFY STILL APPLICABLE before pasting live, per Step A note below)

### Replacement for Finding 1

> **Three-gate verifier**
> Gate 1: re-scan confirms the rule no longer fires. Gate 2: diff bounds check confirms the edit is within the authorised lines. Gate 3: your test suite runs when a runner is available in the environment. A fix that fails a gate is discarded — never pushed. When we can't execute your suite, we say so in the PR, and your CI is the backstop.

### Replacement for Finding 2

> Patchward runs five static analysis scanners (Semgrep, Bandit, pip-audit, Trivy, ESLint), triages findings with an AI analyst, generates fixes, and validates each one through a three-gate deterministic pipeline — re-scan, diff bounds, and your test suite where a runner is available — before opening a draft PR. Every PR states which gates ran; when the suite could not be executed in the hosted environment, the PR says so explicitly and your CI remains the final gate.

**Tone note:** "Every PR states which gates ran" is a *stronger* trust claim than the original absolute one — verifiable by the customer on first use, vs. the original being falsifiable on first use.

---

## 4. Secondary finding — stale figures (not an overclaim)

Site said "371 tests / 89% coverage" at time of check. Real current figure (as of Session 032/033): **565 passed / 3 skipped / 91.20% coverage**. Understated, not risky, but worth refreshing — ideally sourced live from the same `/facts` pattern `patchward-landing` now uses, rather than hand-typed again.

---

## 5b. Calibration correction (same day, 2026-08-11, before any fix shipped)

Severity was overstated in the original finding, corrected the same day: pilots are delivered by Yehor running the CLI directly against the customer's own repository, not the hosted webhook — which has zero real installations to date. Run locally, the customer's test runner IS present, so Gate 3 executes for real. **For every real customer to date, the original claim has been true.** The overclaim is latent (becomes false only once hosted-path pilots begin, which hasn't happened), not active. Still worth fixing before hosted launch — just not an emergency.

---

## 6. Board impact / status as of this re-materialization (2026-08-14)

- Memo §7 step 4 — check itself was completed 2026-08-11.
- **The copy fix described above was NEVER APPLIED** — `callmed-landing`'s actual current live content has not been re-checked since 2026-08-11. Before applying anything from Section 3, re-verify the live site still shows the same wording (three days have passed; it's possible it changed for unrelated reasons).
- Original scope note: `callmed-landing` is a separate repository from `Patchward` and `patchward-landing`, not mounted by default in most sessions.
