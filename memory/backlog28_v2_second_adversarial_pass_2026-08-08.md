# BACKLOG 28 — v2 Second Adversarial Pass

**Reviewer role:** Independent adversarial security reviewer, second pass. Did not author the code, did not read the v1/v2 write-ups, `*BACKLOG28*`, `*adversarial_review*`, or `*v2_implementation*` files. View formed from the diff first.
**Date:** 2026-08-08
**Scope:** `src/patchward/webhook.py` + `tests/test_webhook.py` (the two amendments applied, uncommitted, in the working tree).
**Constraint honored:** read + run only. No `git add/commit/push`, no `apply`, no writes into the repo source. This report is the only file written.

---

## Verdict (up front)

**NOT CLEAN — no security defect, but two legitimate low-severity correctness gaps that should be fixed or explicitly accepted before staging.**

The v2 amendments do close the things they set out to close: the substring bypass (F1) is genuinely replaced by a real PEM parse, and the error path leaks nothing (STEP 4 verified with a secret-bearing malformed key). The security-critical properties hold. But the guard's own stated goal — *"fail loud on a present-but-wrong credential, never false-boot a working one"* — is violated in two places I could reproduce:

- **F-A (MEDIUM, residual instance of the exact target bug class):** a non-RSA private key (EC / Ed25519 / DSA) passes the guard but breaks the `RS256` consumer deep in a background task on the first webhook. The guard validates *"is a parseable private key"*; the consumer requires *"is an RSA key usable for RS256."*
- **F-B (LOW–MEDIUM, false boot):** the consumer reads `GITHUB_APP_PRIVATE_KEY_B64` **only when `GITHUB_APP_PRIVATE_KEY` is absent**, but the guard validates B64 **unconditionally**. A valid RAW key plus a stale/garbage B64 value — a working configuration — **fails the boot**. This directly contradicts the F2 comment's claim to *"accept/reject precisely what the consumer can/cannot use."*

Neither is a credential leak or an auth bypass. Both are cheap to fix. Details, reproductions, and the honest "solid" list below.

---

## Environment (for honest comparison)

| | This pass | Prior report (per task brief) | Real gate |
|---|---|---|---|
| OS | Linux 6.8.0 (sandbox) | Linux (3.10.12) | **Windows** |
| Python | 3.10.12 | 3.10.12 | **3.14.4** |
| cryptography | **50.0.0** (via `/tmp/tenv`) | 50.0.0 | (unknown) |
| pyjwt | 2.13.0 | (n/s) | (unknown) |

I ran the guard and the RS256 consumer against **cryptography 50.0.0**, which **matches the prior report's version**, so the parse/exception behavior below is directly comparable to it. I am on **Linux, not the Windows 3.14.4 gate interpreter** — I cannot execute the real gate here, so every gate number in STEP 5 is labeled **ADVISORY**. (The repo's own `.venv` is a Windows layout, `.venv/Lib/...`, and is not runnable in this Linux sandbox; I used a separate Linux venv with matching library versions.)

---

## STEP 1 — Fresh H24 consumer sweep (not inherited)

Enumerated every consumer under `src/` from scratch (`grep`, then read the consuming code). Result per credential:

| Credential | Real consumer | What consumer needs | Guard check | Match? |
|---|---|---|---|---|
| `ANTHROPIC_API_KEY` | `config.py:279`, pipeline guard `webhook.py:438`; value handed to Anthropic SDK | non-empty; real keys are `sk-ant-…`, ~100+ chars | prefix `sk-ant-` + `len ≥ 20` | ✅ sound; floor is low enough never to reject a real key |
| `GITHUB_APP_ID` | `github_app_auth.py:75` → used as JWT `iss` string | numeric App ID | `isascii() and isdigit()` | ✅ correct; F4 (non-ASCII digit) genuinely closed |
| `GITHUB_APP_PRIVATE_KEY` (raw) | `github_app_auth._load_private_key:47` → `pyjwt.encode(RS256)` | **RSA** PEM parseable by pyjwt | `load_pem_private_key(...)` | ⚠️ parses any key type, not just RSA → **F-A** |
| `GITHUB_APP_PRIVATE_KEY_B64` | `_load_private_key:50` — **only if RAW absent** | b64 → utf-8 → **RSA** PEM | b64decode→utf-8→parse, **unconditional** | ⚠️ ignores consumer precedence → **F-B**; also **F-A** |
| `GITHUB_WEBHOOK_SECRET` | `verify_signature:360` (HMAC) | non-empty; no "shape" | warn-only on absence | ✅ correct (nothing to shape-check) |

**Re-checked from scratch, as instructed:**

- **`GITHUB_TOKEN`** — consumed by `pr_publisher.py`, `cli.py`. **Correctly NOT validated.** `credential_proxy.py:68` and `git_credentials.py:84` document that the hosted Fly webhook has *no* `GITHUB_TOKEN` secret at all (it uses the App-token flow). Validating it at boot would false-fail every hosted deploy. Omission is the right call.
- **`LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY`** — consumed by `tracing.py:32-33`, which **warns and continues** if unset (optional observability). **Correctly NOT validated.** Shape-checking optional creds would create false boot failures.

Coverage choices are sound. The two ⚠️ rows are the findings below.

---

## STEP 2 — Attacks on the NEW code (`load_pem_private_key`)

Ran guard vs. real `pyjwt.encode(..., algorithm="RS256")` consumer, cryptography 50.0.0:

| Input | Guard | RS256 consumer | Assessment |
|---|---|---|---|
| **EC / P-256 key** (raw) | **PASS (boot ok)** | **FAILS** `InvalidKeyError` | **F-A — gap** |
| **EC / P-256 key** (B64) | **PASS (boot ok)** | — | **F-A — gap** |
| **Ed25519 key** (raw) | **PASS (boot ok)** | **FAILS** `InvalidKeyError` | **F-A — gap** |
| RSA key (control) | PASS | works | ✅ |
| **Encrypted RSA** (password PEM, `password=None`) | **RAISE (boot fails)** | fails `TypeError` | ✅ consistent; `TypeError` is an `Exception`, caught by the bare `except Exception` — no divergent-exception escape |
| **RSA *public* key** | **RAISE (boot fails)** | fails | ✅ consistent (`ValueError`, caught) |
| **B64 → non-UTF-8 bytes** (`\xff\xfe…`) | **RAISE (boot fails)** | — | ✅ `UnicodeDecodeError` from `.decode("utf-8")` is caught by the surrounding `except Exception`; matches the consumer's own decode |

### F-A (MEDIUM) — non-RSA private key passes the guard, breaks the consumer

`load_pem_private_key()` happily parses EC, Ed25519, and DSA keys. But the sole consumer signs with **RS256**, which requires an **RSA** key; pyjwt raises `InvalidKeyError` at `generate_app_jwt()` — deep inside a background task, on the first real webhook, *after* signature verification. That is **precisely the failure mode BACKLOG 28 exists to eliminate** (present-but-wrong credential passes boot, detonates on first request). The guard validates a *weaker* property (parseable private key) than the consumer requires (RSA private key).

- **Likelihood: low.** GitHub only issues **RSA** private keys for GitHub Apps, so a legitimately-obtained App key is always RSA. F-A fires only if an operator pastes the *wrong kind* of key entirely.
- **Fix (one line):** after parsing, assert the type, e.g. `isinstance(key, rsa.RSAPrivateKey)`, else append an error. Closes the gap without touching the happy path.

### Encrypted / public / non-UTF-8 — all handled correctly
The encrypted-PEM case is worth calling out because the brief flagged it: an encrypted key raises `TypeError` ("Password was not given…"), **not** the `ValueError` a malformed key raises — but the guard's `except Exception` catches **both**, so there is no divergent-exception escape. Boot fails loud, and the consumer couldn't use an encrypted key either, so failing is correct (not a false positive).

---

## STEP 3 — Do the regression tests exercise the real fix?

Method: copied `src/` + `tests/` to a writable scratch dir, **reverted only the `load_pem_private_key` calls back to the v1 `"PRIVATE KEY" in …` substring check** (both branches), left everything else intact, and re-ran the four new F1/F2 regression tests.

| Test | vs. mutated (v1-substring) guard | Verdict |
|---|---|---|
| `test_junk_pem_that_matches_substring_is_rejected` | **FAILED** ("DID NOT RAISE") | ✅ genuinely exercises the fix |
| `test_startup_rejects_bad_raw_private_key` | **FAILED** | ✅ genuinely exercises the fix |
| `test_startup_rejects_unparseable_b64_pem` | **PASSED** | ⚠️ **F-C — non-discriminating** |
| (`test_startup_rejects_invalid_b64_private_key` — invalid base64, not a parse test) | n/a | fine as a decode test |

### F-C (LOW) — B64-branch F1 upgrade has no discriminating test

`test_startup_rejects_unparseable_b64_pem` feeds a payload (`b"this is valid utf-8 text but is definitely not a PEM key"`) that **does not contain the `"PRIVATE KEY"` substring**, so it is rejected by *both* the old substring check and the new parse — it passes against the broken guard too. The **raw** branch has a proper discriminating test (`test_junk_pem_that_matches_substring_is_rejected`, junk **with** the substring); the **B64** branch does not.

I confirmed the *code* is nonetheless correct: routing a junk-PEM-**with**-substring through the B64 branch, the mutated v1 guard **accepts** it (boot ok) while the **real v2 guard RAISES**. So the fix works on the B64 branch — it's the *test guarantee* that is weaker than claimed. **Fix:** add one test that base64-encodes `-----BEGIN PRIVATE KEY-----\nGARBAGE\n-----END PRIVATE KEY-----` and asserts the guard raises.

For completeness, against the **real v2 guard** all 13 startup tests pass (see STEP 5).

---

## STEP 4 — Credential-leak re-check on the NEW code

Traced whether any `load_pem_private_key` exception (which can carry parser-state fragments in some versions) reaches a log line, error message, or re-raise.

- The parse is wrapped in `try: … except Exception:` and the handler appends a **static string** — `"GITHUB_APP_PRIVATE_KEY is set but is not a valid PEM private key"`. The **caught exception object is never referenced** (no `as e`, not formatted, not logged). Same pattern on the B64 branch.
- `errors` is joined and both logged (`logger.error("… %s", joined)`) and put in `StartupCredentialError` — but `errors` only ever contains those static, name-plus-kind strings. No credential value or substring is ever added.

**Empirical check:** set `GITHUB_APP_PRIVATE_KEY` to a malformed PEM whose body was `SUPERSECRETKEYMATERIAL_shouldNeverLeak_AAAA`, ran the guard, captured the raised message:

```
error message: 'GITHUB_APP_PRIVATE_KEY is set but is not a valid PEM private key'
secret substring present in msg?: False
```

Also confirmed `test_startup_error_never_contains_credential_value` passes against the real guard. **No leak. Clean on this axis.**

---

## STEP 5 — Gate readiness (ADVISORY — not the Windows 3.14.4 gate)

Run on Linux / Python 3.10.12 / cryptography 50.0.0 / pyjwt 2.13.0, coverage plugin disabled (the mounted `.coverage` is read-only in this sandbox — a harness artifact, not a code issue).

- **`tests/test_webhook.py`: 40 passed, 0 failed.** All 13 BACKLOG-28 startup tests included.
- **Full suite: 561 passed, 11 skipped, 8 failed.**

The 8 failures are **environmental, not caused by this change** — none touch `webhook.py`:

- `tests/test_docker_sandbox.py` (6) — require a Docker daemon; fail with the `docker run` subprocess returning 255 / `FileNotFoundError` (no Docker in this sandbox).
- `tests/test_fix_gen.py::test_fix_gen_scope_containment_subprocess_shell_true` (1) — subprocess/infra.
- `tests/test_golden_dataset.py::test_verifier_end_to_end_failed_out_of_bounds` (1) — verifier harness/infra.

**ADVISORY caveat:** these numbers are from a Linux interpreter with cryptography 50.0.0, **not** the Windows Python 3.14.4 gate. The webhook/credential-guard results should port cleanly (pure-Python + cryptography/pyjwt), but the 8 infra failures may resolve or shift on a host that actually has Docker. Re-run on the real gate before trusting the totals.

---

## STEP 6 — Verdict detail

**What I specifically tried to break, and what held:**

- Substring bypass (the v1 hole) → **closed.** Junk-with-header now fails the parse on both raw and B64 branches (verified by mutation + direct repro).
- Exception-type escape (encrypted PEM raising `TypeError` vs. malformed raising `ValueError`) → **no escape;** bare `except Exception` catches both.
- B64 `.decode("utf-8")` on non-UTF-8 bytes → **handled;** `UnicodeDecodeError` is caught, matches the consumer's decode.
- Credential leakage via parser-state in exception text → **none;** exception object never touched, verified with a secret-bearing key.
- `GITHUB_TOKEN` / LANGFUSE omission → **correct;** validating them would false-fail the hosted deploy.

**What broke:**

- **F-A (MEDIUM):** non-RSA private key passes the guard, then breaks `RS256` on the first webhook — a residual instance of the very bug class the guard targets. Low likelihood (GitHub App keys are always RSA), one-line fix (`isinstance(..., rsa.RSAPrivateKey)`).
- **F-B (LOW–MEDIUM):** guard validates `GITHUB_APP_PRIVATE_KEY_B64` unconditionally, but the consumer reads it **only when RAW is absent**. Valid RAW + stale/garbage B64 = a working config that the guard **false-fails at boot** — reproduced. Contradicts the F2 comment's own "accept/reject precisely what the consumer can use" claim. Fix: mirror the consumer's precedence (skip B64 validation when a valid RAW key is present, or validate that *at least one* usable key exists rather than that *every* set variable is valid).
- **F-C (LOW):** the B64-branch F1 fix has no discriminating regression test; the existing one passes against the broken guard too. Code is correct; add one substring-in-B64 test.

**Why NOT CLEAN rather than CLEAN:** the security posture is sound (no leak, no bypass, fail-loud replaces silent-pass), so none of these block on *security* grounds. But this is the pass that decides staging, and F-A and F-B are genuine correctness defects measured against the guard's own stated contract — F-A lets a wrong credential through (the target bug class), F-B rejects a right one (a new false-boot the guard was meant to avoid). They are cheap to fix. **Recommendation: fix F-A and F-B (and add the F-C test) before staging, or record them as explicitly-accepted known low-risk items.** If the author's judgment is that non-RSA keys and dual-set-with-stale-B64 are out of scope, v2 is safe to stage as-is — but that should be a written decision, not a silent gap.

---

*Reproductions available on request; all runs above were read-only. No repo writes were made except this report.*
