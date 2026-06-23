# KS-TRACE: AC-P1-03, C-03 | assumption: SARIF 2.1.0 structural schema sufficient
# | test: normalizer unit tests — no subprocess, no I/O
from __future__ import annotations

from repomend.sarif import (
    SARIF_SCHEMA,
    SARIF_VERSION,
    SARIFLocation,
    SARIFNormalizer,
    SARIFResult,
    SARIFRun,
    sarif_document,
)


# ---------------------------------------------------------------------------
# Dataclass serialisation
# ---------------------------------------------------------------------------

def test_sarif_location_with_lines() -> None:
    loc = SARIFLocation(uri="src/foo.py", start_line=10, end_line=12)
    d = loc.to_dict()
    phys = d["physicalLocation"]
    assert phys["artifactLocation"]["uri"] == "src/foo.py"
    assert phys["region"]["startLine"] == 10
    assert phys["region"]["endLine"] == 12


def test_sarif_location_no_lines() -> None:
    loc = SARIFLocation(uri="requirements.txt")
    d = loc.to_dict()
    assert "region" not in d["physicalLocation"]


def test_sarif_result_structure() -> None:
    """AC-P1-03: result dict contains ruleId, message, level, locations."""
    r = SARIFResult(
        rule_id="test.rule",
        message="bad thing happened",
        level="error",
        locations=[SARIFLocation(uri="a.py", start_line=5)],
    )
    d = r.to_dict()
    assert d["ruleId"] == "test.rule"
    assert d["message"] == {"text": "bad thing happened"}
    assert d["level"] == "error"
    assert len(d["locations"]) == 1
    assert "partialFingerprints" not in d


def test_sarif_result_with_fingerprint() -> None:
    r = SARIFResult(rule_id="r", message="m", fingerprint="fp-abc")
    d = r.to_dict()
    assert d["partialFingerprints"]["primaryLocationLineHash"] == "fp-abc"


def test_sarif_run_to_dict() -> None:
    run = SARIFRun(
        tool_name="semgrep",
        tool_version="1.2.3",
        results=[SARIFResult(rule_id="r1", message="msg")],
    )
    d = run.to_dict()
    assert d["tool"]["driver"]["name"] == "semgrep"
    assert d["tool"]["driver"]["version"] == "1.2.3"
    assert len(d["results"]) == 1


def test_sarif_run_empty() -> None:
    run = SARIFRun(tool_name="bandit")
    d = run.to_dict()
    assert d["results"] == []


def test_sarif_document_valid() -> None:
    """AC-P1-03: full document has version, $schema, and runs."""
    run = SARIFRun(tool_name="semgrep", results=[
        SARIFResult(rule_id="r", message="m", locations=[SARIFLocation(uri="f.py", start_line=1)])
    ])
    doc = sarif_document([run])
    assert doc["version"] == SARIF_VERSION
    assert doc["$schema"] == SARIF_SCHEMA
    assert len(doc["runs"]) == 1
    result = doc["runs"][0]["results"][0]
    assert "ruleId" in result
    assert "message" in result
    assert "locations" in result


def test_sarif_run_to_findings_bridge() -> None:
    """to_findings() produces the flat dict format expected by db.insert_finding."""
    run = SARIFRun(tool_name="semgrep", results=[
        SARIFResult(
            rule_id="test.rule",
            message="bad",
            level="warning",
            locations=[SARIFLocation(uri="src/a.py", start_line=7, end_line=7)],
            fingerprint="fp-001",
        )
    ])
    findings = run.to_findings()
    assert len(findings) == 1
    f = findings[0]
    assert f["rule_id"] == "test.rule"
    assert f["file_path"] == "src/a.py"
    assert f["line_start"] == 7
    assert f["line_end"] == 7
    assert f["severity"] == "warning"
    assert f["message"] == "bad"
    assert f["fingerprint"] == "fp-001"


def test_sarif_run_to_findings_no_location() -> None:
    run = SARIFRun(tool_name="pip-audit", results=[
        SARIFResult(rule_id="pip-audit.CVE-1234", message="vuln")
    ])
    findings = run.to_findings()
    f = findings[0]
    assert f["file_path"] == ""
    assert f["line_start"] is None
    assert f["fingerprint"] is None


# ---------------------------------------------------------------------------
# SARIFNormalizer — from_semgrep
# ---------------------------------------------------------------------------

_SEMGREP_SARIF: dict = {
    "runs": [{
        "tool": {"driver": {"semanticVersion": "1.50.0"}},
        "results": [{
            "ruleId": "python.lang.security.audit.subprocess-shell-true.subprocess-shell-true",
            "message": {"text": "subprocess with shell=True"},
            "level": "warning",
            "locations": [{
                "physicalLocation": {
                    "artifactLocation": {"uri": "vulnerable.py"},
                    "region": {"startLine": 24, "endLine": 24},
                }
            }],
            "partialFingerprints": {"primaryLocationLineHash": "abc123"},
        }],
    }]
}


def test_from_semgrep_parses_finding() -> None:
    run = SARIFNormalizer.from_semgrep(_SEMGREP_SARIF)
    assert run.tool_name == "semgrep"
    assert run.tool_version == "1.50.0"
    assert len(run.results) == 1
    r = run.results[0]
    assert r.rule_id == "python.lang.security.audit.subprocess-shell-true.subprocess-shell-true"
    assert r.locations[0].uri == "vulnerable.py"
    assert r.locations[0].start_line == 24
    assert r.fingerprint == "abc123"


def test_from_semgrep_empty_runs() -> None:
    run = SARIFNormalizer.from_semgrep({"runs": []})
    assert run.tool_name == "semgrep"
    assert run.results == []


def test_from_semgrep_missing_runs_key() -> None:
    run = SARIFNormalizer.from_semgrep({})
    assert run.results == []


# ---------------------------------------------------------------------------
# SARIFNormalizer — from_bandit
# ---------------------------------------------------------------------------

_BANDIT_JSON: dict = {
    "generated_at": "2026-06-11T00:00:00Z",
    "results": [{
        "test_id": "B602",
        "test_name": "subprocess_popen_with_shell_equals_true",
        "issue_text": "subprocess call with shell=True identified",
        "issue_severity": "HIGH",
        "issue_confidence": "HIGH",
        "filename": "vulnerable.py",
        "line_number": 24,
    }]
}


def test_from_bandit_parses_finding() -> None:
    run = SARIFNormalizer.from_bandit(_BANDIT_JSON)
    assert run.tool_name == "bandit"
    assert len(run.results) == 1
    r = run.results[0]
    assert r.rule_id == "bandit.B602"
    assert r.level == "error"
    assert r.locations[0].uri == "vulnerable.py"
    assert r.locations[0].start_line == 24


def test_from_bandit_empty() -> None:
    run = SARIFNormalizer.from_bandit({"results": []})
    assert run.results == []


# ---------------------------------------------------------------------------
# SARIFNormalizer — from_pip_audit
# ---------------------------------------------------------------------------

_PIP_AUDIT_JSON: dict = {
    "dependencies": [{
        "name": "requests",
        "version": "2.25.0",
        "vulns": [{
            "id": "GHSA-j8r2-6x86-q33q",
            "description": "Requests leaks credentials to proxy.",
            "fix_versions": ["2.31.0"],
        }]
    }]
}


def test_from_pip_audit_parses_finding() -> None:
    run = SARIFNormalizer.from_pip_audit(_PIP_AUDIT_JSON)
    assert run.tool_name == "pip-audit"
    assert len(run.results) == 1
    r = run.results[0]
    assert r.rule_id == "pip-audit.GHSA-j8r2-6x86-q33q"
    assert r.level == "error"
    assert "requests@2.25.0" in r.message
    assert "2.31.0" in r.message


def test_from_pip_audit_no_vulns() -> None:
    run = SARIFNormalizer.from_pip_audit({"dependencies": [
        {"name": "urllib3", "version": "2.0.0", "vulns": []}
    ]})
    assert run.results == []


# ---------------------------------------------------------------------------
# SARIFNormalizer — from_eslint
# ---------------------------------------------------------------------------

_ESLINT_JSON: list = [{
    "filePath": "/repo/src/index.js",
    "messages": [{
        "ruleId": "no-eval",
        "severity": 2,
        "message": "eval can be harmful.",
        "line": 5,
        "column": 3,
    }]
}]


def test_from_eslint_parses_finding() -> None:
    run = SARIFNormalizer.from_eslint(_ESLINT_JSON)
    assert run.tool_name == "eslint"
    assert len(run.results) == 1
    r = run.results[0]
    assert r.rule_id == "eslint.no-eval"
    assert r.level == "error"
    assert r.locations[0].start_line == 5


def test_from_eslint_empty() -> None:
    run = SARIFNormalizer.from_eslint([])
    assert run.results == []


# ---------------------------------------------------------------------------
# SARIFNormalizer — from_npm_audit
# ---------------------------------------------------------------------------

_NPM_AUDIT_JSON: dict = {
    "vulnerabilities": {
        "lodash": {
            "name": "lodash",
            "severity": "high",
            "via": [{
                "title": "Prototype Pollution in lodash",
                "url": "https://github.com/advisories/GHSA-4xc9-xhrj-v574",
                "severity": "high",
            }]
        }
    }
}


def test_from_npm_audit_parses_finding() -> None:
    run = SARIFNormalizer.from_npm_audit(_NPM_AUDIT_JSON)
    assert run.tool_name == "npm-audit"
    assert len(run.results) == 1
    r = run.results[0]
    assert r.rule_id == "npm-audit.lodash"
    assert r.level == "error"
    assert "Prototype Pollution" in r.message


def test_from_npm_audit_transitive_only_skipped() -> None:
    """via entries that are plain strings (transitive refs) are skipped."""
    raw = {"vulnerabilities": {"dep": {"severity": "high", "via": ["other-dep"]}}}
    run = SARIFNormalizer.from_npm_audit(raw)
    assert run.results == []


def test_from_npm_audit_empty() -> None:
    run = SARIFNormalizer.from_npm_audit({"vulnerabilities": {}})
    assert run.results == []


# ---------------------------------------------------------------------------
# SARIFNormalizer — from_trivy
# ---------------------------------------------------------------------------

def test_from_trivy_delegates_to_semgrep_path() -> None:
    """Trivy SARIF has same structure; tool_name is patched to 'trivy'."""
    run = SARIFNormalizer.from_trivy(_SEMGREP_SARIF)
    assert run.tool_name == "trivy"
    assert len(run.results) == 1


# ---------------------------------------------------------------------------
# SARIFNormalizer — from_osv_scanner
# ---------------------------------------------------------------------------

_OSV_JSON: dict = {
    "results": [{
        "source": {"path": "/repo/requirements.txt", "type": "lockfile"},
        "packages": [{
            "package": {"name": "Pillow", "version": "9.0.0", "ecosystem": "PyPI"},
            "vulnerabilities": [{
                "id": "GHSA-56pw-mpj4-fxww",
                "summary": "Pillow heap buffer overflow",
                "database_specific": {"severity": "HIGH"},
            }]
        }]
    }]
}


def test_from_osv_scanner_parses_finding() -> None:
    run = SARIFNormalizer.from_osv_scanner(_OSV_JSON)
    assert run.tool_name == "osv-scanner"
    assert len(run.results) == 1
    r = run.results[0]
    assert r.rule_id == "osv-scanner.GHSA-56pw-mpj4-fxww"
    assert r.level == "error"
    assert "Pillow@9.0.0" in r.message
    assert r.locations[0].uri == "/repo/requirements.txt"


def test_from_osv_scanner_empty() -> None:
    run = SARIFNormalizer.from_osv_scanner({"results": []})
    assert run.results == []


# ---------------------------------------------------------------------------
# KS-P1-04: SARIFValidationError + validate_sarif_run / validate_sarif_document
# ---------------------------------------------------------------------------

from repomend.sarif import SARIFValidationError, validate_sarif_run, validate_sarif_document  # noqa: E402


def test_validate_sarif_run_valid() -> None:
    run = SARIFRun(
        tool_name="semgrep",
        results=[SARIFResult(
            rule_id="test.rule",
            message="msg",
            level="warning",
            locations=[SARIFLocation(uri="a.py", start_line=1)],
        )],
    )
    validate_sarif_run(run)  # must not raise


def test_validate_sarif_run_empty_results_valid() -> None:
    validate_sarif_run(SARIFRun(tool_name="bandit"))  # no findings is valid


def test_validate_sarif_run_missing_rule_id() -> None:
    run = SARIFRun(tool_name="semgrep", results=[
        SARIFResult(rule_id="", message="msg")
    ])
    import pytest as _pytest
    with _pytest.raises(SARIFValidationError, match="rule_id"):
        validate_sarif_run(run)


def test_validate_sarif_run_missing_message() -> None:
    run = SARIFRun(tool_name="semgrep", results=[
        SARIFResult(rule_id="r", message="")
    ])
    import pytest as _pytest
    with _pytest.raises(SARIFValidationError, match="message"):
        validate_sarif_run(run)


def test_validate_sarif_run_invalid_level() -> None:
    run = SARIFRun(tool_name="semgrep", results=[
        SARIFResult(rule_id="r", message="m", level="critical")  # not a valid SARIF level
    ])
    import pytest as _pytest
    with _pytest.raises(SARIFValidationError, match="level"):
        validate_sarif_run(run)


def test_validate_sarif_run_empty_location_uri() -> None:
    run = SARIFRun(tool_name="semgrep", results=[
        SARIFResult(rule_id="r", message="m", locations=[SARIFLocation(uri="")])
    ])
    import pytest as _pytest
    with _pytest.raises(SARIFValidationError, match="uri"):
        validate_sarif_run(run)


def test_validate_sarif_run_empty_tool_name() -> None:
    import pytest as _pytest
    with _pytest.raises(SARIFValidationError, match="tool_name"):
        validate_sarif_run(SARIFRun(tool_name=""))


def test_validate_sarif_document_valid() -> None:
    doc = sarif_document([SARIFRun(tool_name="semgrep", results=[
        SARIFResult(rule_id="r", message="m", locations=[SARIFLocation(uri="f.py")])
    ])])
    validate_sarif_document(doc)  # must not raise


def test_validate_sarif_document_wrong_version() -> None:
    import pytest as _pytest
    with _pytest.raises(SARIFValidationError, match="version"):
        validate_sarif_document({"version": "1.0.0", "runs": []})


def test_validate_sarif_document_missing_runs() -> None:
    import pytest as _pytest
    with _pytest.raises(SARIFValidationError, match="runs"):
        validate_sarif_document({"version": "2.1.0"})


def test_validate_sarif_document_missing_rule_id() -> None:
    import pytest as _pytest
    doc = {
        "version": "2.1.0",
        "runs": [{
            "tool": {"driver": {"name": "semgrep"}},
            "results": [{"ruleId": "", "message": {"text": "m"}, "locations": []}],
        }]
    }
    with _pytest.raises(SARIFValidationError, match="ruleId"):
        validate_sarif_document(doc)
