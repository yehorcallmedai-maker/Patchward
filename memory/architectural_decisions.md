# RepoMend — Architectural Decision Log

## Format
ADR-NNN | Date | Decision | Rationale | Status | Approved by

---

## ADR-018 | 2026-06-22 | HTTPS + PAT for git push — no SSH or gh CLI in Phase 5

**Decision:** `git push` in Phase 5 uses HTTPS with `GITHUB_TOKEN` embedded in the
remote URL (`https://oauth2:<token>@github.com/<owner>/<repo>.git`). SSH key management
and `gh` CLI are deferred out of Phase 5 scope.

**Rationale:** HTTPS + env-var token requires no new binary dependencies and fits the
existing `CredentialProxy` pattern. Adding SSH key lifecycle or a `gh` dependency would
introduce new trust-boundary questions out of scope for the minimal Phase 5 build.
`httpx` 0.28.1 confirmed available as a transitive dependency of the `anthropic` SDK —
no new `pyproject.toml` entry needed for the GitHub API POST call.

**Status:** Approved — signed by Yehor 2026-06-22 (KS-P5-01)

---

## ADR-019 | 2026-06-22 | All RepoMend PRs open as draft — human must promote

**Decision:** Every PR opened by RepoMend sets `draft: true`. The human reviewer must
explicitly mark it ready-for-review. This is a safety invariant, not a configuration
option. A one-time retry at `draft: false` is permitted when the GitHub API returns 422
indicating draft PRs are unavailable (GitHub Free private repos) — this is an operational
workaround, not a policy exception. The intent is always draft.

**Rationale:** Auto-merge is prohibited by ADR-003. `draft: true` enforces the human gate
at the GitHub UI level in addition to the code-level invariant. A non-draft PR could be
merged immediately by automation (merge queue, CI bot), bypassing the human review intent.
The retry path must not be cited as precedent for loosening the invariant.

**Status:** Approved — signed by Yehor 2026-06-22 (KS-P5-01)

---
## ADR-015 | 2026-06-16 | Verifier as deterministic subprocess wrapper, not LLM agent
**Decision:** Verifier is not a Claude SDK agent. It is a plain Python class that calls
subprocess tools and applies deterministic gate logic. No model invocation.
**Rationale:** Verification correctness must be auditable without model variance. A
non-deterministic verifier introduces an untestable component into the trust chain.
LLM judgment is inappropriate for a gate that is supposed to catch LLM errors.
**Status:** Confirmed
**Approved by:** Yehor 2026-06-16

## ADR-016 | 2026-06-16 | All three Verifier gates always run — no short-circuit on FAIL
**Decision:** Verifier evaluates all three gates regardless of intermediate failures.
Gate 1 FAIL does not skip Gate 2 or Gate 3.
**Rationale:** Short-circuiting after Gate 1 FAIL prevents false-positive-candidate
detection, which requires Gate 2 and Gate 3 results. The overhead of continuing is
negligible; the false-positive signal is load-bearing for Phase 5 HITL PR labelling.
**Status:** Confirmed
**Approved by:** Yehor 2026-06-16

---

## ADR-001 | 2026-06-10 | Claude Agent SDK as agent foundation
**Decision:** Use `claude-agent-sdk` (PyPI) as the orchestration layer.
**Rationale:** Ships managed agent loop, automatic context compaction,
built-in tools, MCP client support, subagent isolation, lifecycle hooks.
Eliminates boilerplate. Maps directly to scanner/fix/verify pattern.
**Status:** Confirmed
**Approved by:** Yehor

## ADR-002 | 2026-06-10 | Local-first, no SaaS
**Decision:** All repo processing happens on the user's machine.
Code never leaves the machine boundary.
**Rationale:** Primary differentiator vs repomend.com, Aikido, Snyk.
Required for compliance-adjacent buyers (Formalize target profile).
**Status:** Confirmed
**Approved by:** Yehor

## ADR-003 | 2026-06-10 | No auto-merge, ever
**Decision:** All fixes staged as draft PRs. Human merges.
**Rationale:** Safety ceiling. Non-negotiable per Keystone Standing Rules.
**Status:** Confirmed
**Approved by:** Yehor

## ADR-004 | 2026-06-10 | Scanners as MCP/Bash tools, not reimplemented
**Decision:** Semgrep, Bandit, ESLint, pip-audit, npm audit, Trivy,
OSV-Scanner wired as thin wrappers. Output normalized to SARIF.
**Rationale:** Avoid reimplementing what ships production-hardened.
Faster to Phase 3, better scanner quality.
**Status:** Confirmed
**Approved by:** Yehor

## ADR-010 | 2026-06-11 | Docker Desktop as Phase 2 sandbox primitive
**Decision:** Docker Desktop on Windows as the sandbox for all scanner subprocess
execution in Phase 2.
**Rejected alternatives:**
- `@anthropic-ai/sandbox-runtime` — Node package; incompatible with Python-first project without a runtime bridge
- `bubblewrap` — Linux-only; eliminated by Windows dev environment (confirmed by cp1251 defect, PowerShell throughout sessions 001–002)
- `gVisor` — deferred to Phase 3+ hardening on top of Docker
**Rationale:** Filesystem + network isolation in one primitive, runs on Windows,
maps directly to Tier 2 hardening spec in the architecture doc.
**Implementation notes:**
- Base image: `python:3.12-slim`; digest locked at end of KS-P2-02
- Per-scanner network allowlist (not global `--network none`) to preserve pip-audit/npm audit functionality
- `docker info` fail-fast at CLI startup — same pattern as `_require_tool()` in scanner.py
**Status:** Confirmed
**Approved by:** Yehor

## ADR-011 | 2026-06-11 | Flag P2-B deferred — Docker not on PATH
**Decision:** KS-P2-02 accepted as structurally complete without digest pin.
Trust invariants verified by unit tests (102/102 passing). Digest pin and
AC-P2-01 integration test deferred until Docker Desktop installed on dev machine.
**Rationale:** Trust invariants (`--rm`, `:ro`, credential exclusion, per-scanner
network policy) are proven structurally by unit tests that mock the subprocess layer.
The digest pin is an operational hardening step; its absence does not compromise
architectural correctness. Blocking KS-P2-03/04 on a missing install wastes momentum.
**Blocker:** Must close before KS-P2-08 (Keystone Report Phase 2).
**Status:** Open — Flag P2-B
**Approved by:** Yehor

## ADR-009 | 2026-06-11 | Mandatory scanner probe in INTAKE template
**Decision:** Every future INTAKE contract that involves scanner rule plants must include
a mandatory pre-step: run scanner on a 3-line snippet, capture exact `ruleId` output,
paste verbatim into the test contract before build clock starts.
**Rationale:** Phase 1 ssl rule ID required a second diagnostic probe and a non-blocking
flag that stayed open until KS-P1-03 normalizer wiring. Exact rule IDs in the contract
eliminate all ambiguity before wiring begins. Confirmed via §6 of Keystone Report Phase 1.
**Status:** Confirmed — applies from Phase 2 INTAKE onward
**Approved by:** Yehor

## ADR-012 | 2026-06-12 | Fix-Gen context scoping strategy
**Decision:** Orchestrator constructs the Fix-Gen prompt. Fix-Gen receives a scoped JSON
object: `{file_path, rule_id, message, level, snippet_lines: [start, end], evidence}`.
Orchestrator reads `snippet_lines` from SARIF `region` and passes ±5 lines of context.
Fix-Gen may request additional lines via `read_lines(file, start, end)` tool call;
Orchestrator validates range is within the same file.
**Rejected:** Passing full file contents — violates C-P3-01 and increases injection surface.
**Status:** Confirmed (INTAKE Phase 3)
**Approved by:** Yehor

## ADR-013 | 2026-06-12 | iptables OUTPUT egress enforcement (Option A)
**Decision:** `--cap-add NET_ADMIN` granted to scanner container for PYPI_ONLY/NPM_ONLY
policies. Entrypoint script applies default DROP OUTPUT policy, resolves destination IPs
at startup (before DROP applied), then inserts ACCEPT rules for resolved IPs on 443/80.
**Rejected:** DNS-based blocklist (Option B). Reason: bypassed by raw IP addresses.
Threat model includes prompt-injection payloads that hardcode IPs to evade DNS controls.
iptables at IP/CIDR layer is the actual deny-by-default model; DNS is not.
Sidecar proxy deferred to Phase 6 (parallel worker pool, shared egress policy).
**Phase 6 note:** Sidecar egress proxy is the more scalable pattern for multi-repo parallel
runs. Not in scope for Phase 3. ADR to be revisited at Phase 6 INTAKE.
**Status:** Confirmed (INTAKE Phase 3, Yehor 2026-06-12)
**Approved by:** Yehor

## ADR-014 | 2026-06-12 | Custom scanner base image (repomend-scanner)
**Decision:** Replace `python:3.12-slim` with a custom `repomend-scanner:0.1.0` image
built from `docker/scanner.Dockerfile`. iptables and all scanner tools baked in.
**Why custom image is required:**
  1. `python:3.12-slim` does not include iptables binary. Runtime `apt-get install`
     is impossible: iptables rules cannot be applied before the binary exists, but
     installing requires network access before rules are set — chicken-and-egg.
  2. Scanner binaries baked in at same time: one build, not two; no second pass
     over the same artifact in Phase 6.
  3. pip-audit's PyPI calls become pure vulnerability-DB queries, not package installs
     — shrinks the PYPI_ONLY allowlist scope.
  4. Reproducibility: pinned versions at image build time = deterministic Phase 4
     golden dataset.
**Pinned tool versions baked into repomend-scanner:0.1.0:**
  - semgrep:   1.165.0  (host probe 2026-06-12)
  - bandit:    1.9.4    (PyPI latest stable 2026-06-12)
  - pip-audit: 2.10.1   (PyPI latest stable 2026-06-12)
  - eslint:    8.57.1   (intentional — last pre-flat-config; 9+/10 requires eslint.config.js)
  - node:      20 LTS   (nodesource setup_20.x)
  - python:    3.12     (base image)
**ESLint version note:** ESLint 9+ requires flat config (`eslint.config.js`). Arbitrary repos
  will not have one. ESLint 8.x handles unconfigured repos gracefully. Do not upgrade
  to 9.x/10.x without adding `--no-eslintrc` or equivalent handling in scanner.py.
**Image pin:** sha256:578a8147c3604808a5c7e0f1649fc8e6a3a93610e02896d95cc36c388655a5bc
  Built 2026-06-12 (rebuild after entrypoint DNS fix). BASE_IMAGE in docker_sandbox.py updated.
  Defect fixed: entrypoint v1 applied iptables DROP before writing /etc/hosts — pip/npm DNS
  queries failed post-DROP. Fix: write /etc/hosts entries for allowlisted domains before DROP.
**Status:** Confirmed — image built and pinned 2026-06-12.
**Approved by:** Yehor

## ADR-005 | 2026-06-10 | Python package manager: uv
**Decision:** Use `uv` for all Python dependency management.
**Rationale:** 10–100x faster installs, integrated audit commands,
first-class lockfile support. Better fit for this stack than pip+venv.
**Status:** Confirmed
**Approved by:** Yehor

## ADR-006 | 2026-06-10 | Langfuse: cloud free tier for Phase 0
**Decision:** Use Langfuse cloud free tier for OTel tracing in Phase 0.
**Rationale:** Zero Docker overhead during foundations phase. Acceptable
tradeoff — Phase 0 has no sensitive repo data. Revisit for Phase 2
sandbox hardening where local-first constraint applies strictly.
**Status:** Confirmed
**Approved by:** Yehor

## ADR-007 | 2026-06-10 | Walking skeleton test target: fixture repo
**Decision:** Use a dedicated fixture repo owned by Yehor as the
Phase 0 single-repo scan target.
**Rationale:** Deterministic findings, controlled test contract,
predictable scanner output for SARIF normalization work.
**Status:** Confirmed
**Approved by:** Yehor

## ADR-017 | 2026-06-22 | git commit required on fix branch before mark_success()

**Decision:** `fix_gen.py` must call `git_commit_all(worktree_path, message)` after
`submit_fix` returns success and before returning `FixResult`. The commit is
created inside the worktree branch so the fix branch has at least one commit
of its own (separate from the parent repo's HEAD).

**Rationale:** Phase 5 will push the fix branch to GitHub and open a pull request.
`git push` requires at least one new commit on the branch relative to the base.
Currently Fix-Gen writes patches as uncommitted working-tree changes — the fix
branch is structurally identical to main at the git object level. Attempting to
push or open a PR against it would produce an empty diff. This pre-step closes
that gap before Phase 5 INTAKE is written.

**Implementation:**
- `git_commit_all(worktree_path, message)` added to `worktree_common.py`
  (`git add -A` → porcelain check → `git commit -m <message>`)
- Called in `fix_gen.py` `apply_fix()` after `_emit_pr_dict()`, before `return result`
- Commit message format: `fix(<rule_short>): <description[:60]> [repomend/<id[:8]>]`
- Raises `RuntimeError` if nothing is staged (Fix-Gen wrote no files — logic error)
- Raises `CalledProcessError` if git is unavailable or the commit fails

**Tests:** 5 unit tests in `test_fix_worktree.py` (`TestGitCommitAll`);
2 unit tests in `test_fix_gen.py` (commit called on success, not called on failure).

**Status:** CONFIRMED — implemented 2026-06-22, pre-step complete.

---

### ADR-020 — asyncio + Semaphore as concurrency model (Phase 6)
Use `asyncio` event loop with `AsyncAnthropic` and
`asyncio.Semaphore(n)` for bounded multi-repo concurrency.
`ThreadPoolExecutor` and `ProcessPoolExecutor` rejected.
All blocking subprocess calls wrapped in `asyncio.to_thread()`.
Target runtime: Python 3.12+ (ProactorEventLoop, Windows-compatible).
Status: **APPROVED 2026-06-23** (Phase 6 INTAKE signature).

### ADR-021 — Prompt caching on Fix-Gen system prompt (ephemeral)
Add `cache_control: {type: ephemeral}` to the Fix-Gen system prompt
message block. System prompt is large (~2k tokens), stable across
repos, repeated N times per batch. Cache TTL: 5 minutes.
Expected saving: ~90% of system-prompt token cost on cache hits.
Status: **APPROVED 2026-06-23** (Phase 6 INTAKE signature).

### ADR-022 — [[repos]] array of tables with [github] fallback
Multi-repo config uses TOML `[[repos]]` array-of-tables.
`[github]` singleton is the fallback for backward compatibility.
Per-entry fields override `[github]` defaults field-by-field.
`Config.repos` always returns `list[RepoConfig]`.
Status: **APPROVED 2026-06-23** (Phase 6 INTAKE signature).

---

## ADR-020: asyncio Pipeline Architecture (Phase 6)

**Date:** 2026-06-23
**Status:** Accepted

**Decision:** `run_repo_pipeline()` is a single async function that owns the full
scan→fix→verify→PR sequence for one repo. `run_batch()` gathers N pipeline coroutines
under `asyncio.Semaphore(max_concurrent)` with `return_exceptions=True`.
Escaped exceptions are converted to error dicts so the caller always receives
exactly `len(cfg.repos)` result items.

**Rationale:** Uniform result list simplifies CLI summary table and run log iteration.
`return_exceptions=True` as defense-in-depth prevents one repo's crash from cancelling others.

---

## ADR-021: Prompt Caching Scope (Phase 6)

**Date:** 2026-06-23
**Status:** Accepted

**Decision:** Apply `cache_control: {"type": "ephemeral"}` to the Fix-Gen system
prompt block only. User message content (finding + file context) is not cached.

**Rationale:** The system prompt is large (~1.5k tokens), static across all Fix-Gen
calls in a session, and has high cache-hit probability. User messages are variable
(different findings, different file content) — caching them wastes cache slots.

---

## ADR-022: [[repos]] Config Shape (Phase 6)

**Date:** 2026-06-23
**Status:** Accepted

**Decision:** TOML `[[repos]]` array-of-tables. Per-entry fields (`owner`, `repo`,
`base_branch`) override `[github]` singleton field-by-field via `entry.get(field) or github.field`.
When no `[[repos]]` section exists, `load_config()` falls back to `[github]` singleton
as a single-entry repos list — backward-compatible with all Phase 1–5 configs.

**Rationale:** Field-merge (not full-replace) lets users specify only what differs
per repo (typically just `path` and `repo`), inheriting `owner` from `[github]`.
TOML array-of-tables is the idiomatic multi-value pattern and avoids TOML's
table-array-inside-inline-table restrictions.

---

## ADR-023 | 2026-06-23 | uv tool install as primary distribution method

**Decision:** Use `uv tool install` (not pipx) as the primary method for
distributing the `repomend` CLI to end users.

**Rationale:** The project already uses `uv` throughout for all dependency
management, virtual environment creation, and test execution. `uv tool install`
produces an isolated environment identical to `pipx install` without requiring
users to install a separate tool. `pyproject.toml` already declares
`[project.scripts] repomend = "repomend.cli:app"` — no additional packaging
work is required. Consistency across dev and install workflows reduces
onboarding friction.

**Status:** Approved — signed by Yehor 2026-06-23 (KS-P7-01)

---

## ADR-024 | 2026-06-23 | Skip Docker distribution image at Phase 7

**Decision:** No RepoMend application Docker image is produced in Phase 7.
The existing `repomend-scanner:0.1.0` image is an internal sandbox runtime
primitive, not a distribution artifact. `uv tool install` is sufficient for
the target user profile (solo developer, local machine).

**Rationale:** Distributing RepoMend itself as a Docker image would require
Docker-in-Docker or volume-mount orchestration to share the target repo between
the scanner sandbox container and a RepoMend container — a fragile distribution
pattern that adds complexity with no current benefit. Docker distribution image
is deferred to Phase 8+ contingent on multi-user demand.

**Status:** Approved — signed by Yehor 2026-06-23 (KS-P7-01)

---

## ADR-025 | 2026-06-23 | Single-user config; repomend.toml.example as template

**Decision:** `repomend.toml` is a machine-local file. No git-tracked shared
config repo, dotfiles pattern, or substitution tooling is introduced in Phase 7.
A `repomend.toml.example` with full inline comments on every field covers the
template use case: `cp repomend.toml.example repomend.toml` and fill in values.

**Rationale:** RepoMend is a solo project. `[[repos]]` `path` fields are
machine-local and cannot be shared across machines without substitution tooling.
The template pattern is zero-friction and sufficient for the target user profile.
Team config sharing deferred to Phase 8 if multi-user demand arises.

**Status:** Approved — signed by Yehor 2026-06-23 (KS-P7-01)

---

## ADR-026 | 2026-06-23 | docs/ folder extended; MkDocs deferred

**Decision:** Phase 7 documentation deliverables are `docs/user_guide.md`
(installation, quick start, config reference) and an updated `README.md`.
The existing `docs/` folder is extended — no new tooling or site generator.
MkDocs and a public documentation site are deferred to Phase 8+.

**Rationale:** `docs/` already exists with intake contracts for Phases 1–6.
Extending it is zero-friction. MkDocs adds a site-generation layer, theme
dependency, and deployment pipeline that is unjustified for a solo local-first
tool at Phase 7. The user guide content is more valuable than the delivery
mechanism at this stage.

**Status:** Approved — signed by Yehor 2026-06-23 (KS-P7-01)

---

## ADR-027 | 2026-07-07 (retroactive, 2026-07-13) | Rename RepoMend to Patchward

**Decision:** Rename the project from RepoMend to Patchward across the
entire tree: `src/repomend/` → `src/patchward/`, package name, CLI entry
point, config file (`repomend.toml` → `patchward.toml`), docs, and README.

**Evidence:** commit `c27ea40` (2026-07-07, "Rename RepoMend to Patchward —
repomend.com is a live unrelated competitor in the same category"),
135 files changed. Follow-up doc fixes in `6ebe135` and `e6bb75e`
(2026-07-08) corrected remaining RepoMend branding in `user_guide.md` and
`README.md`.

**Rationale (reconstructed from the commit message — no separate design
doc found):** `repomend.com` is a live, unrelated competitor product in
the same category. Continuing under the RepoMend name risked trademark/
confusion issues at exactly the point the project was moving from a local
CLI tool to a hosted product with a public-facing webhook and a GitHub
Marketplace listing — i.e., the rename timing is not incidental, it
precedes the webhook/billing work (`0bb0286`) by two days.

**Consequence:** every ADR before ADR-027 in this log refers to "RepoMend"
by name; those decisions still hold, only the name changed. No functional
behavior changed in `c27ea40` itself (confirmed: diff is renames + import
path updates only, 743 insertions / 741 deletions on a 135-file commit is
consistent with a mechanical rename, not new logic).

**Status:** Accepted (retroactive, reconstructed from git archaeology,
2026-07-13). Not yet reviewed by Yehor — carries the same "proposed"
status as the rest of this audit until signed off.

---

## ADR-028 | 2026-07-09 (retroactive, 2026-07-13) | FastAPI + Uvicorn + PyJWT for the webhook receiver

**Decision:** Build the GitHub App webhook receiver (`src/patchward/
webhook.py`) on FastAPI + Uvicorn, with PyJWT for GitHub App JWT signing,
as a new `webhook` optional-dependency group (`fastapi>=0.115`,
`uvicorn[standard]>=0.30`, `pyjwt[crypto]>=2.9`, `httpx>=0.27`) —
isolated from the CLI's core dependencies.

**Evidence:** commit `0bb0286` (2026-07-09), `pyproject.toml` lines 21-29
(KS-TRACE comment: "only needed to run src/patchward/webhook.py ... The
CLI (patchward scan|fix|batch) does not import this module and does not
need these installed"); `src/patchward/webhook.py`, `github_app_auth.py`.

**Rationale (reconstructed — no separate design doc found in the repo,
see Known Documentation Gap in STATE.md):** async-native web framework
needed for a receiver that clones repos and awaits an LLM pipeline per
request without blocking; `httpx` for the GitHub API token exchange;
`pyjwt[crypto]` for RS256 App JWT signing per GitHub's App auth spec.
Keeping this as an optional extra (not a core dependency) preserves the
existing single-user local CLI as a zero-extra-dependency install path —
consistent with ADR-024/025's Phase 7 "keep the CLI lightweight" stance.

**Status:** Accepted (retroactive, reconstructed from git archaeology,
2026-07-13). Not yet reviewed by Yehor.

---

## ADR-029 | 2026-07-09 (retroactive, 2026-07-13) | Fly.io as the webhook deployment target

**Decision:** Deploy the webhook receiver to Fly.io (`patchward-webhook.fly.dev`)
via `docker/webhook.Dockerfile` and `fly.toml`, with a mounted volume
(`patchward_data` → `/data`) for `installations_db.py`'s SQLite state, and
`min_machines_running = 0` (scale-to-zero).

**Evidence:** commit `0bb0286` added `fly.toml` and `docker/
webhook.Dockerfile`; live at `patchward-webhook.fly.dev/healthz` →
`{"status":"ok"}`, reconfirmed 2026-07-13 (Tier 1, direct HTTPS).

**Rationale (reconstructed from `fly.toml`'s own committed comments,
which are the closest thing to a design doc for this decision):** the
volume is load-bearing, not optional — scale-to-zero means the container
filesystem is wiped on every restart, so the SQLite install/purchase state
must live on the mounted volume or installation state is lost silently
between webhook deliveries. This is a real single-point-of-failure worth
naming: if the volume mount is ever misconfigured, `installations_db.py`
degrades silently (empty DB, not a crash) rather than failing loudly.

**Known operational risk (real, from Session 012):** `flyctl deploy`
regenerates `fly.toml` and strips the hand-written KS-TRACE comment block
and setup walkthrough on every deploy unless manually restored afterward.
This happened once, caught and restored in Session 012 (2026-07-10).
**Recommend, as a follow-up:** move the setup walkthrough out of
`fly.toml`'s comments and into a proper `docs/` file, since comments in a
tool-regenerated config file are provably not a durable place to keep
documentation.

**Correction, same day (2026-07-13):** this ADR originally also claimed
the drift had "happened again" as of 2026-07-13, based on a `git diff`
run in the agent sandbox. **That second claim was false** — Yehor
confirmed via his own `git status` / `git diff -- fly.toml` that
`fly.toml` was clean, matching committed `HEAD`, the whole time. The
sandbox's working-tree read was wrong, not the file. Left visible here
rather than silently deleted, per this project's ADR-immutability
convention — the real, single-occurrence risk from Session 012 above
still stands and is the reason for the follow-up recommendation; only the
second, 2026-07-13 recurrence claim is retracted. See
`memory/STATE.md`'s "Working-tree state" section for the fuller
tool-reliability finding this produced.

**Status:** Accepted (retroactive, reconstructed from git archaeology,
2026-07-13). Amended same day per correction above. Not yet reviewed by
Yehor.

---

## ADR-030 | 2026-07-09 (retroactive, 2026-07-13) | GitHub App + Marketplace billing as the product shift

**Decision:** Adopt a GitHub App installation model (not a personal
access token) with per-installation, 1-hour-lived Installation Access
Tokens (`github_app_auth.py`), and track installation/repo/purchase state
in a new SQLite store (`installations_db.py`) keyed to GitHub Marketplace
`marketplace_purchase` webhook events.

**Evidence:** commit `0bb0286` — `installations_db.py` (188 lines,
`installations` / `installation_repos` / `marketplace_purchases` tables,
`SCHEMA_VERSION = 1`), `github_app_auth.py` (141 lines), `webhook.py`
handling `installation`, `installation_repositories`, and
`marketplace_purchase` event types.

**Rationale (reconstructed from `github_app_auth.py`'s own docstring,
the closest thing to a design doc found for this decision):** short-lived,
installation-scoped tokens instead of a long-lived PAT is explicitly
framed in the code as "the answer to enterprise due diligence." This is a
real product-direction change from the original CLI-only design (Phases
0-7): Patchward is no longer only a tool a developer runs locally against
repos they already have credentials for — it's now a hosted product other
people install and (eventually) pay for through GitHub as merchant of
record. `webhook.py`'s own docstring is explicit that this file
deliberately does not touch payment processing directly.

**Known limitation, confirmed 2026-07-13:** `is_entitled()` gates whether
a scan runs on a push event, but the Marketplace `marketplace_purchase`
event handling in `webhook.py` (L215-230) does not yet distinguish
`cancelled`/`pending_change` from `purchased`/`changed` beyond storing
whatever `action` string GitHub sends as `status` — no explicit test was
found confirming `is_entitled()` correctly treats a `cancelled` status as
non-entitled. Flagged as an open item in BACKLOG.md, not asserted as
broken (may well be correct — just not independently confirmed this
session).

**Status:** Accepted (retroactive, reconstructed from git archaeology,
2026-07-13). Not yet reviewed by Yehor.

---

## ADR-031 | 2026-06-XX (scaffolded), retroactive 2026-07-13 | PyPI Trusted Publisher (OIDC) for release distribution

**Decision:** Publish `patchward` to PyPI via GitHub Actions using OIDC
Trusted Publishing (`pypa/gh-action-pypi-publish@release/v1`,
`id-token: write`), not a stored `PYPI_API_TOKEN` secret. Workflow
triggers on GitHub Release publish or manual dispatch.

**Evidence:** `.github/workflows/publish.yml`, originally added in commit
`4a211a0` ("ci: scaffold PyPI Trusted Publisher workflow (not yet
active)" — commit predates the audited gap window), one-line updated in
`0bb0286` to point at `pypi.org/p/patchward` instead of `/repomend`.

**Rationale:** OIDC trusted publishing avoids a long-lived PyPI API token
sitting in GitHub Secrets — consistent with the short-lived-credential
posture adopted for GitHub App tokens in ADR-030.

**UNVERIFIED, flagged explicitly (do not treat as done):** whether PyPI's
own Trusted Publisher configuration for the `patchward` project has
actually been registered on PyPI's side — this is a PyPI-side setting
this session has no way to check — and whether this workflow has ever
actually run end-to-end. No GitHub Release exists yet as of `d4569d4`.
The workflow's own commit message ("not yet active") is the most honest
status available and should be treated as still current until Yehor
confirms otherwise.

**Status:** Accepted (retroactive, reconstructed from git archaeology,
2026-07-13). Not yet reviewed by Yehor.

---

## ADR-032 | 2026-07-13 | Unrecognized webhook events are acknowledged, not rejected

**Decision:** `POST /webhooks/github` returns HTTP 200
`{"status": "ignored", "event": event}` for any `X-GitHub-Event` value the
handler doesn't explicitly branch on, rather than rejecting with a 4xx.

**Evidence:** `src/patchward/webhook.py` L241-244, present since the
event handler was first written in commit `0bb0286` (2026-07-09) — the
behavior itself is not new, only its documentation as a decision is new.

**Rationale:** GitHub disables a webhook endpoint after enough
consecutive non-2xx responses. Since new event types can arrive that a
given version of the receiver simply hasn't been built to act on yet
(this is explicit in the code comment at the time it was written),
rejecting unknown-but-legitimate events risks GitHub silently disabling
the webhook — a worse failure mode than acknowledging and no-op'ing an
event this version doesn't handle.

**Explicitly considered and rejected alternative:** deny-by-default
(reject unrecognized event types) — this was BUILD_PLAN's Phase 9
Exposure Gate checklist's original assumption. Reviewed and declined by
Yehor 2026-07-13: the GitHub-webhook-auto-disable risk outweighs the
security benefit of rejecting unknown events, since `_verify_signature()`
already runs before any event-type branching — an attacker without the
webhook secret can't reach this code path regardless of which behavior is
chosen here. The choice is about protocol robustness against GitHub's own
future event types, not an authentication boundary.

**Status:** Approved — signed by Yehor 2026-07-13.
