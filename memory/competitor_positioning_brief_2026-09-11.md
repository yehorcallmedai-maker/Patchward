# Patchward — Competitive Positioning Brief

**Date:** 2026-09-11
**Prepared for:** Yehor Kaliberda / Patchward
**Scope:** Direct and adjacent competitors in AI-driven security-fix automation (the "scanner finds it, AI fixes it, bot opens the PR" category), where Patchward actually sits, and what it implies for repositioning, Terms of Service / Privacy Policy, and go-to-market. Every claim below was checked against at least the vendor's own pricing/product page plus one independent source (a second page or a search result); nothing here is taken from a single source without a cross-check. This is competitive/market research, not legal advice — the ToS/Privacy section (§4) flags what to decide, not what the law requires; get that confirmed by someone qualified before publishing anything.

---

## 1. Patchward, audited against its own sources (so the positioning below is accurate, not aspirational)

Pulled from `README.md`, `docs/user_guide.md`, `patchward.toml.example`, and patchward-landing's `facts.yaml`/pages — the same canonical-facts discipline the site itself uses, applied here to the competitive brief.

- **Mechanism:** 5 scanners (Semgrep, Bandit, pip-audit, Trivy, ESLint) run in a network-isolated sandbox → findings normalized to SARIF → an LLM (Anthropic) subagent drafts one bounded fix → **three gates** before a PR ever opens: Gate 1 re-scan confirms the flagged rule no longer fires, Gate 2 confirms the diff stays within authorized lines, Gate 3 runs the target repo's own test suite (skips with explicit disclosure, not silent failure, when no test runner is present — e.g. the hosted webhook path). Opens a **draft** PR; never merges.
- **Data boundary (already disclosed on `/limits` and `/data-boundary`):** triage and fix-generation send repository file contents to the Anthropic API. Credential scrubbing covers Patchward's own CLI/log output, not what's sent to Anthropic. This is stated plainly, not buried.
- **Real-world proof:** 565 tests / 91.20% coverage (2026-08-08, Yehor's machine); 2 merged security-fix PRs on the open-source project `mpfb2`; 1 honestly-disclosed near-miss on `checkdmarc` (PR closed, unmerged — the maintainer wrote their own narrower fix instead, which shipped in v5.17.3). No case study currently overstates this.
- **Actual commercial stage:** pilot-only. Delivery today is Yehor running the CLI directly against a customer's repo; there is no live self-serve signup, no public pricing, and "first paying Marketplace install" is still an open goal in the project's own memory. `README.md` still says "not yet published to PyPI," which is stale — v0.1.0 has been live on PyPI since 2026-07-22 (already flagged in memory, not fixed this session since it's a copy fix, not research).
- **Naming history that matters for §2 below:** Patchward was renamed from "RepoMend" specifically because `repomend.com` was already a live, unrelated product in the same category (logged in this project's own git history, 2026-07-16). That collision was resolved by Yehor's own renaming — it hasn't gone away, it's grown.

---

## 2. The competitive landscape

### 2a. `repomend.com` — the most urgent one, by name history alone

This is the product Patchward was renamed away from. It is now live, self-serve, and priced — Patchward is currently none of those three.

- **Pitch:** "Find it. Fix it. Ship it." / "16 scanners find vulnerabilities across your repos and infrastructure. Claude drafts the fix over MCP. You merge the PR."
- **Mechanism:** connect repos → select scanners → Claude (via MCP) drafts a patch → opens a branch and tags the team for review. **No stated verification step** — no re-scan-to-confirm, no diff-bounds check, no test-suite gate. It asks you to trust Claude's patch directly.
- **Scanner count:** claims 16; 13 are named (Nuclei, Trivy, Semgrep, ZAP Baseline, ZAP API Scan, Nuclei API, Nmap Quick/Full/Vuln, SSL/TLS Scan, Endpoint Patrol, Semgrep Protections, Coverage Diff) — broader than Patchward's 5, and it also covers network/infrastructure scanning Patchward doesn't touch at all.
- **Pricing (live, self-serve):** Solo — free forever (1 repo, 3 scans/day, 1 engineer); Team — $28/seat/month (unlimited repos, auto-fix/merge); Enterprise — custom (self-hosted, dedicated Claude capacity, compliance support).
- **Data handling:** "Findings are sent to Claude through your own Anthropic credentials by default. We never train on customer data" — cloud-managed by default, VPC available on enterprise. Notably vaguer than Patchward's own disclosure about *what* gets sent (Patchward says repo file contents; RepoMend doesn't say what "findings" includes).
- **Company:** no funding, founding date, or team information found anywhere public — reads as a similarly small operation, not a funded competitor with a war chest.

### 2b. Pixee (`pixee.ai`) — the established mid-market player

- **Pricing:** outcome-based, per-resolution (a triage action or a fix action), explicitly *not* per-seat — "Traditional tools profit when your backlog grows. We only profit when it shrinks."
- **Mechanism:** maps the codebase and execution paths → proves exploitability to cut false positives (claims 95% reduction) → generates convention-aware fixes → fixes must pass CI before the PR opens. More deterministic/codemod-flavored than pure LLM generation.
- **Traction claims:** 76% developer merge rate, 5,200+ backlog items cleared, enterprise logos (Oracle, HCL Technologies, NTT Data).
- **Why it matters:** it already has the enterprise social proof and the "we only get paid for shrinking your backlog" framing that Patchward's own "plausible is not verified" instinct is reaching for — Pixee got there first, at a scale Patchward can't yet claim.

### 2c. Corgea (`corgea.com`) — YC-backed, AI-native, broader scope

- **Mechanism:** AI-native detection (business logic flaws, broken auth/authz, not just SAST patterns) plus autonomous fix generation, ~90% claimed auto-fix accuracy, "2x more true positives / 3x fewer false positives" vs. traditional scanners.
- **Trust signals:** SOC 2 Type II certified, Y Combinator-backed, freemium with a 14-day trial, no credit card required.
- **Why it matters:** broader vulnerability-class coverage than Patchward (auth/authz logic, containers/infra) and a compliance certification Patchward doesn't have.

### 2d. GitHub Copilot Autofix (agentic, public preview since 2026-07-10) — the platform-level threat

- **Mechanism:** analyzes the alert, explores the codebase, generates a fix, **reruns the original scan to confirm the fix actually closes the alert** before opening a PR — this is functionally the same idea as Patchward's Gate 1.
- **Distribution:** built into GitHub itself, works across CodeQL and third-party code-scanning alerts, gated behind a GitHub Advanced Security + Copilot license (draws down AI credits during preview, no separate line-item yet).
- **Why it matters most:** this isn't a startup to out-market — it's the platform every one of Patchward's prospective customers already lives inside. If "good enough" autofix ships free-with-the-platform for orgs already paying for GitHub Advanced Security, it compresses the addressable market for standalone tools in this exact category, Patchward included. Worth tracking its rollout pace, not treating it as background noise.

### 2e. Socket.dev — adjacent, dependency/supply-chain focused

- **Pricing:** Free ($0, 1,000 scans/month) → Team ($25/dev, min 5) → Business ($50/dev, min 20) → Enterprise (custom).
- **Fix capability:** "Socket Certified Patches" (one-click apply, automatic patch PRs) is a **separate add-on purchase**, not bundled — and it's scoped to dependency/supply-chain issues, not the SAST-style code findings Patchward targets.

### 2f. Category incumbents, for context rather than head-to-head

- **Snyk:** free for open source, ~$25/dev for teams; has DeepCode AI Fix (one-click suggestions) **and Snyk Agent Fix**, which independently confirmed runs every generated fix through a Snyk Code SAST scan *before it's ever shown to the user*, checking that the fix "is readable and correctly formatted, actually solves the problem it's meant to, [and] doesn't introduce any new security issues" (source: Snyk's own "Building AI Trust" post, fetched directly — this is a re-verification gate, added here after independent spot-check, not in the original research pass). Massive brand recognition — likely the tool a prospective customer already has.
- **DeepSource, Sourcery, Qodo (CodiumAI):** centered on code quality/review with autofix features layered in, not primarily security-gate verification. Adjacent, not head-to-head.

---

## 3. Where Patchward's actual wedge is (and where it currently is not)

**Correction, added 2026-09-11 after independent spot-check of this brief's own load-bearing claims** (the same discipline this project applies to every git claim, applied here to the research itself): the original wording below understated how many competitors have *some* re-verification step — four now, not two (Pixee's CI gate, GitHub's CodeQL rescan, Snyk Agent Fix's pre-presentation SAST scan, all confirmed directly against vendor sources). The wedge is narrower than first stated, but sharper and independently confirmed to still be real:

**Real and currently defensible:** not "verification exists" (four competitors now have some form of it) but **uniform, disclosed verification across every scanner a repo runs, regardless of source.** GitHub's own docs state this precisely, quoted directly: "Copilot validates fixes by re-running CodeQL using the code-scanning query suite, so it can't confirm that a fix resolves alerts generated by custom queries or the security-extended query suite," and separately, "Fix quality for alerts from third-party tools is also not guaranteed." That is an explicit, scoped, best-effort limitation on GitHub's own most-direct feature. Patchward's Gate 1 re-scan is not shown to carry an equivalent carve-out — it applies the same way regardless of which of the five scanners raised the finding. Snyk's pre-presentation SAST scan and Pixee's CI gate are both real but, like GitHub's, undisclosed as to scope/limitations on the vendor's own marketing pages — Patchward's `/limits` page stating the boundary in the open (see §1) is itself part of the same wedge, not a separate one.

**Partially claimed already by others, now with four examples instead of two:** Pixee (CI must pass before PR), GitHub (CodeQL rescan, explicitly scoped), Snyk Agent Fix (pre-presentation SAST scan), and none of RepoMend, Corgea, or Socket state any equivalent step at all. So the wedge is "all three gates, every time, disclosed, with no stated scope carve-out" — narrower and more precise than "verification exists nowhere else," and still true on independent re-check.

**The `/limits` page itself — stating plainly what Patchward does *not* guarantee — is unusual in this category.** Every competitor above markets capability; none published an equivalent of the "what we don't cover" page. That's consistent with a pattern already logged in this project's own memory (an established, hard-won house principle) and worth leaning into explicitly rather than softening it to sound more like the field.

**Where Patchward is currently behind, plainly:** scanner breadth (5 vs. RepoMend's claimed 16), no public pricing or self-serve signup at all (every competitor above has at least a free or trial tier live today), only 2 merged real-world PRs plus one honest near-miss as case-study material, and no compliance certification (Corgea has SOC 2; Patchward doesn't state a security-review status of its own for handling other people's repos).

---

## 4. Terms of Service / Privacy Policy — a real gap found while researching, not just a competitive-tone question

Checked patchward-landing's actual page list (`index`, `how-it-works`, `verification`, `data-boundary`, `examples`, `facts`, `limits`, `404`) — **there is no `/terms` or `/privacy` route on patchward.dev today.**

This matters independent of anything competitive: the go-to-market idea floated this session — offering free Patchward runs to third-party open-source maintainers — means asking people who are not customers, haven't signed anything, and may not have read `/data-boundary`, to let their repository's file contents be sent to the Anthropic API. That should not happen without a stated, findable Privacy Policy covering exactly that, before any outreach goes out — this is a sequencing point, not a legal opinion, and it's worth having someone qualified confirm what's actually required for the jurisdictions involved (this project's own memory already tracks a separate, unrelated EU regulatory question — the CRA/NJORD thread — through actual counsel, which is the right model to reuse here rather than drafting legal text from research alone).

One competitive observation on this point: RepoMend's own privacy language ("through your own Anthropic credentials by default") is vaguer than Patchward's existing `/data-boundary` disclosure about what data actually moves. A Patchward Privacy Policy written in the same plain, disclosure-first voice as `/limits` and `/data-boundary` would be *more* honest than the nearest competitor's, not just compliant — that consistency is itself worth stating as a differentiator once it exists, not treated as a checkbox.

**Important qualifier, found while checking `patchward.toml.example` directly (2026-09-11):** the ToS/Privacy urgency above applies specifically to Yehor personally running Patchward against someone else's repo (today's pilot-delivery model), or to any future hosted/webhook Marketplace path. It does **not** apply the same way to the plain CLI distribution: `patchward.toml.example` confirms the CLI reads `ANTHROPIC_API_KEY` from the *user's own* environment and a repo path on *their own* disk — a person who clones the repo and runs `patchward scan`/`patchward fix` themselves sends their own code to Anthropic using their own credentials, with Patchward's own infrastructure never in the data path at all. That's the same trust model as any other open-source CLI (ripgrep, black, etc.) — a permissive license's standard "AS IS, NO WARRANTY" language covers that case; it's only the "Yehor or Patchward's own service touches a third party's code" cases that need the fuller Privacy Policy treatment.

---

## 4a. Addendum, 2026-09-11 — checked in response to the "make Patchward free/open-source" question

Two facts, checked directly against GitHub and the repo itself, not assumed:

- **`github.com/yehorcallmedai-maker/Patchward` is already public** — a normal public repo view, full code/README/history visible to anyone, 0 stars, **no LICENSE file**. "Open-sourcing" it is not a visibility switch that gets flipped; the code has been readable by anyone for roughly two months and has produced zero visibility (0 stars) without active promotion. What's actually missing is a real OSS license (making reuse *legal*, not just reading *possible*) and, separately, any deliberate effort to get it seen — the two are different problems with different costs.
- **Patchward and FixProve are parallel projects under the same CVR**, per this project's own persistent record — both are AI-code-verification tools for Python/TypeScript, and FixProve is the more advanced of the two by every visible measure right now: a live CLI (v0.1.12) on npm and PyPI, an MIT license already in place, active GTM outreach to named Tier-1 targets, a running 30–90 day demand test (through 2026-11-12), and incubator/funding-pipeline participation. Patchward, by contrast, is pilot-only with zero self-serve traction. This context matters directly for §6 below.

---

## 5. Draft positioning line (for review, not final copy)

> Other tools ask you to trust an AI's patch. Patchward proves it: every fix is re-scanned, bounds-checked, and run against your own tests before it becomes a pull request — and the receipt says exactly what was and wasn't checked.

This leans on the one wedge that's both true today and not fully claimed by the nearest-history competitor (RepoMend). It does not lean on scanner breadth or case-study volume, where Patchward is currently behind — those would need to close before making a volume/breadth claim.

---

## 6. Suggested next steps (sequenced; none of this started — for Yehor's scoping decision)

1. **Decide the ToS/Privacy question first** (§4) — it's a hard blocker for the "offer free runs to maintainers" step of the original idea, independent of anything else here.
2. **Decide the scanner-breadth question**: close the gap toward RepoMend's 16 before going to market, or lead with "narrower but every fix is gated and disclosed" as the honest trade-off? Both are legitimate strategies — this is Yehor's call, not a research conclusion.
3. **The repo-outreach shortlist and pitch** (the alternate option this session didn't pick) is the natural next piece once §4 and the positioning line are settled — starting outreach before the Privacy Policy exists would be sequencing it backwards.
4. **RepoMend specifically** is worth an informal periodic check (pricing/feature changes) given the shared history — this is a competitive-watch item, not a trademark or legal concern; no evidence of registered marks or disputes was found in this research.

---

## Sources

- [RepoMend — repomend.com](https://repomend.com) (fetched directly, twice — product overview and follow-up on verification/scanners/company info)
- [Pixee — Pricing](https://www.pixee.ai/pricing)
- [Pixee — homepage](https://www.pixee.ai/)
- [Pixee — VulnOps](https://www.pixee.ai/vulnops)
- [Corgea — corgea.com](https://corgea.com)
- [Corgea on Y Combinator](https://ycombinator.com/companies/corgea)
- [GitHub Changelog — Agentic autofix for code scanning alerts, public preview](https://github.blog/changelog/2026-07-10-agentic-autofix-for-code-scanning-alerts-in-public-preview/)
- [GitHub Docs — About Copilot Autofix for code scanning](https://docs.github.com/en/code-security/concepts/code-scanning/copilot-autofix-for-code-scanning)
- [Socket.dev — Pricing](https://socket.dev/pricing)
- [Snyk pricing coverage, 2026 (free for OSS, ~$25/dev teams)](https://dev.to/rahulxsingh/snyk-pricing-in-2026-free-plan-team-business-and-enterprise-costs-breakdown-5e88)
- Patchward's own `README.md`, `docs/user_guide.md`, `patchward.toml.example`, and patchward-landing's `src/data/facts.yaml` / `src/pages/{index,limits,how-it-works}.astro` (read directly from the working tree, 2026-09-11)
