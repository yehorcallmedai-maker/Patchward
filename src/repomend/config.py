# KS-TRACE: AC-05, AC-06, AC-P1-10, AC-P3-10, AC-P5-13, AC-P6-05,
#           AC-P6-06, AC-P6-07, C-P6-05, C-P6-06, ADR-022
# assumption: repomend.toml lives in cwd or explicit path
# test: test_config.py
from __future__ import annotations

import os
import sys
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib  # type: ignore[no-redef]

from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator, ValidationError
import typer


class FixGenConfig(BaseModel):
    """
    Fix-Gen subagent configuration (AC-P3-10).

    Loaded from ``[fix_gen]`` toml section.  All fields have safe
    defaults so the section can be omitted entirely.
    """
    max_turns: int = Field(default=10, gt=0, le=50)


class VerifierConfig(BaseModel):
    """
    Verifier configuration (C-P4-10).

    Loaded from ``[verifier]`` toml section.  All fields have safe
    defaults so the section can be omitted entirely.
    """
    # KS-TRACE: C-P4-10 | configurable timeout per gate subprocess call
    timeout_seconds: int = Field(default=120, gt=0, le=3600)


class GithubConfig(BaseModel):
    """
    GitHub integration configuration (C-P5-07, C-P5-10).

    Loaded from ``[github]`` toml section.  ``owner`` and ``repo``
    have no safe defaults — the CLI must reject a missing or empty
    value before any push/PR attempt.  ``base_branch`` defaults to
    ``"main"``.

    # KS-TRACE: C-P5-07, C-P5-10, AC-P5-13
    """
    owner: str = ""
    repo: str = ""
    base_branch: str = "main"


class RepoConfig(BaseModel):
    """
    Per-repository configuration entry (ADR-022, AC-P6-06).

    Constructed by ``load_config()`` after merging each ``[[repos]]``
    entry with ``[github]`` defaults.  Never loaded directly from toml
    by Pydantic — always constructed from pre-merged dicts.

    # KS-TRACE: AC-P6-06, AC-P6-07, C-P6-06, ADR-022
    """
    path: Path
    owner: str
    repo: str
    base_branch: str = "main"


class BatchConfig(BaseModel):
    """
    Concurrency configuration for multi-repo batch runs (C-P6-02).

    Loaded from ``[batch]`` toml section.  ``max_concurrent`` controls
    the ``asyncio.Semaphore`` ceiling.  Default of 3 is conservative
    relative to Anthropic Tier 1 rate limits (~40k TPM for Sonnet);
    three concurrent Fix-Gen calls at ~4k TPM each leaves comfortable
    headroom.  Users on Tier 2+ may safely raise this value.

    ``max_findings_per_repo`` caps how many findings Fix-Gen will
    attempt per repo per run. Default of 5 prevents unbounded cost
    on repos with many findings. (C-P7-02, AC-P7-11)

    # KS-TRACE: C-P6-02, C-P6-10, AC-P6-02, C-P7-02, AC-P7-11
    """
    max_concurrent: int = Field(default=3, gt=0)
    max_findings_per_repo: int = Field(default=5, gt=0)

    @field_validator("max_findings_per_repo")
    @classmethod
    def max_findings_must_be_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError(
                "batch.max_findings_per_repo must be >= 1, "
                f"got {v}"
            )
        return v


class ModelsConfig(BaseModel):
    """
    Model tiering configuration (C-P6-05, ADR-021).

    Loaded from ``[models]`` toml section.  ``scanner_model`` is used
    for Semgrep triage and Gate 1 (cheap/fast).  ``fix_model`` is used
    for Fix-Gen and Gate 2/3 semantic reasoning (capable/expensive).

    # KS-TRACE: C-P6-05, AC-P6-05, ADR-021
    """
    scanner_model: str = "claude-haiku-4-5-20251001"
    fix_model: str = "claude-sonnet-4-6"


class RepomendConfig(BaseModel):
    repo_path: Path
    semgrep_rules: str = "p/python"
    db_path: Path = Path("runs/state.db")
    langfuse_host: str = "https://cloud.langfuse.com"
    tracing_enabled: bool = True
    # KS-TRACE: AC-P1-10 | populated from .env via load_dotenv() before
    #           model init
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    # KS-TRACE: AC-P1-05, C-09 | injected from ANTHROPIC_API_KEY env
    #           var; never in toml
    anthropic_api_key: str = ""
    # KS-TRACE: AC-P3-10 | loaded from [fix_gen] toml section
    fix_gen: FixGenConfig = Field(default_factory=FixGenConfig)
    # KS-TRACE: C-P4-10 | loaded from [verifier] toml section
    verifier: VerifierConfig = Field(default_factory=VerifierConfig)
    # KS-TRACE: C-P5-07, C-P5-10 | loaded from [github] toml section
    github: GithubConfig = Field(default_factory=GithubConfig)
    # KS-TRACE: C-P6-02, C-P6-10 | loaded from [batch] toml section
    batch: BatchConfig = Field(default_factory=BatchConfig)
    # KS-TRACE: C-P6-05 | loaded from [models] toml section
    models: ModelsConfig = Field(default_factory=ModelsConfig)
    # KS-TRACE: C-P6-06, ADR-022 | populated by load_config() after
    #           [[repos]] merge; NOT a direct toml field
    repos: list[RepoConfig] = Field(default_factory=list)

    @field_validator("repo_path")
    @classmethod
    def repo_must_exist(cls, v: Path) -> Path:
        if not v.exists():
            raise ValueError(f"repo_path does not exist: {v}")
        return v

    @field_validator("db_path")
    @classmethod
    def ensure_db_parent(cls, v: Path) -> Path:
        v.parent.mkdir(parents=True, exist_ok=True)
        return v


def _build_repos(
    repos_raw: list[dict],
    github: GithubConfig,
    config_path: Path,
) -> list[RepoConfig]:
    """
    Merge each ``[[repos]]`` entry with ``[github]`` defaults and
    return a validated ``list[RepoConfig]``.

    Field-merge priority (highest → lowest):
      1. Per-entry value
      2. ``[github]`` section default
      3. Hard-coded fallback (base_branch = "main")

    Exits with code 1 if:
      - A ``[[repos]]`` entry is missing ``path``
      - ``owner`` or ``repo`` cannot be resolved for any entry

    # KS-TRACE: C-P6-06, ADR-022, Addendum A-01
    """
    result: list[RepoConfig] = []
    for idx, entry in enumerate(repos_raw):
        # path is required — no fallback
        if "path" not in entry:
            typer.echo(
                f"[repomend] ERROR: [[repos]] entry {idx} is missing"
                " required field 'path'.",
                err=True,
            )
            raise SystemExit(1)

        resolved_owner = entry.get("owner") or github.owner
        resolved_repo = entry.get("repo") or github.repo
        resolved_base = (
            entry.get("base_branch")
            or github.base_branch
            or "main"
        )

        missing = []
        if not resolved_owner:
            missing.append("owner")
        if not resolved_repo:
            missing.append("repo")
        if missing:
            fields = ", ".join(missing)
            typer.echo(
                f"[repomend] ERROR: [[repos]] entry {idx} is missing"
                f" field(s) '{fields}' and [github] provides no"
                " default. Add the field to the [[repos]] entry or"
                " set it in [github].",
                err=True,
            )
            raise SystemExit(1)

        result.append(
            RepoConfig(
                path=Path(entry["path"]),
                owner=resolved_owner,
                repo=resolved_repo,
                base_branch=resolved_base,
            )
        )
    return result


def load_config(
    config_path: Path | None = None,
    dotenv_path: Path | None = None,
) -> RepomendConfig:
    """Load and validate repomend.toml.

    Calls ``load_dotenv()`` before any credential access so that
    ``LANGFUSE_PUBLIC_KEY``, ``LANGFUSE_SECRET_KEY``, and any future
    secrets are available from the environment.  Exits with code 1 on
    any config error.

    Multi-repo support (ADR-022):
      - If ``[[repos]]`` entries are present, merges each with
        ``[github]`` defaults and populates ``cfg.repos``.
      - If ``[[repos]]`` is absent, falls back to a single-element
        list built from ``[github]`` (if ``owner`` and ``repo`` are
        set).  Preserves full backward compatibility with Phase 5
        single-repo configs.
    """
    # KS-TRACE: AC-P1-10 | load .env before reading any credentials
    load_dotenv(dotenv_path)  # no-op if file absent; never raises

    path = config_path or Path("repomend.toml")

    if not path.exists():
        typer.echo(
            f"[repomend] ERROR: config file not found: {path}",
            err=True,
        )
        raise SystemExit(1)

    try:
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        typer.echo(
            f"[repomend] ERROR: could not parse config: {exc}",
            err=True,
        )
        raise SystemExit(1)

    section = raw.get("repomend", {})

    # Inject env-sourced credentials; toml values take precedence if
    # explicitly set.
    section.setdefault(
        "langfuse_public_key",
        os.environ.get("LANGFUSE_PUBLIC_KEY", ""),
    )
    section.setdefault(
        "langfuse_secret_key",
        os.environ.get("LANGFUSE_SECRET_KEY", ""),
    )
    section.setdefault(
        "anthropic_api_key",
        os.environ.get("ANTHROPIC_API_KEY", ""),
    )

    # KS-TRACE: AC-P3-10 | [fix_gen] section → FixGenConfig
    fix_gen_raw = raw.get("fix_gen", {})
    if fix_gen_raw:
        section["fix_gen"] = fix_gen_raw

    # KS-TRACE: C-P4-10 | [verifier] section → VerifierConfig
    verifier_raw = raw.get("verifier", {})
    if verifier_raw:
        section["verifier"] = verifier_raw

    # KS-TRACE: C-P5-07, C-P5-10 | [github] section → GithubConfig
    github_raw = raw.get("github", {})
    if github_raw:
        section["github"] = github_raw

    # KS-TRACE: C-P6-02, C-P6-10 | [batch] section → BatchConfig
    batch_raw = raw.get("batch", {})
    if batch_raw:
        section["batch"] = batch_raw

    # KS-TRACE: C-P6-05 | [models] section → ModelsConfig
    models_raw = raw.get("models", {})
    if models_raw:
        section["models"] = models_raw

    try:
        cfg = RepomendConfig(**section)
    except ValidationError as exc:
        typer.echo(
            f"[repomend] ERROR: invalid config:\n{exc}", err=True
        )
        raise SystemExit(1)

    # KS-TRACE: C-P6-06, ADR-022 | [[repos]] merge
    # TOML array-of-tables appears under the top-level key "repos".
    repos_raw: list[dict] = raw.get("repos", [])
    if repos_raw:
        cfg.repos = _build_repos(repos_raw, cfg.github, path)
    elif cfg.github.owner and cfg.github.repo:
        # Backward-compatible fallback: build single-element list from
        # [github] singleton so that cfg.repos is always populated for
        # Phase 5 single-repo configs.
        cfg.repos = [
            RepoConfig(
                path=cfg.repo_path,
                owner=cfg.github.owner,
                repo=cfg.github.repo,
                base_branch=cfg.github.base_branch,
            )
        ]
    # else: repos stays [] — validate_github_config() handles the
    # missing-owner/repo case for single-repo CLI commands.

    return cfg


def validate_github_config(cfg: RepomendConfig) -> None:
    """
    Abort with SystemExit(1) if [github] owner or repo is unset.

    Call this at CLI startup for any command that requires GitHub
    access.  Provides an actionable error naming the missing field.

    # KS-TRACE: C-P5-10, AC-P5-13
    """
    missing = []
    if not cfg.github.owner:
        missing.append("owner")
    if not cfg.github.repo:
        missing.append("repo")
    if missing:
        fields = ", ".join(missing)
        msg_lines = [
            "[repomend] ERROR: repomend.toml is missing required",
            f"[github] fields: {fields}.",
            "Add to repomend.toml:",
            "  [github]",
        ]
        for f in missing:
            msg_lines.append('  {} = "your-{}"'.format(f, f))
        typer.echo("\n".join(msg_lines), err=True)
        raise SystemExit(1)
