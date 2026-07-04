#!/usr/bin/env python3
"""
Unit Tests for Event Store Cryptographic Hash-Chaining.
"""

import json
import pytest
import shutil
import tempfile
from pathlib import Path
from medagentx.core.event_store import EventStore


@pytest.fixture
def temp_event_store():
    """Setup a temporary directory and clean event store for testing."""
    temp_dir = tempfile.mkdtemp()
    store = EventStore(store_path=temp_dir)
    yield store
    shutil.rmtree(temp_dir)


def test_valid_chain_verifies(temp_event_store):
    """
    Test that a sequence of appended events correctly links hashes,
    and verify_chain returns None (no errors).
    """
    store = temp_event_store

    eid1 = store.append_event(
        execution_id="exec_1",
        event_type="agent_output",
        source="agent",
        source_id="agent_1",
        data={"result": "diagnosis suggestion 1"}
    )

    eid2 = store.append_event(
        execution_id="exec_1",
        event_type="engine_output",
        source="engine",
        source_id="engine_1",
        data={"result": "recommendation 1"}
    )

    eid3 = store.append_event(
        execution_id="exec_2",
        event_type="agent_output",
        source="agent",
        source_id="agent_2",
        data={"result": "diagnosis suggestion 2"}
    )

    event1 = store.get_event(eid1)
    event2 = store.get_event(eid2)
    event3 = store.get_event(eid3)

    assert event1["previous_hash"] == "0" * 64
    assert event2["previous_hash"] == event1["hash"]
    assert event3["previous_hash"] == event2["hash"]

    assert store.verify_chain() is None


def test_tampering_detected(temp_event_store):
    """
    Test that modifying an event's data payload on disk breaks the chain validation.
    """
    store = temp_event_store

    eid1 = store.append_event("exec_1", "agent_output", "agent", "agent_1", {"val": 10})
    eid2 = store.append_event("exec_1", "engine_output", "engine", "engine_1", {"val": 20})
    eid3 = store.append_event("exec_1", "model_output", "model", "model_1", {"val": 30})

    assert store.verify_chain() is None

    # Tamper with eid2's data payload on disk
    file_path = Path(store.store_path) / f"{eid2}.json"
    with open(file_path, "r") as f:
        event = json.load(f)

    event["data"]["val"] = 99  # Tamper!

    with open(file_path, "w") as f:
        json.dump(event, f, indent=2)

    # Verification must detect the tampering and return eid2 as the broken link
    assert store.verify_chain() == eid2


def test_tampering_previous_hash_detected(temp_event_store):
    """
    Test that modifying the previous_hash link pointer breaks the chain validation.
    """
    store = temp_event_store

    eid1 = store.append_event("exec_1", "agent_output", "agent", "agent_1", {"val": 10})
    eid2 = store.append_event("exec_1", "engine_output", "engine", "engine_1", {"val": 20})

    assert store.verify_chain() is None

    file_path = Path(store.store_path) / f"{eid2}.json"
    with open(file_path, "r") as f:
        event = json.load(f)

    event["previous_hash"] = "invalid_hash"

    with open(file_path, "w") as f:
        json.dump(event, f, indent=2)

    assert store.verify_chain() == eid2
