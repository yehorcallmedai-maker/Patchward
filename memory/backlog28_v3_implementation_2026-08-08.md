# BACKLOG 28 — Startup Credential Guard, v3 implementation

**Date:** 2026-08-08
**Round:** v3 (third amendment — v1, then v2 for F1–F5, now v3 for F-A/F-B/F-C)
**Scope:** Amend the existing guard in place. v1 + v2 + v3 are all applied,
uncommitted, in the working tree.
**Findings addressed:** F-A (RSA-specificity), F-B (consumer precedence mirror),
F-C (missing discriminating B64 junk-PEM test) from the second independent
adversarial pass.

---

## ⚠️ Gate-interpreter caveat — READ FIRST (unverified on the gate)

The brief's gate interpreter is `D:\Dev\Projects\Patchward\.venv\Scripts\python.exe`
(Windows CPython **3.14.4**). This session's execution sandbox is **Linux**, and
that `.venv` is a Windows build — it cannot be executed here (`Exec format error`).
`uv` could not download a matching standalone 3.14/3.12 build for Linux (the
GitHub release host is not reachable from the sandbox).

**What I actually ran the suite on:** a Linux **CPython 3.10.12** environment with
the project's runtime + dev dependencies installed from PyPI (`cryptography 48.0.0`,
`fastapi`, `pyjwt[crypto]`, `httpx`, `pytest`, `pytest-cov`, `pytest-asyncio`),
with `PYTHONPATH=src`.

The guard logic under test is version-independent (env reads, `base64`,
`load_pem_private_key`, `isinstance(..., rsa.RSAPrivateKey)`), so the pass/fail
outcomes below are expected to be identical on 3.14.4. **However, the exact numbers
have NOT been confirmed on the 3.14.4 gate.** Yehor should re-run both gate commands
on Windows to seal this:

```
& "D:\Dev\Projects\Patchward\.venv\Scripts\python.exe" -m pytest tests\test_webhook.py -v
& "D:\Dev\Projects\Patchward\.venv\Scripts\python.exe" -m pytest -q
```

---

## Summary of changes (this round only)

Two files changed, both already dirty from v1/v2 (no new files created):

| File | Change |
|------|--------|
| `src/patchward/webhook.py` | Import `rsa`; restructure `_validate_credential_shapes` private-key validation to (a) mirror the consumer's RAW-first precedence, and (b) enforce `rsa.RSAPrivateKey` in both branches |
| `tests/test_webhook.py` | +3 regression tests (F-A, F-B, F-C) plus an EC-key PEM helper |

Consumer precedence was **verified by reading the source**, not assumed —
`github_app_auth.py::_load_private_key` (lines 47–52):

```python
raw = os.environ.get("GITHUB_APP_PRIVATE_KEY", "").strip()
if raw:
    return raw                                    # RAW wins outright
encoded = os.environ.get("GITHUB_APP_PRIVATE_KEY_B64", "").strip()
if encoded:
    return base64.b64decode(encoded).decode("utf-8")   # B64 only if RAW absent
raise GitHubAppAuthError(...)                     # both absent
```

The guard now validates exactly the variable the consumer would use, in the same
order. The "both absent" branch is left unchanged (existing policy).

---

## Full diff — this round's changes only (v2 → v3)

### `src/patchward/webhook.py`

Import (line 44):

```diff
--- a/src/patchward/webhook.py
+++ b/src/patchward/webhook.py
@@ -43,6 +43,7 @@
 from cryptography.hazmat.backends import default_backend
+from cryptography.hazmat.primitives.asymmetric import rsa
 from cryptography.hazmat.primitives.serialization import load_pem_private_key
```

Validation body:

```diff
--- a/src/patchward/webhook.py
+++ b/src/patchward/webhook.py
@@ -127,13 +127,22 @@
         # NOT usable as a GitHub App ID. Require ASCII decimal digits only.
         errors.append("GITHUB_APP_ID is set but is not a numeric App ID")
 
+    # F-B (BACKLOG 28 v3): mirror the consumer's ACTUAL precedence
+    # (github_app_auth.py:_load_private_key, lines 47-52): RAW is read
+    # first and, when present, returned outright — B64 is NEVER consulted.
+    # Only when RAW is absent does the consumer fall back to B64. The prior
+    # (v2) guard validated BOTH variables independently, so a valid RAW key
+    # paired with a stale/garbage B64 value produced a spurious B64 error and
+    # a false boot failure over a value that would never be read. Validate
+    # exactly the variable the consumer would use, in the same order.
+    raw_key = os.environ.get("GITHUB_APP_PRIVATE_KEY", "").strip()
     b64_key = os.environ.get("GITHUB_APP_PRIVATE_KEY_B64", "").strip()
-    if b64_key:
+    if raw_key:
         # F1 (BACKLOG 28 v2): actually attempt to parse the PEM. The prior
         # `"PRIVATE KEY" in raw_key` substring check accepted a valid-looking
         # header wrapped around a garbage body (the adversarial junk-PEM repro).
         try:
-            load_pem_private_key(
+            key = load_pem_private_key(
                 raw_key.encode("utf-8"),
                 password=None,
                 backend=default_backend(),
@@ -142,9 +151,17 @@
             errors.append(
                 "GITHUB_APP_PRIVATE_KEY is set but is not a valid PEM private key"
             )
-
-    raw_key = os.environ.get("GITHUB_APP_PRIVATE_KEY", "").strip()
-    if raw_key:
+        else:
+            # F-A (BACKLOG 28 v3): parseability is not enough. GitHub Apps
+            # sign with RS256, which REQUIRES an RSA key; a well-formed EC or
+            # Ed25519 key parses cleanly but cannot sign a valid App JWT, so
+            # the boot must reject it here rather than fail at first use.
+            if not isinstance(key, rsa.RSAPrivateKey):
+                errors.append(
+                    "GITHUB_APP_PRIVATE_KEY(_B64) is set but is not an RSA private "
+                    "key (GitHub Apps require RSA for RS256 signing)"
+                )
+    elif b64_key:
         # F2 (BACKLOG 28 v2): mirror the real consumer's decode EXACTLY
         # (github_app_auth.py:50-52) — same .strip(), same base64.b64decode()
         # with the default validate flag (validate=False), same .decode("utf-8"),
@@ -162,7 +179,7 @@
             # F1 (BACKLOG 28 v2): actually parse the PEM instead of a substring
             # check, so a well-formed header wrapped around garbage is rejected.
             try:
-                load_pem_private_key(
+                key = load_pem_private_key(
                     decoded_pem.encode("utf-8"),
                     password=None,
                     backend=default_backend(),
@@ -172,6 +189,14 @@
                     "GITHUB_APP_PRIVATE_KEY_B64 is set but is not a valid PEM "
                     "private key"
                 )
+            else:
+                # F-A (BACKLOG 28 v3): enforce RSA specifically, consistently
+                # with the raw branch — a parseable non-RSA key cannot sign RS256.
+                if not isinstance(key, rsa.RSAPrivateKey):
+                    errors.append(
+                        "GITHUB_APP_PRIVATE_KEY(_B64) is set but is not an RSA "
+                        "private key (GitHub Apps require RSA for RS256 signing)"
+                    )
 
     if not os.environ.get("GITHUB_WEBHOOK_SECRET", "").strip():
         logger.warning("[webhook] GITHUB_WEBHOOK_SECRET is not set at startup")
```

### `tests/test_webhook.py`

```diff
--- a/tests/test_webhook.py
+++ b/tests/test_webhook.py
@@ -792,3 +792,95 @@
     monkeypatch.setenv("GITHUB_APP_PRIVATE_KEY", junk_pem)
     with pytest.raises(webhook.StartupCredentialError):
         webhook._validate_credential_shapes()
+
+
+# ---------------------------------------------------------------------------
+# BACKLOG 28 v3 — regression tests for the second adversarial-review findings.
+# F-A: the guard accepted ANY parseable private key, not RSA specifically;
+#      an EC/Ed25519 key parses but cannot sign the RS256 App JWT.
+# F-B: the guard validated BOTH raw and B64 independently, so a valid raw
+#      key + stale/garbage B64 caused a false boot failure — the consumer
+#      reads raw first and never looks at B64.
+# F-C: a discriminating B64-branch junk-PEM test (payload that would have
+#      passed the v1 substring check) was missing.
+# These would have FAILED against v2 and must PASS against v3.
+# ---------------------------------------------------------------------------
+
+
+def _real_ec_private_key_pem() -> bytes:
+    """A genuine, parseable EC (non-RSA) private key PEM (generated fresh —
+    never a real secret). It loads cleanly via load_pem_private_key() but is
+    NOT an rsa.RSAPrivateKey, so the v3 guard must reject it (F-A)."""
+    from cryptography.hazmat.primitives.asymmetric import ec
+
+    key = ec.generate_private_key(ec.SECP256R1())
+    return key.private_bytes(
+        encoding=serialization.Encoding.PEM,
+        format=serialization.PrivateFormat.PKCS8,
+        encryption_algorithm=serialization.NoEncryption(),
+    )
+
+
+def test_startup_rejects_valid_but_non_rsa_private_key(
+    monkeypatch: pytest.MonkeyPatch,
+) -> None:
+    """F-A: a real EC private key parses cleanly but cannot sign RS256, so the
+    guard must REJECT it. v2 (isinstance check absent) ACCEPTED it — this is the
+    regression proof. Asserted for BOTH the raw and the B64 branch."""
+    ec_pem = _real_ec_private_key_pem()
+
+    # Raw branch.
+    monkeypatch.setenv("ANTHROPIC_API_KEY", _VALID_ANTHROPIC_KEY)
+    _clear_app_creds(monkeypatch)
+    monkeypatch.setenv("GITHUB_APP_PRIVATE_KEY", ec_pem.decode("utf-8"))
+    with pytest.raises(webhook.StartupCredentialError) as excinfo_raw:
+        webhook._validate_credential_shapes()
+    assert "RSA" in str(excinfo_raw.value)
+
+    # B64 branch (raw cleared so the consumer — and the guard — fall back to it).
+    _clear_app_creds(monkeypatch)
+    monkeypatch.setenv(
+        "GITHUB_APP_PRIVATE_KEY_B64", base64.b64encode(ec_pem).decode()
+    )
+    with pytest.raises(webhook.StartupCredentialError) as excinfo_b64:
+        webhook._validate_credential_shapes()
+    assert "RSA" in str(excinfo_b64.value)
+
+
+def test_startup_ignores_stale_b64_when_raw_key_valid(
+    monkeypatch: pytest.MonkeyPatch,
+) -> None:
+    """F-B: the consumer (github_app_auth._load_private_key) reads RAW first and
+    returns it outright — B64 is never consulted when RAW is present. So a valid
+    RAW key paired with a deliberately garbage B64 value must still BOOT (guard
+    ACCEPTS). v2 validated B64 independently and raised a spurious error here —
+    a false boot failure. This is the regression proof for F-B."""
+    monkeypatch.setenv("ANTHROPIC_API_KEY", _VALID_ANTHROPIC_KEY)
+    _clear_app_creds(monkeypatch)
+    monkeypatch.setenv("GITHUB_APP_ID", "123456")
+    monkeypatch.setenv(
+        "GITHUB_APP_PRIVATE_KEY", _VALID_PRIVATE_KEY_PEM.decode("utf-8")
+    )
+    # Stale/garbage B64 the consumer will never read.
+    monkeypatch.setenv("GITHUB_APP_PRIVATE_KEY_B64", "not valid base64 %%%")
+    webhook._validate_credential_shapes()  # must not raise
+
+
+def test_junk_pem_with_substring_via_b64_is_rejected(
+    monkeypatch: pytest.MonkeyPatch,
+) -> None:
+    """F-C: the exact junk PEM ('-----BEGIN PRIVATE KEY-----\\nGARBAGE\\n-----END
+    PRIVATE KEY-----') base64-encoded into the B64 variable. Its decoded form
+    satisfies the old v1 `"PRIVATE KEY" in ...` substring check (v1 ACCEPTED it)
+    but is not a parseable private key, so v3 must REJECT it. This is the
+    discriminating B64-branch test that was missing."""
+    monkeypatch.setenv("ANTHROPIC_API_KEY", _VALID_ANTHROPIC_KEY)
+    _clear_app_creds(monkeypatch)
+    junk_pem = "-----BEGIN PRIVATE KEY-----\nGARBAGE\n-----END PRIVATE KEY-----"
+    assert "PRIVATE KEY" in junk_pem  # confirms it would pass the v1 substring gate
+    monkeypatch.setenv(
+        "GITHUB_APP_PRIVATE_KEY_B64", base64.b64encode(junk_pem.encode()).decode()
+    )
+    with pytest.raises(webhook.StartupCredentialError) as excinfo:
+        webhook._validate_credential_shapes()
+    assert "GITHUB_APP_PRIVATE_KEY_B64" in str(excinfo.value)
```

---

## Regression proofs (fail-against-old, pass-against-new)

To prove each new test actually discriminates, I reconstructed scratch copies of
the guard and ran the new tests against them.

### F-A — EC key: **fails against v2, passes against v3** ✅

Reconstructed v2 (no `isinstance(..., rsa.RSAPrivateKey)` check) in `/tmp/v2src`
and ran `test_startup_rejects_valid_but_non_rsa_private_key`:

- **Against v2 → FAILED** (as required). v2 accepts the EC key — `_validate_credential_shapes()`
  does not raise — so the test's `pytest.raises(...)` fails. This is the regression
  proof: v3 rejects a key v2 accepted.
- **Against v3 → PASSED.** Both raw and B64 branches raise with `"RSA"` in the message.

### F-B — stale B64: **fails (false boot) against v2, passes against v3** ✅

Same v2 scratch (validates RAW and B64 independently). Ran
`test_startup_ignores_stale_b64_when_raw_key_valid`:

- **Against v2 → FAILED** (as required). v2 raised
  `StartupCredentialError: GITHUB_APP_PRIVATE_KEY_B64 is set but could not be
  base64-decoded ...` — i.e. the **false boot failure** over a value the consumer
  would never read. The test expects no raise, so it fails.
- **Against v3 → PASSED.** With RAW valid, the guard never inspects the garbage
  B64, so boot succeeds.

### F-C — B64 junk PEM: **discriminates** ✅

Built a scratch copy whose B64 branch reverts to the v1 substring check
(`if "PRIVATE KEY" not in decoded_pem`) in `/tmp/substrsrc`, ran
`test_junk_pem_with_substring_via_b64_is_rejected`:

- **Against the substring-reverted scratch → FAILED** (as required). The decoded
  junk PEM contains `"PRIVATE KEY"`, so the substring check accepts it, no raise,
  test fails — proving the test genuinely discriminates parse-vs-substring.
- **Against v3 → PASSED.** v3 actually parses; the junk PEM fails to parse and is
  rejected.

---

## Exact test numbers (Linux CPython 3.10.12 — see gate caveat)

**Webhook module** — `pytest tests/test_webhook.py -v`:

```
43 passed, 1 warning
```

40 → **43** (+3 new tests), matching the brief's expectation.
The three additions: `test_startup_rejects_valid_but_non_rsa_private_key`,
`test_startup_ignores_stale_b64_when_raw_key_valid`,
`test_junk_pem_with_substring_via_b64_is_rejected`.

**Full suite** — `pytest -q` (project config: `-m 'not integration'`, `--cov-fail-under=80`):

```
566 passed, 2 skipped, 15 deselected, 1 warning in 19.45s
```

**Coverage floor:** `Required test coverage of 80% reached. Total coverage: 91.33%` — **PASSES.**

Note on the "562 → ~565" estimate: the observed full-suite passing count is **566**.
The delta attributable to this round is exactly **+3**, and those three are the only
tests added — all in the webhook module (40 → 43). The full-suite baseline the estimate
was drawn from differs by 1 from what I observed here; since I could not run the exact
gate interpreter I cannot reconcile that ±1 against the v2 gate run, but the +3 delta
is fully and solely accounted for.

---

## Git / staging state

- **Nothing staged, nothing committed.** `git diff --cached` is empty. No `git add`,
  `git commit`, `git push`, or PR was performed (H20 — staging is Yehor's action only).
- Working-tree modifications (all uncommitted, cumulative v1+v2+v3):
  - `src/patchward/webhook.py`
  - `tests/test_webhook.py`

---

## Anything unverified / caveats (not omitted)

1. **Gate interpreter not used.** All numbers above are from Linux CPython **3.10.12**,
   not the Windows **3.14.4** gate `.venv` (which cannot execute in this sandbox, and a
   matching Linux Python build could not be downloaded). Logic is version-independent, but
   **Yehor must re-run both gate commands on Windows to seal the exact numbers.**
2. **Full-suite count ±1 vs the brief estimate** (566 observed vs ~565 estimated). The +3
   delta from this round is exact; the baseline discrepancy is unverified because I could
   not run the v2 gate. Re-running the gate resolves this.
3. **`tests/fixture_repo` shows as modified** in `git status` (`M tests/fixture_repo`). This
   is a **submodule/gitlink** (mode 160000) and was already dirty before this round — I did
   **not** touch it. Flagging it only so it isn't mistaken for a v3 change; it is out of scope.
4. **Deprecation warning** from the test run: `StarletteDeprecationWarning: Using httpx with
   starlette.testclient is deprecated`. Pre-existing, unrelated to this round; 1 warning, no
   failures.
5. The three regression proofs used **reconstructed** v2 / substring scratch copies (faithful
   reversions of the exact v3 blocks), not a git checkout of the historical v2 — because v1/v2/v3
   are all uncommitted in one working tree, there is no committed v2 to check out. The
   reconstructions were syntax-validated and exercised the intended code paths.
