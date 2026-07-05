"""
Event Store + Audit Logging for MedAgentX v2.0

Append-only event store for deterministic replay.
All events are immutable and structured as JSON.
"""

import json
import os
from typing import Any, Dict, List, Optional
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class EventStore:
    """
    Append-only event store.
    
    Stores every execution step as structured JSON.
    Supports deterministic replay from stored events.
    No overwrites allowed.
    """
    
    def __init__(self, store_path: Optional[str] = None):
        """
        Initialize event store.
        
        Args:
            store_path: Path to event store directory (default: ./event_store)
        """
        self.store_path = Path(store_path or "./event_store")
        self.store_path.mkdir(parents=True, exist_ok=True)
        
        # In-memory index for fast lookup
        self._event_index: Dict[str, List[str]] = {}  # execution_id -> [event_ids]
        self._global_chain: List[str] = []  # List of all event IDs in sequential order
        self._load_index()
    def append_event(
        self,
        execution_id: str,
        event_type: str,  # "agent_output", "engine_output", "model_output", "workflow_step", "squad_step"
        source: str,  # "agent", "engine", "model", "workflow", "squad"
        source_id: str,
        data: Dict[str, Any],
        responsibility_metadata: Optional[Dict[str, Any]] = None,
        confidence: Optional[float] = None,
        evidence: Optional[List[str]] = None,
    ) -> str:
        """
        Append an event to the store.
        
        Args:
            execution_id: Execution/workflow ID
            event_type: Type of event
            source: Source type
            source_id: Source identifier
            data: Event data
            responsibility_metadata: Responsibility metadata
            confidence: Confidence score
            evidence: Supporting evidence
            
        Returns:
            Event ID
        """
        import hashlib
        
        # Generate event ID
        event_id = f"{execution_id}_{event_type}_{source_id}_{datetime.now().isoformat()}"
        event_id = event_id.replace(":", "-").replace(".", "-")
        
        # Determine previous event hash
        previous_hash = "0" * 64
        if self._global_chain:
            last_event_id = self._global_chain[-1]
            last_event = self.get_event(last_event_id)
            if last_event and "hash" in last_event:
                previous_hash = last_event["hash"]
        
        # Create event structure
        event = {
            "event_id": event_id,
            "execution_id": execution_id,
            "event_type": event_type,
            "source": source,
            "source_id": source_id,
            "timestamp": datetime.now().isoformat(),
            "data": data,
            "responsibility_metadata": responsibility_metadata or {},
            "confidence": confidence,
            "evidence": evidence or [],
            "previous_hash": previous_hash,
        }
        
        # Compute cryptographic hash (excluding "hash" key)
        canonical = json.dumps(event, sort_keys=True, separators=(',', ':'))
        event["hash"] = hashlib.sha256((previous_hash + canonical).encode('utf-8')).hexdigest()
        
        # Write to file (append-only)
        event_file = self.store_path / f"{event_id}.json"
        with open(event_file, "w") as f:
            json.dump(event, f, indent=2)
        
        # Update indices
        if execution_id not in self._event_index:
            self._event_index[execution_id] = []
        self._event_index[execution_id].append(event_id)
        self._global_chain.append(event_id)
        self._save_index()
        
        logger.debug(f"Appended event {event_id} to execution {execution_id}")
        
        return event_id
    def get_events(
        self,
        execution_id: str,
        event_type: Optional[str] = None,
        source: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get events for an execution.
        
        Args:
            execution_id: Execution ID
            event_type: Optional filter by event type
            source: Optional filter by source
            
        Returns:
            List of events
        """
        if execution_id not in self._event_index:
            return []
        
        events = []
        for event_id in self._event_index[execution_id]:
            event_file = self.store_path / f"{event_id}.json"
            if event_file.exists():
                try:
                    with open(event_file, "r") as f:
                        event = json.load(f)
                    
                    # Apply filters
                    if event_type and event.get("event_type") != event_type:
                        continue
                    if source and event.get("source") != source:
                        continue
                    
                    events.append(event)
                except Exception as e:
                    logger.error(f"Error loading event {event_id}: {e}")
        
        # Sort by timestamp
        events.sort(key=lambda x: x.get("timestamp", ""))
        
        return events
    
    def get_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific event by ID.
        
        Args:
            event_id: Event ID
            
        Returns:
            Event dictionary or None
        """
        event_file = self.store_path / f"{event_id}.json"
        if not event_file.exists():
            return None
        
        try:
            with open(event_file, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading event {event_id}: {e}")
            return None
    
    def list_executions(self) -> List[str]:
        """
        List all execution IDs.
        
        Returns:
            List of execution IDs
        """
        return list(self._event_index.keys())
    
    def export_execution(
        self,
        execution_id: str,
        output_path: Optional[str] = None,
    ) -> str:
        """
        Export all events for an execution to a single JSON file.
        
        Args:
            execution_id: Execution ID
            output_path: Output file path (default: ./exports/{execution_id}.json)
            
        Returns:
            Path to exported file
        """
        events = self.get_events(execution_id)
        
        if not events:
            raise ValueError(f"No events found for execution {execution_id}")
        
        export_data = {
            "execution_id": execution_id,
            "export_timestamp": datetime.now().isoformat(),
            "event_count": len(events),
            "events": events,
        }
        
        if output_path is None:
            export_dir = self.store_path / "exports"
            export_dir.mkdir(exist_ok=True)
            output_path = str(export_dir / f"{execution_id}.json")
        
        with open(output_path, "w") as f:
            json.dump(export_data, f, indent=2)
        
        logger.info(f"Exported {len(events)} events for execution {execution_id} to {output_path}")
        
        return output_path
    
    def verify_chain(self, limit: Optional[int] = None) -> Optional[str]:
        """
        Verify the integrity of the event chain.
        
        Walks the event store using the global chain index, recomputes hashes,
        and returns the first broken link event_id, if any.
        Returns None if the chain is fully valid.
        
        Args:
            limit: If set, only verify the last N events in the chain.
        """
        import hashlib
        
        if not self._global_chain:
            return None
            
        start_idx = 0
        expected_previous_hash = "0" * 64
        
        if limit is not None and len(self._global_chain) > limit:
            start_idx = len(self._global_chain) - limit
            # Fetch preceding event's hash to initialize expected_previous_hash
            prev_event_id = self._global_chain[start_idx - 1]
            prev_event_file = self.store_path / f"{prev_event_id}.json"
            if prev_event_file.exists():
                try:
                    with open(prev_event_file, "r") as f:
                        prev_event = json.load(f)
                        expected_previous_hash = prev_event.get("hash", "0" * 64)
                except Exception as e:
                    logger.error(f"Failed to load preceding event {prev_event_id} for verification: {e}")
                    return prev_event_id
            else:
                logger.error(f"Preceding event file {prev_event_id}.json missing from chain")
                return prev_event_id
        
        for i in range(start_idx, len(self._global_chain)):
            event_id = self._global_chain[i]
            event_file = self.store_path / f"{event_id}.json"
            if not event_file.exists():
                logger.error(f"Event file {event_id}.json missing from chain")
                return event_id
            
            try:
                with open(event_file, "r") as f:
                    event = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load event {event_id}: {e}")
                return event_id
            
            # Check previous hash link
            prev_hash_in_record = event.get("previous_hash")
            if prev_hash_in_record != expected_previous_hash:
                logger.error(f"Event {event_id} broken link: expected previous hash {expected_previous_hash}, got {prev_hash_in_record}")
                return event_id
                
            # Verify stored hash matches computed hash
            stored_hash = event.get("hash")
            if not stored_hash:
                logger.error(f"Event {event_id} has no hash stored")
                return event_id
                
            # Compute expected hash
            event_copy = {k: v for k, v in event.items() if k != "hash"}
            canonical = json.dumps(event_copy, sort_keys=True, separators=(',', ':'))
            computed_hash = hashlib.sha256((prev_hash_in_record + canonical).encode('utf-8')).hexdigest()
            
            if stored_hash != computed_hash:
                logger.error(f"Event {event_id} hash mismatch: stored {stored_hash}, computed {computed_hash}")
                return event_id
                
            expected_previous_hash = stored_hash
            
        return None

    def _load_index(self) -> None:
        """Load event index and global chain from disk."""
        index_file = self.store_path / ".index.json"
        if index_file.exists():
            try:
                with open(index_file, "r") as f:
                    data = json.load(f)
                if isinstance(data, dict) and "event_index" in data and "global_chain" in data:
                    self._event_index = data["event_index"]
                    self._global_chain = data["global_chain"]
                else:
                    # Migration: if .index.json is in old format, index maps execution_id -> event_ids
                    self._event_index = data
                    # Reconstruct global chain by sorting all events by timestamp
                    all_event_ids = []
                    for v in self._event_index.values():
                        all_event_ids.extend(v)
                    
                    event_timestamps = []
                    for eid in all_event_ids:
                        evt = self.get_event(eid)
                        if evt:
                            event_timestamps.append((evt.get("timestamp", ""), eid))
                    event_timestamps.sort()
                    self._global_chain = [eid for _, eid in event_timestamps]
            except Exception as e:
                logger.warning(f"Error loading index: {e}")
                self._event_index = {}
                self._global_chain = []
        else:
            self._event_index = {}
            self._global_chain = []
    
    def _save_index(self) -> None:
        """Save event index and global chain to disk."""
        index_file = self.store_path / ".index.json"
        try:
            with open(index_file, "w") as f:
                json.dump({
                    "event_index": self._event_index,
                    "global_chain": self._global_chain,
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving index: {e}")

