# Phase 6 INTAKE — Parallel Multi-Repo + Cost Controls
**Project:** RepoMend — Local-First Multi-Repo Security Agent  
**Phase:** 6  
**Contract date:** 2026-06-22  
**Status:** DRAFT — awaiting Yehor sign-off  
**Namespace:** AC-P6-XX (base) · AC-P6A-XX (addenda)  
**Blocked by:** Phase 5 closed ✅ 2026-06-22

---

## 0. ADR-009 Pre-Step — Architecture Decisions Locked Before Build

Per ADR-009, the following four questions were resolved before the
INTAKE contract was written. Answers are locked and become binding
constraints in §2.

### Q1 — Concurrency model

**Decision: `asyncio` with `asyncio.Semaphore(n)` bounding concurrent
repos. `AsyncAnthropic` client. Subprocess calls via
`asyncio.to_thread()`.**

Rationale:
- The Claude SDK's `httpx` async client (`AsyncAnthropic`) is already
  async-native. Threads add no throughput benefit for I/O-bound
  LLM calls and complicate error handling.
- `ProcessPoolExecutor` is overkill for I/O-bound work and carries
  Windows pickling constraints that would surface in serialising
  Pydantic models across process boundaries.
- `asyncio.Semaphore(n)` doubles as the cost-rate-limiter: each
  permit = one concurrent LLM call. `n` is configurable.
- `subprocess` calls are blocking. Wrapping with `asyncio.to_thread()`
  yields the event loop during git operations without spawning extra
  processes.
- Windows `asyncio` on Python 3.12+ uses `ProactorEventLoop` by
  default; `asyncio.to_thread()` is supported on this loop. Target
  runtime is 3.12 (updated from 3.11 per Python release timeline).

### Q2 — Cost controls

**Prompt caching: NEW.** Add `cache_control: {type: ephemeral}` to
the Fix-Gen system prompt message block. The system prompt is large,
stable across all repos in a batch, and repeated N times per run —
exactly the profile the caching API targets. Expected saving:
~90% of system-prompt token cost on cache hits.

**Model tiering: EXTEND.** Add `[models]` section to `repomend.toml`.
Expose `--model` CLI flag for one-off override. Defaults:
`scanner_model = claude-haiku-4-5-20251001`,
`fix_model = claude-sonnet-4-6`. Haiku for Semgrep-output triage
and Gate 1 structural checks; Sonnet for fix-gen and Gate 2/3
semantic reasoning.

**Batch API: DEFERRED to Phase 7.** The Batch API is fire-and-forget
(results polled asynchronously). The current pipeline is synchronous:
scan → fix → verify → PR, each step depending on the previous. Wiring
Batch API would require a checkpointing/polling layer that is Phase 7
scope.

### Q3 — Branch protection check

**Decision: in `PRPublisher.publish()` as a pre-push step.
`git_push_branch()` unchanged.**

`PRPublisher` calls
`GET /repos/{owner}/{repo}/branches/{branch}/protection` before every
push:

| Response | Action |
|----------|--------|
| 200 | Raise `RuntimeError("branch '{branch}' is protected — push aborted")`. Do not call `git_push_branch`. |
| 404 | Branch is unprotected. Proceed to push. |
| 403 | No branch-protection read permission. Log warning, proceed. |

`git_push_branch()` remains credential-agnostic with no GitHub API
knowledge. The `--force` flag (added in Phase 5) is never exercised
on a branch that returns 200, because the guard aborts before push.
This closes Phase 5 Known Limitation 8.

### Q4 — Multi-repo config shape

**Decision: `[[repos]]` array of tables. `[github]` singleton is the
default/fallback. Backward-compatible.**

```toml
# New multi-repo shape
[batch]
max_concurrent = 3

[models]
scanner_model = "claude-haiku-4-5-20251001"
fix_model     = "claude-sonnet-4-6"

[[repos]]
path        = "C:/Dev/Projects/foo"
owner       = "acme"
repo        = "foo"
base_branch = "main"

[[repos]]
path        = "C:/Dev/Projects/bar"
owner       = "acme"
repo        = "bar"
base_branch = "develop"
```

If no `[[repos]]` is present, the config loader falls back to the
existing `[github]` singleton. Per-entry fields (`owner`, `repo`,
`base_branch`) override defaults drawn from `[github]`. `path` is
per-entry only (no global default).

---

## 1. Client Goal

Extend RepoMend from single-repo to multi-repo batch processing.
A single `repomend fix` invocation reads all `[[repos]]` entries
from `repomend.toml`, processes them concurrently (bounded by
`asyncio.Semaphore(max_concurrent)`), and produces one draft PR per
verified finding per repo. Cost is controlled via prompt caching on
the Fix-Gen system prompt and model tiering (Haiku for cheap steps,
Sonnet for expensive ones). Branch protection is checked before every
push, closing the Phase 5 force-push safety gap.

Users with existing single-repo `[github]` configs see no behaviour
change.

---

## 2. Constraints

### C-P6-01 — asyncio event loop with `AsyncAnthropic` client
The Phase 6 pipeline runs in an `asyncio` event loop. All Claude API
calls use `anthropic.AsyncAnthropic`. The synchronous `Anthropic`
client may not be used inside the async pipeline.

### C-P6-02 — Bounded semaphore
`asyncio.Semaphore(max_concurrent)` gates all concurrent repo
pipelines. `max_concurrent` is read from `repomend.toml`
`[batch].max_concurrent` (default: 3). A repo's pipeline acquires
the semaphore at entry and releases it on completion or exception.

### C-P6-03 — No blocking calls on the event loop
All `subprocess.run` / `subprocess.check_output` calls inside the
async pipeline must be wrapped with `asyncio.to_thread()`. Blocking
calls directly on the event loop are a defect. Structural tests will
assert this (AC-P6-03).

### C-P6-04 — Prompt caching on Fix-Gen system prompt
The Fix-Gen system prompt message block must include:
```python
{"type": "text", "text": SYSTEM_PROMPT,
 "cache_control": {"type": "ephemeral"}}
```
This applies to every Fix-Gen call regardless of batch size.

### C-P6-05 — Model tiering via config and CLI flag
`[models].scanner_model` controls the model used in Semgrep triage
and Gate 1. `[models].fix_model` controls Fix-Gen and Gate 2/3.
`--model <string>` CLI flag overrides `fix_model` for a single run.
Defaults: `scanner_model = claude-haiku-4-5-20251001`,
`fix_model = claude-sonnet-4-6`.

### C-P6-06 — `[[repos]]` config with `[github]` fallback
`Config.load()` parses `[[repos]]` entries into a
`list[RepoConfig]`. If `[[repos]]` is absent, it constructs a
single-element list from `[github]` fields. Per-entry fields
take precedence over `[github]` defaults field-by-field.

### C-P6-07 — Branch protection check in `PRPublisher`
`PRPublisher.publish()` calls the GitHub branch protection endpoint
before every push. Behaviour per response code: see Q3 table above.
The check must occur after `git_push_branch` arguments are assembled
but before `git_push_branch` is called.

### C-P6-08 — `--force` never used on protected branch
If the branch protection endpoint returns 200, `git_push_branch` is
never called. The `--force` flag therefore cannot be exercised on a
protected branch. This constraint is satisfied by C-P6-07 (the guard
fires first), but it is stated separately as a closed safety property.

### C-P6-09 — Per-repo run log entries
Each repo in a batch gets its own NDJSON session record in
`run_log.ndjson`. Records include a `repo` field (`{owner}/{repo}`)
so post-hoc analysis can filter by repository.

### C-P6-10 — Semaphore ceiling documentation
`max_concurrent = 3` (default) is conservative relative to
Anthropic's Tier 1 rate limits (currently 50 RPM / 40k TPM for
Sonnet). At max concurrency, three simultaneous Fix-Gen calls may
each consume ~4k tokens/min. Three × 4k = 12k TPM, well under the
40k limit. Document this reasoning in `repomend.toml.example`
alongside the `max_concurrent` field. Users who have upgraded to
Tier 2+ may safely raise the ceiling.

---

## 3. Acceptance Criteria

| AC | Description | Test location |
|----|-------------|---------------|
| AC-P6-01 | `asyncio` pipeline processes `[[repos]]` entries concurrently; N repos produce N run log records in a single invocation | `test_multi_repo.py` |
| AC-P6-02 | `Semaphore(2)` with 4 repos: assert no more than 2 repos in-flight simultaneously (mock semaphore acquire/release timing) | `test_multi_repo.py` |
| AC-P6-03 | Structural: every `subprocess.run` call inside the async pipeline is wrapped in `asyncio.to_thread()` — assert via AST inspection or grep + manual review | `test_async_pipeline.py` |
| AC-P6-04 | `cache_control: {type: ephemeral}` present on Fix-Gen system prompt block in the outgoing API request | `test_fix_gen.py` |
| AC-P6-05 | Model tiering: scanner uses `claude-haiku-4-5-20251001`, fix-gen uses `claude-sonnet-4-6` — read from config, assert model string in API call kwargs | `test_config.py`, `test_fix_gen.py` |
| AC-P6-06 | `[[repos]]` config: multiple entries parsed into `list[RepoConfig]`; per-entry `base_branch` override respected | `test_config.py` |
| AC-P6-07 | `[github]` singleton fallback: existing single-repo config (no `[[repos]]`) produces `list[RepoConfig]` of length 1 and pipeline runs identically to Phase 5 | `test_config.py` |
| AC-P6-08 | Branch protection 200 → `RuntimeError` raised, `git_push_branch` not called | `test_pr_publisher.py` |
| AC-P6-09 | Branch protection 403 → warning logged via `logging.warning`, `git_push_branch` called normally | `test_pr_publisher.py` |
| AC-P6-10 | `--force` flag: confirm `git_push_branch` is never reached when protection endpoint returns 200 (assert call count = 0 on the mock) | `test_pr_publisher.py` |
| AC-P6-11 | End-to-end integration: two-repo batch on fixture repos produces two run log records; if both findings verified, two draft PRs opened. Skip guard: `ANTHROPIC_API_KEY` + `GITHUB_TOKEN` + `RUN_E2E_MULTI` env vars must all be set | `test_golden_dataset.py` |

---

## 4. Test Contract

### 4.1 Inputs

| Input | Value |
|-------|-------|
| `repomend.toml` (multi-repo) | Two `[[repos]]` entries; `max_concurrent = 2` |
| `repomend.toml` (singleton) | `[github]` only; no `[[repos]]` |
| Fixture repos | `repomend-fixture` (existing) + second fixture or second finding |
| Env vars | `ANTHROPIC_API_KEY`, `GITHUB_TOKEN`, `RUN_E2E_MULTI` |

### 4.2 Expected outputs

| Scenario | Expected output |
|----------|-----------------|
| 2-repo batch, both verified | 2 run log records · 2 draft PRs |
| 2-repo batch, one Fix-Gen failure | 1 run log record (success) · 1 run log record (failed) · 1 PR · other repo pipeline continues |
| Singleton config | 1 run log record · behaviour identical to Phase 5 |
| Protected branch | `RuntimeError` in run log · `pr_status: push_aborted` · no PR |
| 403 on protection check | Warning in log · push proceeds · PR opened |

### 4.3 Invariants

1. A semaphore permit must be held for the entire duration of one
   repo's pipeline. No repo proceeds past the semaphore acquire
   without a permit.
2. A semaphore permit must be released on all exit paths — success,
   `FixResult.success=False`, unhandled exception — using
   `async with semaphore:` context manager (not manual
   acquire/release).
3. `GITHUB_TOKEN` must not appear in any run log record (carried
   from AC-P5-11).
4. Each repo's run log record must include `repo: "{owner}/{repo}"`.
5. The event loop must not be blocked: no `time.sleep()`,
   `subprocess.run()`, or other synchronous blocking call may appear
   outside an `asyncio.to_thread()` wrapper in the async pipeline.

### 4.4 Adversarial cases

**AD-P6-01 — Mid-pipeline failure isolation.**
One repo in a 3-repo batch raises an unhandled exception in Fix-Gen
(mock raises `RuntimeError`). Assert the other two repos complete
their pipelines normally. Assert the failed repo's semaphore permit
is released (total acquired == total released == 3).

**AD-P6-02 — Semaphore drain without deadlock.**
`max_concurrent = 1`, 5 repos queued. Mock each pipeline to take
10 ms. Assert all 5 complete sequentially without deadlock or
`asyncio.TimeoutError`. Total elapsed < 5 × (10 ms + 5 ms overhead).

**AD-P6-03 — 429 rate limit from Anthropic API.**
Mock the `AsyncAnthropic` client to raise `anthropic.RateLimitError`
on the first Fix-Gen call. Assert the pipeline for that repo records
`fix_status: rate_limited` in the run log and releases the semaphore.
Assert other repos are not affected.

**AD-P6-04 — Config migration: existing user has `[github]` only.**
Load a `repomend.toml` with no `[[repos]]` section. Assert
`Config.repos` is a list of length 1 and its single entry matches the
`[github]` fields exactly. Assert no `KeyError` or `ValidationError`
is raised during load.

---

## 5. Risk Areas

| Risk | Severity | Mitigation |
|------|----------|------------|
| Windows `ProactorEventLoop` subprocess edge cases | MEDIUM | Target Python 3.12+; test with `asyncio.to_thread` wrapping; add CI matrix entry for Windows if possible |
| Thread pool exhaustion under high concurrency | MEDIUM | `asyncio.to_thread` uses the default executor (ThreadPoolExecutor, default workers = min(32, cpu_count+4)). Document that `max_concurrent` should not exceed this ceiling. |
| Anthropic API 429 under concurrent load | HIGH | Default `max_concurrent = 3` stays well under Tier 1 rate limits. Implement exponential back-off on `RateLimitError` (AD-P6-03 hardens this). |
| Protection check adds one HTTP call per PR | LOW | ~50 ms per call, not in the hot path. Acceptable latency. Cache result per branch name within a batch run to avoid re-checking the same branch. |
| `[[repos]]` migration breaking existing configs | HIGH | C-P6-06 mandates backward-compatible fallback. AD-P6-04 is the adversarial test for this. |
| Prompt caching not reducing costs if system prompt changes between runs | LOW | System prompt is static (baked at import time). Cache TTL is 5 minutes per Anthropic docs — safe for batches under 5 min. |

---

## 6. Known Limitations

1. **Batch API deferred.** Fire-and-forget incompatible with the
   synchronous scan→fix→verify→PR pipeline. Phase 7 scope.
2. **No progress UI for concurrent runs.** Multiple repos processing
   simultaneously produce interleaved log lines. A TUI progress view
   is out of scope for Phase 6.
3. **No partial-batch resume.** If a batch run is aborted mid-flight
   (Ctrl-C, crash), there is no checkpoint. Re-running processes all
   repos from scratch. Checkpointing is Phase 7 scope.
4. **`max_concurrent` not auto-tuned.** The ceiling is static config.
   No dynamic back-pressure based on observed 429 rate or API
   latency. Phase 7 scope.
5. **Single finding per repo per run.** The pipeline still processes
   the first verified finding and stops. Multiple-findings-per-repo
   batching is Phase 7 scope.

---

## 7. Proposed Architectural Decisions

### ADR-020 (proposed) — asyncio + Semaphore as concurrency model
Use `asyncio` event loop with `AsyncAnthropic` and
`asyncio.Semaphore(n)` for bounded concurrency. Do not use
`ThreadPoolExecutor` or `ProcessPoolExecutor` for the LLM pipeline.
All blocking subprocess calls wrapped in `asyncio.to_thread()`.

### ADR-021 (proposed) — Prompt caching on Fix-Gen system prompt (ephemeral)
Add `cache_control: {type: ephemeral}` to the Fix-Gen system prompt
message block. Rationale: system prompt is large (~2k tokens), stable
across repos in a batch, and repeated N times per batch run. Cache
TTL is 5 minutes (Anthropic). Expected token saving: ~90% on system
prompt tokens for cache hits after the first call.

### ADR-022 (proposed) — `[[repos]]` array of tables with `[github]` fallback
Multi-repo configuration uses TOML array-of-tables `[[repos]]`.
Single-repo `[github]` block is preserved as a fallback for
backward compatibility. `Config.repos` always returns
`list[RepoConfig]` regardless of which form is present.

---

## 8. Out of Scope for Phase 6

- Anthropic Batch API (deferred — Phase 7)
- Multiple findings per repo per run (Phase 7)
- Partial-batch resume / checkpointing (Phase 7)
- Auto-tuned concurrency ceiling (Phase 7)
- Progress TUI (Phase 7)
- Reviewer assignment on PRs (Phase 7)
- SSH or `gh` CLI auth (Phase 7)

---

## 9. Accountability Statement

_I, Yehor, confirm that this Phase 6 INTAKE contract accurately
captures the client goal, constraints, acceptance criteria, test
contract, risk areas, and known limitations for the Parallel
Multi-Repo + Cost Controls phase of RepoMend. By signing below I
authorise build work to begin. No implementation may start before
this signature._

**Signed:** Yehor  **Date:** 2026-06-23

---

_End of Phase 6 INTAKE contract._

---

## Addendum A — Implementation Notes (post-signature, not contract changes)

### A-01 — AC-P6-06 field-merge test case (flagged during contract review)

The AC-P6-06 test suite **must** include the following specific case:

A `[[repos]]` entry containing only `{path, repo}` (no `owner`, no
`base_branch`) must correctly inherit `owner` from `[github].owner`
and `base_branch` from `[github].base_branch` (defaulting to `"main"`
if also absent from `[github]`).

Assert:
1. No `KeyError` or `ValidationError` is raised during `Config.load()`.
2. The resolved `RepoConfig` has `owner == [github].owner`.
3. The resolved `RepoConfig` has `base_branch == [github].base_branch`
   (or `"main"` if `[github].base_branch` is absent).

Rationale: This is the highest-probability migration breakage point.
A user with an existing `[github].owner` who adds a `[[repos]]` entry
without repeating `owner` will silently break if the per-entry merge
is not implemented correctly. The config loader must perform
field-by-field merge (per-entry overrides `[github]` defaults;
absent per-entry fields fall back to `[github]`), not a strict
all-or-nothing validation.
