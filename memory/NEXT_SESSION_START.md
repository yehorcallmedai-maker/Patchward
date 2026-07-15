# Patchward — Next Session Start Prompt
Regenerated at the actual end of Session 017 (2026-07-15), after
BACKLOG 15b landed and was verified (461 passed). Paste this whole file
as your opening message to start the next session with full context
restored.

---

**Resume Patchward.** Read `memory/STATE.md`, `memory/BACKLOG.md`, and
`memory/project_session_log.md` (Sessions 015-017) first, in full. Do
not assume anything below is still true without re-checking — verify,
don't trust memory, per standing project rules. This file itself is a
claim to be re-verified, not a source of truth (see "A pattern worth
naming" below).

## Housekeeping — confirm these before anything else

1. **Confirm the Session 017 commit landed.** Drafted:
   `test(cli): add dedicated test_cli.py covering version/scan/batch
   (BACKLOG 15b)`. Confirm via `git log --oneline -3` and
   `git ls-remote origin main` before trusting any SHA cited below.
2. **Re-confirm Fly health fresh** — `patchward-webhook.fly.dev/healthz`.
   Confirmed OK 2026-07-15 (direct HTTPS GET, Tier 1). Re-check anyway.
3. **Confirm `.venv` still works.** Confirmed OK by Yehor on his own
   machine 2026-07-15 (four full test runs across Sessions 015-017).
   Re-check anyway; rebuild only if it actually fails.
4. **Re-run the full test suite before trusting it.** Last real number:
   **461 passed, 2 skipped, 15 deselected, 90.46% coverage** — Yehor's
   `.venv`, real machine, 2026-07-15, Session 017 (added
   `tests/test_cli.py`, 12 new tests). Re-confirm rather than cite cold.
5. **This sandbox's `git status`/`git diff` cannot be trusted at all.**
   `git log`/`git ls-remote` remain trustworthy. Restrict sandbox git
   usage to those two.
6. **Sandbox file reads/line-counts can be stale OR truncated.**
   Confirmed multiple times across Sessions 014-016. Trust `Read`/
   `Edit`/`Write` tool output over any bash `cat`/`wc`/`tail`/`grep`/
   `py_compile` read. Verify real correctness only on Yehor's machine.
7. **`.claude/agents/*` is a protected path for `Edit`/`Write` tools —
   `Read` works fine.** If a future change is needed there, the working
   pattern: generate corrected content, base64-encode it, hand Yehor a
   single-line PowerShell `WriteAllText` command per file, verify via
   `Read` before drafting the commit.
8. **`.git/objects/maintenance.lock` may still be present (0-byte,
   known non-blocking quirk).** Check `git status` on Yehor's machine
   before assuming it blocks anything.
9. **Don't trust a tool's self-reported description of what it did —
   check the actual artifact.**
10. **Any new dataclass field added to a result type that's mocked via
    bare `MagicMock()` (not `spec=`'d) anywhere in the test suite must be
    added explicitly to every existing mock-construction site.** Hit
    twice in this exact codebase (2026-07-08, 2026-07-15).
11. **When a synthesis pass files something as "needs scoping" or
    "blocked," check whether that's actually true or just "not yet
    scoped by me."** New this session (017) — the two look identical
    from outside but call for opposite responses: defer to the user, or
    finish the scoping and just build it. Item 10 (Mirror Pass Tier 2)
    is a genuine instance of the former (zero spec anywhere in the
    repo); item 15b turned out to be the latter and got built same-day
    once actually scoped.

## A pattern worth naming (carried forward)

Across Sessions 014-017: two mid-session memory drifts (014), a stale
SHA/lock claim (015), a truncated-file false positive and a stale-tail
false negative (016), and a false "blocked" classification that turned
out to just be unfinished scoping (017). None were real code defects —
all were either memory drift, sandbox-read artifacts, or premature
deferral. Keep verifying via the most direct, independent method
available, and keep checking whether "blocked" claims are actually true
before accepting them, including ones made by a prior pass in this same
session.

## Progress list — where things stand (verified fresh 2026-07-15, Session 017 close)

- [x] BACKLOG 13 — Fix-Gen explicit decline path — CLOSED, verified, shipped.
- [x] BACKLOG 15a — `[DECLINED]` CLI echo path test — CLOSED, verified, shipped.
- [x] `.claude/agents/*.md` naming cleanup — CLOSED, verified, shipped.
- [x] **BACKLOG 15b — `version`/`scan`/`batch` CliRunner coverage —
      CLOSED 2026-07-15.** `tests/test_cli.py` created (12 tests),
      verified (461 passed), commit drafted — **confirm it landed
      (Housekeeping item 1) before trusting this as done.**
- [ ] BACKLOG item 10 — Mirror Pass Tier 2 — still unscoped anywhere in
      the repo (confirmed twice now, Sessions 015 and 017). Genuinely
      needs a conversation with Yehor before it's real work — this is
      not a case of "just scope it yourself," unlike 15b turned out to be.
- [ ] BACKLOG items 9 (PyPI Trusted Publisher), 12 (CRA/GDPR), 8
      (callmed-landing rename), 14 (stray ssh-audit branches) — all
      unchanged, all Yehor-only.

**Nothing agent-startable remains that hasn't been checked twice now.**
Item 10 is confirmed-unscoped (not just assumed), items 9/12/8/14 are
genuinely external. Full detail and WSJF ordering: `memory/BACKLOG.md`.

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
  the base64 `WriteAllText` handoff pattern.
- **Don't trust a tool's self-reported description of what it did —
  check the actual artifact.**
- **When a tool refuses a path as protected, hand the change to Yehor
  rather than working around it.**
- **Before filing something as "needs scoping" or "blocked," check
  whether the information to scope it is already available.**
- **Regenerate this handoff file at the actual end of a session's
  work** — not at the first pause point.

## Suggested first move

Confirm Housekeeping item 1 (commit landed) and item 4 (test suite,
already done this session but re-confirm per standing rule). After
that, there is genuinely nothing left for the agent to pick up
unilaterally — item 10 needs Yehor to describe what "Mirror Pass Tier 2"
actually means before it can be scoped at all, and everything else is
external. Ask Yehor what he wants to do next.
