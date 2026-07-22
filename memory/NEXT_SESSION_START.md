# Patchward — Next Session Start Prompt

> **Full rewrite, 2026-07-22 (Session 022 close). Explicitly a deliberate
> rewrite, not a silent one** — this file had grown to 210 lines of nested
> addenda-on-addenda across 4 sessions. `.strategy/STRATEGY.md` already
> carries the complete historical ledger (session log, calibration record,
> heuristics, failed approaches); this file's job is to be a lean,
> current-state pointer for whoever opens the next session, not a second
> history. Nothing below is new information that isn't already in
> `STRATEGY.md` in full detail — this is a compressed, current-only summary.

Resume Patchward. **Open via the `session-strategy-synthesis` skill**,
grounding in `.strategy/STRATEGY.md` — re-verify its claims fresh, do not
trust them as-is. They were verified 2026-07-22 (Session 022 close) and
can go stale between sessions, exactly like every prior session's memory.

## Housekeeping, in order

1. Run `git ls-remote origin main` yourself for Patchward. Last known:
   `5c5a4790f73e9d0f10163ccf0feea8f738da3cae` ("docs(memory): include
   session log in Session 022 close") — confirmed via fresh `git ls-remote`
   AND a fresh `git clone` with byte-diff against authored content, Tier 0.
2. Re-confirm Fly health fresh: `patchward-webhook.fly.dev/healthz`.
3. Re-confirm PyPI fresh: `pypi.org/project/patchward/0.1.0/` — should
   still show the live package with Trusted Publishing confirmed.
4. **One loose end from Session 022, worth closing early if convenient:**
   callmed-landing's exact remote hash (reported as
   `75f1a7b79ed635fa296cec3d890346e1d9860fab`) was never independently
   `git ls-remote`-confirmed from the sandbox — that repo is private and
   the sandbox has no credentials for it. A fresh `WebFetch` of the live
   `callmedai.com` site DID confirm the deployed content is correct (0
   "RepoMend" mentions, right CLI instructions), which is strong evidence
   the push landed, but it isn't the same as a confirmed hash. Ask Yehor
   for a fresh `git ls-remote origin main` paste from his own machine to
   close this precisely — or treat the live-site match as sufficient and
   move on; his call either way, not a guess.
5. Diff every memory file on the D:\ mount against a fresh clone before
   assuming memory starts clean from the last commit — **this is H8, a
   promoted standing heuristic now, not a one-off check.**

## Current state (verified at Session 022 close, re-verify anyway)

- **BACKLOG item 5** (Phase 9 Exposure Gate) — fully closed since Session
  021, reconfirmed again this session. Nothing agent-actionable remains.
- **BACKLOG item 9** (PyPI Trusted Publisher) — fully closed this session.
  `patchward` v0.1.0 is live on PyPI; the OIDC identity chain is proven
  end-to-end (Actions run + PyPI release page, two independent fetches
  agreeing).
- **BACKLOG item 8** (callmed-landing rename) — fully closed this session.
  45 occurrences fixed (not 34 — that was a line-count, not a word-count),
  plus 3 technical corrections (CLI command, branch-naming placeholder,
  PyPI namespace) verified against real source. Confirmed live in
  production via direct fetch of the deployed site.
- **BACKLOG item 16** (NEW, untriaged) — ~59 internal "repomend" references
  remain in the real Patchward codebase across 15 files (`RepomendConfig`
  class in `config.py`/`webhook.py` and others). Not touched, not scoped.
  Needs a usage inventory before it can even be estimated.
- **BACKLOG item 12** (CRA/GDPR) — unchanged, needs qualified legal
  counsel, not agent work.
- **H4 heuristic corrected**: this sandbox has a working Python 3.13
  interpreter (`/usr/bin/python3.13`) that `uv` finds with zero network
  calls — real in-sandbox `pytest` runs are now possible (they weren't
  known to be, before this session). Kept properly tiered: the *working
  interpreter* is Tier 0 (directly observed); *why prior sessions missed
  it* stays Tier 1 (plausible — H4's diagnosis was about fetching a NEW
  interpreter, never checked for an existing one — but genuinely
  unconfirmed; the sandbox's base image could also have simply changed).
- **The 480-vs-483 test-count question is fully resolved, Tier 0**: the
  gap is `tests/fixture_repo`'s 3 tests, missing from sandbox clones
  because that submodule is a bare gitlink with no `.gitmodules` — not a
  version/platform marker, and not a new problem (BACKLOG item 7d already
  tracked this submodule's state). Both Yehor's 483 and the sandbox's 480
  are correct for their respective checkouts.
- **No agent-startable code work is queued.** Next session opens by
  either: (a) Yehor wants item 16 triaged (agent-startable once he says
  go), (b) something entirely new, or (c) just the housekeeping above.

## Standing heuristics worth knowing before this session (see STRATEGY.md for full evidence)
- **H1**: only remote-ref ops (`git ls-remote`), a fresh `git clone`, or
  direct hosted-content fetches are fully trustworthy for git state —
  local mount reads can lie.
- **H2**: never cite a commit hash inside a file that then gets committed
  — always re-run `git ls-remote` fresh at session open instead of
  trusting a cited hash, even one from a prior session's own close-out.
- **H4**: a bash-level network failure doesn't mean the target/technique
  is universally blocked — test the specific host/tool combination
  (and: check for an already-present local interpreter before assuming
  none exists, per this session's correction).
- **H8**: diff every memory file against a fresh clone before assuming
  memory starts clean — local disk can carry real uncommitted content for
  multiple sessions running, invisible to `git log`.
