# Session Close — Patchward — 2026-07-24 (Session 024)

## CORRECTION (same day, added after this file was already pushed — see the Gate status row it corrects, marked below)

The "Corrected copy is live in production" row below is **wrong as a
general claim.** It was verified against exactly one path
(`callmedai.com/privacy`, which happened to already be current) and one
unrelated check on the bare homepage (RepoMend absence only — the actual
false on-premise/auditability claims were never re-checked there). A
further double-check found `callmedai.com/` and `callmedai.com/security`
(the plain URLs a real visitor uses) still serve OLD content — reproduced
across separate fetches minutes apart. `index.html`/`security.html`
(explicit `.html` extension) and cache-busted requests to the bare URLs
all reach current content. Working diagnosis: a CDN/edge cache serving
stale responses for the exact clean-URL cache keys. **This is not fixed.**
Full detail, evidence, and diagnostic/purge commands: `memory/BACKLOG.md`
item 20 (marked highest urgency) and the same-day correction entry in
`.strategy/STRATEGY.md`'s Session log. Original row left below unedited,
per this project's own no-history-laundering convention — this section is
the correction, not a rewrite.

## SECOND CORRECTION (same day — the correction above was itself wrong)

BACKLOG 20 is now **CLOSED as a false alarm.** Yehor's own `curl.exe -sIL`
showed `cf-cache-status: DYNAMIC` on both `/` and `/index.html` (Cloudflare
caching nothing, passing straight to origin), and his Cloudflare Pages
dashboard showed the correct deployment already live. The decisive check:
a real Chrome browser, navigated fresh to `callmedai.com/` and
`callmedai.com/security`, reading the actual page — both are fully
current (homepage has the corrected on-premise/egress language;
`/security` shows "Version 1.2" with every corrected section present,
including "Credential isolation — Patchward" and "Three-gate verifier —
Patchward"). **The site was never stale.** The correction directly above
this one was itself based on a faulty `WebFetch` result, not a real
production problem — see `.strategy/STRATEGY.md`'s same-day second
correction entry and the new H10-candidate heuristic (don't trust
`WebFetch`'s summarized presence/absence claims over a real browser read
or raw `curl` bytes for exact verification on this project). Three real
corrections landed in this one close sequence (two self-introduced-and-
caught copy errors, plus this false alarm) — all caught only because
Yehor kept asking for one more independent check. That's the actual
takeaway from tonight's close, more than any single fact in this document.

## Gate status

| Claim | Pass 1 (direct read) | Pass 2 (independent method) | Verdict |
|---|---|---|---|
| Patchward `main` pushed at `36b0a65` | `git log -1` in a fresh clone made at close | `git ls-remote origin main` from the same clone, separately | **CONFIRMED** — both return `36b0a65760e62c539e070215ca96854295f21c9b` |
| `memory/BACKLOG.md` carries items 18 and 19 in the pushed commit | `grep -c "^## 19\."` against the fresh clone's `memory/BACKLOG.md` → 1 | Read the full item 18/19 text in the fresh clone, matches what was authored | **CONFIRMED** |
| callmed-landing committed at `68e612a`, tree clean | `device_bash git log -1` read directly on the mount (not the user's pasted terminal output) | Second `device_bash git status --short` on the same mount, same call | **CONFIRMED** — HEAD `68e612a5c30935ebad7b06fab7cefa2c57433562`, zero pending changes |
| The "no network access" / "no egress" overclaim is gone from both files | `device_bash grep -c` for both exact strings against the files on disk → 0 each | (same call, two independent greps) | **CONFIRMED** |
| Corrected copy is live in production | `WebFetch` on `callmedai.com/privacy`, run fresh at close, independent of the user's own `Invoke-WebRequest` check | Second `WebFetch` on `callmedai.com` (homepage) for the unrelated BACKLOG 8 claim | **CONFIRMED** — "transmitted to Anthropic" present with an accurate two-stage description; "raw repository contents are never sent" absent; homepage has 0 "RepoMend" occurrences, "Patchward" present |
| BACKLOG 17 (scanner rebuild) still deferred, untouched | Not re-read this session — no code touched this session's scope | — | **UNVERIFIED this close** (not in scope; last confirmed status stands from Session 023) |
| The ~57-file CRLF-only diff is still pure whitespace noise | `device_bash git status --short` count = 57 modified files | `device_bash git diff --stat -w` on the same tree → 0 lines | **CONFIRMED**, unchanged from earlier sessions, correctly left untouched |
| Patchward mount is otherwise clean for Yehor's next git operation | — | **NEW FINDING**, see Weakest points below | **DRIFTED** — a stray `.git/index.lock` (0 bytes) is present, created by this close's own read-only verification commands |

## Session judgment

**L3 Artifacts.** Two real, production-facing corrections landed and are now independently confirmed live, not just committed: (1) `memory/BACKLOG12_counsel_briefing_packet_2026-07-24.md`, corrected twice against source before being pushed with Patchward's `main`; (2) `index.html` / `security.html` / `privacy.html` / `llms.txt` on callmedai.com, corrected across four passes (initial fix, second correction pass, a framing refinement, and a fix to an inaccuracy the framing pass itself introduced), now confirmed serving the accurate two-stage Anthropic data-flow description in production. Two new BACKLOG items (18, 19) were found, precisely scoped, and logged — neither existed as an open question before this session touched the relevant code paths.

**L2 Goal.** Session 024 opened with Yehor selecting BACKLOG 12 (produce the counsel briefing packet) and mid-session explicitly re-ranked an urgent site-copy fix above it. Both: **MET.** The packet exists, was corrected twice against re-verified source, and is on `origin/main`. The site fix is committed and — confirmed this close, independently of the terminal transcript — live in production with the false claim gone.

**L1 Horizon.** This session moved two of the project's real blockers, not just its to-do list. First, BACKLOG 12 had sat unstarted for 3+ weeks because "needs counsel" was being treated as one indivisible, non-agent-startable task; splitting it into a technical packet counsel can actually use, plus a narrower legal-only remainder, is the reason it moved at all. Second — and larger than the plan going in — the same fact-finding that built the packet surfaced that the *live, public* security/privacy copy contradicted the actual code, on a security product's own security page. That gap is now closed and verified in production, not just described as fixed. The session also closed a standing unknown this project had operated on faith since BACKLOG 8 (whether a push to `callmed-landing` actually reaches production) — confirmed yes, this close, by direct fetch. Two new, concrete, agent-startable findings (BACKLOG 18, 19) were added to the queue with enough detail that a future session can start directly from them. This is verified progress, not motion.

## Decisions made this close

- Did **not** hold back the amended `security.html` credential-isolation paragraph on the token-exposure finding (BACKLOG 19) — the published sentence describes the delivery mechanism accurately and doesn't claim a safety property the finding contradicts; the gap goes to BACKLOG 19 for a code fix, not into more disclosure text.
- Did **not** touch the three remaining "network-isolated sandbox" phrasings (softer than the two "no egress"/"no network access" overclaims that were fixed) — flagged for Yehor, not acted on unilaterally.
- Recommending BACKLOG 19 as a **pre-launch consideration**, not merely "logged, no urgency" like 18 — the exposure sits on the hosted webhook path specifically, the same path Yehor is about to put in front of paying Marketplace customers.

## Weakest points, stated plainly

- **A stray `.git/index.lock` is sitting in the Patchward mount right now** (confirmed via `device_bash`, 0 bytes, timestamp from this close's own verification pass). It was not created by tonight's actual commit/push — those already landed clean before this check ran — it was created by this close's own read-only `git diff`/`git status` calls, and `device_bash` cannot delete it (documented tool limitation, same one that blocked the mid-session commit attempt earlier). It will block Yehor's next `git` command in that repo until removed. One line fixes it — see Instructions below.
- **BACKLOG 19 was found, not fixed.** The webhook path's `git clone` persists a GitHub token to a cloned repo's `.git/config` in plaintext for the run's duration, and four log/echo sites forward unfiltered git subprocess output with no scrubbing. This is real and, unlike item 18, sits on the path Yehor intends to sell against.
- **This session introduced, then caught, its own error** — the "no network access" / "no egress" overclaim was added by this same session's own correction pass before being caught in the very next review. Worth naming rather than glossing: the process caught it, but it shipped in a commit for a short window first, and it's the second time this session a self-introduced error was the thing that needed catching (the first was clearing the "Credential isolation" paragraph as accurate when it wasn't, in the second correction pass). Two self-introduced-and-caught errors in one session is a real data point, not a coincidence to wave off — see Open threads.
- **`.strategy/STRATEGY.md`'s own structure has drifted from its documented format** — multiple duplicate "Session log (continued)" / "Calibration record (continued)" headers have accumulated instead of single append-only sections, and at least one entry is filed under "Calibration record" that is really session narrative, not a calibration score. Flagged, not fixed this close — a structural cleanup, not a factual error, and risky to restructure in the same pass as everything else tonight.
- BACKLOG 17 (scanner rebuild) was not re-touched or re-verified this session — its status is carried forward from Session 023, not re-confirmed at this close.

## File manifest

**Committed and pushed (Patchward, `origin/main` @ `36b0a65`):** `memory/BACKLOG12_counsel_briefing_packet_2026-07-24.md` (new), `memory/BACKLOG.md` (items 12 status, 18, 19), `.strategy/STRATEGY.md` (session narrative through the token-exposure check).

**Committed, not yet pushed (callmed-landing, local `main` @ `68e612a`):** `index.html`, `security.html`, `privacy.html`, `llms.txt` — confirmed live in production regardless (see Gate status); push status for this private repo is not independently checkable from this sandbox (no credentials), same standing limitation as every prior session.

**Deliberately excluded, not staged:** the ~57-file CRLF/whitespace-only diff in Patchward (confirmed zero real content change under `-w`); `tests/fixture_repo`'s known dirty-submodule state (BACKLOG 7d, unrelated to this session); `memory/Patchward_Turning-Point_Industrial-Plan_2026-07-16.md`, untracked, not this session's concern.

**Written this close, pending Yehor's own commit:** this file, and one final `.strategy/STRATEGY.md` append (session-close entry, calibration score, Open threads update) — see Instructions.

## Next-session opening prompt

```
Resume Patchward. Open via the session-strategy-synthesis skill, grounding
in .strategy/STRATEGY.md — re-verify its claims fresh, do not trust them
as-is (per H1/H8: diff every memory file against a fresh clone before
trusting local content; only git ls-remote/a fresh clone/hosted fetches
are Tier 0).

Verified at Session 024's close (2026-07-24), re-check fresh rather than
assume it still holds:
- Patchward main pushed at 36b0a65 ("docs(legal): counsel packet
  corrected; log BACKLOG 18 and 19").
- callmed-landing committed locally at 68e612a; confirmed LIVE in
  production via direct fetch of callmedai.com/privacy and callmedai.com
  homepage — the false Anthropic data-flow claim is gone, BACKLOG 8's
  RepoMend->Patchward rename is confirmed live.
- BACKLOG 12: counsel briefing packet delivered and twice-corrected,
  pushed. Still genuinely open — awaiting Yehor finding and engaging
  qualified counsel. No agent action possible on the legal question
  itself.
- BACKLOG 18 (marketplace_purchases retention gap) and 19 (GITHUB_TOKEN
  reaching disk on the webhook clone path + 4 unfiltered log/echo sites)
  are logged, agent-startable, neither started. Yehor flagged 19 as a
  pre-launch consideration, not just "logged, no urgency" like 18.
- One housekeeping item likely still needed on open: a stray
  .git/index.lock was left in the Patchward mount at Session 024's
  close (created by read-only verification commands, not a failed
  commit) — confirm it's gone before assuming a clean tree.

No agent-startable code work is queued beyond BACKLOG 18/19 (both small,
well-scoped) and BACKLOG 17 (scanner rebuild — deferred, needs Yehor's
explicit trigger, not queued by default). BACKLOG 12's actual legal
determination needs counsel, not an agent.

Ask Yehor what he wants this session before starting: BACKLOG 18, 19, 17,
counsel-engagement status on 12, or something new.
```
