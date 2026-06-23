# KS-TRACE: AC-P7-07, AC-P7-08, AC-P7-09
# | assumption: all distribution artifacts (toml.example, user_guide,
# |             README) are committed at project root / docs/
# | test: test_distribution.py
"""
Distribution artifact existence and content checks (Track B, Phase 7).
"""
from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent


def test_repomend_toml_example_exists() -> None:
    """repomend.toml.example must be present at project root.
    (AC-P7-07)"""
    assert (PROJECT_ROOT / "repomend.toml.example").exists(), (
        "repomend.toml.example not found at project root"
    )


def test_user_guide_exists_with_five_sections() -> None:
    """docs/user_guide.md must exist and contain all 5 required
    section headings. (AC-P7-08)"""
    guide = PROJECT_ROOT / "docs" / "user_guide.md"
    assert guide.exists(), "docs/user_guide.md not found"
    text = guide.read_text(encoding="utf-8")
    required = [
        "## Prerequisites",
        "## Installation",
        "## Configuration",
        "## Quick Start",
        "## Config Reference",
    ]
    for heading in required:
        assert heading in text, (
            f"docs/user_guide.md missing heading: {heading!r}"
        )


def test_readme_contains_uv_install_and_user_guide_link() -> None:
    """README.md must mention uv tool install and link to
    docs/user_guide.md. (AC-P7-09)"""
    readme = PROJECT_ROOT / "README.md"
    assert readme.exists(), "README.md not found"
    text = readme.read_text(encoding="utf-8")
    assert "uv tool install" in text, (
        "README.md missing 'uv tool install'"
    )
    assert "docs/user_guide.md" in text, (
        "README.md missing link to docs/user_guide.md"
    )
