# Patchward вЂ” Next Session Start Prompt

> Full rewrite, 2026-07-23 (Session 023 close) вЂ” same convention as the
> Session 022 rewrite: `.strategy/STRATEGY.md` carries the complete
> historical ledger (session log, calibration, heuristics, failed
> approaches); this file is a lean, current-only pointer, not a second
> history.

Resume Patchward. **Open via the `session-strategy-synthesis` skill**,
grounding in `.strategy/STRATEGY.md` вЂ” re-verify its claims fresh, do not
trust them as-is, including everything below. They were verified
2026-07-23 (Session 023 close) and can go stale between sessions.

## Housekeeping, in order

1. Run `git ls-remote origin main` yourself. Last known:
   `e4f3cca0684ea04654094e0cb0620664151f1f32` ("docs(memory): close
   BACKLOG 16, log item 17") вЂ” confirmed via fresh `git ls-remote` AND a
   fresh `git clone` with byte-diff against the agent's own authored
   drafts, Tier 0.
2. Re-confirm Fly health fresh: `patchward-webhook.fly.dev/healthz`.
3. Re-confirm PyPI fresh вЂ” the plain `WebFetch` to `pypi.org/project/patchward/`
   may 404 (robots.txt/bot-detection, not a package-removal signal, per
   Session 023's finding); if so, use `pip index versions patchward` from
   sandbox bash instead, which reads the real package index without
   hitting the blocked route.
4. **Diff the D:\ mount's memory files against a fresh clone before trusting
   anything in them вЂ” this is H8, and Session 023 close found a real
   instance of the mirror-image problem (H9-candidate): after Yehor
   committed and pushed Session 023's work, `memory/BACKLOG.md` and
   `.strategy/STRATEGY.md` on his own disk had regressed to their
   pre-session content (most likely an editor autosave clobbering a
   reviewed buffer) even though GitHub had the correct content all along.
   This was found and fixed at close, but check it again fresh вЂ” don't
   assume last session's fix held.**
5. Two small, harmless untracked files were flagged for optional cleanup
   at Session 023 close and may still be sitting in the working tree:
   `BACKLOG16_rename.patch` (redundant вЂ” the rename it documents already
   landed) and `collected_314.txt` (pre-existing, unrelated to any current
   work). Neither blocks anything; delete if convenient.

## Current state (verified at Session 023 close, re-verify anyway)

- **BACKLOG item 5** (Phase 9 Exposure Gate) вЂ” closed since Session 021,
  reconfirmed every session since. Nothing agent-actionable remains.
- **BACKLOG item 8** (callmed-landing rename) вЂ” closed since Session 022,
  reconfirmed live in production a third time this session (0 "RepoMend",
  correct CLI line). Stable across 3 sessions now.
- **BACKLOG item 9** (PyPI Trusted Publisher) вЂ” closed since Session 022.
  `patchward` v0.1.0 live; confirmed again this session via
  `pip index versions patchward` after the direct PyPI page fetch was
  blocked by robots.txt.
- **BACKLOG item 16** (internal `Repomend`-naming debt) вЂ” **CLOSED this
  session (023).** `RepomendConfig` в†’ `PatchwardConfig` across 12 files,
  plus 2 test-function renames and a test-only env var rename. The one
  boundary-crossing reference (`REPOMEND_NETWORK_POLICY`, the scanner
  sandbox's egress-policy env var) was handled with a transitional
  dual-name design (both `PATCHWARD_NETWORK_POLICY` and the legacy name
  are set/read) rather than a straight rename, because the scanner's
  Docker image is digest-pinned and won't pick up an `entrypoint.sh`
  change until deliberately rebuilt. Fail-closed behavior (a name
  mismatch can only make egress *more* restrictive, never open it) was
  verified directly from the iptables logic before this design was chosen.
  Pushed and independently confirmed byte-identical at close.
- **BACKLOG item 17** (NEW, Session 023) вЂ” rebuild `patchward-scanner`,
  re-pin its digest, then drop the legacy env var and rename the image
  tag/binary. Directing-Engineer action, not agent-startable вЂ” a rebuild
  pulls current dependency versions and needs its own before/after
  scan-result check. No urgency; the dual-name design is safe
  indefinitely until this lands.
- **BACKLOG item 12** (CRA/GDPR) вЂ” unchanged, needs qualified legal
  counsel, not agent work.
- **No agent-startable code work is queued.** Item 17 becomes
  agent-startable only once Yehor explicitly decides to trigger the
  rebuild (it's a deliberate, non-urgent action with its own verification
  needs, not something to default into). Otherwise: (a) something entirely
  new, or (b) just the housekeeping above.

## Standing heuristics worth knowing before this session (see STRATEGY.md for full evidence)
- **H1**: only remote-ref ops (`git ls-remote`), a fresh `git clone`, or
  direct hosted-content fetches are fully trustworthy for git state вЂ”
  local mount reads can lie.
- **H2**: never cite a commit hash inside a file that then gets committed
  вЂ” always re-run `git ls-remote` fresh at session open instead of
  trusting a cited hash, even one from a prior session's own close-out.
- **H4**: a bash-level network failure doesn't mean the target/technique
  is universally blocked вЂ” test the specific host/tool combination.
  Session 023 added an instance: the plain PyPI project-page `WebFetch`
  can 404 under robots.txt/bot-detection even though the package is live
  вЂ” `pip index versions <pkg>` is a working alternative route.
- **H7**: re-paste actual evidence rather than asserting "already done" вЂ”
  Session 023 close applied this to the *user's own* claims (a pasted
  commit transcript), not just memory-file content, and it caught a real
  finding (see H9-candidate).
- **H8**: diff every memory file against a fresh clone before assuming
  memory starts clean вЂ” local disk can carry real uncommitted content for
  multiple sessions running, invisible to `git log`.
- **H9-candidate** (1 occurrence, Session 023 close, needs one more before
  promotion): the mirror image of H8 вЂ” local disk can also fall *behind*
  git after a genuine, successful push (an editor autosave on a stale
  buffer is the leading suspect). Lower risk than H8 since nothing real is
  lost, but still worth an explicit mount-vs-HEAD diff after any session
  where Yehor reports committing memory-file changes himself.
