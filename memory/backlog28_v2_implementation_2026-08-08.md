# BACKLOG 28 — Startup Credential Guard, v2 amendment

**Date:** 2026-08-08
**Author:** Claude (agent), amending in place at Yehor's direction
**Scope:** Address adversarial-review findings F1–F5 on the (uncommitted) BACKLOG 28 patch.
**Files touched this round:** `src/patchward/webhook.py`, `tests/test_webhook.py`
**Staging/commit status:** nothing staged, nothing committed, nothing pushed (see §7).

---

## 0. Environment / gate interpreter — READ THIS FIRST (a real gap)

The instructions asked me to confirm the gate interpreter
`D:\Dev\Projects\Patchward\.venv\Scripts\python.exe` prints `3.14.4` and to
run the suite with it. **I could not execute that interpreter**, and I did not
fabricate a run that used it. The honest situation:

- The gate venv is a **Windows** virtualenv (`.venv\Scripts\*.exe`, no `bin/`).
  My execution shell is an **isolated Linux sandbox**; a Windows `.exe` cannot
  run there. The desktop terminal is available to me only at a tier that blocks
  typing, so I could not drive PowerShell to run it either.
- I **did** verify the gate interpreter's version *declaratively*:
  `.venv/pyvenv.cfg` states `version_info = 3.14.4` and `home = C:\Python314`.
  That confirms the pin is 3.14.4, but it is **not** the same as watching the
  binary print it.
- To provision an equivalent CPython 3.14 inside the sandbox, `uv` tried to
  download python-build-standalone from GitHub and was **blocked by the sandbox
  network allowlist**. So a true 3.14 run was not possible here either.

**What I actually ran the tests on:** CPython **3.10.12** (Linux) in a fresh venv
with the project's exact webhook + dev dependency set installed from PyPI,
including **cryptography 50.0.0** (the gate's own site-packages has cryptography
48.0.0 — same major behavior for `load_pem_private_key` and `base64`).

**Why this is still trustworthy, and how to close the gap:**
- The webhook module's **baseline count reproduced exactly** on 3.10 (36 passed),
  matching the number you cited for the gate, which is strong evidence the module
  behaves identically.
- The credential-guard logic uses only stdlib `base64` and `cryptography` APIs
  whose behavior is stable across 3.10→3.14.
- **Action for you:** please re-run the two commands on the real gate before
  relying on the numbers as gate-official:
  ```
  & "D:\Dev\Projects\Patchward\.venv\Scripts\python.exe" -m pytest tests\test_webhook.py -v
  & "D:\Dev\Projects\Patchward\.venv\Scripts\python.exe" -m pytest -q
  ```
  I expect webhook = 40 passed, and the full suite = your ~567 baseline **+ 4**.

---

## 1. What changed and why (F1–F5)

### F1 — substring check → real PEM parse (both branches)
The v1 guard accepted `GITHUB_APP_PRIVATE_KEY` / `..._B64` if the text merely
*contained* `PRIVATE KEY`. A well-formed header wrapped around garbage passed.
Both branches now attempt an actual
`load_pem_private_key(key_bytes, password=None, backend=default_backend())`
and append an error if it raises.

### F2 — B64 decode now mirrors the consumer EXACTLY
The real consumer (`src/patchward/github_app_auth.py`, lines 47–52) does:
```python
encoded = os.environ.get("GITHUB_APP_PRIVATE_KEY_B64", "").strip()
if encoded:
    return base64.b64decode(encoded).decode("utf-8")
```
i.e. `.strip()` → `base64.b64decode(...)` **with the default `validate` flag
(`validate=False`)** → `.decode("utf-8")`, in that order. The v1 guard diverged:
it used `base64.b64decode(b64_key, validate=True)` and never `.decode("utf-8")`.
That divergence meant the guard could **reject a value the consumer accepts**
(e.g. line-wrapped base64) — a false boot failure. The guard now performs the
identical `base64.b64decode(b64_key).decode("utf-8")` before parsing the PEM.

### F3 — minimum length on ANTHROPIC_API_KEY
After the `sk-ant-` prefix check, reject if `len(value) < 20`. Real keys are
~100+ chars, so the floor is deliberately permissive and cannot reject a genuine
key; it catches truncated pastes / stubs that still carry the prefix.

### F4 — GITHUB_APP_ID ASCII-digit check
`str.isdigit()` is `True` for non-ASCII digit characters (superscripts, other
scripts) that are not usable as a GitHub App ID. Changed to
`app_id.isascii() and app_id.isdigit()`.

### F5 — the three missing tests + the F1 exploit regression test
Added (see §3):
- `test_startup_rejects_bad_raw_private_key`
- `test_startup_rejects_invalid_b64_private_key`
- `test_startup_rejects_unparseable_b64_pem`
- `test_junk_pem_that_matches_substring_is_rejected` (the F1 exploit repro)

### Necessary collateral edits to pre-existing v1 tests (disclosed)
The F1/F3 changes made two *existing* "accepts"-path fixtures invalid, so I
updated them (they would otherwise break for the wrong reason):
- `test_startup_accepts_valid_b64_private_key` used a **fake** PEM
  (`...\nZm9v\n...`, i.e. "foo") that real parsing correctly rejects — replaced
  with a genuine, freshly generated RSA key.
- Short stub Anthropic fillers (`sk-ant-ok`, `sk-ant-test-value`) that are now
  too short under F3 were replaced with a valid `_VALID_ANTHROPIC_KEY`
  constant so each "rejects" test still isolates its intended failure.

---

## 2. Full diff of everything changed this round (v1 → v2)

This is the precise **v2-only** diff: I reconstructed the v1 files by applying
`backlog28_startup_credential_guard.patch` to `HEAD` in a scratch copy, then
diffed against the current working tree. (Because the v1 patch is itself
uncommitted, a plain `git diff` would fold v1 + v2 together; this isolates the
amendment.)

```diff
=== src/patchward/webhook.py (v1 -> v2) ===
--- v1/src/patchward/webhook.py	2026-08-08 16:00:35.641886607 +0200
+++ b/src/patchward/webhook.py	2026-08-08 15:57:06.900400500 +0200
@@ -40,6 +40,8 @@
 from contextlib import asynccontextmanager
 from pathlib import Path
 
+from cryptography.hazmat.backends import default_backend
+from cryptography.hazmat.primitives.serialization import load_pem_private_key
 from fastapi import BackgroundTasks, FastAPI, Header, HTTPException, Request
 
 from patchward import installations_db as idb
@@ -100,34 +102,75 @@
     errors: list[str] = []
 
     anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
-    if anthropic_key and not anthropic_key.startswith("sk-ant-"):
-        errors.append(
-            "ANTHROPIC_API_KEY is set but does not begin with the expected "
-            "'sk-ant-' prefix"
-        )
-    elif not anthropic_key:
+    if anthropic_key:
+        if not anthropic_key.startswith("sk-ant-"):
+            errors.append(
+                "ANTHROPIC_API_KEY is set but does not begin with the expected "
+                "'sk-ant-' prefix"
+            )
+        elif len(anthropic_key) < 20:
+            # F3 (BACKLOG 28 v2): a value with the right prefix but far too
+            # short to be a real key (e.g. a truncated paste or an "sk-ant-ok"
+            # stub). Floor kept deliberately low — real keys are ~100+ chars,
+            # so this never rejects a genuine credential.
+            errors.append(
+                "ANTHROPIC_API_KEY is set but is too short to be a valid key"
+            )
+    else:
         logger.warning("[webhook] ANTHROPIC_API_KEY is not set at startup")
 
     app_id = os.environ.get("GITHUB_APP_ID", "").strip()
-    if app_id and not app_id.isdigit():
+    if app_id and not (app_id.isascii() and app_id.isdigit()):
+        # F4 (BACKLOG 28 v2): str.isdigit() returns True for non-ASCII digit
+        # characters (e.g. superscripts or digits from other scripts) that are
+        # NOT usable as a GitHub App ID. Require ASCII decimal digits only.
         errors.append("GITHUB_APP_ID is set but is not a numeric App ID")
 
     b64_key = os.environ.get("GITHUB_APP_PRIVATE_KEY_B64", "").strip()
     if b64_key:
+        # F2 (BACKLOG 28 v2): mirror the real consumer's decode EXACTLY
+        # (github_app_auth.py:50-52) — same .strip(), same base64.b64decode()
+        # with the default validate flag (validate=False), same .decode("utf-8"),
+        # in the same order — so the guard accepts/rejects precisely what the
+        # consumer can/cannot use. A stricter decode here (e.g. validate=True)
+        # would reject values the consumer accepts and cause false boot failures.
         try:
-            decoded = base64.b64decode(b64_key, validate=True)
-        except ValueError:
-            errors.append("GITHUB_APP_PRIVATE_KEY_B64 is set but is not valid base64")
+            decoded_pem = base64.b64decode(b64_key).decode("utf-8")
+        except Exception:
+            errors.append(
+                "GITHUB_APP_PRIVATE_KEY_B64 is set but could not be base64-decoded "
+                "to UTF-8 text (does not match the consumer's decode)"
+            )
         else:
-            if b"PRIVATE KEY" not in decoded:
+            # F1 (BACKLOG 28 v2): actually parse the PEM instead of a substring
+            # check, so a well-formed header wrapped around garbage is rejected.
+            try:
+                load_pem_private_key(
+                    decoded_pem.encode("utf-8"),
+                    password=None,
+                    backend=default_backend(),
+                )
+            except Exception:
                 errors.append(
-                    "GITHUB_APP_PRIVATE_KEY_B64 is set but does not decode to a "
-                    "PEM private key"
+                    "GITHUB_APP_PRIVATE_KEY_B64 is set but is not a valid PEM "
+                    "private key"
                 )
 
     raw_key = os.environ.get("GITHUB_APP_PRIVATE_KEY", "").strip()
-    if raw_key and "PRIVATE KEY" not in raw_key:
-        errors.append("GITHUB_APP_PRIVATE_KEY is set but is not a PEM private key")
+    if raw_key:
+        # F1 (BACKLOG 28 v2): actually attempt to parse the PEM. The prior
+        # `"PRIVATE KEY" in raw_key` substring check accepted a valid-looking
+        # header wrapped around a garbage body (the adversarial junk-PEM repro).
+        try:
+            load_pem_private_key(
+                raw_key.encode("utf-8"),
+                password=None,
+                backend=default_backend(),
+            )
+        except Exception:
+            errors.append(
+                "GITHUB_APP_PRIVATE_KEY is set but is not a valid PEM private key"
+            )
 
     if not os.environ.get("GITHUB_WEBHOOK_SECRET", "").strip():
         logger.warning("[webhook] GITHUB_WEBHOOK_SECRET is not set at startup")

=== tests/test_webhook.py (v1 -> v2) ===
--- v1/tests/test_webhook.py	2026-08-08 16:00:35.641886607 +0200
+++ b/tests/test_webhook.py	2026-08-08 15:58:34.966169900 +0200
@@ -8,6 +8,8 @@
 from pathlib import Path
 
 import pytest
+from cryptography.hazmat.primitives import serialization
+from cryptography.hazmat.primitives.asymmetric import rsa
 from fastapi.testclient import TestClient
 
 from patchward import webhook
@@ -610,6 +612,30 @@
 # manager, so they never trigger the lifespan and are unaffected by this guard.
 # ---------------------------------------------------------------------------
 
+# A realistic, > 20-char valid-shaped Anthropic key for the "accepts" path and
+# as filler where the Anthropic value is not the subject under test. BACKLOG 28
+# v2 (F3) adds a minimum-length check, so short stubs like "sk-ant-ok" no longer
+# pass the guard and cannot be used as innocuous filler.
+_VALID_ANTHROPIC_KEY = "sk-ant-api03-" + "a" * 24
+
+
+def _real_private_key_pem() -> bytes:
+    """A genuine, parseable RSA private key PEM (generated fresh — never a real
+    secret). BACKLOG 28 v2 (F1) replaces the guard's substring check with an
+    actual load_pem_private_key() parse, so the "accepts" tests must use a key
+    that really parses, not a header wrapped around filler bytes."""
+    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
+    return key.private_bytes(
+        encoding=serialization.Encoding.PEM,
+        format=serialization.PrivateFormat.TraditionalOpenSSL,
+        encryption_algorithm=serialization.NoEncryption(),
+    )
+
+
+# Generated once per module run — RSA keygen is comparatively expensive.
+_VALID_PRIVATE_KEY_PEM = _real_private_key_pem()
+
+
 def _clear_app_creds(monkeypatch: pytest.MonkeyPatch) -> None:
     for k in (
         "GITHUB_APP_ID",
@@ -634,7 +660,7 @@
 
 
 def test_startup_accepts_valid_anthropic_key(monkeypatch: pytest.MonkeyPatch) -> None:
-    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-value")
+    monkeypatch.setenv("ANTHROPIC_API_KEY", _VALID_ANTHROPIC_KEY)
     _clear_app_creds(monkeypatch)
     webhook._validate_credential_shapes()  # must not raise
 
@@ -646,7 +672,7 @@
 
 
 def test_startup_rejects_non_numeric_app_id(monkeypatch: pytest.MonkeyPatch) -> None:
-    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-ok")
+    monkeypatch.setenv("ANTHROPIC_API_KEY", _VALID_ANTHROPIC_KEY)
     _clear_app_creds(monkeypatch)
     monkeypatch.setenv("GITHUB_APP_ID", "not-numeric")
     with pytest.raises(webhook.StartupCredentialError):
@@ -654,7 +680,7 @@
 
 
 def test_startup_rejects_bad_b64_private_key(monkeypatch: pytest.MonkeyPatch) -> None:
-    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-ok")
+    monkeypatch.setenv("ANTHROPIC_API_KEY", _VALID_ANTHROPIC_KEY)
     _clear_app_creds(monkeypatch)
     # valid base64, but does not decode to a PEM private key
     monkeypatch.setenv(
@@ -665,10 +691,13 @@
 
 
 def test_startup_accepts_valid_b64_private_key(monkeypatch: pytest.MonkeyPatch) -> None:
-    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-ok")
+    monkeypatch.setenv("ANTHROPIC_API_KEY", _VALID_ANTHROPIC_KEY)
     _clear_app_creds(monkeypatch)
-    pem = b"-----BEGIN RSA PRIVATE KEY-----\nZm9v\n-----END RSA PRIVATE KEY-----\n"
-    monkeypatch.setenv("GITHUB_APP_PRIVATE_KEY_B64", base64.b64encode(pem).decode())
+    # A genuine, parseable PEM — the guard now really parses it (BACKLOG 28 v2).
+    monkeypatch.setenv(
+        "GITHUB_APP_PRIVATE_KEY_B64",
+        base64.b64encode(_VALID_PRIVATE_KEY_PEM).decode(),
+    )
     monkeypatch.setenv("GITHUB_APP_ID", "123456")
     webhook._validate_credential_shapes()  # must not raise
 
@@ -694,3 +723,72 @@
     with pytest.raises(webhook.StartupCredentialError):
         with TestClient(webhook.app):
             pass
+
+
+# ---------------------------------------------------------------------------
+# BACKLOG 28 v2 — regression tests for the adversarial-review findings.
+# F1: substring check accepted a valid header wrapped around garbage.
+# F2: the guard's base64 decode diverged from the real consumer's decode.
+# These would have FAILED against v1 and must PASS against v2.
+# ---------------------------------------------------------------------------
+
+def test_startup_rejects_bad_raw_private_key(
+    monkeypatch: pytest.MonkeyPatch,
+) -> None:
+    """A raw GITHUB_APP_PRIVATE_KEY that CONTAINS the 'PRIVATE KEY' substring
+    but is not a parseable PEM must now be rejected (v1 accepted it)."""
+    monkeypatch.setenv("ANTHROPIC_API_KEY", _VALID_ANTHROPIC_KEY)
+    _clear_app_creds(monkeypatch)
+    monkeypatch.setenv(
+        "GITHUB_APP_PRIVATE_KEY",
+        "-----BEGIN RSA PRIVATE KEY-----\n"
+        "this is not real base64 key material\n"
+        "-----END RSA PRIVATE KEY-----\n",
+    )
+    with pytest.raises(webhook.StartupCredentialError):
+        webhook._validate_credential_shapes()
+
+
+def test_startup_rejects_invalid_b64_private_key(
+    monkeypatch: pytest.MonkeyPatch,
+) -> None:
+    """Input that is not valid base64 at all must be rejected with a clear
+    message (the guard's decode now mirrors the consumer's b64decode)."""
+    monkeypatch.setenv("ANTHROPIC_API_KEY", _VALID_ANTHROPIC_KEY)
+    _clear_app_creds(monkeypatch)
+    monkeypatch.setenv("GITHUB_APP_PRIVATE_KEY_B64", "not valid base64 %%%")
+    with pytest.raises(webhook.StartupCredentialError) as excinfo:
+        webhook._validate_credential_shapes()
+    assert "GITHUB_APP_PRIVATE_KEY_B64" in str(excinfo.value)
+
+
+def test_startup_rejects_unparseable_b64_pem(
+    monkeypatch: pytest.MonkeyPatch,
+) -> None:
+    """Valid base64 that decodes to UTF-8 text which is NOT a parseable PEM
+    must be rejected — the F1 substring check is gone from the B64 branch too."""
+    monkeypatch.setenv("ANTHROPIC_API_KEY", _VALID_ANTHROPIC_KEY)
+    _clear_app_creds(monkeypatch)
+    payload = b"this is valid utf-8 text but is definitely not a PEM key"
+    monkeypatch.setenv(
+        "GITHUB_APP_PRIVATE_KEY_B64", base64.b64encode(payload).decode()
+    )
+    with pytest.raises(webhook.StartupCredentialError) as excinfo:
+        webhook._validate_credential_shapes()
+    assert "GITHUB_APP_PRIVATE_KEY_B64" in str(excinfo.value)
+
+
+def test_junk_pem_that_matches_substring_is_rejected(
+    monkeypatch: pytest.MonkeyPatch,
+) -> None:
+    """The exact junk PEM from the adversarial review — a well-formed header
+    and footer wrapped around 'GARBAGE'. It satisfies the old
+    `"PRIVATE KEY" in raw_key` substring check (so v1 ACCEPTED it) but is not
+    a parseable private key. This test is the proof F1 is actually closed."""
+    monkeypatch.setenv("ANTHROPIC_API_KEY", _VALID_ANTHROPIC_KEY)
+    _clear_app_creds(monkeypatch)
+    junk_pem = "-----BEGIN PRIVATE KEY-----\nGARBAGE\n-----END PRIVATE KEY-----"
+    assert "PRIVATE KEY" in junk_pem  # confirms it would pass the v1 substring gate
+    monkeypatch.setenv("GITHUB_APP_PRIVATE_KEY", junk_pem)
+    with pytest.raises(webhook.StartupCredentialError):
+        webhook._validate_credential_shapes()
```

---

## 3. F1 exploit repro — boot now correctly refuses

Run against the **current (v2)** code:

```
F1 junk PEM contains 'PRIVATE KEY' (would pass v1 substring gate): True
F1 RESULT (v2): boot REFUSED -> GITHUB_APP_PRIVATE_KEY is set but is not a valid PEM private key
```

Proof it is a genuine regression test — the **same** new tests run against the
reconstructed **v1** module:

```
FAILED tests/test_webhook.py::test_startup_rejects_bad_raw_private_key - Failed: DID NOT RAISE StartupCredentialError
FAILED tests/test_webhook.py::test_junk_pem_that_matches_substring_is_rejected - Failed: DID NOT RAISE StartupCredentialError
2 failed, 3 passed, 35 deselected
```

So the exact junk PEM `-----BEGIN PRIVATE KEY-----\nGARBAGE\n-----END PRIVATE KEY-----`
was **ACCEPTED by v1** and is **REFUSED by v2**. That is the F1 fix, demonstrated.

**Honest note on the other two new tests:** `test_startup_rejects_invalid_b64_private_key`
and `test_startup_rejects_unparseable_b64_pem` **pass on both v1 and v2** — v1's
`validate=True` + substring path happened to already reject those particular
inputs. They are still worth keeping: they lock in the new decode path and its
clear messaging. The two tests above are the ones that strictly prove F1.

---

## 4. F2 decode-divergence — guard now matches the consumer

Scenario: a **line-wrapped** base64 copy of a real PEM (common when a secret UI
inserts 64-col newlines). Run against current (v2) code:

```
F2 line-wrapped base64 contains newlines: True
F2 v1 decode(validate=True): RAISES Error -> v1 would FALSELY reject this key
F2 consumer decode base64.b64decode(...).decode('utf-8') round-trips to the real PEM: True
F2 RESULT (v2 guard): ACCEPTED  <-- matches consumer (correct)
```

v1 would have failed the boot on a key the consumer can use perfectly well; v2's
decode is byte-for-byte the consumer's, so guard and consumer now agree.

---

## 5. Test output — exact numbers

All runs on CPython 3.10.12 (Linux sandbox), `addopts` cleared to bypass the
coverage-gate/`-m 'not integration'` defaults, cryptography 50.0.0.

### Webhook module
- **Baseline (v1):** `36 passed`
- **After v2:** `40 passed` — **+4**, reconciles (36 + 4 new). ✅

```
tests/test_webhook.py ... 40 passed, 1 warning in 1.50s
```
(The 4 additions: test_startup_rejects_bad_raw_private_key,
test_startup_rejects_invalid_b64_private_key, test_startup_rejects_unparseable_b64_pem,
test_junk_pem_that_matches_substring_is_rejected.)

### Full suite
- **Baseline (v1):** `557 passed, 8 failed, 11 skipped`
- **After v2:** `561 passed, 8 failed, 11 skipped` — **+4 passed**, same 8 failures. ✅

The delta is exactly +4 in both the module and the suite, so it reconciles.

**About the absolute base (557 vs your "~567"):** the 8 failures are **pre-existing
and environmental**, not caused by this patch — they fail identically on the v1
baseline:
```
tests/test_docker_sandbox.py (6 tests)   -> need a Docker daemon (unavailable in sandbox)
tests/test_fix_gen.py::test_fix_gen_scope_containment_subprocess_shell_true
tests/test_golden_dataset.py::test_verifier_end_to_end_failed_out_of_bounds
```
On your Windows gate (Docker present) these should pass, which is consistent with
your ~567 baseline; there `567 + 4 = 571` is expected. I did **not** explain the
mismatch away — I ran the same failing tests against v1 and got the same 8
failures, confirming they predate and are independent of this change.

---

## 6. Verification steps performed
1. Reproduced the v1 baseline (36 / 557) before editing.
2. Wrote fixes for F1–F4; re-ran webhook module → 40 passed.
3. Re-ran full suite → 561 passed, same 8 pre-existing failures.
4. Reconstructed the v1 module and ran the new tests against it — confirmed the
   two F1 tests FAIL on v1 and PASS on v2 (regression proof, §3).
5. Demonstrated the F1 junk-PEM refusal and the F2 line-wrapped-base64 agreement
   with the consumer against live v2 code (§3, §4).
6. Confirmed the guard's B64 decode is line-for-line the consumer's
   (github_app_auth.py:50–52): `.strip()` → `base64.b64decode(...)` (default
   validate) → `.decode("utf-8")`.

---

## 7. Staging / commit confirmation
Nothing was staged, committed, or pushed. `git diff --cached --stat` is empty:

```
[empty staged tree]
```

Working tree still shows only unstaged modifications (as expected for an in-place
amendment):
```
 M src/patchward/webhook.py
 M tests/test_webhook.py
```
Staging/committing remains yours to do (H20).

---

## 8. Things I could NOT verify / open gaps (not omitted)
1. **The gate interpreter itself never ran the suite.** Tests ran on Linux
   CPython 3.10.12, not the Windows 3.14.4 gate (§0). Version pin confirmed only
   via `pyvenv.cfg`. Please re-run on the gate to make the numbers gate-official.
2. **cryptography version differs** (test env 50.0.0 vs gate 48.0.0). Same major
   PEM/base64 behavior, but not byte-identical libraries.
3. **8 full-suite failures could not be exercised** in the sandbox (no Docker,
   subprocess/network constraints). I verified they are pre-existing (fail on v1
   too) but I did not see them pass; that requires the gate environment.
4. **Full-suite absolute baseline (557) is lower than your ~567** purely due to
   items 1–3; only the +4 delta is what this change is responsible for.
