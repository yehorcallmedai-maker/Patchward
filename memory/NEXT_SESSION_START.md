# Patchward — Next Session Start Prompt
Generated at close of Session 013 (2026-07-13). Paste this whole file as
your opening message to start the next session with full context restored.

---

**Resume Patchward.** Read `memory/STATE.md`, `memory/BACKLOG.md`, and
`memory/project_session_log.md` (Session 013 entry) first, in full. Do
not assume anything below is still true without re-checking — verify,
don't trust memory, per standing project rules. This file itself is a
claim to be re-verified, not a source of truth.

## Housekeeping — confirm these before anything else

1. **Confirm `main`'s SHA fresh.** Last known-good, independently
   verified via `git ls-remote origin main` at the actual close of
   Session 013 (after this file's own commit landed):
   `afb6818511a689b13f93e6f5263e9a7f8aa477a5`. (Self-reference note: an
   earlier draft of this file cited `8b601e9` — that was correct when
   written, then went stale the instant Yehor committed this file as
   part of a later commit. Caught and fixed before handoff, per this
   skill's own warning about exactly this trap. Re-check the SHA anyway
   — don't trust this number once time has passed either.)
2. **Re-confirm Fly health fresh** — `patchward-webhook.fly.dev/healthz`,
   cheap and authoritative. Last confirmed OK 2026-07-13 (checked twice,
   most recently after the final commit).
3. **Confirm `.venv` still works before trusting any `uv run` failure as
   a code problem.** Session 013 found `.venv` had gone stale after the
   project directory's rename (uv's Windows trampoline launchers embed
   absolute paths at install time) — `error: uv trampoline failed to
   canonicalize script path` was the symptom, not a code bug. Fix if it
   recurs: `Remove-Item -Recurse -Force .venv` then `uv sync --all-extras`
   (the `--all-extras` flag matters — without it, the webhook test files
   fail to collect). Rebuild after any future directory move/rename.
4. **Do not trust this sandbox's `git status`/`git diff` for anything,
   full stop** — not just for files edited earlier in the same session.
   Session 013 found the sandbox reporting a `fly.toml` drift that didn't
   exist on Yehor's real machine, and later showing nearly the entire
   `src/patchward/` tree as falsely modified. `git log`/`git ls-remote`
   (ref/object reads) remain trustworthy from the sandbox; working-tree
   comparisons do not. Yehor's own machine is the only authority for
   working-tree state.
5. **Don't trust a tool's self-reported description of what it did —
   check the actual artifact.** Session 013's Stage-1 test: Fix-Gen
   reported a correct-sounding fix for one finding; the actual pushed
   diff was objectively broken. Verified by reading `git diff` against
   the real pushed branch, not by trusting the CLI's own summary. Apply
   this same skepticism to any future Fix-Gen/Verifier output before
   treating "VERIFIED" as truth.

## Progress list — where things stand (verified fresh at Session 013 close)

- [x] **Phase 8 (State Reconstruction Audit) — CLOSED.** `memory/STATE.md`,
      `memory/BACKLOG.md`, ADR-027 through ADR-032, and the Consolidated
      Keystone Report (`docs/keystones/consolidated_keystone_2026-06-23_to_2026-07-09.md`)
      committed (`27d0ba3`) and tagged `state-audit-2026-07`. All content
      still marked "not yet reviewed by Yehor" internally — landed and
      pushed is not the same as approved.
- [x] **Test suite re-verified on current `main`:** 421 passed, 2 skipped,
      15 deselected, 90.01% coverage. Supersedes the old pre-rename "371
      passed" figure everywhere it still appears in older docs.
- [x] **Stage-1 E2E pipeline test — run and documented.** Full report:
      `docs/keystones/stage1_e2e_test_2026-07-13.md`. Pipeline confirmed
      working end-to-end (scan → Fix-Gen → Verifier → git push) post-rename.
      3/5 findings reached "verified" status; 0 PRs opened (token
      permission gap); of the 3 "verified" fixes, only 2 are actually
      correct.
- [ ] **BLOCKER — Verifier gate gap (BACKLOG item 3a, HIGH).** A Fix-Gen
      output that deletes a needed import (code still calls it elsewhere)
      passed all 3 Verifier gates as "VERIFIED." Structural gap, not a
      fixture fluke: Gate 1's rescan goes clean because the deletion
      silences the semgrep pattern; Gate 3's test-suite check goes clean
      because nothing exercises the affected function. **Needs Yehor's
      decision on approach** (three candidates sketched in the Stage-1
      report: stronger Gate 1 call-site check / stronger Gate 3 coverage
      requirement / constrain Fix-Gen's prompt against removing
      referenced imports) before implementation. **Recommend this blocks
      Stage 2 (third-party repo) and Mirror Pass Tier 2** until resolved.
- [ ] `GITHUB_TOKEN` cannot create PRs (BACKLOG item 3b, MEDIUM) — pushes
      succeed, `POST /pulls` returns 403. Check token permissions
      (fine-grained: needs "Pull requests: write"; classic: check expiry).
- [ ] CLI misreports failed PR creation as success (BACKLOG item 3c, LOW)
      — `cli.py` L496-499, confirmed by direct code read, cheap fix.
- [ ] "requires login" invalid branch name (BACKLOG item 3d) — root cause
      not yet investigated, hypothesis only (semgrep registry auth
      message leaking into fingerprint pipeline).
- [ ] `patchward.toml.example` has the same config-loading defect just
      fixed in the real `patchward.toml` (BACKLOG item 6a) — no
      `repo_path` documented, wrong `[anthropic]` section that doesn't
      match `config.py`'s actual schema.
- [ ] `docs/architecture/patchward-webhook-billing-design.md` is cited by
      three KS-TRACE comments but doesn't exist (BACKLOG item 6) —
      recreate from the ADRs, or scrub the references. Undecided.
- [ ] `memory/project_open_tasks.md` reconciliation (BACKLOG item 7) —
      still not decided: fold into BACKLOG.md and archive, or keep
      maintaining separately.
- [ ] `runs/state.db` is tracked in git despite `.gitignore` listing it —
      pre-existing gap, needs a `git rm --cached runs/state.db` cleanup
      commit whenever convenient.
- [ ] `tests/fixture_repo` remains a non-submodule embedded repo with its
      own local diff — pre-existing, still not investigated, low urgency.
- [ ] ClinInsight/Databutton LinkedIn DM replies — still unconfirmed, no
      tool access to check, answer directly with Yehor.
- [ ] PyPI Trusted Publisher — workflow scaffolded, PyPI-side
      registration status still unconfirmed, no release tagged yet
      (BACKLOG item 9).
- [ ] Regulatory flags (CRA/GDPR classification) — needed before any paid
      Marketplace listing, not before (BACKLOG item 12).
- [ ] callmed-landing rename — cheap, zero-dependency, slot in whenever
      (BACKLOG item 8).

Full detail and WSJF ordering for all of the above: `memory/BACKLOG.md`.

## Standing rules (unchanged unless noted, still binding)

- Verify before reporting anything as done — re-fetch/re-check live
  state, never trust a prior session's cached belief.
- **Never run git writes against Patchward from the bash sandbox** — hand
  git writes to Yehor to run on his own machine. This includes not just
  `commit`/`push` but `restore`, `tag`, and anything else that mutates
  refs or the working tree.
- **Never paste or forward API keys/secrets through terminal output into chat.**
- Apply the trust-tier logic from `BUILD_PLAN_2026-07-10.md` Appendix B:
  Tier 0 (git hashes, `git ls-remote`, local exit codes) — accept as-is.
  Tier 1 (authenticated direct reads, e.g. a direct HTTPS healthz probe)
  — accept with evidence. Tier 2 (proxied/unauthenticated reads, e.g.
  `api.github.com` from this sandbox) — never sufficient alone for a
  gating decision.
- **This sandbox's `git status`/`git diff` (working-tree comparisons)
  cannot be trusted at all** — refined and hardened this session from the
  earlier, narrower "don't trust it for same-session edits" rule. `git
  log`/`git ls-remote` remain trustworthy.
- **When a commit message is long or multi-line, write it to a file and
  use `git commit -F <file>`, not inline `-m`** — avoids PowerShell
  quoting risk. Delete the temp file after, and don't assume the delete
  worked without checking.
- **Diff anything `git status` flags that you didn't expect to have
  changed, before staging it** — Session 013 found `uv.lock` modified for
  a legitimate reason (webhook extras being locked for the first time)
  only after actually diffing it, not assuming from the size of the change.
- **Trust the file-reading tool over shell `cat`/`wc`/`diff` for
  integrity checks** — the sandbox's shell mount can lag behind the real
  file state; the file tool has not shown this problem this project.
- **The agent's sandbox should not run `git status`/`git diff` against
  this repo at all going forward — not just "don't trust the output."**
  Confirmed this session: a sandbox `git status` call left a stale
  `.git/index.lock` that then blocked Yehor's real `git add`/`git commit`
  on his own machine with "Unable to create index.lock: File exists" —
  because the sandbox and Yehor's machine share the same underlying
  files. This is a step up from the earlier finding (unreliable *output*)
  to a confirmed real *side effect* that breaks the human's own tools.
  Restrict sandbox git usage to `git log`/`git ls-remote` (pure ref
  reads, no index touched) only. If a stale lock does appear, the fix is
  unchanged: `Remove-Item <path> -Force` on Yehor's machine.

## Suggested first move

Ask directly: "How do you want to close the Verifier gate gap (BACKLOG
item 3a)? Three directions are on the table: (1) Gate 1 additionally
confirms the specific dangerous call site is gone, not just that the
scanner rule stops firing, (2) Gate 3 requires the modified file's own
tests to cover the changed function, (3) constrain Fix-Gen's prompt to
never remove an import still referenced elsewhere in the file. Pick one,
some combination, or tell me if you see a better option — this is the
one thing standing between here and Stage 2 or Mirror Pass Tier 2." Don't
default to the smaller housekeeping items (`GITHUB_TOKEN` permissions,
the CLI misreport bug) as "the next thing" just because they're easier —
they're real but lower-stakes than this one.
