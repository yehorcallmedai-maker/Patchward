# KS-TRACE: AC-P1-03, C-03 | assumption: SARIF 2.1.0 structural validation sufficient for Phase 1;
# full JSON Schema validation deferred to Phase 4 | test: test_sarif.py
#
# C-03 firewall: every scanner's raw stdout passes through SARIFNormalizer before
# reaching any other layer. Raw output NEVER bypasses this module.
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


class SARIFValidationError(ValueError):
    """Raised when a SARIFRun or SARIF document fails structural validation.

    # KS-TRACE: AC-P1-03 | assumption: structural check (ruleId, locations, message)
    # is sufficient for Phase 1; full jsonschema validation is Phase 4.
    """


SARIF_VERSION = "2.1.0"
SARIF_SCHEMA = "https://schemastore.azurewebsites.net/schemas/json/sarif-2.1.0.json"

# Severity → SARIF level mappings per tool
_BANDIT_LEVEL: dict[str, str] = {
    "LOW": "note",
    "MEDIUM": "warning",
    "HIGH": "error",
}
_ESLINT_LEVEL: dict[int, str] = {1: "warning", 2: "error"}
_NPM_LEVEL: dict[str, str] = {
    "info": "note",
    "low": "note",
    "moderate": "warning",
    "high": "error",
    "critical": "error",
}
_OSV_LEVEL: dict[str, str] = {
    "LOW": "note",
    "MODERATE": "warning",
    "HIGH": "error",
    "CRITICAL": "error",
}


@dataclass
class SARIFLocation:
    uri: str
    start_line: int | None = None
    end_line: int | None = None

    def to_dict(self) -> dict[str, Any]:
        phys: dict[str, Any] = {"artifactLocation": {"uri": self.uri}}
        region: dict[str, int] = {}
        if self.start_line is not None:
            region["startLine"] = self.start_line
        if self.end_line is not None:
            region["endLine"] = self.end_line
        if region:
            phys["region"] = region
        return {"physicalLocation": phys}


@dataclass
class SARIFResult:
    rule_id: str
    message: str
    level: str = "warning"  # "error" | "warning" | "note" | "none"
    locations: list[SARIFLocation] = field(default_factory=list)
    fingerprint: str | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "ruleId": self.rule_id,
            "message": {"text": self.message},
            "level": self.level,
            "locations": [loc.to_dict() for loc in self.locations],
        }
        if self.fingerprint:
            d["partialFingerprints"] = {"primaryLocationLineHash": self.fingerprint}
        return d


@dataclass
class SARIFRun:
    tool_name: str
    tool_version: str = "unknown"
    results: list[SARIFResult] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool": {
                "driver": {
                    "name": self.tool_name,
                    "version": self.tool_version,
                }
            },
            "results": [r.to_dict() for r in self.results],
        }

    def to_findings(self) -> list[dict[str, Any]]:
        """Flatten to the dict format expected by db.insert_finding."""
        findings = []
        for r in self.results:
            loc = r.locations[0] if r.locations else None
            findings.append({
                "rule_id": r.rule_id,
                "file_path": loc.uri if loc else "",
                "line_start": loc.start_line if loc else None,
                "line_end": loc.end_line if loc else None,
                "severity": r.level,
                "message": r.message,
                "fingerprint": r.fingerprint,
            })
        return findings


def sarif_document(runs: list[SARIFRun]) -> dict[str, Any]:
    """Wrap one or more SARIFRun objects into a full SARIF 2.1.0 document."""
    return {
        "version": SARIF_VERSION,
        "$schema": SARIF_SCHEMA,
        "runs": [r.to_dict() for r in runs],
    }


class SARIFNormalizer:
    """
    Converts each scanner's raw JSON output into a SARIFRun.

    All methods are static and pure — no I/O, no side effects.
    This is the mandatory C-03 firewall: every scanner result passes
    through here before reaching the orchestrator or any LLM prompt.

    NOTE (KS-P1-03 flag): rule_id strings are passed through verbatim from
    each scanner. At normalizer assertion time, use exact strings as confirmed
    by the diagnostic probe (e.g. the full qualified Semgrep rule ID).
    """

    @staticmethod
    def from_semgrep(raw: dict) -> SARIFRun:
        """Semgrep --sarif output is native SARIF 2.1.0; parse into SARIFRun."""
        runs = raw.get("runs", [])
        if not runs:
            return SARIFRun(tool_name="semgrep")
        run = runs[0]
        version = (
            run.get("tool", {}).get("driver", {}).get("semanticVersion", "unknown")
        )
        results: list[SARIFResult] = []
        for r in run.get("results", []):
            rule_id = r.get("ruleId", "unknown")
            message = r.get("message", {}).get("text", "")
            level = r.get("level", "warning")
            fingerprint = (
                r.get("partialFingerprints", {}).get("primaryLocationLineHash")
                or r.get("fingerprints", {}).get("matchBasedId/v1")
            )
            locations: list[SARIFLocation] = []
            for loc in r.get("locations", []):
                phys = loc.get("physicalLocation", {})
                uri = phys.get("artifactLocation", {}).get("uri", "")
                region = phys.get("region", {})
                locations.append(SARIFLocation(
                    uri=uri,
                    start_line=region.get("startLine"),
                    end_line=region.get("endLine"),
                ))
            results.append(SARIFResult(
                rule_id=rule_id,
                message=message,
                level=level,
                locations=locations,
                fingerprint=fingerprint,
            ))
        return SARIFRun(tool_name="semgrep", tool_version=version, results=results)

    @staticmethod
    def from_bandit(raw: dict) -> SARIFRun:
        """Bandit --format json output."""
        version = raw.get("generated_at", "unknown")
        results: list[SARIFResult] = []
        for r in raw.get("results", []):
            test_id = r.get("test_id", "unknown")
            rule_id = f"bandit.{test_id}"
            message = r.get("issue_text", "")
            severity = r.get("issue_severity", "MEDIUM")
            level = _BANDIT_LEVEL.get(severity.upper(), "warning")
            file_path = r.get("filename", "")
            line = r.get("line_number")
            results.append(SARIFResult(
                rule_id=rule_id,
                message=message,
                level=level,
                locations=[SARIFLocation(uri=file_path, start_line=line, end_line=line)],
            ))
        return SARIFRun(tool_name="bandit", tool_version=version, results=results)

    @staticmethod
    def from_pip_audit(raw: dict) -> SARIFRun:
        """pip-audit --format json output."""
        results: list[SARIFResult] = []
        for dep in raw.get("dependencies", []):
            pkg = dep.get("name", "unknown")
            ver = dep.get("version", "unknown")
            for vuln in dep.get("vulns", []):
                vuln_id = vuln.get("id", "unknown")
                rule_id = f"pip-audit.{vuln_id}"
                desc = vuln.get("description", "")
                fixes = ", ".join(vuln.get("fix_versions", [])) or "no fix available"
                message = f"{pkg}@{ver} — {desc} Fix: {fixes}"
                results.append(SARIFResult(
                    rule_id=rule_id,
                    message=message,
                    level="error",
                    locations=[SARIFLocation(uri=f"requirements/{pkg}")],
                ))
        return SARIFRun(tool_name="pip-audit", results=results)

    @staticmethod
    def from_eslint(raw: list) -> SARIFRun:
        """ESLint -f json output (list of per-file result objects)."""
        results: list[SARIFResult] = []
        for file_result in raw:
            file_path = file_result.get("filePath", "")
            for msg in file_result.get("messages", []):
                rule_id = f"eslint.{msg.get('ruleId') or 'unknown'}"
                message = msg.get("message", "")
                level = _ESLINT_LEVEL.get(msg.get("severity", 1), "warning")
                line = msg.get("line")
                results.append(SARIFResult(
                    rule_id=rule_id,
                    message=message,
                    level=level,
                    locations=[SARIFLocation(uri=file_path, start_line=line, end_line=line)],
                ))
        return SARIFRun(tool_name="eslint", results=results)

    @staticmethod
    def from_npm_audit(raw: dict) -> SARIFRun:
        """npm audit --json output (npm v7+ format)."""
        results: list[SARIFResult] = []
        for pkg_name, vuln in raw.get("vulnerabilities", {}).items():
            severity = vuln.get("severity", "moderate")
            level = _NPM_LEVEL.get(severity.lower(), "warning")
            for via_entry in vuln.get("via", []):
                if isinstance(via_entry, dict):
                    rule_id = f"npm-audit.{pkg_name}"
                    message = via_entry.get("title", f"Vulnerability in {pkg_name}")
                    results.append(SARIFResult(
                        rule_id=rule_id,
                        message=message,
                        level=level,
                        locations=[SARIFLocation(uri=f"node_modules/{pkg_name}")],
                    ))
        return SARIFRun(tool_name="npm-audit", results=results)

    @staticmethod
    def from_trivy(raw: dict) -> SARIFRun:
        """Trivy --format sarif output is SARIF 2.1.0; reuse the semgrep path."""
        run = SARIFNormalizer.from_semgrep(raw)
        run.tool_name = "trivy"
        return run

    @staticmethod
    def from_osv_scanner(raw: dict) -> SARIFRun:
        """osv-scanner --json output."""
        results: list[SARIFResult] = []
        for result in raw.get("results", []):
            source_path = result.get("source", {}).get("path", "unknown")
            for pkg_entry in result.get("packages", []):
                pkg = pkg_entry.get("package", {})
                pkg_name = pkg.get("name", "unknown")
                pkg_version = pkg.get("version", "unknown")
                for vuln in pkg_entry.get("vulnerabilities", []):
                    vuln_id = vuln.get("id", "unknown")
                    summary = vuln.get("summary", f"Vulnerability {vuln_id}")
                    severity = vuln.get("database_specific", {}).get("severity", "MODERATE")
                    level = _OSV_LEVEL.get(severity.upper(), "warning")
                    rule_id = f"osv-scanner.{vuln_id}"
                    message = f"{pkg_name}@{pkg_version}: {summary}"
                    results.append(SARIFResult(
                        rule_id=rule_id,
                        message=message,
                        level=level,
                        locations=[SARIFLocation(uri=source_path)],
                    ))
        return SARIFRun(tool_name="osv-scanner", results=results)


# ---------------------------------------------------------------------------
# Structural validation  (KS-P1-04, AC-P1-03)
# ---------------------------------------------------------------------------

_VALID_LEVELS = {"error", "warning", "note", "none"}


def validate_sarif_run(run: SARIFRun) -> None:
    """Validate that a SARIFRun is structurally sound.

    Checks:
    - tool_name is a non-empty string
    - every SARIFResult has a non-empty rule_id and non-empty message
    - every SARIFResult.level is a recognised SARIF level value
    - every SARIFLocation has a non-empty uri

    Raises SARIFValidationError describing the first violation found.
    # KS-TRACE: AC-P1-03 | test: test_sarif.py::test_sarif_validation_*
    """
    if not run.tool_name:
        raise SARIFValidationError("SARIFRun.tool_name must not be empty")

    for idx, result in enumerate(run.results):
        prefix = f"results[{idx}]"
        if not result.rule_id:
            raise SARIFValidationError(f"{prefix}.rule_id must not be empty")
        if not result.message:
            raise SARIFValidationError(f"{prefix}.message must not be empty")
        if result.level not in _VALID_LEVELS:
            raise SARIFValidationError(
                f"{prefix}.level '{result.level}' is not a valid SARIF level "
                f"(expected one of {sorted(_VALID_LEVELS)})"
            )
        for loc_idx, loc in enumerate(result.locations):
            if not loc.uri:
                raise SARIFValidationError(
                    f"{prefix}.locations[{loc_idx}].uri must not be empty"
                )


def validate_sarif_document(doc: dict[str, Any]) -> None:
    """Validate that a serialised SARIF 2.1.0 document dict is structurally sound.

    Checks:
    - version == "2.1.0"
    - runs is a list
    - each run contains tool.driver.name, and results list
    - each result contains ruleId, message.text, locations list

    Raises SARIFValidationError on first violation.
    # KS-TRACE: AC-P1-03 | test: test_sarif.py::test_sarif_document_validation_*
    """
    if doc.get("version") != SARIF_VERSION:
        raise SARIFValidationError(
            f"SARIF document version must be '{SARIF_VERSION}', got '{doc.get('version')}'"
        )
    runs = doc.get("runs")
    if not isinstance(runs, list):
        raise SARIFValidationError("SARIF document must contain a 'runs' list")

    for run_idx, run in enumerate(runs):
        rprefix = f"runs[{run_idx}]"
        driver_name = run.get("tool", {}).get("driver", {}).get("name", "")
        if not driver_name:
            raise SARIFValidationError(f"{rprefix}.tool.driver.name must not be empty")

        results = run.get("results")
        if not isinstance(results, list):
            raise SARIFValidationError(f"{rprefix}.results must be a list")

        for res_idx, result in enumerate(results):
            sprefix = f"{rprefix}.results[{res_idx}]"
            if not result.get("ruleId"):
                raise SARIFValidationError(f"{sprefix}.ruleId must not be empty")
            if not result.get("message", {}).get("text"):
                raise SARIFValidationError(f"{sprefix}.message.text must not be empty")
            if not isinstance(result.get("locations"), list):
                raise SARIFValidationError(f"{sprefix}.locations must be a list")
