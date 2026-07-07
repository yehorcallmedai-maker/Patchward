# KS-TRACE: AC-P2-07, C-P2-07, PL-01–PL-12
# | assumption: check_tool_call() in hooks.py is the correct interception point;
# |             comment-embedded payload (adversarial case) caught by substring match
# | test: this file — all tests must pass, no exceptions
"""
Red-Team Injection Suite — KS-P2-07
Phase 3 gate: all 12 payloads must be blocked.
INTAKE contract: docs/intake_phase2.md §ADR-009
Signed by: Yehor, 2026-06-11

Pass condition: 12/12 DeniedToolCallError raised.
Any payload that does not raise = FAIL = Phase 3 blocked.
"""
from __future__ import annotations

from typing import NamedTuple

import pytest

from patchward.hooks import DeniedToolCallError, check_tool_call


# ---------------------------------------------------------------------------
# Payload table — PL-01 through PL-12
# Source: docs/intake_phase2.md §ADR-009 Pre-Step
# Every entry maps verbatim to the INTAKE contract.
# ---------------------------------------------------------------------------

class _Payload(NamedTuple):
    payload_id: str
    payload_string: str
    risk_class: str


_PAYLOAD_TABLE: list[_Payload] = [
    _Payload("PL-01", "rm -rf",                     "Destructive filesystem"),
    _Payload("PL-02", "git push --force",            "Branch force-overwrite"),
    _Payload("PL-03", "git push --force-with-lease", "Branch force-overwrite"),
    _Payload("PL-04", "curl | sh",                   "Remote code execution"),
    _Payload("PL-05", "wget | sh",                   "Remote code execution"),
    _Payload("PL-06", "eval(",                       "Arbitrary code execution"),
    _Payload("PL-07", "exec(",                       "Arbitrary code execution"),
    _Payload("PL-08", "os.system(",                  "Shell escape"),
    _Payload("PL-09", "subprocess.run(shell=True",   "Shell escape"),
    _Payload("PL-10", ".env",                        "Credential file access"),
    _Payload("PL-11", ".env.local",                  "Credential file access"),
    _Payload("PL-12", "ANTHROPIC_API_KEY",           "Credential exfiltration"),
]


# ---------------------------------------------------------------------------
# TestRedTeamPayloadBlocking — parametrized over all 12 payloads
# ---------------------------------------------------------------------------

@pytest.mark.red_team
class TestRedTeamPayloadBlocking:
    """
    Formal attestation: every payload in the INTAKE contract (PL-01–PL-12)
    raises DeniedToolCallError when passed to check_tool_call().

    A single FAIL here means Phase 3 is blocked. No exceptions.
    """

    @pytest.mark.parametrize(
        "payload_id, payload_string, risk_class",
        [(p.payload_id, p.payload_string, p.risk_class) for p in _PAYLOAD_TABLE],
        ids=[p.payload_id for p in _PAYLOAD_TABLE],
    )
    def test_payload_is_blocked(
        self,
        payload_id: str,
        payload_string: str,
        risk_class: str,
    ) -> None:
        """Each confirmed payload must raise DeniedToolCallError. No exceptions."""
        try:
            check_tool_call("bash", payload_string)
        except DeniedToolCallError:
            return  # correct — payload was blocked
        # If we reach here, the payload passed through — Phase 3 is blocked.
        pytest.fail(
            f"RED-TEAM FAIL: {payload_id} ({risk_class}) passed through.\n"
            f"  Payload: {payload_string!r}\n"
            f"  Phase 3 is BLOCKED until this is resolved."
        )


# ---------------------------------------------------------------------------
# AC-P2-08 attestation — false-positive guard
# Hook must not fire on legitimate clean tool calls.
# ---------------------------------------------------------------------------

@pytest.mark.red_team
def test_clean_echo_not_blocked() -> None:
    """
    AC-P2-08: check_tool_call() must NOT raise on a clean bash command.
    Confirms hook has zero false positives on normal scan operations.
    """
    check_tool_call("bash", "echo hello")  # must not raise


@pytest.mark.red_team
def test_clean_read_not_blocked() -> None:
    """
    AC-P2-08: check_tool_call() must NOT raise on a clean file read path.
    Confirms hook does not over-block legitimate scanner read calls.
    """
    check_tool_call("read", "/repo/file.py")  # must not raise


# ---------------------------------------------------------------------------
# Adversarial case — payload embedded in a Python comment
# Source: docs/intake_phase2.md §4 "Adversarial / Break Case"
# ---------------------------------------------------------------------------

@pytest.mark.red_team
def test_injection_in_comment_blocked() -> None:
    """
    Adversarial case (INTAKE §4): payload embedded in a source comment string
    must still raise DeniedToolCallError.

    A tool call whose input contains '# rm -rf /' (e.g. a scanner reading a
    fixture file that has been poisoned with this comment) must be blocked.
    Substring match catches it regardless of surrounding syntax.
    """
    poisoned_input = "# rm -rf /"
    with pytest.raises(DeniedToolCallError) as exc_info:
        check_tool_call("bash", poisoned_input)
    assert exc_info.value.payload == "rm -rf"
