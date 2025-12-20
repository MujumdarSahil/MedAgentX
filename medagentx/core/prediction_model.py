"""
Prediction Model Abstraction for MedAgentX v1.7

Provides a governed interface for clinical prediction generation.
PredictionModels MUST NOT emit diagnosis or treatment.
All outputs require human approval.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class PredictionOutput:
    """Structured output from a prediction model."""
    probability: float = 0.0  # 0.0-1.0
    confidence: float = 0.5  # 0.0-1.0
    explanation: str = ""
    evidence: List[str] = field(default_factory=list)
    human_approval_required: bool = True  # Always True
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class PredictionModel(ABC):
    """
    Abstract base class for prediction models.
    
    PredictionModels provide probability estimates and explanations
    but MUST NOT emit diagnosis or treatment recommendations.
    """
    
    def __init__(
        self,
        model_id: str,
        name: str,
        description: str,
        purpose: str,
        scope: str,
        allowed_outputs: List[str],
        governance_constraints: Dict[str, Any],
        feature_schema: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize prediction model.
        
        Args:
            model_id: Unique identifier
            name: Human-readable name
            description: Description of model capabilities
            purpose: Purpose of this model
            scope: Scope of operation (e.g., "risk_prediction", "outcome_prediction")
            allowed_outputs: List of allowed output types (must not include "diagnosis" or "treatment")
            governance_constraints: Constraints for governance validation
            feature_schema: JSON schema for input features
        """
        self.model_id = model_id
        self.name = name
        self.description = description
        self.purpose = purpose
        self.scope = scope
        self.allowed_outputs = allowed_outputs
        self.governance_constraints = governance_constraints
        self.feature_schema = feature_schema or {}
        
        # Validate that diagnosis/treatment are not in allowed_outputs
        forbidden = ["diagnosis", "treatment", "prescription"]
        if any(f in str(allowed_outputs).lower() for f in forbidden):
            raise ValueError(f"PredictionModel cannot emit diagnosis or treatment. Got: {allowed_outputs}")
    
    @abstractmethod
    async def predict(
        self,
        features: Dict[str, Union[float, int, str, bool]],
    ) -> PredictionOutput:
        """
        Generate prediction from features.
        
        Args:
            features: Structured numeric/categorical features
            
        Returns:
            PredictionOutput with probability, confidence, explanation, evidence
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if model is available."""
        pass
    
    def validate_features(self, features: Dict[str, Any]) -> bool:
        """
        Validate input features against schema.
        
        Args:
            features: Features to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not self.feature_schema:
            return True  # No schema, accept all
        
        # Basic validation (can be extended)
        required = self.feature_schema.get("required", [])
        for field_name in required:
            if field_name not in features:
                logger.warning(f"PredictionModel {self.model_id} missing required feature: {field_name}")
                return False
        
        return True
    
    def validate_output(self, output: PredictionOutput) -> bool:
        """
        Validate output against governance constraints.
        
        Args:
            output: Output to validate
            
        Returns:
            True if valid, False otherwise
        """
        # Ensure human approval is always required
        if not output.human_approval_required:
            logger.warning(f"PredictionModel {self.model_id} output missing human_approval_required flag")
            return False
        
        # Validate probability range
        if not (0.0 <= output.probability <= 1.0):
            logger.warning(f"PredictionModel {self.model_id} probability out of range: {output.probability}")
            return False
        
        # Validate confidence range
        if not (0.0 <= output.confidence <= 1.0):
            logger.warning(f"PredictionModel {self.model_id} confidence out of range: {output.confidence}")
            return False
        
        return True


class DeterministicPredictionModel(PredictionModel):
    """Deterministic prediction model (rule-based)."""
    
    def __init__(
        self,
        model_id: str,
        name: str,
        description: str,
        purpose: str,
        scope: str,
        allowed_outputs: List[str],
        governance_constraints: Dict[str, Any],
        feature_schema: Optional[Dict[str, Any]] = None,
        rule_function: Optional[callable] = None,
    ):
        """
        Initialize deterministic prediction model.
        
        Args:
            rule_function: Function that takes features and returns PredictionOutput
        """
        super().__init__(model_id, name, description, purpose, scope, allowed_outputs, governance_constraints, feature_schema)
        self.rule_function = rule_function
    
    async def predict(self, features: Dict[str, Union[float, int, str, bool]]) -> PredictionOutput:
        """Generate prediction using rule-based logic."""
        if not self.validate_features(features):
            raise ValueError(f"Invalid features for PredictionModel {self.model_id}")
        
        if self.rule_function:
            result = self.rule_function(features)
            if isinstance(result, PredictionOutput):
                output = result
            else:
                # Convert dict to PredictionOutput
                output = PredictionOutput(**result) if isinstance(result, dict) else PredictionOutput()
        else:
            # Default deterministic behavior
            output = PredictionOutput(
                probability=0.5,
                confidence=0.5,
                explanation="Deterministic rule-based prediction",
                evidence=["Rule-based calculation"],
            )
        
        # Ensure human approval
        output.human_approval_required = True
        output.metadata["model_id"] = self.model_id
        output.metadata["model_type"] = "deterministic"
        
        if not self.validate_output(output):
            logger.error(f"PredictionModel {self.model_id} output validation failed")
        
        return output
    
    def is_available(self) -> bool:
        return True


class MLBackedPredictionModel(PredictionModel):
    """ML-backed prediction model (optional ML assistance)."""
    
    def __init__(
        self,
        model_id: str,
        name: str,
        description: str,
        purpose: str,
        scope: str,
        allowed_outputs: List[str],
        governance_constraints: Dict[str, Any],
        feature_schema: Optional[Dict[str, Any]] = None,
        ml_model: Optional[Any] = None,
    ):
        """
        Initialize ML-backed prediction model.
        
        Args:
            ml_model: Optional ML model for prediction
        """
        super().__init__(model_id, name, description, purpose, scope, allowed_outputs, governance_constraints, feature_schema)
        self.ml_model = ml_model
    
    async def predict(self, features: Dict[str, Union[float, int, str, bool]]) -> PredictionOutput:
        """Generate prediction with optional ML assistance."""
        if not self.validate_features(features):
            raise ValueError(f"Invalid features for PredictionModel {self.model_id}")
        
        # Start with deterministic base
        base_output = await DeterministicPredictionModel(
            self.model_id,
            self.name,
            self.description,
            self.purpose,
            self.scope,
            self.allowed_outputs,
            self.governance_constraints,
            self.feature_schema,
        ).predict(features)
        
        # Optionally enhance with ML if available
        if self.ml_model:
            try:
                # Convert features to ML model format
                # This is a placeholder - actual implementation depends on ML framework
                ml_features = self._prepare_features(features)
                
                # Get ML prediction (synchronous call wrapped in async)
                import asyncio
                loop = asyncio.get_event_loop()
                ml_prediction = await loop.run_in_executor(
                    None,
                    lambda: self._ml_predict(ml_features)
                )
                
                # Enhance base output with ML prediction
                if ml_prediction:
                    base_output.probability = ml_prediction.get("probability", base_output.probability)
                    base_output.confidence = ml_prediction.get("confidence", base_output.confidence)
                    if ml_prediction.get("explanation"):
                        base_output.explanation = ml_prediction["explanation"]
                    if ml_prediction.get("evidence"):
                        base_output.evidence.extend(ml_prediction["evidence"])
                
                base_output.metadata["ml_used"] = True
                base_output.metadata["ml_model_type"] = type(self.ml_model).__name__
            except Exception as e:
                logger.warning(f"ML enhancement failed for {self.model_id}: {e}")
                base_output.metadata["ml_used"] = False
        
        base_output.human_approval_required = True
        base_output.metadata["model_id"] = self.model_id
        base_output.metadata["model_type"] = "ml_backed"
        
        if not self.validate_output(base_output):
            logger.error(f"PredictionModel {self.model_id} output validation failed")
        
        return base_output
    
    def _prepare_features(self, features: Dict[str, Any]) -> Any:
        """Prepare features for ML model (placeholder)."""
        # Convert features dict to ML model input format
        # This should be overridden for specific ML frameworks
        return features
    
    def _ml_predict(self, ml_features: Any) -> Optional[Dict[str, Any]]:
        """Run ML model prediction (placeholder)."""
        # This should be overridden for specific ML frameworks
        # For now, return None to use deterministic fallback
        return None
    
    def is_available(self) -> bool:
        return True  # Always available, ML is optional

