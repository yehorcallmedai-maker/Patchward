# Session Close — Patchward — 2026-08-04 (Session 029)

Opened via `session-strategy-synthesis`; closed via `session-close`. This file is
the handoff for Session 030. Per H2 it deliberately cites NO closing hash (the
memory commit that seals this session moves HEAD after this file is written); the
close is verified BY CONTENT below. The code commit this session shipped is
`d72c0df` and that hash IS stable — it was pushed and fresh-clone verified before
this file was written.

## Session shape (one line)

The first code-shipping session in three: §5 decision C2 went from decided-only to
implemented, tested, adversarially attacked, and landed on `origin` — with an
injection defense that was not in the memo spec and that the naive spec-conformant
implementation would have shipped as a verification bypass.

## Gate status

| Claim | Pass 1 | Pass 2 | Verdict |
|---|---|---|---|
| Session 028 close had fully landed | fresh clone: `SESSION_CLOSE_2026-08-01.md` + `BACKLOG_S5_..._memo` both present AND tracked (`git ls-files`) | memo §7 content grep = "§5 = C2"; BACKLOG L1323 pointer; STRATEGY L1774/1831/1848/1863 | **CONFIRMED** — H18 check applied to the memo, it was genuinely filed |
| Real HEAD at open (prompt cited none, per H2) | local `git rev-parse` = `b003a39` | `git ls-remote origin` + fresh clone agree | **CONFIRMED** |
| Working tree "modified" in 57 files | sandbox `git status` | per-file CRLF-stripped sha256 → **0** real-content diffs | **CONFIRMED noise** (H16, 5th consecutive session) |
| §5 mechanism: hosted repo with tests hard-FAILs | source read `verifier.py` L769/L790 | line numbers exact; `pyproject.toml` puts pytest in `dev`, Dockerfile installs `.[webhook]` only | **CONFIRMED** |
| Item 21: `github_token` dead in `run_repo_pipeline` | grep: appears at L68, L330, L347 only | no use anywhere in body L68–329; `PRPublisher` reads `GITHUB_TOKEN` from proxy instead | **CONFIRMED** — and traced to one hop |
| Item 28 patch prepared, not landed | file present in repo root | `git ls-files` returns empty → untracked | **CONFIRMED still unlanded** |
| C2 steps 1–2 implemented correctly | full CRLF-normalised diff read line-by-line | full suite on Yehor's Py 3.14.4: **531 passed / 3 skipped / 91.11%** | **CONFIRMED** |
| Injection defense actually holds | code read: probe takes only `worktree_path`, never `output`/`proc`/`summary` | **real-repo adversarial pass, no mocks**: 6 forged-signature attacks all still FAILed; mutation check (probe deleted) turns both negative controls red | **CONFIRMED** |
| Commit landed on origin | `git push` reported `b003a39..d72c0df` | **fresh clone**: HEAD = `d72c0df`, 4 files +354/−8, all four blobs stored **LF** (no CRLF corruption), suite run FROM origin = 529 passed / 91.24% | **CONFIRMED by content** |
| Working tree clean at close | `git status` shows only untracked helpers | CRLF-normalised per-file hash vs HEAD → 0 real changes | **CONFIRMED** |

## Session judgment

**L3 Artifacts.** One code commit, `d72c0df`, 4 files, +354/−8, fresh-clone verified:
`verifier.py` (3 distinct SKIP reason constants; runner-absent SKIPs instead of
FAILs for both pytest and jest; `_pytest_module_absent()` probe with a documented
COUPLING INVARIANT), `pr_publisher.py` (PR-body disclosure keyed off the gate
REASON, never the status), and **+12 tests** — 10 mocked, 2 unmocked real-repo
controls. Plus, uncommitted at the time of writing, this close-out, the
STRATEGY Session-029 block, and two BACKLOG corrections.

**L2 Goal.** Recorded at open: *implement §5 C2 + item 21 as one arc*.
Verdict: **PARTIAL — and deliberately so.** Steps 1–2 (verifier SKIP + PR-body
disclosure) are MET and landed. Steps 3–4 (item 21 token threading; live
site-copy check) are NOT done. This is not slippage: Yehor explicitly ruled that
item 21 must be traced before being touched, and split out if the trace showed it
reaching the App-credential path. The trace was done, the answer was "one hop, no
App-token machinery", and the work was still held for a separate arc pending his
bundle-or-split call. Scope discipline chose the partial.

**L1 Horizon.** Genuine progress, and the first non-documentation progress since
Session 027. The North Star is distance to a first paying Marketplace install; the
hosted path had three defects blocking it, and this session removed one of the two
remaining. **The needle moved but the hosted path still cannot publish a PR** —
C2 cleared the *verifier* blocker; the *auth* blocker (item 21) remains, and both
must clear before a hosted PR exists. Stated plainly so this commit is not read as
more progress than it is.

## Decisions made this close

1. **The injection defense was added over the memo spec, not to it.** Memo §7 said
   "detect the runner-absent signature". Tested literally, that string-match alone
   false-positives on repo-controlled output. Since a customer repo is adversarial
   input (ADR-013), the spec-conformant implementation was a verification bypass.
   The SKIP now requires a line-anchored match AND an independent import probe.
2. **The commit was made on Windows, not from the agent sandbox.** Verified hazard:
   sandbox git has `core.autocrlf` unset and there is no `.gitattributes`, so
   `git hash-object` from the sandbox produced a **CRLF** blob where HEAD stores
   **LF**. A sandbox commit would have rewritten all four files whole and polluted
   history permanently. This is now a standing rule (H20).
3. **Item 21 held out of the commit** despite touching the same file, per the
   split discipline. Traced, scoped, written up in BACKLOG — not implemented.
4. **The 3.10 sandbox run was never treated as the authorizing gate.** Yehor held
   that line across three turns; the gate was his 3.14.4 run.

## Weakest points, stated plainly

- **The hosted path still cannot publish a PR.** One of two blockers cleared. If
  this session is remembered as "C2 shipped", the memory will be flattering and
  wrong.
- **My first adversarial run produced a false alarm — six phantom "bypasses".**
  The patch was fine; my harness was broken (bare `python` in the sandbox is
  `/usr/bin/python`, which has no pytest, so the suites never ran and SKIP was
  correct). Had I reported the first result, I would have raised a false security
  alarm on my own work. The lesson is logged as H21.
- **The mocked negative control was insufficient and I shipped it that way
  initially.** A mocked `subprocess.run` also mocks the probe, so a broken probe
  would still have looked correct. It took Yehor's explicit demand for a negative
  control to surface that. The unmocked controls and the mutation check exist
  because he pushed, not because I got there alone.
- **`_run_jest` coverage is 81% with the jest timeout/pass/fail paths uncovered.**
  Pre-existing (no jest fixtures in the repo); my added line 890 IS covered. Not a
  regression, but it means the jest half of Gate 3 is thinner than the pytest half.
- **`_run_pytest` invokes bare `python`, not `sys.executable`.** Pre-existing and
  unchanged by this commit. It is currently *safe* only because the probe mirrors
  it exactly — which is why the COUPLING INVARIANT is documented in the code. A
  future well-intentioned cleanup of one without the other would break the gate.
- **UNVERIFIED — the live site-copy check (memo §7 step 4) was never done.** No
  claim about what the deployed `callmed-landing` site currently says about
  test-suite verification has been checked this session. It remains open.
- **UNVERIFIED — nothing about the hosted image was re-tested this session.** C2
  is verified by unit/integration tests on two machines, not by a `fly ssh` run
  against the live image. The last live confirmation was Session 027.
- **The 110-char foreign credential is still unrotated**, five sessions running.

## File manifest

**Committed this session (`d72c0df`, verified on origin):**
- `src/patchward/verifier.py`, `src/patchward/pr_publisher.py`
- `tests/test_verifier.py`, `tests/test_pr_publisher.py`

**Written at close, pending Yehor's Windows commit:**
- `memory/SESSION_CLOSE_2026-08-04.md` (this file)
- `.strategy/STRATEGY.md` (Session 029 log, close, calibration, heuristics)
- `memory/BACKLOG.md` (two corrections: §5 pointer now records IMPLEMENTED steps
  1–2 + commit hash; item 21 upgraded from "Suspected" to "CONFIRMED" with the
  full trace)

**Deliberately excluded:**
- `backlog_S5_C2_gate3_skip_and_disclose.patch` — redundant with `d72c0df`; delete
- `COMMIT_MSG_S5_C2.txt` — consumed by `git commit -F`; delete
- `backlog28_startup_credential_guard.patch` — item 28, still pending, keep untracked
- `Patchward_Counsel_Briefing_Packet_2026-08-03.pdf` — item 12 material, keep

**FLAGGED — reference-only artifact, H18 second occurrence:**
- `memory/Patchward_Turning-Point_Industrial-Plan_2026-07-16.md` is **untracked on
  origin** but referenced by **five tracked documents** (`SESSION_CLOSE` 07-22,
  07-24, 07-27, 08-01 and `.strategy/STRATEGY.md` L77). 25.8 KB, contains no
  credential-shaped strings, and is **not gitignored** — so this is an accidental
  omission, not a deliberate exclusion. Anyone cloning the repo gets five dangling
  references to a document that does not exist. **Recommend tracking it**; left to
  Yehor because it is his strategic document, not an agent artifact.

## Next-session opening prompt

Copy-pasteable. Every claim below was verified at close; it is still re-verified at
open on purpose, because claims go stale between sessions.

```
Resume Patchward. Open via the session-strategy-synthesis skill, grounding in
.strategy/STRATEGY.md — re-verify fresh, do not trust as-is. Per H13/H14/H16 that
includes this prompt's own claims, the backlog entries' premises, anything I assert
from memory, and any hash/diff mismatch (normalise line endings FIRST — mixed CRLF
tree; use CRLF-normalised diffs to tell real change from noise).

RECURRING TRAP (H14, now 5x): do NOT accept any assertion that a memory file is
"stale", "predates" recent items, or that a figure is the current baseline —
VERIFY against origin (ls-remote + fresh clone), by CONTENT, before acting. In
Session 029 the asserted "483 passed" baseline was five sessions stale; the live
figure is now 531/3 skipped/91.11% on Python 3.14.4.

H18 (PROMOTED, applies to INHERITED references too): when anything points at a
file, confirm that file is tracked on origin — not just that a pointer exists.
Session 029 found memory/Patchward_Turning-Point_Industrial-Plan_2026-07-16.md
cited by FIVE tracked documents while itself untracked for 19 days.

H20 (HARD RULE): the agent must NEVER git add/commit from its sandbox on this
repo. Sandbox git has core.autocrlf unset and there is no .gitattributes, so it
stores CRLF blobs where HEAD stores LF — a sandbox commit rewrites whole files
and pollutes history irreversibly. Agent prepares and verifies; Yehor stages and
commits on Windows. Tripwire before every push: `git diff --cached --stat` must
show the expected small line counts, not thousands.

Session 029 closed. Per H2 this prompt cites NO closing hash. Establish real HEAD
yourself (git ls-remote + fresh clone), then confirm the close landed BY CONTENT:
  * memory/SESSION_CLOSE_2026-08-04.md exists AND is tracked on origin;
  * .strategy/STRATEGY.md contains "Session log (continued) — Session 029" AND a
    Session-029 CLOSE entry with calibration 10/10 and heuristics H20/H21/H22;
  * memory/BACKLOG.md §5 pointer reads "IMPLEMENTED 2026-08-04 (Session 029),
    steps 1-2 only, commit d72c0df";
  * memory/BACKLOG.md item 21 header reads "CONFIRMED hosted-path breakage" (not
    "Suspected") and carries the TRACE 2026-08-04 paragraph.
If any is missing, the close did not fully land — settle that first.

VERIFIED STATE at close (re-verify, don't trust):
  * §5 C2 steps 1-2 SHIPPED as commit d72c0df — verifier SKIPs (not FAILs) when
    the test runner is absent, with a distinct RUNNER_ABSENT_REASON, and the PR
    body discloses it. Hardened with a forged-signature injection defense
    (independent import probe, fail-closed) because the memo-spec string-match
    alone was tested and found to be a verification BYPASS. Adversarial pass done
    at BACKLOG 19 tier: 6 real-repo attacks repelled, mutation check confirms the
    negative controls have teeth.
  * THE HOSTED PATH STILL CANNOT PUBLISH A PR. C2 cleared the verifier blocker.
    The auth blocker (item 21) remains. Both must clear. Do not read d72c0df as
    more progress than that.
  * Item 21 TRACED, NOT WRITTEN — one hop, does NOT touch App-token minting.
    webhook.py:276/282/302 already mint/register/clone with the installation
    token; webhook.py:333-338 passes it to run_repo_pipeline, which DROPS it
    (pipeline.py:68); PRPublisher._push_token() reads GITHUB_TOKEN from
    CredentialProxy and Fly has no such secret (credential_proxy.py:68). The fix
    is a push_token param on PRPublisher.__init__ taking precedence over the proxy
    lookup, passed at pipeline.py:234 — NOT a static PAT on Fly. CLI path keeps
    its env token unchanged.
  * Item 22 deferred, dormant, undecided by construction of C2. Do NOT touch it.
  * Item 28 PATCH-PREPARED, NOT LANDED (backlog28_startup_credential_guard.patch
    in repo root; last tested 526/90.75%).

PRIORITY (North-Star = distance to first paying Marketplace install):
  * P0 — item 21, its own arc. Agent-startable; the trace is done, so this is
    implementation not investigation. Add push_token to PRPublisher (precedence
    over the proxy lookup), thread the already-minted token from
    run_repo_pipeline, and prove by test that the CLI path is unaffected. Full
    suite as the gate ON YEHOR'S 3.14.4 — the sandbox 3.10 run is ADVISORY ONLY.
    §2 line-by-line + adversarial pass, same tier as BACKLOG 19: this touches the
    credential path, so the adversarial brief is "can the token leak into a log,
    a URL, .git/config, or an exception message?" Scoped git add (never -A), diff
    before commit, commit -F (not -m), push, ls-remote, THEN the adversarial pass.
  * P0b — memo §7 step 4, the live site-copy check. LIVE WEB task (browser tools
    against the deployed callmed-landing site), NOT a repo grep. Correct any claim
    that hosted fixes are test-suite-verified; if no such claim exists, say so
    explicitly. Never done; still open.
  * P1 — item 22 A/B/C (Yehor's call, only forced by a later §5 upgrade to A);
    item 12 CRA/GDPR counsel (calendar-driven, ~2026-09-11).
  * P2 — land item 28 if still unlanded; items 18, 24.
  * P3 — infra debt, no live exposure: 17, 26.

YEHOR-OWNED, independent:
  * ROTATE the 110-char foreign credential at its source; check whether the same
    paste reached another secret. Open five sessions running.
  * Decide whether to track memory/Patchward_Turning-Point_Industrial-Plan_
    2026-07-16.md (five tracked docs cite it; it is untracked and NOT gitignored).
  * Item 22 A/B/C (parked, correct).

Known-UNVERIFIED at close:
  * The live site copy (memo §7 step 4) — never checked, no claim made.
  * The hosted image itself — C2 is proven by tests on two machines, NOT by a
    `fly ssh` run against the live image. Last live confirmation was Session 027.
  * _run_jest coverage is thin (jest timeout/pass/fail paths uncovered,
    pre-existing — no jest fixtures in the repo).

Ask Yehor what he wants this session before starting — though P0 is fully
unblocked and agent-startable.
```
