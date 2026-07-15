# Patchward — Next Session Start Prompt
Regenerated at the actual end of Session 015 (2026-07-15), after BACKLOG
item 13 closed and both commits were drafted (not yet confirmed landed —
see Housekeeping item 1). Paste this whole file as your opening message
to start the next session with full context restored.

---

**Resume Patchward.** Read `memory/STATE.md`, `memory/BACKLOG.md`, and
`memory/project_session_log.md` (Session 015 entry) first, in full. Do
not assume anything below is still true without re-checking — verify,
don't trust memory, per standing project rules. This file itself is a
claim to be re-verified, not a source of truth — it has gone stale
within its own session three separate times now (see "A pattern worth
naming" below).

## Housekeeping — confirm these before anything else

1. **Confirm the two Session 015 commits actually landed.** Drafted for
   Yehor to run at session close: `docs: correct stale SHA/lock claims
   in NEXT_SESSION_START.md`, then `feat(fix-gen): add explicit
   decline_fix tool path (BACKLOG 13)`. **Not confirmed landed as of
   this file being written** — the test run that validated the change
   (448 passed, 2 skipped, 90.46% coverage) happened before the commit
   step. Check `git log --oneline -5` and `git ls-remote origin main` on
   Yehor's machine before trusting anything below that assumes these
   are on `main`.
2. **Confirm `main`'s SHA fresh** via `git ls-remote origin main` —
   don't trust any SHA cited in this file's own text without
   re-checking (see item 1 and the pattern note below).
3. **Check `.git/objects/maintenance.lock`.** Present (0-byte) as of
   this session on the sandbox mount; `.git/index.lock` was absent this
   session (cleared since Session 014). Known, previously self-resolving
   mount-permission quirk (Sessions 012, 013) — not confirmed blocking
   anything on Yehor's real machine. Check `git status` there first.
4. **Re-confirm Fly health fresh** — `patchward-webhook.fly.dev/healthz`,
   cheap and authoritative. Confirmed OK 2026-07-15 (direct HTTPS GET,
   Tier 1). Re-check anyway.
5. **Confirm `.venv` still works.** Confirmed OK by Yehor directly on
   his own machine 2026-07-15 (two full test runs). Re-check anyway;
   rebuild only if it actually fails (`Remove-Item -Recurse -Force .venv`
   then `uv sync --all-extras`).
6. **Re-run the full test suite before trusting it.** Last real number:
   **448 passed, 2 skipped, 15 deselected, 90.46% coverage** — Yehor's
   `.venv`, real machine, 2026-07-15 (second run, after fixing 2
   test-mock failures the first run caught — see BACKLOG item 13). Any
   session after this one should still re-confirm rather than cite this
   number cold.
7. **This sandbox's `git status`/`git diff` (working-tree comparisons)
   cannot be trusted at all** — unchanged from prior sessions. `git
   log`/`git ls-remote` (ref/object reads) remain trustworthy. Restrict
   sandbox git usage to those two.
8. **Sandbox file reads can go stale on recently-edited files** — this
   session confirmed the opposite is also true: a `grep`-after-`Edit`
   check on 5 freshly-edited files all matched immediately, no lag
   observed. File-specific and unpredictable either way — trust the
   Read/Edit tools' own view, verify compile/tests on Yehor's real
   machine, not the sandbox.
9. **Don't trust a tool's self-reported description of what it did —
   check the actual artifact.**
10. **PowerShell heredoc paste is unreliable on this machine for
    multi-line strings.** Working pattern: base64-encode + `WriteAllText`,
    or a single unbroken line, or (new this session, lower-risk when
    Yehor is the one running the command, not the agent typing into his
    terminal) a plain single-line `git commit -m "..."` with no commit
    body — full rationale lives in code comments and the session log
    instead of a long commit message.

## A pattern worth naming — this file's own claims have now gone stale three times

Session 014 caught this file going stale mid-session, twice, within the
same session (see the two Session 014 drift notes, preserved below for
the record). Session 015 caught a third instance on the very first
read: the file's own claimed SHA and lock-file state were already wrong
by the time a fresh session opened it. This is not "occasionally
happens" — it is the default outcome for any transient-state claim in
this file, because a new commit can land after the file is written and
before it is next read. Treat every SHA, lock-file, or "as of this
session" claim in this file as a hypothesis with a near-100% chance of
being stale, not as a fact, no matter how recently it says it was
checked. Re-verify via `git ls-remote`/`git rev-parse HEAD` first, every
time, before anything else.

### Session 014 drift notes (preserved)

The first Session 014 handoff was written after only BACKLOG 3a landed,
then 3c/3d/6a/6/7/3b/11/7a/7b/7c/7d all closed in the same session
without the file being regenerated to match until a `/session-strategy-
synthesis` drift check caught it — twice. Lesson from that session:
regenerate this file once, at the point work actually stops, not at the
first natural pause and not so late that drift compounds. This session
tried to follow that — regenerating once, now, after BACKLOG 13 actually
closed (pending commit confirmation, see Housekeeping item 1).

## Progress list — where things stand (verified fresh 2026-07-15)

- [x] Phase 8 (State Reconstruction Audit) — CLOSED, tagged `state-audit-2026-07`.
- [x] Stage-1 E2E pipeline test — run and documented (Session 013).
- [x] Stage 2 (BACKLOG item 11) — real third-party E2E test, COMPLETE.
      `github.com/yehorcallmedai-maker/ssh-audit/pull/1` shipped, merged,
      branch deleted. Pipeline validated end-to-end against a real
      third-party repo.
- [x] BACKLOG 3a/3b/3c/3d, 6, 6a, 7, 7a, 7b, 7c, 7d — all CLOSED (Session 014).
- [x] **BACKLOG 13 — Fix-Gen explicit decline path — CLOSED 2026-07-15
      (pending commit confirmation, Housekeeping item 1).** Selected over
      item 10 via `/session-strategy-synthesis` on WSJF terms (item 10
      has no spec anywhere in the repo — see BACKLOG item 13's full
      writeup and item 10 below). `decline_fix` tool added to Fix-Gen;
      `FixResult.declined`/`.decline_reason` added; `pipeline.py`/`cli.py`
      updated to surface it distinctly from generic `fix_failed`/`[SKIP]`.
      7 new tests. Caught and fixed a real recurrence of a previously-
      documented MagicMock test-mock bug class along the way (see
      BACKLOG 13 for the full writeup — now flagged as a standing
      heuristic for this codebase's test-mocking style).
- [ ] **BACKLOG item 10 — Mirror Pass Tier 2 — still unscoped, not
      started.** Confirmed this session: no design spec exists anywhere
      in `memory/`, `docs/`, or `src/` beyond a one-line BACKLOG/BUILD_PLAN
      table entry. Its real next step is a scoping conversation with
      Yehor, not code. Don't start "implementing" it without that
      conversation happening first.
- [ ] BACKLOG item 9 — PyPI Trusted Publisher — confirm live. Yehor-only
      (PyPI account access required).
- [ ] BACKLOG item 12 — Regulatory flags (CRA/GDPR) — Yehor-only
      (external legal input required), needed before paid listing, not now.
- [ ] BACKLOG item 8 — `callmed-landing` rename — different repo, out of
      scope for Patchward sessions.
- [ ] BACKLOG item 14 — stray pre-rename `repomend/` branches on
      `ssh-audit` — Yehor-only, not investigated further.
- [ ] `.claude/agents/fix-gen.md` — **NEW, flagged this session, not
      scheduled.** Stale legacy template: still says "RepoMend", still
      describes a never-implemented "ESCALATE signal" tool. Appears to be
      a distribution/setup artifact, not the live prompt (the real one is
      `_FIX_GEN_SYSTEM_PROMPT` embedded in `fix_gen.py`, which is what
      was actually updated for BACKLOG 13) — not confirmed unused, just
      observed inconsistent. Owner: TBD.
- [ ] No `tests/test_cli.py` exists in this repo at all — confirmed via
      `Glob` this session. `cli.py`'s `[DECLINED]` echo branch (BACKLOG
      13) has no dedicated unit test as a result. Not blocking, but worth
      knowing before assuming CLI-level output is covered.

Full detail and WSJF ordering for all of the above: `memory/BACKLOG.md`.

## Standing rules (unchanged unless noted, still binding)

- Verify before reporting anything as done — re-fetch/re-check live
  state, never trust a prior session's cached belief, including this
  file itself (see "A pattern worth naming" above).
- **Never run git writes against Patchward from the bash sandbox** —
  hand git writes to Yehor to run on his own machine.
- **Never paste or forward API keys/secrets through terminal output
  into chat.**
- Trust-tier logic (BUILD_PLAN_2026-07-10.md Appendix B): Tier 0 (git
  hashes, `git ls-remote`, local exit codes) — accept as-is. Tier 1
  (authenticated direct reads, e.g. a direct HTTPS healthz probe) —
  accept with evidence. Tier 2 (proxied/unauthenticated reads) — never
  sufficient alone for a gating decision.
- **This sandbox's `git status`/`git diff` cannot be trusted at all** —
  restrict sandbox git usage to `git log`/`git ls-remote` only.
- **Don't trust a tool's self-reported description of what it did —
  check the actual artifact.**
- **New this session: any new dataclass field added to a result type
  that's mocked via bare `MagicMock()` (not `spec=`'d) anywhere in the
  test suite must be added explicitly to every existing mock-construction
  site** — an unset attribute auto-vivifies as a truthy,
  non-JSON-serializable object, which silently breaks any code path that
  both branches on truthiness and serializes the mock to JSON. This
  exact class of bug has now hit this codebase twice (2026-07-08 and
  2026-07-15) in the same file (`test_orchestrator.py`).
- **Regenerate this handoff file at the actual end of a session's
  work** — not at the first pause point.

## New capability from Session 014, still relevant

`gh` (GitHub CLI) is installed and authenticated on Yehor's machine
(device-flow, `yehorcallmedai-maker` account, org access to FixProve and
yehorkaliberda). Useful for independent verification — `gh pr view`,
`gh pr diff`, `gh repo list` — rather than trusting a tool's or CLI's own
self-report.

## Suggested first move

Confirm Housekeeping items 1-6 above — especially item 1, since the two
Session 015 commits were drafted but not confirmed landed before this
file was written. Once confirmed, nothing in the current backlog is
agent-actionable without Yehor's input: item 10 needs a scoping
conversation before it's real work, items 9/12/8/14 are Yehor-only. Ask
Yehor what he wants to look at next rather than assuming continuation
into any of them.
