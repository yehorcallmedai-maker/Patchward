# KS-TRACE: AC-P1-09, C-08 | assumption: package.json presence = JS ecosystem;
# pyproject.toml / requirements.txt / setup.py = Python ecosystem
# | test: test_repo.py::test_repo_detection_*
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class Ecosystem(str, Enum):
    PYTHON = "python"
    NODE = "node"
    BOTH = "both"
    UNKNOWN = "unknown"


class PackageManager(str, Enum):
    UV = "uv"
    POETRY = "poetry"
    PIP = "pip"
    NPM = "npm"
    PNPM = "pnpm"
    YARN = "yarn"
    UNKNOWN = "unknown"


class TestRunner(str, Enum):
    PYTEST = "pytest"
    JEST = "jest"
    UNKNOWN = "unknown"


@dataclass
class RepoContext:
    """
    Auto-detected repository context. All fields are derived from the filesystem
    on construction — no hardcoding, no network calls.

    # KS-TRACE: AC-P1-09, C-08 | test: test_repo.py
    """
    repo_path: Path
    ecosystem: Ecosystem = Ecosystem.UNKNOWN
    package_manager: PackageManager = PackageManager.UNKNOWN
    test_runner: TestRunner = TestRunner.UNKNOWN
    lockfile_path: Path | None = None
    has_package_json: bool = False

    # Python-specific
    has_requirements_txt: bool = False
    has_pyproject_toml: bool = False

    @classmethod
    def from_path(cls, repo_path: Path) -> "RepoContext":
        """Detect ecosystem, package manager, test runner, and lockfile from filesystem."""
        ctx = cls(repo_path=repo_path)
        ctx._detect(repo_path)
        return ctx

    def _detect(self, p: Path) -> None:
        has_python = self._detect_python(p)
        has_node = self._detect_node(p)

        if has_python and has_node:
            self.ecosystem = Ecosystem.BOTH
        elif has_python:
            self.ecosystem = Ecosystem.PYTHON
        elif has_node:
            self.ecosystem = Ecosystem.NODE
        else:
            self.ecosystem = Ecosystem.UNKNOWN

        self._detect_test_runner(p)

    def _detect_python(self, p: Path) -> bool:
        self.has_requirements_txt = (p / "requirements.txt").exists()
        self.has_pyproject_toml = (p / "pyproject.toml").exists()
        has_setup_py = (p / "setup.py").exists()
        has_setup_cfg = (p / "setup.cfg").exists()
        has_any_py = bool(list(p.glob("*.py"))) or bool(list(p.glob("src/**/*.py")))

        is_python = any([
            self.has_requirements_txt,
            self.has_pyproject_toml,
            has_setup_py,
            has_setup_cfg,
            has_any_py,
        ])

        if is_python:
            self.package_manager = self._detect_python_pm(p)

        return is_python

    def _detect_python_pm(self, p: Path) -> PackageManager:
        # uv: uv.lock present, or [tool.uv] in pyproject.toml
        if (p / "uv.lock").exists():
            self.lockfile_path = p / "uv.lock"
            return PackageManager.UV
        if self.has_pyproject_toml:
            try:
                content = (p / "pyproject.toml").read_text(encoding="utf-8")
                if "[tool.uv]" in content or 'requires = ["uv' in content:
                    return PackageManager.UV
                if "[tool.poetry]" in content:
                    lock = p / "poetry.lock"
                    if lock.exists():
                        self.lockfile_path = lock
                    return PackageManager.POETRY
            except OSError:
                pass
        if (p / "poetry.lock").exists():
            self.lockfile_path = p / "poetry.lock"
            return PackageManager.POETRY
        if self.has_requirements_txt:
            return PackageManager.PIP
        return PackageManager.UNKNOWN

    def _detect_node(self, p: Path) -> bool:
        self.has_package_json = (p / "package.json").exists()
        if not self.has_package_json:
            return False

        # Only override package_manager if Python didn't already claim it
        if self.package_manager == PackageManager.UNKNOWN:
            if (p / "pnpm-lock.yaml").exists():
                self.lockfile_path = p / "pnpm-lock.yaml"
                self.package_manager = PackageManager.PNPM
            elif (p / "yarn.lock").exists():
                self.lockfile_path = p / "yarn.lock"
                self.package_manager = PackageManager.YARN
            elif (p / "package-lock.json").exists():
                self.lockfile_path = p / "package-lock.json"
                self.package_manager = PackageManager.NPM
            else:
                self.package_manager = PackageManager.NPM  # default for Node

        return True

    def _detect_test_runner(self, p: Path) -> None:
        # pytest: pyproject.toml [tool.pytest...] or pytest.ini or conftest.py
        if (
            (p / "pytest.ini").exists()
            or (p / "conftest.py").exists()
            or bool(list(p.glob("tests/conftest.py")))
        ):
            self.test_runner = TestRunner.PYTEST
            return
        if self.has_pyproject_toml:
            try:
                content = (p / "pyproject.toml").read_text(encoding="utf-8")
                if "[tool.pytest" in content:
                    self.test_runner = TestRunner.PYTEST
                    return
            except OSError:
                pass
        # jest: jest key in package.json, or jest.config.*
        if self.has_package_json:
            for cfg in ["jest.config.js", "jest.config.ts", "jest.config.mjs"]:
                if (p / cfg).exists():
                    self.test_runner = TestRunner.JEST
                    return
            try:
                import json
                pkg = json.loads((p / "package.json").read_text(encoding="utf-8"))
                if "jest" in pkg or "jest" in pkg.get("scripts", {}).get("test", ""):
                    self.test_runner = TestRunner.JEST
                    return
            except (OSError, ValueError):
                pass
        self.test_runner = TestRunner.UNKNOWN
