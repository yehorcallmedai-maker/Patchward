# BACKLOG 12 — Addendum to the Counsel Briefing Packet

**Date:** 2026-08-22 (Session 039) · **Supplements:**
`BACKLOG12_counsel_briefing_packet_2026-07-24.md` (unchanged, still valid) ·
**Status:** FACTS AND QUESTIONS ONLY — no legal conclusions, same hard rule as the
base packet.

**Why this exists:** the base packet was written 2026-07-24 and verified against
Patchward source at HEAD `3e63587`. Two things have changed since. This addendum
records both, re-scopes the question list, and does not restate anything the base
packet already covers. Read the base packet first; read this second.

---

## Part A — The material change: official Commission guidance now exists

**The base packet's Step 5 concluded that "counsel reading the actual Regulation
text and Commission Implementing Regulation (EU) 2025/2392 is the only way to
close this out with confidence." That is now out of date.**

On **27 July 2026** — three days after the base packet was written — the European
Commission published practical guidance on applying the CRA:

| Item | Detail |
|---|---|
| Instrument | `C(2026) 5252` — Communication + Annex (Commission guidance on the application of the CRA) |
| Published | 2026-07-27 |
| Legal weight | **Non-binding**, but it is the Commission's own stated interpretation |
| Basis | Article 26 CRA; developed via the CRA expert group + a 2026 public consultation |

**Why this matters specifically for Patchward** — the guidance is described by the
Commission as addressing, by name, the exact questions this packet poses:

- *"Clarifying when certain products fall within the scope of the Cyber Resilience
  Act, including **remote data processing solutions and free and open source
  software**"* — this is base-packet Questions 1 and 2, and "remote data processing
  solutions" is the category most likely to capture the hosted Fly.io webhook
  service, which the base packet already identifies as the only mode that persists
  third-party data.
- *"How to meet **reporting obligations and risk assessment requirements**"*
  (Section 9.1 of the guidance) — this is the 2026-09-11 obligation itself.
- *"What constitutes a **substantial modification**"* and *"how **support periods**
  should be understood"* — neither was in the base packet's question list; both are
  live for a tool that ships frequent releases.
- **67 practical examples, use cases, flowcharts and graphs, with particular
  attention paid to microenterprises and SMEs.** A one-person
  `enkeltmandsvirksomhed` is squarely the addressee.

**Operational consequence:** the classification questions may now be substantially
answerable from the Commission's own worked examples rather than from first
principles. That is a materially cheaper question to put to counsel — potentially
"confirm our reading of the guidance's example N" rather than "research this from
the Regulation text." **Stated as a fact about the source material, not as a
prediction about the answer.**

### Also new since the base packet

- **Delegated act** on CSIRTs withholding notifications through the Single Reporting
  Platform, adopted 2025-12-11 (`CELEX:32026R0881`). Not in the base packet.
- **Commission FAQ on CRA implementation** — Section 5 covers reporting. Not cited
  in the base packet.
- **ENISA Single Reporting Platform** — confirmed by the Commission (page last
  updated 2026-07-31) as **operational by 2026-09-11**; functional and security
  testing under way. The base packet did not know whether the platform would exist
  in time. It will.

### Re-verified, unchanged

| Claim | Verdict, 2026-08-22 |
|---|---|
| Article 14 reporting obligations bind from **2026-09-11** | CONFIRMED — European Commission's own page, last updated 2026-07-31 |
| 24h early warning / 72h full notification / 14-day final report | CONFIRMED, verbatim from the same source |
| Full applicability / conformity assessment: **2027-12-11** | CONFIRMED |
| Reporting is addressed to the CSIRT of the manufacturer's **main establishment**, shared with ENISA | CONFIRMED — for a Danish sole trader this points at the Danish CSIRT; which authority exactly is a question for counsel, not assumed here |
| No amendment, delay, or change to either date | CONFIRMED — none found |

### The CRA's own open-source language, quoted rather than paraphrased

From the Commission's dedicated CRA open-source page (last updated 2026-05-26),
relevant to base-packet Question 2 and quoted here so counsel sees the source text
rather than this agent's reading of it:

> only free and open-source software that is made available on the market, and
> therefore supplied for distribution or use in the course of a commercial
> activity, falls in scope

> the provision of products with digital elements qualifying as free and
> open-source software that are not monetised by their manufacturers should not be
> considered to be a commercial activity

**The fact pattern this has to be applied to — stated neutrally, not resolved:**
Patchward's CLI is distributed free of charge via PyPI under an open-source licence
and is not monetised today. The hosted webhook service contains fully-functional
GitHub Marketplace billing code, gated by `is_entitled()`, with no live paid plan
listed yet. **Whether "not monetised" survives the existence of built-but-unlisted
billing code, and whether it survives the moment a paid plan goes live, is a
classification judgment for counsel.** This agent has deliberately not formed a
view, and the base packet's hard rule against hedging toward a legal conclusion
applies here unchanged.

---

## Part B — Technical re-verification against current source

The base packet was verified at Patchward HEAD `3e63587`. Current HEAD is
`b5a02ed40064dc68fdcc9254883f0216ca61075d` — **42 commits later**. Every
load-bearing technical claim in the base packet was re-checked against current
source today.

### Still accurate — no change needed

| Base-packet claim | Re-verified 2026-08-22 |
|---|---|
| `installations` / `installation_repos` / `marketplace_purchases` schema | Unchanged |
| `marketplace_purchases` has **no deletion path at all** | Still true — `DELETE FROM` exists only for `installation_repos` and `installations` |
| **Zero** `.scrub()` call sites in `fix_gen.py` or `subagent.py` | Still true — the packet's central data-flow finding stands |
| `.scrub()` invoked only in `cli.py` (CLI/log display output) | Still true — now at lines 143 and 308 |
| `is_entitled()` gates the scan pipeline on an active Marketplace purchase | Still true — `webhook.py:414` |
| Anthropic / GitHub / Fly.io as the three third-party processors | Unchanged |

### Stale details — corrected here, none affecting any question posed to counsel

1. **`CredentialProxy`'s credential set widened from 4 keys to 8.** The base packet
   states `.scrub()` covers `ANTHROPIC_API_KEY`, `LANGFUSE_PUBLIC_KEY`,
   `LANGFUSE_SECRET_KEY`, `GITHUB_TOKEN`. It now also covers
   `GITHUB_APP_PRIVATE_KEY_B64`, `GITHUB_APP_PRIVATE_KEY`, `GITHUB_APP_ID`,
   `GITHUB_WEBHOOK_SECRET` (BACKLOG 25 — real security hardening closing a
   cross-tenant exposure, not cosmetic). **This strengthens Patchward's position
   slightly and changes no question.** The packet's actual finding — that scrubbing
   covers only Patchward's *own* credentials and nothing in a customer's source
   code, and is not applied on either path to Anthropic — is unaffected.
2. **Test-file occurrence count.** The base packet cites "five occurrences in
   `tests/test_credential_proxy.py`"; there are now seven. Immaterial.
3. **`README.md`'s stale line** — *"Patchward is not yet published to PyPI. Install
   from source"* — flagged as an out-of-scope aside in the base packet on
   2026-07-24 and **still uncorrected today, a month later.** Not a legal issue;
   noted again so it does not disappear a second time.

**Verdict on the base packet: READY TO SEND, unchanged, with this addendum
attached.** The counsel-facing content of Steps 1–5 is accurate. Nothing in Part B
alters a single question in Step 3.

---

## Part C — Revised question list for counsel

The base packet's eight questions all remain live. The Commission guidance
re-shapes how three of them should be *asked*, and adds two that were missing.

### Re-shaped by the new guidance

| # | Base-packet question | How to ask it now |
|---|---|---|
| Q1 / Q2 | CRA scope; manufacturer vs. open-source steward; does the exemption survive a paid Marketplace listing? | Ask counsel to apply the **Commission guidance's own worked examples on free and open-source software** to this fact pattern, rather than reasoning from the Regulation text alone. Cheaper, and grounded in the Commission's stated interpretation. |
| Q3 | Annex III "important" product, Class I or II? | Same — the guidance's scope section and 67 examples should be the starting point, with Commission Implementing Regulation (EU) 2025/2392 as the authority behind it. |
| Q8 | Does the Anthropic data flow change the analysis? | Add the guidance's **"remote data processing solutions"** scope discussion — the hosted webhook is likely to be assessed under that heading, which did not exist as a named category when the base packet was written. |

### New — not in the base packet, surfaced by the guidance

- **Q9 — Substantial modification.** What counts as a "substantial modification"
  for a tool that ships frequent releases, and does a release cadence like
  Patchward's trigger re-assessment obligations?
- **Q10 — Support period.** What support period must be declared, how is it
  determined for a one-person operation, and what does committing to one actually
  oblige?

### The one question that is now urgent rather than merely open

- **Q0 — Does the 2026-09-11 Article 14 reporting obligation apply to Patchward, in
  its current state, on that date?** Everything else in this packet has runway to
  2027-12-11. This one does not. **If the answer is yes, an incident-reporting
  runbook (who reports, to which Danish CSIRT, within 24h/72h/14d, via the ENISA
  Single Reporting Platform) has to exist by 2026-09-11.** If the answer is no, it
  should be recorded on file *why* not, dated, so the position is defensible later.

**This is the question to get answered first. It is the only one with a deadline
inside 30 days.**

---

## Sources consulted for this addendum (2026-08-22)

- [Cyber Resilience Act — Reporting obligations, European Commission](https://digital-strategy.ec.europa.eu/en/policies/cra-reporting) (page last updated 2026-07-31)
- [Commission publishes new guidance to support timely Cyber Resilience Act implementation, European Commission](https://digital-strategy.ec.europa.eu/en/library/commission-publishes-new-guidance-support-timely-cyber-resilience-act-implementation) (2026-07-27)
- [C(2026) 5252 — Annex — Commission guidance on the application of the CRA](https://ec.europa.eu/newsroom/dae/redirection/document/131456)
- [C(2026) 5252 — Communication on the CRA guidance](https://ec.europa.eu/newsroom/dae/redirection/document/131455)
- [Cyber Resilience Act — Open source, European Commission](https://digital-strategy.ec.europa.eu/en/policies/cra-open-source) (page last updated 2026-05-26)
- [Cyber Resilience Act — Legal text (Regulation (EU) 2024/2847)](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A32024R2847)
- [Delegated act on CSIRTs withholding notifications (CELEX:32026R0881)](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32026R0881)
- [ENISA — Single Reporting Platform FAQ](https://www.enisa.europa.eu/topics/product-security-and-certification/single-reporting-platform-srp)

**Sourcing tier, explicit:** every item above is primary or near-primary (European
Commission, EUR-Lex, ENISA). Unlike the base packet's Step 5, this addendum relies
on **no** secondary explainer or law-firm sources for any load-bearing claim.
