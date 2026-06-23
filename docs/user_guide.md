# RepoMend User Guide

## Prerequisites

- Python 3.12+
- uv: https://docs.astral.sh/uv/getting-started/installation/
- Docker Desktop (for sandbox isolation): https://docs.docker.com/desktop/
- Scanners installed on PATH:
  - semgrep: `pip install semgrep`
  - bandit: `pip install bandit`
  - pip-audit: `pip install pip-audit`
  - trivy: https://trivy.dev/latest/getting-started/installation/
  - eslint (JS/TS repos): `npm install -g eslint`
- Anthropic API key: https://console.anthropic.com
- GitHub personal access token with `repo` + `pull_requests: write`

## Installation

Install RepoMend using uv:

```
uv tool install repomend
```

Verify:

```
repomend --version
repomend --help
```

## Configuration

Copy the example config and fill in your values:

```
cp repomend.toml.example repomend.toml
```

Set required environment variables:

```
export ANTHROPIC_API_KEY="sk-ant-..."
export GITHUB_TOKEN="github_pat_..."
```

## Quick Start

Scan a single repo:

```
repomend scan --repo /path/to/your/repo
```

Fix and open a PR:

```
repomend fix --repo /path/to/your/repo
```

Batch mode (multi-repo, defined in repomend.toml):

```
repomend batch
```

## Config Reference

All fields supported in `repomend.toml`:

| Field | Type | Default | Description |
|---|---|---|---|
| `[github].owner` | string | `""` | GitHub org or username |
| `[github].repo` | string | `""` | GitHub repository name |
| `[github].base_branch` | string | `"main"` | Branch PRs target |
| `[batch].max_concurrent` | int | `3` | Max repos processed concurrently |
| `[batch].max_findings_per_repo` | int | `5` | Max findings Fix-Gen attempts per repo per run |
| `[models].scanner_model` | string | `"claude-haiku-4-5-20251001"` | Model for scanner triage (cheap/fast) |
| `[models].fix_model` | string | `"claude-sonnet-4-6"` | Model for fix generation and verification |
| `[verifier].timeout_seconds` | int | `120` | Timeout for Gate 1 scanner re-runs |
| `[verifier].max_out_of_bounds_lines` | int | `0` | Max lines a fix may touch outside the vulnerability range |
| `[[repos]].path` | string | required | Absolute path to the local repo clone |
| `[[repos]].owner` | string | inherits `[github]` | Per-repo GitHub owner override |
| `[[repos]].repo` | string | inherits `[github]` | Per-repo GitHub repo name override |
| `[[repos]].base_branch` | string | `"main"` | Per-repo base branch override |
