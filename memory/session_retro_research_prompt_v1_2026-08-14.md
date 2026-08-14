# Research Prompt v1 — Cross-Session Retrospective Skill ("learning how to learn")

**Prompt version:** v1.0 (2026-08-14). Pin this. All N models must answer this
byte-identical text. If an error is found mid-run, re-run the affected models —
do not patch one model's copy, or the tiering will misread a question-difference
as a model-disagreement.

---

## ROLE

You are a systems architect who designs **durable operating procedures for AI
agents** — the written protocols that let an agent working in a fresh, memoryless
session pick up a long-running project without re-deriving everything, and get
measurably better at doing so over time. Your expertise spans knowledge
management, incident-review practice (post-mortems, after-action reviews),
calibration and forecasting scoring, and the practical limits of LLM context.

You are NOT designing a product, a UI, or a memory *database*. You are designing
a **skill document**: prose instructions an LLM reads and follows, which produce
and consume plain-text artifacts on disk.

---

## GROUND TRUTH — verified facts. Do not invent beyond this.

Every fact below was directly checked on the target machine on 2026-08-14. Treat
it as fixed. Where a fact is marked UNTESTED, do not build a load-bearing
recommendation on it.

**1. Two related skills already exist and form a closed loop.** Any new skill
must justify its existence against them or be rejected as duplication.

- `session-strategy-synthesis` (session OPEN). Loop:
  *Ground → Verify → Synthesize → Commit → Learn.* Reads a persistent memory
  file, extracts its claims as hypotheses, verifies each with two independent
  passes (direct read + different-method re-check), then plans at three nested
  zoom levels (L1 project horizon → L2 testable session goal → L3 immediate next
  step), then updates the memory with calibration and heuristics.
- `session-close` (session CLOSE). Loop:
  *Reconcile → Verify → Judge → Seal → Learn.* Reconciles durable state (git),
  applies the same two-pass verification to every claim the session produced,
  judges the session at the same three zoom levels, writes a dated close-out
  document including an explicit "weakest points, stated plainly" section and a
  next-session opening prompt, then updates the memory.

**2. The shared memory artifact.** Both skills read/write
`<project-root>/.strategy/STRATEGY.md`, a plain-Markdown file with mandated
sections: Mission, Success criteria, Current state, Open threads, Heuristics
(earned), Failed approaches (ledger), Session log, Calibration record.

Documented rules for it:
- Claims must be *checkable* — "making good progress" is explicitly banned;
  a claim must name the file/artifact/command that proves it.
- Heuristics require **two logged sessions of evidence** to be promoted; **one
  logged failure** to be demoted. Demoted heuristics stay visible ("negative
  knowledge is knowledge").
- Calibration = confirmed claims / checked claims, one line per session. Below
  0.7 for two consecutive sessions triggers a memory-hygiene thread.
- **Compression rule:** "When the Session log exceeds ~15 entries, compress the
  oldest into one summary entry rather than deleting them." The format file
  states plainly: "this file is read at the start of every session, so bloat
  directly taxes future sessions."

**3. The compression rule is not being followed, and this is measured, not
alleged.** On the one real project using this system, `STRATEGY.md` is
**181,415 bytes / 2,609 lines** after ~16 sessions. It has accumulated duplicate
`## Session log (continued)` and `## Calibration record (continued)` headers
instead of single append-only sections. The project's own memory file flags this
as a known, unfixed problem. **A file read at the start of every session has
grown to a size that itself consumes a significant fraction of the context it
was meant to save.** This is the single most important verified failure in the
current design.

**4. The calibration mechanism demonstrably works.** Real scored history from
that project, in order: 0.75, 0.94, 1.00, 0.88, 1.00, 0.94. The scores move,
they are argued for in prose, and at least one session scored itself *down*
(0.88) for a defect that its own review passes missed and only the close caught.
Self-scoring has produced non-trivial, non-flattering output at least sometimes.

**5. What neither existing skill does: read the actual prior conversation.**
Both skills read only the *distilled artifact* the previous session chose to
write. Nothing reads the previous session's real transcript. Consequences
observed on the real project:
- Two significant process incidents in one session (a prompt-injection-shaped
  artifact embedded in a pasted message; a near-miss where an unrelated repo
  with a similar name was almost edited in production) reached the memory file
  **only because a human explicitly directed that they be recorded.** Nothing in
  either skill would have surfaced them.
- A handoff prompt for a later session asserted two priority-zero items were
  still open. Both had in fact been fixed 3–6 days earlier. The stale claims
  came from a *summary*, and were only caught because the next session
  re-verified against ground truth instead of trusting the handoff.

**6. Session-history mechanisms actually present on this machine** (checked
directly):
- `~/.claude/history.jsonl` — 47 lines. Shape per line:
  `{display, pastedContents, timestamp, project, sessionId}`. This is **prompt/
  command history, not conversation transcripts.**
- `~/.claude/sessions/*.json` — two files, 266 and 291 bytes. Pointer/metadata
  scale, **not transcripts.**
- `~/.claude/projects/<slug>/memory/` — exists, declared as a persistent memory
  location, and is **empty** despite being available for months.
- A transcript-search capability (`search_session_transcripts`, `list_sessions`,
  `get_session`) is advertised in this environment's tool list. **UNTESTED:** its
  actual retention window, coverage, and whether it returns full text or only
  matched excerpts were not verified. Do not assume full-transcript retrieval is
  available; treat it as a possible enhancement, never as a required dependency.

**7. The artifact must be portable.** The target is a *general-use* skill for any
model, any project, any environment — including ones with no transcript access,
no git, and no MCP tooling at all. Environment-specific capability may be used
opportunistically but must never be load-bearing.

**8. A recurring, verified failure mode in this exact workflow:** valuable
content produced during a session (a full analysis document, a complete skill
definition) existed only in conversation and was **never written to disk**,
requiring re-materialization one to three days later. This happened at least
twice on the real project. Any design that assumes "the model will remember to
save it" is contradicted by observed evidence.

---

## LENSES

Apply all five. Each is defined here so every model uses the same definition
rather than its own reading of the label.

**L1 · Retrieval architecture.** By what concrete mechanism does session N+1
obtain knowledge of session N? Evaluate the real candidates — full transcript
replay, a distilled artifact written at close, a structured event log, or a
hybrid — against fidelity (what is lost), cost (context consumed at every future
open), and portability (does it work with no special tooling).

**L2 · Compression and decay.** What survives, in what compressed form, for how
long, and on what trigger. A ledger that only grows eventually costs more to read
than it returns. Address explicitly: what gets summarized, what gets demoted to
cold storage, what is deleted outright, and who or what decides.

**L3 · Self-assessment integrity.** A session grading its own work is a
structurally compromised evaluator. Identify the specific mechanisms that make
honest self-critique likely rather than merely requested — structural forcing
functions, falsifiable claim formats, adversarial framing, external anchors.
Assume the instruction "be honest about weaknesses" is necessary but insufficient.

**L4 · Portability and graceful degradation.** The skill must produce value at
three capability tiers: (a) full — transcript access, git, tooling; (b) typical —
files and git only; (c) minimal — files only, no version control, no history.
Define what the skill does at each tier and what it explicitly declines to claim
when running degraded.

**L5 · Learning yield.** Distinguish what measurably improves the *next* session
from what merely documents the last one. For each proposed output, state the
mechanism by which a future session is concretely better off. Anything that
cannot answer that question is ceremony and should be cut.

---

## OUTPUT STRUCTURE

Answer in these lettered sections, in order. **Give decisions, not options.**
Name specific mechanisms, specific formats, specific thresholds, specific
numbers. "Consider tracking metrics" is a non-answer; "score X as
confirmed/checked, flag below 0.7 twice consecutively" is an answer. Where you
genuinely believe a choice is the user's to make, say so explicitly and state
which way you would decide and why — do not hedge silently.

**A · Existence and scope.** Given that `session-strategy-synthesis` and
`session-close` already exist (GROUND TRUTH 1), state your decision: should a
third, separate retrospective skill exist, or should this capability be folded
into the existing two? Defend it. If separate: define the exact boundary — what
this skill does that neither existing one does, and what it must not duplicate.
If folded in: specify which skill absorbs what.

**B · Retrieval architecture (L1).** Your decision on how session N+1 reaches
session N. Name the mechanism, the artifact(s), and the exact read sequence at
session start. State what is lost under your choice and why that loss is
acceptable.

**C · The artifact schema.** The exact structure of what gets written — section
names, required fields, an example entry with realistic content. If you propose
changing or replacing `STRATEGY.md`'s existing schema (GROUND TRUTH 2), give the
migration path for a 2,609-line existing file.

**D · Compression and decay policy (L2).** Your decision, with concrete triggers
and thresholds. It must demonstrably prevent the measured 181KB failure
(GROUND TRUTH 3). State what the file size looks like at session 50 under your
policy, and show the reasoning.

**E · Self-assessment integrity (L3).** The specific structural mechanisms.
For each, state the failure it prevents and how you would detect that it stopped
working. Address directly: how would this skill have surfaced the two incidents
in GROUND TRUTH 5 *without* a human prompting for them?

**F · The next-session payload (L5).** Precisely what a fresh session receives
and in what order it reads it. Include the handling of stale-claim risk — the
GROUND TRUTH 5 case where a handoff asserted two closed items were open. State
how your design prevents a confident-but-stale handoff from misdirecting the
next session.

**G · Degradation tiers (L4).** What the skill does at each of the three
capability tiers, and what it explicitly refuses to claim when degraded.

**H · Failure modes and anti-patterns.** The three most likely ways your own
design fails in practice, each with the early symptom that would reveal it. Be
specific and adversarial toward your own proposal. Include at least one failure
mode that is *caused* by your design rather than merely unaddressed by it.

**I · Confidence.** Rate each of sections A–H as HIGH / MEDIUM / LOW confidence,
and for each non-HIGH rating state precisely what evidence or test would raise
it. Self-rated confidence is not evidence, but a section that many models mark
LOW is a reliable signal that the ground truth was thin there.

---

## MERGE NOTICE

You are one of several models answering this identical prompt **independently**.
You cannot see the others' answers and they cannot see yours. All answers will be
reconciled by a separate synthesis pass that tiers claims by how many models
reached them independently: agreement across models becomes a settled decision,
a single model's proposal remains an attributed option, and direct contradictions
are surfaced to the human with both sides intact — **never averaged.**

Two consequences for how you should answer:

1. **Precision beats breadth.** A specific, falsifiable, possibly-wrong
   recommendation is far more useful to this process than a hedged survey of
   possibilities. Hedging cannot be merged — it dissolves.
2. **Do not try to be comprehensive or balanced for its own sake.** Commit to
   positions. If you hold a minority view you can argue well, state it plainly
   and give your reasoning — a well-argued single-model position is explicitly
   preserved and flagged rather than discarded.

Do not speculate about what other models will say. Do not soften a position to
seem more mergeable.
