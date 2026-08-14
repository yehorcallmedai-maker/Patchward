# Cross-Session Retrospective Skill — Build Document (v1)

## Provenance

**5 independent responses (N=5, above the 3-model floor).** Model identities were
not provided — the answers were pasted inline rather than saved with the
`<subject>_<model>_<date>.md` naming convention the process calls for. Labeled
R1–R5 by order of appearance, arbitrary, not meaningful. **This is a real gap,
not a formality:** family-independence weighting (agreement between relatives is
weaker evidence than agreement across families) cannot be applied — treat every
"N/5" count below as a raw count, not a family-adjusted one. Two stylistic tells
worth noting without asserting identity: R2 cites real external sources with URLs
(academic papers, Google SRE/NIST/USACE docs); R5 uses LaTeX-style math notation
mid-prose ("Sessions 1 through $N-3$"). If you want full provenance rigor on a
future run, save each answer with its model name before bringing it back.

**Synthesist:** Claude (this conversation), deliberately excluded from the panel
per the skill's own provenance rule — the ground-truth block already carries my
architectural framing, so including me on the panel would double-count my
perspective.

**Prompt version:** v1.0, 2026-08-14, confirmed all 5 answered the full lettered
structure (A–I). No skipped sections observed.

**Tier thresholds for N=5** (per the skill's own scaling rule): HIGH = 4–5/5,
MEDIUM = 2–3/5, OPTION = 1/5, CONFLICT = direct contradiction regardless of count.

---

## Decisions (HIGH confidence — 4-5/5 independent agreement)

**D1. Never make transcript/conversation-log access load-bearing for the core
mechanism.** 5/5. Every response either avoids transcript reads entirely (R1,
R5 — purely file/git-based) or explicitly tier-gates them as an optional
enhancement with named degradation when unavailable (R2 "optional transcript
audit"; R3 explicitly "does not read... transcript access is UNTESTED and not
portable"; R4 explicitly scopes its transcript-diffing mechanism to "tier-a
only" with named fallbacks for tiers b/c). This directly and unanimously honors
GROUND TRUTH 6/7's constraint — no adjudication needed, it's a correct reading
of the ground truth, not just consensus for its own sake.

**D2. Compression/heavy-audit work must be threshold-triggered, never
"remember to do it."** 5/5, though the trigger shapes differ (R1: 5
sessions/8KB; R2: soft/hard byte triggers + every-8th-close cadence; R3: entry
count/byte/duplicate-header/session-count triggers; R4: 5 sessions/calibration
threshold/explicit request; R5: continuous 5-session sliding window). This is
the single most load-bearing finding of the whole synthesis: it's a direct,
mechanical fix for GROUND TRUTH 3 (the compression rule exists today and is
simply not enforced). **Adjudication note:** this counts as HIGH not because
5 models independently invented triggering — the prompt's own D section
explicitly demanded "concrete triggers and thresholds," so convergence on
*having* triggers is partly an echo of the question's own wording. What
remains genuine independent evidence is that all 5 converged on triggers being
*mechanical/self-enforcing* rather than advisory — none proposed "flag it and
hope," which the prompt did not demand.

**D3. Every routine session-open reads a bounded artifact, not the full
historical log.** 5/5 at the principle level (see also D1). All five keep
Mission/Current-state/Open-threads/Heuristics in a hot file and push older
session-log/calibration detail elsewhere (archive file, per-session cold files,
or a rolled-up summary line).

**D4. Stale-claim risk needs an explicit freshness/age mechanism on carried-over
claims, not just "re-verify everything."** 4/5 (R1's "Last Verified" timestamp
+ evidence field; R2's `UNVERIFIED_CARRYOVER` status stamped on every inherited
claim at open; R4's per-open-thread "fact-age tag" with a 3-session staleness
threshold; R5's git-diff cross-reference that auto-purges claims contradicted by
commit history, calling it a "handoff hallucination"). R3 has the weaker
version of this (a 3-day freshness line on the *opening prompt as a whole*,
not per-claim) — present but less granular, so counted as partial/aligned
rather than a 5th full vote. **Adjudication:** this is the mechanism that
would have caught GROUND TRUTH 5's actual observed failure (a handoff
asserting two P0s were still open when they'd been fixed 3–6 days earlier) —
worth weighting heavily since it maps to a real, not hypothetical, incident.

**D5. Failed/demoted approaches and closed threads are demoted to cold
storage, never silently deleted.** 5/5, consistent with GROUND TRUTH 2's
existing "negative knowledge is knowledge" rule already in the current system
— this is arguably the lowest-information agreement in the set, since it's
close to restating an existing rule rather than new architecture. Included for
completeness, not weighted as a strong independent finding.

---

## Leading options (MEDIUM confidence — 2-3/5)

**M1. A per-session cold-storage file, separate from the rolled-up ledger.**
3/5 explicitly propose a new mechanism for this (R1's archived
`NEXT-SESSION.md` copies; R2's session capsules; R5's
`.strategy/sessions/session-NN.md`). R3 relies on the *already-existing*
session-close deliverable (dated `SESSION_CLOSE_<date>.md` files) rather than
proposing a new artifact — arguably not a competing option so much as "reuse
what's already there," worth noting as the cheapest version of this idea. R4
declines local per-session files entirely, instead depending on the platform's
own session-history API — the one proposal that runs directly into GROUND
TRUTH 6's untested-capability warning, though R4 handles that risk correctly
by tier-gating it (see D1).

**M2. The retrospective/compression function should live in a separate file
from the hot ledger** (not additional sections crammed into `STRATEGY.md`
itself). 3/5 (R1's `STRATEGY-ARCHIVE.md`; R4's `RETROSPECTIVE.md` +
`ARCHIVE.md`; R2's `.strategy/archive/` + `retrospectives/*.md`). Against
this: R3 and R5 both add sections *directly into* `STRATEGY.md` (Incidents
ledger / Retrospective summary; Active Heuristics / Compacted Session Log)
and keep it a single file. This is a real, practical fork — see Open
Decisions.

**M3. A structured incident-detection checklist/scan is the primary mechanism
for surfacing unlogged incidents without a human prompting for them.** All 5
proposed *some* version of this, but they split into two genuinely different
mechanisms worth distinguishing rather than merging:
- **Self-report checklist at close** (R1's 4 yes/no incident probes; R3's 5
  yes/no incident-harvest questions; R5's mandatory adversarial audit pass
  over `git diff`) — 3/5. Cheap, works at every tier, but is answered by the
  same model that did the work — a structurally compromised evaluator
  (Lens L3's own framing).
- **External/mechanical pattern scan against a different artifact** (R2's
  transcript-vs-ledger diff; R4's adversarial pattern scan for
  incident-shaped markers in transcripts, tier-gated) — 2/5, weaker count but
  structurally stronger (an external check, not self-report) *where the
  capability exists*.

These are not equivalent under any reasonable rule — one is self-report, the
other is an independent check — so they are **not tiered together** despite
both nominally answering "how do you catch incidents." See Open Decisions.

---

## Single-model options (attributed, not decisions)

**O1 (R2 only).** A `PROJECT_ID` + `OPEN_SESSION` identity-gate file pair,
checked *before every write*, that blocks mutation on a root/repository
fingerprint mismatch. This is the only proposal that turns GROUND TRUTH 5's
near-miss (an unrelated same-named repo almost getting a production edit) into
a **preventive gate** rather than a **detective/retrospective check** — every
other model's mechanism catches this after the fact, in review; R2's catches it
before the write happens. Worth flagging as unusually well-argued: it directly
answers "how would this have surfaced the near-miss" with a mechanism that
doesn't depend on any review step running at all.

**O2 (R2 only).** Cites two real external findings to justify the
self-assessment design: LLM self-correction can fail or degrade answers
without external feedback (Huang et al.), and models show self-preference bias
evaluating their own generations (Panickssery et al.). Conclusion drawn: "the
same model remains a compromised evaluator... adversarial wording is
supplementary; file state, tests, repository state and user corrections are
the evaluator." No other model grounded its self-assessment design in external
evidence this directly — the other four rely on structural mechanisms
(checklists, forcing functions) without stating *why* those mechanisms are
necessary beyond "LLMs might grade themselves generously."

**O3 (R5 only).** "Mandatory Mission & Constraint Challenge every 10
sessions" — a scheduled re-litigation of the project's foundational
assumptions, proposed as the mitigation for a failure mode R5 itself named
("Stale Architecture Lock-in... early architectural assumptions become
fossilized dogma"). No other model raised this failure mode at all. It's a
genuinely different risk than the others identified (which mostly worry about
losing *facts*; this one worries about losing the *ability to question
decisions*) — worth carrying forward even though it's a single-model idea.

**O4 (R4 only).** Precision tracking on the incident-detection mechanism
itself: "if verified-real / total-candidates drops below ~20% for two audits
running, the pattern-scan heuristics need re-tuning." This is the only
proposal that treats the detection mechanism as something that can itself
silently degrade and defines a numeric tripwire for catching that. Directly
useful if M3's external-scan option is adopted.

**O5 (R1 only).** A written pre-mortem clause before every calibration score
("If this session later turns out to have failed, the most likely reason is
___"), cross-checked against the score itself — if the pre-mortem names a real
risk but the score is 1.00, the score is capped at 0.90 pending reconciliation.
A cheap, concrete forcing function distinct from the others' checklist
approach.

---

## Open decisions — needs your call

**OD1. Third skill, or fold into the existing two?** Split 2/5 (R1, R4: yes,
periodic third skill) vs 3/5 (R2, R3, R5: no, extend the existing two) — close
enough, and foundational enough, that I'm not resolving it by count. Both
sides' reasoning:

- **For a third skill (R1, R4):** the function has a genuinely different
  *cadence* (multi-session, not per-session) and a genuinely different *input*
  (cross-session pattern, not single-session state) than either existing
  skill. Cramming a periodic function into a per-session skill risks either
  running it too often (cost) or it silently never running (GROUND TRUTH 3's
  actual failure — a rule that existed but nobody enforced). A separate,
  named skill is at least *invocable on purpose* and auditable as its own
  thing.
- **Against (R2, R3, R5):** a third skill is one more thing to remember to
  invoke — and R4 itself concedes this as its #1 self-identified failure mode
  ("Audit skipped/forgotten... an extra skill to remember to invoke"). Folding
  the trigger-check into `session-close`'s own existing Phase 5 ("Learn")
  means the check-for-due-audit piggybacks on something that already runs
  every session by construction, which is a stronger enforcement guarantee
  than a periodic skill's own discipline.

**Synthesist's note** (not a model vote, marked separately per the skill's
own rule): R4's self-critique is the detail that tips this for me. A skill
that itself admits its main failure mode is "gets forgotten" is arguing
against its own premise. I'd fold the *trigger check* into `session-close`
(R4's "is an audit due?" surfaced in the existing close-out, which R4
proposed as a belt-and-suspenders safeguard even within its own third-skill
design) regardless of which way OD1 resolves — that part isn't actually in
tension with having a separate skill do the *work* once triggered.

**OD2. Where does the retrospective/compression output live — inside
`STRATEGY.md` itself, or a separate file?** M2 above: 3/5 separate file, 2/5
inside `STRATEGY.md`. Trade-off, stated plainly: a separate file keeps
`STRATEGY.md` smaller (helps D3) but adds a second file every session-open
routine has to know about (partially undercuts D3's own goal if the second
file isn't actually optional). A section inside `STRATEGY.md` is simpler to
reason about but re-creates exactly the bloat-via-accretion pattern that
produced the measured 181KB failure in the first place, unless the section's
own size is independently capped (R3 does cap it — "≤500 words" — R5 does
not cap its equivalent sections explicitly).

**OD3. The hot-file byte ceiling — no real convergence on a number.** Spread:
R1 8,000 bytes / R2 24,576 bytes (24 KiB) / R3 ~80,000 bytes trigger,
~37–40,000 bytes steady-state / R4 ~40,000 bytes target / R5 ~10,000–15,000
bytes steady-state. That's roughly a 5x spread between the most and least
aggressive proposals — this is a genuine specific-level conflict under any
reasonable equivalence rule, not something to average into "~30KB." The
aggressiveness trade-off is explicit in the responses that named it: smaller
ceilings (R1, R5) compress more often and risk R3/R1's own named failure mode
("summary atrophy" / "retrospective-induced amnesia" — losing a
guard-condition or a Tuesday-only failure detail in compression); larger
ceilings (R3, R4) hold more verbatim history but concede more of the context
tax the whole exercise exists to eliminate. No model gave empirical grounds
for its specific number — all are judgment calls. **This is a real number you
have to pick, not something the research can settle further** — see
Confidence, section D below.

**OD4. Self-report checklist vs. external pattern-scan for incident
detection (M3).** Not a count disagreement so much as a capability-tier
question: the external-scan approach (R2, R4) is structurally stronger — it
doesn't ask the same model that may have missed something to also grade
whether it missed something — but it's only available where transcript
access actually works (tier-a, per GROUND TRUTH 6's UNTESTED status). The
self-report checklist (R1, R3, R5) works at every tier but is weaker exactly
where it matters most (a session that made a mistake and didn't notice it is,
by construction, unlikely to flag it in its own checklist). **Recommendation
worth stating plainly rather than hedging:** run both, layered — self-report
checklist always, external scan opportunistically when the tier allows it,
never designed as either/or. None of the 5 explicitly proposed running both
as complementary rather than as alternatives; this is a synthesist's note,
not a tiered finding.

---

## What the research could not answer

**The incident-detection mechanisms are validated only against the two cases
they were told to solve.** GROUND TRUTH 5 named exactly two incidents
(prompt-injection-shaped pasted content; a near-miss wrong-repo edit), and
Section E's own question directly asked "how would this have surfaced these
two incidents." Unsurprisingly, R2's, R4's, and R5's mechanisms map cleanly
onto exactly those two cases — this is expected convergence given the prompt's
own wording (an **echo**, per the skill's own adjudication rule, not
independent evidence of general robustness). **Genuine unknown, flagged
honestly by the models themselves:** R4 self-rated its own incident-scan
mechanism LOW confidence — the only LOW rating across all 5 responses on any
section — specifically because "real transcripts may produce far more noise
than assumed," i.e., the false-positive rate on *incidents nobody thought to
name in advance* is untested by construction. No amount of re-reading these
five answers resolves this; it needs a trial run against real transcripts
containing incidents the prompt didn't pre-specify.

**Byte-ceiling numbers (OD3)** are five judgment calls, not five
measurements — none of the models ran or cited an actual compression trial.

**Whether a scheduled third skill actually gets invoked reliably in practice**
(OD1's core tension) is not resolvable from architecture alone — it's an
empirical question about this specific environment's habits, which none of
the 5 could test from inside a single response.

---

## Decision log

- **[2026-08-14] OD1 — Fold into the existing two skills; no third skill.**
  Decided by Claude, responsibility explicitly taken by Yehor. Rationale: R4's
  own self-identified top failure mode ("gets forgotten — an extra skill to
  remember to invoke") argues against its own premise; `session-close`'s
  existing Phase 5 ("Learn") can carry an "is a retrospective due?" check for
  free, every session, by construction — a stronger enforcement guarantee than
  a periodic skill's own discipline.
- **[2026-08-14] OD2 — Retrospective output lives in a separate file
  (`RETROSPECTIVE.md`), not a section inside `STRATEGY.md`.** Rationale: the
  measured 181KB failure happened because everything lived in one growing
  file; a section-word-cap (R3's approach) depends on the model remembering
  to enforce it every close, the same self-discipline gap D2 already
  identified. A separate file's size is mechanically checkable on its own,
  independent of model discipline.
- **[2026-08-14] OD3 — Hot-file (`STRATEGY.md`) byte ceiling: 16,000 bytes.**
  Rationale: roughly the middle of the observed 8–40KB spread across the 5
  responses, deliberately biased toward the conservative end. The
  demonstrated failure (181KB, real, dated 2026-08-14) is runaway growth;
  information lost to over-aggressive compression is a hypothesized risk with
  zero observed incidents to date. Bias the number toward the failure that
  already happened, not the one that might.
- **[2026-08-14] OD4 — Run both incident-detection mechanisms, layered, not
  either/or.** Self-report checklist (M3) runs at every capability tier;
  external pattern-scan against transcripts/git (M3's second variant) runs
  opportunistically wherever tier access allows, per G's degradation-tier
  design. Confirmed as the decision, not left as a synthesist's aside.

**Document version: v1.1** (decisions logged; supersedes v1's open items for
OD1–OD4 specifically — Provenance, the Decisions/Leading-options/Single-model
sections, and What-the-research-could-not-answer remain unchanged from v1 and
are not relitigated by this log entry).
