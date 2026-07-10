# Deep Research Brief — Patchward: Closing Informational Gaps & Establishing Industrial-Grade Project Organization

**Purpose of this document:** This is a research prompt, meant to be pasted as-is into a
deep-research-capable model (or several, for cross-synthesis). It is self-contained —
no other file access is assumed. The output of this research will be used to build a
step-by-step, professional-grade project organization and build plan for a real,
in-progress software project.

---

## 1. Role for the research agent

Act as a **principal engineering-operations consultant** who specializes in two combined
disciplines: (a) software delivery governance for small/solo teams operating at
professional/industrial rigor, and (b) human–AI-agent collaborative software
development workflows as they exist in 2026. Your output will be read by a solo
technical founder who is the sole developer, reviewer, and product owner of the
project described below, working in close daily collaboration with AI coding agents
(Claude-based, operating with file/shell/git tool access). Write for that audience:
assume technical fluency, no hand-holding on basic software engineering concepts, but
be explicit and prescriptive about process, tooling, and cadence.

---

## 2. Project foundation (use this as ground truth context)

**Project:** Patchward (renamed 2026-07-07 from "RepoMend" — the old name collided with
a live unrelated competitor, repomend.com).

**What it does:** A local-first, multi-repository security remediation agent. It scans
target codebases with Semgrep, Bandit, pip-audit, and Trivy; normalizes findings to
SARIF; runs an LLM-backed "Fix-Gen" subagent (Anthropic Claude, restricted to
Read/Edit/Write tools, no Bash) inside an isolated git worktree branch to patch each
finding; verifies the patch with a **deterministic, non-LLM Verifier** (three gates);
and — on verified success — opens a draft GitHub pull request for human review via a
"PRPublisher" component. Everything below the top level is designed around
human-sign-off gates: nothing merges without a human.

**Stack:** Python 3.12+, `uv` for packaging/dependency management, Typer CLI,
Pydantic v2 config, OpenTelemetry tracing (Langfuse), AsyncAnthropic client,
asyncio-based multi-repo pipeline with concurrency limits, Docker sandbox with
deny-by-default network egress (iptables-hardened, per-scanner network policy),
PreToolUse hook-based deny rules against a red-team payload list, a credential proxy
that keeps secrets out of the LLM's context and out of committed diffs, and
`git worktree`-based isolation per fix attempt.

**Newer addition (2026-07-09), not yet reconciled into project docs:** A GitHub App
webhook receiver + Marketplace billing state (`src/patchward/webhook.py`,
`github_app_auth.py`, `installations_db.py`), built on FastAPI + Uvicorn + PyJWT,
deployed to Fly.io (`patchward-webhook.fly.dev`, `/healthz` confirmed live) via
`docker/webhook.Dockerfile` and `fly.toml`. This represents a shift from "single-user
CLI tool" toward "installable GitHub App with a billing surface" — a meaningful
architectural and product direction change that has not yet been captured in any
planning document.

**Development methodology used so far (pre-rename, "RepoMend era"):** An 8-phase
build (Phase 0 through Phase 7), each gated by a signed "INTAKE contract" (scope +
acceptance criteria before building) and a signed "Keystone Report" (evidence-based
close-out after building), with an Architectural Decision Record (ADR) log for
significant decisions, a per-session log, and a running open-tasks/backlog file. This
produced a genuinely rigorous audit trail through 2026-06-23 (Phase 7 close, "RepoMend
v0.1.0," 371 tests passing, 89% coverage) — but the process was not continued after
the rename. Real, substantial work happened between 2026-06-23 and 2026-07-09 (the
rename itself, the webhook/billing build, the Fly deployment, CI scaffolding for a
future PyPI Trusted Publisher release) with **zero corresponding session logs, ADRs,
INTAKE contracts, or Keystone Reports.** This is the primary gap this research should
help close.

**Known operational reliability lesson from this project (2026-07-10):** Verifying
live GitHub state through an AI agent's sandboxed/proxied network path
(unauthenticated `api.github.com` REST calls through a shared, rate-limited egress
proxy) produced silently stale/incorrect reads — the agent repeatedly "confirmed" a
commit was not on the default branch when it actually was. Ground truth only emerged
from the human operator running `git ls-remote` and checking the authenticated GitHub
web UI directly. This is a concrete instance of a broader problem worth researching:
**how to design verification protocols for AI-agent-assisted development that don't
silently trust an unreliable data path.**

**Owner/operator:** One person (solo founder/developer), working across sessions with
an AI coding agent that has direct file, shell, and (human-mediated) git access, plus
a separate human-only step for anything that writes to the real git remote.

---

## 3. Problem statement — why this research is needed

The project has two compounding gaps:

1. **Informational/documentation gap.** Real project state (current architecture,
   current phase/roadmap, current test/coverage status, current deployment topology,
   current backlog and its priority order) has drifted out of sync with what's
   recorded in the project's own memory/context files. This has already caused a
   concrete failure: a prior session incorrectly reported unresolved work as
   unresolved when it had, in fact, resolved — an assumption that persisted across
   sessions until directly challenged and re-verified from first principles.

2. **Organizational/process gap.** The rigorous phase-gate methodology that worked
   well pre-rename (INTAKE contracts, Keystone Reports, ADRs) was abandoned under
   time pressure once the project pivoted toward a new surface (GitHub App +
   billing). There is currently no clear answer to: What phase is the project
   actually in? What's the prioritized backlog? What does "done" mean for the
   current work? How should the solo operator and the AI agent divide
   responsibility, and how should the operator verify the agent's claims without
   having to personally re-derive everything from scratch each time?

---

## 4. Research objectives

Produce a comprehensive report that enables synthesis into a concrete, step-by-step,
professional/industrial-grade build-and-organization plan. Specifically:

### A. Closing informational gaps
1. What is the state-of-the-art methodology (2025–2026) for **reconstructing an
   accurate project state** after a period of undocumented work — i.e., how do
   professional engineering organizations perform a "state audit" or "documentation
   reconciliation" pass efficiently, without re-litigating every decision from
   scratch? Include concrete techniques (git archaeology, diff-based state
   reconstruction, structured interview/checklist approaches).
2. What structures/formats best prevent this gap from recurring — living
   architecture docs, ADR logs, session/changelog discipline, "definition of done"
   checklists — specifically **adapted for a solo developer working with an AI
   coding agent**, where the agent itself can be tasked with maintaining some of
   this, but where the boundary between agent-claimed-state and verified-state must
   stay explicit.
3. How should verification/trust boundaries be designed when an AI agent's own tool
   access (sandboxed network, mediated git access) may itself be an unreliable
   source of truth? What patterns exist for "trust but verify" pipelines in agentic
   dev workflows — e.g., dual-source confirmation, human-in-the-loop checkpoints,
   cryptographic/content-addressable verification (as was used successfully here via
   git commit-hash matching) — and how should these be systematized rather than
   improvised per-incident?

### B. Professional/industrial organizational development
4. What does an "industrial-grade" (i.e., audit-ready, investor/enterprise-credible)
   solo-developer software project actually require at minimum — distinguishing
   genuinely valuable rigor (traceable decisions, reproducible verification,
   security posture, change history) from process theater that doesn't scale to a
   team of one?
5. How should a phase-gate/INTAKE-and-Keystone-style methodology (as already
   partially used in this project) be adapted now that the project has shifted from
   "internal CLI tool" to "installable product with a billing surface and a public
   deployment"? What additional gates matter now (security review before exposing a
   webhook endpoint publicly, billing/compliance considerations for GitHub
   Marketplace apps, SLA/uptime expectations for a hosted service) that didn't
   matter for a local-only tool?
6. What prioritization frameworks are best suited to resolving the current
   three-way backlog tension in this project: (a) an authorized, real end-to-end
   pipeline test (scan → fix → verify → PR) that costs API credits and may open a
   real draft PR against a third-party repo, (b) continued feature build-out
   ("Mirror Pass Tier 2"), and (c) a smaller branding/rename task
   ("callmed-landing"). Research should surface a defensible, criteria-based way to
   sequence this kind of mixed technical-risk/product-value/cost backlog — not just
   name a framework, but show how to apply it to exactly this kind of decision.

### C. Self-organization — how the human operator should run this
7. **Define a role for the human operator (the solo founder) that fits this
   workflow** — i.e., propose and justify a specific operating persona/title (for
   example, something like "Technical Director acting as Product Owner and final
   Verifier," or an alternative you consider better) that clarifies what the human
   is responsible for deciding, reviewing, and signing off on, versus what can be
   safely delegated to the AI agent. Be concrete about the boundary.
8. What cadence, rituals, and artifacts (daily/weekly check-ins, review gates,
   async status digests, sign-off ceremonies) are actually effective for a solo
   operator working with AI agents across many short sessions, given that context
   does not automatically persist between sessions and must be deliberately
   maintained in files?
9. **How should the operator interact with the AI agent day to day to get the most
   effective and innovative results possible as of 2026** — covering current
   best practices in prompt/session design, memory/context engineering, task
   delegation patterns, when to demand independent verification vs. accept agent
   output, and how to use multiple AI agents/models productively (including the
   specific workflow already underway here: commissioning parallel research from
   several different models and having one agent synthesize the results). Include
   anything genuinely new/emerging in this space as of today rather than generic,
   dated advice.

---

## 5. Required output structure

Structure the research output so it can be **synthesized alongside two other
independent research runs on the same brief**. To make that synthesis tractable:

- Use clear numbered sections matching objectives A/B/C above.
- For every recommendation, state it as an actionable, falsifiable claim (not vague
  advice) — e.g., "adopt X pattern, structured as Y, because Z" rather than "consider
  best practices."
- Where frameworks/methodologies are named, briefly justify why they fit *this*
  project's actual size and risk profile (solo dev, AI-agent-assisted, security
  product, real but non-enterprise stakes) rather than defaulting to
  enterprise-scale process.
- Include a short "if you only do three things" summary at the end of each major
  section (A, B, C).
- Cite sources/prior art where relevant (named methodologies, real tools, real
  practitioner writing) so claims can be checked, not just asserted.
- Keep total length substantial but not padded — depth over word count.

---

## 6. Constraints

- Do not recommend generic enterprise-scale process (e.g., full Scrum ceremonies,
  multi-approver CAB boards) without explicitly justifying why it's proportionate
  for a team of one human plus AI agents.
- Do not assume access to any tool, platform, or vendor not already implied by the
  stack above unless clearly flagged as an optional addition with a stated reason.
- Favor concrete, adoptable-this-week recommendations over aspirational,
  hard-to-implement ones — this plan needs to actually get used by one person.
