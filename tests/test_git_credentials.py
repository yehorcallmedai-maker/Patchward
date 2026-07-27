# KS-TRACE: BACKLOG 19, C-P5-03 | ephemeral git credential passing + redaction
"""
Tests for BACKLOG 19: the token must never reach .git/config, argv, or
any log/exception text.

Covers:
  - git_credentials.py: tokenless URL, helper args, env construction
  - the empirical persistence property itself: a real local `git clone`
    invoked with the new command shape leaves no token in .git/config
    (the OLD url-embedded form is also demonstrated to persist, so this
    test would catch a regression back to it)
  - credential_proxy.scrub_text(): pattern + register-at-mint layers
  - worktree_common.git_push_branch(): token via helper (argv-free),
    TimeoutExpired never embeds argv, failure text scrubbed
"""
from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from patchward import credential_proxy
from patchward.credential_proxy import register_runtime_credential, scrub_text
from patchward.git_credentials import (
    GIT_TOKEN_ENV,
    credential_env,
    credential_helper_args,
    tokenless_clone_url,
)
from patchward.worktree_common import git_push_branch

# Token-shaped but fake — matches the ghs_ pattern (36-char base62 tail).
FAKE_TOKEN = "ghs_" + "A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8"


@pytest.fixture(autouse=True)
def _isolate_runtime_credentials():
    """Give each scrub unit test a CLEAN module-global registry, then
    restore whatever was there.

    _RUNTIME_CREDENTIALS is process-global and append-only by design
    (correct product behavior — the webhook accumulates minted tokens,
    the CLI registers its GITHUB_TOKEN). That means earlier tests which
    drive the webhook/CLI paths (e.g. test_async_pipeline's CLI-batch
    tests) leave real fixture token values in it. These scrub unit tests
    assert exact input/output equality, so they must start from empty —
    snapshot-and-restore would inherit that pollution. Clear on entry,
    restore the pre-existing set on exit so we don't perturb other files."""
    saved = set(credential_proxy._RUNTIME_CREDENTIALS)  # noqa: SLF001
    credential_proxy._RUNTIME_CREDENTIALS.clear()  # noqa: SLF001
    yield
    credential_proxy._RUNTIME_CREDENTIALS.clear()  # noqa: SLF001
    credential_proxy._RUNTIME_CREDENTIALS.update(saved)  # noqa: SLF001


# ---------------------------------------------------------------------------
# git_credentials primitives
# ---------------------------------------------------------------------------

class TestGitCredentialPrimitives:
    def test_tokenless_clone_url_has_no_userinfo(self) -> None:
        url = tokenless_clone_url("acme", "backend")
        assert url == "https://github.com/acme/backend.git"
        assert "@" not in url

    def test_helper_args_contain_no_token_material(self) -> None:
        """The helper fragment reads an env var — the args themselves are
        constant and secret-free, safe to appear in argv/ps output."""
        args = credential_helper_args()
        joined = " ".join(args)
        assert GIT_TOKEN_ENV in joined  # helper references the env var...
        assert FAKE_TOKEN not in joined  # ...but never a value

    def test_helper_args_reset_configured_helpers_first(self) -> None:
        """First -c must blank the helper list so no system/global helper
        (e.g. an OS credential store) is consulted or fed the token."""
        args = credential_helper_args()
        assert args[0] == "-c"
        assert args[1] == "credential.helper="
        assert args[2] == "-c"
        assert args[3].startswith("credential.helper=!")

    def test_credential_env_sets_token_without_mutating_environ(self) -> None:
        import os
        assert GIT_TOKEN_ENV not in os.environ
        env = credential_env(FAKE_TOKEN)
        assert env[GIT_TOKEN_ENV] == FAKE_TOKEN
        assert GIT_TOKEN_ENV not in os.environ  # copy, not mutation


# ---------------------------------------------------------------------------
# The persistence property itself — real local git, no network.
# ---------------------------------------------------------------------------

class TestClonePersistence:
    @pytest.fixture()
    def local_origin(self, tmp_path: Path) -> Path:
        """A local git repo with one commit, cloneable via file path."""
        origin = tmp_path / "origin"
        origin.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=origin, check=True)
        (origin / "README.md").write_text("fixture\n")
        subprocess.run(["git", "add", "-A"], cwd=origin, check=True)
        subprocess.run(
            ["git", "-c", "user.email=t@t", "-c", "user.name=t",
             "commit", "-q", "-m", "init"],
            cwd=origin, check=True,
        )
        return origin

    def test_new_command_shape_persists_no_token(
        self, tmp_path: Path, local_origin: Path
    ) -> None:
        """A real clone with the BACKLOG 19 command shape (helper args +
        env-carried token) leaves no token anywhere in .git/config."""
        dest = tmp_path / "clone-new"
        proc = subprocess.run(
            ["git", *credential_helper_args(),
             "clone", "-q", str(local_origin), str(dest)],
            capture_output=True, text=True,
            env=credential_env(FAKE_TOKEN),
        )
        assert proc.returncode == 0, proc.stderr
        config_text = (dest / ".git" / "config").read_text()
        assert FAKE_TOKEN not in config_text
        assert "x-access-token" not in config_text
        assert GIT_TOKEN_ENV not in config_text  # -c is not persisted

    def test_old_url_embedded_shape_would_have_persisted(
        self, tmp_path: Path, local_origin: Path
    ) -> None:
        """Regression tripwire documenting WHY the URL-embedded form was
        removed: git persists a credential-bearing remote URL verbatim
        into .git/config (this is the empirical finding that falsified
        clone_url_with_token's old docstring). Uses a file:// origin so
        no network is involved; the userinfo is ignored for auth but
        still persisted, which is the point."""
        dest = tmp_path / "clone-old"
        url = f"file://x-access-token:{FAKE_TOKEN}@/{local_origin.as_posix().lstrip('/')}"
        proc = subprocess.run(
            ["git", "clone", "-q", url, str(dest)],
            capture_output=True, text=True,
        )
        if proc.returncode != 0:
            pytest.skip(
                "this git build rejects userinfo in file:// URLs — "
                "property already demonstrated for https in the "
                "BACKLOG 19 scoping pass"
            )
        config_text = (dest / ".git" / "config").read_text()
        assert FAKE_TOKEN in config_text  # the old form DOES persist


# ---------------------------------------------------------------------------
# scrub_text — pattern layer + register-at-mint layer
# ---------------------------------------------------------------------------

class TestScrubText:
    @pytest.mark.parametrize("prefix", ["ghp", "gho", "ghu", "ghs", "ghr"])
    def test_github_classic_prefixes_redacted(self, prefix: str) -> None:
        tok = prefix + "_" + "Z9y8X7w6V5u4T3s2R1q0P1o2N3m4L5k6"
        out = scrub_text(f"fatal: could not read from '{tok}' remote")
        assert tok not in out
        assert "[REDACTED-GITHUB-TOKEN]" in out

    def test_fine_grained_pat_redacted(self) -> None:
        tok = "github_pat_" + "11ABCDEFG0" * 6  # long base62/underscore tail
        out = scrub_text(f"error: {tok} rejected")
        assert tok not in out
        assert "[REDACTED-GITHUB-TOKEN]" in out

    def test_short_lookalikes_not_redacted(self) -> None:
        """Prose like 'ghs_abc' (below the length floor) must survive —
        false-positive control."""
        text = "the ghs_abc prefix and ghp_short are not real tokens"
        assert scrub_text(text) == text

    def test_plain_text_unchanged(self) -> None:
        text = "git push failed (exit 1)\nstderr: 'permission denied'"
        assert scrub_text(text) == text

    def test_registered_runtime_credential_redacted_by_value(self) -> None:
        """Register-at-mint layer: an arbitrary-shaped secret (no GitHub
        prefix — the pattern layer can NOT catch it) is redacted once
        registered."""
        secret = "not-github-shaped-secret-0123456789"
        assert scrub_text(secret) == secret  # pattern layer alone: miss
        register_runtime_credential(secret)
        out = scrub_text(f"boom: {secret} leaked")
        assert secret not in out
        assert "[REDACTED]" in out

    def test_register_ignores_empty_values(self) -> None:
        register_runtime_credential("")
        register_runtime_credential("   ")
        assert "" not in credential_proxy._RUNTIME_CREDENTIALS  # noqa: SLF001

    def test_empty_text_passthrough(self) -> None:
        assert scrub_text("") == ""

    def test_token_redacted_when_preceded_by_word_char(self) -> None:
        """BACKLOG 19 follow-up (finding #5): a leading \\b is defeated by
        a preceding word char, so a percent-encoded or run-on token
        escaped redaction. It must now be caught mid-'word'."""
        tok = "ghs_" + "Z9y8X7w6V5u4T3s2R1q0P1o2N3m4L5k6"
        for carrier in (
            f"https%3A%2F%2Fx-access-token%3A{tok}%40github.com",  # URL-encoded
            f"x-access-token:{tok}@github.com",                     # run-on colon
            f"prefixword{tok}",                                     # bare word char
        ):
            out = scrub_text(carrier)
            assert tok not in out, carrier
            assert "[REDACTED-GITHUB-TOKEN]" in out, carrier

    def test_scrub_text_concurrent_smoke(self) -> None:
        """BACKLOG 19 follow-up (finding #4), SMOKE test only — read the
        honest caveat before trusting it. The fix is `for val in
        tuple(_RUNTIME_CREDENTIALS)`: scrub_text iterates a SNAPSHOT so a
        concurrent register cannot raise 'Set changed size during
        iteration'. That guarantee is correct BY CONSTRUCTION (verifiable
        by reading credential_proxy.scrub_text), but it is NOT
        deterministically unit-testable: the race window is timing- and
        interpreter-dependent, and the re-attack confirmed this test stays
        green even against the UNFIXED source, so it is NOT discriminating.
        It is retained only as a low-value belt that would catch a gross
        regression (e.g. scrub_text starting to raise outright). The real
        assurance is the tuple() snapshot, reviewed line-by-line."""
        import threading

        errors: list[BaseException] = []

        def register_loop() -> None:
            # Bounded: enough churn to race the iterator, not so much it
            # starves the GIL or bloats the (fixture-restored) set.
            for i in range(2000):
                register_runtime_credential(f"secret-value-{i:06d}")

        def scrub_loop() -> None:
            try:
                for _ in range(2000):
                    scrub_text("some log line with git push failed exit 1")
            except BaseException as exc:  # noqa: BLE001
                errors.append(exc)

        threads = [threading.Thread(target=register_loop) for _ in range(2)]
        threads += [threading.Thread(target=scrub_loop) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert not errors, f"scrub_text raced: {errors!r}"


# ---------------------------------------------------------------------------
# git_push_branch — token via helper, argv-free; TimeoutExpired sealed
# ---------------------------------------------------------------------------

class TestGitPushBranchCredentialPath:
    def test_token_goes_to_env_and_helper_never_argv(self, tmp_path: Path) -> None:
        mock_ok = MagicMock()
        mock_ok.returncode = 0
        with patch(
            "patchward.worktree_common.subprocess.run", return_value=mock_ok
        ) as mock_run:
            git_push_branch(
                tmp_path, "https://github.com/acme/repo.git", "fix-b",
                token=FAKE_TOKEN,
            )
        argv = mock_run.call_args[0][0]
        assert FAKE_TOKEN not in " ".join(argv)  # never in argv
        assert "credential.helper=" in argv  # helper reset present
        assert argv[0] == "git" and "push" in argv
        env = mock_run.call_args.kwargs["env"]
        assert env[GIT_TOKEN_ENV] == FAKE_TOKEN  # carried by env only

    def test_no_token_still_resets_helpers_and_installs_none(
        self, tmp_path: Path
    ) -> None:
        """BACKLOG 19 follow-up (finding #3): the tokenless path (every
        hosted webhook push) must STILL clear all configured credential
        helpers — so git cannot consult or `erase` an ambient host
        credential store — but must NOT install our env-reading helper
        and must pass env=None. Previously the reset was skipped entirely
        when token was falsy, leaving the host's ambient config in play."""
        mock_ok = MagicMock()
        mock_ok.returncode = 0
        remote = "https://github.com/acme/repo.git"
        with patch(
            "patchward.worktree_common.subprocess.run", return_value=mock_ok
        ) as mock_run:
            git_push_branch(tmp_path, remote, "fix-b")
        argv = mock_run.call_args[0][0]
        assert argv == [
            "git", "-c", "credential.helper=",
            "push", "--force", remote, "fix-b:fix-b",
        ]
        # reset present exactly once; our inline helper NOT installed
        assert argv.count("credential.helper=") == 1
        assert not any(a.startswith("credential.helper=!") for a in argv)
        assert mock_run.call_args.kwargs["env"] is None

    def test_timeout_message_never_embeds_argv_or_token(self, tmp_path: Path) -> None:
        """str(TimeoutExpired) embeds the full argv — git_push_branch must
        catch it and raise a message with no argv and no token, even if a
        (hypothetical) token-bearing command were in flight."""
        poisoned_cmd = [
            "git", "push", "--force",
            f"https://x-access-token:{FAKE_TOKEN}@github.com/acme/repo.git",
            "fix-b:fix-b",
        ]
        with patch(
            "patchward.worktree_common.subprocess.run",
            side_effect=subprocess.TimeoutExpired(poisoned_cmd, 60),
        ):
            with pytest.raises(RuntimeError) as excinfo:
                git_push_branch(
                    tmp_path, "https://github.com/acme/repo.git", "fix-b",
                    token=FAKE_TOKEN,
                )
        msg = str(excinfo.value)
        assert "timed out" in msg
        assert FAKE_TOKEN not in msg
        assert "x-access-token" not in msg
        assert "--force" not in msg  # no argv fragments at all
        # and the chained-exception context must not resurrect the argv
        assert excinfo.value.__cause__ is None
        assert excinfo.value.__suppress_context__ is True

    def test_timeout_neutralizes_captured_streams_at_source(
        self, tmp_path: Path
    ) -> None:
        """BACKLOG 19 follow-up: even if a TimeoutExpired arrives carrying a
        token in its captured .stdout/.stderr, the handler must neutralize
        those stream ATTRIBUTES on the object before re-raising — not merely
        sever the cause chain. Asserts against the stream attributes on the
        surviving __context__, not just str(exception)."""
        te = subprocess.TimeoutExpired(
            cmd=["git", "push", "--force",
                 f"https://x-access-token:{FAKE_TOKEN}@github.com/a/r.git", "b:b"],
            timeout=60,
            output=f"pushing... {FAKE_TOKEN} leaked to stdout",
            stderr=f"fatal: unable to access '{FAKE_TOKEN}'",
        )
        with patch(
            "patchward.worktree_common.subprocess.run", side_effect=te
        ):
            with pytest.raises(RuntimeError) as excinfo:
                git_push_branch(
                    tmp_path, "https://github.com/acme/repo.git", "fix-b",
                    token=FAKE_TOKEN,
                )
        ctx = excinfo.value.__context__
        assert isinstance(ctx, subprocess.TimeoutExpired)
        # the captured streams on the original exception are neutralized
        assert FAKE_TOKEN not in (ctx.stdout or "")
        assert FAKE_TOKEN not in (ctx.stderr or "")
        assert "[REDACTED-GITHUB-TOKEN]" in (ctx.stdout or "")
        # and exc.cmd (argv) is scrubbed too — so a REGRESSION that put a
        # token-bearing URL back in argv cannot survive on __context__.cmd
        # (re-attack finding F1). Assert against the reconstructed argv:
        assert FAKE_TOKEN not in " ".join(str(a) for a in ctx.cmd)
        # and nothing token-shaped survives on the re-raised exception str
        assert FAKE_TOKEN not in str(excinfo.value)

    def test_failure_stderr_is_scrubbed(self, tmp_path: Path) -> None:
        """If git stderr ever carries a token (older git, verbose modes),
        the RuntimeError text must have it redacted."""
        mock_proc = MagicMock()
        mock_proc.returncode = 1
        mock_proc.stdout = ""
        mock_proc.stderr = f"fatal: unable to access '{FAKE_TOKEN}'"
        with patch(
            "patchward.worktree_common.subprocess.run", return_value=mock_proc
        ):
            with pytest.raises(RuntimeError, match="git push failed") as excinfo:
                git_push_branch(
                    tmp_path, "https://github.com/acme/repo.git", "fix-b",
                    token=FAKE_TOKEN,
                )
        msg = str(excinfo.value)
        assert FAKE_TOKEN not in msg
        assert "[REDACTED-GITHUB-TOKEN]" in msg
