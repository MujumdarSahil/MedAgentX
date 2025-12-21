"""
Counterfactual Diagnosis Engine (CDE) for MedAgentX v2.0

Non-diagnostic, bias-reduction and decision-support module.
Generates controlled counterfactual scenarios for anchoring bias reduction
and alternate explanation comparison.

HARD CONSTRAINTS:
- Must NOT generate diagnoses
- Must NOT rank diseases
- Must NOT suggest treatments or medications
- Must NOT override clinician authority
- Must be explicitly labeled as "Counterfactual Analysis — Non-Diagnostic Decision Support"
"""

from typing import Any, Dict, List, Optional, Set
from datetime import datetime
import logging

from medagentx.core.replay_engine import ReplayEngine
from medagentx.core.event_store import EventStore
from medagentx.core.workflow import RecommendationWorkflow
from medagentx.core.crf import ResponsibilityMetadata, ResponsibilityTag

logger = logging.getLogger(__name__)


class CounterfactualScenario:
    """Represents a single counterfactual scenario."""
    
    def __init__(
        self,
        scenario_id: str,
        original_symptom: Optional[str],
        modified_symptom: Optional[str],
        original_context: Dict[str, Any],
        modified_context: Dict[str, Any],
        what_changed: str,
        what_remained_stable: List[str],
        confidence_shifts: Optional[Dict[str, float]] = None,
        uncertainty_markers: Optional[List[str]] = None,
    ):
        """
        Initialize counterfactual scenario.
        
        Args:
            scenario_id: Unique scenario identifier
            original_symptom: Original symptom (if modified)
            modified_symptom: Modified symptom (if modified)
            original_context: Original context
            modified_context: Modified context
            what_changed: Description of what changed
            what_remained_stable: List of what remained stable
            confidence_shifts: Optional confidence shifts by component
            uncertainty_markers: Optional uncertainty markers
        """
        self.scenario_id = scenario_id
        self.original_symptom = original_symptom
        self.modified_symptom = modified_symptom
        self.original_context = original_context
        self.modified_context = modified_context
        self.what_changed = what_changed
        self.what_remained_stable = what_remained_stable
        self.confidence_shifts = confidence_shifts or {}
        self.uncertainty_markers = uncertainty_markers or []
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "scenario_id": self.scenario_id,
            "original_symptom": self.original_symptom,
            "modified_symptom": self.modified_symptom,
            "original_context": self.original_context,
            "modified_context": self.modified_context,
            "what_changed": self.what_changed,
            "what_remained_stable": self.what_remained_stable,
            "confidence_shifts": self.confidence_shifts,
            "uncertainty_markers": self.uncertainty_markers,
            "timestamp": self.timestamp,
        }


class CounterfactualDiagnosisEngine:
    """
    Counterfactual Diagnosis Engine.
    
    Generates controlled counterfactual scenarios by removing or altering
    EXACTLY ONE symptom or ONE contextual variable at a time.
    Executes counterfactuals via the existing deterministic Replay Engine.
    Produces structured delta reports.
    
    MANDATORY LABELING:
    "Counterfactual Analysis — Non-Diagnostic Decision Support"
    
    PERMITTED USE CASES:
    - Anchoring bias reduction
    - Alternate explanation comparison
    - Rare condition surfacing WITHOUT naming conditions
    """
    
    def __init__(
        self,
        replay_engine: ReplayEngine,
        event_store: EventStore,
    ):
        """
        Initialize Counterfactual Diagnosis Engine.
        
        Args:
            replay_engine: Replay engine instance
            event_store: Event store instance
        """
        self.replay_engine = replay_engine
        self.event_store = event_store
        logger.info("Counterfactual Diagnosis Engine initialized")
    
    async def generate_counterfactual(
        self,
        execution_id: str,
        modify_symptom: Optional[str] = None,
        remove_symptom: Optional[str] = None,
        modify_context_key: Optional[str] = None,
        modify_context_value: Optional[Any] = None,
    ) -> CounterfactualScenario:
        """
        Generate a single counterfactual scenario.
        
        Only ONE modification is allowed per scenario:
        - Either modify one symptom
        - Or remove one symptom
        - Or modify one context variable
        
        Args:
            execution_id: Original execution ID
            modify_symptom: Symptom to modify (format: "symptom_name:new_value")
            remove_symptom: Symptom to remove
            modify_context_key: Context key to modify
            modify_context_value: New context value
            
        Returns:
            CounterfactualScenario with delta report
            
        Raises:
            ValueError: If multiple modifications specified
        """
        # Validate: only one modification allowed
        modifications = [
            modify_symptom is not None,
            remove_symptom is not None,
            modify_context_key is not None,
        ]
        if sum(modifications) != 1:
            raise ValueError(
                "Exactly ONE modification must be specified: "
                "modify_symptom, remove_symptom, or modify_context_key"
            )
        
        # Get original events
        original_events = self.event_store.get_events(execution_id)
        if not original_events:
            raise ValueError(f"No events found for execution {execution_id}")
        
        # Extract original input and context
        first_event = original_events[0]
        original_input = first_event.get("data", {}).get("input", {})
        original_context = first_event.get("data", {}).get("context", {})
        
        # Build modified inputs/context
        modified_inputs = None
        modified_context = None
        what_changed = ""
        
        if modify_symptom:
            # Parse symptom modification
            if ":" not in modify_symptom:
                raise ValueError("modify_symptom must be in format 'symptom_name:new_value'")
            symptom_name, new_value = modify_symptom.split(":", 1)
            modified_inputs = original_input.copy()
            if isinstance(modified_inputs, dict):
                modified_inputs["symptoms"] = modified_inputs.get("symptoms", "").replace(
                    symptom_name, new_value
                )
            what_changed = f"Modified symptom: {symptom_name} -> {new_value}"
        
        elif remove_symptom:
            modified_inputs = original_input.copy()
            if isinstance(modified_inputs, dict):
                symptoms_text = modified_inputs.get("symptoms", "")
                # Simple removal (can be enhanced)
                modified_inputs["symptoms"] = symptoms_text.replace(remove_symptom, "").strip()
            what_changed = f"Removed symptom: {remove_symptom}"
        
        elif modify_context_key:
            modified_context = original_context.copy()
            modified_context[modify_context_key] = modify_context_value
            what_changed = f"Modified context: {modify_context_key} -> {modify_context_value}"
        
        # Execute replay
        replay_result = await self.replay_engine.replay(
            execution_id=execution_id,
            modified_inputs=modified_inputs,
            modified_context=modified_context,
        )
        
        # Extract original outputs for comparison
        original_outputs = self._extract_outputs(original_events)
        replay_outputs = self._extract_outputs_from_replay(replay_result)
        
        # Compute what remained stable
        what_remained_stable = self._compute_stable_elements(
            original_outputs,
            replay_outputs,
        )
        
        # Compute confidence shifts
        confidence_shifts = self._compute_confidence_shifts(
            original_events,
            replay_result,
        )
        
        # Generate uncertainty markers
        uncertainty_markers = self._generate_uncertainty_markers(
            original_outputs,
            replay_outputs,
            confidence_shifts,
        )
        
        # Create scenario
        scenario_id = f"{execution_id}_counterfactual_{datetime.now().isoformat()}"
        scenario_id = scenario_id.replace(":", "-").replace(".", "-")
        
        scenario = CounterfactualScenario(
            scenario_id=scenario_id,
            original_symptom=modify_symptom or remove_symptom,
            modified_symptom=modify_symptom.split(":")[1] if modify_symptom and ":" in modify_symptom else None,
            original_context=original_context,
            modified_context=modified_context or original_context,
            what_changed=what_changed,
            what_remained_stable=what_remained_stable,
            confidence_shifts=confidence_shifts,
            uncertainty_markers=uncertainty_markers,
        )
        
        logger.info(f"Generated counterfactual scenario {scenario_id}")
        
        return scenario
    
    async def generate_counterfactual_batch(
        self,
        execution_id: str,
        symptom_modifications: Optional[List[str]] = None,
        symptom_removals: Optional[List[str]] = None,
        context_modifications: Optional[Dict[str, Any]] = None,
    ) -> List[CounterfactualScenario]:
        """
        Generate multiple counterfactual scenarios.
        
        Each scenario modifies exactly ONE element.
        
        Args:
            execution_id: Original execution ID
            symptom_modifications: List of symptom modifications (format: "name:value")
            symptom_removals: List of symptoms to remove
            context_modifications: Dict of context key->value modifications
            
        Returns:
            List of CounterfactualScenario objects
        """
        scenarios = []
        
        # Generate scenarios for symptom modifications
        if symptom_modifications:
            for mod in symptom_modifications:
                scenario = await self.generate_counterfactual(
                    execution_id=execution_id,
                    modify_symptom=mod,
                )
                scenarios.append(scenario)
        
        # Generate scenarios for symptom removals
        if symptom_removals:
            for removal in symptom_removals:
                scenario = await self.generate_counterfactual(
                    execution_id=execution_id,
                    remove_symptom=removal,
                )
                scenarios.append(scenario)
        
        # Generate scenarios for context modifications
        if context_modifications:
            for key, value in context_modifications.items():
                scenario = await self.generate_counterfactual(
                    execution_id=execution_id,
                    modify_context_key=key,
                    modify_context_value=value,
                )
                scenarios.append(scenario)
        
        return scenarios
    
    def _extract_outputs(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract outputs from events."""
        outputs = {}
        for event in events:
            source_id = event.get("source_id", "")
            if source_id:
                outputs[source_id] = event.get("data", {}).get("output", {})
        return outputs
    
    def _extract_outputs_from_replay(self, replay_result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract outputs from replay result."""
        outputs = {}
        replay_data = replay_result.get("replay_result", {})
        
        if "structured_symptoms" in replay_data:
            outputs["symptom_analyzer"] = {"symptoms": replay_data.get("structured_symptoms", [])}
        if "support" in replay_data:
            outputs["diagnosis_support"] = replay_data.get("support", {})
        if "coding" in replay_data:
            outputs["medical_coder"] = replay_data.get("coding", {})
        
        return outputs
    
    def _compute_stable_elements(
        self,
        original_outputs: Dict[str, Any],
        replay_outputs: Dict[str, Any],
    ) -> List[str]:
        """Compute what remained stable between original and replay."""
        stable = []
        
        all_keys = set(original_outputs.keys()) | set(replay_outputs.keys())
        for key in all_keys:
            orig = original_outputs.get(key, {})
            replay = replay_outputs.get(key, {})
            
            if orig == replay:
                stable.append(key)
        
        return stable
    
    def _compute_confidence_shifts(
        self,
        original_events: List[Dict[str, Any]],
        replay_result: Dict[str, Any],
    ) -> Dict[str, float]:
        """Compute confidence shifts between original and replay."""
        shifts = {}
        
        # Extract original confidence
        original_confidence = {}
        for event in original_events:
            source_id = event.get("source_id", "")
            if source_id and event.get("confidence") is not None:
                original_confidence[source_id] = event.get("confidence")
        
        # Extract replay confidence
        replay_data = replay_result.get("replay_result", {})
        replay_confidence = replay_data.get("workflow_confidence", {})
        
        # Compute shifts
        all_keys = set(original_confidence.keys()) | set(replay_confidence.keys())
        for key in all_keys:
            orig_conf = original_confidence.get(key, 0.0)
            replay_conf = replay_confidence.get(key, 0.0)
            shift = replay_conf - orig_conf
            if abs(shift) > 0.01:  # Only record meaningful shifts
                shifts[key] = shift
        
        return shifts
    
    def _generate_uncertainty_markers(
        self,
        original_outputs: Dict[str, Any],
        replay_outputs: Dict[str, Any],
        confidence_shifts: Dict[str, float],
    ) -> List[str]:
        """Generate uncertainty markers based on differences."""
        markers = []
        
        # Check for significant output differences
        if original_outputs != replay_outputs:
            markers.append("Output differences detected between original and counterfactual")
        
        # Check for confidence shifts
        if confidence_shifts:
            for key, shift in confidence_shifts.items():
                if abs(shift) > 0.1:
                    markers.append(
                        f"Significant confidence shift in {key}: {shift:+.2f}"
                    )
        
        # If no differences, mark as stable
        if not markers:
            markers.append("Counterfactual scenario produced stable outputs")
        
        return markers
    
    def format_counterfactual_report(
        self,
        scenario: CounterfactualScenario,
    ) -> Dict[str, Any]:
        """
        Format counterfactual scenario as a structured report.
        
        Includes mandatory labeling:
        "Counterfactual Analysis — Non-Diagnostic Decision Support"
        
        Args:
            scenario: CounterfactualScenario to format
            
        Returns:
            Formatted report dictionary
        """
        report = {
            "label": "Counterfactual Analysis — Non-Diagnostic Decision Support",
            "scenario_id": scenario.scenario_id,
            "timestamp": scenario.timestamp,
            "modification": {
                "what_changed": scenario.what_changed,
                "original_symptom": scenario.original_symptom,
                "modified_symptom": scenario.modified_symptom,
            },
            "stability_analysis": {
                "what_remained_stable": scenario.what_remained_stable,
            },
            "confidence_analysis": {
                "confidence_shifts": scenario.confidence_shifts,
            },
            "uncertainty_analysis": {
                "uncertainty_markers": scenario.uncertainty_markers,
            },
            "disclaimer": (
                "This counterfactual analysis is for decision support only. "
                "It does not constitute a diagnosis, treatment recommendation, "
                "or medical advice. All clinical decisions require human clinician review."
            ),
            "responsibility_metadata": ResponsibilityMetadata.create_ai_suggested(
                evidence=["counterfactual_analysis"]
            ).to_dict(),
            "human_approval_required": True,
        }
        
        return report

