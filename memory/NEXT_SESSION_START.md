# Patchward — Next Session Start Prompt
Regenerated during Session 014's continuation (2026-07-14), superseding
the version generated earlier the same session (which went stale within
the session itself — see the Drift note below). Paste this whole file as
your opening message to start the next session with full context restored.

---

**Resume Patchward.** Read `memory/STATE.md`, `memory/BACKLOG.md`, and
`memory/project_session_log.md` (Session 014 entry and both addenda)
first, in full. Do not assume anything below is still true without
re-checking — verify, don't trust memory, per standing project rules.
This file itself is a claim to be re-verified, not a source of truth.

## Drift note (why this file was regenerated mid-session)

The first version of this file was written at Session 014's initial
close-out point, after only BACKLOG 3a landed. Yehor then asked to keep
going down the full progress list, and 3c, 3d, 6a, 6, 7, and 3b all
closed in the same session — but the handoff file was never
regenerated to match until this pass (caught via
`/session-strategy-synthesis`'s drift check). **Lesson carried forward:
regenerate this file at the actual end of a session's work, not at the
first natural pause point** — or, if the session keeps going after this
file is written, treat it as stale until explicitly redone.

## Housekeeping — confirm these before anything else

1. **Confirm `main`'s SHA fresh.** Last known-good, independently
   verified via `git ls-remote origin main` at the actual close of this
   session: `7225a12fba859e0f61e6b70e956ef491cba5b87d`. Confirmed
   matching local HEAD on Yehor's machine, `git ls-remote`, and a fresh
   independent sandbox `git log` — three methods, same session, all
   agreed. Re-check anyway; this file's own claims have gone stale
   mid-session before (see the Drift note above and Session 013/014's
   logs).
2. **Check for a stuck `.git/index.lock` / `.git/objects/maintenance.lock`
   before your first git command.** The sandbox's own mount shows both
   present as of this session's close (0-byte files, consistent with
   the known quirk documented in `BACKLOG.md`'s "Deferred, not
   forgotten" section — a mount permission boundary, not real
   corruption, seen self-resolving in Sessions 012 and 013). **This has
   not been confirmed as actually blocking anything on Yehor's real
   machine** — check `git status` there first. If it genuinely blocks a
   real git command: `Remove-Item .git\index.lock -Force` (and the
   `maintenance.lock` equivalent if needed) on Yehor's own machine, per
   the established pattern. Don't assume it's already resolved just
   because it has been twice before.
3. **Re-confirm Fly health fresh** — `patchward-webhook.fly.dev/healthz`,
   cheap and authoritative. Last confirmed OK 2026-07-14 (re-checked live
   during this strategy pass, not just re-cited from memory).
4. **Confirm `.venv` still works** — last confirmed OK by Yehor directly
   on his own machine 2026-07-14. Re-check anyway; rebuild only if it
   actually fails (`Remove-Item -Recurse -Force .venv` then
   `uv sync --all-extras`).
5. **Re-run the full test suite before trusting it.** Last real number:
   **441 passed, 2 skipped, 90.31% coverage**, from BACKLOG 7b's fix
   (Yehor's `.venv`, real machine, this session's final test run). Any
   session after this one should still re-confirm rather than cite this
   number cold.
6. **This sandbox's `git status`/`git diff` (working-tree comparisons)
   cannot be trusted at all** — unchanged from prior sessions. `git
   log`/`git ls-remote` (ref/object reads) remain trustworthy. Restrict
   sandbox git usage to those two.
7. **Sandbox file reads can also be stale on recently-edited files** —
   confirmed this session (`cli.py` served truncated/days-old from the
   bash mount while `verifier.py` synced fine same session — file-specific,
   not universal). Trust the Read tool's view; verify compile/tests on
   Yehor's real machine, not the sandbox.
8. **Don't trust a tool's self-reported description of what it did —
   check the actual artifact.**
9. **PowerShell heredoc paste is unreliable on this machine for
   multi-line strings** (backticks/parens/colons, or plain multi-line
   `if/elseif/else`). Confirmed multiple times this session in both
   forms. **Working pattern:** base64-encode the text in the sandbox
   (single line, no shell metacharacters), then decode via
   `[System.IO.File]::WriteAllText(path, [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($b64)), (New-Object System.Text.UTF8Encoding($false)))`
   on Yehor's machine. For conditionals, write the whole thing on one
   line instead of a multi-line block.

## Drift note 2 — this file went stale a second time within the same session

Regenerated again after `/session-strategy-synthesis` was run a further
time to close every remaining "pinned decision": BACKLOG 7a (structured
PR template — corrected, was already implemented), 7b (risk-class
routing — rescoped to a concrete, scoped gap), 7c (`.dockerignore` —
the "untracked" claim was itself wrong, corrected visibly), 7d
(`tests/fixture_repo`'s one-line docstring diff — committed after fresh
Pass 2 verification), `runs/state.db` (untracked from git), and the
ClinInsight/Databutton item (removed from engineering memory, it never
belonged here). Current HEAD: `234cbc2`. **Pattern to actually break
next time:** regenerate this file once, at the point work stops for
real — not proactively after every sub-pass, and not so late that two
rounds of drift accumulate. Somewhere between those extremes.

## Progress list — where things stand (verified fresh at this pass)

- [x] **Phase 8 (State Reconstruction Audit) — CLOSED**, tagged
      `state-audit-2026-07`.
- [x] **Stage-1 E2E pipeline test — run and documented** (Session 013).
- [x] **BACKLOG 3a — Verifier gate gap — CLOSED, commit `b2559a5`.**
      Gate 2 now rejects an import removal (in-range or out-of-range)
      unless `_removed_import_still_referenced()` proves it's genuinely
      unused. Full suite: 431 passed at the time, since risen to 439.
- [x] **BACKLOG 3b — `GITHUB_TOKEN` cannot create PRs — CLOSED, no code
      change.** Root cause: fine-grained PAT had Contents (read/write)
      and Metadata (read-only) but no Pull Requests permission at all.
      Yehor added Pull requests: Read and write to the existing token in
      place (no regeneration, `.env` untouched). Verified via a live
      `POST /pulls` call (head=main, base=main, deliberately no diff)
      returning `422` (validation error reached only after permission
      checks pass) instead of `403`. **Stage 2 is now unblocked.**
- [x] **BACKLOG 3c — CLI misreports failed PR creation as success —
      CLOSED, commit `190fb01`.** `cli.py` now branches on
      `pr_dict['status']` instead of printing "[PR] Opened" unconditionally.
- [x] **BACKLOG 3d — "requires login" invalid branch name — CLOSED,
      commit `ee5e465`.** `sanitize_branch_component()` added to
      `worktree_common.py`, wired into both `cli.py` and `pipeline.py`.
      Upstream root cause (why semgrep's fingerprint contained that
      text) remains unconfirmed — the crash is fixed regardless.
- [x] **BACKLOG 6a — `patchward.toml.example` schema mismatch — CLOSED,
      commit `435ab94`.** Rewritten to match `config.py`'s real schema;
      verified by actually running `load_config()` against it.
- [x] **BACKLOG 6 — dead architecture-doc citations — CLOSED, commit
      `31ae2f0`.** Decision: scrub, don't recreate (ADR-028/030 already
      are the canonical reconstructed record). All 5 citations (not 3 —
      recount caught 2 more) rewritten to point at
      `memory/architectural_decisions.md`.
- [x] **BACKLOG 7 — `project_open_tasks.md` reconciliation — CLOSED,
      commit `31ae2f0`.** Decision: fold + archive. Archive banner
      added; 2 genuinely novel items folded forward as 7a/7b
      (unscored, relevance to current product direction unconfirmed —
      Yehor's call if/when to prioritize).
- [x] Memory close-out for all of the above committed and pushed —
      `66bb9c0` confirmed matching `origin/main`.
- [ ] **BACKLOG 9 — PyPI Trusted Publisher — confirm live.** Still open,
      Yehor-only (PyPI account access required). Confirm the PyPI-side
      Trusted Publisher registration exists and that
      `.github/workflows/publish.yml` has actually run at least once via
      `workflow_dispatch`.
- [x] **`runs/state.db` — untracked from git**, commit `234cbc2`.
- [x] **`tests/fixture_repo` — one-line docstring diff committed**
      (submodule commit `3984504`, parent pointer bumped in `234cbc2`),
      after a fresh Pass 2 `git status`/`git diff` confirmed it matched
      the prior harmless-diff claim exactly.
- [x] **BACKLOG 7a (structured PR template) — corrected and closed.**
      `pr_publisher.py` already implements a five-section PR body
      template; a prior grep-only pass wrongly claimed it didn't exist.
- [x] **BACKLOG 7b (risk-class in PR body) — CLOSED, commit `53cd052`.**
      `_build_pr_body()` now shows `**Risk class:**` in the Finding
      section (falls back to `unknown`). 441 passed, 90.31% coverage.
      No behavior-gating added — that's a separate, unscheduled product
      decision.
- [x] **`.dockerignore` — the "untracked" claim was itself wrong,
      corrected.** It's been tracked since `8b601e9`. No action needed.
- [x] **ClinInsight/Databutton LinkedIn DM item — removed from
      Patchward's engineering memory entirely** (visibly, not silently
      — see `BACKLOG.md`). It never belonged in this project's tracker.
- [ ] Regulatory flags (CRA/GDPR) — needed before paid listing, not now
      (BACKLOG 12).
- [ ] `callmed-landing` rename — different repo, out of scope this
      session (BACKLOG 8).
- [x] **Stage 2 (BACKLOG item 11) — authorized third-party E2E test —
      COMPLETE.** Ran against `yehorcallmedai-maker/ssh-audit` (Yehor's
      own public fork, chosen via a scored shortlist of his 26 repos —
      see BACKLOG item 11 for the full selection rationale). Result: 1
      finding verified and shipped as real draft PR
      `github.com/yehorcallmedai-maker/ssh-audit/pull/1` (confirmed via
      `gh pr view`/`gh pr diff`, not CLI self-report), 4 correctly
      declined rather than force-fixed. **The pipeline is now validated
      end-to-end against a real third-party repo, not just the
      fixture.** New non-blocking item opened (13 — Fix-Gen's decline
      path is implicit/ambiguous). New evidence for 3d's still-open
      root cause (see BACKLOG item 11's writeup).
- [ ] **Mirror Pass Tier 2 (BACKLOG item 10)** — Stage 2 has now passed
      cleanly, so this is unblocked. Not started.
- [ ] **BACKLOG item 13 (NEW) — Fix-Gen's "decline, not a real issue"
      path is implicit.** Currently just exhausts `max_turns` without
      calling `submit_fix`, which is safe but produces an ambiguous log
      signal. Low-medium priority, not scheduled.
- [ ] Local `patchward.toml` (gitignored) currently points at
      `D:/Dev/Projects/ssh-audit` / repo `ssh-audit` / base `master`
      from Stage 2. Not reverted to the fixture — low-stakes since it's
      local-only, but worth knowing before assuming a future `patchward
      scan`/`fix` invocation targets the fixture by default.
- [x] **PR #1 on `ssh-audit` — squash-merged, branch deleted.** Was
      draft (ADR-019); `gh pr merge` initially failed as expected
      ("still a draft"), resolved via `gh pr ready` then `gh pr merge
      --squash --delete-branch`. Stage 2's full loop (scan → fix →
      verify → push → PR → human review → merge) is now complete.
- [ ] **NEW — BACKLOG item 14: stray pre-rename branches on `ssh-audit`.**
      Found during final close-out verification (fresh clone + `git
      ls-remote`): two branches (`repomend/fix-bandit.B110-1fdaef`,
      `repomend/fix-bandit.B311-6323af`) dated 2026-06-29, using the old
      `repomend/` prefix, never logged anywhere in this project's
      memory before now. Undocumented earlier run of the tool against
      this repo. Owner: Yehor — only he can confirm origin/intent; not
      investigated further. See BACKLOG item 14 for full detail
      including a real data point for item 13 (Fix-Gen historically DID
      produce a fix for the B311 finding today's run declined).
- [x] **`future-agi-contribution/` directory — relocated, not a
      Patchward concern.** Was a separate, actively-managed OSS-
      contribution project's working directory (own `.strategy/
      STRATEGY.md`), nested inside Patchward's tree by circumstance —
      untracked by Patchward's git throughout, verified via direct file
      read as genuine (not an error/security concern). Moved to
      `D:\Dev\Projects\future-agi-contribution` — verified gone from
      Patchward's tree via `Test-Path`. That project continues in its
      own session; no further action here.

Full detail and WSJF ordering for all of the above: `memory/BACKLOG.md`.

## Standing rules (unchanged unless noted, still binding)

- Verify before reporting anything as done — re-fetch/re-check live
  state, never trust a prior session's cached belief, **including this
  file itself** (see Drift note above — it went stale within its own
  session once already).
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
- **Sandbox file reads can go stale on recently-edited files too** —
  trust the Read tool over sandbox `cat`/`wc`/`diff`/`py_compile`;
  verify compile/tests on Yehor's real machine.
- **Long/multi-line commit messages or PowerShell conditionals: use the
  base64 + `WriteAllText` pattern, or a single unbroken line** — not a
  heredoc, not a multi-line pasted `if/elseif/else` block.
- **Diff anything `git status` flags that you didn't expect to have
  changed, before staging it.**
- **Don't trust a tool's self-reported description of what it did —
  check the actual artifact.**
- **Regenerate this handoff file at the actual end of a session's
  work** — not at the first pause point, per this session's own drift.

## New capability this session: GitHub CLI

`gh` is now installed and authenticated on Yehor's machine (`gh auth
login` completed, device-flow authorized for the `yehorcallmedai-maker`
account, including org access to FixProve and yehorkaliberda). Useful
for `gh repo list`/`gh repo view`/`gh pr view`/`gh pr diff` — all used
this session for independent verification (not trusting CLI self-report
or the sandbox's unauthenticated API view, which returns nothing for
this account's repos).

## Suggested first move

Confirm housekeeping items 1-4 above (SHA, Fly health, `.venv`, fresh
full test-suite run). Stage 2 is now complete — the pipeline has a real,
independently-verified draft PR on a third-party repo
(`ssh-audit/pull/1`). Nothing in this session's original scope remains
open except items only Yehor can act on: PyPI Trusted Publisher
confirmation (item 9), regulatory CRA/GDPR classification (item 12),
`callmed-landing` rename (item 8, different repo), and whether/when to
merge or close PR #1 on `ssh-audit` (it's a real open draft PR now — not
urgent, but not nothing either). Ask Yehor what he wants to look at next
rather than assuming continuation into Mirror Pass Tier 2 (item 10)
just because it's now unblocked.
