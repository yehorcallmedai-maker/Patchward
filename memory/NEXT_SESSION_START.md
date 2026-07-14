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
   pass: `66bb9c095597eb1db19b6777bf92bb7c5d9ee6bb`. Confirmed matching
   local HEAD on Yehor's machine the same session (`git push` +
   `git ls-remote` + `git log -1` all agreed). Re-check anyway.
2. **Re-confirm Fly health fresh** — `patchward-webhook.fly.dev/healthz`,
   cheap and authoritative. Last confirmed OK 2026-07-14 (re-checked live
   during this strategy pass, not just re-cited from memory).
3. **Confirm `.venv` still works** — last confirmed OK by Yehor directly
   on his own machine 2026-07-14. Re-check anyway; rebuild only if it
   actually fails (`Remove-Item -Recurse -Force .venv` then
   `uv sync --all-extras`).
4. **Re-run the full test suite before trusting it.** Last real number:
   **439 passed, 2 skipped, 90.30% coverage**, from BACKLOG 3d's fix
   (Yehor's `.venv`, real machine). Everything since (3b, 6, 7 closures)
   was documentation-only — no source file changed — so this number is
   *expected* to still hold, but it has not been re-run since and should
   not be cited as freshly confirmed until it is.
5. **This sandbox's `git status`/`git diff` (working-tree comparisons)
   cannot be trusted at all** — unchanged from prior sessions. `git
   log`/`git ls-remote` (ref/object reads) remain trustworthy. Restrict
   sandbox git usage to those two.
6. **Sandbox file reads can also be stale on recently-edited files** —
   confirmed this session (`cli.py` served truncated/days-old from the
   bash mount while `verifier.py` synced fine same session — file-specific,
   not universal). Trust the Read tool's view; verify compile/tests on
   Yehor's real machine, not the sandbox.
7. **Don't trust a tool's self-reported description of what it did —
   check the actual artifact.**
8. **PowerShell heredoc paste is unreliable on this machine for
   multi-line strings** (backticks/parens/colons, or plain multi-line
   `if/elseif/else`). Confirmed multiple times this session in both
   forms. **Working pattern:** base64-encode the text in the sandbox
   (single line, no shell metacharacters), then decode via
   `[System.IO.File]::WriteAllText(path, [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($b64)), (New-Object System.Text.UTF8Encoding($false)))`
   on Yehor's machine. For conditionals, write the whole thing on one
   line instead of a multi-line block.

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
- [ ] `runs/state.db` tracked despite `.gitignore` — pre-existing,
      low priority, needs `git rm --cached runs/state.db` on Yehor's
      machine whenever convenient (real git write).
- [ ] `tests/fixture_repo` — pre-existing dirty embedded repo, still not
      investigated, low urgency.
- [ ] ClinInsight/Databutton LinkedIn DM replies — still unconfirmed,
      no tool access, answer directly with Yehor.
- [ ] Regulatory flags (CRA/GDPR) — needed before paid listing, not now
      (BACKLOG 12).
- [ ] `callmed-landing` rename — different repo, out of scope this
      session (BACKLOG 8).
- [ ] **Stage 2 (BACKLOG item 11) — authorized third-party E2E test.**
      **No longer blocked.** All four Stage-1-discovered defects (3a,
      3b, 3c, 3d) are closed and pushed. This is now the single highest-
      leverage next move — it's the first real test of whether the
      pipeline can produce an actual, correct PR end-to-end since the
      rename. Requires Yehor's explicit authorization before running
      (real action on a third-party repo, not the fixture).
- [ ] **Mirror Pass Tier 2 (BACKLOG item 10)** — contingent on Stage 2
      passing cleanly, don't start before it.

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

## Suggested first move

Confirm housekeeping items 1-4 above (SHA, Fly health, `.venv`, and — new
this pass — a fresh full test-suite run, since docs-only commits landed
after the last real run). Then ask Yehor directly: "Every Stage-1-
discovered defect is closed. Do you want to authorize Stage 2 (a real
third-party E2E test) now, or is there something else to prioritize
first?" Don't assume Stage 2 is automatically next just because it's
unblocked — confirm, the same way this session confirmed each fix's
approach before implementing rather than defaulting to the easiest
reading of the backlog.
