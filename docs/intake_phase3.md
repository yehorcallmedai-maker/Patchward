# Phase 3 INTAKE Contract — KS-P3-01
**Date:** 2026-06-12  
**Signed by:** Yehor  
**Status:** SIGNED 2026-06-12

---

## ADR-009 Pre-Step — Egress Constraint Ground Truth

Per ADR-009, concrete implementation targets are confirmed before this contract is written.
The constraint carried from Phase 2 §4 (NetworkPolicy.PYPI_ONLY / NPM_ONLY too permissive)
requires the following specific approach, approved by Yehor 2026-06-12:

**Option A — iptables OUTPUT rules inside container (`--cap-add NET_ADMIN`)**

Rationale locked by Yehor:
1. DNS-based allowlisting (Option B) is bypassed by hardcoded IP addresses — the exact
   threat model for prompt-injection-driven exfiltration from inside the sandbox.
2. iptables OUTPUT rules operate at the IP/CIDR layer: deny-by-default, explicit allow.
   This is the actual model the Phase 2 contract described.
3. `--cap-add NET_ADMIN` is scoped to the ephemeral `--rm` scanner container only.
   Privilege surface is bounded and well-understood.
4. Sidecar egress proxy is the Phase 6 pattern (parallel worker pool, shared policy).
   Not in scope for Phase 3.

**Resolved IP/CIDR allowlists (resolved at container startup, not hardcoded):**

| Policy | Allowed destinations |
|--------|---------------------|
| `PYPI_ONLY` | Resolved IPs for `pypi.org`, `files.pythonhosted.org` |
| `NPM_ONLY` | Resolved IPs for `registry.npmjs.org` |
| `OFFLINE` | No outbound permitted (unchanged) |

Adversarial test requirement (Yehor, 2026-06-12): a fixture container must attempt
`curl` to a **non-allowlisted IP address** (not just a hostname) and be blocked by
the iptables rule — not by DNS resolution failure. This closes the bypass-by-IP gap
that disqualified Option B.

---

## 1. Client Goal

Build the Fix-Gen subagent: an Opus/Sonnet agent that receives a single SARIF finding
(file path + rule ID + message + scanner evidence) and produces a targeted patch on a
`repomend/fix-<id>` branch. The patch is human-reviewable, never auto-merged. Context
passed to Fix-Gen is scoped to the finding only — no raw file dumps, no full repo context.

Before Fix-Gen ships, the egress allowlist hardening required by Phase 2 §4 must be
complete and verified. Fix-Gen runs inside the same Docker sandbox; the sandbox must
enforce true per-destination egress before any agent with write access touches files.

Phase 3 gate: ≥30% repair success on the golden dataset (C-P3-09).

---

## 2. Constraints

| # | Constraint |
|---|-----------|
| C-P3-01 | Fix-Gen subagent receives exactly: file path, rule_id, message, scanner evidence (SARIF snippet). It does NOT receive: full file contents, directory listings, other findings, repo metadata. Context is scoped at the caller (Orchestrator), not inside Fix-Gen. |
| C-P3-02 | Fix-Gen operates on `repomend/fix-<id>` branch (created from the worktree, not from main). Never writes to main or the caller's working branch. Branch naming: `repomend/fix-<rule_id_slug>-<uuid4_short>`. |
| C-P3-03 | No auto-merge. Every fix surfaces as a structured PR dict: `{intent, diff, risk_class, scanner_evidence, test_log}`. PR dict is written to `runs/session_<timestamp>.json` and printed to stdout. No GitHub API call in Phase 3 (Phase 5 item). |
| C-P3-04 | Fix-Gen model tiering: `claude-opus-4-8` for HIGH/CRITICAL risk_class findings; `claude-sonnet-4-6` for MEDIUM/LOW. Risk class derived from SARIF `level` field (`error` → HIGH, `warning` → MEDIUM, `note` → LOW). |
| C-P3-05 | File checkpointing: before any edit, the original file content is written to `runs/checkpoints/<session_id>/<filename>.orig`. Restore path must be executable without Fix-Gen involvement. |
| C-P3-06 | SARIF finding passes through the existing SARIFNormalizer + validate_sarif_run() before reaching Fix-Gen. Raw scanner output never enters the Fix-Gen prompt. |
| C-P3-07 | Fix-Gen is a leaf agent. It cannot spawn subagents. Allowed tools: Read, Edit, Write, Bash (scoped to the fix branch worktree only). Bash commands are subject to the same PreToolUse deny hook (PL-01–PL-12) as all other tool calls. |
| C-P3-08 | **REQUIRED from Phase 2 §4 (Yehor 2026-06-12):** NetworkPolicy.PYPI_ONLY and NetworkPolicy.NPM_ONLY must enforce true per-destination allowlisting via iptables OUTPUT rules inside the scanner container (`--cap-add NET_ADMIN`), allowlisting resolved IPs for pypi.org, files.pythonhosted.org (PYPI_ONLY) and registry.npmjs.org (NPM_ONLY). The current `--network bridge` implementation is not sufficient. This constraint must be closed before Fix-Gen ships — Fix-Gen runs in the same sandbox. |
| C-P3-09 | Phase 3 gate: Fix-Gen must achieve ≥30% repair success on the golden dataset (PL-01–PL-12 findings in the fixture repo). "Repair success" = patched file passes re-scan (finding no longer present) AND existing unit tests still pass. |
| C-P3-10 | maxTurns is set on every Fix-Gen agent session. No infinite loops. Default: 10 turns. Configurable via `repomend.toml` `[fix_gen] max_turns`. |
| C-P3-11 | Every Fix-Gen run appends to `runs/session_<timestamp>.json`: `{repo, finding, fix_attempt, patch_diff, verification_status, pr_dict}`. Schema is append-only; no in-place mutation of existing run records. |

---

## 3. Acceptance Criteria

| ID | Criterion | How verified |
|----|-----------|-------------|
| AC-P3-01 | iptables OUTPUT deny-by-default applied inside container; PYPI_ONLY allows pip index query; NPM_ONLY allows npm registry query; OFFLINE blocks all | Integration: three parametrized container runs; assert exit codes and response bodies. Unit: NetworkPolicy routing logic unchanged. |
| AC-P3-02 | Adversarial: container with PYPI_ONLY policy attempts `curl` to a non-allowlisted **IP address** (not hostname); blocked by iptables, not DNS | Integration: `curl <raw_ip>` returns connection refused or timeout; iptables rule confirmed as blocking mechanism (not DNS NXDOMAIN) |
| AC-P3-03 | Fix-Gen context is scoped: prompt contains file path + rule_id + message + evidence only; no full file contents, no directory listing | Unit: assert prompt string does not contain lines outside the finding's snippet; mock Fix-Gen client, inspect call args |
| AC-P3-04 | Fix-Gen writes patch to `repomend/fix-<id>` branch only; main and working branch unchanged after run | Unit + integration: assert branch before/after; assert no commits on main |
| AC-P3-05 | Original file checkpoint written before any edit | Unit: assert `.orig` file exists with original content after Fix-Gen run; delete checkpoint, re-run, assert again |
| AC-P3-06 | File checkpoint is restorable without Fix-Gen: `cp runs/checkpoints/<id>/<file>.orig <original_path>` restores pre-fix state | Integration: apply fix, restore from checkpoint, re-run scanner, assert original finding present again |
| AC-P3-07 | Model tiering: `error`-level finding routes to Opus; `warning`/`note` routes to Sonnet | Unit: mock client constructor; assert model param from call args matches risk_class |
| AC-P3-08 | No auto-merge: PR dict written to run log and stdout; no GitHub API call | Unit: assert no `github` import; assert PR dict fields present in run JSON |
| AC-P3-09 | ≥30% repair success on golden dataset (PL-01–PL-12 fixture findings) | Integration: run Fix-Gen on all 3 fixture findings; assert ≥1 passes re-scan + test suite |
| AC-P3-10 | maxTurns respected: Fix-Gen session terminates at or before configured limit | Unit: mock client with turn counter; assert session terminates at max_turns |
| AC-P3-11 | Run log append-only: two sequential runs produce two records; no mutation of first record | Unit: write two run records, assert len == 2, assert first record unchanged |
| AC-P3-12 | Deny hook PL-01–PL-12 fires on Fix-Gen tool calls same as Scanner | Unit: inject each payload via mock Fix-Gen tool call; assert DeniedToolCallError; same test vectors as test_red_team.py |

---

## 4. Test Contract

### Inputs

| Input | Value |
|-------|-------|
| Fixture repo | `C:/Dev/Projects/repomend-fixture` — 3 confirmed findings at lines 24, 30, 37 |
| Golden dataset | PL-01–PL-12 mapped to fixture findings: subprocess-shell-true, insecure-hash-algorithm-md5, ssl-wrap-socket-is-deprecated |
| Fix-Gen model (HIGH) | `claude-opus-4-8` |
| Fix-Gen model (DEFAULT) | `claude-sonnet-4-6` |
| maxTurns | 10 (default) |
| Docker image | `python:3.12-slim@sha256:a39549e211a16149edf74e5fdc9ef03a6767e46cd987c5048b6659b6c9904c94` |
| Egress policy under test | PYPI_ONLY, NPM_ONLY, OFFLINE |
| Adversarial IP target | A public IP address (e.g. 1.1.1.1 or 8.8.8.8) — not an allowlisted destination; confirmed non-allowlisted before test run |

### Expected Outputs

```json
{
  "iptables_pypi_only": {
    "pip_index_query": "pass",
    "curl_non_allowlisted_ip": "blocked — iptables OUTPUT rule (not DNS)"
  },
  "fix_gen": {
    "branch_created": "repomend/fix-<rule_id_slug>-<uuid4_short>",
    "main_branch_mutated": false,
    "checkpoint_written": true,
    "pr_dict_fields": ["intent", "diff", "risk_class", "scanner_evidence", "test_log"],
    "repair_success_rate": ">=30% (>=1 of 3 fixture findings repaired)"
  },
  "run_log": {
    "records_after_two_runs": 2,
    "first_record_mutated": false
  }
}
```

### Invariants

- Fix-Gen never receives a full file dump. Context is always scoped to the finding snippet.
- iptables OUTPUT rules are applied before scanner exec. No scanner code runs before egress is locked.
- `repomend/fix-<id>` branch always cleaned up on test teardown. No stale fix branches in fixture repo.
- Checkpoint always written before the first edit. No edit without a checkpoint.
- Deny hook fires on Fix-Gen tool calls with the same block rate as Scanner (12/12 payloads).
- Run log records are append-only. No in-place mutation.

### Adversarial / Break Case

**Bypass-by-IP egress test (motivated by Option B rejection):**  
Inside a PYPI_ONLY container, attempt `curl <raw_non_allowlisted_ip>:80`.  
Pass condition: connection blocked by iptables OUTPUT rule. DNS is not involved.  
Failure condition: connection succeeds, OR connection fails only because DNS resolution fails (not iptables). The test must confirm the iptables rule is the blocking mechanism — assert `iptables -L OUTPUT` shows the DROP rule and that the curl exit code indicates network-layer rejection.

**Scoped-context injection attempt:**  
Fix-Gen prompt is constructed with a crafted SARIF message field containing `rm -rf /`.  
Pass condition: PreToolUse hook fires before any tool call executes the string; no filesystem mutation; Fix-Gen run terminates with `DeniedToolCallError`; run log records the denial.

**Fix introduces a new vulnerability:**  
Fix-Gen patches `subprocess.run(shell=True, ...)` by removing `shell=True` but inadvertently leaves a string-concatenated command argument.  
Pass condition: Verifier subagent (Phase 4) catches this — noted as a **known limitation** for Phase 3 since Verifier is not yet built. In Phase 3, the re-scan check (AC-P3-09) only confirms the original finding is gone; it does not guarantee no new findings. This gap is documented in §4 Known Limitations.

---

## 5. Risk Areas

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| iptables unavailable or restricted in Docker Desktop WSL2 VM | Medium | Test `--cap-add NET_ADMIN` + `iptables -L` inside container before building policy logic; fail fast with actionable error if NET_ADMIN unavailable |
| IP addresses for pypi.org / files.pythonhosted.org change (CDN edge rotation) | Medium | Resolve IPs at container startup, not hardcoded; log resolved IPs to run record; Phase 6 item: refresh cache on TTL |
| **[RESOLVED pre-sign-off]** Entrypoint applied iptables DROP before writing /etc/hosts — pip/npm DNS queries failed post-DROP (Docker's 127.0.0.11 resolver does not route through lo) | High (was) | Fixed: write /etc/hosts entries for allowlisted domains before DROP. Re-verified: 2/2 integration tests pass against repomend-scanner:0.1.0@sha256:578a... — see ADR-014. |
| Fix-Gen context scoping too narrow — fix requires reading adjacent functions | Medium | Allow Fix-Gen to request additional file context via a structured tool call (`read_lines(file, start, end)`); Orchestrator validates range is within the same file |
| Fix breaks existing tests (regression) | High | Re-run `pytest` (Python) or `jest` (JS) after patch; failure = repair_success = false for that finding; documented in AC-P3-09 |
| Opus cost for HIGH findings blows monthly cap | Medium | Set `max_turns=10`; prompt-cache the system prompt and tool definitions; Opus only for `error`-level findings |
| Fix-Gen produces syntactically invalid patch (unparseable diff) | Low | Run `git diff --check` on the fix branch after edit; if invalid, mark repair_success=false, log to run record |
| Phase 3 ships without Verifier — fix quality unverified beyond re-scan | High (known) | Documented limitation. Phase 4 adds Verifier. Re-scan is necessary but not sufficient. Human review of PR dict is required before merge. |

---

## 6. Architecture Decisions

### ADR-012 — Fix-Gen context scoping strategy

**Decision:** Orchestrator constructs the Fix-Gen prompt. Fix-Gen receives a JSON
object: `{file_path, rule_id, message, level, snippet_lines: [start, end], evidence}`.
Orchestrator reads `snippet_lines` from SARIF `region` and passes `±5 lines` of context
around the finding. Fix-Gen may request additional lines via `read_lines(file, start, end)`
tool call; Orchestrator validates the range is within the same file before fulfilling.

**Rejected:** Passing full file contents. Reason: violates C-P3-01 (scoped context)
and increases token cost and injection surface unnecessarily.

**Logged as:** ADR-012 (to be added to `memory/architectural_decisions.md` after Yehor signs)

### ADR-013 — iptables egress enforcement approach

**Decision:** `--cap-add NET_ADMIN` granted to scanner container. At container entrypoint,
before scanner exec: (1) resolve destination IPs via DNS, (2) apply iptables OUTPUT DROP
default policy, (3) insert ACCEPT rules for resolved IPs on ports 443/80, (4) exec scanner.
Step (1) must complete before step (2) — otherwise the resolution call itself is blocked.

**Rejected:** DNS blocklist (Option B). Reason: bypassed by raw IP addresses. The threat
model includes prompt-injection payloads that hardcode IPs specifically to evade DNS-based
controls. See Yehor's reasoning on record (2026-06-12).

**Logged as:** ADR-013 (to be added to `memory/architectural_decisions.md` after Yehor signs)

---

## 7. Open Flags

**Flag P3-A — RESOLVED 2026-06-12 (ADR-014)**  
Probe result: `docker run --rm --cap-add NET_ADMIN python:3.12-slim iptables -L` returned
`iptables: executable file not found in $PATH` — not a kernel capability error.
NET_ADMIN was granted without complaint; the WSL2 Linux VM kernel supports iptables.
The binary is simply absent from `python:3.12-slim`.

Resolution: custom `repomend-scanner:0.1.0` image (`docker/scanner.Dockerfile`) bakes
in iptables at image-build time. Runtime network access not required for the binary.
Chicken-and-egg eliminated. See ADR-014.

**Flag P3-A — FULLY CLOSED 2026-06-12**

Versions confirmed and pinned in `docker/scanner.Dockerfile`:
- semgrep 1.165.0 · bandit 1.9.4 · pip-audit 2.10.1 · eslint 8.57.1 · node 20 LTS

Image built and ID pinned:
```
repomend-scanner:0.1.0@sha256:578a8147c3604808a5c7e0f1649fc8e6a3a93610e02896d95cc36c388655a5bc
```
`BASE_IMAGE` in `docker_sandbox.py` updated. ADR-014 finalised. No open flags.
Entrypoint defect caught pre-sign-off: DNS failure after iptables DROP. Fixed by writing
`/etc/hosts` entries for allowlisted domains before applying DROP policy.

---

## Addendum

**Addendum P3-03** — `docs/intake_phase3_addendum_p3-03.md` — **SIGNED 2026-06-12**  
Covers KS-P3-03 (Fix-Gen subagent) scoping: fix trigger contract (C-P3-09), inverted-lifecycle
`fix_worktree_context` (C-P3-10), git-native checkpoint/rollback (C-P3-11), fail-safe default
`.mark_success()` sentinel (C-P3-12), ACs P3-03 through P3-08, scope-containment adversarial
case, shared-primitives drift risk. Supersedes C-P3-05/06 and ACs P3-05/P3-06 from this base
contract.

---

## Accountability Statement

_I, Yehor, have reviewed this INTAKE contract. The ADR-009 pre-step constraint table,
acceptance criteria, test contract, and adversarial cases accurately reflect Phase 3
requirements. The iptables approach (Option A, ADR-013) is approved as stated.
No build work begins until this is signed._

**Signed:** Yehor  **Date:** 2026-06-12
