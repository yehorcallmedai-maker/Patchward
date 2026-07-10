# Patchward — Industrial-Grade Organization Build Plan
**Synthesized from three independent deep-research runs, 2026-07-10.**
**Status: proposed — awaiting your review/edits before Part 1 execution begins.**

---

## 0. How this was built (read before trusting anything below)

Three independently commissioned research reports answered the same brief. This
document reconciles them into one plan, not three summarized side-by-side. Where all
three converged, confidence is high and I present a single recommendation without
hedging. Where they diverged, I made an explicit judgment call and say so — you should
override any of those calls that don't sit right with you; they're not settled facts.

I also spot-checked the two most consequential *factual* claims before building them
into this plan, rather than taking any report's citations on faith:

- **EU Cyber Resilience Act reporting timeline** (Report 2's claim: 24h early warning,
  72h full notification, 14-day/1-month final report, via ENISA's Single Reporting
  Platform, binding from 2026-09-11) — **confirmed independently**, current as of this
  check. What I could *not* independently confirm is which CRA Annex/Class Patchward
  specifically falls under — that's a legal classification judgment, not a lookup, and
  I've flagged it below as requiring actual legal confirmation rather than asserting it.
- **AGENTS.md as a cross-tool standard** (Report 3's claim) — **confirmed**, with one
  correction: Claude Code specifically reads `CLAUDE.md`, not `AGENTS.md`, natively. The
  correct pattern (which I've built into Part 2) is a one-line `CLAUDE.md` that imports
  `AGENTS.md`, so you get one shared file that every tool — including Claude — reads.

**Convergence signal worth naming explicitly:** all three reports, independently,
landed on the same backlog sequencing (validate the pipeline end-to-end before
building more features, using a safe/controlled target before a real third-party
repo) and the same core mechanism for the informational-gap problem (split "what the
agent claims" from "what's verified," and never let an unauthenticated/proxied
network read be the sole basis for a decision). That's three-for-three agreement from
independent runs — treat those two conclusions as load-bearing.

---

## 1. Operating principle (the one sentence that generates the rest of this plan)

**Treat project state exactly like Patchward treats a Fix-Gen patch: agent-drafted,
deterministically verified, human-signed, content-addressed where possible.**
Every recommendation below is this principle applied to a different surface —
documentation, verification, prioritization, and your own role. This framing came
from Report 3 and is the strongest organizing idea across all three reports: it means
you don't have to invent a new philosophy for project management, you already built
and validated one, you just stopped applying it to your own process.

---

## 2. Your role: Directing Engineer

**Adopted title:** *Directing Engineer.* One title, one bright-line rule — deliberately
not three overlapping titles ("Technical Director / Product Owner / Verifier"), because
a single unambiguous boundary is what actually gets followed under time pressure, and
"under time pressure" is exactly the condition that caused the current gap.

**The rule:** *Anything irreversible or externally visible is yours. Anything
reversible and sandboxed is delegable.*

| Decision/action class | Owner | Why |
|---|---|---|
| What to build, why, and the acceptance criteria (INTAKE scope) | You (agent may draft, you approve) | No stake, no ownership |
| Pushing to the real git remote, deploying, opening real PRs, spending above a per-session cap, publishing, DNS/billing changes | You execute or explicitly authorize each instance | Matches the human-mediated-remote pattern you already run |
| Promoting a claim from "agent said so" to "verified project state"; ADR acceptance; Keystone sign-off | You (or CI, where the check is deterministic) | This is the Verifier-equivalent role for project state |
| Implementation inside a signed INTAKE; tests; refactors; git archaeology; drafting ADRs/logs; research | The agent | Reversible, sandboxed, checkable |
| Any diff touching a security boundary (hooks, egress policy, credential proxy, webhook signature validation) | You review line-by-line, always, no skimming | The one review class where "looks fine" isn't good enough |

---

## 3. Immediate action: the State Reconstruction Audit (do this first, ~half a day)

**Goal:** produce a small, fixed set of artifacts that let a fresh agent session
answer "what phase are we in, what's actually deployed, what currently passes, what's
next" from files alone, every answer backed by evidence. Not a diary of the last three
weeks — a snapshot of *as-built* reality, because the sessions that did the work are
gone and git is a better witness than memory.

**Deliverables (exactly these five, no more — a capped list is what keeps this to half
a day):**
1. A git tag marking the audit boundary, e.g. `git tag state-audit-2026-07 HEAD`
2. `memory/STATE.md` — see template in Appendix A
3. 4–6 retroactive ADRs in `docs/adr/` (MADR format) covering only decisions that are
   still binding and would surprise a future reader: the RepoMend→Patchward rename,
   adopting FastAPI/Uvicorn/PyJWT for the webhook, deploying to Fly.io, the product
   shift toward installable GitHub App + Marketplace billing, and the PyPI Trusted
   Publisher path. Mark each `status: accepted (retroactive, reconstructed from git
   archaeology, 2026-07-10)` — be honest about the artifact's own provenance.
4. One Consolidated Keystone Report in `docs/keystones/` covering 2026-06-23 →
   2026-07-09 as a single unit (not eight separate reports) — what was built, evidence
   (commit hashes, live URLs), what was *not* verified, known debt.
5. A priority-ordered `memory/BACKLOG.md` (seeded from Part 5 of this plan)

**Procedure:**
1. `git log state-audit-2026-07^..v0.1.0-or-equivalent --stat` (or, if no v0.1.0 tag
   exists, `git log --since=2026-06-23 --stat`) to enumerate every file added,
   modified, or renamed in the gap window.
2. Cluster the commits into work-streams by inspection — this project's gap window
   clusters cleanly into: rename, webhook/billing, Fly deployment, CI/PyPI scaffolding.
   For each new component (`webhook.py`, `github_app_auth.py`, `installations_db.py`,
   `webhook.Dockerfile`, `fly.toml`), have the agent draft a one-sentence purpose
   summary; you edit/approve rather than write from scratch.
3. **Re-derive current facts by re-running things today, never by trusting old
   numbers.** Test count and coverage: `uv run pytest --cov`, run now. Deployment
   state: `fly status` / a live `/healthz` probe, run now, from your own machine (not
   through a proxied agent path — see Part 4). The old "371 tests, 89%" figure is a
   historical fact about the pre-rename state, not a claim about today.
4. Write the retroactive ADRs and the Consolidated Keystone Report from the clustered
   commits, citing commit hashes for every factual claim.
5. Tag, commit, done. This audit itself becomes the first entry under the new regime.

---

## 4. Memory & verification infrastructure

### 4.1 Two-namespace memory, with an enforced epistemic boundary

The root cause of the "resolved work reported as unresolved" incident wasn't
carelessness — it was that *claimed* state and *verified* state shared one file with
no marker distinguishing them. Fix this structurally, not by trying harder:

- **`memory/STATE.md`** — verified facts only. Every entry carries an evidence tuple:
  `(claim, evidence command or hash, date checked, verified by: you/CI)`. The agent may
  *read* this file freely. **The agent never writes to it directly** — it proposes
  updates in WORKLOG, and only you (or a deterministic CI check) promote an entry into
  STATE.
- **`memory/WORKLOG.md`** (or a `memory/sessions/YYYY-MM-DD.md` per-session log,
  either works) — agent-claimed, cheap, append-only. This is where "I did X, here's
  the commit hash, I have not independently verified Y" lives.

This is not busywork for its own sake — it's the same claimed-vs-verified split
Patchward already enforces on Fix-Gen's output via the deterministic Verifier, applied
to project bookkeeping instead of code.

### 4.2 One instruction file, correctly wired for Claude specifically

Adopt **`AGENTS.md`** at the repo root as the single, cross-tool instruction file
(this is a genuine, widely-adopted 2026 convention — confirmed independently, not just
asserted by the research). Keep it small: coding conventions, the trust-tier rules
from 4.3, the session rituals from Part 6, and *pointers* to STATE.md/BACKLOG.md rather
than their contents inline.

**Correction to bake in:** Claude Code does not read `AGENTS.md` natively — it reads
`CLAUDE.md`. The correct setup, confirmed independently, is a `CLAUDE.md` whose entire
content is one import line:
```
@AGENTS.md
```
This gets you one real source of truth that every tool (Claude, and anything else you
adopt later) reads identically, instead of two files silently drifting apart — which
is exactly the failure mode that already bit this project once.

### 4.3 Trust-tier verification protocol (`memory/VERIFICATION.md`)

This directly encodes the lesson from the 2026-07-10 incident (a proxied,
unauthenticated `api.github.com` read silently served stale data and was trusted as
ground truth). All three research runs converged on a tiered-trust model; this is the
merged version:

| Tier | What's in it | Rule |
|---|---|---|
| **Tier 0 — deterministic/content-addressed** | git commit hashes, file digests, local exit codes, `git ls-remote` against the real remote | Accept as-is; this is what actually resolved the July 10 incident |
| **Tier 1 — authenticated direct reads** | Authenticated API calls on a non-shared path, `fly status` with credentials, GitHub web UI while logged in | Accept with evidence attached; spot-check weekly |
| **Tier 2 — proxied / unauthenticated / cached / rate-limited** | Any read made through the agent's sandboxed network path, including `api.github.com` reads made by an agent session | **Never sufficient alone for a gating decision.** Must be labeled `UNVERIFIED (tier-2)` and cannot be promoted to STATE.md without a Tier 0/1 confirmation |

**Standing rule:** for any claim about external state that gates a real decision, two
independent paths must agree (e.g., agent's read + your `git ls-remote`) or the claim
stays `UNVERIFIED`. This is now written down instead of improvised per-incident.

**Verifier ≠ implementer, at the meta level too.** Just as Fix-Gen doesn't grade its
own patches, the agent that did the work is not the one that gets to declare the
project-state claim confirmed — that's either CI, a fresh agent session with no stake
in the prior narrative, or you.

### 4.4 The complete artifact set — capped at seven

`AGENTS.md` (+ one-line `CLAUDE.md` import), `memory/STATE.md`, `memory/WORKLOG.md`,
`memory/BACKLOG.md`, `docs/adr/`, `docs/keystones/`, `memory/VERIFICATION.md`. Adding
an eighth requires deleting one. A hard cap is what keeps a documentation system alive
for one person — sprawl is how these systems die, and it's arguably how the pre-rename
one did.

---

## 5. Phase-gate redesign: why the old process died, and the fix

**Diagnosis (all three reports agree on the mechanism, even where they differ on
naming):** the INTAKE/Keystone process didn't fail because it was a bad idea — it
failed because it priced *every* unit of work at full ceremony. Under the time
pressure of a product pivot, the price stopped being paid at all, and the process
died completely rather than degrading gracefully.

**Fix: two-speed gating.**
- **Full INTAKE + Keystone ceremony** — reserved for phase boundaries and direction
  changes (exactly the kind of thing the webhook/billing pivot was).
- **Lightweight continuous gate** — for routine work: CI (tests + lint + security
  scan) plus the "docs travel with code" rule below. No ceremony, but not undocumented
  either.

**"Docs travel with code" rule:** any commit that changes a public interface, security
boundary, dependency, deployment target, or introduces spend must include either an
ADR or a WORKLOG entry *in the same commit*. Enforced by a pre-commit hook or CI grep,
not by discipline — discipline is what failed last time.

**Restart the phase counter honestly, with new gate types your local-CLI-era process
never needed:**

- **Phase 8 — Reconciliation.** The State Reconstruction Audit (Part 3). Already
  scoped above.
- **Phase 9 — Hosted-Surface Hardening.** New gate type: **Exposure Gate**, applied
  retroactively since `/webhook` is already live. Checklist:
  - `X-Hub-Signature-256` HMAC validation using a **timing-safe comparison**
    (Python's `hmac.compare_digest`, not `==`) — proven by a test, not just present in
    code
  - Deny-by-default handling of unrecognized webhook event types
  - Rate limiting / request body size limits on the FastAPI surface
  - Secrets live in Fly secrets, never in `fly.toml` or the image, with a rotation note
  - Structured logging of every webhook delivery ID (needed for both debugging and any
    future incident report)
  - `pip-audit` run against the `webhook` optional-dependency group specifically
- **Phase 10 — Marketplace Readiness.** New gate type: **Billing/Exposure-for-Payment
  Gate**. Checklist:
  - Handle all `marketplace_purchase` event types (new purchase, upgrade, downgrade,
    cancellation, free trial) — GitHub requires this for any paid listing
  - **A paid Marketplace listing requires an organization-owned, publisher-verified
    account** — a personal-account app must be transferred to an org first. Sequencing
    implication: list free first, defer org-transfer/verification, validate the
    installation flow before taking payment.
  - Privacy policy, support contact, pricing plan present before submitting for review
  - Confirmed process for notifying GitHub within 24h of a confirmed security incident
    on the app
  - A written SLO you actually accept — "best-effort, no pager" is a legitimate SLO if
    it's stated — plus external uptime monitoring on `/healthz` with alerting to you,
    and a one-page incident runbook

### Regulatory flags — verify with a professional before relying on these

Two real compliance regimes plausibly apply once Patchward is a hosted product with a
billing surface. I independently confirmed the mechanics below; I did **not**, and
cannot, independently confirm exactly how they apply to Patchward's specific product
classification — that needs an actual legal read, not a research-agent's opinion:

- **EU Cyber Resilience Act (CRA).** Confirmed, independently: manufacturers of
  products with digital elements must submit an early warning within **24 hours** of
  becoming aware of an actively exploited vulnerability or severe incident, a full
  notification within **72 hours**, and a final report within **14 days** of a fix
  (or one month for severe incidents), via ENISA's Single Reporting Platform. These
  obligations become enforceable **2026-09-11**. What's *not* independently confirmed:
  whether Patchward — a security-scanning/remediation tool — falls under CRA Annex III
  ("important" products) at all, and if so which class. That determines whether
  self-assessment is sufficient or third-party conformity assessment is required.
  **Action:** get this classification confirmed by someone qualified before the
  Marketplace-paid launch, not after. Build the 24h/72h/14-day incident-reporting
  runbook regardless — it's good practice even if Patchward turns out to be out of
  scope.
- **GDPR.** Installation/billing data (`installations_db`) plausibly constitutes
  personal data processing. A lightweight DPIA and explicit TTL/data-minimization
  policy on that database is cheap insurance and should happen before Phase 10, not
  after a first complaint.

---

## 6. Backlog resolution — the three-way tension, resolved

**Framework: WSJF (Cost of Delay ÷ Job Size), with one addition — an explicit
irreversibility check**, because WSJF is the mainstream framework that natively prices
risk-reduction work, and item (a) below is exactly that. All three independent
research runs converged on the same sequencing conclusion despite using slightly
different scoring mechanics — that's a strong signal, not a coincidence.

| Item | Value | Time-crit. | Risk reduction | Job size | WSJF | Irreversibility |
|---|---|---|---|---|---|---|
| **(a) Real E2E pipeline test** (scan→fix→verify→PR) | High | Med | **Very high** — the entire product thesis is currently unproven end-to-end | Small | **Highest** | Mitigable — see staging below |
| **(c) callmed-landing rename** | Low-med | Low-med | Low | Very small | Second | None — do whenever a gap opens |
| **(b) Mirror Pass Tier 2** | High (nominal) | Low | Low | Large | Lowest *for now* | Its value is contingent on (a) — features built on an unproven pipeline are inventory risk |

**Resolved sequencing:**
1. **Run the E2E test now, staged, not as one monolithic risky step.** All three
   reports converge on this refinement of your original framing: instead of choosing
   between "test the pipeline" and "risk a real draft PR on someone else's repo" as a
   single binary decision, split it —
   - **Stage 1:** run scan→fix→verify→PR against a repo you own (a fixture repo, or a
     fork with deliberately planted, non-critical vulnerabilities). Zero third-party
     exposure, bounded and known API-credit cost, and it exercises the full pipeline
     including the GitHub App installation and webhook trigger if you install the App
     on that repo too — meaning this single test also partially validates Phase 9/10
     surfaces.
   - **Stage 2:** only once Stage 1 passes cleanly, run an authorized third-party test
     per your original plan.
   - This is falsifiable either way: if Stage 1 fails, you've found the biggest
     problem for the smallest cost, which is the entire point of doing it first.
2. **Slot (c) callmed-landing into gaps** — whenever you're blocked on (a) or context-
   switching, do it. It's cheap and has zero downstream dependency, but doesn't
   outrank de-risking the core pipeline.
3. **Begin (b) Mirror Pass Tier 2 only after (a)'s Consolidated Keystone confirms the
   walking skeleton works end to end.** Building more feature surface on an unvalidated
   core is the kind of work that has to be redone if the core turns out to have a
   structural problem.

---

## 7. Cadence — three layers, no more

More layers than this is the enterprise-process trap the original brief explicitly
warned against; fewer than this is how the current gap happened.

- **Session-open (≤2 min, every session, ideally hook/Skill-enforced):** agent reads
  `AGENTS.md` → `STATE.md` → top of `BACKLOG.md`, states in one paragraph what it
  believes the current state and task are. You confirm or correct *before* any work
  starts. This turns "stale assumption persists across sessions" into a 30-second
  catch, which is precisely the failure that happened on 2026-07-10 before you caught
  it manually.
- **Session-close (every session, hook/Skill-enforced, not optional):** agent appends
  a WORKLOG entry (what changed, commit hashes, what's still `UNVERIFIED`), updates
  `BACKLOG.md`. A session that ends without this is, by definition, unfinished — don't
  push until it exists.
- **Weekly, 30 minutes, you only:** verify that week's `UNVERIFIED`/claimed items by
  actually running the commands; promote confirmed ones into `STATE.md`; re-score the
  top of `BACKLOG.md`; prune anything in `AGENTS.md` that's gone stale (stale
  instruction-file content measurably degrades agent output, independent of this
  project's own experience); tag the repo `weekly/YYYY-WW`. This is the entire
  recurring overhead of the whole system.
- **Phase gates, on demand:** full INTAKE before, Keystone after — reserved for the
  Phase 8/9/10 transitions and any future direction change, per Part 5.

---

## 8. Day-to-day human–agent interaction protocol

1. **Every task is written as a mini-INTAKE, however small** — background, goal,
   explicit acceptance criteria, and the exact command that defines done (e.g., a
   specific `pytest` invocation). A three-sentence version of this for a 20-minute task
   is still worth writing; it's the same INTAKE contract, scaled down.
2. **Context frugality.** Fresh session per unrelated task. Load `STATE.md`/
   `BACKLOG.md` by reference, not by pasting their full contents into every prompt.
   Never let a debugging session drift into an unrelated feature. If a long session
   starts showing signs of context degradation (forgetting stated constraints,
   inventing function signatures that don't exist), stop, have the agent write a short
   summary of current state, and start a clean session with that summary — don't push
   through a degraded session hoping it recovers.
3. **Acceptance calibrated by trust tier, not by plausibility** (this is the Part 4.3
   protocol applied day-to-day): Tier-0-evidenced output — accept on the evidence.
   Anything touching external state or a security boundary — independent verification
   is the rule, not a judgment call you make per-instance. Judgment calls are what
   erode under deadline pressure; the July incident is the proof.
4. **Three deliberate multi-model patterns, and stick to only these three** so token
   spend stays proportionate to stakes:
   - **Parallel research → single synthesizer** — exactly what produced this document.
     Keep the parallel runs blind to each other; have the synthesizer surface
     disagreements explicitly rather than quietly averaging them away.
   - **Cross-model adversarial review of high-stakes diffs** — a different model
     reviews a security-boundary patch than the one that wrote it. Same
     verifier-≠-implementer principle as Part 4.3, applied across vendors for the
     highest-stakes work only.
   - **Restricted-tool subagents for scoped jobs** — you already validated this
     pattern with Fix-Gen (Read/Edit/Write, no Bash). Reuse it: a docs-maintenance
     subagent that can write only under `docs/` and the memory files is the same idea
     applied to project hygiene.
   Reserve all three for decisions expensive to reverse — not as a default. At solo
   scale, token spend is a real budget line, not a rounding error.

---

## Appendix A — `memory/STATE.md` starter template

```markdown
# STATE — verified project facts only
# Every line must carry: (claim) — (evidence) — (date checked) — (verified by)
# The agent may read this file. The agent does NOT write to it directly —
# proposals go in WORKLOG.md and are promoted here by the human (or CI).

## Phase
Phase 8 — Reconciliation (State Reconstruction Audit) — tag state-audit-2026-07 — 2026-07-10 — you

## Deployed services
patchward-webhook.fly.dev — /healthz returns {"status":"ok"} —
  curl https://patchward-webhook.fly.dev/healthz, run 2026-07-10 — you

## Repo
main @ <SHA> — confirmed via `git ls-remote origin main` (Tier 0) — 2026-07-10 — you

## Tests
<count> passed, <coverage>% — `uv run pytest --cov`, run <date> — you

## Known UNVERIFIED (do not treat as fact until promoted)
- <item> — Tier-2 source only — needs Tier 0/1 confirmation
```

## Appendix B — `memory/VERIFICATION.md` starter template

```markdown
# VERIFICATION — trust tiers for any claim about external state

Tier 0 (deterministic/content-addressed): git hashes, `git ls-remote`, file digests,
local exit codes. Accept as-is.

Tier 1 (authenticated direct reads): authenticated API calls on a non-shared path,
`fly status` with credentials, logged-in web UI. Accept with evidence; spot-check weekly.

Tier 2 (proxied/unauthenticated/cached/rate-limited): any read through an agent's
sandboxed network path. NEVER sufficient alone for a gating decision. Label
`UNVERIFIED (tier-2)`. Requires Tier 0/1 confirmation before promotion to STATE.md.

Standing rule: any claim gating a real decision needs two independent paths in
agreement, or it stays UNVERIFIED.
```

## Appendix C — first 14 days, concretely

| Day | Action |
|---|---|
| 1 | Run the State Reconstruction Audit (Part 3) in full. Create the 7-artifact set. |
| 2 | Write the Phase 9 Exposure Gate INTAKE; implement HMAC timing-safe signature validation on `/webhook` (retroactive hardening — it's already live). |
| 3–4 | Stage 1 of the E2E test: scan→fix→verify→PR against a repo/fixture you own. |
| 5 | Consolidated review of Stage 1 results; Keystone Report for the E2E validation; decide on Stage 2 timing. |
| 6–7 | callmed-landing rename task (fills the gap while Stage 2 authorization/target selection happens in the background). |
| 8+ | Stage 2 authorized third-party E2E test, or begin Phase 10 Marketplace-readiness checklist, or begin Mirror Pass Tier 2 — decided by what Stage 1 revealed. |

---

*This plan is a proposal, not a contract — it hasn't been through the INTAKE process
it recommends. Treat Part 3 (the audit) as the first real INTAKE under the new
regime: read it, edit what you disagree with, then sign off before execution starts.*
