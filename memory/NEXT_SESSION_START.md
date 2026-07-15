# Patchward — Next Session Start Prompt
Regenerated at the end of Session 018 (2026-07-15), after cross-project
research in `C:\Dev\Projects\Autonomous-Core` resolved item 10 and 14
and rescoped items 8 and 9. Paste this whole file as your opening
message to start the next session with full context restored.

---

**Resume Patchward.** Read `memory/STATE.md`, `memory/BACKLOG.md`, and
`memory/project_session_log.md` (Sessions 015-018) first, in full. Do
not assume anything below is still true without re-checking — verify,
don't trust memory, per standing project rules. This file itself is a
claim to be re-verified, not a source of truth.

## Housekeeping — confirm these before anything else

1. **Run `git ls-remote origin main` yourself — do not trust any SHA
   cited anywhere in this file, including this line.** This isn't
   general caution: it's a structural fact, proven twice in one close
   this session. This file is itself part of the commit chain it
   describes — the moment it's committed, any hash it cites for "the
   current commit" is already one commit behind (this exact thing
   happened twice in a row while closing Session 018: the file said
   "not yet committed" about a commit that then landed; the fix that
   named the new hash was itself committed in a later commit, making
   the named hash stale again on arrival). No amount of re-checking
   before commit fixes this — only checking *after* opening the file
   in a new session does. So: run the command, don't read the number.
2. **Re-confirm Fly health fresh** — `patchward-webhook.fly.dev/healthz`.
   Confirmed OK 2026-07-15, re-checked a second time at the actual
   session close (same result both times).
3. **Re-run the full test suite before trusting it.** Last real number:
   **461 passed, 2 skipped, 15 deselected, 90.46% coverage** —
   2026-07-15, Session 017.
4. **This sandbox's `git status`/`git diff` cannot be trusted.**
   `git log`/`git ls-remote` remain trustworthy.
5. **Sandbox file reads/line-counts can be stale or truncated.** Trust
   `Read`/`Edit`/`Write` tool output over bash reads.
6. **`.claude/agents/*` is a protected path for `Edit`/`Write`** — use
   the base64 `WriteAllText` handoff pattern if it needs touching again.
7. **New this session: a second connected folder,
   `C:\Dev\Projects\Autonomous-Core`, contains real, relevant context
   about Patchward that isn't mirrored in this project's own memory.**
   See "Cross-project findings" below. Treat anything sourced from
   there as Tier 2 (secondhand, another project's own memory files) —
   strong leads, not independently re-verified against live GitHub/PyPI
   state from this session. Worth checking that folder whenever a
   Patchward question feels unanswerable from `memory/`/`docs/`/`src/`
   alone — it wasn't obviously connected to Patchward-specific
   questions before this session.
8. **Don't trust a tool's self-reported description of what it did —
   check the actual artifact.**

## Cross-project findings (Session 018) — action items for Yehor

**Item 9 (PyPI Trusted Publisher) — mostly done, one thing to verify.**
Autonomous-Core's records say Yehor completed the PyPI-side pending
publisher registration 2026-07-08 (project `patchward`, repo
`yehorcallmedai-maker/Patchward`, workflow `publish.yml`, environment
name "Any"). **Check specifically:** does PyPI's pending-publisher page
show the environment field as blank/unrestricted, or literally the text
"Any"? The real `publish.yml` in this repo declares
`environment: name: pypi` — if PyPI has a literal string "Any" rather
than no restriction, the OIDC claim won't match and the first real
publish will fail on identity, not code. If it looks right, trigger
`workflow_dispatch` once (Actions tab → "Publish to PyPI" → Run
workflow) to prove the chain end-to-end.

**Item 10 — REMOVED.** "Mirror Pass Tier 2" was never a Patchward
feature — it's a pricing upsell for a completely different product
(Symbiote / Mirror Pass, $1,500 PEP 484 type-annotation service),
tracked in Autonomous-Core's own backlog. Nothing to do here in this
repo, ever.

**Item 14 — RESOLVED.** The stray branches on `ssh-audit` are confirmed
remnants of PRs #359/#360 against the real upstream `jtesta/ssh-audit`,
rejected 2026-07-03 as "AI slop." Optional cleanup: delete the two
stale branches from your fork (`repomend/fix-bandit.B110-1fdaef`,
`repomend/fix-bandit.B311-6323af`) — safe either way, your call.

**Item 8 (callmed-landing) — narrower than before.** The citation/proof-
count fixes are already live (2026-07-06). What's left: the
RepoMend→Patchward product-name swap on the site copy itself.

**Item 12 (CRA/GDPR) — unchanged, still needs qualified legal input.**
Not found addressed anywhere in either project.

Full detail, sourcing, and the exact quotes behind each of the above:
`memory/BACKLOG.md` items 8, 9, 10 (now removed), 12, 14, and
`memory/project_session_log.md`'s Session 018 entry.

## Progress list — where things stand (2026-07-15, Session 018 close)

- [x] BACKLOG 13, 15a, 15b — all closed, verified, shipped (Sessions 015-017).
- [x] `.claude/agents/*.md` naming cleanup — closed, shipped.
- [x] BACKLOG item 10 — REMOVED, resolved as not-a-Patchward-item.
- [x] BACKLOG item 14 — RESOLVED, origin fully confirmed.
- [ ] BACKLOG item 9 — rescoped, one verification step left (Yehor).
- [ ] BACKLOG item 8 — rescoped, narrower remaining step left (Yehor).
- [ ] BACKLOG item 12 — unchanged, Yehor + external legal counsel.
- [x] Session 018's memory edits — committed and pushed
      (`d8ba1bc` → `b7f9e69` → `b8c0bba`, the last of which removed this
      file's own self-referential hash citation). Independently
      confirmed via `git fetch` + `git ls-remote`, matching Yehor's own
      `git push` output at each step.

## Standing rules (unchanged unless noted, still binding)

- Verify before reporting anything as done.
- **Never run git writes against Patchward from the bash sandbox** —
  hand git writes to Yehor.
- **Never paste or forward API keys/secrets through terminal output
  into chat.**
- Trust-tier logic (BUILD_PLAN_2026-07-10.md Appendix B): Tier 0 (git
  hashes, `git ls-remote`, local exit codes) — accept as-is. Tier 1
  (authenticated direct reads) — accept with evidence. Tier 2
  (proxied/unauthenticated, or **another project's own memory files**)
  — never sufficient alone for a gating decision; treat as a lead to
  verify, not a fact.
- **This sandbox's `git status`/`git diff` cannot be trusted at all.**
- **Sandbox file reads/line-counts can be stale or truncated** — trust
  `Read`/`Edit`/`Write` tool output, verify real correctness on Yehor's
  machine.
- **`.claude/agents/*` is a protected path for `Edit`/`Write`.**
- **Don't trust a tool's self-reported description of what it did —
  check the actual artifact.**
- **Before filing something as "needs scoping" or "blocked," check
  whether the information to scope it is already available** —
  including in a second connected folder, per this session.
- **Regenerate this handoff file at the actual end of a session's
  work** — not at the first pause point.

## Suggested first move

Nothing agent-startable is queued. The four action items above (9, 8,
12, and 14's optional cleanup) are Yehor's to work through at his own
pace — none are urgent, none block anything else in this repo.
