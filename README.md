# Patchward

Local-first multi-repo security agent: scans your code for vulnerabilities,
generates patches with an LLM subagent, verifies them deterministically, and
opens draft GitHub PRs for human review.

## Prerequisites

- Python 3.12+, uv, Docker Desktop
- Scanners on PATH: semgrep, bandit, pip-audit, trivy
- Anthropic API key + GitHub personal access token

See [docs/user_guide.md](docs/user_guide.md) for full setup instructions.

## Installation

Patchward is not yet published to PyPI. Install from source:

```
git clone https://github.com/yehorcallmedai-maker/Patchward.git
cd Patchward
uv tool install .
```

## Quick Start

```
cp patchward.toml.example patchward.toml
# edit patchward.toml with your GitHub owner/repo and API keys
patchward scan --repo /path/to/your/repo
patchward fix  --repo /path/to/your/repo
```

Batch mode (multiple repos defined in patchward.toml):

```
patchward batch
```

## Documentation

Full configuration reference, prerequisites, and usage examples:
[docs/user_guide.md](docs/user_guide.md)
