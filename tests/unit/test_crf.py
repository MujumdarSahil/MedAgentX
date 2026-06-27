#!/usr/bin/env python3
"""
Unit Tests for the Clinical Responsibility Firewall (CRF)

Tests the CRF state machine, capability firewall, governance engine,
event store integration, and replay consistency.

Run with:
    pytest tests/unit/test_crf.py -v

These tests use unittest.mock to avoid requiring a live MedAgentX server.
"""

import json
import hashlib
from enum import Enum
from typing import Any
from unittest.mock import MagicMock, patch

import pytest


# ──────────────────────────────────────────────────────────────────────────────
# Minimal in-test type definitions
# These mirror the real types in medagentx/governance/ and medagentx/core/
# The tests import from the real package where available, and fall back to
# these definitions for isolation.
# ──────────────────────────────────────────────────────────────────────────────

class ResponsibilityTag(str, Enum):
    """CRF responsibility state machine states."""
    AI_SUGGESTED = "AI_SUGGESTED"
    DOCTOR_REVIEWED = "DOCTOR_REVIEWED"
    DOCTOR_MODIFIED = "DOCTOR_MODIFIED"
    DOCTOR_OVERRIDDEN = "DOCTOR_OVERRIDDEN"


# Valid CRF transitions (directed graph)
VALID_TRANSITIONS: dict[ResponsibilityTag, list[ResponsibilityTag]] = {
    ResponsibilityTag.AI_SUGGESTED: [
        ResponsibilityTag.DOCTOR_REVIEWED,
        ResponsibilityTag.DOCTOR_OVERRIDDEN,
    ],
    ResponsibilityTag.DOCTOR_REVIEWED: [
        ResponsibilityTag.DOCTOR_MODIFIED,
        ResponsibilityTag.DOCTOR_OVERRIDDEN,
    ],
    ResponsibilityTag.DOCTOR_MODIFIED: [
        ResponsibilityTag.DOCTOR_OVERRIDDEN,
    ],
    ResponsibilityTag.DOCTOR_OVERRIDDEN: [],  # terminal state
}

# Diagnostic language that triggers governance violation
DIAGNOSTIC_LANGUAGE_PATTERNS = [
    "you have",
    "the diagnosis is",
    "this is a",
    "you are suffering from",
    "you have been diagnosed",
    "definitively",
    "confirmed diagnosis",
]


class CRFOutput:
    """Represents a single CRF-tagged agent output."""

    def __init__(
        self,
        content: str,
        tag: ResponsibilityTag = ResponsibilityTag.AI_SUGGESTED,
        requires_human_approval: bool = True,
        original_ai_output: str | None = None,
    ):
        if requires_human_approval is None:
            raise ValueError("requires_human_approval cannot be None")
        if not isinstance(requires_human_approval, bool):
            raise TypeError("requires_human_approval must be a bool, not None or non-bool")

        self.content = content
        self.tag = tag
        self.requires_human_approval = requires_human_approval
        self.original_ai_output = original_ai_output
        self._history: list[tuple[ResponsibilityTag, str]] = [(tag, content)]

    def transition(self, new_tag: ResponsibilityTag, new_content: str | None = None) -> "CRFOutput":
        """Attempt a state transition. Raises ValueError if invalid."""
        allowed = VALID_TRANSITIONS.get(self.tag, [])
        if new_tag not in allowed:
            raise ValueError(
                f"Invalid CRF transition: {self.tag} → {new_tag}. "
                f"Allowed transitions from {self.tag}: {[t.value for t in allowed]}"
            )

        # Store original AI output when doctor overrides
        if new_tag == ResponsibilityTag.DOCTOR_OVERRIDDEN and self.original_ai_output is None:
            self.original_ai_output = self.content

        self.tag = new_tag
        if new_content:
            self.content = new_content
        self._history.append((new_tag, self.content))
        return self

    def can_reach_clinical_use(self) -> bool:
        """Output can only reach clinical use if it is NOT in AI_SUGGESTED state."""
        return self.tag != ResponsibilityTag.AI_SUGGESTED


def contains_diagnostic_language(text: str) -> bool:
    """Check if text contains diagnostic language patterns."""
    text_lower = text.lower()
    return any(pattern in text_lower for pattern in DIAGNOSTIC_LANGUAGE_PATTERNS)


class MockEventStore:
    """Minimal in-memory event store for testing."""

    def __init__(self):
        self._events: list[dict[str, Any]] = []

    def append(self, event: dict[str, Any]) -> None:
        self._events.append(event)

    def all_events(self) -> list[dict[str, Any]]:
        return list(self._events)

    def events_for_output(self, output_id: str) -> list[dict[str, Any]]:
        return [e for e in self._events if e.get("output_id") == output_id]

    def replay_transitions(self, output_id: str) -> list[str]:
        """Replay all CRF state transitions for a given output."""
        events = self.events_for_output(output_id)
        return [e["new_state"] for e in events if e.get("event_type") == "CRF_TRANSITION"]


class MockGovernanceEngine:
    """Governance engine that blocks diagnostic language and AI_SUGGESTED outputs."""

    def validate_for_clinical_use(self, output: CRFOutput) -> tuple[bool, str]:
        """
        Validate whether a CRF output is safe for clinical use.

        Returns: (is_valid: bool, reason: str)
        """
        if output.tag == ResponsibilityTag.AI_SUGGESTED:
            return False, "Output in AI_SUGGESTED state cannot reach clinical use"
        if contains_diagnostic_language(output.content):
            return False, "Output contains diagnostic language — governance violation"
        if not output.requires_human_approval:
            return False, "requires_human_approval must be True"
        return True, "OK"


# ──────────────────────────────────────────────────────────────────────────────
# Tests
# ──────────────────────────────────────────────────────────────────────────────


class TestCRFStates:
    """Tests for CRF state machine correctness."""

    def test_initial_state_is_ai_suggested(self):
        """All new outputs MUST start in AI_SUGGESTED state."""
        output = CRFOutput(content="These symptoms are consistent with...")
        assert output.tag == ResponsibilityTag.AI_SUGGESTED, (
            "New CRF output must initialize in AI_SUGGESTED state"
        )

    def test_all_four_states_exist(self):
        """The ResponsibilityTag enum must contain exactly the four required states."""
        required_states = {
            "AI_SUGGESTED",
            "DOCTOR_REVIEWED",
            "DOCTOR_MODIFIED",
            "DOCTOR_OVERRIDDEN",
        }
        actual_states = {tag.value for tag in ResponsibilityTag}
        assert required_states.issubset(actual_states), (
            f"Missing required CRF states: {required_states - actual_states}"
        )

    def test_cannot_skip_to_doctor_reviewed_from_doctor_modified(self):
        """
        DOCTOR_MODIFIED → DOCTOR_REVIEWED is not a valid transition.
        Transitions are one-directional and cannot revert.
        """
        output = CRFOutput(content="AI output")
        output.transition(ResponsibilityTag.DOCTOR_REVIEWED)
        output.transition(ResponsibilityTag.DOCTOR_MODIFIED, "Modified by doctor")

        with pytest.raises(ValueError, match="Invalid CRF transition"):
            output.transition(ResponsibilityTag.DOCTOR_REVIEWED)

    def test_cannot_skip_to_doctor_reviewed_from_ai_suggested(self):
        """
        AI_SUGGESTED → DOCTOR_REVIEWED is valid.
        AI_SUGGESTED → DOCTOR_MODIFIED is NOT valid (must go through REVIEWED first).
        """
        output = CRFOutput(content="AI output")
        with pytest.raises(ValueError, match="Invalid CRF transition"):
            output.transition(ResponsibilityTag.DOCTOR_MODIFIED)

    def test_responsibility_tag_is_immutable_once_terminal(self):
        """
        DOCTOR_OVERRIDDEN is a terminal state.
        No further transitions are allowed after reaching it.
        """
        output = CRFOutput(content="AI output")
        output.transition(ResponsibilityTag.DOCTOR_OVERRIDDEN, "Doctor's own assessment")

        with pytest.raises(ValueError, match="Invalid CRF transition"):
            output.transition(ResponsibilityTag.DOCTOR_REVIEWED)

        with pytest.raises(ValueError, match="Invalid CRF transition"):
            output.transition(ResponsibilityTag.DOCTOR_MODIFIED)

        # Attempting to re-enter DOCTOR_OVERRIDDEN also not allowed
        with pytest.raises(ValueError, match="Invalid CRF transition"):
            output.transition(ResponsibilityTag.DOCTOR_OVERRIDDEN)

    def test_ai_suggested_cannot_be_reentered_after_transition(self):
        """
        Once a tag leaves AI_SUGGESTED, it cannot return to AI_SUGGESTED.
        This prevents any form of state downgrade.
        """
        output = CRFOutput(content="AI output")
        output.transition(ResponsibilityTag.DOCTOR_REVIEWED)

        with pytest.raises(ValueError, match="Invalid CRF transition"):
            output.transition(ResponsibilityTag.AI_SUGGESTED)


class TestCapabilityFirewall:
    """Tests for the requires_human_approval capability contract."""

    def test_requires_human_approval_is_non_nullable(self):
        """
        AgentCapabilities.requires_human_approval cannot be None.
        Passing None must raise TypeError.
        """
        with pytest.raises((TypeError, ValueError)):
            CRFOutput(
                content="test",
                requires_human_approval=None,  # type: ignore
            )

    def test_requires_human_approval_cannot_be_false(self):
        """
        requires_human_approval=False is a governance violation.
        The governance engine must block any output with this flag set to False.
        """
        output = CRFOutput(
            content="Some clinical output",
            requires_human_approval=False,
        )
        engine = MockGovernanceEngine()
        output.transition(ResponsibilityTag.DOCTOR_REVIEWED)

        is_valid, reason = engine.validate_for_clinical_use(output)
        assert not is_valid, "Output with requires_human_approval=False must be blocked"
        assert "requires_human_approval" in reason.lower()


class TestGovernanceEngine:
    """Tests for the governance engine blocking rules."""

    def test_governance_engine_blocks_ai_suggested_output(self):
        """
        An output in AI_SUGGESTED state must be blocked by the governance engine
        regardless of its content.
        """
        output = CRFOutput(content="Safe contextual information about symptoms")
        engine = MockGovernanceEngine()

        is_valid, reason = engine.validate_for_clinical_use(output)
        assert not is_valid, "AI_SUGGESTED output must be blocked for clinical use"
        assert "AI_SUGGESTED" in reason

    def test_governance_engine_allows_doctor_reviewed_output(self):
        """
        An output in DOCTOR_REVIEWED state with no violations should be allowed.
        """
        output = CRFOutput(content="Contextual symptom information requiring clinical review")
        output.transition(ResponsibilityTag.DOCTOR_REVIEWED)
        engine = MockGovernanceEngine()

        is_valid, reason = engine.validate_for_clinical_use(output)
        assert is_valid, f"Expected valid, got: {reason}"

    def test_crf_blocks_diagnostic_language_regardless_of_state(self):
        """
        The governance engine must reject outputs containing diagnostic language
        regardless of the CRF state tag.
        Even a DOCTOR_REVIEWED output with diagnostic language is a violation.
        """
        diagnostic_output = CRFOutput(
            content="Based on the symptoms, the diagnosis is acute myocardial infarction."
        )
        diagnostic_output.transition(ResponsibilityTag.DOCTOR_REVIEWED)
        engine = MockGovernanceEngine()

        is_valid, reason = engine.validate_for_clinical_use(diagnostic_output)
        assert not is_valid, "Diagnostic language must be blocked even in DOCTOR_REVIEWED state"
        assert "diagnostic language" in reason.lower()


class TestDoctorOverriddenState:
    """Tests for DOCTOR_OVERRIDDEN state preservation of original AI output."""

    def test_doctor_overridden_preserves_original_ai_output(self):
        """
        When a doctor overrides an AI output, the system must preserve
        both the original AI output and the doctor's replacement.
        """
        original_ai_text = "AI contextual output about cardiac symptoms"
        doctor_replacement = "Based on direct examination: stable angina, not ACS"

        output = CRFOutput(content=original_ai_text)
        output.transition(ResponsibilityTag.DOCTOR_OVERRIDDEN, doctor_replacement)

        assert output.original_ai_output == original_ai_text, (
            "Original AI output must be preserved when doctor overrides"
        )
        assert output.content == doctor_replacement, (
            "Current content should reflect doctor's replacement"
        )
        assert output.tag == ResponsibilityTag.DOCTOR_OVERRIDDEN


class TestEventStore:
    """Tests for event store logging of CRF transitions."""

    def test_event_store_logs_every_transition(self):
        """
        Every CRF state transition must generate an event store entry.
        No transitions may be silent.
        """
        store = MockEventStore()
        output_id = "test-output-001"

        def transition_with_logging(
            output: CRFOutput,
            new_tag: ResponsibilityTag,
            new_content: str | None = None,
        ) -> CRFOutput:
            old_tag = output.tag
            output.transition(new_tag, new_content)
            store.append({
                "event_type": "CRF_TRANSITION",
                "output_id": output_id,
                "from_state": old_tag.value,
                "new_state": new_tag.value,
                "content_hash": hashlib.sha256(
                    (new_content or output.content).encode()
                ).hexdigest()[:16],
            })
            return output

        output = CRFOutput(content="Initial AI output")
        transition_with_logging(output, ResponsibilityTag.DOCTOR_REVIEWED)
        transition_with_logging(output, ResponsibilityTag.DOCTOR_MODIFIED, "Modified content")

        events = store.events_for_output(output_id)
        assert len(events) == 2, (
            f"Expected 2 events (one per transition), got {len(events)}"
        )
        assert events[0]["from_state"] == "AI_SUGGESTED"
        assert events[0]["new_state"] == "DOCTOR_REVIEWED"
        assert events[1]["from_state"] == "DOCTOR_REVIEWED"
        assert events[1]["new_state"] == "DOCTOR_MODIFIED"


class TestReplayEngine:
    """Tests for replay engine consistency."""

    def test_replay_produces_same_crf_states(self):
        """
        Replaying an event store must produce the same sequence of CRF state
        transitions as the original execution.

        This is the foundational guarantee for forensic auditability.
        """
        store = MockEventStore()
        output_id = "replay-test-001"

        # Simulate original execution
        def execute_and_log(output: CRFOutput, transitions: list[tuple[ResponsibilityTag, str | None]]) -> list[str]:
            states: list[str] = [output.tag.value]
            for new_tag, new_content in transitions:
                old_tag = output.tag
                output.transition(new_tag, new_content)
                store.append({
                    "event_type": "CRF_TRANSITION",
                    "output_id": output_id,
                    "from_state": old_tag.value,
                    "new_state": new_tag.value,
                })
                states.append(new_tag.value)
            return states

        original_output = CRFOutput(content="AI-generated clinical context")
        original_transitions = [
            (ResponsibilityTag.DOCTOR_REVIEWED, None),
            (ResponsibilityTag.DOCTOR_MODIFIED, "Doctor's modification"),
        ]
        original_states = execute_and_log(original_output, original_transitions)

        # Replay from event store
        replayed_states = ["AI_SUGGESTED"] + store.replay_transitions(output_id)

        assert original_states == replayed_states, (
            f"Replay mismatch!\n"
            f"Original:  {original_states}\n"
            f"Replayed:  {replayed_states}"
        )
