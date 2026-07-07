# KS-TRACE: C-P2-03, AC-P2-04, AC-P2-08
# | assumption: substring match + allowlist suffices for all 12 confirmed payloads;
# |             AC-P2-08 false-positive test validates no over-blocking on clean scan calls
# | test: test_hooks.py
"""
PreToolUse deny hook for the patchward agent (Phase 2).

Fires before every tool call. Blocks the 12 confirmed payloads (PL-01–PL-12)
from the Phase 2 INTAKE contract. Safe on legitimate scanner tool calls (AC-P2-08).

Trust invariant enforced here:
  C-P2-03  Hook is the first line of defence — runs before subprocess, before Docker,
           before any I/O.

Usage::

    from patchward.hooks import check_tool_call, DeniedToolCallError

    try:
        check_tool_call(tool_name, json.dumps(tool_input))
    except DeniedToolCallError as exc:
        logger.warning("Blocked: %s", exc)
        raise
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Confirmed deny payload table — PL-01 through PL-12
# Source: docs/intake_phase2.md §ADR-009 Pre-Step (Yehor, 2026-06-11)
# DO NOT modify without updating the INTAKE contract and re-running test_hooks.py.
# ---------------------------------------------------------------------------
DENY_PAYLOADS: list[str] = [
    "rm -rf",                       # PL-01  Destructive filesystem
    "git push --force-with-lease",  # PL-03  Branch force-overwrite (before PL-02 — more specific)
    "git push --force",             # PL-02  Branch force-overwrite
    "curl | sh",                    # PL-04  Remote code execution
    "wget | sh",                    # PL-05  Remote code execution
    "eval(",                        # PL-06  Arbitrary code execution
    "exec(",                        # PL-07  Arbitrary code execution
    "os.system(",                   # PL-08  Shell escape
    "subprocess.run(shell=True",    # PL-09  Shell escape
    ".env.local",                   # PL-11  Credential file access (before PL-10 — more specific)
    ".env",                         # PL-10  Credential file access
    "ANTHROPIC_API_KEY",            # PL-12  Credential exfiltration
]

# Contexts that allowlist an otherwise-matching payload substring.
# A match at position [i:j] is allowlisted if any of these strings appears
# within _ALLOWLIST_WINDOW characters of the match.
# Source: docs/intake_phase2.md §7 Flag P2-A resolution (Yehor, 2026-06-11)
ALLOWLIST_CONTEXTS: list[str] = [
    "execute_",  # method/function prefixed with "execute_" — not builtin exec
    "execution",  # noun; common in test runner / SQL / task queue contexts
    "executor",   # class/variable name (e.g. ThreadPoolExecutor)
    "exec_",      # function prefixed with "exec_"
    "context",    # variable/class name (e.g. scan_context, RepoContext)
    "execute(",   # named method "execute" — distinct from builtin exec(
]

# Character window searched around a payload match when evaluating allowlist.
_ALLOWLIST_WINDOW: int = 30


class DeniedToolCallError(RuntimeError):
    """
    Raised by check_tool_call() when a deny-payload match is detected.

    Attributes:
        tool_name: Name of the tool that was blocked.
        payload:   The matched payload string (for logging and test assertions).
    """

    def __init__(self, tool_name: str, payload: str) -> None:
        self.tool_name = tool_name
        self.payload = payload
        super().__init__(
            f"Blocked tool call '{tool_name}': "
            f"input contains denied payload {payload!r}"
        )


def _match_is_allowlisted(text: str, match_start: int, match_end: int) -> bool:
    """
    Return True if the payload match at text[match_start:match_end] is surrounded
    by an allowlist context string within _ALLOWLIST_WINDOW characters.

    # KS-TRACE: C-P2-03, AC-P2-08
    """
    window_start = max(0, match_start - _ALLOWLIST_WINDOW)
    window_end = min(len(text), match_end + _ALLOWLIST_WINDOW)
    window = text[window_start:window_end]
    return any(ctx in window for ctx in ALLOWLIST_CONTEXTS)


def check_tool_call(tool_name: str, tool_input: str) -> None:
    """
    PreToolUse hook. Call before every tool execution.

    Scans tool_input for each payload in DENY_PAYLOADS. Raises DeniedToolCallError
    on first match unless the match falls within an allowlist context.

    Args:
        tool_name:  Name of the tool being invoked (for error message and logging).
        tool_input: Full stringified input of the tool call. Typically
                    json.dumps(tool_arguments) from the agent hook callback.

    Returns:
        None (no return value — callers check by absence of exception).

    Raises:
        DeniedToolCallError: If a denied payload is found and not allowlisted.

    # KS-TRACE: C-P2-03, AC-P2-04, AC-P2-08
    """
    for payload in DENY_PAYLOADS:
        idx = tool_input.find(payload)
        if idx == -1:
            continue
        if _match_is_allowlisted(tool_input, idx, idx + len(payload)):
            continue
        raise DeniedToolCallError(tool_name, payload)
