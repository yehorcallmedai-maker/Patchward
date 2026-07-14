# Patchward — Next Session Start Prompt
Generated at close of Session 014 (2026-07-14). Paste this whole file as
your opening message to start the next session with full context restored.

---

**Resume Patchward.** Read `memory/STATE.md`, `memory/BACKLOG.md`, and
`memory/project_session_log.md` (Session 014 entry) first, in full. Do
not assume anything below is still true without re-checking — verify,
don't trust memory, per standing project rules. This file itself is a
claim to be re-verified, not a source of truth.

## Housekeeping — confirm these before anything else

1. **Confirm `main`'s SHA fresh.** Last known-good, independently
   verified via `git ls-remote origin main` at the actual close of
   Session 014: `b2559a586225a837f2bb7a745466b6cedad204d2`. Confirmed
   matching local HEAD on Yehor's machine the same session. Re-check
   anyway — this file's own SHA claims have gone stale mid-session
   before (see Session 013's and 014's logs both).
2. **Re-confirm Fly health fresh** — `patchward-webhook.fly.dev/healthz`,
   cheap and authoritative. Last confirmed OK 2026-07-14.
3. **Confirm `.venv` still works** — confirmed OK by Yehor directly on
   his own machine 2026-07-14 (`uv run python -c "print('venv OK')"`).
   Re-check anyway; rebuild only if it actually fails
   (`Remove-Item -Recurse -Force .venv` then `uv sync --all-extras`).
4. **This sandbox's `git status`/`git diff` (working-tree comparisons)
   cannot be trusted at all** — unchanged from prior sessions. `git
   log`/`git ls-remote` (ref/object reads) remain trustworthy. Restrict
   sandbox git usage to those two.
5. **Don't trust a tool's self-reported description of what it did —
   check the actual artifact.** Reconfirmed again this session in a new
   way: after the Gate 2 fix was committed, the CLI's own PR-creation
   misreport bug (BACKLOG 3c — prints "[PR] Opened" even on a 403) is
   still live and unfixed. Any future PR-creation test must be verified
   against the real GitHub API/UI, not the CLI's own success message.
6. **PowerShell heredoc paste is unreliable on this machine for
   multi-line strings containing backticks/parens/colons.** Confirmed
   twice this session — both a `-Encoding utf8NoBOM` failure (invalid on
   Windows PowerShell 5.1) and a full heredoc-parsing corruption (the
   `@"` opener didn't register, so PowerShell tried to execute every
   line of a commit message as its own command). **Working pattern:**
   base64-encode the text in the sandbox (single line, no shell
   metacharacters), then decode via
   `[System.IO.File]::WriteAllText(path, [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($b64)), (New-Object System.Text.UTF8Encoding($false)))`
   on Yehor's machine. Use this pattern first for any commit message or
   file content longer than one line — don't reach for a heredoc.

## Progress list — where things stand (verified fresh at Session 014 close)

- [x] **Phase 8 (State Reconstruction Audit) — CLOSED**, tagged
      `state-audit-2026-07`, confirmed still pointing at `27d0ba3`.
- [x] **Stage-1 E2E pipeline test — run and documented** (Session 013).
- [x] **BACKLOG 3a — Verifier gate gap — CLOSED 2026-07-14, commit
      `b2559a5`.** Gate 2 (`_out_of_bounds_lines` in `verifier.py`) now
      rejects an import removal — whether inside the nominal vuln range
      (where the actual Stage-1 defect lived: bandit B404's flagged line
      *is* the import statement) or outside it — unless
      `_removed_import_still_referenced()` (AST-based, conservative on
      any ambiguity) proves the removed name is unused elsewhere in the
      post-edit file. Regression test reproduces the exact Stage-1
      shape; contrast test confirms genuinely-unused import removal
      still passes. Full suite re-verified by Yehor: 431 passed, 2
      skipped, 90.25% coverage. Pushed and confirmed on `origin/main`.
      **Deferred, not closed by this fix** (separate follow-ups, do not
      assume they're covered): excluding purely-informational bandit
      rules like B404 from Fix-Gen's candidates at the pipeline level
      (no filter mechanism exists yet); broadening Gate 1's rescan
      beyond the single rule_id; converting Gate 3 into a soft
      confidence signal instead of a hard gate. None of these are
      currently blocking — they're future hardening, revisit if Stage 2
      surfaces a new gap in the same family.
- [ ] **BACKLOG 3b — `GITHUB_TOKEN` cannot create PRs (MEDIUM).** Still
      open, untouched this session. Branches push; `POST /pulls`
      returned 403 three times in Stage-1. This is the next real
      blocker for Stage 2 specifically — Stage 2's actual deliverable is
      a real draft PR on a third-party repo (BACKLOG item 11), and
      without this fixed, a Stage 2 run would reproduce the same
      "branches push, zero PRs" outcome Stage 1 already found. **Owner:**
      Yehor — check `GITHUB_TOKEN`'s type/permissions (GitHub → Settings
      → Developer settings → Personal access tokens). Fine-grained:
      needs "Pull requests: Read and write". Classic: check expiry/scope.
- [ ] **BACKLOG 3c — CLI misreports failed PR creation as success
      (LOW).** `cli.py` L496-499, confirmed by direct code read, cheap
      one-condition fix. Worth bundling into whichever session tests 3b,
      since a fixed token makes this bug harder to accidentally re-hide.
- [ ] **BACKLOG 3d — "requires login" invalid branch name (unconfirmed
      root cause).** Hypothesis only (semgrep registry auth message
      leaking into the fingerprint pipeline). Not investigated. Low
      urgency unless it recurs in a future run.
- [ ] `patchward.toml.example` config-loading defect (BACKLOG 6a).
- [ ] `docs/architecture/patchward-webhook-billing-design.md` — cited,
      doesn't exist (BACKLOG 6). Undecided: recreate or scrub references.
- [ ] `memory/project_open_tasks.md` reconciliation (BACKLOG 7).
- [ ] `runs/state.db` tracked despite `.gitignore` (pre-existing,
      still present, still unstaged in every session's `git status` —
      needs a `git rm --cached runs/state.db` cleanup commit whenever
      convenient).
- [ ] `tests/fixture_repo` — pre-existing dirty embedded repo, still
      not investigated, low urgency.
- [ ] ClinInsight/Databutton LinkedIn DM replies — still unconfirmed.
- [ ] PyPI Trusted Publisher — registration status still unconfirmed
      (BACKLOG 9).
- [ ] Regulatory flags (CRA/GDPR) — needed before paid listing, not now
      (BACKLOG 12).
- [ ] callmed-landing rename — cheap, zero-dependency filler task
      (BACKLOG 8).
- [ ] **Stage 2 (third-party E2E test) and Mirror Pass Tier 2** — BACKLOG
      3a's specific blocker is resolved, but Stage 2 additionally needs
      3b resolved first (see above) to actually produce its deliverable.
      Don't start Stage 2 until 3b is confirmed working, or you'll get
      an uninformative repeat of Stage 1's "no PRs opened" result.

Full detail and WSJF ordering for all of the above: `memory/BACKLOG.md`.

## Standing rules (unchanged unless noted, still binding)

- Verify before reporting anything as done — re-fetch/re-check live
  state, never trust a prior session's cached belief.
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
- **Long/multi-line commit messages: use the base64 + `WriteAllText`
  pattern (see Housekeeping item 6 above), not a PowerShell heredoc.**
  This supersedes the older "use `git commit -F`, not inline `-m`"
  rule — that part still holds, but the *file-writing* step needs the
  base64 pattern on this machine, confirmed twice this session.
- **Diff anything `git status` flags that you didn't expect to have
  changed, before staging it.** Reconfirmed this session — `state.db`
  and `fixture_repo` correctly excluded from the 3a commit because this
  check was actually done, not assumed.
- **Trust the file-reading tool over shell `cat`/`wc`/`diff`** for
  integrity checks.
- **Don't trust a tool's self-reported description of what it did —
  check the actual artifact.** Reconfirmed again this session (see
  Housekeeping item 5).

## Suggested first move

Confirm housekeeping items 1-3 above, then ask Yehor directly: "BACKLOG
3a is closed. Do you want to move straight to 3b (`GITHUB_TOKEN`
permissions — needed before Stage 2 can actually produce a PR), or is
there something else you'd rather prioritize first?" Don't assume 3b is
automatically next just because it's cheap — confirm, the way today's
session confirmed 3a's approach before implementing rather than
defaulting to the easiest reading of the backlog.
