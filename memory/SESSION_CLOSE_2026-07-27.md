# Session Close — Patchward — 2026-07-27 (Session 025)

## Gate status (two-pass hard check, all CONFIRMED)
| Claim | Pass 1 (fresh clone) | Pass 2 (independent) | Verdict |
|---|---|---|---|
| Memory close pushed | ls-remote → 9e70f36 | mount HEAD == origin/main == 9e70f36 | CONFIRMED |
| BACKLOG 19 fix in tree | credential_reset_args in git_credentials.py + worktree_common.py at HEAD | working tree clean of real changes | CONFIRMED |
| Item 19 CLOSED in memory | CLOSED-2026-07-27 marker in HEAD BACKLOG.md | byte-identical to delivered reconciliation | CONFIRMED |
| H11/H12 logged | both in HEAD STRATEGY.md | — | CONFIRMED |
| Fix deployed + live | Fly image sha256:ac54d18a, machine 7841600fd5e7e8 | /healthz 200 {"status":"ok"} via WebFetch AND real Chrome read | CONFIRMED |
| Working tree sealed | — | no real uncommitted changes, no index.lock, 1 benign untracked doc | CONFIRMED |

## Session judgment
- **L3 Artifacts:** commits 37b3bfd (base fix) → dee84e1 (five-finding follow-up) → 9e70f36 (memory close), all fresh-clone-verified byte-identical; Fly deploy live on the new image. Suite 505/3/15 @ 90.62% (Yehor's machine, Py 3.14.4); 503/2/15 in-sandbox.
- **L2 Goal:** close BACKLOG 19 — **MET** as a testable outcome (committed → pushed → deployed → /healthz-green), not merely code-written.
- **L1 Horizon:** real progress on the pre-distribution Exposure Gate. Credential-DELIVERY boundary shut; the review enumerated adjacent boundaries (21/22/23/24) so the frontier is mapped, not hidden. Not motion-without-progress.

## Decisions made this close
- BACKLOG 19 reconciled to CLOSED only after state (c) — deploy + /healthz-green — reached, not at push.
- The three robustness spin-offs (22/23/24) were NOT folded into the security commit; each is its own unit (H11).
- Item 22 (Gate 3 credential inheritance) chosen as the next security priority, ahead of 18/23/24, on severity (demonstrated ANTHROPIC_API_KEY exposure to adversarial repo code).

## Weakest points, stated plainly
- **#4's fix is review-verified, NOT test-proven.** The cross-thread scrub race is not deterministically reproducible through the public API; the accompanying concurrency test is an honestly-labeled non-discriminating smoke test. The one-line tuple() snapshot is correct by construction (GIL-atomic), but the suite does not prove it red-on-revert. This is the single claim in the whole arc that rests on construction + review rather than a discriminating test.
- **BACKLOG 21 (dead github_token param) is open and unproven end-to-end.** The webhook path likely cannot push a PR at all today (reads a nonexistent Fly GITHUB_TOKEN secret). A post-deploy webhook smoke test may fail at PR-push for THIS reason, not a regression. Not verified live — code-path-inferred only.
- **The deployed image → dee84e1 link is by build-provenance, not a stamped git SHA.** fly image show shows a digest, not a git label; the chain (built from the dee84e1 working tree, digest matches build manifest, /healthz green) is sound but not cryptographically tied to the commit.
- **Item 22 is a proven, larger exposure that is now OPEN.** Closing 19 does not reduce 22's severity — it sequences it. The site/product still ships adversarial-repo-code-with-live-API-keys until 22 lands.

## File manifest
- Committed this session: src/patchward/{cli,credential_proxy,git_credentials,worktree_common}.py, tests/{test_git_credentials,test_fix_worktree}.py (dee84e1); memory/BACKLOG.md, .strategy/STRATEGY.md (9e70f36).
- Deliberately excluded: memory/Patchward_Turning-Point_Industrial-Plan_2026-07-16.md (untracked, never tracked, benign); ~53 CRLF-phantom files (sandbox core.autocrlf artifact, clean on native git).

## Next-session opening prompt
Resume Patchward. Open via the session-strategy-synthesis skill, grounding in
.strategy/STRATEGY.md — re-verify fresh, do not trust as-is (claims can go
stale between sessions).

Session 025 closed clean at main @ 9e70f36, confirmed via fresh clone +
ls-remote + mount HEAD match. BACKLOG 19 (GITHUB_TOKEN exposure) is CLOSED:
committed (37b3bfd base + dee84e1 follow-up), deployed to Fly image
sha256:ac54d18a, /healthz green confirmed by WebFetch AND a real browser read.
Five findings closed across the original trace + three adversarial passes;
final pass 0 leaks/0 blockers with 3 robustness spin-offs (22/23/24). The
concurrency-scrub fix (#4) is review-verified, NOT test-proven — do not
re-label it as test-proven.

Next security priority is BACKLOG 22 (Gate 3 runs the cloned adversarial
repo's own test suite unsandboxed with ANTHROPIC_API_KEY + other creds in the
inherited os.environ — demonstrated key exposure to attacker-controlled code,
no race needed). Run it SCOPE-ONLY first per H11/H12: trace and quote the real
source, enumerate which creds are in os.environ at Gate 3 exec time on both
paths, lay out the sandbox-vs-scrubbed-env design options WITHOUT choosing,
surface the decision for Yehor, stage nothing. Expect its own pass to spawn
25/26 (H11) — budget for it.

Also open, lower priority: 21 (dead github_token param — webhook may not push
a PR at all; will surface if a webhook smoke test is run — NOT a regression),
23 (remaining unscrubbed error sinks), 24 (unbounded _RUNTIME_CREDENTIALS
growth), 18 (marketplace_purchases retention gap), 17 (scanner image rebuild —
deferred, needs Yehor's explicit trigger). BACKLOG 12 (CRA/GDPR) still awaits
qualified counsel — ~46 days to the 2026-09-11 reporting-obligation date.

No agent-startable code work is queued beyond BACKLOG 22 (scope-first), 21,
18, 23, 24. Ask Yehor what he wants this session before starting.

## Heuristics carried / added
- H11 (PROMOTED): an adversarial pass on one boundary enumerates adjacent ones — budget every security close to spawn successors; keep each spin-off its own diff.
- H12 (PROMOTED): adversarial passes on internet-facing credential code run until zero leaks/blockers; some correct fixes are not unit-testable — record as construction-verified, never fabricate a discriminating test.
- H1/H2/H8 held; H10-candidate applied (browser-corroborated /healthz), no new WebFetch failure, stays candidate.
