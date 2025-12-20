"""
Recommendation Engine Abstraction for MedAgentX v1.7

Provides a governed interface for clinical recommendation generation.
RecommendationEngines MUST NOT emit diagnosis or treatment.
All outputs require human approval.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class RecommendationOutput:
    """Structured output from a recommendation engine."""
    insights: List[str] = field(default_factory=list)
    risk_modifiers: Dict[str, Any] = field(default_factory=dict)
    evidence: List[str] = field(default_factory=list)
    confidence: float = 0.5  # 0.0-1.0
    human_approval_required: bool = True  # Always True
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class RecommendationEngine(ABC):
    """
    Abstract base class for recommendation engines.
    
    RecommendationEngines provide clinical insights and risk modifiers
    but MUST NOT emit diagnosis or treatment recommendations.
    """
    
    def __init__(
        self,
        engine_id: str,
        name: str,
        description: str,
        purpose: str,
        scope: str,
        allowed_outputs: List[str],
        governance_constraints: Dict[str, Any],
    ):
        """
        Initialize recommendation engine.
        
        Args:
            engine_id: Unique identifier
            name: Human-readable name
            description: Description of engine capabilities
            purpose: Purpose of this engine
            scope: Scope of operation (e.g., "symptom_analysis", "risk_assessment")
            allowed_outputs: List of allowed output types (must not include "diagnosis" or "treatment")
            governance_constraints: Constraints for governance validation
        """
        self.engine_id = engine_id
        self.name = name
        self.description = description
        self.purpose = purpose
        self.scope = scope
        self.allowed_outputs = allowed_outputs
        self.governance_constraints = governance_constraints
        
        # Validate that diagnosis/treatment are not in allowed_outputs
        forbidden = ["diagnosis", "treatment", "prescription"]
        if any(f in str(allowed_outputs).lower() for f in forbidden):
            raise ValueError(f"RecommendationEngine cannot emit diagnosis or treatment. Got: {allowed_outputs}")
    
    @abstractmethod
    async def recommend(
        self,
        clinical_context: Dict[str, Any],
    ) -> RecommendationOutput:
        """
        Generate recommendations from clinical context.
        
        Args:
            clinical_context: Structured clinical context (symptoms, patient_data, etc.)
            
        Returns:
            RecommendationOutput with insights, risk_modifiers, evidence, confidence
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if engine is available."""
        pass
    
    def validate_output(self, output: RecommendationOutput) -> bool:
        """
        Validate output against governance constraints.
        
        Args:
            output: Output to validate
            
        Returns:
            True if valid, False otherwise
        """
        # Ensure human approval is always required
        if not output.human_approval_required:
            logger.warning(f"RecommendationEngine {self.engine_id} output missing human_approval_required flag")
            return False
        
        # Check that output type is allowed
        output_type = output.metadata.get("output_type", "")
        if output_type and output_type not in self.allowed_outputs:
            logger.warning(f"RecommendationEngine {self.engine_id} output type {output_type} not in allowed_outputs")
            return False
        
        return True


class DeterministicRecommendationEngine(RecommendationEngine):
    """Deterministic recommendation engine (rule-based)."""
    
    def __init__(
        self,
        engine_id: str,
        name: str,
        description: str,
        purpose: str,
        scope: str,
        allowed_outputs: List[str],
        governance_constraints: Dict[str, Any],
        rule_function: Optional[callable] = None,
    ):
        """
        Initialize deterministic recommendation engine.
        
        Args:
            rule_function: Function that takes clinical_context and returns RecommendationOutput
        """
        super().__init__(engine_id, name, description, purpose, scope, allowed_outputs, governance_constraints)
        self.rule_function = rule_function
    
    async def recommend(self, clinical_context: Dict[str, Any]) -> RecommendationOutput:
        """Generate recommendations using rule-based logic."""
        if self.rule_function:
            result = self.rule_function(clinical_context)
            if isinstance(result, RecommendationOutput):
                output = result
            else:
                # Convert dict to RecommendationOutput
                output = RecommendationOutput(**result) if isinstance(result, dict) else RecommendationOutput()
        else:
            # Default deterministic behavior
            symptoms = clinical_context.get("symptoms", [])
            output = RecommendationOutput(
                insights=[f"Analyzed {len(symptoms)} symptoms"],
                risk_modifiers={"symptom_count": len(symptoms)},
                evidence=["Deterministic rule-based analysis"],
                confidence=0.5,
            )
        
        # Ensure human approval
        output.human_approval_required = True
        output.metadata["engine_id"] = self.engine_id
        output.metadata["engine_type"] = "deterministic"
        
        if not self.validate_output(output):
            logger.error(f"RecommendationEngine {self.engine_id} output validation failed")
        
        return output
    
    def is_available(self) -> bool:
        return True


class LLMBackedRecommendationEngine(RecommendationEngine):
    """LLM-backed recommendation engine (optional LLM assistance)."""
    
    def __init__(
        self,
        engine_id: str,
        name: str,
        description: str,
        purpose: str,
        scope: str,
        allowed_outputs: List[str],
        governance_constraints: Dict[str, Any],
        llm_engine: Optional[Any] = None,
    ):
        """
        Initialize LLM-backed recommendation engine.
        
        Args:
            llm_engine: Optional LLM engine for assistance
        """
        super().__init__(engine_id, name, description, purpose, scope, allowed_outputs, governance_constraints)
        self.llm_engine = llm_engine
    
    async def recommend(self, clinical_context: Dict[str, Any]) -> RecommendationOutput:
        """Generate recommendations with optional LLM assistance."""
        # Start with deterministic base
        base_output = await DeterministicRecommendationEngine(
            self.engine_id,
            self.name,
            self.description,
            self.purpose,
            self.scope,
            self.allowed_outputs,
            self.governance_constraints,
        ).recommend(clinical_context)
        
        # Optionally enhance with LLM if available
        if self.llm_engine and self.llm_engine.is_available():
            try:
                from medagentx.models.llm_engine import LLMPurpose
                
                prompt = f"Analyze clinical context and provide insights (NOT diagnosis or treatment): {clinical_context}"
                system_prompt = "You are a clinical assistant. Provide insights and risk modifiers only. Do NOT diagnose or prescribe."
                
                llm_response = await self.llm_engine.generate(
                    prompt=prompt,
                    purpose=LLMPurpose.EVIDENCE_SUMMARIZATION,
                    system_prompt=system_prompt,
                )
                
                # Parse LLM response and enhance base output
                if llm_response.get("structured_output"):
                    llm_data = llm_response["structured_output"]
                    if isinstance(llm_data, dict):
                        if "insights" in llm_data:
                            base_output.insights.extend(llm_data["insights"])
                        if "risk_modifiers" in llm_data:
                            base_output.risk_modifiers.update(llm_data["risk_modifiers"])
                        if "evidence" in llm_data:
                            base_output.evidence.extend(llm_data["evidence"])
                        if "confidence" in llm_data:
                            base_output.confidence = float(llm_data["confidence"])
                
                base_output.metadata["llm_used"] = True
                base_output.metadata["llm_provider"] = self.llm_engine.provider.value
                base_output.metadata["llm_model"] = self.llm_engine.model_name
            except Exception as e:
                logger.warning(f"LLM enhancement failed for {self.engine_id}: {e}")
                base_output.metadata["llm_used"] = False
        
        base_output.human_approval_required = True
        base_output.metadata["engine_id"] = self.engine_id
        base_output.metadata["engine_type"] = "llm_backed"
        
        if not self.validate_output(base_output):
            logger.error(f"RecommendationEngine {self.engine_id} output validation failed")
        
        return base_output
    
    def is_available(self) -> bool:
        return True  # Always available, LLM is optional

