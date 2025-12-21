"""
Governed Multi-Agent Clinical Task Execution (Squad) for MedAgentX v1.7

A Squad is:
- A static execution graph (no loops)
- Explicit roles
- Fixed instructions
- Deterministic execution order
- Governance checks at every step

Execution pattern:
Agents → RecommendationEngines → PredictionModels

Rules:
- No free-form agent communication
- No autonomy
- No improvisation
- No recursive execution

Every step must emit:
- Structured output
- Evidence
- Confidence
- Human approval flag
- Audit trace
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import logging

from medagentx.core.types import AgentTrace
from medagentx.core.mcp_registry import MCPRegistry
from medagentx.core.recommendation_engine import RecommendationOutput
from medagentx.core.prediction_model import PredictionOutput
from medagentx.core.crf import ClinicalResponsibilityFirewall

logger = logging.getLogger(__name__)


@dataclass
class SquadStep:
    """A single step in a squad execution graph."""
    step_id: str
    step_type: str  # "agent", "engine", "model"
    entity_id: str  # ID of agent/engine/model to execute
    role: str  # Role description
    instructions: str  # Fixed instructions
    dependencies: List[str] = field(default_factory=list)  # Step IDs this depends on
    input_mapping: Dict[str, str] = field(default_factory=dict)  # Map previous outputs to inputs


@dataclass
class SquadExecutionResult:
    """Result of squad execution."""
    squad_id: str
    execution_id: str
    steps_executed: List[str] = field(default_factory=list)
    outputs: Dict[str, Any] = field(default_factory=dict)  # step_id -> output
    aggregated_confidence: float = 0.5
    requires_human_approval: bool = True  # Always True
    execution_trace: List[AgentTrace] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class SquadExecutor:
    """
    Governed squad executor.
    
    Executes a static execution graph with governance checks at every step.
    """
    
    def __init__(
        self,
        squad_id: str,
        execution_graph: List[SquadStep],
        mcp_registry: MCPRegistry,
        governance_engine: Optional[Any] = None,
        crf: Optional[ClinicalResponsibilityFirewall] = None,  # v2.0: CRF
    ):
        """
        Initialize squad executor.
        
        Args:
            squad_id: Squad identifier
            execution_graph: List of SquadStep objects (must be acyclic)
            mcp_registry: MCP registry for entity lookup
            governance_engine: Optional governance engine for validation
            crf: Optional Clinical Responsibility Firewall
        """
        self.squad_id = squad_id
        self.execution_graph = execution_graph
        self.mcp_registry = mcp_registry
        self.governance_engine = governance_engine
        self.crf = crf or ClinicalResponsibilityFirewall()  # v2.0: Default CRF
        
        # Validate execution graph
        self._validate_execution_graph()
    
    def _validate_execution_graph(self) -> None:
        """Validate execution graph for safety."""
        # Check for cycles
        step_ids = {step.step_id for step in self.execution_graph}
        
        for step in self.execution_graph:
            # Check dependencies exist
            for dep in step.dependencies:
                if dep not in step_ids:
                    raise ValueError(f"Squad {self.squad_id}: step {step.step_id} depends on non-existent step {dep}")
            
            # Check for cycles (simple check - no step can depend on itself or future steps)
            step_index = next(i for i, s in enumerate(self.execution_graph) if s.step_id == step.step_id)
            for dep in step.dependencies:
                dep_index = next(i for i, s in enumerate(self.execution_graph) if s.step_id == dep)
                if dep_index >= step_index:
                    raise ValueError(f"Squad {self.squad_id}: step {step.step_id} depends on step {dep} which comes after it (potential cycle)")
    
    async def execute(
        self,
        initial_context: Dict[str, Any],
        execution_id: Optional[str] = None,
    ) -> SquadExecutionResult:
        """
        Execute squad with initial context.
        
        Args:
            initial_context: Initial clinical context
            execution_id: Optional execution ID (auto-generated if not provided)
            
        Returns:
            SquadExecutionResult with all step outputs and trace
        """
        if execution_id is None:
            execution_id = f"{self.squad_id}_{datetime.now().isoformat()}"
        
        result = SquadExecutionResult(
            squad_id=self.squad_id,
            execution_id=execution_id,
        )
        
        # Track outputs from each step
        step_outputs: Dict[str, Any] = {}
        
        # Execute steps in order
        for step in self.execution_graph:
            try:
                # Resolve dependencies
                step_input = self._resolve_step_input(step, step_outputs, initial_context)
                
                # Execute step
                step_output = await self._execute_step(step, step_input)
                
                # Store output
                step_outputs[step.step_id] = step_output
                result.outputs[step.step_id] = step_output
                result.steps_executed.append(step.step_id)
                
                # v2.0: CRF enforcement
                if isinstance(step_output, dict):
                    step_output = self.crf.enforce(
                        step_output,
                        source=step.step_type,
                        source_id=step.entity_id,
                    )
                elif hasattr(step_output, "__dict__"):
                    # Convert dataclass to dict for CRF
                    step_output_dict = step_output.__dict__ if hasattr(step_output, "__dict__") else {}
                    step_output_dict = self.crf.enforce(
                        step_output_dict,
                        source=step.step_type,
                        source_id=step.entity_id,
                    )
                    # Update dataclass if possible
                    if hasattr(step_output, "responsibility_metadata"):
                        step_output.responsibility_metadata = step_output_dict.get("responsibility_metadata")
                
                # Create trace entry
                trace = self._create_trace_entry(step, step_input, step_output)
                result.execution_trace.append(trace)
                
                # Governance check
                if self.governance_engine:
                    if isinstance(step_output, dict):
                        self.governance_engine.enforce(step_output)
                    else:
                        # Convert to dict for governance
                        output_dict = step_output.__dict__ if hasattr(step_output, "__dict__") else {}
                        self.governance_engine.enforce(output_dict)
                
            except Exception as e:
                logger.error(f"Squad {self.squad_id} step {step.step_id} failed: {e}")
                result.metadata["error"] = str(e)
                result.metadata["failed_step"] = step.step_id
                raise
        
        # Aggregate confidence
        confidences = []
        for step_output in step_outputs.values():
            if isinstance(step_output, dict):
                conf = step_output.get("confidence")
                if conf is not None:
                    confidences.append(float(conf))
            elif hasattr(step_output, "confidence"):
                confidences.append(float(step_output.confidence))
        
        result.aggregated_confidence = sum(confidences) / len(confidences) if confidences else 0.5
        result.requires_human_approval = True  # Always True
        result.metadata["total_steps"] = len(self.execution_graph)
        result.metadata["successful_steps"] = len(result.steps_executed)
        
        return result
    
    def _resolve_step_input(
        self,
        step: SquadStep,
        step_outputs: Dict[str, Any],
        initial_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Resolve input for a step from dependencies and initial context.
        
        Args:
            step: Step to resolve input for
            step_outputs: Outputs from previous steps
            initial_context: Initial context
            
        Returns:
            Resolved input dictionary
        """
        step_input = initial_context.copy()
        
        # Add outputs from dependencies
        for dep_id in step.dependencies:
            if dep_id in step_outputs:
                dep_output = step_outputs[dep_id]
                
                # Apply input mapping if specified
                if step.input_mapping:
                    for source_key, target_key in step.input_mapping.items():
                        if source_key in str(dep_output):
                            step_input[target_key] = dep_output
                else:
                    # Default: add dependency output with step_id as key
                    step_input[dep_id] = dep_output
        
        return step_input
    
    async def _execute_step(
        self,
        step: SquadStep,
        step_input: Dict[str, Any],
    ) -> Any:
        """
        Execute a single squad step.
        
        Args:
            step: Step to execute
            step_input: Input for step
            
        Returns:
            Step output
        """
        if step.step_type == "agent":
            agent = self.mcp_registry.get_agent(step.entity_id)
            if not agent:
                raise ValueError(f"Agent {step.entity_id} not found in registry")
            
            # Execute agent with instructions
            task = f"{step.instructions}\n\nContext: {step_input}"
            result = await agent.run(task, context=step_input)
            return result
        
        elif step.step_type == "engine":
            engine = self.mcp_registry.get_engine(step.entity_id)
            if not engine:
                raise ValueError(f"Engine {step.entity_id} not found in registry")
            
            # Execute engine with clinical context
            result = await engine.recommend(step_input)
            return result
        
        elif step.step_type == "model":
            model = self.mcp_registry.get_model(step.entity_id)
            if not model:
                raise ValueError(f"Model {step.entity_id} not found in registry")
            
            # Extract features from input
            features = step_input.get("features", step_input)
            if not isinstance(features, dict):
                features = {"input": features}
            
            result = await model.predict(features)
            return result
        
        else:
            raise ValueError(f"Unknown step type: {step.step_type}")
    
    def _create_trace_entry(
        self,
        step: SquadStep,
        step_input: Dict[str, Any],
        step_output: Any,
    ) -> AgentTrace:
        """
        Create trace entry for a step.
        
        Args:
            step: Step executed
            step_input: Step input
            step_output: Step output
            
        Returns:
            AgentTrace entry
        """
        # Extract evidence and confidence from output
        evidence = None
        confidence = None
        
        if isinstance(step_output, dict):
            evidence = step_output.get("evidence") or step_output.get("output")
            confidence = step_output.get("confidence")
        elif hasattr(step_output, "evidence"):
            evidence = step_output.evidence
        if hasattr(step_output, "confidence"):
            confidence = step_output.confidence
        
        return AgentTrace(
            agent_name=f"{step.step_type}:{step.entity_id}",
            input=step_input,
            plan={"step_id": step.step_id, "role": step.role, "instructions": step.instructions},
            tools_used=[],
            evidence=evidence,
            output=step_output,
            confidence=confidence,
            visualization_metadata={
                "step_type": step.step_type,
                "step_id": step.step_id,
                "entity_id": step.entity_id,
                "role": step.role,
            },
        )

