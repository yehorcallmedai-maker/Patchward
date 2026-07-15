# Patchward — Next Session Start Prompt
Regenerated at the actual end of Session 016 (2026-07-15), after both
pending items (BACKLOG 15a test verification, `.claude/agents/*.md`
manual diff) landed and were independently confirmed on `origin/main`.
Paste this whole file as your opening message to start the next session
with full context restored.

---

**Resume Patchward.** Read `memory/STATE.md`, `memory/BACKLOG.md`, and
`memory/project_session_log.md` (Session 015 and 016 entries, including
the 016 close-out addendum) first, in full. Do not assume anything below
is still true without re-checking — verify, don't trust memory, per
standing project rules. This file itself is a claim to be re-verified,
not a source of truth (see "A pattern worth naming" below — it has gone
stale or been caught mid-write multiple times across Sessions 014-016).

## Housekeeping — confirm these before anything else

1. **Confirm `main`'s SHA fresh** via `git ls-remote origin main`.
   Last known-good, independently confirmed via `git fetch` + `git
   ls-remote` (Tier 0, two methods, same result): `main` @
   `7effbad32b7c51bfa379d19b1f3b442269faef59`. Re-check anyway.
2. **Re-confirm Fly health fresh** — `patchward-webhook.fly.dev/healthz`.
   Confirmed OK 2026-07-15 (direct HTTPS GET, Tier 1). Re-check anyway.
3. **Confirm `.venv` still works.** Confirmed OK by Yehor directly on
   his own machine 2026-07-15 (three full test runs across Sessions 015
   and 016). Re-check anyway; rebuild only if it actually fails.
4. **Re-run the full test suite before trusting it.** Last real number:
   **449 passed, 2 skipped, 15 deselected, 90.46% coverage** — Yehor's
   `.venv`, real machine, 2026-07-15, confirmed after BACKLOG 15a
   landed. Any session after this one should still re-confirm rather
   than cite this number cold.
5. **This sandbox's `git status`/`git diff` cannot be trusted at all.**
   `git log`/`git ls-remote` remain trustworthy. Restrict sandbox git
   usage to those two.
6. **Sandbox file reads/line-counts can be stale OR truncated, not just
   "different."** Confirmed this session: `test_orchestrator.py`'s bash
   mount reported a false syntax error from a truncated read (1401 of
   1505 real lines) even though the `Read` tool and the actual test run
   both confirmed the file was correct. Also confirmed:
   `project_session_log.md`'s bash `tail` stayed stale for an entire
   session even after the real content was committed and pushed. Trust
   `Read`/`Edit`/`Write` tool output over any bash `cat`/`wc`/`tail`/
   `grep`/`py_compile` read. Verify real correctness only on Yehor's
   machine.
7. **`.claude/agents/*` is a protected path — `Edit`/`Write` tools will
   refuse it.** `Read` works fine. If a future change is needed there,
   the working pattern (used successfully this session) is: generate
   the corrected content, base64-encode it, hand Yehor a single-line
   PowerShell `[System.IO.File]::WriteAllText(path,
   [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String("...")),
   (New-Object System.Text.UTF8Encoding($false)))` command per file, then
   verify the result via `Read` before drafting the commit.
8. **`.git/objects/maintenance.lock` may still be present (0-byte,
   known non-blocking quirk, self-resolving in past sessions).** Check
   `git status` on Yehor's machine before assuming it blocks anything.
9. **Don't trust a tool's self-reported description of what it did —
   check the actual artifact.**
10. **Any new dataclass field added to a result type that's mocked via
    bare `MagicMock()` (not `spec=`'d) anywhere in the test suite must be
    added explicitly to every existing mock-construction site.** Hit
    twice in this exact codebase (2026-07-08, 2026-07-15,
    `test_orchestrator.py` both times).

## A pattern worth naming (carried forward)

Across Sessions 014-016, this file or its underlying memory files have
gone stale, been caught mid-write, or been misread by the sandbox at
least five separate times — two mid-session drifts (014), a stale SHA/
lock claim (015), a truncated-file false positive and a stale-tail false
negative (both 016). None of these were real code defects; all were
either genuine memory drift or sandbox-read artifacts. The lesson that
keeps proving itself: verify via the most direct, independent method
available — `git ls-remote` over any cached SHA, the `Read` tool over
any bash read, a real `pytest` run over `ast.parse` — and when a
secondary check (sandbox) disagrees with the tool that did the actual
write (`Edit`, a `git commit` Yehor ran), trust the latter, then find
out why the former disagreed rather than assuming the write failed.

## Progress list — where things stand (verified fresh 2026-07-15, Session 016 close)

- [x] BACKLOG 13 — Fix-Gen explicit decline path — CLOSED, verified,
      committed (`1ffb038`), pushed.
- [x] BACKLOG 15a — `[DECLINED]` CLI echo path test — CLOSED, verified
      (449 passed), committed (`2b57e52`), pushed.
- [x] `.claude/agents/*.md` naming cleanup — CLOSED, verified via
      `Read`, committed (`7effbad`), pushed. Deliberately left open:
      whether these 3 unreferenced files are worth keeping at all —
      Yehor's call, not decided this session.
- [ ] BACKLOG 15b — `version`/`scan`/`batch` CliRunner coverage — real
      gap, scoped-but-not-sized, not started. Needs its own scoping pass
      before it's startable (same discipline as item 10).
- [ ] BACKLOG item 10 — Mirror Pass Tier 2 — still unscoped anywhere in
      the repo, needs a conversation with Yehor before it's real work.
- [ ] BACKLOG items 9 (PyPI Trusted Publisher), 12 (CRA/GDPR), 8
      (callmed-landing rename), 14 (stray ssh-audit branches) — all
      unchanged, all Yehor-only.

**Nothing in the current backlog is agent-startable without Yehor's
input.** Every item left is either genuinely unscoped (10, 15b) or
requires an external account/legal/business decision only he can make
(9, 12, 8, 14). Full detail and WSJF ordering: `memory/BACKLOG.md`.

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
  `Read`/`Edit`/`Write` tool output, verify real correctness on Yehor's
  machine.
- **`.claude/agents/*` is a protected path for `Edit`/`Write`** — use
  the base64 `WriteAllText` handoff pattern (see Housekeeping item 7).
- **Don't trust a tool's self-reported description of what it did —
  check the actual artifact.**
- **When a tool refuses a path as protected, hand the change to Yehor
  rather than working around it via bash or another channel.**
- **Regenerate this handoff file at the actual end of a session's
  work** — not at the first pause point.

## Suggested first move

No agent-actionable coding work is queued. Ask Yehor what he wants to
look at next: a scoping conversation for Mirror Pass Tier 2 (item 10),
scoping the CLI test-coverage gap properly (15b), or one of the
Yehor-only items (9, 12, 8, 14) if he's ready to act on any of those
himself.
