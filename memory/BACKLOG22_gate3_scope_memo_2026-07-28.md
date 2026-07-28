# BACKLOG 22 — Gate 3 unsandboxed credential inheritance

## SCOPE MEMO — no fix code, nothing chosen, nothing staged

**Verified at:** `main` @ `23dc9bdb529c065653428bc0e628dc591bcb5a9c`
(fresh `git clone` from GitHub, confirmed against `git ls-remote origin main`
and the local mount's HEAD — all three agree).
**Date:** 2026-07-28 (Session 026)
**Status of this document:** scope only, hard stop. §2 boundary. No option is
chosen here; the sandbox-vs-strip call is Yehor's and is deliberately left open.

---

## 0. Premise correction — read this first

Item 22's own text contains one factual claim that **does not hold at HEAD**, and
it is load-bearing for the whole options analysis. Quoting item 22:

> "…with **no `docker_sandbox`** (grep: zero references in `verifier.py`, while
> scanners DO route through the sandbox via `pipeline.py`→`run_all_scanners`)…"

The first half is correct. **The second half is not.** `run_all_scanners` accepts
an *optional* sandbox and defaults to host execution:

```python
# scanner.py:320-328
def run_all_scanners(
    repo_path: Path,
    semgrep_rules: str = "p/python",
    sandbox: "DockerSandbox | None" = None,
) -> list[SARIFRun]:
    """
    ...
    sandbox=None → local subprocess (Phase 1 path, all existing tests unaffected)
    sandbox=DockerSandbox() → all subprocesses routed through Docker (Phase 2 path)
```

Every production call site passes **no sandbox argument**:

| Call site | Arguments passed | Effective sandbox |
|---|---|---|
| `pipeline.py:126-130` (webhook + batch path) | `run_all_scanners, repo_path, cfg.semgrep_rules` | `None` |
| `cli.py:124-126` (`patchward scan`) | `run_all_scanners(scan_path, cfg.semgrep_rules)` | `None` |
| `cli.py:290-292` (`patchward fix`) | `run_all_scanners(scan_path, cfg.semgrep_rules)` | `None` |
| `worktree.py:29` (docstring example) | `run_all_scanners(scan_path)` | `None` |

Exhaustive grep for the constructor across the tree:

```
$ grep -rn "DockerSandbox(" src/ tests/
src/patchward/docker_sandbox.py:109:        sandbox = DockerSandbox()      # ← docstring
src/patchward/scanner.py:106:    sandbox=DockerSandbox() → ...            # ← docstring
src/patchward/scanner.py:328:    sandbox=DockerSandbox() → ...            # ← docstring
tests/test_docker_sandbox.py:83,94,109,137,166,179,191,231,246,259,267,280,293,306,322,338
```

**`DockerSandbox` is never instantiated anywhere in `src/` production code.** It
exists, it is well built, it is thoroughly unit-tested — and it is not wired in.
ADR-013's container isolation is not in force on *either* path today.

**Why this matters for the decision:** Option A is not "extend the sandboxing the
scanners already have to Gate 3." There is no sandboxing in production to extend.
Option A means standing up container execution in the pipeline for the first
time, and Gate 3 would be its first customer. That is a materially larger change
than item 22's framing implies, and it is the single biggest input to the call.

*Recommend correcting item 22's text when this memo is promoted.*

---

## 1. Gate 3 runs adversarial code with no sandbox and no env control — CONFIRMED

Both exec sites, quoted verbatim. Line numbers match item 22's citation exactly.

```python
# verifier.py:744-753  (_run_pytest)
        try:
            proc = subprocess.run(
                ["python", "-m", "pytest", "--tb=short", "-q"],
                cwd=str(worktree_path),
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                encoding="utf-8",
                errors="replace",
            )
```

```python
# verifier.py:777-786  (_run_jest)
        try:
            proc = subprocess.run(
                ["npx", "jest", "--no-coverage"],
                cwd=str(worktree_path),
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                encoding="utf-8",
                errors="replace",
            )
```

Both mechanical checks:

```
$ grep -c "docker_sandbox" src/patchward/verifier.py
0
$ grep -n "env=" src/patchward/verifier.py
(no output)
```

No `env=` → the child inherits the parent's full `os.environ` by CPython default.
No sandbox → same uid, same filesystem, same network as the pipeline process.

**Reachability on the hosted path is confirmed end-to-end:**
`webhook.py:67` imports `run_repo_pipeline`; `webhook.py:333` awaits it;
`pipeline.py:206-208` calls `asyncio.to_thread(verifier.verify, …)`;
`verifier.py:228` calls `result.gate_3 = self._gate_3_test_suite(…)`.

Note `asyncio.to_thread` — Gate 3 runs on a **worker thread of the same process**,
concurrently with whatever else the event loop is doing. This is what makes
exposure (a) below a live race rather than a theoretical one.

---

## 2. Credentials in `os.environ` at Gate 3 exec time

### The governing mechanism

`CredentialProxy.load()` **only reads**; it never removes anything from
`os.environ`:

```python
# credential_proxy.py:164-176
    def load(self) -> "CredentialProxy":
        """
        Read credential values from os.environ into self._creds.
        ...
        """
        for key in _CREDENTIAL_KEYS:
            val = os.environ.get(key, "").strip()
            if val:
                self._creds[key] = val
        return self
```

`get_container_env()` (`credential_proxy.py:190-197`) *does* return a scrubbed
copy — but its only callers are `cli.py:95` and `cli.py:263`, both feeding
`assert_credentials_excluded()` for the Docker boundary that §0 shows is never
crossed in production. **The scrubbing machinery exists and is not on the path
Gate 3 takes.**

`_CREDENTIAL_KEYS` is the full list of what the codebase considers a credential:

```python
# credential_proxy.py:39-45
_CREDENTIAL_KEYS: frozenset[str] = frozenset({
    "ANTHROPIC_API_KEY",
    "LANGFUSE_PUBLIC_KEY",
    "LANGFUSE_SECRET_KEY",
    "GITHUB_TOKEN",   # KS-TRACE: AC-P5-01, C-P5-03 | Phase 5 push credential
})
```

### (a) Webhook path — Fly.io

| Variable | Enters at | In `_CREDENTIAL_KEYS`? | Stripped before Gate 3? | Exposure |
|---|---|---|---|---|
| `ANTHROPIC_API_KEY` | `fly.toml:13` secret; checked `webhook.py:318` | yes | **no** | **direct inherit** |
| `GITHUB_APP_PRIVATE_KEY_B64` | `fly.toml:14` secret; read `github_app_auth.py:50` | **NO** | **no** | **direct inherit** |
| `GITHUB_APP_PRIVATE_KEY` (raw PEM alt) | read `github_app_auth.py:47` | **NO** | **no** | **direct inherit** |
| `GITHUB_APP_ID` | `fly.toml:13`; read `github_app_auth.py:75` | **NO** | **no** | direct inherit |
| `GITHUB_WEBHOOK_SECRET` | `fly.toml:13`; read `webhook.py:238` | **NO** | **no** | **direct inherit** |
| `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` | `config.py:271,275`; `tracing.py:32-33` | yes | no | direct inherit *if set* — `fly.toml` does not list them |
| `PATCHWARD_GIT_TOKEN` | `git_credentials.py:44,119-120` | n/a (runtime-minted) | **not in parent at all** | **race-only** (see below) |
| `GITHUB_TOKEN` | — | yes | n/a | **not set on Fly** (`fly.toml` lists no such secret) |

**`PATCHWARD_GIT_TOKEN` is more contained than item 22 implies, and this is worth
stating precisely** — BACKLOG 19's fix holds here:

```python
# git_credentials.py:111-120
def credential_env(token: str) -> dict[str, str]:
    """
    ...
    The returned dict is a copy; os.environ itself is never mutated.
    """
    env = dict(os.environ)
    env[GIT_TOKEN_ENV] = token
```

So the installation token exists **only in the git child's environment**, never in
the parent. Gate 3's child does **not** inherit it. It is recoverable only by an
adversarial poller reading `/proc/<pid>/environ` of a *concurrently alive*
token-bearing git process — exactly what item 22's reviewer demonstrated, and
exactly why `asyncio.to_thread` concurrency matters. Owner-only `0400`, same uid,
so the read succeeds when the timing lands.

**The four `GITHUB_APP_*` / `GITHUB_WEBHOOK_SECRET` rows are, as far as I can
tell, new relative to item 22's write-up — and at least one is more severe than
anything item 22 records.** The App private key plus the App ID mints installation
access tokens for **every installation of the App**, not just the repo under scan.
That is a cross-tenant credential sitting in plain `os.environ`, inherited
directly by adversarial repo code, with no race required. `GITHUB_WEBHOOK_SECRET`
separately lets an attacker forge signed deliveries.

### (b) CLI path — Yehor's machine / any self-hosted run

`config.py` runs `load_dotenv()` before `CredentialProxy.load()` (stated as the
module's own assumption at `credential_proxy.py:2-3`), so everything in `.env`
lands in `os.environ` and stays there. From `.env.example`:

| Variable | In `_CREDENTIAL_KEYS`? | Exposure |
|---|---|---|
| `ANTHROPIC_API_KEY` | yes | **direct inherit** |
| `LANGFUSE_PUBLIC_KEY` | yes | **direct inherit** |
| `LANGFUSE_SECRET_KEY` | yes | **direct inherit** |
| `GITHUB_TOKEN` (long-lived fine-grained PAT) | yes | **direct inherit, no race needed** |

Item 22's summary of the CLI path is confirmed: the long-lived PAT is the worst
item here because it does not expire with the run.

---

## 3. The adversarial entry point — CONFIRMED

`cwd=str(worktree_path)` is the cloned repo's own tree. Two mechanisms give
repo-controlled code execution:

**pytest.** `conftest.py` is auto-imported by pytest at collection time, before
any test runs. It is also *itself* one of the detection triggers, so a repo
containing nothing but a hostile `conftest.py` both selects the pytest branch and
gets executed by it:

```python
# verifier.py:709-710  (_detect_test_runner)
        if (worktree_path / "conftest.py").exists():
            return "pytest"
```

**jest.** `package.json`'s `test` script and `jest.config.*` are both detection
triggers (`verifier.py:719-732`) and both are repo-controlled config that jest
evaluates as JavaScript.

There is no allowlist, no signature check, no human review, and no trust boundary
of any kind between "this repo was cloned from a webhook event" and "we exec its
code." ADR-013 already classifies the cloned repo as hostile.

---

## 4. THE DISQUALIFIER — what does Gate 3 *legitimately* need to run?

Item 22 flags this as the load-bearing unknown: sandboxing "might break legitimate
test suites that need network / build tools." **Answered from source, and the
answer is unexpectedly clean: Gate 3 legitimately needs almost nothing, because it
already cannot do most of what a real test suite requires.**

### 4.1 It installs nothing, and is designed to give up when deps are missing

```python
# verifier.py:764-768
        # SKIP (not FAIL) when tests can't run due to missing dependencies.
        # This happens for external repos whose test deps aren't installed in
        # the current Python environment — not a sign the fix is wrong.
        if "ModuleNotFoundError" in output or "ImportError" in output or "no tests ran" in output:
            return GateResult(SKIP, f"test deps not installed: {summary[:200]}")
```

There is no `pip install`, no `npm install`, no venv creation, no lockfile
resolution anywhere in the Gate 3 path. The design already accepts that a
customer's suite usually cannot run, and degrades to SKIP rather than failing the
verification.

### 4.2 It uses Patchward's own interpreter, not the repo's environment

`["python", "-m", "pytest", …]` resolves `python` from the parent's `PATH` —
Patchward's interpreter and Patchward's `site-packages`. A customer's suite passes
only in the coincidental case that its dependencies are already installed in
*Patchward's* environment. There is no per-repo environment at all.

### 4.3 Network: not needed by the pytest branch; needed by the jest branch — which is dead on the hosted path

`npx jest` would fetch jest from the npm registry when it is not installed
locally, so the jest branch does have a genuine network need. But
`docker/webhook.Dockerfile` installs only `git` and `ca-certificates` — **no
nodejs, no npm, no npx**. So on Fly:

```python
# verifier.py:789-790
        except FileNotFoundError:
            return GateResult(FAIL, "npx not found")
```

The jest branch cannot execute on the hosted path today. Its network requirement
is therefore not a real constraint on the hosted decision.

### 4.4 Filesystem: nothing beyond the worktree is *needed* (though nothing prevents more)

`cwd=worktree_path` and no path arguments. Gate 3 has no legitimate need to read
or write outside the worktree. (It is not *restricted* to it — that is the finding
— but restricting it breaks no stated capability.)

### 4.5 Disqualifier verdict

**Full sandboxing does not break a capability Gate 3 actually has.** The
"might break legitimate suites" concern is largely already realised as SKIP-or-FAIL
in today's behaviour. If Gate 3 ran in a container with the repo mounted
read-only, no network, and credentials stripped, the observable outcome for the
overwhelming majority of customer repos would be **the same SKIP it already
returns** — because the deps still would not be installed.

**But the constraint that actually bites Option A is a different one, and it is
infrastructural, not behavioural:** there is no Docker on the Fly host.
`webhook.Dockerfile` installs no Docker CLI, and a Fly machine does not expose a
Docker daemon. Combined with §0 (the sandbox is not wired into production
anywhere), Option A on the hosted path is **new infrastructure**, not a wiring
change. That — not "will it break test suites" — is the real cost question.

---

## 5. Adjacent finding surfaced by this trace (flagged, NOT folded in)

Reasoning about the hosted runtime image, **not yet empirically confirmed — treat
as Tier 1 and verify before acting:**

`pyproject.toml` puts `pytest` in `[dependency-groups].dev`, while
`webhook.Dockerfile` installs `uv pip install --system --no-cache .[webhook]`
where `webhook = [fastapi, uvicorn[standard], pyjwt[crypto], httpx]`. If pytest is
genuinely absent from the deployed image, `python -m pytest` emits
`No module named pytest` — which contains **none** of the three SKIP triggers at
`verifier.py:767` (`ModuleNotFoundError` / `ImportError` / `no tests ran`) — so it
returns **FAIL**, not SKIP. Then:

```python
# verifier.py:110
        g3_ok = self.gate_3.status in (PASS, SKIP)
```
```python
# pipeline.py:220-227
                            if (
                                verify_result.verification_status
                                != "verified"
                            ):
                                finding_status = "verify_failed"
```

→ no PR is ever published on the hosted path, for any pytest-detecting repo.

**This converges with BACKLOG 21** ("the webhook likely cannot push a PR at all")
from a completely independent direction. It is a functional launch-blocker
candidate, not a security finding, and it belongs to 21's investigation — noted
here, deliberately not folded into 22. Confirming it needs one command against the
deployed image, which this memo does not run (§2 discipline).

---

## 6. Options — laid out, NOT chosen

The sandbox-vs-strip call is Yehor's. Each option below is stated with what it
breaks, what it costs, and what residual risk survives it.

### Option A — run Gate 3 inside `docker_sandbox`

Repo mounted read-only, `NetworkPolicy.OFFLINE`, credentials structurally excluded
by `_build_docker_cmd`'s existing `if key not in _CREDENTIAL_KEYS` filter
(`docker_sandbox.py:174-178`).

**What it breaks (given §4):** essentially nothing that works today. Suites that
currently SKIP still SKIP. The jest branch is already dead on the hosted path. The
only real loss is the coincidental case where a customer's deps happen to be
present in Patchward's own image and the suite currently runs for real — that case
would move to SKIP unless the scanner image also carries those deps.

**What it costs:** the large one. (1) Docker is not available on Fly — this needs
either a different execution host, a Fly machine with a Docker daemon, or an
external runner. (2) Per §0, the sandbox has never been wired into production, so
this is the first production use of `DockerSandbox` and inherits BACKLOG 17's
un-rebuilt image (`BASE_IMAGE` still pins `patchward-scanner:0.1.0@sha256:578a8147…`
with the legacy `repomend-entrypoint`). (3) Container startup per finding, per
repo. (4) `_CREDENTIAL_KEYS` must be widened first (§2a) or the filter will happily
forward `GITHUB_APP_PRIVATE_KEY_B64` into the container.

**Residual risk:** adversarial code still executes, just with no credentials, no
network and a read-only mount — the ADR-013 posture. Container escape remains the
tail risk. `/proc` racing against a concurrent git process is closed, since the
child is in a separate PID namespace.

### Option B — spawn Gate 3 with an explicit scrubbed `env=`

`subprocess.run(…, env=<os.environ minus all credential keys>)`, plus a scheduling
rule that Gate 3 never overlaps in time with a token-bearing git process.

**What it breaks:** nothing observable. A one-line-per-call-site change at
`verifier.py:745` and `:778`. `get_container_env()` already computes exactly the
right dict — though note it filters only `_CREDENTIAL_KEYS`, so **this option is
wrong until `_CREDENTIAL_KEYS` is widened** to cover `GITHUB_APP_PRIVATE_KEY_B64`,
`GITHUB_APP_PRIVATE_KEY`, `GITHUB_APP_ID` and `GITHUB_WEBHOOK_SECRET`. As written
today it would strip the Anthropic key and leave the App private key behind.

**What it costs:** small. No infrastructure. The non-overlap requirement is the
awkward part — `pipeline.py` currently runs verify via `asyncio.to_thread` with no
scheduling constraint relative to git operations, so enforcing non-overlap means
real coordination (a lock, or serialising the git and verify phases), and getting
it subtly wrong reopens the `/proc` race silently.

**Residual risk:** substantial and worth stating plainly — **adversarial code still
runs as the same uid with full filesystem and network access.** It just cannot read
credentials out of its own environment. It can still read files the pipeline user
can read (including `~/.gitconfig`, the SQLite DBs under `runs/`, other repos'
worktrees), exfiltrate over the network, and poll `/proc` for anything the
non-overlap rule fails to exclude. This is mitigation, not containment.

### Option C — hybrid

Ship B now as the immediate mitigation (small, no infrastructure, closes the
direct-inherit path that is today's demonstrated exfiltration), and treat A as the
target posture once the BACKLOG 17 image rebuild and a Docker-capable execution
host exist.

**What it breaks:** nothing immediately.

**What it costs:** two changes to the same boundary instead of one, and the honest
risk that B ships and A never does because the pressure is off. If C is chosen it
should carry a written trigger for when A lands (e.g. "before Marketplace listing"
or "with BACKLOG 17"), or it is functionally just B.

**Residual risk:** B's residual risk for however long the interim lasts.

---

## 7. HARD STOP

Nothing implemented. No option chosen. Nothing staged. No adversarial pass run on
this memo (that belongs to the eventual diff, not the scope).

**Decisions that are Yehor's, in the order they gate each other:**

1. **Widen `_CREDENTIAL_KEYS`?** Independent of A/B/C and required by both A and B.
   Candidate spin-off item **25**.
2. **A, B, or C** — the sandbox-vs-strip call, now informed by "sandboxing breaks
   almost nothing behaviourally, but needs infrastructure Fly doesn't have."
3. **Wire `DockerSandbox` into production at all?** Per §0 it never has been, which
   is a wider ADR-013 gap than Gate 3. Candidate spin-off item **26**.
4. **Confirm or refute §5** (hosted Gate 3 hard-FAILs on missing pytest → no PR).
   Belongs to BACKLOG 21.

Per H11: this pass spawned candidates 25 and 26 as predicted, plus a convergence
onto 21. Recorded as spin-offs, not folded in.
