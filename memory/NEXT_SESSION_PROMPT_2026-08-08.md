# Patchward — Next Session Start Prompt (written at Session 032 close, 2026-08-08)

Resume Patchward. **Open via the `session-strategy-synthesis` skill**,
grounding in `.strategy/STRATEGY.md` — re-verify its claims fresh, do not
trust them as-is, including everything in this file. They were verified at
Session 032 close (2026-08-08) and can go stale between sessions.

## Grounding first, in order (H13 / H14 / H16)

1. **H13/H16** — trust only remote-ref ops and hosted content for git
   state; local mount reads and `git status` on this Windows-origin tree
   are noisy-by-default. Run `git ls-remote origin main` yourself. Last
   known HEAD: **`f653e77`** ("fix(webhook): startup credential shape
   guard … BACKLOG 28"). Confirm it fresh; a fresh `git clone` + byte-diff
   against memory is the Tier-0 check.
2. **H16** — expect ~dozens of "modified" files that are pure CRLF noise;
   diff with `core.autocrlf=input` (or against a clean clone) before
   believing any file changed.
3. **H14** — do not accept any "already done / N sessions running /
   baseline is X" claim on say-so; trace it to its origin before acting.
   Re-derive test baselines rather than inheriting them.
4. **H8/H18** — diff every memory file against a fresh clone before
   trusting it, and run the tracked-file check on INHERITED references too
   (`Patchward_Turning-Point_Industrial-Plan_2026-07-16.md` is still cited
   by 7+ tracked docs while itself untracked — verify the count yourself).

## H20 — HARD RULE (staging is Yehor's, not the agent's)

The agent must **NEVER** `git add` / `commit` / `push` from its sandbox on
this repo. Sandbox git has `core.autocrlf` unset; even with the new
`.gitattributes` (`132f47a`, `* text=auto eol=lf`) a sandbox commit can
rewrite whole files and pollute history. The agent prepares and verifies;
**Yehor stages and commits on Windows**, using his project venv:

> **`D:\Dev\Projects\Patchward\.venv\Scripts\python.exe` (Python 3.14.4,
> nested inside the repo, gitignored — NOT a sibling folder). Verified
> 2026-08-08 by direct filesystem check (three prior wrong guesses before
> this was checked — see H26).**

Never restate the venv as a sibling folder (`...\Patchward.venv`) or as
"one directory over" — both are wrong. The global interpreter lacks the
dev deps and produces ~23 unrelated collection errors. Tripwire before
every push: `git diff --cached --stat` must show the expected small line
counts, not thousands. **This session proved the hazard is real:**
`f653e77` shipped `webhook.py` with a whole-file BOM + mojibake re-encode
(see P0 below).

## Standing heuristics worth knowing (full evidence in STRATEGY.md)

- **H1/H2/H8/H9-cand** — git state: remote-ref/clone/hosted only; never
  cite a hash into a file that then gets committed; diff memory vs clone
  both ways (disk can lead *or* lag git).
- **H14** — re-derive inherited claims; don't accept "done" on narration.
- **H16** — CRLF-normalise before believing a diff (7+ sessions running).
- **H18** — verify referenced/pointed-to files are actually tracked,
  including inherited references.
- **H20** — never stage/commit from the agent; corrected venv path above.
- **H21/H22/H25** — a failing adversarial result is a claim about the
  harness until proven; mocked tests prove branching not behaviour; a
  "CLEAN" verdict is only as strong as what it demonstrably broke
  (mutation-test the load-bearing lines).
- **H23 / H28-cand** — when a check matches by string/structure
  ("PRIVATE KEY" substring, prefix, "looks like a PEM"), test it against
  hostile look-alike input BEFORE trusting it; a resemblance proxy is a
  bypass. (H28 candidate, 2 occurrences, needs one more to promote.)
- **H24 / H29** — validate against the CONSUMER's real contract:
  enumerate every consumer of a credential class, and mirror the exact
  type it needs (RSA for RS256, not "parseable") and its precedence order
  (raw-first). **H29 promoted 2026-08-08** (F-A + F-B in one patch).
- **H26 [standing, promoted 2026-08-08]** — byte-check any
  encoding/corruption claim, positive OR negative, before recording it.
  Session 030 it killed a false alarm; Session 032 it caught a real
  committed BOM+mojibake regression. Same discipline, opposite outcome.
- **H27** — nested PowerShell pipelines silently shadow `$_`; capture
  outer-loop values into named variables before a nested stage.

## Verified state at Session 032 close (re-verify anyway)

- **HEAD `f653e77` == origin/main** by `git ls-remote`. Two commits landed
  this session: `132f47a` (`.gitattributes`, byte-verified BOM-free) and
  `f653e77` (BACKLOG 28 guard). Nothing staged/committed by the agent.
- **BACKLOG 28 — CLOSED.** Startup credential-shape guard, three
  adversarial rounds (v1 substring → v2 F1–F5 → v3 F-A/F-B/F-C + M1),
  third independent pass CLEAN, verified on origin by content, real gate
  **565 / 3 skipped / 15 deselected / 91.20%** on Yehor's 3.14.4. It is a
  startup guard — committed and gate-passing, but **NOT yet exercised on
  Fly**; do not treat CLOSED as live-verified boot behavior.
- **BACKLOG 29** — remains FIXED + DEPLOYED + live-verified since Session
  031 (`66680c0`, deployment `…RA8F`). Nothing new this session.
- A stale `.git/index.lock` sits in the mount (un-unlinkable from the
  sandbox, `Operation not permitted`) — a mount-permission artifact, not a
  live git op. If it blocks Yehor's staging, delete it manually.

## Open items and priorities

- **P0 (a): fix the encoding regression on `f653e77:webhook.py`.** It was
  committed with a leading UTF-8 BOM (`EF BB BF`) and 29 mojibake
  em-dashes (`D0 B2 D0 82 E2 80 9D`, a UTF-8 em-dash misdecoded through
  CP1251) — a whole-file re-encode that corrupted 21 pre-existing
  em-dashes plus ~8 new ones in comments. Cosmetic (comments/preamble,
  gate unaffected) but a real content regression on main that defeats the
  `.gitattributes` intent. Fix: strip the 3 BOM bytes, replace the 29
  sequences with `E2 80 94`, re-run the gate (a comment/BOM change can't
  move it), commit as a one-line encoding fix. The agent can prepare a
  corrected copy as a separate artifact on request. New this close.
- **P0 (b): live site-copy check** (memo §7 step 4) — untouched again and
  now the OLDEST untouched item on the board. Overdue; do it.
- **P1: decide the six untracked root artifacts + the Turning-Point plan.**
  Track, gitignore, or delete — Yehor's call. Untracked set:
  `backlog28_startup_credential_guard.patch`,
  `backlog28_v2_implementation_2026-08-08.md`,
  `backlog28_v2_second_adversarial_pass_2026-08-08.md`,
  `backlog28_v3_implementation_2026-08-08.md`,
  `backlog29_implementation_2026-08-07.md`,
  `credential_identification_2026-08-07.md` (+ `verify_session_open_2026-08-05.md`,
  and the long-untracked `memory/Patchward_Turning-Point_Industrial-Plan_2026-07-16.md`).
  `tests/fixture_repo` shows modified (gitlink, dirty before this session,
  out of scope).
- **P2: the two BACKLOG 28 design questions never decided** — (a) should
  ABSENCE of a required credential also fail the boot (guard only fails on
  present-but-malformed today); (b) should `/healthz` assert credential
  validity so "green" means "can actually work." Both are Yehor's design
  calls, not agent-startable.

## Then

No agent-startable code work is queued beyond P0(a). Start by grounding
per the checklist above, then **ask Yehor what he wants to do this
session** — P0(a) encoding fix, P0(b) live site-copy check, P1 artifact
cleanup, the P2 design questions, or something entirely new.
