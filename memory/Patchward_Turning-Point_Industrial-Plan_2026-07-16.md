# Patchward — Turning-Point Industrial Plan

**Prepared:** 2026-07-16 (the turning point) · **Owner:** Yehor (solo founder / Directing Engineer) · **Planner role:** guidance model — plans, verifies, instructs; does not execute in the repo.

**Reading focus:** this document has one job — turn a validated engineering project into a validated *product in the world*, on a clock set by the market. Read Sections 1, 3, 6, and 7 first if short on time.

**Honesty note (per your own CR-3 / CR-8):** every number below is either sourced (market data, your own memory files) or explicitly labelled *estimate — judgment call*. Nothing here is presented as verified that isn't.

---

## 1. Verified product state (as of 2026-07-16)

This is the "define the verified product state" deliverable. Each line is drawn from your own committed memory/docs, not assumed.

**What Patchward is (verified).** A local-first, multi-repo security agent. It scans code with seven scanners (Semgrep, Bandit, pip-audit, ESLint, npm audit, Trivy, OSV-Scanner), an LLM sub-agent (Haiku) drafts a patch, a **deterministic, no-LLM Verifier** checks it against three gates, and it opens a **draft** GitHub PR for a human to review. CLI via Typer: `patchward scan | fix | batch`. Python 3.12, uv, SQLite state store, OTel→Langfuse tracing. Repo: `github.com/yehorcallmedai-maker/Patchward` (renamed from RepoMend on 2026-07-07 because repomend.com is a live competitor).

**What is built and proven (verified).**
- Core scan→fix→verify→PR pipeline: complete through the original Phases 0–7.
- Tests: **461 passed, 2 skipped, 90.46% coverage**, run on your own machine 2026-07-15 (Tier 0). Threshold 80% cleared.
- A real Verifier bug was found and closed 2026-07-14 (commit `b2559a5`): a broken fix that deleted a still-referenced import passed all three gates. Fixed with an AST-based check; regression + 8 unit tests added. *This is important context for the market section — it is exactly the "AI slop" failure mode, caught by your own gate.*
- GitHub App + Marketplace-billing work stream exists (`webhook.py`, `github_app_auth.py`, `installations_db.py`), deployed live on Fly.io (`patchward-webhook.fly.dev`, `/healthz` OK, re-checked twice 2026-07-15). HMAC signature validation is timing-safe (`hmac.compare_digest`).
- Phase 8 (State Reconstruction Audit): closed, tagged `state-audit-2026-07`.

**What is NOT yet done (verified gaps — these define the runway).**
- **No end-to-end validation against a real third-party repo.** The pipeline has run on the fixture; a real external target (Stage 2 E2E) has not been completed. This is the single most important missing proof.
- **Not on PyPI.** Install is from source only. Trusted-Publisher CI is scaffolded but the OIDC environment-name (`pypi` vs. "Any") may mismatch and fail the first publish — unverified (item 9).
- **Landing site still says RepoMend** — 34 "RepoMend" hits, 0 "Patchward" (item 8).
- **No Marketplace listing.** Phase 10 gate not started; a *paid* listing needs an org-owned, publisher-verified account.
- **CRA/GDPR legal classification unresolved** (item 12) — needs qualified legal input, not a lookup.
- One real-world signal already arrived and was negative: fix PRs #359/#360 to `jtesta/ssh-audit` were rejected 2026-07-03 as "AI slop." *Treat this as the most valuable data point you have — see Section 3.*

**One-line verified status:** *A tested, working, scanner-agnostic autofix engine with a live webhook, that has never been proven on a real outside repo, isn't installable by a stranger, and whose public face still carries the old name.*

---

## 2. The wave and the entry point (market analysis → your deadline)

You asked me to define the deadline from market analysis rather than pick one. Here it is, with the evidence.

**The wave is real and current.** AppSec in 2026 has shifted from "find and triage" to "detect and act" — autonomous security patching is now its own category. Funded leaders: Pixee (publishes a 76% merge rate across 12+ scanners), Mobb (multi-scanner), Corgea, plus vendor-locked entrants (GitHub Copilot Autofix, Snyk Agent Fix, Veracode Fix). This is a crowded, well-capitalised space — so you do not win by being "an autofix tool." You win on a wedge.

**Your wedge (corrected after verification — see Addendum).** The originally drafted wedge ("GitHub sunset third-party SAST support in Oct 2025") came from a competitor's blog and **failed independent verification**: GitHub's own changelog shows partner-tool Autofix support being *added* (Oct 2024: ESLint first; JFrog SAST and Black Duck Polaris announced). The verified wedge is narrower but real: **Copilot Autofix is CodeQL-centric with only a short partner list — Semgrep, Bandit, pip-audit, Trivy, and OSV-Scanner are not on it.** Teams running those scanners (the dominant OSS stack) get no in-GitHub autofix for their findings. Patchward is scanner-agnostic across exactly that stack, verifies deterministically, and opens draft PRs. Concrete and defensible — just state it precisely.

**New threat, 6 days old (verified).** GitHub launched **agentic autofix in public preview on 2026-07-10** — it explores files, proposes a fix, and *reruns CodeQL to confirm the fix closes the alert*. Two readings: (a) it validates Patchward's core thesis (verify the fix, don't just generate it) at the platform level; (b) it compresses the window — GitHub is moving toward exactly this pattern, still CodeQL-only for now. This strengthens, not weakens, the case for the September window: enter while "verified autofix for non-CodeQL scanners" is still open ground.

**The timing anchor (hard external date).** EU **Cyber Resilience Act vulnerability-reporting obligations become binding 11 September 2026** (24h early warning / 72h full / 14-day final report). This puts fast, *trustworthy* remediation on every EU-touching team's agenda right now, and the security press is running a countdown. That date is ~8 weeks away.

**The live landmine.** The market's loudest current failure mode is AI-generated security PRs rejected as "slop" — maintainers reject incomplete or wrong fixes, and research confirms many agent PRs fail human/CI review. You already walked into this once (ssh-audit). Your deterministic Verifier + draft-only + human-review posture is the *answer* to this — but only if the first public fixes are visibly correct.

**Entry decision.** The wrong move is to launch loudly now: unproven on real repos + "slop" reputation risk + old name on the site = walking into the exact wall that already stopped you. The right entry point is a **gated launch timed to the pre-CRA urgency window**, roughly **1–8 September 2026**, so your public proof lands while buyers and press are primed. That sets the horizon.

> **IMPORTANT: Derived deadline — LAUNCH-READY by Tue 1 Sep 2026; public launch window 8–11 Sep 2026 (riding the CRA news cycle). Working horizon = ~8 weeks to launch (~6.5 weeks to launch-ready).** This is an *estimate — judgment call* built on the two sourced dates above; revisit it at the end of Sprint 2 (Section 6) when Stage-2 proof either exists or doesn't. If Stage-2 validation isn't done by ~20 Aug, the launch slips, not the quality bar.

---

## 3. What "success" honestly looks like — per step and long term

**Per step (the ladder, each rung an honest bar):**

| Step | Success means (honest) | The failure it's guarding against |
|---|---|---|
| Phase 9 — Hosted-Surface Hardening | Every Exposure-Gate item *proven by a test*, not just present: timing-safe HMAC, deny-by-default events, body-size limits, secrets in Fly with a rotation note, per-delivery logging, pip-audit clean on webhook deps. | A live public endpoint with unproven security. |
| Stage 2 E2E — the keystone proof | **One real third-party repo: scan → fix → verify → draft PR, and the fix genuinely passes your own line-by-line review + the repo's CI.** Not auto-merged. | "AI slop." This one step is what separates you from the reject pile. |
| Phase 10 — Marketplace Readiness | Free listing path chosen; install flow works; all `marketplace_purchase` events handled; privacy policy + support contact present. | Charging before the install flow is proven. |
| Distribution readiness | `pip install patchward` works for a stranger; site says Patchward (0 RepoMend); Marketplace free listing live. | Launching something nobody can actually install or trust. |
| First real-world signal | **Any one of:** a maintainer merges or seriously engages a Patchward draft PR; a stranger installs from PyPI; a first Marketplace install; a Show HN with substantive positive engagement. | Building forever with zero outside contact. |

**The "real outcome from the world" you asked for** is the last rung: *one* unsolicited external user, or *one* merge-quality PR accepted by someone who isn't you. That is the confirmation of value — not revenue yet. Design everything to reach that single signal fastest.

**Long-term (12+ months, realistic — not hype).** A credible good outcome is a small but real base of teams running Patchward in CI for scanner-agnostic, verified, human-in-the-loop autofix — a defensible reputation for "fixes that pass review" (low slop rate), a handful of paying Marketplace installs, riding the CRA tailwind. The honest ceiling for a solo founder in a funded category is a strong *niche* plus reputation — which can mature into a sustainable micro-SaaS, a portfolio-defining OSS project, or an acqui-hire. It is not "beat Snyk." Naming that plainly is what keeps the plan real and keeps you from measuring yourself against the wrong yardstick.

**On not losing interest (you named this explicitly).** Motivation dies when the payoff is one far-off event. So the plan is built to emit *visible, compounding proof* on a weekly cadence — a merged PR, a star count, a download number, a closed gate — so every week returns a small signal from the world, not just from you. The metric board in Section 8 is the antidote to the interest problem.

---

## 4. Scenarios that increase the success rate

Ranked by leverage. Each is an *estimate — judgment call*; treat as strong hypotheses.

1. **Lead with the coverage-gap wedge (corrected wording).** Message #1: *"Verified autofix for the scanners Copilot doesn't cover — Semgrep, Bandit, pip-audit, Trivy, OSV."* Concrete, current, and it survives a fact-check. Everything else is secondary.
2. **Turn the ssh-audit rejection into your proof, not your scar.** Publish the deterministic-Verifier story *with* a real merged PR beside it: "here's the class of broken fix our gate rejects (the import bug), here's a fix that passed review." You already have the raw material.
3. **Time the public launch to the CRA cycle (8–11 Sep).** Free press attention, primed buyers.
4. **Zero-config CI path.** `pip install patchward`, one command, runs in GitHub Actions with near-zero setup — this is literally the adoption criterion the market selects on (actionable output, actively maintained, no plugin ecosystem needed).
5. **Draft-PR-only, human-review as a headline feature.** After the slop backlash, the market *wants* this posture. Sell the restraint.
6. **Pick low-slop first targets deliberately.** For your first public PRs, choose findings your Verifier is strongest on (real, reachable, single-file fixes) — not the informational rules (like B404) whose only "fix" is deletion. First impressions set the reputation.
7. **Keep the momentum board public** (stars, downloads, merged PRs). Compounding visible proof is both marketing and your own motivation fuel.

---

## 5. Questions that must be closed before distribution starts

This is the pre-launch gate. Do not open distribution until each **Blocking** item is answered YES with evidence.

| # | Question | Status today | Gate |
|---|---|---|---|
| Q1 | Has Patchward produced ≥1 correct, review-passing fix on a **real third-party repo**? | No (Stage 2 not done) | **Blocking** |
| Q2 | Is the Verifier's real-world false-pass rate acceptable — is the import-bug *class* fully closed, or are there siblings? | Partially (one instance fixed 2026-07-14) | **Blocking** |
| Q3 | Is the landing site fully renamed to Patchward (0 RepoMend hits)? | No (34 hits) | **Blocking** |
| Q4 | Can a stranger install it? (PyPI publish chain proven; OIDC env-name mismatch resolved) | No | **Blocking** |
| Q5 | Legal: does Patchward fall in CRA scope, and are patch-liability disclaimers in place ("draft PRs, human reviews, no warranty on fixes")? | No (item 12, needs counsel) | **Blocking for EU positioning** |
| Q6 | Is the live webhook's security posture fully proven (Exposure Gate)? | Partial | **Blocking (it's already public)** |
| Q7 | Marketplace: personal vs org account decided; free-first path chosen; all `marketplace_purchase` events handled? | No | Blocking for Marketplace only (not for PyPI/OSS launch) |
| Q8 | What is the ONE-LINE claim and the ONE metric you'll show at launch? | Not set | **Blocking for messaging** |

---

## 6. The session-by-session plan (daily 30–60 min cadence)

**Cadence assumption:** daily short sessions, ~4–5/week. Over ~8 weeks that's ~32–40 sessions. The plan is organised into **four ~2-week sprints**. The governing rule that keeps a solo founder alive on a daily cadence:

> **Every session closes exactly ONE definition-of-done (mandatory). Up to 2 further micro-tasks are *stretch*, taken only if time remains. One clear finish per day beats five half-finished threads.**

This is deliberate: your own BUILD_PLAN diagnosed that the previous process died because it *priced every unit of work at full ceremony*. This plan prices a session at one closed thing.

### Sprint 1 (Weeks 1–2) — Prove it works on the real world · **Goal: Stage 2 E2E passes**

| Session | Mandatory definition-of-done (1) | Stretch (≤2) |
|---|---|---|
| S1 | Finish Phase 9 Exposure Gate: pick the ONE remaining unproven item and add a test that proves it. | pip-audit on webhook deps; log a delivery ID. |
| S2 | Close Q2: audit `verifier.py` for *siblings* of the import-bug class; write down what's covered vs. not. | Add one guard test. |
| S3 | Choose the Stage-2 target repo (real, small, a finding your Verifier is strong on). Write a 5-line mini-INTAKE. | Dry-run scan only. |
| S4 | Run scan→fix→verify on the target; inspect the draft locally. **Do not open the PR yet.** | — |
| S5 | Review the fix line-by-line yourself; decide pass/fail against "would a maintainer merge this?" | — |
| S6 | If pass: open the real draft PR (your hands on git, not the sandbox). If fail: log why, return to S4. | — |
| S7 | Write the Stage-2 keystone report: what worked, what didn't, evidence (hashes, PR URL). | — |
| S8 | **Sprint-1 reevaluation (full checkpoint).** Stage-2 passed? If not, this is the STOP-and-rethink gate. | Update STATE/BACKLOG. |

**Must be closed for sure by end of Sprint 1:** Phase 9 gate proven; Q2 answered; **one real draft PR that you'd stake your name on** (or a documented, honest reason Stage 2 failed and a decision on the Verifier approach).

### Sprint 2 (Weeks 3–4) — Make it installable & legal-safe · **Goal: a stranger can install it; legal risk known**

| Session | Mandatory definition-of-done (1) | Stretch |
|---|---|---|
| S9 | Resolve Q4: fix the PyPI OIDC env-name mismatch; confirm `publish.yml` identity will match. | — |
| S10 | Trigger a `workflow_dispatch` publish to a TestPyPI or a real dry-run; prove the chain. | — |
| S11 | First real PyPI publish; verify `pip install patchward` from a clean environment. | Version-tag hygiene. |
| S12 | Write the CRA/GDPR legal-question brief for counsel (scope + patch-liability disclaimer). | — |
| S13 | Get the legal brief in front of a qualified person (async is fine); log the open question. | — |
| S14 | Draft the patch-liability / no-warranty disclaimer text for the repo + site. | — |
| S15 | Buffer / overflow session (protect one for slippage — there will be slippage). | — |
| S16 | **Sprint-2 reevaluation + revisit the launch date** (Section 2). Is 1 Sep still real? | — |

**Must be closed for sure by end of Sprint 2:** Patchward installable from PyPI by a stranger (Q4 YES); legal question formally posed (Q5 in motion); launch date confirmed or consciously moved.

### Sprint 3 (Weeks 5–6) — Make it findable & trustworthy · **Goal: public face is correct and the story is written**

| Session | Mandatory definition-of-done (1) | Stretch |
|---|---|---|
| S17 | Close Q3: landing site RepoMend→Patchward, every hit (target: 0 RepoMend). | — |
| S18 | Rewrite the site/README hero around the corrected wedge: "Verified autofix for the scanners Copilot doesn't cover." | — |
| S19 | Set Q8: the one-line claim + the one metric (e.g., "N verified fixes, all draft, human-reviewed"). | — |
| S20 | Write the launch narrative: the Verifier-vs-slop story + the ssh-audit case study + the merged PR. | — |
| S21 | Marketplace decision (Q7): free-first, personal-vs-org; handle `marketplace_purchase` events. | — |
| S22 | Create the free Marketplace listing draft (privacy policy, support contact, description). | — |
| S23 | Dry-run the full install flow as if you were a new user; fix the worst friction point. | — |
| S24 | **Sprint-3 reevaluation.** Are all Blocking gate questions (Section 5) green except launch-day ones? | — |

**Must be closed for sure by end of Sprint 3:** site fully renamed (Q3 YES); wedge messaging + one-line claim set (Q8 YES); Marketplace free listing drafted; the launch story written with real evidence.

### Sprint 4 (Weeks 7–8) — Launch into the wave · **Goal: first real-world signal**

| Session | Mandatory definition-of-done (1) | Stretch |
|---|---|---|
| S25 | **Go/No-Go gate:** walk Section 5. Any Blocking = NO still red → fix or slip. Record the decision. | — |
| S26 | Publish the free Marketplace listing (once install flow proven). | — |
| S27 | Prepare the Show HN / dev-community post; schedule for the CRA window. | — |
| S28 | Open 2–3 more high-quality real draft PRs to well-chosen repos (build the evidence base). | — |
| S29 | **Launch day (target 8–11 Sep):** post, listing live, PyPI live, site live. | — |
| S30 | Watch and respond: engage every reply/issue/PR comment within the day. | — |
| S31 | Capture the first real-world signal (or its absence) honestly; write it down. | — |
| S32 | **Post-launch reevaluation:** what the world actually said → next horizon. | — |

**Must be closed for sure by end of Sprint 4:** Go/No-Go recorded; public launch executed *or* consciously deferred with a reason; **first real-world signal captured** — the outcome you set out for.

---

## 7. Which system to run this on — Keystone Ledger, or what you already built?

**Short answer: do NOT adopt the full Keystone Ledger v2.0.0 for Patchward. Keep the two-speed system you already designed, and bolt on three small parts of Keystone. Keep Keystone Ledger as a reference philosophy, not a daily operating harness.**

**Why (from your own evidence, not my preference).** Your `BUILD_PLAN_2026-07-10.md` §5 diagnosed exactly this: *"the INTAKE/Keystone process didn't fail because it was a bad idea — it failed because it priced every unit of work at full ceremony. Under the time pressure of a product pivot, the price stopped being paid at all, and the process died completely."* Keystone Ledger v2 is *more* ceremony, not less: nine RISK-GATE gates, four simulated roles, context-isolated verification, ATTEST reports, EVOLVE entries with N=5 samples per change. Running that on a daily 30–60 minute cadence would consume the whole session in bookkeeping and re-create the failure that already stopped you once. On a solo, short-session cadence, ceremony is the enemy of continuity.

**What you already have that's better-fit** (from BUILD_PLAN §4): a two-namespace memory with an enforced claimed-vs-verified boundary (`STATE.md` = verified only; `WORKLOG.md` = agent-claimed), a **trust-tier protocol** (Tier 0 content-addressed / Tier 1 authenticated / Tier 2 proxied-never-alone) that is a *sharper* version of Keystone's verification-honesty rule, **two-speed gating** (full ceremony only at phase boundaries; lightweight CI for routine work), and the **Directing Engineer** rule ("anything irreversible or externally visible is yours; anything reversible and sandboxed is delegable") which already encodes Keystone's Critical-Actions idea in one sentence a tired founder can actually follow.

**What to *borrow* from Keystone (three bolts, not the cathedral):**
1. **INTAKE contract — but only at the four sprint boundaries and the Go/No-Go gate**, never per task. The 5-line mini-INTAKE in S3 is the daily-scale version.
2. **A distilled RISK-GATE — three lines, not nine** — used only before an irreversible/external action (open a real PR, publish to PyPI, go live): *(a) does it match the definition of done; (b) is every external claim Tier 0/1 verified; (c) is this a Directing-Engineer action needing your own hands?*
3. **The EVOLVE habit — one process change at a time, with a rollback note** — applied to *this plan itself*, logged in WORKLOG, so the system improves without churn.

**Net:** you don't need to build something better than Keystone, and you don't need to run Keystone. You already built the right-sized system for this exact situation; the task is to *actually use it* and stop letting either extreme (full ceremony / no process) win. Section 9 gives the updated instructions that encode this.

---

## 8. The one-screen momentum board (check every session; the antidote to losing interest)

Keep these six numbers visible. They convert an 8-week grind into weekly signals from the world.

- **Real draft PRs opened** (quality ones) — target: ≥1 by end of Sprint 1, ≥4 by launch.
- **Merge-quality rate** — of your opened PRs, how many you'd stake your name on / that get engaged.
- **PyPI installs / downloads** — 0 until Sprint 2; any non-zero from a stranger is a signal.
- **GitHub stars** — vanity, but a real weekly pulse.
- **Blocking gate questions closed** (Section 5) — X of 8.
- **First real-world signal** — the binary that ends the plan: yes/no.

---

## 9. Reevaluation checkpoints (where the plan is allowed to change)

- **End of every sprint (~2 weeks):** full checkpoint — is the sprint goal met, is the next sprint still right, is the launch date still real.
- **Hard STOP-and-rethink after Sprint 1 if Stage 2 fails twice:** if two honest attempts can't produce a merge-quality fix on a real repo, the Verifier/Fix-Gen approach — not the schedule — is what to reconsider. This is the most likely place the whole thesis gets tested.
- **Sprint 2 launch-date reconfirmation:** the 1 Sep date is a market estimate; if the proof isn't there, the date moves, the quality bar doesn't.
- **Go/No-Go before distribution (S25):** Section 5's Blocking questions are the gate. Red means slip.
- **Post-launch (S32):** the world's response resets the horizon.

---

*Numbers audit (CR-8): CRA binding 11 Sep 2026 — multi-source confirmed (EC digital-strategy page + two law firms). Copilot Autofix partner list (ESLint first; JFrog/Black Duck announced) and agentic-autofix preview (2026-07-10) — GitHub's own changelog. Pixee's 76% merge rate — self-reported vendor marketing, unverified. Project facts (461 tests, commit hashes, item numbers) — your committed memory files. The 1 Sep launch date, the horizon, all per-session groupings, and all long-term outcomes are explicitly estimates — judgment calls, to be revisited at the checkpoints above.*

---

## Addendum — Verification pass, 2026-07-16 (same day)

Run at your request ("verify + adjust"). Two passes: external claims re-checked against independent sources; internal consistency re-checked against the calendar and your memory files.

**REFUTED and corrected:**
- *"GitHub sunset third-party SAST support for Copilot Autofix in Oct 2025"* — sole source was Pixee's blog (a competitor; Tier 2 under your own rules). Two independent search passes found no such announcement; GitHub's own changelog shows partner support being **added** (2024-10-29: ESLint; JFrog SAST and Black Duck Polaris announced). Section 2, Section 4 item 1, S18, and the launch messaging were all rewritten to the verified, narrower wedge. **This was load-bearing — the kind of error that would have been embarrassing in launch copy.**
- *"Mon 1 Sep 2026"* — 1 Sep 2026 is a **Tuesday**. Fixed.

**NEW material fact found:**
- GitHub **agentic autofix public preview, 2026-07-10** (explores files, proposes fix, reruns CodeQL to confirm). CodeQL-only for now. Read: thesis-validating but window-compressing. Incorporated into Section 2.

**CONFIRMED:**
- CRA reporting obligations binding **11 Sep 2026** — European Commission page + two independent law-firm alerts. The timing anchor holds.
- `patchward-webhook.fly.dev/healthz` → `{"status":"ok"}` — live direct HTTPS fetch, this session.
- PyPI: no published `patchward` project found (JSON endpoint returns no project) — consistent with "not yet published"; the name does not appear taken. *Weak-positive evidence — confirm from your own machine when you run item 9.*
- Project facts (461 tests / 90.46%, commit `b2559a5`, items 8/9/12, 34 RepoMend hits) — consistent with your memory files as cited; per your own rules these remain claims to re-verify on your machine, not re-verified here.

**Judgment unchanged after verification:** the September window, the sprint structure, the session task loads, and the Keystone recommendation all stand. Only the wedge wording and the day-of-week were wrong.*
