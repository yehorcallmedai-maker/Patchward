# KS-TRACE: AC-P1-09, C-08 | assumption: package.json = JS ecosystem
# | test: RepoContext auto-detection against synthetic and fixture structures
from __future__ import annotations

import json
from pathlib import Path

import pytest

from patchward.repo import Ecosystem, PackageManager, RepoContext, TestRunner


# ---------------------------------------------------------------------------
# Helper: build a minimal Python-only repo layout in tmp_path
# ---------------------------------------------------------------------------

def make_python_repo(tmp_path: Path, *, pm: str = "pip") -> Path:
    (tmp_path / "main.py").write_text("print('hello')", encoding="utf-8")
    if pm == "pip":
        (tmp_path / "requirements.txt").write_text("requests==2.31.0\n", encoding="utf-8")
    elif pm == "uv":
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname="x"\n[tool.uv]\n', encoding="utf-8"
        )
        (tmp_path / "uv.lock").write_text("# uv lock\n", encoding="utf-8")
    elif pm == "poetry":
        (tmp_path / "pyproject.toml").write_text(
            '[tool.poetry]\nname = "x"\n', encoding="utf-8"
        )
        (tmp_path / "poetry.lock").write_text("# poetry lock\n", encoding="utf-8")
    return tmp_path


def make_node_repo(tmp_path: Path, *, pm: str = "npm") -> Path:
    pkg: dict = {"name": "my-app", "version": "1.0.0"}
    (tmp_path / "package.json").write_text(json.dumps(pkg), encoding="utf-8")
    if pm == "npm":
        (tmp_path / "package-lock.json").write_text("{}", encoding="utf-8")
    elif pm == "pnpm":
        (tmp_path / "pnpm-lock.yaml").write_text("lockfileVersion: '6.0'\n", encoding="utf-8")
    elif pm == "yarn":
        (tmp_path / "yarn.lock").write_text("# yarn lockfile\n", encoding="utf-8")
    return tmp_path


# ---------------------------------------------------------------------------
# Ecosystem detection
# ---------------------------------------------------------------------------

def test_detect_python_pip(tmp_path: Path) -> None:
    make_python_repo(tmp_path, pm="pip")
    ctx = RepoContext.from_path(tmp_path)
    assert ctx.ecosystem == Ecosystem.PYTHON
    assert ctx.package_manager == PackageManager.PIP
    assert ctx.has_requirements_txt is True
    assert ctx.has_package_json is False


def test_detect_python_uv(tmp_path: Path) -> None:
    make_python_repo(tmp_path, pm="uv")
    ctx = RepoContext.from_path(tmp_path)
    assert ctx.ecosystem == Ecosystem.PYTHON
    assert ctx.package_manager == PackageManager.UV
    assert ctx.lockfile_path is not None
    assert ctx.lockfile_path.name == "uv.lock"


def test_detect_python_poetry(tmp_path: Path) -> None:
    make_python_repo(tmp_path, pm="poetry")
    ctx = RepoContext.from_path(tmp_path)
    assert ctx.ecosystem == Ecosystem.PYTHON
    assert ctx.package_manager == PackageManager.POETRY
    assert ctx.lockfile_path is not None
    assert ctx.lockfile_path.name == "poetry.lock"


def test_detect_node_npm(tmp_path: Path) -> None:
    make_node_repo(tmp_path, pm="npm")
    ctx = RepoContext.from_path(tmp_path)
    assert ctx.ecosystem == Ecosystem.NODE
    assert ctx.package_manager == PackageManager.NPM
    assert ctx.has_package_json is True
    assert ctx.lockfile_path is not None
    assert ctx.lockfile_path.name == "package-lock.json"


def test_detect_node_pnpm(tmp_path: Path) -> None:
    make_node_repo(tmp_path, pm="pnpm")
    ctx = RepoContext.from_path(tmp_path)
    assert ctx.ecosystem == Ecosystem.NODE
    assert ctx.package_manager == PackageManager.PNPM
    assert ctx.lockfile_path.name == "pnpm-lock.yaml"  # type: ignore[union-attr]


def test_detect_node_yarn(tmp_path: Path) -> None:
    make_node_repo(tmp_path, pm="yarn")
    ctx = RepoContext.from_path(tmp_path)
    assert ctx.ecosystem == Ecosystem.NODE
    assert ctx.package_manager == PackageManager.YARN


def test_detect_both_ecosystems(tmp_path: Path) -> None:
    make_python_repo(tmp_path, pm="pip")
    make_node_repo(tmp_path, pm="npm")
    ctx = RepoContext.from_path(tmp_path)
    assert ctx.ecosystem == Ecosystem.BOTH


def test_detect_unknown_ecosystem(tmp_path: Path) -> None:
    # Empty directory with no recognised files
    ctx = RepoContext.from_path(tmp_path)
    assert ctx.ecosystem == Ecosystem.UNKNOWN
    assert ctx.package_manager == PackageManager.UNKNOWN


# ---------------------------------------------------------------------------
# Test runner detection
# ---------------------------------------------------------------------------

def test_detect_pytest_via_ini(tmp_path: Path) -> None:
    (tmp_path / "pytest.ini").write_text("[pytest]\n", encoding="utf-8")
    ctx = RepoContext.from_path(tmp_path)
    assert ctx.test_runner == TestRunner.PYTEST


def test_detect_pytest_via_conftest(tmp_path: Path) -> None:
    (tmp_path / "conftest.py").write_text("", encoding="utf-8")
    ctx = RepoContext.from_path(tmp_path)
    assert ctx.test_runner == TestRunner.PYTEST


def test_detect_pytest_via_pyproject(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        "[tool.pytest.ini_options]\ntestpaths = ['tests']\n", encoding="utf-8"
    )
    (tmp_path / "main.py").write_text("", encoding="utf-8")
    ctx = RepoContext.from_path(tmp_path)
    assert ctx.test_runner == TestRunner.PYTEST


def test_detect_jest_via_config(tmp_path: Path) -> None:
    make_node_repo(tmp_path)
    (tmp_path / "jest.config.js").write_text("module.exports = {}", encoding="utf-8")
    ctx = RepoContext.from_path(tmp_path)
    assert ctx.test_runner == TestRunner.JEST


def test_detect_jest_via_package_json(tmp_path: Path) -> None:
    pkg = {"name": "app", "version": "1.0.0", "jest": {"testEnvironment": "node"}}
    (tmp_path / "package.json").write_text(json.dumps(pkg), encoding="utf-8")
    ctx = RepoContext.from_path(tmp_path)
    assert ctx.test_runner == TestRunner.JEST


def test_detect_unknown_test_runner(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text("", encoding="utf-8")
    ctx = RepoContext.from_path(tmp_path)
    assert ctx.test_runner == TestRunner.UNKNOWN


# ---------------------------------------------------------------------------
# Against the real fixture repo structure  (AC-P1-09 evidence)
# ---------------------------------------------------------------------------

def test_fixture_repo_detection() -> None:
    """
    patchward-fixture: Python only, requirements.txt, no package.json.
    ESLint and npm audit must be skipped per AC-P1-09 / C-08.
    """
    fixture = Path("C:/Dev/Projects/patchward-fixture")
    if not fixture.exists():
        pytest.skip("patchward-fixture not available in this environment")
    ctx = RepoContext.from_path(fixture)
    assert ctx.ecosystem == Ecosystem.PYTHON
    assert ctx.has_package_json is False
    assert ctx.has_requirements_txt is True
    # These are the gate flags scanner.py checks before running JS tools
    assert ctx.has_package_json is False  # ESLint + npm audit must be skipped
