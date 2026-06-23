# KS-TRACE: AC-04 | assumption: LANGFUSE_PUBLIC_KEY + LANGFUSE_SECRET_KEY in env | test: manual Langfuse UI check
# Note: raw OTel + SimpleSpanProcessor confirmed working with Langfuse cloud.
# Traces appear in Langfuse UI with ~5-10min delay on free tier. langfuse SDK not required.
from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Generator

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource

_provider: TracerProvider | None = None
_tracer: trace.Tracer | None = None


def setup_tracing(langfuse_host: str, enabled: bool) -> None:
    """
    Wire OTel → Langfuse via OTLP HTTP. SimpleSpanProcessor (synchronous) used for CLI:
    ensures spans are exported before process exits.
    Failures are non-fatal — tracing must never crash a scan.
    """
    global _provider, _tracer

    if not enabled:
        _tracer = trace.get_tracer("repomend.noop")
        return

    public_key = os.environ.get("LANGFUSE_PUBLIC_KEY", "")
    secret_key = os.environ.get("LANGFUSE_SECRET_KEY", "")

    if not public_key or not secret_key:
        import typer
        typer.echo(
            "[repomend] WARNING: LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY not set. "
            "Tracing disabled for this run.",
            err=True,
        )
        _tracer = trace.get_tracer("repomend.noop")
        return

    try:
        import base64
        credentials = base64.b64encode(f"{public_key}:{secret_key}".encode()).decode()
        endpoint = f"{langfuse_host.rstrip('/')}/api/public/otel/v1/traces"

        exporter = OTLPSpanExporter(
            endpoint=endpoint,
            headers={"Authorization": f"Basic {credentials}"},
        )

        _provider = TracerProvider(
            resource=Resource.create({"service.name": "repomend"}),
        )
        # SimpleSpanProcessor: synchronous export — correct for short-lived CLI processes.
        _provider.add_span_processor(SimpleSpanProcessor(exporter))
        trace.set_tracer_provider(_provider)
        _tracer = trace.get_tracer("repomend")

    except Exception as exc:
        import typer
        typer.echo(f"[repomend] WARNING: tracing setup failed (scan continues): {exc}", err=True)
        _tracer = trace.get_tracer("repomend.noop")


def flush() -> None:
    """Force-flush all pending spans before process exit."""
    global _provider
    if _provider is not None:
        try:
            _provider.force_flush(timeout_millis=5000)
        except Exception:
            pass


def get_tracer() -> trace.Tracer:
    global _tracer
    if _tracer is None:
        _tracer = trace.get_tracer("repomend.noop")
    return _tracer


@contextmanager
def span(name: str, **attributes: str | int) -> Generator[trace.Span, None, None]:
    """Context manager for a single OTel span. Safe even if tracing is not configured."""
    tracer = get_tracer()
    with tracer.start_as_current_span(name) as s:
        for k, v in attributes.items():
            s.set_attribute(k, v)
        yield s
