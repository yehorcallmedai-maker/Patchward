# Phase 2 INTAKE Contract — KS-P2-01
**Date:** 2026-06-11  
**Signed by:** Yehor (pending)  
**Status:** DRAFT — awaiting Yehor signature

---

## ADR-009 Pre-Step — Confirmed Payload Table

Per ADR-009, exact payload strings were confirmed before this contract was written.
Phase 2 has no new Semgrep rule plants. The equivalent ground truth is the PreToolUse
deny hook payload list below. Every string in this table is the verbatim test contract
invariant for KS-P2-04 and KS-P2-07.

| # | Payload string | Risk class |
|---|---------------|------------|
| PL-01 | `rm -rf` | Destructive filesystem |
| PL-02 | `git push --force` | Branch force-overwrite |
| PL-03 | `git push --force-with-lease` | Branch force-overwrite |
| PL-04 | `curl \| sh` | Remote code execution |
| PL-05 | `wget \| sh` | Remote code execution |
| PL-06 | `eval(` | Arbitrary code execution |
| PL-07 | `exec(` | Arbitrary code execution |
| PL-08 | `os.system(` | Shell escape |
| PL-09 | `subprocess.run(shell=True` | Shell escape |
| PL-10 | `.env` | Credential file access |
| PL-11 | `.env.local` | Credential file access |
| PL-12 | `ANTHROPIC_API_KEY` | Credential exfiltration |

**Pass condition:** hook blocks all 12. Any payload on this list that passes through = FAIL.
Any additional payload the hook blocks = acceptable bonus, not required.

---

## 1. Client Goal

Harden the Phase 1 walking skeleton against unsafe tool execution, credential leakage,
and branch mutation. All scanner subprocesses must run inside Docker containers with
deny-by-default egress. A PreToolUse hook must block the 12 confirmed payloads before
any tool executes. Credentials must never enter the container boundary. Every scan must
operate on a git worktree, leaving the caller's working branch untouched. A red-team
injection suite (KS-P2-07) must pass 100% before Phase 3 opens.

---

## 2. Constraints

| # | Constraint |
|---|-----------|
| C-P2-01 | All scanner subprocesses run inside a Docker container. No scanner tool (Semgrep, Bandit, pip-audit, etc.) runs directly on the host process. |
| C-P2-02 | Docker container egress is deny-by-default. Only explicitly whitelisted outbound destinations permitted: PyPI (pip-audit), npm registry (npm audit), NVD/OSV (Trivy, OSV-Scanner). Arbitrary curl/wget to unwhitelisted hosts must be blocked. |
| C-P2-03 | PreToolUse hook fires before every tool call. Must block all 12 payloads in the confirmed payload table (PL-01 through PL-12). Hook is the first line of defence — runs before subprocess, before Docker, before any I/O. |
| C-P2-04 | Credentials (ANTHROPIC_API_KEY, LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY) MUST NOT be present in the Docker container environment. Verified by `docker exec env` assertion in tests. |
| C-P2-05 | Every scan operates on a `git worktree` branch (`repomend/scan-<id>`), never on the caller's working branch or main. Worktree is cleaned up after scan regardless of outcome. |
| C-P2-06 | CLI startup runs `docker info` check. If Docker is not running or not installed, exit code 1 with actionable error message. Same `_require_tool()` pattern as scanner.py. |
| C-P2-07 | KS-P2-07 red-team suite must pass at 100% (all 12 payloads blocked). This is a hard gate — Phase 3 does not open until this test file reports 0 failures. |
| C-P2-08 | No changes to the target repo's working branch. Scanner is read-only at the git level, not just the filesystem level. |

---

## 3. Acceptance Criteria

| ID | Criterion | How verified |
|----|-----------|-------------|
| AC-P2-01 | Docker container starts, scanner runs inside it, SARIF output returned to host | `repomend scan` end-to-end on fixture; assert SARIF findings returned and container exits cleanly |
| AC-P2-02 | `docker info` fail-fast fires when Docker not available | Mock `docker info` to return non-zero; assert `SystemExit(1)` with actionable message |
| AC-P2-03 | Egress deny-by-default: PyPI/npm work, arbitrary curl blocked | Integration: `pip-audit` succeeds inside container; `curl https://evil.example.com` blocked by network policy |
| AC-P2-04 | All 12 payloads in PL-01–PL-12 blocked by PreToolUse hook | Unit: call hook with each payload string; assert all 12 raise `DeniedToolCallError` or equivalent |
| AC-P2-05 | ANTHROPIC_API_KEY not present in container environment | Assert `ANTHROPIC_API_KEY not in container_env`; injected via proxy outside sandbox |
| AC-P2-06 | Scanner operates on `repomend/scan-<id>` worktree; caller's working branch unchanged | Before/after `git branch --show-current`; assert working branch unchanged; worktree cleaned up |
| AC-P2-07 | Red-team injection suite passes 100% — all 12 payloads blocked, zero pass-through | `test_red_team.py` — 12 parameterised tests, each injecting one payload; all must PASS |
| AC-P2-08 | Hook does not fire on clean tool calls (no false positives on normal scan operation) | Run full Phase 1 fixture scan with hook active; assert 0 DeniedToolCallError on legitimate scan |

---

## 4. Test Contract

### Inputs
| Input | Value |
|-------|-------|
| Fixture repo | `C:/Dev/Projects/repomend-fixture` |
| Confirmed payload table | PL-01 through PL-12 (see §ADR-009 Pre-Step) |
| Docker image | `python:3.12-slim` (baseline; locked digest in Phase 2 hardening) |
| Container network policy | `--network none` for scanner runs; allowlist applied per scanner tool |

### Expected Outputs
```json
{
  "docker_check": "pass — docker info returns 0",
  "container_scan": {
    "sarif_returned": true,
    "findings_count": 3,
    "container_exit_code": 0
  },
  "hook_block_rate": "12/12 — all payloads denied",
  "false_positive_rate": "0/N — no clean calls denied",
  "credential_in_container": false,
  "working_branch_mutated": false,
  "worktree_cleaned_up": true
}
```

### Invariants
- Hook block rate for confirmed payloads is always 12/12. Any value below 12 is a FAIL.
- `ANTHROPIC_API_KEY` is never readable from inside the Docker container.
- Caller's git working branch is identical before and after any scan.
- Worktree `repomend/scan-<id>` is always deleted after scan, pass or fail.
- No payload in PL-01–PL-12 may bypass the hook by encoding, case variation, or whitespace padding — exact string match is the minimum; substring match is preferred.

### Adversarial / Break Case
**Injection payload in source file (extends AC-P1-07 to sandbox layer):**  
A source file in the fixture contains a comment: `# rm -rf /` embedded in valid Python.  
Pass condition: PreToolUse hook fires on any tool call that would execute this string; SARIF
finding count is unaffected (still 3); no destructive command executes.

**Credential exfiltration attempt:**  
A fixture file contains the string `ANTHROPIC_API_KEY=sk-ant-fake`.  
Pass condition: `ANTHROPIC_API_KEY` not present in container env; finding normalised to SARIF
without raw credential value in the `message` field.

---

## 5. Risk Areas

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Docker Desktop not installed on dev machine | Medium | `_require_tool("docker", "Install Docker Desktop: https://docs.docker.com/desktop/")` — fail fast at CLI startup |
| Container startup latency degrades scan UX | Medium | Phase 2 baseline only; Phase 6 adds container pooling |
| Hook substring matching too broad — false positives on `exec` in identifiers | Medium | Test AC-P2-08 explicitly; tune to word-boundary or context-aware matching if needed |
| `git worktree` unavailable (git < 2.5) | Low | Add `git --version` check alongside `docker info`; fail fast with version requirement message |
| Credential scrubber misses base64-encoded keys in SARIF message fields | Low | Add scrubber pass over SARIF results before any output; Phase 2 hardening item |
| `--network none` breaks pip-audit/npm audit (need PyPI/npm) | High | Per-scanner network allowlist: pip-audit and npm audit containers get restricted outbound; semgrep/bandit run fully offline |

---

## 6. Architecture Decision — Docker as Sandbox (ADR-010)

**Decision:** Docker Desktop on Windows as the Phase 2 sandbox primitive.  
**Rejected alternatives:**
- `@anthropic-ai/sandbox-runtime` — Node package; incompatible with Python-first project without a runtime bridge
- `bubblewrap` — Linux-only; eliminated by Windows dev environment (confirmed by cp1251 defect in Session 002)
- `gVisor` — Phase 2+ hardening option on top of Docker; deferred to Phase 3 or later

**Logged as:** ADR-010 (to be added to `memory/architectural_decisions.md` after Yehor signs)

---

## Accountability Statement

_I, Yehor, have reviewed this INTAKE contract. The ADR-009 pre-step payload table, acceptance criteria, and test contract accurately reflect Phase 2 requirements. No build work begins until this is signed._

**Signed:** Yehor  **Date:** 2026-06-11

---

## 7. Open Flags (non-blocking)

**Flag P2-A — RESOLVED 2026-06-11 (Yehor):** Hook matching strategy confirmed as
**substring match with allowlist exception list**. Exact match rejected — misses variants
like `rm -rf /tmp`. Global substring match rejected — false positives on `exec` in
identifiers like `execute_query`, `execution`, `context`. Resolved implementation:

```python
DENY_PAYLOADS = [
    "rm -rf", "git push --force", "git push --force-with-lease",
    "curl | sh", "wget | sh", "eval(", "exec(",
    "os.system(", "subprocess.run(shell=True",
    ".env", ".env.local", "ANTHROPIC_API_KEY"
]

ALLOWLIST_CONTEXTS = [
    "execute_", "execution", "executor", "exec_",
    "context", "execute(",  # function name, not builtin
]
```

Hook logic: if payload substring found AND not preceded/followed by allowlist context → DENY.
AC-P2-08 (false positive test on clean scan) catches over-blocking immediately.

**Flag P2-B:** Container image digest must be locked (not `python:3.12-slim` floating tag)
before Phase 2 ships. Locking deferred to end of KS-P2-02 — confirm digest after image
is built and tested, paste into contract §4 before KS-P2-08.
