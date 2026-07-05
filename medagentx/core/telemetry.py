"""
MedAgentX Telemetry Module
===========================
Initialises the OpenTelemetry TracerProvider and optionally wires a
self-hosted Langfuse v3 instance as an OTel exporter.

Environment variables (all optional — module degrades gracefully):
    LANGFUSE_PUBLIC_KEY   : Langfuse project public key
    LANGFUSE_SECRET_KEY   : Langfuse project secret key
    LANGFUSE_HOST         : Langfuse server URL  (default: http://localhost:3000)

PII masking
-----------
A ``PiiMaskingSpanProcessor`` sits in front of the Langfuse exporter and
replaces the values of any span attribute whose key matches a known-PII
pattern with the literal string ``[REDACTED]``.  Keys scrubbed:
    patient_id, mrn, dob, ssn, nhs_number, email, phone,
    and any key containing the substring ``pii_``.
"""

from __future__ import annotations

import hashlib
import logging
import os
import re
from typing import Any, Sequence

from opentelemetry import trace
from opentelemetry.sdk.trace import ReadableSpan, SpanProcessor, TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    SimpleSpanProcessor,
    ConsoleSpanExporter,
    SpanExporter,
    SpanExportResult,
)

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# PII attribute keys to redact before export
# ─────────────────────────────────────────────────────────────────────────────
_PII_EXACT_KEYS: frozenset[str] = frozenset(
    {
        "patient_id",
        "mrn",
        "medical_record_number",
        "dob",
        "date_of_birth",
        "ssn",
        "social_security_number",
        "nhs_number",
        "email",
        "phone",
        "phone_number",
        "address",
        "full_name",
        "first_name",
        "last_name",
        "date_of_birth",
    }
)

_PII_SUBSTRING_PATTERNS: tuple[str, ...] = ("pii_", "_pii", "patient_", "_ssn", "_mrn")


def _is_pii_key(key: str) -> bool:
    """Return True if the attribute key is considered PII-sensitive."""
    lk = key.lower()
    if lk in _PII_EXACT_KEYS:
        return True
    return any(pat in lk for pat in _PII_SUBSTRING_PATTERNS)


# ─────────────────────────────────────────────────────────────────────────────
# PiiMaskingSpanProcessor
# ─────────────────────────────────────────────────────────────────────────────

class PiiMaskingSpanProcessor(SpanProcessor):
    """
    Wraps a downstream SpanExporter and scrubs PII attribute values before
    forwarding the span for export.

    Only span *attributes* are masked.  Span names and events are left
    untouched because they should never contain raw patient data by
    convention (use hashed task identifiers instead).
    """

    def __init__(self, exporter: SpanExporter) -> None:
        self._inner = BatchSpanProcessor(exporter)

    # Delegate lifecycle methods
    def on_start(self, span: Any, parent_context: Any = None) -> None:
        self._inner.on_start(span, parent_context)

    def on_end(self, span: ReadableSpan) -> None:
        # Build a sanitised copy of the attributes mapping
        if span.attributes:
            sanitised: dict[str, Any] = {}
            for k, v in span.attributes.items():
                sanitised[k] = "[REDACTED]" if _is_pii_key(k) else v
            # Attributes on ReadableSpan are immutable; patch via the
            # underlying MutableSpan only when running under the SDK.
            try:
                # noinspection PyProtectedMember
                object.__setattr__(span, "_attributes", sanitised)
            except Exception:
                pass  # If patching fails, forward as-is; log nothing (avoid log-amplification)
        self._inner.on_end(span)

    def shutdown(self) -> None:
        self._inner.shutdown()

    def force_flush(self, timeout_millis: int = 30_000) -> bool:
        return self._inner.force_flush(timeout_millis)


# ─────────────────────────────────────────────────────────────────────────────
# TracerProvider initialisation
# ─────────────────────────────────────────────────────────────────────────────

_langfuse_enabled: bool = False


def _init_provider() -> TracerProvider:
    """
    Build and register the global OTel TracerProvider.

    Always attaches a ConsoleSpanExporter (SimpleSpanProcessor) for local
    debugging.  Conditionally attaches a PiiMaskingSpanProcessor →
    LangfuseSpanExporter when all three Langfuse env vars are present.
    """
    global _langfuse_enabled
    provider = TracerProvider()

    # Console exporter — always on; safe for local dev
    provider.add_span_processor(
        SimpleSpanProcessor(ConsoleSpanExporter())
    )

    # Langfuse exporter — conditional on env vars
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY", "").strip()
    secret_key = os.getenv("LANGFUSE_SECRET_KEY", "").strip()
    host = os.getenv("LANGFUSE_HOST", "http://localhost:3000").strip()

    if public_key and secret_key:
        try:
            from langfuse.opentelemetry import LangfuseSpanExporter  # type: ignore

            lf_exporter = LangfuseSpanExporter(
                public_key=public_key,
                secret_key=secret_key,
                host=host,
            )
            # Wrap with PII masking before attaching
            provider.add_span_processor(PiiMaskingSpanProcessor(lf_exporter))
            _langfuse_enabled = True
            logger.info(
                "Langfuse OTel exporter initialised (host=%s, project_key=%s...)",
                host,
                public_key[:8],
            )
        except ImportError:
            logger.warning(
                "langfuse package not installed — Langfuse exporter disabled. "
                "Install with: pip install langfuse>=3.0.0"
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to initialise Langfuse exporter: %s", exc)
    else:
        logger.info(
            "LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY not set — "
            "Langfuse exporter disabled (console-only tracing active)."
        )

    return provider


try:
    if not isinstance(trace.get_tracer_provider(), TracerProvider):
        _provider = _init_provider()
        trace.set_tracer_provider(_provider)
    else:
        # Provider already initialised (e.g. in tests) — reuse it
        logger.debug("OTel TracerProvider already configured; skipping re-init.")
except Exception as _init_exc:  # noqa: BLE001
    logger.warning("Failed to initialise OTel TracerProvider: %s", _init_exc)

tracer = trace.get_tracer("medagentx")


# ─────────────────────────────────────────────────────────────────────────────
# Convenience helpers for structured governance / audit events
# ─────────────────────────────────────────────────────────────────────────────

def _task_hash(task: str) -> str:
    """Return a short, non-reversible identifier for a task string (PII-safe)."""
    return hashlib.sha256(task.encode()).hexdigest()[:16]


def record_governance_event(
    name: str,
    attributes: dict[str, Any] | None = None,
) -> None:
    """
    Emit a governance-tagged span for dashboard filtering.

    All governance events carry the ``governance=True`` boolean attribute so
    operators can build Langfuse dashboards filtered exclusively on
    governance activity.
    """
    attrs: dict[str, Any] = {"governance": True}
    if attributes:
        attrs.update(attributes)
    with tracer.start_as_current_span(f"governance.{name}") as span:
        for k, v in attrs.items():
            try:
                span.set_attribute(k, v)
            except Exception:  # noqa: BLE001
                pass  # OTel only accepts primitive attribute values


def record_crf_event(
    tag: str,
    agent_id: str,
    forged: bool = False,
) -> None:
    """
    Emit a Clinical Responsibility Firewall event span.

    Args:
        tag      : The ``ResponsibilityTag`` value assigned (e.g. ``ai_suggested``).
        agent_id : The source agent identifier.
        forged   : True when the CRF detected and rejected a forged tag.
    """
    record_governance_event(
        "crf_enforcement",
        {
            "crf.tag": tag,
            "crf.agent_id": agent_id,
            "crf.forged_tag_rejected": forged,
        },
    )


def record_eval_event(
    scenario_id: str,
    violation_type: str,
    latency_ms: int,
    violation_detected: bool = False,
) -> None:
    """
    Emit an evaluation-run event span for the governance test runner.
    """
    record_governance_event(
        "eval_scenario",
        {
            "eval.scenario_id": scenario_id,
            "eval.violation_type": violation_type,
            "eval.violation_detected": violation_detected,
            "eval.latency_ms": latency_ms,
        },
    )
