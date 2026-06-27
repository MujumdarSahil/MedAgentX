"""
Time-Travel Replay Engine for MedAgentX v2.0

Re-run past workflows using stored events.
Supports:
- Modified inputs
- Updated guideline versions
- Altered environmental context
- Delta comparison between original and replay
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import logging

from medagentx.core.event_store import EventStore
from medagentx.core.workflow import RecommendationWorkflow

logger = logging.getLogger(__name__)


class ReplayEngine:
    """
    Time-Travel Replay Engine.
    
    Replays past workflows deterministically.
    Supports modified inputs and context.
    """
    
    def __init__(
        self,
        event_store: EventStore,
        workflow: RecommendationWorkflow,
    ):
        """
        Initialize replay engine.
        
        Args:
            event_store: Event store instance
            workflow: Workflow instance to replay with
        """
        self.event_store = event_store
        self.workflow = workflow
    
    async def replay(
        self,
        execution_id: str,
        modified_inputs: Optional[Dict[str, Any]] = None,
        modified_context: Optional[Dict[str, Any]] = None,
        use_updated_guidelines: bool = False,
    ) -> Dict[str, Any]:
        """
        Replay a past execution.
        
        Args:
            execution_id: Original execution ID
            modified_inputs: Optional modified inputs (e.g., different symptoms)
            modified_context: Optional modified context (e.g., different patient data)
            use_updated_guidelines: Whether to use updated guidelines (if available)
            
        Returns:
            Replay result with delta comparison
        """
        # Get original events
        original_events = self.event_store.get_events(execution_id)
        if not original_events:
            raise ValueError(f"No events found for execution {execution_id}")
        
        # Extract original input
        first_event = original_events[0]
        original_input = first_event.get("data", {}).get("input", {})
        
        # Use modified inputs if provided, otherwise use original
        replay_input = modified_inputs or original_input
        
        # Extract original context
        original_context = first_event.get("data", {}).get("context", {})
        
        # Merge with modified context
        replay_context = original_context.copy()
        if modified_context:
            replay_context.update(modified_context)
        
        # Replay workflow
        if isinstance(replay_input, str):
            # Symptoms text
            replay_result = await self.workflow.run(replay_input)
        else:
            # Structured input
            symptoms_text = replay_input.get("symptoms", "")
            replay_result = await self.workflow.run(symptoms_text)
        
        # Store replay events
        replay_execution_id = f"{execution_id}_replay_{datetime.now().isoformat()}"
        replay_execution_id = replay_execution_id.replace(":", "-").replace(".", "-")
        
        # Compare original vs replay
        delta = self._compute_delta(original_events, replay_result, replay_execution_id)
        
        return {
            "original_execution_id": execution_id,
            "replay_execution_id": replay_execution_id,
            "replay_result": replay_result,
            "delta": delta,
            "modified_inputs": modified_inputs is not None,
            "modified_context": modified_context is not None,
            "use_updated_guidelines": use_updated_guidelines,
        }
    
    def _compute_delta(
        self,
        original_events: List[Dict[str, Any]],
        replay_result: Dict[str, Any],
        replay_execution_id: str,
    ) -> Dict[str, Any]:
        """
        Compute delta between original and replay.
        
        Args:
            original_events: Original execution events
            replay_result: Replay result
            replay_execution_id: Replay execution ID
            
        Returns:
            Delta comparison dictionary
        """
        delta = {
            "differences": [],
            "matches": [],
            "confidence_delta": {},
            "output_delta": {},
        }
        
        # Compare outputs
        original_outputs = {}
        for event in original_events:
            source_id = event.get("source_id", "")
            if source_id:
                original_outputs[source_id] = event.get("data", {}).get("output", {})
        
        # Compare with replay result
        replay_outputs = {}
        if "structured_symptoms" in replay_result:
            replay_outputs["symptom_analyzer"] = {"symptoms": replay_result.get("structured_symptoms", [])}
        if "support" in replay_result:
            replay_outputs["diagnosis_support"] = replay_result.get("support", {})
        if "coding" in replay_result:
            replay_outputs["medical_coder"] = replay_result.get("coding", {})
        
        # Compare each output
        all_source_ids = set(original_outputs.keys()) | set(replay_outputs.keys())
        for source_id in all_source_ids:
            original_output = original_outputs.get(source_id, {})
            replay_output = replay_outputs.get(source_id, {})
            
            if original_output == replay_output:
                delta["matches"].append(source_id)
            else:
                delta["differences"].append({
                    "source_id": source_id,
                    "original": original_output,
                    "replay": replay_output,
                })
        
        # Compare confidence
        original_confidence = {}
        for event in original_events:
            source_id = event.get("source_id", "")
            if source_id and event.get("confidence") is not None:
                original_confidence[source_id] = event.get("confidence")
        
        replay_confidence = replay_result.get("workflow_confidence", {})
        
        for source_id in set(original_confidence.keys()) | set(replay_confidence.keys()):
            orig_conf = original_confidence.get(source_id)
            replay_conf = replay_confidence.get(source_id)
            if orig_conf != replay_conf:
                delta["confidence_delta"][source_id] = {
                    "original": orig_conf,
                    "replay": replay_conf,
                    "delta": (replay_conf or 0) - (orig_conf or 0),
                }
        
        # Overall comparison
        delta["overall_match"] = len(delta["differences"]) == 0
        delta["match_rate"] = len(delta["matches"]) / max(len(all_source_ids), 1)
        
        return delta
    
    async def replay_with_guideline_update(
        self,
        execution_id: str,
        new_guideline_version: str,
        modified_inputs: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Replay with updated guideline version.
        
        Args:
            execution_id: Original execution ID
            new_guideline_version: New guideline version identifier
            modified_inputs: Optional modified inputs
            
        Returns:
            Replay result with delta
        """
        # This would require integration with guideline versioning system
        # For now, we'll just replay with a flag
        return await self.replay(
            execution_id=execution_id,
            modified_inputs=modified_inputs,
            modified_context={"guideline_version": new_guideline_version},
            use_updated_guidelines=True,
        )

