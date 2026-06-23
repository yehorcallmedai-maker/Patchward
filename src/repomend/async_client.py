# KS-TRACE: C-P6-01, ADR-020 | injectable factory for AsyncAnthropic
# assumption: callers inject via get_async_client() — never import
# AsyncAnthropic directly in pipeline code
# test: test_async_pipeline.py
from __future__ import annotations

from anthropic import AsyncAnthropic


def get_async_client(api_key: str) -> AsyncAnthropic:
    """
    Return a configured ``AsyncAnthropic`` client.

    Thin factory wrapper — exists so tests can monkeypatch
    ``repomend.async_client.get_async_client`` without touching
    the Anthropic SDK directly.

    # KS-TRACE: C-P6-01, ADR-020
    """
    return AsyncAnthropic(api_key=api_key)
