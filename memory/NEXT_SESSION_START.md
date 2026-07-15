# Patchward — Next Session Start Prompt
Regenerated at the actual end of Session 016 (2026-07-15). Paste this
whole file as your opening message to start the next session with full
context restored.

---

**Resume Patchward.** Read `memory/STATE.md`, `memory/BACKLOG.md`, and
`memory/project_session_log.md` (Session 015 and 016 entries) first, in
full. Do not assume anything below is still true without re-checking —
verify, don't trust memory, per standing project rules. This file itself
is a claim to be re-verified, not a source of truth — it has gone stale
within its own session or across sessions four separate times now (see
"A pattern worth naming," carried forward from Session 015).

## Housekeeping — confirm these before anything else, in order

1. **Run the real test suite — this is the actual blocker, not routine
   housekeeping.** Session 016 added one new test
   (`test_run_log_fix_gen_declined_writes_declined_echo_and_record` in
   `test_orchestrator.py`, BACKLOG 15a) that has **never been run on
   real Python** — only `ast.parse`'d, and even that hit a false
   positive first (see item 7 below). Run:
   ```
   cd D:\Dev\Projects\Patchward
   uv run pytest --cov
   ```
   Expected: 449 passed (448 + the 1 new test), same 2 skipped, 15
   deselected, coverage roughly flat or slightly up from 90.46%. If it
   fails, don't assume it's a repeat of BACKLOG 13's MagicMock gap
   without checking — read the actual failure first.
2. **Apply the `.claude/agents/*.md` manual diff (below) — the agent
   could not do this itself.** The `Edit` tool refused all three files
   as a protected path. Three small, purely textual changes: rename
   "RepoMend" → "Patchward" in `scanner.md`, `fix-gen.md`, `verifier.md`;
   and in `fix-gen.md`, replace the "ESCALATE signal" description (never
   actually implemented) with a description of the real `decline_fix`
   tool that shipped in BACKLOG 13. See "Manual diff for Yehor" below
   for exact before/after text.
3. **If both of the above are done, commit + push:**
   ```
   git add tests/test_orchestrator.py memory/BACKLOG.md memory/project_session_log.md memory/NEXT_SESSION_START.md .claude/agents/scanner.md .claude/agents/fix-gen.md .claude/agents/verifier.md
   git commit -m "test(cli): cover [DECLINED] echo path (BACKLOG 15a); fix stale RepoMend naming in .claude/agents templates"
   git push
   ```
   Then `git ls-remote origin main` to confirm it landed — don't trust
   the terminal output alone; a fresh session should re-check
   independently regardless.
4. **Confirm `main`'s SHA fresh** via `git ls-remote origin main` before
   trusting any SHA cited anywhere in this file.
5. **Re-confirm Fly health fresh** — `patchward-webhook.fly.dev/healthz`.
   Confirmed OK 2026-07-15 (direct HTTPS GET, Tier 1). Re-check anyway.
6. **This sandbox's `git status`/`git diff` cannot be trusted at all.**
   `git log`/`git ls-remote` remain trustworthy. Restrict sandbox git
   usage to those two.
7. **Sandbox file/line-count reads can be truncated, not just stale.**
   Confirmed twice now, different files, different sessions: `cli.py`
   (Session 014) and `tests/test_orchestrator.py` (this session — bash
   `wc -l` reported 1401 lines and `ast.parse` reported a false
   unclosed-paren syntax error at the truncation point; the `Read` tool
   confirmed the real file is 1505 lines, complete, well-formed). Trust
   the `Read`/`Edit` tools' own view of a file's contents over any bash
   `cat`/`wc`/`grep`/`py_compile` read of it. Verify real correctness
   (syntax, tests) only on Yehor's actual machine.
8. **`.git/objects/maintenance.lock` may still be present (0-byte,
   known non-blocking quirk).** Check `git status` on Yehor's machine
   before assuming it blocks anything.
9. **Don't trust a tool's self-reported description of what it did —
   check the actual artifact.**
10. **Any new dataclass field added to a result type that's mocked via
    bare `MagicMock()` (not `spec=`'d) anywhere in the test suite must be
    added explicitly to every existing mock-construction site.** Hit
    twice in this exact codebase (2026-07-08, 2026-07-15,
    `test_orchestrator.py` both times).

## Manual diff for Yehor — `.claude/agents/*.md` (agent-blocked, apply by hand)

All three files currently start their body with a line like `You are
the <Name> subagent for RepoMend.` — change `RepoMend` to `Patchward` in
all three (`scanner.md`, `fix-gen.md`, `verifier.md`).

In `fix-gen.md` specifically, this line:
```
- If you are uncertain about scope: stop and return an
  ESCALATE signal, do not guess
```
should become something like:
```
- If you are uncertain about scope: stop and do not guess.
- If, after inspecting the code, this is not a real, fixable
  vulnerability (by-design behavior, false positive, test/simulation
  code): call decline_fix with a clear reason instead of forcing an
  unnecessary edit. This is the real, implemented mechanism (BACKLOG
  13, 2026-07-15) — the old "ESCALATE signal" language here never
  corresponded to an actual tool.
```
(Optional, your call: all three files also carry a "SETUP NOTE: Copy
this file to .claude/agents/X.md" trailer that's self-referential —
they're already at that path. Confirmed via grep this session that none
of the three are referenced anywhere in `src/`; whether to delete them
outright rather than just correct the content is a decision only you
should make, not something decided unilaterally this session.)

## Progress list — where things stand (verified fresh 2026-07-15, Session 016)

- [x] BACKLOG 13 — Fix-Gen explicit decline path — CLOSED, verified,
      committed, pushed (`9788656`).
- [x] BACKLOG 15 — triaged (not built blind): split into 15a (small,
      implemented this session, **unverified on real Python — see
      Housekeeping item 1**) and 15b (real gap, genuinely unscoped,
      parked).
- [ ] `.claude/agents/*.md` cleanup — content drafted, **blocked on
      Yehor applying it manually** (agent-blocked path). See "Manual
      diff" above.
- [ ] BACKLOG item 10 — Mirror Pass Tier 2 — still unscoped, needs a
      conversation with Yehor before it's real work, not started.
- [ ] BACKLOG items 9, 12, 8, 14 — unchanged, all Yehor-only.
- [ ] BACKLOG 15b — `version`/`scan`/`batch` CliRunner coverage — real
      gap, not scoped, not started.

Full detail and WSJF ordering for all of the above: `memory/BACKLOG.md`.

## A pattern worth naming (carried forward, now a 4th instance)

This file, or its underlying memory files, have gone stale or been
caught mid-write four separate times across Sessions 014-016: two
mid-session drifts in 014, one stale SHA/lock claim caught at the start
of 015, and this session's sandbox-mount truncation (a different failure
mode — not memory drift, but a read-tool artifact that could have been
mistaken for a real code defect if trusted uncritically). The common
thread: verify via the most direct, most independent method available
before trusting any claim, including this file's own — and when a
sandbox check contradicts a tool's own success confirmation (e.g. `Edit`
reporting success, then a later `Read` should be trusted over a bash
`ast.parse` that disagrees), trust the tool that did the actual write,
not the secondary read path.

## Standing rules (unchanged unless noted, still binding)

- Verify before reporting anything as done.
- **Never run git writes against Patchward from the bash sandbox** —
  hand git writes to Yehor.
- **Never paste or forward API keys/secrets through terminal output
  into chat.**
- Trust-tier logic (BUILD_PLAN_2026-07-10.md Appendix B): Tier 0 (git
  hashes, `git ls-remote`, local exit codes) — accept as-is. Tier 1
  (authenticated direct reads) — accept with evidence. Tier 2
  (proxied/unauthenticated) — never sufficient alone for a gating
  decision.
- **This sandbox's `git status`/`git diff` cannot be trusted at all.**
- **Sandbox file reads/line-counts can be stale or truncated** — trust
  `Read`/`Edit` tool output, verify real correctness on Yehor's machine.
- **Don't trust a tool's self-reported description of what it did —
  check the actual artifact.**
- **When a tool (like `Edit`) refuses a path as protected, hand the
  change to Yehor rather than working around it via bash or another
  channel.**
- **Regenerate this handoff file at the actual end of a session's
  work** — not at the first pause point.

## Suggested first move

Run the real test suite (Housekeeping item 1) — this session shipped one
untested-on-real-Python test and needs that confirmed before anything
else. Apply the `.claude/agents` manual diff whenever convenient (small,
independent, no dependency on the test run). After both land, the
backlog has no agent-startable coding work left without your input —
item 10 needs a scoping conversation, 15b needs its own scoping pass,
everything else is Yehor-only.
