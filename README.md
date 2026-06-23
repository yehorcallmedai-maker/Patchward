# RepoMend

Local-first multi-repo security agent: scans your code for vulnerabilities,
generates patches with an LLM subagent, verifies them deterministically, and
opens draft GitHub PRs for human review.

## Prerequisites

- Python 3.12+, uv, Docker Desktop
- Scanners on PATH: semgrep, bandit, pip-audit, trivy
- Anthropic API key + GitHub personal access token

See [docs/user_guide.md](docs/user_guide.md) for full setup instructions.

## Installation

```
uv tool install repomend
```

## Quick Start

```
cp repomend.toml.example repomend.toml
# edit repomend.toml with your GitHub owner/repo and API keys
repomend scan --repo /path/to/your/repo
repomend fix  --repo /path/to/your/repo
```

Batch mode (multiple repos defined in repomend.toml):

```
repomend batch
```

## Documentation

Full configuration reference, prerequisites, and usage examples:
[docs/user_guide.md](docs/user_guide.md)
