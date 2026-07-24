# Patchward — Counsel Briefing Packet (CRA / GDPR)

**Prepared:** 2026-07-24 (Session 024) · **Revised:** 2026-07-24, same session — correction pass
after Yehor's own independent re-read of the source found the data-flow section understated the
finding and mis-stated one call-site count; see the "Data flow to Anthropic" section for the
corrected text, marked inline · **Status:** DRAFT — facts and questions only, no legal
conclusions · **Purpose:** give qualified counsel everything needed to answer BACKLOG item 12
without them having to reverse-engineer the product from scratch.

## How to read this document

This packet strictly separates two kinds of content:

- **Facts about Patchward** — written by the agent that maintains this codebase, verified
  against the real source at git HEAD `3e63587306d659d1282e8a75542dca7cf3d8dfe5` on
  2026-07-24 (not paraphrased from memory or from an earlier session's notes).
- **Questions for counsel** — every classification judgment (CRA scope, Annex III class,
  manufacturer status, GDPR controller/processor role, DPIA necessity) is posed as an open
  question. None of these are answered here. Where background regulatory material is included
  (Step 5), it is cited to its source and clearly separated from any conclusion about how it
  applies to Patchward specifically.

**Hard rule this packet follows:** the agent that wrote this is not a lawyer and must not
pretend to be one. Every "likely X" or "probably Y" has been deliberately avoided in favor of
"here are the facts; here is the question; counsel decides."

---

## Step 1 — Technical data inventory (`installations_db.py`)

Source: `src/patchward/installations_db.py`, read directly at HEAD `3e63587`. This is the only
persistent, multi-tenant customer data store in the codebase — it backs the Fly-hosted webhook
service, not the local CLI (the CLI processes a user's own repo locally and does not persist
anything about third parties).

### Table: `installations`

| Field | Type | Example | Origin | Retention |
|---|---|---|---|---|
| `id` | INTEGER (PK) | `12345678` | GitHub's own installation ID, from the `installation` webhook payload | Deleted when GitHub sends `installation` / `action=deleted` (see below) |
| `account_login` | TEXT | `"acme"` or `"jane-doe"` | `payload["installation"]["account"]["login"]` — the GitHub org or user login that installed the App | Same as above |
| `account_type` | TEXT | `"Organization"` or `"User"` | Same payload, `account["type"]` | Same as above |
| `installed_at` | TEXT (ISO-8601 UTC) | `"2026-07-24T10:00:00+00:00"` | Server-generated at insert time | Same as above |
| `suspended_at` | TEXT, nullable | `null` or a timestamp | Set when GitHub sends a `suspend` action | Same as above |

### Table: `installation_repos`

| Field | Type | Example | Origin | Retention |
|---|---|---|---|---|
| `installation_id` | INTEGER (FK) | `12345678` | Same as above | Deleted along with the parent installation |
| `repo_full_name` | TEXT | `"acme/backend"` | `repo["full_name"]` from the webhook payload | Deleted along with the parent installation |
| `added_at` / `removed_at` | TEXT, nullable | timestamps | Server-generated | — |

### Table: `marketplace_purchases`

| Field | Type | Example | Origin | Retention |
|---|---|---|---|---|
| `account_login` | TEXT (PK) | `"acme"` | `marketplace_purchase` webhook payload | **No deletion path exists anywhere in the codebase — see gap below** |
| `plan_id` | INTEGER | `1` | Same payload | Same |
| `unit_count` | INTEGER | `5` | Same payload | Same |
| `billing_cycle` | TEXT, nullable | `"monthly"` | Same payload | Same |
| `status` | TEXT | `"purchased"` / `"changed"` / `"cancelled"` / `"pending_change"` | Same payload (the webhook `action`) | Same |
| `effective_date` | TEXT | timestamp | Server-generated | Same |

### Is there any deletion/TTL mechanism today?

**Partial.** `webhook.py`'s `installation` event handler calls `delete_installation()` when
GitHub sends `action == "deleted"` (i.e., the customer uninstalls the GitHub App) — this row and
its associated `installation_repos` rows are genuinely removed at that point. Confirmed directly
in `webhook.py`'s event dispatch.

**Gap, confirmed by reading every call site of the `installations_db` module:** the
`marketplace_purchases` table has **no deletion path at all**. A `cancelled` status only ever
updates the `status` column — the row itself is never removed, even after the account also
uninstalls the App. There is no TTL, no scheduled purge, and no code path that ever calls
`DELETE FROM marketplace_purchases`. This means a GitHub account login plus its historical plan
and billing-cycle metadata is retained indefinitely, with no explicit data-minimization policy
anywhere in the codebase or docs.

### Candidate personal data (flagged for counsel to confirm, not concluded here)

- `account_login` when `account_type == "User"` is an individual's GitHub username — this is
  the field most likely to constitute personal data under GDPR, especially combined with
  billing/plan history in `marketplace_purchases`.
- `account_login` when `account_type == "Organization"` identifies an org, not an individual,
  though very small organizations (e.g. a one-person company) may still indirectly identify a
  natural person.
- No email addresses, real names, or IP addresses are stored in any of these three tables.
- Deployment note: this SQLite database lives on a Fly.io volume in the `iad` (US) region (see
  Step 2) — so this data, including any candidate personal data, is stored on US infrastructure
  regardless of an EU customer's own location.

---

## Step 2 — Product-facts sheet for counsel

### What Patchward does

Patchward scans a codebase with static analysis tools (Semgrep, Bandit, pip-audit, ESLint),
sends each individual finding to an LLM subagent that drafts a minimal patch, runs a
deterministic verifier over the patch (re-scan + test-scope check), and opens a draft GitHub
pull request for a human to review and merge. No fix is ever merged automatically; a human
always reviews the PR.

### Deployment models (all three are real and shipping today, not roadmap items)

1. **Local CLI**, installed via `uv tool install patchward` from PyPI. Package `patchward`
   v0.1.0 has been live on PyPI since 2026-07-22 (re-confirmed this session, see Housekeeping).
   Runs entirely on the user's own machine against their own repo; nothing about a third party
   is transmitted or stored anywhere by this mode.
   *(Aside, unrelated to CRA/GDPR but worth flagging honestly since it was noticed while reading
   source for this packet: the repo's own `README.md` still says "Patchward is not yet published
   to PyPI. Install from source" — that line is stale and should be corrected; it doesn't affect
   this packet's content.)*
2. **Docker sandbox** for the scanner subprocesses specifically (`docker_sandbox.py`): each
   scanner runs inside a digest-pinned custom image (`patchward-scanner:0.1.0@sha256:...`) with
   `iptables`-enforced default-deny egress, used both in local-CLI mode and inside the hosted
   webhook flow. This isolates the scanning step only — the LLM calls described in the data-flow
   section below happen outside this sandbox, from the calling process directly.
3. **Hosted webhook service**, a FastAPI app (`src/patchward/webhook.py`) deployed as a single
   Fly.io Machine (`fly.toml`: app `patchward-webhook`, region `iad`, scale-to-zero). This is the
   GitHub App + Marketplace integration surface: it receives GitHub's `installation`,
   `installation_repositories`, `marketplace_purchase`, and `push` webhook events, persists
   installation/repo/purchase state in the SQLite database described in Step 1 (on a mounted Fly
   volume so it survives machine restarts), mints a fresh GitHub Installation Access Token
   (GitHub-issued, short-lived — on the order of one hour, per GitHub's own token design) instead
   of using a long-lived personal access token, and triggers the scan→fix→verify→PR pipeline as a
   background task per `push` event — gated by `is_entitled()`, i.e. only for accounts with a
   non-cancelled Marketplace purchase on file.

These three modes have materially different exposure profiles: the CLI touches nothing but the
user's own machine; the webhook service is the only mode that persists third-party data and is
internet-facing.

### Data flow to Anthropic — corrected from an earlier, imprecise description

**Correction pass, 2026-07-24, same session:** the first draft of this section understated both
the strength of the `read_file` finding and the scope of the data flow. Both are corrected below,
re-verified against real source a second time before writing this revision.

An existing product description states that "only the fix prompt reaches the Anthropic API,
scrubbed of credentials." Verified directly against `src/patchward/fix_gen.py`,
`src/patchward/subagent.py`, and `src/patchward/credential_proxy.py` at HEAD `3e63587` — **this is
not accurate as stated**, in three specific ways:

1. **More than a "prompt" is sent, and it is mandated by the system prompt, not merely an
   available option.** The first draft of this packet described `read_file` as a tool the
   Fix-Gen subagent "is given" and "would normally" call — that undersold it. The system prompts
   embedded in `fix_gen.py` **instruct the model to call it**, on every path, including the path
   where the model decides *not* to make a fix:
   - `fix_gen.py:224` (in the `decline_fix` tool's own description): *"You MUST call read_file at
     least once before calling decline_fix — a decline must be based on having actually inspected
     the code, not assumed from the finding text alone."*
   - `fix_gen.py:272` (main system prompt): *"Use read_file first to inspect the code before
     editing."*
   - `fix_gen.py:547` (the per-finding user message): *"Step 1: read_file to inspect the code
     around lines {line_start}–{line_end}."*
   - `fix_gen.py:355` (docstring of the tool executor): *"read_file is unrestricted within
     worktree_path (read-only, no trust concern)"* — i.e. the tool is not scoped to the
     finding's line range; it can read any file anywhere in the cloned repository worktree.

   Whatever `read_file` returns — the actual source code content read from the customer's cloned
   repository, not a description of it — is appended to the conversation and sent to Anthropic in
   the next turn. This is a Tier 0, source-confirmed design fact (what the code instructs the
   model to do), not an inference about what the model might happen to do at runtime.

2. **A second, independent stage also reads and can transmit repository content — the packet's
   first draft only analyzed Fix-Gen and missed this entirely.** `src/patchward/subagent.py`
   implements the *triage* stage (per its own module docstring, "Model B architecture" — the
   Perception step that runs **before** Fix-Gen's Action step). `ScannerSubagent` is given its own
   read-only tool surface — `SCANNER_ALLOWED_TOOLS = {"read_file", "grep_files", "glob_files"}`
   (`subagent.py:29-33`) — and its system prompt explicitly authorizes using it: *"You may use
   read_file, grep_files, or glob_files to gather additional context"* (`subagent.py:129`). This
   stage's primary input is serialized SARIF JSON (finding metadata, not raw file content), but
   the tool surface exists specifically so the model can pull in repository content beyond the
   findings when it judges that useful — a second, independent path by which repository content
   can reach Anthropic's API, distinct from and prior to Fix-Gen's. **Correct framing: repository
   source code can reach Anthropic at two stages — triage and fix generation — not one.**
3. **No scrubbing is applied to what's actually sent to Anthropic, and the "one call site" count
   in this packet's first draft was itself wrong — corrected here.** `CredentialProxy.scrub()`
   does exist and can redact the *literal values* of four specific credentials Patchward itself
   loads from its own environment (`ANTHROPIC_API_KEY`, `LANGFUSE_PUBLIC_KEY`,
   `LANGFUSE_SECRET_KEY`, `GITHUB_TOKEN`). A repo-wide search of every call site
   (`grep -rn "\.scrub("`, re-run for this correction) shows it invoked in **two** places in
   `cli.py` (lines 139 and 304, both `message=proxy.scrub(f["message"])` — constructing CLI/log
   display output from a scanner finding's message field), plus one occurrence in
   `credential_proxy.py:27` itself — which, re-checked, is inside that module's own docstring
   `Usage::` example block, not executable code — plus five occurrences in
   `tests/test_credential_proxy.py`. **The count in the first draft ("exactly one place") was
   wrong; the substantive conclusion it supported was not and is unchanged:** `.scrub()` has
   **zero** call sites in `fix_gen.py` or `subagent.py` — nothing scrubs anything on either path
   to Anthropic. Even if it were called there, it would only catch Patchward's own four
   credential values — it has no mechanism to detect or redact a secret that happens to be
   hardcoded in a *customer's* source file (e.g. an accidentally committed API key or a personal
   name in a comment).

**Net effect, stated plainly:** real source code from the customer's repository — whatever it
contains — is transmitted to Anthropic's API as a mandated part of both the triage and
fix-generation stages, with no automated redaction of anything found inside that code. This is a
factual correction to the existing "scrubbed of credentials" description, not a judgment about
whether that data flow is permissible — that's for counsel and for Yehor's own risk decision,
informed by Anthropic's own terms for API data handling (not reviewed as part of this packet).

### No audit trail of what was actually transmitted to Anthropic

Checked `src/patchward/run_log.py` and the real run-log files under `runs/` on Yehor's own
machine (not the git repo, which does not track them). Confirmed two things directly:

- `run_log.py`'s own docstring defines the per-finding record shape as: `finding_id`, `file_path`,
  `rule_id`, `severity`, `model_used`, `branch_name`, `success`, `timestamp` — metadata about a
  Fix-Gen attempt, not its content.
- A real run log was read in full (`runs/session_20260723T131843Z.json`, 460 bytes — one of
  several dozen files of that same exact size in the directory listing) to confirm the schema
  matches reality, not just the docstring. Its actual content is four NDJSON lines of the batch
  form (`{"repo":..., "status":..., "pr_url":..., "error":..., "timestamp":...}`) — again, pure
  status metadata, no prompt text, no file content, no request or response body.

**Practical consequence, stated plainly:** if a customer or a regulator later asks "demonstrate
what data was transferred to your US sub-processor for repo X," there is currently no record
capable of answering that question. Neither run-log format retains the actual payload sent to or
received from Anthropic — only that an attempt happened, on what file, with what outcome. This is
a real gap to put in front of counsel alongside the rest, not a conclusion about whether one is
legally required.

### Commercial model

- **Today:** the CLI is free and open-source; there is no payment code path in it at all.
- **Built but not yet live:** the webhook service's Marketplace billing integration is fully
  functional in code (`marketplace_purchase` webhook handling, `is_entitled()` gating scan runs
  on an active purchase) — but per the project's own backlog notes, there is no live, publicly
  listed paid GitHub Marketplace plan yet. The plan is to list one before relying on this code
  path commercially.
- **Merchant of record:** by design, GitHub is intended to be the merchant of record —
  `webhook.py`'s own module docstring states it "never calls a payments API directly," only
  reacting to Marketplace webhook events to keep entitlement state current.

### Jurisdiction

Denmark, `enkeltmandsvirksomhed` (sole proprietorship), one CVR number, sole trader — as stated
by Yehor. This is a business/legal fact about the operating entity, not something derivable from
the source code, and is included here as self-reported by the business owner rather than
independently verified by this agent.

### Third-party processors

- **Anthropic (US)** — receives Fix-Gen and Verifier prompts, including real repository source
  code per the corrected data-flow description above.
- **GitHub** — hosts the GitHub App, Marketplace listing/billing, OAuth/installation-token
  issuance, and the repositories themselves.
- **Fly.io** — hosts the webhook service and its persistent SQLite volume, region `iad` (US).

---

## Step 3 — Question list for counsel

Each question below carries the specific facts from Steps 1–2 that bear on it.

1. **Is Patchward a "product with digital elements" under the CRA, and is Yehor (or his sole
   proprietorship) a "manufacturer"?** Per the European Commission's own summary of the
   Regulation, a manufacturer is "a natural or legal person who develops or manufactures products
   with digital elements... and markets them under its name or trademark, **whether for payment,
   monetisation or free of charge**" (emphasis reflects the source text). Patchward is currently
   distributed free of charge under the `patchward` name via PyPI and GitHub — does the explicit
   "free of charge" language in that definition mean manufacturer status doesn't turn on the
   billing question at all?
2. **Does an open-source exemption apply, and does it survive a paid Marketplace listing?** The
   CRA's own working materials distinguish "Open Source Stewards" (who don't monetize) from
   "Manufacturers" — but the criteria for which one an entity is, and specifically whether
   introducing a paid GitHub Marketplace plan alongside a free CLI changes that status, is
   explicitly left unresolved in the public working-group materials available to this agent (see
   Step 5's sourcing notes). This is a genuinely open question, not something this session's
   research could settle.
3. **If in scope, is Patchward an Annex III "important" product, and if so Class I or Class II —
   i.e., is self-assessment sufficient or is third-party conformity assessment required?** The
   Annex III category examples this agent found in secondary sources (SIEM systems, malware
   removal/quarantine software, identity/privileged-access-management software for Class I;
   industrial firewalls/IDS/IPS for Class II) do not obviously describe "a static-analysis
   scanner plus LLM-drafted, human-reviewed patch generator" — but this agent did not read the
   full authoritative category list in the Regulation text itself or Commission Implementing
   Regulation (EU) 2025/2392 (adopted 28 November 2025, in force 21 December 2025), only
   secondary summaries of it. Counsel should confirm against that primary text directly.
4. **What changes when GitHub becomes merchant of record for a paid Marketplace listing** — does
   that shift any CRA "manufacturer" or GDPR "controller" responsibility toward GitHub, or does
   it stay with Yehor regardless of who processes payment?
5. **GDPR: is Yehor's sole proprietorship a controller or processor for the data in
   `installations_db`** (account logins, repo names, installation/billing metadata — see Step 1)?
6. **Is a DPIA required?** For background only (see Step 5): GDPR Art. 35 requires a DPIA when
   processing is "likely to result in a high risk to the rights and freedoms" of individuals,
   with named triggers including systematic profiling, large-scale special-category data, and
   systematic public monitoring; the Commission's own guidance illustrates that small-scale
   processing (its example: a single community doctor's patient list) can fall outside that
   requirement. Patchward's current install volume is small and the data does not include special
   categories — but whether that puts it under the "high risk" threshold, now or as it scales, is
   for counsel to assess, not this agent.
7. **Is a Data Processing Agreement (DPA) needed with Marketplace customers**, and if so, does
   one exist today? (None was found in the repository or docs during this session's read.)
8. **Given the corrected Anthropic data-flow fact in Step 2** — real customer source code, not a
   scrubbed prompt, reaching a US sub-processor at *two* independent stages (triage in
   `subagent.py`, then fix generation in `fix_gen.py`), and with no audit trail of what was
   actually transmitted (see Step 2's run-log finding) — does this change the DPIA/controller
   analysis, and does it require disclosure to customers beyond what currently exists?

---

## Step 4 — Draft disclaimer

> **DRAFT — NOT REVIEWED BY COUNSEL. Do not publish this anywhere.**
>
> Patchward is provided on an "as-is" basis. [Operator name / CVR] makes no representation that
> Patchward's use, distribution, or any associated GitHub Marketplace listing has been assessed
> for compliance with the EU Cyber Resilience Act, GDPR, or any other regulation. Users deploying
> Patchward against their own infrastructure, and any organizations installing the hosted GitHub
> App, do so on the understanding that regulatory classification work is in progress and has not
> been finalized. This disclaimer is a placeholder pending qualified legal review and must not be
> treated as a compliance statement.

This draft is intentionally minimal and generic — it is not a substitute for whatever specific
disclaimer language counsel recommends once Steps 1–3 are answered; it exists only so the
pre-distribution gate has *something* on file rather than nothing, and is explicitly not to be
published in its current form.

---

## Step 5 — CRA timeline, re-verified fresh (not inherited from a prior session)

Prior project memory (`BUILD_PLAN_2026-07-10.md`, `memory/CONTEXT.md`) already cited a 24-hour /
72-hour / 14-day ENISA reporting timeline, binding 2026-09-11 — but that figure traced back to an
external research report, only secondarily cross-checked at the time. Per this session's
instruction to verify fresh rather than inherit, the following was re-checked today
(2026-07-24) directly against the European Commission's own Cyber Resilience Act pages
(`digital-strategy.ec.europa.eu`), cross-checked against an independent CRA explainer site.

**Confirmed, from the European Commission's own summary and reporting pages:**

| Milestone | Date |
|---|---|
| CRA entered into force | 2024-12-10 |
| Notification of Conformity Assessment Bodies (Chapter IV) | 2026-06-11 |
| **Reporting obligations (Article 14) become binding** | **2026-09-11** |
| Full applicability / main conformity-assessment requirements | 2027-12-11 |

**This confirms the existing figure was accurate**, but surfaces a nuance the prior memory files
did not carry explicitly: **the September 2026 date is specifically the Article 14
incident/vulnerability-reporting obligation** (24h early warning of an actively-exploited
vulnerability or severe incident / 72h fuller notification / 14-day-or-one-month final report,
via ENISA's Single Reporting Platform) — **not** the date the CRA's full conformity-assessment
regime takes effect, which is over a year later (2027-12-11). One source characterizes reporting
obligations as applying to products already on the market ahead of the full-applicability date,
though this agent did not independently verify that specific carry-over rule against the
Regulation text itself.

**Practical read for the launch-timeline framing (fact, not advice):** Yehor's stated launch
window (public launch 2026-09-08 to 2026-09-11) does land directly on the Article 14
reporting-obligation start date — so if Patchward is in scope for that obligation as a
"manufacturer," the incident-reporting runbook needs to exist by launch regardless of how the
harder Annex III classification question resolves. The classification question itself has more
runway against the 2027-12-11 date, though getting it confirmed before any paid Marketplace
listing remains the existing (and reasonable) internal target.

**Sourcing tier, explicit:**
- **Near-primary (European Commission's own site):** the date table above, and the "manufacturer"
  definition quoted in Step 3, Q1.
- **Secondary (explainer/law-firm/industry sites, not the raw Regulation or Implementing
  Regulation text):** the specific Annex III category examples in Step 3, Q3, and the "open
  source steward" exemption discussion in Step 3, Q2. These should not be treated as exhaustive —
  counsel reading the actual Regulation text and Commission Implementing Regulation (EU)
  2025/2392 is the only way to close this out with confidence.
- **No newer amendment, delay, or change to the 2026-09-11 / 2027-12-11 dates was found** during
  this session's search.

---

## Sources consulted this session (Step 5 / background research)

- [Cyber Resilience Act - Reporting obligations — European Commission](https://digital-strategy.ec.europa.eu/en/policies/cra-reporting)
- [The Cyber Resilience Act - Summary of the legislative text — European Commission](https://digital-strategy.ec.europa.eu/en/policies/cra-summary)
- [CRA Reporting: 24h, 72h & 14-Day Deadlines (Article 14) — cyberresilienceact.eu](https://www.cyberresilienceact.eu/reporting.html)
- [Open Source Software Stewards and CRA Whitepaper — ORCWG](https://github.com/orcwg/orcwg/blob/main/cyber-resilience-sig/whitepapers/stewards-and-cra.md)
- [The 3 product categories covered by the Cyber Resilience Act — theembeddedkit.io](https://theembeddedkit.io/blog/product-categories-cyber-resilience-act/)
- [Cyber Resilience Act: Commission clarifies "important" and "critical" product categories — HSF Kramer](https://www.hsfkramer.com/notes/cybersecurity/2026-posts/cyber-resilience-act-commission-clarifies-important-and-critical-product-categories)
- [When is a Data Protection Impact Assessment (DPIA) required? — European Commission](https://commission.europa.eu/law/law-topic/data-protection/information-business-and-organisations/obligations/when-data-protection-impact-assessment-dpia-required_en)

---

## Close: proposed BACKLOG 12 status update

This session does **not** close BACKLOG item 12. Proposed status update for Yehor to apply:

> **12. Regulatory flags — CRA / GDPR classification — BRIEFING PACKET READY, AWAITING COUNSEL
> ENGAGEMENT (2026-07-24, Session 024).** Technical data inventory, product-facts sheet, question
> list, draft disclaimer, and a freshly re-verified CRA timeline are complete — see
> `memory/BACKLOG12_counsel_briefing_packet_2026-07-24.md`. Still genuinely blocked on finding and
> engaging qualified counsel; nothing agent-startable remains on this item until counsel responds.
> New sub-finding surfaced during this triage: `marketplace_purchases` has no deletion/TTL
> mechanism at all (see new backlog item below) — worth fixing regardless of how the CRA/GDPR
> classification lands.

**New backlog item to log** (from Step 1's confirmed gap): `marketplace_purchases` rows are
never deleted — only `status` is updated to `"cancelled"`. No TTL, no purge job, no
data-minimization policy exists for this table. Recommend a lightweight retention policy (e.g.
delete or anonymize rows N days after `status = "cancelled"` and no re-purchase) as a small,
agent-startable fix once Yehor wants it scheduled — independent of the CRA/GDPR legal answer,
since "don't keep customer billing data forever for no reason" is good practice regardless.
