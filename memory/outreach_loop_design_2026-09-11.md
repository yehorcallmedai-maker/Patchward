# Patchward Daily Outreach & Feedback Loop — Design Document

Status: DESIGN ONLY. No automation exists yet. No code has been written
for this. This document exists to get the guardrails agreed on paper
before anything runs against a real repo or a real inbox — per this
project's own standing discipline of reviewing before building anything
that touches external, real-world targets (same review-before-build
pattern applied to every git write, every heuristic promotion, and every
STRATEGY.md edit tonight).

Origin: this design responds to the go-to-market/automation idea Yehor
floated at this session's open (logged in `.strategy/STRATEGY.md` under
Open threads) and to a second-model review that correctly identified two
points in that idea needing a hard gate rather than an engineering
answer. Both review claims were independently checked before this
document treated them as settled — see "Claims checked" at the end.

## 1. Non-negotiable constraints

These hold regardless of anything else decided below or later:

1. **No fully autonomous "find a repo and run" path exists anywhere in
   this design.** Every repo Patchward runs against was put on the list
   by Yehor, explicitly, before any run happens. There is no code path
   that selects a repo Yehor has not already approved.
2. **Patchward's own existing behavior — draft PR, never auto-merge — is
   preserved and is a load-bearing safety property of this whole
   design, not incidental.** (Confirmed against `patchward-landing`'s
   own site copy: "Patchward opens a draft PR. It does not merge to your
   main branch under any circumstance." This is a Tier-1 check — site
   copy, not source code directly inspected this session — consistent
   with everything else this project has stated about Patchward's
   mechanism, and not contradicted anywhere.)
3. **Email replies are created as Gmail drafts by default, sent only by
   Yehor's own hand, for now.** Per Yehor's own answer when asked
   directly, this is NOT locked in as a permanent, un-revisitable rule —
   he wants to "figure it out with time." So: the architecture below
   implements draft-only with no auto-send code path *built*, but this
   document does not claim the decision is closed forever. If Yehor
   later wants auto-send for a specific, trusted use case, that is a new
   design decision made deliberately then — not a toggle sitting
   dormant in this codebase waiting to be flipped. Concretely: no
   `send()` call against the Gmail API exists in this design at all,
   in any form, gated or not. Adding one later is new work, not a
   config change.
4. **A single stop switch halts all scheduled runs immediately**, checked
   at the start of every scheduled invocation before it does anything
   else (repo scan, email read, or PR open).
5. **A digest reports to Yehor; it does not feed back into the system's
   own behavior without Yehor reading it and approving a specific
   change.** No component of this design reads its own past outcomes to
   change its own future targeting or messaging.

## 2. Target-repo model: recommendation

Yehor asked for a reasoned recommendation rather than picking between the
two options himself. Recommendation: **start with a Yehor-maintained
shortlist (Option A), with Option B (propose-and-approve) as an explicit
Phase 2, not built now.**

Reasoning:
- Option A is strictly simpler to build correctly: a flat list of
  repos, no candidate-scoring logic, no proposal/approval queue and no
  UI or notification flow needed just to add a repo. Fewer moving parts
  means fewer places for a mistake to hide, which matters most before
  this has any track record.
- Option A also produces the fastest real signal on the two riskiest
  open questions — does an unsolicited draft PR from a stranger's tool
  actually land well with real maintainers, and does the digest format
  actually tell Yehor what he needs to know — without also having to
  validate a candidate-scoring heuristic at the same time.
- Option B's main advantage (scaling past a short list without Yehor
  hand-picking every repo) only matters once volume actually demands
  it. It's real, just not urgent, and it's a clean, additive Phase 2:
  the shortlist mechanism doesn't get thrown away, a proposal stage gets
  added in front of it.
- Recommendation is explicitly conditional: if Yehor already has strong
  opinions about which repos he wants covered (mpfb2 and similar, per
  this project's own existing PR history), a shortlist costs him almost
  nothing to populate — he already knows the names.

This is a recommendation, not a decision made on Yehor's behalf — Step 1
below asks him to confirm or override it before Phase 1 is built.

## 3. Architecture (Phase 1 — shortlist model, draft-only outreach)

Components:

- **`outreach_config.yaml`** (Yehor-edited, lives in the Patchward repo
  or a sibling `memory/` file, git-tracked so changes are visible in
  history): the approved repo shortlist, one entry per repo with owner,
  name, and a `paused: false` flag Yehor can flip per-repo without
  touching code. This file is the entire "target selection" surface —
  there is no other way a repo enters scope.
- **`STOP` file** (or equivalent — a single well-known path, e.g.
  `memory/OUTREACH_STOP`): if present, every scheduled run exits
  immediately after checking for it, before touching Patchward, Gmail,
  or GitHub. Creating this file is the entire "kill switch" — no
  separate command, no service to restart, just a file Yehor can create
  from any terminal or even by hand in the folder.
- **Scheduler** (cron, or a scheduled task — this project already uses
  Cloudflare/GitHub-native scheduling elsewhere, so the concrete
  mechanism is an implementation choice, not a design constraint): once
  daily, invokes a single entry-point script.
- **Runner**: reads `outreach_config.yaml`, checks `OUTREACH_STOP`
  first, then for each non-paused repo not already run today, invokes
  the existing `patchward` CLI exactly as Yehor runs it manually today
  (same scan → fix → draft-PR pipeline, no new PR-opening logic
  written for this feature — it reuses Patchward's own existing,
  already-reviewed mechanism rather than reimplementing it).
- **Gmail watcher**: reads for replies/feedback on threads this loop
  itself started (scoped by a consistent subject-line tag or label, not
  a blanket inbox scan), drafts a proposed reply via the Gmail API's
  draft-creation endpoint specifically (never the send endpoint), and
  stops there.
- **Stats store**: a flat, append-only log (JSON lines or a small
  SQLite file, not a growing hand-edited markdown file like
  `STRATEGY.md` — this is operational data, not project memory, and
  should not compete with that file's own size discipline) recording,
  per run: repo, timestamp, scan result, whether a PR was opened, PR
  URL, and later, PR outcome (merged/closed/ignored) checked on a
  follow-up pass.
- **Digest generator**: reads the stats store, produces a daily or
  weekly summary (repos run, PRs opened, PRs merged, replies received,
  drafts waiting) and surfaces it to Yehor — as a chat message, an
  email to himself, or a small artifact, implementation detail — for
  him to read. It does not write anything back into
  `outreach_config.yaml` or any targeting logic.

What this explicitly does NOT include in Phase 1: candidate discovery,
repo scoring, auto-send, or any self-adjusting messaging logic. All of
that is out of scope until Yehor asks for it as a separate, later
decision.

## 4. Open questions for Yehor (Step 1)

1. Confirm or override the shortlist-first recommendation (§2).
2. If shortlist: which repos go on it first? (mpfb2 is the obvious
   candidate — Patchward already has 2 merged PRs there.)
3. Where should the stats store and digest actually surface — a file
   Yehor checks, a scheduled chat message, an email, something else?
4. Cadence: daily, or less frequent to start (e.g. weekly) while this is
   unproven?

## 4a. Section 4 — locked answers (2026-09-11)

Answered and confirmed by Yehor the same session this document was
written. These override anything in §4 above where the two disagree —
§4 is left intact as the question record, this section is the decision
record.

1. **Shortlist-first, confirmed, not overridden.** Phase 1 uses the
   Yehor-maintained-shortlist model from §2. Propose-and-approve remains
   an explicit, not-yet-built Phase 2.
2. **Shortlist contents: `mpfb2` only, to start.** Rationale, confirmed
   over adding more repos now: it's the one repo where Patchward already
   has a real track record (2 merged security-fix PRs), so it isolates
   "does the automation loop itself work" from "does a brand-new
   maintainer relationship respond well" — two different unknowns that
   adding more repos now would conflate. The shortlist expands only
   after a first supervised live run goes cleanly, not on a fixed
   timeline.
3. **Digest surface: Telegram, delivered ~12:00 (noon), was proposed by
   Yehor mid-session.** NOT locked as a final decision alongside the
   other three — this arrived attached to a live bot API token pasted
   directly into a chat session, which is a credential-exposure event in
   its own right regardless of what channel is eventually chosen. As of
   this entry, that token has NOT yet been revoked by Yehor's own
   confirmation. Standing rule this project now carries forward: **any
   secret that touches a chat transcript is compromised the instant it's
   typed, revoke immediately, no exceptions and no sequencing behind
   other work** — logged as a new candidate heuristic (see
   `.strategy/STRATEGY.md`, H44-candidate). The Telegram-as-digest-
   channel idea itself is reasonable and not rejected — it's simply not
   treated as settled infrastructure until (a) the exposed token is
   revoked and (b) a replacement token, if this channel is still wanted,
   is stored via env var / gitignored secrets file per item 4 below,
   never typed into a chat or committed to the repo. Until then, the
   file-based digest described in §3's architecture remains the default
   surface actually implemented in Phase 1.
4. **Secret storage, confirmed as standing practice, not just for this
   feature: environment variable or a local gitignored secrets file,
   referenced by name in code, never a literal value in any git-tracked
   file.** This matters more than it would have before tonight's own
   MIT pivot — Patchward's GitHub repo is now public, so anything
   committed to it is committed to the public internet, permanently
   recoverable from git history even after a later deletion commit.
5. **Cadence: weekly, to start**, confirmed over daily. Directly applies
   this project's own H42-candidate (a new integration surface has
   consistently taken more verification passes than its first framing
   implied) — escalate to daily only after weekly has run cleanly a few
   times, an evidence-based trigger rather than a fixed date.

## 5. Claims checked before this document was written

- **"Patchward opens draft PRs, never merges"** — confirmed via direct
  read of `patchward-landing/src/pages/limits.astro`'s live copy this
  session ("Patchward opens a draft PR. It does not merge to your main
  branch under any circumstance."). Single source (site copy, not
  Patchward's own source code re-inspected this turn) — consistent with
  every other session's description of the mechanism, not contradicted
  anywhere in `.strategy/STRATEGY.md`.
- **The reviewing model's H20 citation** — checked against H20's actual
  text in `.strategy/STRATEGY.md` (line 1821): H20 is specifically about
  never running `git add`/`commit`/`push` from the agent sandbox on
  *this project's own two repos*, because the sandbox lacks
  `core.autocrlf`/`.gitattributes` and a sandbox commit has actually
  corrupted line endings on origin once before. It is NOT, in its
  literal text, about PR-opening authority against third-party repos —
  the reviewing model's citation was directionally right but imprecise.
  The underlying principle it was reaching for is real and independently
  supported elsewhere in this project's own memory: "Version control:
  Git — all operations run by Yehor only" (ways-of-working.md) and the
  phrase "Directing-Engineer action, not agent-startable" used elsewhere
  in `.strategy/STRATEGY.md` for exactly this class of judgment call
  (BACKLOG 17). Net: the substantive point stands — this project treats
  irreversible, externally-visible actions as Yehor's call — just not
  via H20 specifically. Worth naming so a future session doesn't cite
  H20 for something it doesn't actually say.
- **The Hacktoberfest spam-PR precedent** — verified via web search, not
  taken on the reviewing model's word: real, well-documented 2020
  incident (Drew DeVault's widely-cited "Spamtoberfest" post, The
  Register's coverage, and DigitalOcean's own acknowledgment that
  Hacktoberfest was generating spam PRs against maintainers who hadn't
  opted in). Confirms the reputational-risk framing is grounded in an
  actual precedent, not a hypothetical.
