# BACKLOG.md Retrospective — cold storage

Companion file to `memory/BACKLOG.md`, mirroring `.strategy/STRATEGY.md`'s
existing `.strategy/RETROSPECTIVE.md` pattern. Holds verbatim history
archived out of `BACKLOG.md` when an item's full narrative was no longer
needed live, to keep the hot file under control. Nothing here is deleted —
moved, verbatim, byte-for-byte from what `BACKLOG.md` used to contain at
the point of archiving. Consult this file only when a specific item's older
history is directly relevant; routine reads of `BACKLOG.md` should not need
it.

First archived 2026-09-02 (Session 044), backup-first, dual loss-check —
see `.strategy/STRATEGY.md` Session 044's own log entry for the process.
Pre-compression snapshot of the untouched original: `memory/
PRE-COMPRESSION-BACKLOG-2026-09-02.md`, sha256-verified byte-identical to
`memory/BACKLOG.md` before this pass (hash confirmed by Yehor's own
terminal via `Get-FileHash`).

---

## Item 13 — Fix-Gen lacks an explicit "not a real issue, decline" path — CLOSED 2026-07-15

Archived from `memory/BACKLOG.md` item 13, 2026-09-02, Session 044.

## 13. Fix-Gen lacks an explicit "not a real issue, decline" path (CLOSED 2026-07-15)
**WSJF: low-medium — real gap, not urgent.** Stage 2 showed Fix-Gen
correctly avoiding bad fixes on 4 by-design findings, but the *mechanism*
was running out of `max_turns` without calling `submit_fix`, not an
explicit "I assessed this and it's not a real issue" decision.
Functionally safe (no bad fix shipped either way) but wastes the full
turn budget on every by-design finding and produces an ambiguous
`[SKIP]` reason ("max_turns reached") indistinguishable from Fix-Gen
genuinely struggling vs. correctly declining.

**Selected via `/session-strategy-synthesis`, 2026-07-15** — of the three
unscheduled options open at session start (this item, Mirror Pass Tier 2
/ item 10, or a no-op), item 10 was ruled out on its own WSJF terms: grep
across every memory file and `src/` found zero design spec anywhere
beyond its one-line BACKLOG/BUILD_PLAN entry (`Job Size: Large`,
`WSJF: lowest for now`) — its real first step would be a scoping
conversation with Yehor, not code, so it couldn't produce a testable
session outcome today. This item was concrete, scoped, and already had a
named mechanism and a named file, so it was chosen without re-asking.

**Implemented:** new `decline_fix` tool in Fix-Gen's schema (`fix_gen.py`)
— requires `reason` + `confidence`, and the system prompt now instructs
the model to call it (after at least one `read_file`) when a finding is
by-design/false-positive, instead of exhausting `max_turns` silently.
`FixResult` gained `declined: bool` and `decline_reason: str`.
`pipeline.py`'s batch status is now `"declined"` (not the generic
`"fix_failed"`) when `fix_result.declined` is true. `cli.py` prints
`[DECLINED] <reason>` instead of the ambiguous `[SKIP] ...max_turns
reached`, and logs `declined`/`decline_reason` in the run log record.

**Real bug caught and fixed during this same pass, not a separate
follow-up:** the first test run (448 total collected, 2 failed) hit the
*exact same failure class* this codebase already documented once
(2026-07-08, `project_open_tasks.md #25`, preserved verbatim in
`_make_fix_result()`'s own comment in `test_orchestrator.py`): an unset
`MagicMock` attribute auto-vivifies as a truthy, non-JSON-serializable
object. Two test mocks predating the new `declined`/`decline_reason`
fields — `_make_fix_result()` and one inline `MagicMock()` in
`TestRunLogThreaded.test_run_log_record_on_fix_failure` — hit it again.
Production was never affected (the real `FixResult` dataclass always
defaults `declined=False` correctly); only the test mocks needed the new
fields set explicitly. Fixed both. **Worth carrying forward as a
standing heuristic, now proven twice in the same codebase:** any new
field added to `FixResult` (or any dataclass mocked via a bare
`MagicMock()` in this test suite, not `spec=`'d) must be added explicitly
to every existing untyped mock construction site, not assumed safe by
default — grep for the class's mock-builder helpers and any inline
`MagicMock()` construction before considering a dataclass field addition
complete.

**Verified:** Yehor ran the real suite twice on his own machine (`.venv`,
Windows) — first run: 2 failed (the mock gap above), 446 passed; second
run after the fix: **448 passed, 2 skipped, 15 deselected, 90.46%
coverage** (up from 441/90.31% pre-session — the 7 new tests across
`test_fix_gen.py` and `test_async_pipeline.py` fully account for the
delta). Commits: `docs: correct stale SHA/lock claims in
NEXT_SESSION_START.md`, then `feat(fix-gen): add explicit decline_fix
tool path (BACKLOG 13)`.

**Not done, flagged rather than silently skipped:** `cli.py`'s new
`[DECLINED]` echo branch has no dedicated unit test — no `tests/test_cli.py`
file exists in this repo at all (checked via `Glob`, confirmed absent),
so there was no existing harness/convention to extend without building
one from scratch. `pipeline.py` and `fix_gen.py`'s decline logic are
both covered (now closed — see BACKLOG 15a). **`.claude/agents/*.md`
naming — CLOSED 2026-07-15, commit `7effbad`.** Widened during Session
016: all three templates (`scanner.md`, `fix-gen.md`, `verifier.md`),
not just `fix-gen.md`, still said "RepoMend"; grep across `src/`
confirmed zero runtime references to any of them (they're not the live
prompt — the real one is `_FIX_GEN_SYSTEM_PROMPT`, embedded directly in
`fix_gen.py`). The `Edit`/`Write` tools refused all three as a protected
path, so content was generated, base64-encoded, and handed to Yehor as
three `WriteAllText` PowerShell commands to run himself — verified via
the `Read` tool (not blocked) before handoff. All three now say
"Patchward"; `fix-gen.md`'s branch-naming line and its fictional
"ESCALATE signal" description now correctly describe the real
`decline_fix` mechanism (BACKLOG 13) and the real `patchward/fix-<id>`
branch prefix. **Not decided, deliberately left to Yehor:** whether these
three unreferenced files are worth keeping at all, versus deleting
outright — correcting content was the safe, reversible move; deletion is
a call only he should make.

---

## Item 14 — Stray pre-rename branches on `ssh-audit` — RESOLVED 2026-07-15

Archived from `memory/BACKLOG.md` item 14, 2026-09-02, Session 044.

## 14. Stray pre-rename branches on `ssh-audit` — RESOLVED 2026-07-15 (Session 018, cross-project research), origin confirmed
**Origin fully confirmed, not "Yehor-only" anymore.** Cross-referenced
against `Autonomous-Core/memory/symbiote-recurring-income-research-and-
buildplan.md` §1.5: on **2026-06-29**, two RepoMend PRs were opened
against **`jtesta/ssh-audit`** (the real upstream, 4.2k stars/221
forks — not Yehor's fork) — **#359** (bare `except` clause, Bandit
B110) and **#360** (`random.randint`→`secrets.randbelow`, Bandit B311).
The stray branches `repomend/fix-bandit.B110-1fdaef` and
`repomend/fix-bandit.B311-6323af` on Yehor's fork are the local source
branches for those two PRs. **Both PRs were closed by the upstream
owner on 2026-07-03** with review comments reading, in full: *"This is
AI slop."* and *"More AI slop."* — then tagged with a project-level "AI
slop" label. No technical engagement with the actual diffs; the fixes
themselves were narrow and correct. This incident is the single piece
of evidence that most directly drove Autonomous-Core's Patchward
Marketplace pivot recommendation (self-serve GitHub App, not unsolicited
open-source outreach — see `docs/architecture/patchward-marketplace-
buildplan.md` §1).

**Reconciled against Stage 2 (item 11):** Session 014's later reuse of
"ssh-audit" as a Stage 2 target was a separate, independently-reasoned
decision (Yehor's own fork specifically, chosen to avoid external-consent
complexity) made without cross-referencing this incident — but it
happens to be compatible with it: both agree the real upstream
`jtesta/ssh-audit` should never be targeted again. Current
`patchward.toml` confirmed (`[github].owner = "yehorcallmedai-maker"`)
to target only the fork, not upstream — no live conflict.

**Notable data point, not just housekeeping:** the `B311` branch shows a
real fix was produced historically for the exact finding Stage 2's own
2026-07-14 run declined (Fix-Gen exhausted `max_turns` without
`submit_fix` — see item 13). Not asserted as a regression — could be a
prompt/model change, version difference, or non-determinism — but
evidence Fix-Gen *can* produce a fix for this exact finding, so
"declined" isn't necessarily "unfixable."

**Recommended, not decided:** the two stale branches on Yehor's fork are
now dead weight from rejected PRs — safe to delete, or safe to leave as
a historical record. Genuinely low-stakes either way; still Yehor's
call, but now a fully-informed one rather than an open mystery.

---

## Item 16 — Internal `Repomend`-naming debt — TRIAGED AND EXECUTED 2026-07-23

Archived from `memory/BACKLOG.md` item 16, 2026-09-02, Session 044.
**Status correction, not silently fixed:** this item's own header said
"staged uncommitted for Yehor's review" — stale. `.strategy/STRATEGY.md`'s
own Session 023 CLOSE entry records this work as executed AND pushed,
commit `e4f3cca0684ea04654094e0cb0620664151f1f32` ("docs(memory): close
BACKLOG 16, log item 17"). Treated as CLOSED for archiving purposes, per
that cross-reference — not re-verified against current source this pass,
since that would exceed a compression pass's scope.

## 16. Internal `Repomend`-naming debt in the real Patchward codebase — TRIAGED AND EXECUTED 2026-07-23 (Session 023), staged uncommitted for Yehor's review
Surfaced 2026-07-22 (Session 022) as a side effect of closing item 8. This
session (023) did the full triage the prior entry called for, then executed
the safe part of the rename. **Triage (independently re-verified against a
fresh clone, not just trusted from this file):** of the original 59
occurrences / 15 files (`src/`, `tests/`), a full literal-quoted-string grep
(not just the identifier grep) found exactly ONE occurrence that crosses a
process/serialization boundary — `REPOMEND_NETWORK_POLICY`, an env var set by
`docker_sandbox.py` and read by `docker/entrypoint.sh` (itself outside the
original 15-file scope, since that grep was `src/`+`tests/`-only). The other
58 are pure Python identifiers (the `RepomendConfig` class name, its
imports, type hints, and docstrings) with no `__all__` export, no
`README`/`docs` exposure beyond one internal design doc, and no top-level
`from patchward import RepomendConfig` pattern anywhere — confirmed
non-breaking. A second env var, `REPOMEND_FIXTURE_REPO` (test-only, read via
`os.environ.get` with a hardcoded fallback default, not referenced in any CI
workflow or doc), was also found and included.

**Executed this session:**
- `RepomendConfig` → `PatchwardConfig` across all 12 files (6 `src/`, 6
  `tests/`) — find-usages based, not a blind string swap; verified via
  fresh grep that zero case-insensitive "repomend" references remain in any
  of those 12 files.
- `test_repomend_toml_example_exists` → `test_patchward_toml_example_exists`
  (`tests/test_distribution.py`) and `test_repomend_config_has_verifier` →
  `test_patchward_config_has_verifier` (`tests/test_orchestrator.py`) — pure
  internal test-function-name renames.
- `REPOMEND_FIXTURE_REPO` → `PATCHWARD_FIXTURE_REPO` in `tests/test_golden_dataset.py`
  and `tests/test_fix_gen.py`. **Flag for Yehor:** if you have this env var
  set anywhere in your own shell profile/CI (not found in this repo's CI
  configs or docs, but that doesn't rule out a personal setup), it needs
  updating there too — otherwise those two test files just silently fall
  back to their hardcoded default path, not a hard failure.
- `REPOMEND_NETWORK_POLICY` (the security-relevant one, controls the
  scanner sandbox's egress policy — BUILD_PLAN §2's line-by-line review
  class): kept BOTH names live, transitionally, rather than a straight
  rename. Traced two things directly from source before deciding this: (1)
  `docker/entrypoint.sh` applies `iptables -P OUTPUT DROP` unconditionally
  and only adds ACCEPT rules on an exact `PYPI_ONLY`/`NPM_ONLY` string
  match — confirmed **fail-closed**, a name mismatch degrades to
  more-restrictive, never opens egress. (2) `docker_sandbox.py`'s
  `BASE_IMAGE` is a digest-pinned, manually-built local image
  (`patchward-scanner:0.1.0@sha256:...`, built 2026-06-12, comment says
  "update after deliberate image rebuild only") — so editing
  `docker/entrypoint.sh` in the repo does **not** reach that already-built
  image until a deliberate rebuild; skew during that window is real, just
  safe-direction. Given that, `docker_sandbox.py` now sets both
  `PATCHWARD_NETWORK_POLICY` (canonical) and `REPOMEND_NETWORK_POLICY`
  (legacy) to the same value; `entrypoint.sh` reads the new name with a
  fallback to the old one, iptables logic itself untouched;
  `docker/scanner.Dockerfile`'s comments updated to mention both names.
  `tests/test_docker_sandbox.py` updated to assert both env vars are
  present (3 tests) plus docstring/comment updates (4 more lines) — same
  480/2/15 pass count as baseline, nothing broken.
- Deliberately **NOT** touched this pass: the Docker image tag name
  (`repomend-scanner:0.1.0` in `docker/scanner.Dockerfile`'s build
  instructions) and the installed entrypoint binary name
  (`/usr/local/bin/repomend-entrypoint`) — both only take effect on a
  future deliberate image rebuild anyway, so bundling their rename with
  that rebuild (not with this internal-identifier pass) avoids mixing a
  naming cleanup with an image-rebuild decision. See new item 17.
- Also deliberately not touched: `.bandit` and `.env.example` comment-level
  "RepoMend"/"repomend-fixture" mentions — the former is old-product-name
  branding (same category as item 8, but internal comments, not user-facing
  product copy — low priority, optional, not scoped into item 16), the
  latter (`repomend-fixture`) is the *actual name* of Yehor's real external
  GitHub fork used for E2E testing (see item 11/14) — renaming the string
  in a comment would misdocument a real external repo, not clean anything
  up. Left alone on purpose, not missed.

**Verification:** full `uv run --python 3.13 --extra webhook pytest --cov`
in the sandbox after all edits → `480 passed, 2 skipped, 15 deselected,
90.60% coverage` — identical pass/skip/deselect counts to this session's
own pre-edit baseline (see `.strategy/STRATEGY.md` Session 023 open entry),
confirming the rename broke nothing. Diff: 17 files changed, 97
insertions, 59 deletions — delivered to Yehor as a patch file plus the
full corrected files, written **uncommitted** to the D:\ working tree for
his own line-by-line review and commit, per standing process (items 8/9's
same pattern). No git commits made from the sandbox.
**Owner:** Yehor, for the `git diff` review + commit only; the actual
content work is done for the non-deferred scope.

---

## Item 19 — `GITHUB_TOKEN` disk/log exposure — CLOSED 2026-07-27 (Session 025)

Archived from `memory/BACKLOG.md` item 19, 2026-09-02, Session 044.

## 19. `GITHUB_TOKEN` reaches disk (webhook path) and unfiltered logs (both paths) — NEW, surfaced 2026-07-24, Session 024, during security.html copy verification
**Origin:** Yehor asked for a bounded, read-only trace of `_build_remote_url()`'s
output before publishing a security.html sentence describing it. The sentence
itself checked out; the trace surfaced a real, separate code gap.

**Confirmed, not persisted via `git remote add`/`set-url` anywhere in the
codebase** (grepped `worktree_common.py`, `pr_publisher.py`,
`github_app_auth.py`, `webhook.py` — zero matches). The token-bearing URL is
used two ways:
1. `worktree_common.py:295` — `["git", "push", "--force", remote_url, ...]`,
   passed inline as an argv element to `git push`. Ephemeral, argv-only,
   never touches `.git/config`. This is the CLI/worktree path (Yehor's own
   machine) — clean.
2. `webhook.py:278` — `["git", "clone", "--depth", "1", clone_url, ...]`.
   Git's own default behavior writes the clone source URL — including the
   embedded `x-access-token:<token>@github.com` — into the freshly cloned
   repo's `.git/config` as the `origin` remote. Nothing in `webhook.py`
   rewrites or strips it afterward. `tmp_dir` (and therefore that
   `.git/config`) is only removed in the outer `finally: shutil.rmtree(...)`
   — i.e. the token sits in plaintext on the Fly.io host's disk for the
   full duration of the scan → fix-gen → verify → publish run, not just the
   clone step. Cleanup does run on both success and exception paths
   (Python `finally`), so this is not a permanent leak, but it is a real,
   avoidable exposure window on the hosted path specifically — the CLI path
   has no equivalent because the user already owns the local clone.

**Also confirmed: no scrubbing on two log paths, either.** `scrub()` is
never called on git subprocess output.
- `webhook.py:283` — `logger.error("[webhook] clone failed for %s: %s",
  repo_full_name, proc.stderr)` logs raw `git clone` stderr verbatim. Git is
  well known to echo the full remote URL (credentials included) in several
  of its own failure modes (e.g. `fatal: unable to access '<url>'`,
  auth/connection errors) — whether it does so for this exact failure case
  was not empirically tested this session, but the code applies zero
  filtering regardless of what git prints.
- `worktree_common.py:294-308`'s `git_push_branch()` raises
  `RuntimeError(f"...stdout: {proc.stdout!r}\nstderr: {proc.stderr!r}")` on
  a failed push — same unfiltered pattern. This propagates to two more
  unfiltered sinks: `cli.py:544-548`'s `except Exception as pr_exc:
  typer.echo(f"  [PR] Publish failed: {pr_exc}", err=True)` (CLI stderr),
  and, on the webhook path, `pipeline.py:266-274`'s `err_str = str(exc) or
  repr(exc)` → `result["error"] = err_str` + `logger.error("[pipeline]
  error for %s: %s", repo_label, err_str)`, and that same `result` dict is
  then logged again in full by `webhook.py:311`'s
  `logger.info("[webhook] scan finished for %s: %s", repo_full_name,
  result)`. **The run log itself (NDJSON, `run_log.py`) is not affected** —
  `pipeline.py`'s `run_log.append_batch_result()` only ever writes the
  `finding_status` string, never `err_str`, so this is specifically an
  application-log (Fly.io `logger.*`) and CLI-stderr exposure, not a
  run-log-artifact exposure.

**Not acted on, deliberately — this is a code fix, not a copy question.**
The security.html sentence this trace was checking ("embedded in the HTTPS
remote URL passed as a command argument") remains accurate as written and
was not changed further; it describes the delivery mechanism honestly
without claiming a safety property this finding would contradict. This item
tracks the actual gap for a future code fix: (a) strip credentials from the
webhook path's cloned `.git/config` immediately after clone (or avoid
embedding the token in the clone URL at all, e.g. via a short-lived
credential helper), and (b) route git subprocess `stdout`/`stderr` through
`CredentialProxy.scrub()` (or an equivalent token-aware redaction) before
any of the four log/echo sites above.
**Owner:** unassigned — **SUPERSEDED, see `STATUS: CLOSED` below ↓** — not urgent enough to block tonight's site-copy
commit (the sentence is accurate), but real, and on the hosted path, not
just theoretical. Yehor's call on priority/timing.

---

**STATUS: CLOSED 2026-07-27 (Session 025).** Fix committed, pushed, deployed,
and `/healthz`-confirmed on the new image. Verification chain, each step
independent of the last:
- Base fix committed+pushed as `37b3bfd`; five-finding follow-up committed+
  pushed as `dee84e1`. Both verified via fresh `git ls-remote` + a fresh
  `git clone` byte-compared against the authored trees (zero drift).
- Deployed to Fly image `sha256:ac54d18a802e4db6d35d6574ad1188b90797630ca3cceb39c507490b06d6a8e3`
  on machine `7841600fd5e7e8`, built from the `dee84e1` working tree
  (`fly image show` digest matches the build manifest).
- `/healthz` → `200 {"status":"ok"}` confirmed by TWO methods: WebFetch AND
  a real Chrome browser read (Claude-in-Chrome), per this project's own
  H10-candidate (WebFetch alone is not trusted for a closing gate). The
  deploy emitted a transient "not listening on 0.0.0.0:8000" warning during
  the rolling restart; the green `/healthz` on the new image proves the app
  bound and the warning did not persist.

**What the remediation actually covered.** This trace named two surfaces
(.git/config persistence + unfiltered logs). Adversarial review of the fix
surfaced three more, all closed:
- (this trace) `.git/config` token persistence on the webhook clone →
  closed: tokenless clone URL + inline env-reading credential helper; the
  token never enters the URL, so git has nothing to persist.
- (this trace) unfiltered git stderr/exception text at four log/echo sites →
  closed: `scrub_text()` (pattern + register-at-mint layers) at all four.
- (review #1) token in argv / `/proc/<pid>/cmdline` → closed: credential
  travels via the subprocess environment + helper, never argv; empirically
  confirmed token-free via a live `/proc` poll on Linux and a real
  authenticated clone on Windows.
- (review #1) `subprocess.TimeoutExpired` captures stdout/stderr AND argv on
  the exception object → closed: handler scrubs `exc.stdout`/`exc.stderr`/
  `exc.cmd` at source before re-raising argv-free.
- (review #1) cross-thread race: `scrub_text()` iterating the live
  `_RUNTIME_CREDENTIALS` set while another thread registered could raise
  `Set changed size during iteration` FROM INSIDE the `except` block,
  surfacing the original UNSCRUBBED exception via `__context__` — a scrubber
  that leaks the token it exists to redact, reachable only under the hosted
  webhook's real threading model. Closed: `for val in tuple(...)` GIL-atomic
  snapshot. **This fix is review-verified / correct-by-construction, NOT
  test-proven** — the race is not deterministically reproducible through the
  public API, so the accompanying `test_scrub_text_concurrent_smoke` is an
  honestly-labeled non-discriminating smoke test, not a red-on-revert proof.
- (review #1) token regex leading `\b` defeated by a preceding word char
  (e.g. percent-encoded `%3Aghs_...`) → closed: de-anchored; negative-control
  test confirms the `{16,255}` floor still protects legitimate prose.
- (review #3) `#3` the credential-helper reset was inside `if token:`, so the
  tokenless webhook push borrowed ambient host credentials and issued
  `erase` against them → closed: `credential_reset_args()` on every path,
  fails loud with no credential.

**Adversarial review: three passes, NOT "clean."** Pass 1 found the five
findings above (plus items later split to 21/22/23). Pass 2 found two
non-blocking issues in the fix itself (F1: `exc.cmd` unscrubbed + an
over-claiming docstring; F2: a non-discriminating test) — both fixed. Pass 3
(re-attack on the final tree) returned **0 leaks / 0 blockers**, and found
**three robustness items** — logged as BACKLOG 22 (Gate 3 unsandboxed
credential inheritance — the single largest pre-launch exposure, see item 22),
23 (remaining unscrubbed error sinks), 24 (unbounded `_RUNTIME_CREDENTIALS`
growth). The empty-of-leaks final pass was the convergence signal to ship;
the three robustness spin-offs are honestly recorded, not swept into "clean."

**Suite at close:** 505 passed / 3 skipped / 15 deselected, coverage 90.62%,
Python 3.14.4 (Yehor's machine); reproduced 503/2/15 in-sandbox.

**Spun off, still open:** 21 (dead `github_token` param — webhook may not push
a PR at all), 22 (Gate 3 credential inheritance — NEXT security priority), 23,
24. BACKLOG 19's credential-DELIVERY boundary is closed; item 22 is the
credential-INHERITANCE boundary the same review found adjacent to it.

**Owner:** CLOSED — no further action on item 19 itself.

---

## Item 20 — `callmed-landing` "stale copy" scare — CLOSED same day, FALSE ALARM

Archived from `memory/BACKLOG.md` item 20, 2026-09-02, Session 044.

## 20. `callmed-landing`'s corrected copy appeared not to be live at the plain URLs — CLOSED same day, FALSE ALARM (surfaced 2026-07-24 close, resolved 2026-07-24, same session)
**WSJF: highest — this is the actual state of the item this whole session
treated as its top priority.** Session 024's close-out claimed the
data-flow corrections were "confirmed live in production," based on one
fetch of `callmedai.com/privacy` (which happened to be current) and one
fetch of `callmedai.com` for an unrelated check (RepoMend absence only —
never checked for the actual false-claim strings). A second, more
thorough double-check found this was wrong as a general claim:

- `https://callmedai.com/` (bare root, no extension) — still serves the
  OLD copy. Confirmed twice, independently, several minutes apart (ruling
  out this tool's own 15-minute fetch cache as the explanation): "your
  code never leaves your infrastructure" and "fully auditable on-premise"
  are both still present.
- `https://callmedai.com/security` (bare, no extension) — serves an even
  older stub, dated May 2026 (predates even the June 2026 v1.1 revision,
  let alone tonight's July 2026 v1.2).
- `https://callmedai.com/index.html` and `https://callmedai.com/security.html`
  (explicit `.html` extension) — both serve the fully current, corrected
  copy. A cache-busting query string on the bare URLs also returns current
  content.

**Working diagnosis, not confirmed from this sandbox (no header/DNS access
— `curl`/`dig` to arbitrary hosts blocked here, consistent with H4):** a
CDN/edge cache is serving a stale cached response for the exact clean
URLs (`/`, `/security`) while `.html`-suffixed and cache-busted requests
bypass that cache key and reach current origin content. This is Yehor's
to diagnose and fix — likely a dashboard cache-purge or a fresh deploy
trigger on whichever platform serves the site (Vercel/Netlify/Cloudflare —
not yet identified from this sandbox).

**Why this matters more than anything else on this list:** the homepage
and the security page's clean URL are exactly what a real visitor types
or clicks — not the `.html` form. The false "code never leaves your
infrastructure" / "fully auditable" claims that this entire session's
urgent-priority site fix was meant to remove are, right now, still being
shown to anyone who visits the plain URLs.

**RESOLVED, same session, false alarm — root cause was this session's own
tooling, not production.** Yehor's own diagnostics (real `curl.exe -sIL`
from his machine) showed `cf-cache-status: DYNAMIC` on both `/` and
`/index.html` — Cloudflare is NOT caching these responses at all, passing
every request straight to origin — which already contradicted the CDN-
cache hypothesis above. Yehor's own Cloudflare Pages dashboard screenshot
then showed the `callmed-landing` project's latest deployment (21 minutes
old at the time, matching commit `68e612a`'s message exactly) already live
in production. **Final, decisive check: a real Chrome browser (via
Claude-in-Chrome), navigated fresh to both `callmedai.com/` and
`callmedai.com/security` and read the actual rendered page content —** the
homepage shows the corrected "default-deny iptables" / two-stage Anthropic
language; `/security` shows "Last updated: July 2026 · Version 1.2" with
every corrected section present (`Credential isolation — Patchward`,
`Three-gate verifier — Patchward`, `Transport security`, `Supply chain`,
all current). **The site was never stale. The "stale" finding was an
artifact of this session's own `WebFetch` tool** — which fetches a page
and summarizes it through a small, fast model rather than returning raw
bytes — reporting "not found" for strings that were, per the real browser,
actually present. Root cause of the tool's error not fully determined
(possibly its own internal cache, possibly the summarization step
under/over-reporting on a long page) — not chased further since the
underlying question (is the site correct?) is now answered definitively.
See new heuristic candidate in `.strategy/STRATEGY.md`.
**Owner:** none — closed. No action needed from Yehor.

---

## Item 25 — `_CREDENTIAL_KEYS` missing four GitHub App credentials — CLOSED 2026-07-29 (Session 027)

Archived from `memory/BACKLOG.md` item 25, 2026-09-02, Session 044.

## 25. `_CREDENTIAL_KEYS` omits four credentials that ARE in `os.environ` on the hosted path (NEW, surfaced 2026-07-28, Session 026, BACKLOG 22 scope pass)

**STATUS: CLOSED 2026-07-29 (Session 027)** — shipped as commit `f02ad21`, pushed
to `origin/main`, verified on the remote by fresh clone. Full suite 519 passed /
90.62% on Yehor's machine; `credential_proxy.py` at 100%. All four GitHub App
credentials are now in `_CREDENTIAL_KEYS` (excluded from `get_container_env()`
and scrubbed). Follow-up flagged, not blocking: `GITHUB_APP_ID` (7-char,
non-secret) is now also scrubbed — a documented, conservative over-redaction.
Original entry preserved below. ↓

**Status:** OPEN — pre-launch security item, agent-startable, and the sequencing
note matters: it gates BOTH Option A and Option B of item 22, so it should ship
STANDALONE and FIRST, independent of which way the Gate 3 decision goes.

**The finding (source-verified at `8931702`):** `_CREDENTIAL_KEYS`
(`credential_proxy.py:39-45`) covers only `ANTHROPIC_API_KEY`,
`LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `GITHUB_TOKEN`. Four further
credentials are read from `os.environ` and are covered by nothing:

| Variable | Read at | Set on Fly |
|---|---|---|
| `GITHUB_APP_PRIVATE_KEY_B64` | `github_app_auth.py:50` | `fly.toml:14` |
| `GITHUB_APP_PRIVATE_KEY` (raw PEM alternative) | `github_app_auth.py:47` | alternative to the above |
| `GITHUB_APP_ID` | `github_app_auth.py:75` | `fly.toml:13` |
| `GITHUB_WEBHOOK_SECRET` | `webhook.py:238` | `fly.toml:13` |

**Blast radius — worse than anything item 19 or item 22 records.** The App
private key plus the App ID mints installation access tokens for EVERY
installation of the GitHub App, not just the repo under scan. That is a
cross-tenant credential in plain `os.environ`, inherited directly by Gate 3's
adversarial child (item 22), with no race required. `GITHUB_WEBHOOK_SECRET`
separately allows an attacker to forge signed webhook deliveries.

**Why it gates both 22 options:** `_build_docker_cmd`'s structural exclusion
(`docker_sandbox.py:174-178`) and `get_container_env()`
(`credential_proxy.py:190-197`) both filter on `_CREDENTIAL_KEYS` and nothing
else. Option A would forward the App private key straight into the container;
Option B would strip the Anthropic key and leave the App private key behind.
Neither option closes the exposure until this list is widened.

**Proposed fix:** add the four names to `_CREDENTIAL_KEYS`. Check first whether
any legitimate consumer requires them downstream of a filtered env (the App
auth path reads `os.environ` directly, so most likely not). Note `GITHUB_APP_ID`
is not secret on its own but is useless to withhold separately.

**LIVE CONFIRMATION [2026-07-28, Session 026 close]:** read from the running
container's own `os.environ` (names + lengths only, no values printed) —
`GITHUB_APP_PRIVATE_KEY_B64` SET (len 2236), `GITHUB_APP_ID` SET (len 7),
`GITHUB_WEBHOOK_SECRET` SET (len 36), `ANTHROPIC_API_KEY` SET. All four are
present in the parent environment Gate 3's child would inherit. Confirmed
ABSENT, as predicted: `PATCHWARD_GIT_TOKEN` (BACKLOG 19's copy-not-mutate fix
holds on the live host — `credential_env()` never mutates `os.environ`),
`GITHUB_TOKEN` (item 21's root cause), and both Langfuse keys. The enumeration
in this item is therefore live-confirmed, not merely source-traced.

**Owner:** agent-startable.

---

## Item 27 — Hosted `ANTHROPIC_API_KEY` was not an Anthropic key — CLOSED 2026-07-29 (Session 027)

Archived from `memory/BACKLOG.md` item 27, 2026-09-02, Session 044.

## 27. Hosted `ANTHROPIC_API_KEY` is not an Anthropic key — Fix-Gen 401s before Gate 3 is ever reached (surfaced 2026-07-28, Session 026 close, live container read; TWO values rejected the same evening — a 9-char stub, then a 110-char credential from a different service)

**STATUS: CLOSED 2026-07-29 (Session 027)** — Yehor re-set the secret with a real
Anthropic key (a 4th value; the prior three all 401'd — a 9-char stub, a 110-char
foreign credential, and a third rejected on 2026-07-29, `req_011CdWa5on6JfoSxS2MGxP3h`).
The new key was validated LOCALLY before deploy (`models.list()` → OK), then set
via `fly secrets set`, rolling-updated on machine `7841600fd5e7e8`, and
re-confirmed on the RUNNING image: `python -c "...models.list(); print('ANTHROPIC
KEY OK')"` → `ANTHROPIC KEY OK`. Fix-Gen can now authenticate on the hosted path.
**STILL TRACKED BUT RESOLVED 2026-08-07 (Session 031):** the unidentified
110-char credential was exhaustively searched for (git history, local
`.env`, both PowerShell history profiles, all sibling project folders,
`.fly`/`.config`, Windows Credential Manager target names, and a live
`fly ssh` read of all 4 production secrets) and found nowhere. It never
reached git, is not in the current `.env` or any of Fly's 4 secrets
(confirmed by length: 108 / 7 / 2236 / 36 chars, none 110), and does not
appear duplicated anywhere else reachable from this machine. Most likely
origin: a clipboard or password-manager-only paste, never written to
disk. No further agent-startable action remains -- see
`credential_identification_2026-08-07.md`. Rotate at source only if the
service is ever recognized by inspection. Original entry preserved
below. ↓

**Status:** OPEN — **CONFIRMED Tier 0**, functional launch blocker, UPSTREAM of
both of item 21's defects. Belongs to the same investigation unit as 21.
The fix is a Fly secret re-set (Yehor only), not a code change.

**The finding:** a credential-presence read inside the running container
(`fly ssh console -a patchward-webhook`, machine `7841600fd5e7e8`) reported
`ANTHROPIC_API_KEY  SET  len=9`. No value was printed or observed. A valid
Anthropic API key is ~100+ characters and begins `sk-ant-api03-`; nine
characters cannot be one.

**CONFIRMED BY LIVE API CALL [2026-07-28, same session]:** inside the running
container, `python -c "import anthropic; anthropic.Anthropic().models.list()"`
→ `anthropic.AuthenticationError: Error code: 401 - {'type': 'error', 'error':
{'type': 'authentication_error', 'message': 'invalid x-api-key'}, 'request_id':
'req_011CdUpKqhwSQoJufxCitjcZ'}`. Both links are now Tier 0: the length
(measured in the process) and the invalidity (rejected by Anthropic's own API
from the deployment itself). No inference remains in this item.

**Therefore, established as fact:** the hosted webhook cannot call the Anthropic
API at all. Fix-Gen fails on its FIRST request, every run, for every repo. This
is the earliest failure on the hosted path — earlier than the dead
`github_token` param and earlier than Gate 3's pytest FAIL, both of which sit
downstream of a Fix-Gen result that never arrives.

**Why it outranks the other two defects on this path:** `webhook.py:318` guards
only on falsiness (`if not ANTHROPIC_API_KEY: logger.error(...)`), and a 9-char
string is truthy, so the guard passes. The pipeline then constructs
`FixGenSubagent(api_key=...)` and the first Anthropic call fails
authentication. Fix-Gen never produces a fix → verify is never reached → Gate 3
never runs → no PR. It fires BEFORE the pytest defect, which means the hosted
path has been non-functional at an even earlier stage than item 21 supposed.

**FIX ATTEMPT 1 — DELIVERED BUT DID NOT FIX [2026-07-28, same evening]:** Yehor
ran `flyctl secrets set ANTHROPIC_API_KEY=…`; the rolling update reported
`Machine 7841600fd5e7e8 [app] update succeeded` and `/healthz` returned
`{"status":"ok"}` on the restarted machine. The new value DID reach the process
— an in-process read returned `length: 110`, so delivery is not the problem —
but `models.list()` still returned `401 invalid x-api-key`, with a NEW request
id (`req_011CdUqmbwJFzk9S97aPP1eP`, distinct from the original
`req_011CdUpKqhwSQoJufxCitjcZ`), proving a fresh call rather than a cached
result.

**Diagnosis — the secret does not contain an Anthropic key at all.** Checks run
in-process, printing only booleans and lengths, never any part of the value:
- Contamination RULED OUT: raw length == stripped length (110), no leading or
  trailing whitespace, no whitespace anywhere, no quote at either end, no
  non-ASCII. The PowerShell-quoting hypothesis is refuted.
- Prefix sweep against ten credential families — Anthropic (`sk-ant-`), OpenAI
  project/legacy, GitHub PAT/classic/app, Langfuse public/secret, Fly, Slack —
  **all False**, including `sk-ant-`. Every Anthropic key begins `sk-ant-api…`
  or `sk-ant-admin…`; this does not.
- Shape: 110 chars, 0 dots (not a JWT), not all-hex, not base64url-only,
  contains both `-` and `_` plus at least one character outside that alphabet.

**Conclusion:** a well-formed credential belonging to some OTHER system was
placed in this secret. The 401 is not Anthropic rejecting an Anthropic key; it
is Anthropic being handed a credential that was never theirs.

**Identification deliberately NOT pursued further.** Each additional probe
leaks more shape about a live credential while yielding less, and identifying
it belongs to Yehor's own records, not to character-by-character narrowing from
a session. Logged as a boundary held on purpose, not an unfinished check.

**SECURITY CONSEQUENCE, independent of the Anthropic fix:** whatever that
credential is, it has been sitting in a production environment variable and is
therefore exposed on the Gate 3 inheritance path (items 22 and 25). It should
be treated as compromised-by-exposure and ROTATED AT ITS SOURCE. This also
widens item 25's blast radius to include a credential neither party can name —
worth stating plainly rather than filing as an Anthropic-key problem.

**Fix (still open, Yehor only):** `flyctl secrets set ANTHROPIC_API_KEY=…` with
a genuine `sk-ant-api03-…` key, then re-run the `models.list()` check. Also
worth tracing where the mystery value came from — if it was pasted from
somewhere, the same paste may have reached another secret.

**Owner:** Yehor — secret re-set, plus rotation of the unidentified credential.
The startup guard is a separate unit: see item 28.

---

## Item 28 — Startup credential-shape guard (falsiness-only validation) — CLOSED 2026-08-08 (Session 032)

Archived from `memory/BACKLOG.md` item 28, 2026-09-02, Session 044.

## 28. `webhook.py:318` validates the Anthropic credential by FALSINESS ONLY — two different broken secrets passed startup in one evening (NEW, surfaced 2026-07-28, Session 026 close)

**STATUS: CLOSED 2026-08-08 (Session 032)** — commit `f653e77`, three
adversarial review rounds, verified on origin by content, real gate
565/3/91.20%. See `SESSION_CLOSE_2026-08-08.md` for full history.
(Known follow-up, not a reopen: `f653e77` shipped `webhook.py` with a
UTF-8 BOM + 29 mojibake em-dashes — cosmetic, comments-only, gate
unaffected — logged as a P0-adjacent encoding fix in the Session 032
close. The two deferred design questions below — absence-fails-boot and
`/healthz` depth — were also never decided.)

Original prepared-patch history preserved below. ↓

**PATCH PREPARED 2026-07-29 (Session 027)** — implemented
and tested in a clean clone (full suite 526 passed / 90.75%; +9 tests). Delivered
as `backlog28_startup_credential_guard.patch` (in repo root). Adds
`_validate_credential_shapes()` wired via a FastAPI `lifespan`, failing the boot
loudly on a present-but-malformed secret (validates `sk-ant-` prefix, numeric
App ID, PEM/base64 key shape; absent → warn only; no value ever logged). Existing
webhook tests use `TestClient` WITHOUT a context manager, so they never trigger
the lifespan → zero regressions. NOT committed as of close: working tree +
`origin` both at `f02ad21`. TWO YEHOR DECISIONS deliberately excluded from the
patch: (a) should ABSENCE of a required credential also fail the boot (I only
fail on present-but-malformed); (b) should `/healthz` assert credential validity.
Original entry preserved below. ↓

**Status:** OPEN — agent-startable, one-line core fix, and it has **two live
occurrences** rather than a hypothetical justification. Split from item 27
deliberately: 27 is a secret to be re-set (Yehor), 28 is code to be changed
(agent) — same §2 discipline that split 21 from 19.

**The finding:** the guard reads, in substance,
`if not os.environ.get("ANTHROPIC_API_KEY"): logger.error(...)`. It rejects
exactly one value — the empty string — which is the one failure mode nobody
actually hits. Everything else passes startup and fails later, at the first
API call, inside a pipeline run, where the failure is attributed to Fix-Gen
rather than to configuration.

**The two occurrences, both observed on the live deployment on 2026-07-28:**
1. A **9-character** value (item 27's original finding). Truthy → passed.
2. A **110-character credential from a different service** (item 27's failed
   fix attempt). Truthy → passed.

Both would have been rejected at startup by a single predicate:

```python
if not key.startswith("sk-ant-"):
    raise RuntimeError("ANTHROPIC_API_KEY is not an Anthropic API key")
```

**Why this matters beyond tidiness:** the hosted webhook has been deployed and
"healthy" — `/healthz` green throughout — while holding an unusable credential.
A liveness probe that does not touch the dependency it needs will report green
over a broken configuration indefinitely. That is precisely how three
independent defects sat undetected on this service (see item 21).

**Proposed scope (keep it small and separately reviewable):**
- Prefix/shape validation at startup for `ANTHROPIC_API_KEY`, failing loudly.
- Consider the same treatment for the other required secrets
  (`GITHUB_APP_ID`, `GITHUB_APP_PRIVATE_KEY_B64`, `GITHUB_WEBHOOK_SECRET`) —
  each currently has the same falsiness-only or absent guard.
- Do NOT log any part of a credential value in the failure message. The
  message names the variable and the expected shape, never the observed value.
- Open question for Yehor, not decided here: should `/healthz` also assert
  credential validity (a startup-time probe result cached, not a per-request
  API call), so a green health check means "can actually work" rather than
  "process is running"? That is a design choice with cost, not an obvious yes.

**Owner:** agent-startable for the guard; the `/healthz` semantics question is
Yehor's.

---

## Item 29 — `pipeline.py` false "pr_opened" status on PR-creation failure — FIXED 2026-08-07 (Session 031)

Archived from `memory/BACKLOG.md` item 29, 2026-09-02, Session 044.

## 29. `pipeline.py` records "pr_opened" even when PR creation fails (status != "opened") — NEW, surfaced 2026-08-05, Session 030, second independent adversarial pass on item 21's fix

**STATUS: FIXED AND DEPLOYED 2026-08-07 (Session 031)** -- landed as commit
`66680c0` (`src/patchward/pipeline.py`, mirrors `cli.py`'s existing
three-way status handling exactly: `pr_opened` / `pr_already_open` /
`pr_failed`, fail-closed on any unrecognised or missing status). 3 new
tests added; 8/8 mutations caught on a scratch copy (zero silent
survivors). Gated on Yehor's real Python 3.14.4: 558 passed / 3 skipped /
91.20%, coverage floor enforced. Pushed to origin, independently
reconfirmed via a fresh clone. Deployed
(`deployment-01KZECVHTM3QQ62Q32YBBXRA8F`) and live-verified by a direct
`fly ssh` grep against the running container's own source -- matches the
committed diff exactly, line for line. Full diff and mutation log:
`backlog29_implementation_2026-08-07.md`.

Original finding preserved below for record. ↓
Pre-existing bug that item 21 makes reachable, not a defect item 21
introduced. Two independent adversarial passes agreed item 21's own diff
(credential threading into `_push_token()`/`_github_headers()`) is CLEAN;
this is a separate concern discovered in the same pass, kept separate per
the same §2 keep-security-diffs-clean discipline that split 21 from 19 and
28 from 27.

**The finding:** `pipeline.py:262-263` reads

```python
finding_pr_url = pr_dict.get("url")
finding_status = "pr_opened"
```

unconditionally, ignoring `pr_dict["status"]` — the value
`PRPublisher.publish()` → `_create_pr()` actually returns. `_create_pr()`
returns `status: "api_error"` (not an exception) on a 403, an unexpected
status, or a failed draft-retry. Pre-item-21 this branch was unreachable
in practice on the hosted path: the push itself failed first (no
credential), so the pipeline never got far enough to call `_create_pr()`
and report a false status.

**Why item 21 makes this consequential rather than merely present:** item
21 fixed the push. If PR creation subsequently fails for ANY reason other
than the auth bug just closed — most plausibly the GitHub App
installation lacking `pull_requests: write` permission — the sequence is
now: push succeeds (force-push, branch lands on the customer's repo) →
`_create_pr()` returns `api_error` → `pipeline.py` ignores that and
records `"pr_opened"` with an empty `pr_url`. Nothing surfaces the
failure anywhere: not the run log, not the returned result dict, not any
log line. A force-pushed `patchward/fix-*` branch sits on the customer's
repository indefinitely with no PR and no error trail.

**Severity note (deliberately flagged above what "Medium" alone implies):**
rank this by consequence, not by code complexity. The failure mode is an
unexplained artifact appearing on a CUSTOMER's infrastructure that
neither the customer nor Patchward's own operator has any signal to
notice — not an internal metric being wrong. Triage accordingly.

**Fix (not written here — scope only):** mirror `cli.py:531-547`'s
existing status handling in `pipeline.py`'s equivalent branch — that path
already distinguishes `pr_data["status"]` correctly
(`"[PR] Failed to open (status=...)"`) and can be copied rather than
re-derived.

**Owner:** unassigned, agent-startable once triaged. Its own arc — do not
bundle with item 21 or any other open credential-path item.

---

## Item 1 — State Reconstruction Audit close-out — in progress at archive time

Archived from `memory/BACKLOG.md` item 1, 2026-09-02, Session 044.

## 1. State Reconstruction Audit close-out
**WSJF: highest (in progress).** Tag `state-audit-2026-07`, get
`memory/STATE.md`, ADR-027 through ADR-032, the Consolidated Keystone
Report, and this file all reviewed and committed as one unit. Everything
below this line is easier to prioritize correctly once this lands, because
right now the backlog itself is partly built on a reconstructed-not-verified
foundation.
**Owner:** Yehor (review + commit + tag — all git writes run on his
machine, not the sandbox).
**Blocks:** nothing downstream is hard-blocked, but doing this first is the
whole point of the audit — see BUILD_PLAN §1's operating principle.

---

## Item 2 — `fly.toml` drift resolution — CLOSED, false positive

Archived from `memory/BACKLOG.md` item 2, 2026-09-02, Session 044.

## 2. `fly.toml` drift resolution — CLOSED, false positive
**Resolved 2026-07-13, no action needed.** The claimed drift was a
sandbox `git diff` misread, not a real working-tree change — Yehor's own
`git status`/`git diff` came back clean. See `memory/STATE.md` and the
correction appended to ADR-029. Retained here (rather than deleted) as a
record that this line item was opened and closed same-day, not silently
dropped.

---

## Item 3a — Verifier gate gap (Gate 2 import-removal exemption) — CLOSED 2026-07-14, commit `b2559a5`

Archived from `memory/BACKLOG.md` item 3a, 2026-09-02, Session 044.

## 3a. Verifier gate gap — broken fix passed all 3 gates (CLOSED 2026-07-14, commit `b2559a5`)
**WSJF: highest — this blocks everything downstream.** Stage-1 E2E
(below) found a Fix-Gen output that deletes a needed import while the
code that uses it is untouched — objectively broken (`NameError` at
runtime) — and the Verifier marked it `VERIFIED` with all 3 gates
passing. Full writeup: `docs/keystones/stage1_e2e_test_2026-07-13.md` §2.

**Decision (2026-07-14):** direct code inspection of `verifier.py`
(not just the Stage-1 report's summary) showed the real mechanism is
Gate 2, not Gate 1: `_out_of_bounds_lines` unconditionally exempted any
removed import-statement line, whether inside the nominal vuln range
(bandit B404's flagged line *is* the import statement itself, so this is
where the actual defect lived) or outside it — with zero check for
whether the removed name was still referenced anywhere else in the
post-edit file. Implemented: `_removed_import_still_referenced()`
(AST-based, not regex/substring — parses the removed import and the
post-edit file, checks `Name`/`Attribute` references; conservative on
any ambiguity: unparseable line, star import, or unparseable post-edit
file all count as "still referenced," i.e. rejected). Gate 2 now only
permits an import removal — in-range or out-of-range — when this
returns False.

**Why Gate 2 and not the other two candidates:** Gate 1 rescanning the
same rule_id can't distinguish "vulnerability fixed" from "the rule's
own trigger condition was deleted" for a rule like B404 whose entire
definition is "this import exists" — broadening Gate 1 would need a
bigger, riskier redesign (rescanning beyond the single rule_id). Gate 3
(require coverage of the changed function) was deferred: real third-party
Stage 2 targets will have uneven test coverage, and making it a hard
gate risks blocking legitimate fixes to exactly the neglected code that
most needs patching — better as a future confidence signal than a
blocking gate. A Fix-Gen prompt constraint alone was rejected as the
primary fix because it's advisory, not enforced — an LLM can still
ignore it; the Gate 2 static check is enforced regardless of what
Fix-Gen produces.

**Status: CLOSED.** Code change + regression test (reproducing the exact
Stage-1 shape) + 8 new unit tests for the helper first verified in an
isolated sandbox venv (36/36 `test_verifier.py` tests pass), then
re-verified by Yehor against the real `.venv` on his own machine: full
suite **431 passed, 2 skipped, 15 deselected, 90.25% coverage** (up
from 90.01% pre-fix; the 10 new tests fully account for the delta, no
regressions elsewhere). Committed `b2559a5` and pushed to `origin/main`
— confirmed via `git ls-remote origin main` matching local HEAD exactly.
See `memory/project_session_log.md` Session 014 entry for the full
walkthrough, including a mid-session PowerShell heredoc/BOM detour
(commit initially landed with a stray UTF-8 BOM character in the
subject line from `Set-Content -Encoding utf8`; fixed via
`git commit --amend` using a base64-encoded, single-line-paste-safe
message after two consecutive heredoc-paste corruptions on this
terminal — worth carrying forward as a standing note, see below).

**Deferred, not forgotten (separate follow-ups, not bundled into this
fix):** excluding purely-informational bandit rules like B404 (whose
only possible "fix" is deleting the thing it flags) from Fix-Gen's
candidate findings at the pipeline level — no existing filter mechanism
was found in `pipeline.py`, so this is a real feature addition, not a
one-liner; broadening Gate 1's rescan; converting Gate 3 to a
confidence signal rather than a blocking gate.

---

## Item 3b — `GITHUB_TOKEN` cannot create PRs — CLOSED 2026-07-14, token permission fixed

Archived from `memory/BACKLOG.md` item 3b, 2026-09-02, Session 044.

## 3b. `GITHUB_TOKEN` cannot create PRs (CLOSED 2026-07-14 — token permission fixed, no code change)
Branches push successfully; `POST /pulls` returned 403 three times in the
Stage-1 run. Classic signature of a token with contents-write but not
pull-request-write permission.

**Root cause confirmed:** the `GITHUB_TOKEN` is a fine-grained PAT
(`github_pat_...`, 93 chars) named "RepoMend", scoped to
`yehorcallmedai-maker/repomend-fixture`. `GET /user` returned 200 (token
live, not expired/revoked). Its Repository permissions had **Contents:
Read and write** and **Metadata: Read-only**, but no **Pull requests**
permission at all — verified visually at
`github.com/settings/tokens?type=beta`, screenshot inspected directly
(not self-reported).

**Fix:** Yehor added **Pull requests: Read and write** to the existing
token via the GitHub UI (Edit → Add permissions → Update). No token
regeneration needed — editing permissions in place does not change the
token string, so `.env` required no change.

**Verified:** a live `POST /repos/.../pulls` call with `head=main,
base=main` (deliberately no diff, to avoid creating a real PR) returned
`422 "No commits between main and main"` — the correct validation
failure for a *permitted* request with no content, as opposed to the
`403` a permissions failure would produce. This confirms the token can
now reach PR-creation logic. Full end-to-end confirmation (an actual fix
branch producing a real PR) is deferred to item 18 (Stage 2 E2E test),
which this item was blocking.

---

## Item 3c — CLI misreports failed PR creation as success — CLOSED 2026-07-14, commit `190fb01`

Archived from `memory/BACKLOG.md` item 3c, 2026-09-02, Session 044.

## 3c. CLI misreports failed PR creation as success (CLOSED 2026-07-14, commit `190fb01`)
`cli.py` L496-499 printed `[PR] Opened: {url}` unconditionally, without
checking `pr_dict['status']` — a 403/422 failure printed as if it
succeeded, just with a blank URL. Confirmed by direct code read.

**Fix:** now branches on `pr_dict['status']`: `"opened"` → `[PR]
Opened: {url}`; `"already_open"` (idempotent case from
`pr_publisher._create_pr`) → `[PR] Already open: {url}`; anything else
(`"api_error"` or any future unexpected value) → `[PR] Failed to open
(status=...)`, printed to stderr. `cli.py` is excluded from this
project's unit-coverage requirement (`pyproject.toml` `omit` list —
integration-tested only, no `test_cli.py`), so no new unit test was
added; verified by direct code read plus a real `py_compile` on
Yehor's machine.

**Notable this session:** the sandbox's bash mount served a
byte-for-byte stale copy of `cli.py` (file `stat` showed a
2026-07-07 mtime — days before today's edit, and the file was
truncated mid-statement at line 624 of 677) when asked to verify the
edit, producing a false `SyntaxError`. `verifier.py` synced correctly
earlier the same session, so this isn't a universal mount failure —
likely file-specific caching. Resolved by trusting the Read tool
(already an established rule for `git status`/`diff`; this extends it
to plain file reads too) and having Yehor run the real compile check
directly. Worth carrying forward: **don't assume a sandbox-side
compile/test failure on a just-edited file is real without an
independent check on the real machine** — same spirit as the existing
"don't trust a tool's self-report" rule, one layer earlier in the
pipeline.

---

## Item 3d — Investigate "requires login" invalid branch name — crash CLOSED 2026-07-14, upstream root cause still unconfirmed

Archived from `memory/BACKLOG.md` item 3d, 2026-09-02, Session 044.

## 3d. Investigate "requires login" invalid branch name (crash CLOSED 2026-07-14; upstream root cause still unconfirmed)
One finding (semgrep subprocess-shell-true) produced a branch name
containing the literal text "requires login", an invalid git ref
(contains a space), crashing `git worktree add`.

**Root cause still unconfirmed** — traced as far as `sarif.py`'s SARIF
normalization reading semgrep's `partialFingerprints`/`fingerprints`
fields verbatim into `finding_id` (`cli.py`/`pipeline.py`), but couldn't
reproduce the actual semgrep behavior without live network access to
the `p/python` registry pack. The original hypothesis (a login-gated
registry request's message leaking into the fingerprint) remains
plausible but unverified.

**The crash itself is fixed regardless of that root cause.** Neither
`cli.py` nor `pipeline.py` validated that `finding_id` (built from
scanner-provided fingerprint/rule_id text) was safe to embed in a git
branch name before calling `git worktree add`. Added
`sanitize_branch_component()` to `worktree_common.py` (this project's
designated single source of truth for shared git primitives, per its
own docstring) — strips/replaces characters git-check-ref-format
forbids (space, `~^:?*[]\`), strips leading/trailing `.`/`-`, collapses
`..` sequences, caps length, and falls back to a safe placeholder if
sanitization would produce an empty string (callers always append a
uuid suffix after, so the fallback only needs to be non-empty). Wired
into both `cli.py`'s and `pipeline.py`'s `finding_id` construction.
8 new unit tests in `test_worktree.py` (`TestSanitizeBranchComponent`
section), including a direct regression test reproducing the exact
"requires login" string. Full suite re-verified by Yehor: 439 passed,
2 skipped, 90.30% coverage, 0 failures.

**Also found and fixed along the way:** `test_config.py`'s
`test_toml_example_parses_cleanly` had to be updated — its own design
prepended a second `[patchward]` block on the (correct) assumption
that the example file had none, which was true before BACKLOG 6a's fix
landed. Against the now-fixed example (which correctly has its own
`[patchward]` section), that produced a duplicate-TOML-table error.
This was the test being stale relative to 6a's fix, not a new defect —
updated to substitute the placeholder `repo_path` value instead of
injecting a second section. Worth noting: this test's original
docstring asserted the missing `[patchward]` section was "intentional
— users set repo_path via CLI flag or scan command," which directly
contradicted this project's own BACKLOG 6a/STATE.md finding that it
was a real, harmful defect. Caught here because running the full suite
after a fix is exactly how a stale test's wrong assumption surfaces.

**Owner:** Claude (agent) implemented and verified via Yehor's full
suite run; root-cause investigation of the semgrep-side anomaly itself
remains TBD if it recurs.

---

## Item 3 (Stage 1) — E2E pipeline test against an owned repo — COMPLETE, result documented

Archived from `memory/BACKLOG.md` item 3 (Stage 1), 2026-09-02, Session 044.

## 3. Stage 1 — E2E pipeline test against an owned repo — COMPLETE, result documented
Full report: `docs/keystones/stage1_e2e_test_2026-07-13.md`. Headline:
3/5 findings reached "verified" status, all 3 branches pushed to the real
remote (confirmed via `git ls-remote`, not just trusting CLI output), 0
PRs opened (blocked by item 3b), and of the 3 "verified" fixes only 2 are
actually correct (item 3a). This is exactly the outcome BUILD_PLAN
predicted was possible and valuable — a cheap Stage-1 failure surfaced
the biggest problem before Stage 2 or wider exposure. Superseded-text
below kept for record of what was planned going in:
**WSJF: highest** (risk-reduction, small job size, the entire product
thesis is unproven end-to-end since the rename). Precondition (item 4)
satisfied 2026-07-13. Pre-flight complete same day:
- `patchward.toml` config defect found and fixed (see `memory/STATE.md`)
- Live dry-run `patchward scan --repo tests\fixture_repo` confirmed 5
  actionable findings (semgrep subprocess-shell-true, bandit
  B602/B307/B105/B404) — two-pass verified against `git show
  HEAD:vulnerable.py`, see Session Strategy brief 2026-07-13
- Decision: run `patchward fix` against all 5 findings unmodified (no
  CLI-level single-finding filter exists; narrowing further would mean
  unproven bespoke engineering on the thing being validated)
**Owner:** Yehor runs `patchward fix` on his own machine (real git push +
PR creation — never from the agent sandbox, per standing rule).
**Still unverified going in:** `GITHUB_TOKEN` push/PR path — `scan`
never exercises it; first real test is this run itself. Treated as an
acceptable unknown, not a blocker — a credential failure here is still a
clean, informative Stage-1 result.
**Gate:** falsifiable either way — a Stage 1 failure is the cheapest place
to find the biggest problem.

---

## Item 4 — Re-verify test suite on current `main` — CLOSED 2026-07-13

Archived from `memory/BACKLOG.md` item 4, 2026-09-02, Session 044.

## 4. Re-verify test suite on current `main` — CLOSED 2026-07-13
**Result: 421 passed, 2 skipped, 15 deselected, 90.01% coverage.**
Confirmed by Yehor on his own machine, promoted into `memory/STATE.md`.
Found and fixed a real environment defect along the way (stale `.venv`
Windows trampoline launchers, left over from before the project
directory's rename — see `memory/STATE.md`'s Tests section for the fix).
Item 3's precondition is now satisfied.

---

## Item 5 — Phase 9 Exposure Gate — FULLY CLOSED, committed and pushed through `3d1ec08`

Archived from `memory/BACKLOG.md` item 5, 2026-09-02, Session 044.

## 5. Phase 9 Exposure Gate — FULLY CLOSED, committed and pushed through `3d1ec08`
**WSJF: high** (security-adjacent, small-medium job size, already-live
surface). Per Session 020's verification, HMAC signature validation is
already done — do not re-implement it. All four original sub-parts
implemented, tested, and confirmed on Yehor's real Python 3.14.4 venv
(`uv run pytest --cov` → 468 passed, 2 skipped, 15 deselected, 90.46%
coverage, threshold 80% reached, no regressions). **Committed and
pushed** — feature commit `0c6a742` (webhook.py + both test files),
docs commit `793a1d0` (this file + session log + strategy memory).
**Session 021 correction: this is not the end of the chain.** Two more
commits landed after `793a1d0`, both real security work, not docs:
`4b6a023` (3 defense-in-depth spy tests proving the post-read body-size
check actually rejects a missing/lying `Content-Length`) and `3d1ec08`
("harden(webhook): range-validate rate-limit/body-size env parsers" —
moves the rate limiter to run *after* `_verify_signature` so an
unauthenticated flood can't consume the rate-limit budget, and closes a
guard hole found in adversarial review of that reorder: the env-parser
helpers now reject non-finite (`inf`/`nan`/`-inf`) and out-of-range
(`<1`, `<=0`) overrides via `math.isfinite()` instead of a bare `except
ValueError`, with a negative-control test
(`test_infinite_window_env_still_expires_limiter_recovers`) proving the
guard actually discriminates guarded vs. unguarded behavior, not just
suppressing a 500). `origin/main` is now `3d1ec086972445373ac6a1eb7ac8abed238559a5`,
confirmed 2026-07-21 via `git ls-remote`, a fresh `git clone`, and a
direct `raw.githubusercontent.com` fetch + sha256 compare of
`webhook.py` against that clone (identical) — three independent methods,
none touching the local `D:\` mount. Test-count cross-check: 468 + 3
(`4b6a023`) + 12 (`3d1ec08`) = 483, matching the reported real-machine
figure exactly. **Note on citing hashes at all** (H2): re-run
`git ls-remote` fresh in any future session rather than trusting the
number above.
- Rate limiting / request body size limits on `/webhooks/github` —
  **IMPLEMENTED 2026-07-16 (Session 020), VERIFIED on Yehor's real
  machine same day.** Checked `fly.toml` first: single Fly
  machine, scale-to-zero, no shared store — same v0 constraints ADR-030
  already accepts elsewhere, so an in-memory approach is consistent
  scope, not a corner cut. Body-size default (25 MB) matches GitHub's
  own documented hard cap on webhook payloads (confirmed via
  `WebSearch`), so it never rejects a real delivery while still
  bounding worst-case memory per request; checked via `Content-Length`
  before the body is read, with a second post-read length check as
  defense-in-depth for a missing/lying header (chunked encoding) —
  documented as a real residual gap, not oversold as fully solved (true
  protection there needs a streaming ASGI-level limit, out of scope for
  this v0 pass). Rate limiting is a plain in-process sliding-window
  counter (60 req/60s default, both tunable via
  `PATCHWARD_WEBHOOK_RATE_LIMIT_MAX` /
  `PATCHWARD_WEBHOOK_RATE_LIMIT_WINDOW_SECONDS` env vars) — bounds a
  runaway/replay flood, not a per-installation fairness mechanism.
  6 new tests in `test_webhook.py` (threshold, window-slide,
  oversized-rejected, within-limit-still-works), plus an autouse
  fixture resetting the limiter's module-level state between tests.
  Sandbox pre-check (Python 3.10, ad hoc `pip install`) predicted 467
  passed (461 + 6); a real sandbox tooling bug was hit and fixed
  mid-session, not routed around: the bash mount served a stale/truncated
  copy of both `webhook.py` and `test_webhook.py` after editing (same
  documented class of bug as Sessions 016/017's `cli.py`/
  `test_orchestrator.py` truncations) — fixed by re-reading each file in
  full via the `Read` tool (trusted per this project's own rule) and
  rewriting it byte-for-byte through a bash heredoc to force the
  sandbox's view back in sync, verified via `ast.parse` before re-running
  tests. **Real confirmation, Yehor's own machine, same day (Python
  3.14.4):** `uv run pytest --cov` → 468 passed (461 baseline + 6 rate-
  limit/body-size tests + 1 pending_change test, combined with the other
  sub-items below), 2 skipped, 15 deselected, **90.46% coverage**,
  threshold 80% reached — exact match to every sandbox prediction, no
  regressions. Diff staged only, not yet committed.
- `X-GitHub-Delivery` header in structured logs — **IMPLEMENTED
  2026-07-16 (Session 020), VERIFIED on Yehor's real machine same day.**
  `webhook.py`'s `github_webhook` now takes an `x_github_delivery` header
  param and includes `delivery=%s` in the single `logger.info(...)` line
  at the top of the handler — since that line runs before the event-type
  dispatch, this covers every path (ping, installation,
  installation_repositories, marketplace_purchase, push, and the
  unrecognized/"ignored" fallback) with one change, not six. Missing
  header logs an empty string, never raises. Two new tests added to
  `tests/test_webhook.py` (`test_delivery_id_logged_for_every_handled_delivery`
  using `caplog.at_level(...)`, matching the existing convention in
  `test_pr_publisher.py`; `test_missing_delivery_header_does_not_crash`).
  Sandbox pre-check (Python 3.10, ad hoc pip install) predicted 463
  passed. **Real confirmation, Yehor's own machine, same day (Python
  3.14.4):** `uv run pytest --cov` → 468 passed (combined total across
  all of item 5's sub-items), 2 skipped, 15 deselected, 90.46% coverage
  — `webhook.py` correctly excluded from the coverage measurement itself
  (`pyproject.toml`'s `[tool.coverage.run].omit` list), consistent with
  the coverage % staying flat despite the new code. Changes staged only,
  not yet committed — diff to be reviewed line-by-line per BUILD_PLAN
  §2's security-boundary rule before Yehor's own commit.
- `pip-audit` run scoped to the `webhook` optional-dependency group —
  **CLOSED 2026-07-16 (Session 020).** Agent's sandbox attempt was
  blocked cleanly (no internet egress to download a matching Python
  3.12+ interpreter for `uv export`; details preserved in
  `project_session_log.md`'s Session 020 entry) — command handed to
  Yehor rather than a guessed verdict. **Yehor ran it for real, on his
  own machine, from the repo root:**
  ```
  uv export --no-emit-project --extra webhook > webhook-reqs.txt
  pip-audit -r webhook-reqs.txt --no-deps
  ```
  (`--no-deps` needed — without it, `pip-audit` tries to build its own
  resolution venv and re-resolve the whole tree, which is slow enough to
  look hung; `uv export` already emits every pinned transitive dependency
  from the lockfile, so there's nothing left to resolve.) **Result: "No
  known vulnerabilities found"** across all 77 resolved packages in the
  `webhook` extra (`fastapi==0.139.0`, `uvicorn==0.51.0`,
  `pyjwt==2.13.0`, `httpx==0.28.1`, and their full transitive tree) —
  Tier 0, Yehor's own terminal output. Re-run periodically as dependency
  versions drift; not a one-time clearance.
- Confirm `is_entitled()` correctly treats `cancelled`/`pending_change`
  Marketplace status as non-entitled — **CLOSED 2026-07-16 (Session
  020). Behavior confirmed correct as-is; Yehor confirmed the reversal
  above after independently checking GitHub's Marketplace docs
  himself** (cancellations/downgrades only take effect at the start of
  the next billing cycle; the current plan stays active until then).
  The session's own earlier "confirmed bug" framing was wrong — kept
  visible in this file rather than silently deleted, per this project's
  correction convention. **No production code changed.** Added
  `test_is_entitled_true_while_pending_change_not_yet_effective` to
  `tests/test_installations_db.py`, same style as the existing
  `is_entitled` tests, asserting `is_entitled()` stays `True` for a
  `pending_change` status and documenting why in its docstring — turns
  today's implicit behavior into an explicit, tested contract instead of
  an unexamined accident. Sandbox pre-check predicted 468 passed.
  **Real confirmation, Yehor's own machine, same day (Python 3.14.4):**
  `uv run pytest --cov` → **468 passed, 2 skipped, 15 deselected, 90.46%
  coverage**, threshold 80% reached, no regressions — exact match,
  `tests\test_installations_db.py` included in the run (11 tests in that
  file, matching). **All four of item 5's sub-parts are now real-machine
  confirmed; only Yehor's commit remains.** Still open, not itself
  resolved this session:
  whether `pending_change_cancelled` exists as a distinct action and
  needs the same reasoning applied — low priority, noted for whenever
  this area is revisited.
- **Session 021 (2026-07-21) addendum — item genuinely, fully closed.**
  `4b6a023` and `3d1ec08` (see header above) landed after this section
  was last edited, closing a real guard hole (non-finite/out-of-range env
  overrides) found in adversarial review of the post-HMAC rate-limiter
  reorder. 12 new tests in `3d1ec08` alone, including a negative-control
  test proving the fix actually changes behavior rather than just
  silencing an exception. Nothing left agent-actionable on this item;
  the only open sub-thread is `pending_change_cancelled` above (low
  priority, whenever revisited).
**Owner:** Claude (agent) for implementation, Yehor reviews line-by-line
per BUILD_PLAN §2's security-boundary rule.

---

## Item 6a — Fix `patchward.toml.example` — CLOSED 2026-07-14, pending commit

Archived from `memory/BACKLOG.md` item 6a, 2026-09-02, Session 044.

## 6a. Fix `patchward.toml.example` (CLOSED 2026-07-14, pending commit)
**WSJF: medium — real defect in a committed, user-facing artifact, cheap
to fix.** The example config that shipped in ADR-025/Phase 7 had no
`[patchward]` section and no `repo_path` field at all (the single most
critical required field for single-repo mode), plus a nonfunctional
`[anthropic]` section that doesn't match `config.py`'s actual schema
(`anthropic_api_key` comes from the env var, not a toml section). A new
user following this template would hit the exact same hard config-load
failure Session 013 found and fixed in the real `patchward.toml`. Found
2026-07-13 while preparing the Stage-1 E2E test.

**Rewritten 2026-07-14.** Direct read of `config.py` surfaced a third,
previously uncatalogued defect in the same file: the old example
documented `max_out_of_bounds_lines` under `[verifier]`, a field that
does not exist on `VerifierConfig` at all — pydantic's default
`extra='ignore'` behavior means this was always silently dropped, a
phantom option that looked configurable but did nothing. New version:
adds the required `[patchward]` section with `repo_path` front and
center and a clear "REQUIRED, no default" comment; removes the bogus
`[anthropic]` section, replacing it with an in-context comment on
`anthropic_api_key` (env var recommended, toml override documented);
removes `max_out_of_bounds_lines`; adds the previously-undocumented
`[fix_gen]` section (`max_turns`, real schema, has a default but worth
surfacing). Top-level section structure (`[patchward]`, `[github]`,
`[batch]`, `[models]`, `[verifier]`, `[fix_gen]`, `[[repos]]` — none
nested) now matches `config.py`'s actual `load_config()` exactly.

**Verified, not just eyeballed:** copied `config.py` and the new
example into an isolated sandbox venv, filled in only `repo_path` (the
one edit the file's own instructions ask a new user to make), and ran
the real `load_config()` against it end to end — every field resolved
correctly, including the `[[repos]]` single-repo fallback list, no
`ValidationError`. **Owner:** Claude (agent) rewrote; Yehor to review
before commit.

---

## Item 6 — `docs/architecture/patchward-webhook-billing-design.md` decision — CLOSED 2026-07-14, scrubbed not recreated

Archived from `memory/BACKLOG.md` item 6, 2026-09-02, Session 044.

## 6. `docs/architecture/patchward-webhook-billing-design.md` decision (CLOSED 2026-07-14 — scrubbed, not recreated)
**Decision: scrub, don't recreate.** ADR-028 and ADR-030 (the two
decisions this phantom file would have covered — FastAPI/Uvicorn/PyJWT
webhook stack, and the GitHub App + Marketplace billing model) each
explicitly state they were "reconstructed... no separate design doc
found in the repo" — meaning the ADRs already are the complete,
canonical record of the facts this file would have contained. Writing
a new `docs/architecture/` file with the same information would create
a second source of truth for the same decisions, with no mechanism to
keep them in sync if either is amended later — exactly the kind of
drift this project's ADR-immutability convention and the State
Reconstruction Audit exist to prevent. Recreating the doc would also
just be citation-satisfying theater: it produces no new information,
only a second copy of what ADR-028/029/030 already say.

**Done:** all three KS-TRACE comments citing the dead path
(`installations_db.py` L1-4, `github_app_auth.py` L9-10, `fly.toml`
L2) rewritten to point at the correct ADR in
`memory/architectural_decisions.md` instead. Note on `fly.toml`
specifically: ADR-029 already documents that `flyctl deploy`
regenerates this file and strips hand-written comments unless manually
restored — this fix may not be durable across the next deploy, same
known fragility as the rest of that file's comments, not a new risk
introduced here.

**Owner:** Claude (agent) decided and implemented, pending Yehor's
review/commit like everything else this session.

---

## Item 7 — `project_open_tasks.md` reconciliation — CLOSED 2026-07-14, folded and archived

Archived from `memory/BACKLOG.md` item 7, 2026-09-02, Session 044.

## 7. `project_open_tasks.md` reconciliation (CLOSED 2026-07-14 — folded and archived)
**Decision: fold + archive**, not keep maintaining separately.
Rationale: the file is ~95% a fully-signed-off historical record
(Phases 0-7, all `[x]`), ends "PROJECT COMPLETE — RepoMend v0.1.0", and
points at `D:\Dev\Projects\RepoMend` — a directory that no longer
exists post-rename. `BACKLOG.md` has already functioned as this
project's sole active task tracker all session; maintaining two
parallel tracking files with no clear boundary between them is exactly
the dual-source-of-truth risk the State Reconstruction Audit exists to
eliminate.

**Done:** archive banner added to the top of `project_open_tasks.md`
marking it historical, pointing to `BACKLOG.md` as the active tracker.
Of its unchecked items: `D-P5-01` (confirm end-to-end PR creation with
a working `GITHUB_TOKEN`) is already substantively covered by items 3b
and 18 below — not duplicated. `KL-P6-01`, the `conftest.py`
`load_dotenv()` call, and two forward-looking Phase 6/7 placeholder
bullets were all confirmed already implemented elsewhere in that same
file (checkboxes just never flipped) — no action needed. Two items had
no equivalent anywhere in current `BACKLOG.md` and are folded forward
as 7a/7b below, explicitly flagged as pre-pivot ideas rather than
freshly-scoped priorities.
**Owner:** Claude (agent) decided and executed; Yehor reviews per usual.

---

## Item 7a — Structured PR template — CLOSED 2026-07-14, already substantively implemented

Archived from `memory/BACKLOG.md` item 7a, 2026-09-02, Session 044.

## 7a. Structured PR template (CLOSED 2026-07-14 — already substantively implemented)
**Correction to this item's own prior entry:** the 2026-07-14 note above
said direct reading of `pr_publisher.py` found this "never implemented."
A closer read this pass (full read of `_build_pr_body()`, not just a
grep) found that's wrong — `pr_publisher.py` already renders a
five-section PR body template (Finding / Fix / Verification Evidence /
Diff / Test Output, `_build_pr_body()` L228-286) per ADR-018/ADR-019 and
constraints C-P5-04 through C-P5-12. This satisfies the pre-rename ask
(intent, diff summary, evidence/test-log links) in substance, just not
labeled "risk class" as its own section. **Not a real gap — folded into
7b below**, since the one missing piece (`risk_class`) is the same data
gap that item already covers. No separate action needed.

---

## Item 7b — Surface `risk_class` in the PR body — CLOSED 2026-07-14, commit `53cd052`

Archived from `memory/BACKLOG.md` item 7b, 2026-09-02, Session 044.

## 7b. Surface `risk_class` in the PR body (CLOSED 2026-07-14, commit `53cd052`)
**Rescoped, then closed, same session.** Original folded item asked for
"risk-class escalation routing." Investigation found the classification
itself already existed (`fix_gen.py`'s `_risk_class_for_severity()`,
AC-P3-08 — `HIGH`/`MEDIUM`/`LOW` from SARIF severity, stored on
`FixResult.risk_class`), but was never displayed anywhere a human
reviewer would see it. Rescoped from vague "escalation routing" to the
concrete gap: display it.

**Done:** `pr_publisher.py`'s `_build_pr_body()` now includes a
`**Risk class:**` line in the Finding section (falls back to `unknown`
if unset). Two new tests in `test_pr_publisher.py`
(`test_build_pr_body_shows_risk_class`,
`test_build_pr_body_risk_class_falls_back_to_unknown`) cover both cases.
Full suite re-verified by Yehor: **441 passed, 2 skipped, 90.31%
coverage** (up from 439/90.30% — the 2 new tests fully account for the
delta, no regressions). Sandbox `py_compile` produced a false
`SyntaxError` on this just-edited file (same stale-mount pattern as
`cli.py` earlier this session) — resolved by trusting the Read tool's
view, confirmed correct, and verifying compile+tests on Yehor's real
machine instead.

**Deliberately not done:** no behavior gates on `risk_class` yet (e.g.,
blocking or extra review for HIGH-risk fixes) — that's a separate
product decision, not scheduled, Yehor's call if/when it matters.

---

## Item 7c — `.dockerignore` untracked — CORRECTED 2026-07-14, claim was false

Archived from `memory/BACKLOG.md` item 7c, 2026-09-02, Session 044.

## 7c. `.dockerignore` untracked (CORRECTED 2026-07-14 — claim was false, already tracked)
**Correction, same day:** this entry originally claimed `.dockerignore`
was untracked and decided to track it. That check was incomplete — it
confirmed the file's content and that `.gitignore` doesn't exclude it,
but never actually ran `git ls-files` to check whether it was tracked,
which is the one check that would have caught the real answer.
`git ls-files --error-unmatch .dockerignore` confirms it **is** tracked,
committed in `8b601e9` ("Stage-1 E2E test report + BACKLOG/STATE
updates, lock webhook extras") and unmodified since. There was no real
gap here — the `git add .dockerignore` run as part of this pass's
commit batch staged nothing, exactly as it should for an already-tracked,
unmodified file. Left visible rather than silently fixed, per this
project's established correction convention (see ADR-029's amendment,
BACKLOG item 2). **No action was actually needed.**

---

## Item 8 — `callmed-landing` rename — CLOSED 2026-07-22 (Session 022)

Archived from `memory/BACKLOG.md` item 8, 2026-09-02, Session 044.

## 8. callmed-landing rename — CLOSED 2026-07-22 (Session 022)
**Fully closed this session, Tier-0 verified.** `C:\Dev\Projects` connected
mid-session, making both `callmed-landing` and `Autonomous-Core` directly
reachable for the first time. Fresh direct read (not the prior Tier-2
Autonomous-Core secondhand record) confirmed: the `#381→#383` citation fix
and "9 PRs"→"11 PRs" proof-count update were already live in `index.html`
line 174 (upgraded Tier 2→Tier 0). The RepoMend→Patchward swap itself:
**45 real word-occurrences** across `index.html`(24)/`privacy.html`(7)/
`security.html`(14) — not 34 as previously estimated; that figure was a
`grep -c` line-count, not a word-count (several lines carry 2-3 instances).
Fixed via case-sensitive two-pass swap (`RepoMend`→`Patchward`,
`repomend`→`patchward`), verified 45→0 via `grep -o -i`.
**Investigation also caught 3 occurrences that weren't cosmetic** — the
page was giving visitors actively wrong instructions, not just an old
brand name: (a) index.html's CLI sample (`uv tool install repomend` /
`repomend fix --repo .`) — real entry point is `patchward`
(`pyproject.toml` `[project.scripts]`), fixed automatically by the plain
swap and cross-checked against `src/patchward/cli.py`'s real `fix --repo`
option; (b) security.html's branch-naming line (`repomend/fix-{id}`) —
real pattern per `src/patchward/fix_worktree.py`'s own docstring is
`patchward/fix-<finding-id>`, required a manual fix beyond the naive
swap (HTML-entity-encoded as `&lt;finding-id&gt;` so it renders as text,
not markup); (c) security.html's PyPI-namespace claim (`repomend`
namespace) — now correctly `patchward`, fixed by the plain swap and
Tier-0 confirmed via item 9's fresh publish this same session. Corrected
files delivered to Yehor and written to `C:\Dev\Projects\callmed-landing\`
**uncommitted** (not pushed, live site untouched) for his own `git diff`
review and commit — per standing process, no agent commits to a repo
without Yehor's own review pass first. **New backlog candidate surfaced,
not acted on:** the real Patchward codebase still has ~59 internal
"repomend" references across 15 files (e.g. `RepomendConfig` class in
`config.py`/`webhook.py`) — see item 16.
**Owner:** Yehor, for the `git diff` review + commit only; the actual
content work is done.

---

## Item 9 — PyPI Trusted Publisher — CLOSED 2026-07-22 (Session 022), Tier-0 end-to-end

Archived from `memory/BACKLOG.md` item 9, 2026-09-02, Session 044.

## 9. PyPI Trusted Publisher — CLOSED 2026-07-22 (Session 022), Tier-0 end-to-end
**Fully closed this session — the real publish happened and was verified
two independent ways, not inferred.** PyPI's pending-publisher UI showed
**Environment name: `(Any)`** (parenthesized italic — PyPI's own
placeholder for "no restriction," not a literal string "Any" someone
typed), which matches `publish.yml`'s `environment: pypi` claim without
issue — the risk this item flagged does not materialize. Yehor then
triggered `workflow_dispatch` on `main` @ `07f97d3` (the session's
verified HEAD) via GitHub's UI. Result, confirmed via two independent
methods: (1) the Actions run itself — `build` (10s) → `publish` (21s),
both green, 47s total; (2) the actual PyPI release page,
`pypi.org/project/patchward/0.1.0/` — live, uploaded 2026-07-22, both
`patchward-0.1.0.tar.gz` and `patchward-0.1.0-py3-none-any.whl` present,
explicitly stating **"uploaded using Trusted Publishing via GitHub
Actions from the repository `yehorcallmedai-maker/Patchward`"** — the
OIDC identity chain proven working end-to-end, not just "environment
field looks right." Minor non-blocking oddity: the bare
`pypi.org/project/patchward` (no version) 404'd twice via this session's
fetch tool while the version-pinned URL loaded fine — read as a
caching/propagation quirk on the fetch side, not a real problem; Yehor
can confirm with his own browser at his convenience. `patchward` v0.1.0
is now a real, live, public PyPI package. **Owner:** none — closed.

---

## Item 10 — "Mirror Pass Tier 2" — REMOVED 2026-07-15, never belonged in this file

Archived from `memory/BACKLOG.md` item 10, 2026-09-02, Session 044.
**Note:** this entry's original body names dollar figures for a
different Yehor-run product's pricing (Mirror Pass / Symbiote, on
`callmedai.com`) — unrelated to any Patchward/NJORD commercial figure
this project has ever redacted. Preserved verbatim as pre-existing
archival content, flagged here rather than silently altered.

## 10. "Mirror Pass Tier 2" — REMOVED 2026-07-15 (Session 018, cross-project research) — never belonged in this file
**This was a category error carried in from `BUILD_PLAN_2026-07-10.md`,
not a Patchward feature at all.** Confirmed via `Autonomous-Core`
(`docs/architecture/competitive_analysis.md`,
`memory/symbiote-recurring-income-research-and-buildplan.md`): "Mirror
Pass" (also called Symbiote) is a completely separate product Yehor
runs — a $1,500 flat-fee PEP 484 type-annotation consulting service for
Python codebases, marketed on callmedai.com. "Tier 2" is a pricing/scope
upsell for that service (service layer + entities layer, $3,000–$4,000),
tracked as its own numbered backlog item **inside Autonomous-Core's own
tracker** (a different "#12" than this file's item 12 — pure numbering
coincidence, confirmed by content, not by number). It is a sales/outreach
task (find ICP-matched prospects per `competitive_analysis.md` §5c),
not an engineering task, and has zero code surface in this repo.
Removed here rather than silently reassigned, per this project's own
correction convention — same treatment as the ClinInsight/Databutton
item removed in Session 014. If Yehor wants to track it, it belongs in
Autonomous-Core's tracker, where it already lives.

---

## Item 11 — Stage 2 authorized third-party E2E test — COMPLETE 2026-07-14, PR #1 on ssh-audit

Archived from `memory/BACKLOG.md` item 11, 2026-09-02, Session 044.

## 11. Stage 2 — authorized third-party E2E test (COMPLETE 2026-07-14 — PR #1 on ssh-audit)
**Target selection:** `yehorcallmedai-maker/ssh-audit` (public fork, 1.4 MB,
real Python security tool) — chosen over `checkdmarc` and explicitly over
`django`/`langchain`/`twisted` (too large/complex for a first controlled
run) and over Yehor's private repos (real personal/business assets,
unnecessary risk vs. a disposable public fork). "Third-party" satisfied
via real, unplanted third-party *code* (someone else wrote ssh-audit)
with zero external-consent complexity (Yehor owns the fork outright).

**Dry-run scan:** 703 raw findings, 698 in test files (correctly excluded
by `patchward fix`'s test-path pre-filter, `cli.py` L317-337). 5
actionable, all in `ssh_socket.py`/`dheat.py`. Scanner-model triage
correctly assessed 4/5 as by-design (bind-to-all-interfaces ×2 + B104
duplicate — intentional for an SSH-auditing server; B311 — weak PRNG in
a DHEat attack *simulation*, not production crypto) and 1/5 as a clean,
real fix candidate (B110 — bare `except Exception: pass`).

**`patchward fix` result:** 4/5 correctly **not** force-fixed — Fix-Gen
exhausted its turn budget without calling `submit_fix` on the by-design
findings rather than fabricating unnecessary changes (a real, valuable
outcome: it didn't file bad PRs on non-issues, though "runs out of
turns" vs. an explicit "decline, not a real issue" path is worth
improving later — see new item 13 below). 1/5 **verified and shipped**:
`bandit.B110` fix (`except Exception:` → `except OSError:` in
`_close_socket()`) passed Gate 1 (pass), Gate 2 (pass), Gate 3 (**skip**
— no test suite detected in the fix worktree, expected and correct per
`verifier.py`'s own doc: `ssh-audit`'s test dependencies aren't installed
in Patchward's `.venv`, this is documented as SKIP-not-FAIL specifically
for this external-repo scenario, not a red flag).

**Verified independently, not from CLI self-report** (per BACKLOG 3c's
own history): `gh pr view` confirmed PR #1 is real, `state: OPEN`,
**`isDraft: true`** (ADR-019 satisfied), `baseRefName: master` (correct —
`ssh-audit` predates GitHub's "main" default, caught via `gh repo view`'s
`defaultBranchRef` before configuring). `gh pr diff` confirmed the actual
diff matches Fix-Gen's self-reported `diff_summary` exactly — 1 file,
+1/-1.

**New evidence for BACKLOG 3d's still-unconfirmed root cause:** the exact
anomalous `"requires login"` string recurred in `finding_id`/branch-name
construction for 2 of the 4 declined findings
(`avoid-bind-to-all-interfaces`) — a *different* semgrep rule than Stage
1's occurrence (`subprocess-shell-true`), in a *different* repo. Confirmed
via grep that this string is not hardcoded anywhere in Patchward's own
code (`worktree_common.py`'s only match is the comment describing the
phenomenon, not producing it) — it's genuinely scanner-sourced. Recurring
across different rules and repos shifts the working theory from "one
rule's message leaking into its own fingerprint" toward a more systemic
cause (e.g., a shared semgrep registry/auth response bleeding into
fingerprint generation broadly). The crash itself remains fixed
regardless (`sanitize_branch_component()` handled both occurrences
cleanly, no crash this run) — root cause still not conclusively
identified, but narrowed.

**Owner:** Yehor authorized, Claude executed — result reviewed together
with independent verification at each step.

**Post-close-out follow-up (same day):** PR #1 sat as a draft after the
Stage 2 run — per ADR-019/ADR-003 (always draft, never auto-merge),
merging is a deliberate human action, not something the pipeline does.
Re-verified the diff was still unchanged via a third, independent method
(`patch-diff.githubusercontent.com`, distinct from both `gh pr view` and
the GitHub API) before recommending merge — Yehor's own repo, no
external stakeholder, fix confirmed correct, no reason to leave it open
indefinitely. `gh pr merge` initially failed ("Pull Request is still a
draft" — expected, GitHub blocks merging drafts directly); resolved via
`gh pr ready` then `gh pr merge --squash --delete-branch`. Squash-merged,
branch deleted. Stage 2's full loop (scan → fix → verify → push → PR →
human review → merge) is now complete end to end, not just up through
PR creation.

**Unrelated housekeeping caught in the same pass:** a `future-agi-contribution/`
directory was found nested inside Patchward's folder tree (untracked by
this repo's git throughout the session — correctly isolated, never
staged). Verified via direct file read: it's a genuine, separate,
actively-managed project (an OSS contribution effort to
`future-agi/future-agi`, with its own `.strategy/STRATEGY.md` memory and
session history) that happened to be created inside Patchward's
directory rather than its own. Not a Patchward concern content-wise —
duplicating analysis of it here would risk exactly the
dual-source-of-truth problem this project's own conventions exist to
avoid (same pattern as `project_open_tasks.md` vs `BACKLOG.md`).
Relocated to `D:\Dev\Projects\future-agi-contribution` (verified via
`Test-Path`: gone from Patchward's tree, present with its memory intact
at the new location) — no other action taken, that project continues in
its own session.

**Correction, same day:** the relocation above was wrong and has been
reversed. The Future AGI session was still actively running, independent
of this one, with its own memory of the original nested path. After this
session moved the directory out, that other session found nothing at
its remembered path, treated it as data loss, and rebuilt its memory
file from scratch back at the original nested location — then kept
working there, producing a more complete, more current record
(including a `SESSION_CLOSE_2026-07-14.md` this pass's copy never saw).
Discovered when the directory reappeared in `git status` after the
move; confirmed via `Get-ChildItem` on both paths (nested copy: newer,
larger, includes the session-close file; relocated copy: frozen at the
pre-continuation state) and a direct read of the nested `STRATEGY.md`
confirming it matches the more recent, more detailed record. **Lesson:**
relocating a directory that might be a live dependency of a different,
concurrently-running session risks exactly this kind of silent fork —
should have flagged the possibility rather than treating the move as
purely a Patchward-side hygiene call. The stale duplicate at
`D:\Dev\Projects\future-agi-contribution` is being deleted; the nested
copy inside Patchward's tree is being kept and remains untracked by
this repo's git, as it was throughout.

---

## Item 12 — Regulatory flags (CRA / GDPR classification) — full session-by-session history through settlement (paused 2026-09-02)

Archived from `memory/BACKLOG.md` item 12, 2026-09-02, Session 044. The
live file now carries a condensed settled-status summary and a pointer
here. Full verbatim text below, exactly as it stood in `BACKLOG.md`
immediately before this compression:

## 12. Regulatory flags — CRA / GDPR classification — PAUSED BY YEHOR (BUDGET/TIMING, PRE-REVENUE) — REOPENS ON HIS OWN INITIATIVE, NO FIXED DATE (2026-07-24, Session 024; updated 2026-09-02, Session 044)
**WSJF: low urgency now, high cost if skipped before Phase 10.** Get
Patchward's CRA Annex III classification and a lightweight GDPR
DPIA/TTL policy on `installations_db.py` confirmed by someone qualified
before any paid Marketplace listing — not after.

**Session 024 update:** this item is NOT closed — it is still genuinely
blocked on finding and engaging qualified counsel, same as every prior
session. What changed: the previously indivisible "needs counsel" label has
been split into the actual legal determination (not agent-startable) and
the technical briefing packet counsel needs before they can even answer
(fully agent-startable, and the real reason this sat still for 3+ weeks —
nobody had written it). That packet now exists:
`memory/BACKLOG12_counsel_briefing_packet_2026-07-24.md`. It contains,
strictly separated from any legal conclusion: (1) a field-by-field data
inventory of `installations_db.py` read directly from source, including a
confirmed retention gap (see new item 18 below); (2) a product-facts sheet
covering all three real deployment models (CLI/PyPI, Docker sandbox,
Fly-hosted webhook), the commercial model, jurisdiction, and third-party
processors; (3) a corrected data-flow fact, verified against
`fix_gen.py`/`credential_proxy.py` at HEAD `3e63587` — the "only the fix
prompt reaches the Anthropic API, scrubbed of credentials" description is
not accurate as stated (real repository source code is sent via the
Fix-Gen subagent's `read_file` tool results, and `CredentialProxy.scrub()`
is only ever called on CLI/log output in `cli.py`, never on anything
actually sent to Anthropic); (4) a precise question list for counsel
(manufacturer status, open-source exemption vs. a paid Marketplace
listing, Annex III class, controller/processor role, DPIA need, DPA need);
(5) a DRAFT (unpublished, not reviewed) pre-distribution disclaimer; (6) a
freshly re-verified CRA timeline — the previously-cited 24h/72h/14-day
reporting deadline, binding 2026-09-11, was confirmed again via the
European Commission's own CRA pages (not just re-asserted from
`BUILD_PLAN`'s original secondary-sourced figure), with one nuance the
prior memory didn't carry explicitly: 2026-09-11 is specifically the
Article 14 *reporting*-obligation date, not the CRA's full
conformity-assessment applicability date (2027-12-11) — Yehor's launch
window (2026-09-08 to 2026-09-11) lands directly on the earlier,
reporting-obligation date regardless of how the harder Annex III
classification question resolves.
**Owner:** Yehor (external legal input required — not something the agent
can resolve; the packet above is the agent-startable part, now done).

**Session 042 open update (2026-08-28), verified via Gmail + Calendar,
two independent tool calls each:** the 2026-08-26 16:00-17:00 NJORD
meeting (Nis Peter Dall) happened — confirmed by the opening line of
Yehor's own follow-up email ("Thank you for a good meeting today"), not
assumed. The CRA follow-up email (subject "Follow-up to today's meeting
— CRA question as a possible separate task", to `npd@njordlaw.com`,
with `Patchward_Counsel_Briefing_Packet_2026-08-03.pdf` attached) was
sent 2026-08-26 18:40 Europe/Copenhagen (thread `1a03eea261e68ac5`) —
after the meeting as planned, about an hour past the 17:15-17:30
reminder window, not a concern. It asks NJORD directly (1) whether CRA/
product-regulation work is in their wheelhouse, and (2) whether the
Article 14 question can be scoped as a separate task alongside the
Phase 1 (FixProve) work discussed in the meeting. **No reply from NJORD
as of this check** (`from:njordlaw.com`/`from:npd@njordlaw.com` searches
both return nothing newer than the 2026-08-20 meeting-scheduling
thread) — 2 days elapsed, not yet a concern, but worth a nudge if it
passes roughly a week with no response given the 2026-09-11 Article 14
deadline. This item remains NOT closed; still externally gated, now on
NJORD's answer rather than on getting a meeting scheduled.

**Session 042 continued (2026-08-28), commit + nudge:** commit
`f1fe546` (the memory update above) independently confirmed on origin
via fresh clone + `ls-remote` — diff-stat matches exactly (2 files, 43
insertions, 1 deletion). A nudge reminder was set for **2026-08-31
09:00 Europe/Copenhagen** (event `uueepgqam0mvuh0dngq6sp34tk`),
independently re-read via a separate `list_events` call — creation
response and re-read agree exactly, no discrepancy (H35-candidate
still just 1 occurrence, not reinforced by this check). **Honest note
on the 09-08 vs 09-11 question:** the existing text above ("launch
window lands directly on the earlier, reporting-obligation date")
confirms the two dates are the same regulatory window, not two
unrelated numbers — but it does not itself state whether counsel
sign-off must land before the window opens (09-08) or merely by the
Article 14 date (09-11); that reading is still Yehor's call, not
something this file resolves on its own. 2026-08-31 was chosen because
it is safely conservative either way (8 days before 09-08, 11 before
09-11) — the date does not depend on settling that interpretation.

**Session 043 open (2026-08-31), NJORD responded — verified via
`get_thread` on the actual message body, not the search snippet alone:**
NJORD replied 2026-08-31 11:39 CPH, **not in the CRA-specific thread**
(`1a03eea261e68ac5` — re-checked via `get_thread`, still shows only
Yehor's original outbound message, no reply landed there) **but in a
separate, broader meeting-follow-up thread** (`1a0579e503bd7a7f`,
subject "Opfølgning på møde - Fixprove - Patchward") that covers three
distinct workstreams in one email. Answering this item's two open
questions directly:

1. **Is CRA/product-regulation work in NJORD's wheelhouse? Yes,
   explicitly.** ("Vi kan bistå med en særskilt og afgrænset vurdering
   af CRA-spørgsmålet ift. Patchward ved siden af arbejdet med
   privatlivspolitik og vilkår for anvendelse til FixProve.")
2. **How would it be scoped alongside FixProve Fase 1?** As a
   deliberately narrow, separate task, priced and delivered
   independently of the FixProve privacy-policy/terms work:
   - **Scope offered:** an assessment of whether the CRA Article 14
     reporting obligation applies to Patchward from 2026-09-11,
     touching CRA's scope of application and the "manufacturer" role
     only as far as needed to answer that one question. Deliverable: a
     short written memo, plus — if the reporting obligation is found to
     apply — a practical minimum-procedure overview for handling
     relevant vulnerabilities/security incidents.
   - **Price:** [quote received, filed privately — see Yehor's own
     records, not tracked in this public repo].
   - **Explicitly out of scope** of this narrow assessment (NJORD's own
     words): full CRA classification, GDPR roles, DPIA, US transfers,
     data processing agreement, disclaimer-text review — all available
     as further separate tasks if/when relevant. This confirms the
     Article 14 question and the fuller classification question this
     backlog item originally scoped are NOT the same engagement in
     NJORD's proposal; Article 14 alone is what's on the table at the
     price quoted above.
   - **Not yet engaged/paid** — this is a quote, not a completed
     assessment. The item stays open until Yehor confirms he wants this
     workstream started and NJORD delivers the memo.

The same email also quotes: FixProve privacy policy + terms of use
[quote received, filed privately]; and, unprompted, a company-structure
recommendation (convert/found an ApS to limit personal liability —
[quotes received, filed privately] depending on the chosen model) — both
out of this item's scope (CRA/GDPR classification) and logged here only so the
three-offer email isn't read as CRA-only if revisited later. NJORD's
close asks Yehor to confirm, in one reply, which of the three
(FixProve terms, company structuring, Patchward CRA assessment) to
proceed with — nothing is actioned automatically.

**Session 043 continued (2026-08-31), Yehor already replied — verified
via `get_thread` on the actual sent message, not assumed from the
user's own paraphrase:** Yehor sent a reply at 14:34 CPH (thread
`1a0583baf61a4e21`, "SV: Opfølgning på møde - Fixprove - Patchward",
to `npd@njordlaw.com`) — **before this session's Session 043 memory
commit (`b5da9e8`) had even landed**, meaning the "awaiting Yehor's
go/no-go" framing above was already stale the moment it was pushed.
Logged honestly rather than left uncorrected. The reply covers all
three of NJORD's offers in one message:
1. **Correction on record:** FixProve is a CLI (npm/PyPI) + GitHub App
   only — no separate web-based version, contra NJORD's notes.
2. **FixProve terms/privacy:** before committing to the full quoted
   estimate, Yehor asked for a narrower "Phase 1" estimate instead —
   the legal minimum to open the GitHub App for free third-party
   installs (durable terms + privacy policy for the current free beta,
   with the business-only restriction NJORD recommended). Payment flow,
   paid-version terms, and broader consumer-law questions deferred to a
   Phase 2 once a paid version actually ships. Noted that drafts of
   both documents already exist for NJORD to start from.
3. **ApS structuring:** agrees with the direction, explicitly parks it
   until there's real demand and paying customers — doesn't block
   opening the app. Will revisit separately.
4. **Patchward CRA/Article 14 — this backlog item's own question:**
   thanked NJORD for the narrow scoping, then proposed splitting it
   further into two steps: (1) a short assessment of whether Article 14
   is expected to apply to Patchward *in its current form* (free open
   source only, paid Marketplace not live), and (2) the practical
   procedure overview — **only if step (1) answers yes.** Explicitly
   asked for an estimate for step 1 alone, and whether step 1 can be
   delivered before 2026-09-11. This functionally supersedes the
   "confirm whether 15k alone satisfies 09-11" question flagged earlier
   this session — Yehor's actual question is more precise (asks for a
   deliverable and a deadline commitment, not just a yes/no).
5. Also asked NJORD about the partial extended payment terms they
   mentioned in the meeting, for whichever tasks proceed.

**Session 043 continued (2026-08-31, 15:07 CPH), sufficiency-gap
addendum sent — verified via `get_thread`, sent text compared word for
word against the drafted version, not assumed unchanged:** a re-read of
point 4 above found a real, if subtle, gap: Yehor's 14:34 message asks
whether the **step 1 answer** can arrive before 2026-09-11, but never
asks whether **step 1 alone** (without step 2 also being in place)
actually **discharges** the Article 14 reporting obligation by that
date. A short addendum was drafted, reviewed by Yehor, sent unedited
(sent body matches the draft exactly) at 15:07 CPH — same thread
(`1a0583baf61a4e21`), message `1a0585cbb9e933a7`, to `npd@njordlaw.com`
cc `malped@njordlaw.com`. Verbatim: *"Endnu en kort opfølgning på
CRA-spørgsmålet: mit spørgsmål ovenfor gik på, om selve
trin 1-vurderingen kan leveres inden den 11. september. Jeg vil gerne
præcisere om det er trin 1 alene — altså blot vurderingen af, om
artikel 14 gælder — der opfylder rapporteringsforpligtelsen pr. den
11. september, eller om trin 2 (den praktiske procedure) også skal
være på plads inden da, for at forpligtelsen reelt er overholdt."*
(EN gloss: does step 1 alone satisfy the Sept 11 obligation, or does
step 2 also need to be in place by then.)

**Owner:** NJORD now — the ball is genuinely in their court on all four
numbered points from the 14:34 message plus this addendum's
sufficiency question. Next agent-relevant action is checking for
NJORD's reply in thread `1a0583baf61a4e21` in a future session, not
drafting anything further now.

**Nudge reminder status:** the 2026-08-31 09:00 CPH nudge event
(`uueepgqam0mvuh0dngq6sp34tk`) fired before NJORD's 11:39 CPH reply — at
09:00 the silence was still real (2 → 5 days elapsed, correctly past
the "worth a nudge" threshold set in Session 042), so the reminder was
not a false alarm; it is simply superseded now — no nudge send is
needed today, NJORD answered on its own first. No further action needed
on the reminder itself.

**Session 044 open (2026-09-02), NJORD answered both outstanding
questions — verified via `get_thread` on thread `1a0583baf61a4e21`
directly (not a search snippet), cross-checked via `search_threads
from:njordlaw.com newer_than:1d` (returns the same single thread, no
reply landed anywhere else this time — contra Session 043's own
two-threads-in-one-day pattern, worth noting since this project has
hit that shape twice before):** NJORD (Nis Peter Dall) replied
2026-09-02 11:23 CPH (09:23:41 UTC), message `1a0616f07ab2fe70`, to
`yehor.callmedai@gmail.com`, cc `malped@njordlaw.com` — same thread as
Yehor's 14:34/15:07 messages, not a new one.

1. **Scope/price for the Article 14 step-1 assessment, confirmed as
   offered:** "Vedrørende CRA-spørgsmålet om Patchward kan vi godt
   afgrænse opgaven, som du foreslår. Vi kan først foretage en kort
   vurdering af, om rapporteringsforpligtelsen i artikel 14 må
   forventes at gælde for Patchward i dets nuværende form. Den
   praktiske procedure vil herefter kun blive relevant, hvis
   vurderingen fører til, at rapporteringsforpligtelsen finder
   anvendelse." Price for step 1 alone: [quote received, filed
   privately — see Yehor's own records, not tracked in this public
   repo]. Step 2 (the practical procedure) would be separately scoped
   and separately priced, only if step 1 concludes the obligation
   applies.

2. **The sufficiency question (does step 1 alone discharge the Sept 11
   obligation, or is step 2 also required by then) is answered
   directly, not hedged — quoted verbatim, this is NJORD's legal
   reading, not this project's own interpretation, logged per this
   file's standing rule against hedging toward a legal conclusion:**
   "Hvis Patchward er omfattet af rapporteringsforpligtelsen i CRA
   artikel 14, er den 11. september 2026 ikke en frist, hvor der skal
   indsendes en rapport eller dokumenteres en konkret sårbarhed på
   forhånd. Datoen er derimod det tidspunkt, hvor rapporteringsreglerne
   begynder at gælde. Skulle Patchward efter denne dato bliver
   opmærksom på en aktivt udnyttet sårbarhed eller en alvorlig
   sikkerhedshændelse, kan der opstå pligt til at foretage
   indberetning inden for de frister, som artikel 14 fastsætter." (EN
   gloss: if Patchward is covered by Article 14, Sept 11 2026 is NOT a
   deadline to file a report or document a specific vulnerability in
   advance — it is the date the reporting *rules* start applying. Only
   if Patchward becomes aware, after that date, of an actively
   exploited vulnerability or a serious security incident does an
   obligation to report within Article 14's own (24h/72h/14-day)
   deadlines arise — those sub-deadlines would run from the incident,
   not from Sept 11 itself.) **Answering this item's open sufficiency
   question: step 1 alone is what's needed by/around Sept 11; there is
   no separate requirement that step 2 also be in place by that date
   as a compliance gate.** Step 2 only becomes operationally relevant
   if a real triggering incident occurs after Sept 11 and Article 14
   is found to apply.

3. **Real timing pressure:** NJORD states they need Yehor's go-ahead by
   Friday (2026-09-04) to be able to deliver the Article 14 assessment
   before Sept 11.

4. **Payment terms proposed:** FixProve terms/privacy work — half
   invoiced with 14 days' notice on completion, remainder over 3
   months (final payment by year-end). The smaller Patchward CRA task
   specifically — full amount invoiced at once, 14 days' notice.

**Owner: Yehor.** Next action is his decision on whether to greenlight
the CRA step-1 assessment (and/or the other two NJORD offers), ideally
before Friday 2026-09-04 per NJORD's own stated cutoff. Nothing further
for the agent unless asked to draft that reply.

**Session 044 continued (2026-09-02, 17:39 CPH) — RESOLVED, PAUSED BY
YEHOR'S OWN DECISION. Verified via a fresh `get_thread` on the actual
sent message, not the pasted screenshot text alone — one correction to
a claim made about it:** a pasted review ("guide model") reported this
reply as landing in thread `1a0583baf61a4e21` (the same thread as the
14:34/15:07 messages and NJORD's 09:23 reply). Independent check
(`search_threads to:npd@njordlaw.com newer_than:1d` + `get_thread`)
found this is **not accurate — the reply landed in a new thread,
`1a062be715af4ce6`**, same subject line, sent 2026-09-02T15:39:01Z
(17:39 CPH), matching the pasted content word-for-word once located.
Corrected here rather than silently inherited — this is the same
thread-splitting shape NJORD's own side has hit twice before, now
observed on Yehor's outbound side too; a future session checking this
chain should search broadly
(`{from:npd@njordlaw.com OR to:npd@njordlaw.com} newer_than:Xd`)
rather than assume every message lands in one known thread ID.

**Outcome, Yehor's own words, verified:** both open workstreams —
FixProve Fase 1 (terms/privacy) and Patchward CRA Article 14 step 1 —
are **paused indefinitely**, for timing/economics in a pre-revenue
phase, explicitly not dissatisfaction with NJORD's offer (Yehor called
it "fair and well-scoped" — "fair og velafgrænset"). He thanked NJORD
for the Sept-11 clarification (rules-start-date, not a filing
deadline), said he'll return "when the foundation is in place" ("når
grundlaget er på plads") and assumes the same estimates will still
apply then — **his own stated assumption, not a commitment NJORD has
agreed to**; nothing in NJORD's own reply promises the quote holds
open. No fixed revisit date; reopens on Yehor's own initiative, tied
to revenue/funding.

**What this changes for BACKLOG 12:** the counsel-engagement path is
parked, not abandoned and not answered. The technical briefing packet
(`memory/BACKLOG12_counsel_briefing_packet_2026-07-24.md`) remains on
file as Yehor's own preliminary, good-faith self-assessment — stated
here plainly, as it should be stated anywhere this is referenced
again: **this is not a substitute for qualified legal review**, only a
documented starting position for whenever counsel is re-engaged.
NJORD's own clarification on the Article 14 timeline (2026-09-11 is
when the reporting obligation's rules begin applying, not a one-time
filing deadline; an actual reporting duty, with its own 24h/72h/14-day
sub-deadlines, would only arise from a real post-Sept-11 incident)
stands on record regardless of the pause and remains the most current,
qualified-source information this project has on the question — even
though it stops short of full formal advice.

**Redaction check on this update, per H40's standing rule, run before
writing rather than after:** neither NJORD's fee quote nor any other
kr figure appears in the sent reply itself (confirmed by reading its
full body) or in this entry. A fresh grep of the actual local working
tree (`.strategy/STRATEGY.md`, `memory/BACKLOG.md`, both files this
session has touched) for currency patterns and the bare word "kr"
found zero numeric leaks — the two "kr" matches present are prose
describing the earlier redaction, not restated figures.

**Owner: Yehor**, for whenever he chooses to reopen this — no
agent-startable work remains on BACKLOG 12 at this time.
