#!/usr/bin/env python3
"""
Unit Tests for OpenTelemetry Tracing.
"""

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
import pytest
import asyncio

import hashlib

from medagentx.core.agent import BaseAgent
from medagentx.core.types import AgentConfig
from medagentx.core.telemetry import tracer


@pytest.fixture(scope="module")
def memory_exporter():
    """Setup InMemorySpanExporter on the global TracerProvider."""
    provider = trace.get_tracer_provider()
    exporter = InMemorySpanExporter()
    processor = SimpleSpanProcessor(exporter)
    provider.add_span_processor(processor)
    return exporter


@pytest.mark.asyncio
async def test_agent_run_traces(memory_exporter):
    """
    Test that running an agent creates a trace span with expected attributes.
    """
    config = AgentConfig(
        agent_id="telemetry_test_agent",
        agent_name="Telemetry Agent",
        description="A telemetry testing agent",
        created_by="test"
    )

    async def dummy_plan(task, context=None):
        return {"steps": [], "reasoning": "Plan telemetry check"}

    async def dummy_act(plan, context=None):
        return {"output": {"status": "success"}, "confidence": 0.8}

    async def dummy_reflect(action_result):
        return {"reflection": "Telemetry test passed", "requires_human_approval": True}

    agent = BaseAgent(config=config)
    agent.plan = dummy_plan
    agent.act = dummy_act
    agent.reflect = dummy_reflect

    # Clear previous spans
    memory_exporter.clear()

    # Run agent
    await agent.run("Test telemetry task")

    # Get finished spans
    spans = memory_exporter.get_finished_spans()

    # Find the agent run span
    agent_spans = [s for s in spans if s.name == "agent_telemetry_test_agent_run"]
    assert len(agent_spans) == 1

    span = agent_spans[0]
    assert span.attributes["agent_id"] == "telemetry_test_agent"
    # Raw task text is never stored (PII-safe). Verify the hash matches.
    expected_hash = hashlib.sha256(b"Test telemetry task").hexdigest()[:16]
    assert span.attributes["task_hash"] == expected_hash
    assert span.attributes["agent.type"] == "BaseAgent"
    assert span.attributes["confidence"] == 0.8
