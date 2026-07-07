# KS-TRACE: AC-05, AC-06, AC-P1-10, AC-P3-10, AC-P6-05, AC-P6-06,
#           AC-P6-07 | test: config loader — valid, missing, malformed,
#           fix_gen, github, [[repos]] merge, batch, models
from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
import typer

from patchward.config import (
    load_config,
    RepomendConfig,
    FixGenConfig,
    RepoConfig,
    BatchConfig,
    ModelsConfig,
)


def test_load_valid_config(tmp_path: Path) -> None:
    repo = tmp_path / "myrepo"
    repo.mkdir()
    toml = tmp_path / "patchward.toml"
    toml.write_text(
        textwrap.dedent(f"""
        [patchward]
        repo_path = "{repo.as_posix()}"
        semgrep_rules = "p/python"
        db_path = "{(tmp_path / 'runs/state.db').as_posix()}"
        tracing_enabled = false
        """),
        encoding="utf-8",
    )
    cfg = load_config(toml)
    assert cfg.repo_path == repo
    assert cfg.semgrep_rules == "p/python"
    assert cfg.tracing_enabled is False


def test_missing_config_exits_1(tmp_path: Path) -> None:
    with pytest.raises(SystemExit) as exc_info:
        load_config(tmp_path / "nonexistent.toml")
    assert exc_info.value.code == 1


def test_malformed_toml_exits_1(tmp_path: Path) -> None:
    bad = tmp_path / "patchward.toml"
    bad.write_text("this is not valid toml }{", encoding="utf-8")
    with pytest.raises(SystemExit) as exc_info:
        load_config(bad)
    assert exc_info.value.code == 1


def test_invalid_repo_path_exits_1(tmp_path: Path) -> None:
    toml = tmp_path / "patchward.toml"
    toml.write_text(
        textwrap.dedent("""
        [patchward]
        repo_path = "/does/not/exist/anywhere"
        """),
        encoding="utf-8",
    )
    with pytest.raises(SystemExit) as exc_info:
        load_config(toml)
    assert exc_info.value.code == 1


# KS-TRACE: AC-P1-10 | assumption: load_dotenv() runs before model init | test: test_dotenv_loads_langfuse_key
def test_dotenv_loads_langfuse_key(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """AC-P1-10: LANGFUSE_PUBLIC_KEY is readable from config object when .env is present."""
    # Ensure env var is clean before test
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)

    repo = tmp_path / "repo"
    repo.mkdir()

    dotenv_file = tmp_path / ".env"
    dotenv_file.write_text(
        "LANGFUSE_PUBLIC_KEY=pk-test-abc123\nLANGFUSE_SECRET_KEY=sk-test-xyz789\n",
        encoding="utf-8",
    )

    toml = tmp_path / "patchward.toml"
    toml.write_text(
        f'[patchward]\nrepo_path = "{repo.as_posix()}"\ntracing_enabled = false\n',
        encoding="utf-8",
    )

    cfg = load_config(config_path=toml, dotenv_path=dotenv_file)

    assert cfg.langfuse_public_key == "pk-test-abc123"
    assert cfg.langfuse_secret_key == "sk-test-xyz789"


def test_dotenv_absent_leaves_keys_empty(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """load_config() with no .env and no env vars → keys default to empty string (no crash)."""
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)

    repo = tmp_path / "repo"
    repo.mkdir()
    toml = tmp_path / "patchward.toml"
    toml.write_text(
        f'[patchward]\nrepo_path = "{repo.as_posix()}"\ntracing_enabled = false\n',
        encoding="utf-8",
    )

    cfg = load_config(config_path=toml)

    assert cfg.langfuse_public_key == ""
    assert cfg.langfuse_secret_key == ""


def test_defaults_applied(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    toml = tmp_path / "patchward.toml"
    toml.write_text(
        f'[patchward]\nrepo_path = "{repo.as_posix()}"\n',
        encoding="utf-8",
    )
    cfg = load_config(toml)
    assert cfg.semgrep_rules == "p/python"
    assert cfg.tracing_enabled is True
    assert cfg.langfuse_host == "https://cloud.langfuse.com"


# KS-TRACE: AC-P3-10 | test: [fix_gen] toml section → FixGenConfig nested model
def test_fix_gen_max_turns_from_toml(tmp_path: Path) -> None:
    """
    [fix_gen] max_turns in toml overrides the default (10) — AC-P3-10.
    Non-default value must propagate from toml → RepomendConfig.fix_gen.max_turns.
    """
    repo = tmp_path / "repo"
    repo.mkdir()
    toml = tmp_path / "patchward.toml"
    toml.write_text(
        textwrap.dedent(f"""
        [patchward]
        repo_path = "{repo.as_posix()}"

        [fix_gen]
        max_turns = 5
        """),
        encoding="utf-8",
    )
    cfg = load_config(toml)
    assert cfg.fix_gen.max_turns == 5, (
        f"Expected fix_gen.max_turns=5 from toml [fix_gen] section, got {cfg.fix_gen.max_turns}"
    )


def test_fix_gen_max_turns_default_when_section_absent(tmp_path: Path) -> None:
    """
    When [fix_gen] section is absent, fix_gen.max_turns defaults to 10 — AC-P3-10.
    """
    repo = tmp_path / "repo"
    repo.mkdir()
    toml = tmp_path / "patchward.toml"
    toml.write_text(
        f'[patchward]\nrepo_path = "{repo.as_posix()}"\n',
        encoding="utf-8",
    )
    cfg = load_config(toml)
    assert cfg.fix_gen.max_turns == 10


def test_fix_gen_config_standalone_default() -> None:
    """FixGenConfig default: max_turns=10."""
    cfg = FixGenConfig()
    assert cfg.max_turns == 10


# ---------------------------------------------------------------------------
# KS-P5-02 STEP 1 — [github] section tests (C-P5-07, C-P5-10, AC-P5-13)
# ---------------------------------------------------------------------------
from patchward.config import GithubConfig, validate_github_config


def test_github_config_loaded_from_toml(tmp_path: Path) -> None:
    """[github] section is parsed into cfg.github (C-P5-07, C-P5-10)."""
    repo = tmp_path / "repo"
    repo.mkdir()
    toml = tmp_path / "patchward.toml"
    toml.write_text(
        f'[patchward]\nrepo_path = "{repo.as_posix()}"\n'
        '[github]\nowner = "acme"\nrepo = "my-app"\nbase_branch = "develop"\n',
        encoding="utf-8",
    )
    cfg = load_config(toml)
    assert cfg.github.owner == "acme"
    assert cfg.github.repo == "my-app"
    assert cfg.github.base_branch == "develop"


def test_github_config_defaults(tmp_path: Path) -> None:
    """No [github] section → defaults: owner='', repo='', base_branch='main'."""
    repo = tmp_path / "repo"
    repo.mkdir()
    toml = tmp_path / "patchward.toml"
    toml.write_text(
        f'[patchward]\nrepo_path = "{repo.as_posix()}"\n',
        encoding="utf-8",
    )
    cfg = load_config(toml)
    assert cfg.github.base_branch == "main"
    assert cfg.github.owner == ""
    assert cfg.github.repo == ""


def test_missing_github_owner_exits(tmp_path: Path) -> None:
    """validate_github_config() exits 1 with 'owner' in message when owner empty (AC-P5-13)."""
    repo = tmp_path / "repo"
    repo.mkdir()
    toml = tmp_path / "patchward.toml"
    toml.write_text(
        f'[patchward]\nrepo_path = "{repo.as_posix()}"\n'
        '[github]\nrepo = "my-app"\n',
        encoding="utf-8",
    )
    cfg = load_config(toml)
    with pytest.raises(SystemExit) as exc_info:
        validate_github_config(cfg)
    assert exc_info.value.code == 1


def test_missing_github_repo_exits(tmp_path: Path) -> None:
    """validate_github_config() exits 1 with 'repo' in message when
    repo empty (AC-P5-13)."""
    repo = tmp_path / "repo"
    repo.mkdir()
    toml = tmp_path / "patchward.toml"
    toml.write_text(
        f'[patchward]\nrepo_path = "{repo.as_posix()}"\n'
        '[github]\nowner = "acme"\n',
        encoding="utf-8",
    )
    cfg = load_config(toml)
    with pytest.raises(SystemExit) as exc_info:
        validate_github_config(cfg)
    assert exc_info.value.code == 1


# ---------------------------------------------------------------------------
# KS-P6-01 — [[repos]] array-of-tables, BatchConfig, ModelsConfig
# AC-P6-05, AC-P6-06, AC-P6-07, C-P6-05, C-P6-06, ADR-022
# Addendum A-01: field-merge critical case documented in intake_phase6.md
# ---------------------------------------------------------------------------


def _base_toml(repo_dir: Path) -> str:
    """Minimal [patchward] block referencing an existing directory."""
    return (
        f'[patchward]\nrepo_path = "{repo_dir.as_posix()}"\n'
    )


def test_repos_loaded_from_array_of_tables(tmp_path: Path) -> None:
    """[[repos]] with 2 full entries → cfg.repos has length 2 with
    correct field values. (AC-P6-06)"""
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    toml = tmp_path / "patchward.toml"
    toml.write_text(
        _base_toml(repo_dir)
        + '[github]\nowner = "default-owner"\nrepo = "default-repo"\n'
        + "[[repos]]\n"
        + f'path = "{repo_dir.as_posix()}"\n'
        + 'owner = "acme"\nrepo = "alpha"\nbase_branch = "main"\n'
        + "[[repos]]\n"
        + f'path = "{repo_dir.as_posix()}"\n'
        + 'owner = "acme"\nrepo = "beta"\nbase_branch = "develop"\n',
        encoding="utf-8",
    )
    cfg = load_config(toml)
    assert len(cfg.repos) == 2
    assert cfg.repos[0].owner == "acme"
    assert cfg.repos[0].repo == "alpha"
    assert cfg.repos[0].base_branch == "main"
    assert cfg.repos[1].repo == "beta"
    assert cfg.repos[1].base_branch == "develop"


def test_repos_field_merge_inherits_github_owner(
    tmp_path: Path,
) -> None:
    """Addendum A-01 (critical merge case):
    [[repos]] entry with only {path, repo} (no owner, no base_branch)
    inherits owner from [github].owner and base_branch defaults to
    'main'. No KeyError or ValidationError. (AC-P6-06, ADR-022)"""
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    toml = tmp_path / "patchward.toml"
    toml.write_text(
        _base_toml(repo_dir)
        + '[github]\nowner = "acme"\nrepo = "default-repo"\n'
        + "[[repos]]\n"
        + f'path = "{repo_dir.as_posix()}"\n'
        + 'repo = "my-service"\n',  # no owner, no base_branch
        encoding="utf-8",
    )
    cfg = load_config(toml)
    assert len(cfg.repos) == 1
    entry = cfg.repos[0]
    assert entry.owner == "acme"          # inherited from [github]
    assert entry.repo == "my-service"     # from [[repos]] entry
    assert entry.base_branch == "main"   # github default


def test_repos_fallback_to_github_singleton(tmp_path: Path) -> None:
    """No [[repos]] section → cfg.repos is a single-element list built
    from [github] fields. Backward-compatible. (AC-P6-07)"""
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    toml = tmp_path / "patchward.toml"
    toml.write_text(
        _base_toml(repo_dir)
        + '[github]\nowner = "acme"\nrepo = "legacy"\n'
        + 'base_branch = "main"\n',
        encoding="utf-8",
    )
    cfg = load_config(toml)
    assert len(cfg.repos) == 1
    entry = cfg.repos[0]
    assert entry.owner == "acme"
    assert entry.repo == "legacy"
    assert entry.base_branch == "main"
    assert entry.path == repo_dir


def test_repos_entry_missing_path_raises(tmp_path: Path) -> None:
    """[[repos]] entry with no 'path' field → SystemExit(1)."""
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    toml = tmp_path / "patchward.toml"
    toml.write_text(
        _base_toml(repo_dir)
        + '[github]\nowner = "acme"\nrepo = "x"\n'
        + "[[repos]]\n"
        + 'owner = "acme"\nrepo = "no-path"\n',
        encoding="utf-8",
    )
    with pytest.raises(SystemExit) as exc_info:
        load_config(toml)
    assert exc_info.value.code == 1


def test_repos_entry_missing_owner_after_merge_raises(
    tmp_path: Path,
) -> None:
    """[[repos]] entry with no owner AND [github] has no owner →
    SystemExit(1) with 'owner' in error message. (AC-P6-06)"""
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    toml = tmp_path / "patchward.toml"
    toml.write_text(
        _base_toml(repo_dir)
        # [github] deliberately has no owner
        + '[github]\nrepo = "x"\n'
        + "[[repos]]\n"
        + f'path = "{repo_dir.as_posix()}"\n'
        + 'repo = "my-service"\n',  # no owner here either
        encoding="utf-8",
    )
    with pytest.raises(SystemExit) as exc_info:
        load_config(toml)
    assert exc_info.value.code == 1


def test_batch_config_loaded(tmp_path: Path) -> None:
    """[batch] max_concurrent from toml overrides default. (C-P6-02)"""
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    toml = tmp_path / "patchward.toml"
    toml.write_text(
        _base_toml(repo_dir) + "[batch]\nmax_concurrent = 5\n",
        encoding="utf-8",
    )
    cfg = load_config(toml)
    assert cfg.batch.max_concurrent == 5


def test_batch_config_default(tmp_path: Path) -> None:
    """No [batch] section → max_concurrent defaults to 3. (C-P6-02)"""
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    toml = tmp_path / "patchward.toml"
    toml.write_text(_base_toml(repo_dir), encoding="utf-8")
    cfg = load_config(toml)
    assert cfg.batch.max_concurrent == 3


def test_models_config_loaded(tmp_path: Path) -> None:
    """[models] section fields load correctly into cfg.models.
    (AC-P6-05, C-P6-05)"""
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    toml = tmp_path / "patchward.toml"
    toml.write_text(
        _base_toml(repo_dir)
        + "[models]\n"
        + 'scanner_model = "claude-haiku-4-5-20251001"\n'
        + 'fix_model = "claude-sonnet-4-6"\n',
        encoding="utf-8",
    )
    cfg = load_config(toml)
    assert cfg.models.scanner_model == "claude-haiku-4-5-20251001"
    assert cfg.models.fix_model == "claude-sonnet-4-6"


def test_models_config_defaults(tmp_path: Path) -> None:
    """No [models] section → haiku and sonnet defaults. (AC-P6-05)"""
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    toml = tmp_path / "patchward.toml"
    toml.write_text(_base_toml(repo_dir), encoding="utf-8")
    cfg = load_config(toml)
    assert cfg.models.scanner_model == "claude-haiku-4-5-20251001"
    assert cfg.models.fix_model == "claude-sonnet-4-6"


# ---------------------------------------------------------------------------
# KS-P7-04 — max_findings_per_repo (C-P7-02, AC-P7-11, AD-P7-02)
# ---------------------------------------------------------------------------


def test_max_findings_per_repo_default(tmp_path: Path) -> None:
    """No [batch] section → max_findings_per_repo defaults to 5."""
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    toml = tmp_path / "patchward.toml"
    toml.write_text(_base_toml(repo_dir), encoding="utf-8")
    cfg = load_config(toml)
    assert cfg.batch.max_findings_per_repo == 5


def test_max_findings_per_repo_from_toml(tmp_path: Path) -> None:
    """[batch] max_findings_per_repo = 2 → cfg value 2. (AC-P7-11)"""
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    toml = tmp_path / "patchward.toml"
    extra = "[batch]\nmax_findings_per_repo = 2\n"
    toml.write_text(
        _base_toml(repo_dir) + extra, encoding="utf-8"
    )
    cfg = load_config(toml)
    assert cfg.batch.max_findings_per_repo == 2


def test_max_findings_per_repo_zero_raises(tmp_path: Path) -> None:
    """max_findings_per_repo = 0 → SystemExit. (AD-P7-02)"""
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    toml = tmp_path / "patchward.toml"
    extra = "[batch]\nmax_findings_per_repo = 0\n"
    toml.write_text(
        _base_toml(repo_dir) + extra, encoding="utf-8"
    )
    with pytest.raises(SystemExit):
        load_config(toml)


def test_max_findings_per_repo_negative_raises(
    tmp_path: Path,
) -> None:
    """max_findings_per_repo = -1 → SystemExit."""
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    toml = tmp_path / "patchward.toml"
    extra = "[batch]\nmax_findings_per_repo = -1\n"
    toml.write_text(
        _base_toml(repo_dir) + extra, encoding="utf-8"
    )
    with pytest.raises(SystemExit):
        load_config(toml)


def test_toml_example_parses_cleanly(tmp_path: Path) -> None:
    """
    patchward.toml.example loads without ValidationError or SystemExit
    when a valid repo_path is injected. (AC-P7-07)

    The example file has no [patchward] section (intentionally — users
    set repo_path via CLI flag or scan command).  We inject a minimal
    [patchward] block pointing at tmp_path so load_config() can
    validate repo_path existence without touching the rest of the
    example content.
    """
    example = (
        Path(__file__).parent.parent / "patchward.toml.example"
    )
    assert example.exists(), "patchward.toml.example not found"
    base = example.read_text(encoding="utf-8")
    injected = (
        f'[patchward]\nrepo_path = "{tmp_path.as_posix()}"\n'
        + base
    )
    toml = tmp_path / "patchward.toml"
    toml.write_text(injected, encoding="utf-8")
    cfg = load_config(toml)
    assert cfg.github.owner == "your-github-username"
    assert cfg.batch.max_concurrent == 3
    assert cfg.batch.max_findings_per_repo == 5
