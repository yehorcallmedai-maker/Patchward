# Patchward — Next Session Start Prompt (written at Session 033 close, 2026-08-11)

Resume Patchward. **Open via the `session-strategy-synthesis` skill**,
grounding in `.strategy/STRATEGY.md` — re-verify its claims fresh, do not
trust them as-is, including everything in this file. They were verified at
Session 033 close (2026-08-11) and can go stale between sessions.

## Grounding first, in order (H13 / H14 / H16)

1. **H13/H16** — trust only remote-ref ops and hosted content for git
   state; local mount reads and `git status` on this Windows-origin tree
   are noisy-by-default. Run `git ls-remote origin main` yourself for
   BOTH repos now in scope: Patchward (last known HEAD `76274e4` —
   **may have moved if Yehor cleared the index.lock and committed the
   Session 033 memory files after this prompt was written; check first**)
   and the new sibling `patchward-landing` (HEAD `599ed04` as of the
   Session 033 addendum — confirmed via `git ls-remote` AND a byte-level
   raw-content fetch, both Tier-0).
0. **[NEW, check FIRST, before anything else]** — at Session 033's close,
   the Patchward repo had a stale `.git/index.lock` that was actively
   BLOCKING Yehor's commit (not just a benign artifact, as Session 032 had
   assumed). If this session opens and the Patchward repo still shows
   uncommitted Session 033 memory files (`SESSION_CLOSE_2026-08-11.md`,
   `NEXT_SESSION_PROMPT_2026-08-11.md`, the `.strategy/STRATEGY.md`
   update), check whether the lock was cleared and the commit landed. If
   not, that commit is still the most basic piece of unfinished business
   from last session — surface it before anything else.
2. **[NEW this session]** — the same "don't trust the rendered state,
   re-verify from a fresh source" discipline now applies beyond git: a
   SaaS dashboard (Cloudflare) showed an action as successful in-session
   that had silently reverted by reload. If anything about `patchward.dev`
   or Cloudflare project state is load-bearing this session, re-check it
   live, don't inherit the "Active/SSL enabled" verdict below without a
   fresh look.
3. **H14** — do not accept any "already done / N sessions running /
   baseline is X" claim on say-so; trace it to its origin before acting.
4. **H8/H18** — diff every memory file against a fresh clone before
   trusting it, including the newly-created `patchward-landing/memory/`
   files (copied in at this close, not yet committed as of this writing —
   confirm they landed before citing them).

## H20 — HARD RULE (staging is Yehor's, not the agent's) — now applies to BOTH repos

The agent must **NEVER** `git add` / `commit` / `push` from its sandbox on
either the Patchward repo or `patchward-landing`. For Patchward, Yehor
stages and commits on Windows using:

> **`D:\Dev\Projects\Patchward\.venv\Scripts\python.exe`** (Python 3.14.4,
> nested inside the repo, gitignored — NOT a sibling folder).

`patchward-landing` has no equivalent Python venv (it's a static Astro
site) — Yehor commits it directly via `git`/GitHub Desktop/whatever he
normally uses on Windows; its own README states the same H20-equivalent
rule in its "Standing rules for this repo" section.

## Standing heuristics worth knowing (full evidence in STRATEGY.md)

- **H1/H2/H8/H9-cand** — git state: remote-ref/clone/hosted only.
- **H14** — re-derive inherited claims; don't accept "done" on narration.
- **H16** — CRLF-normalise before believing a diff.
- **H18** — verify referenced/pointed-to files are actually tracked.
- **H20** — never stage/commit from the agent; now spans two repos.
- **H26 [standing]** — byte-check any encoding/corruption claim before
  recording it. **Still unresolved on `f653e77:webhook.py`** — see P0(a).
- **[candidate, 2026-08-11]** — Cloudflare Workers and Pages projects can
  share an identical name as fully independent resources; whichever holds
  the zone's Custom Domain binding wins regardless of which has the real
  content. Check the full Workers & Pages resource list before assuming a
  wrong-content symptom is a build or DNS-propagation issue.
- **[candidate, 2026-08-11]** — a SaaS dashboard's "success" state
  (domain attached, action completed) needs a fresh-reload re-check, not
  same-session trust — one reattachment tonight silently reverted and was
  only caught this way.

## Verified state at Session 033 close (re-verify anyway)

- **Patchward repo**: HEAD `76274e4`, unchanged this session — no new
  commits landed here. Pre-existing untracked debt (six-ish files, see
  SESSION_CLOSE_2026-08-11.md) still sitting, still Yehor's call.
- **`patchward-landing` repo** (NEW): HEAD `fcc0af4`, clean working tree,
  pushed to `github.com/yehorcallmedai-maker/patchward-landing`. Astro 7,
  static output, `src/data/facts.yaml` as the single source of truth for
  every number on the site.
- **`patchward.dev` is LIVE and correct**: Cloudflare Pages Custom Domain
  status "Active" / "SSL enabled"; fresh fetch confirmed real branded
  content; `/facts` renders all 8 canonical claims; the account's
  Workers & Pages list shows exactly one `patchward-landing` resource
  (the broken duplicate Worker that was hijacking the domain was deleted
  this session, byte/screenshot-confirmed gone).
- **GitHub profile README**: Yehor applied his own further-evolved
  version; the specific overclaim this session flagged (false "PR merged"
  on checkdmarc) is confirmed corrected in the live version.
- **LinkedIn**: explicitly still in progress, out of scope, Yehor's own
  words — do not assume any state about it.

## Open items and priorities

- **P0 (a), carried from Session 032, now 2 sessions untouched**: fix the
  `f653e77:webhook.py` encoding regression (BOM + 29 mojibake em-dashes).
  Recipe already recorded in Session 032's close doc.
- **P0 (b)**: apply the corrected Gate-3 copy to live `callmedai.com` —
  drafted this session (`patchward_site_copy_check_2026-08-11.md`,
  currently only in this agent's temporary scratchpad — ask for it to be
  regenerated if it's needed and not already saved somewhere durable).
- **P1**: decide the `multi-model-research-synthesis` skill's permanent
  home — this was asked and left open across this entire session.
- **P1**: decide the six-ish untracked root artifacts in the Patchward
  repo (track / gitignore / delete).
- **P1**: `patchward-landing` currently deploys by manual
  `wrangler pages deploy` — consider wiring Cloudflare Pages' own
  (working) Git-integration auto-deploy now that the conflicting broken
  Worker is gone, so future pushes go live without a manual step.
- **P2**: remaining `patchward-landing` lookbook pages (`/how-it-works`,
  `/verification`, `/data-boundary`, `/examples`), the PR-body-template
  artifact, the CLI-output chapter, the ~1.2s Gate-3 motion sequence.
- **P2**: the two BACKLOG 28 design questions from Session 032, still
  undecided (absence-of-credential boot failure; `/healthz` validity
  assertion).

## Then

No agent-startable code work is queued as an obvious top pick — P0(a) is
the oldest debt (tool-repo security-adjacent), P0(b) is the oldest
site-copy debt, but both are real work, not quick picks. Start by
grounding per the checklist above, confirm both repos' git state and
`patchward.dev`'s live state fresh, then **ask Yehor what he wants to do
this session.**
