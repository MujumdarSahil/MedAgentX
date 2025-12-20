"""
Base template for specialized agent implementations.

This module provides a foundation for building domain-specific agents
with specialized reasoning patterns and workflows.
"""

import logging
from typing import Any, Dict, List, Optional
from medagentx.core.agent import BaseAgent
from medagentx.core.types import (
    AgentConfig,
    AgentState,
    Recommendation,
    RecommendationType,
    ClinicalConfidence,
    AgentCapabilities,
)
from medagentx.governance.engine import GovernanceException

logger = logging.getLogger(__name__)


class SpecializedAgent(BaseAgent):
    """
    Base class for specialized medical agents.
    
    Provides common functionality for medical domain agents:
    - Clinical recommendation generation
    - Evidence gathering
    - Risk assessment
    - Confidence scoring
    """
    
    def __init__(
        self,
        config: AgentConfig,
        tool_registry: Optional[Any] = None,
        governance_engine: Optional[Any] = None,
        knowledge_base: Optional[Any] = None,
        capabilities: Optional[AgentCapabilities] = None,
        llm_engine: Optional[Any] = None,
    ):
        """
        Initialize specialized agent.
        
        Args:
            config: Agent configuration
            tool_registry: Tool registry
            governance_engine: Governance engine
            knowledge_base: Knowledge base for retrieval
            capabilities: Agent capabilities (defaults to safe restrictions)
            llm_engine: Optional LLM engine for reasoning
        """
        super().__init__(config, tool_registry, governance_engine, llm_engine)
        self.knowledge_base = knowledge_base
        self.capabilities = capabilities or AgentCapabilities()
        
        # Validate capabilities on initialization
        if self.governance_engine:
            self.governance_engine.validate_agent(self, self.capabilities)
    
    async def generate_recommendation(
        self,
        recommendation_type: RecommendationType,
        content: str,
        confidence_score: float,
        supporting_evidence: Optional[List[str]] = None,
        alternative_options: Optional[List[str]] = None,
        risks_and_warnings: Optional[List[str]] = None,
    ) -> Recommendation:
        """
        Generate a clinical recommendation with proper metadata.
        
        Args:
            recommendation_type: Type of recommendation
            content: Recommendation content
            confidence_score: Confidence score (0.0-1.0)
            supporting_evidence: Supporting evidence
            alternative_options: Alternative options
            risks_and_warnings: Risks and warnings
            
        Returns:
            Recommendation object
        """
        # Map confidence score to confidence level
        if confidence_score >= 0.9:
            confidence = ClinicalConfidence.VERY_HIGH
        elif confidence_score >= 0.7:
            confidence = ClinicalConfidence.HIGH
        elif confidence_score >= 0.5:
            confidence = ClinicalConfidence.MODERATE
        elif confidence_score >= 0.3:
            confidence = ClinicalConfidence.LOW
        else:
            confidence = ClinicalConfidence.VERY_LOW
        
        recommendation = Recommendation(
            recommendation_type=recommendation_type,
            content=content,
            confidence=confidence,
            confidence_score=confidence_score,
            supporting_evidence=supporting_evidence or [],
            alternative_options=alternative_options or [],
            risks_and_warnings=risks_and_warnings or [],
            requires_human_approval=True,  # Always require approval for safety
        )
        
        self.add_recommendation(recommendation)
        return recommendation
    
    async def retrieve_clinical_knowledge(
        self,
        query: str,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant clinical knowledge.
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of retrieved knowledge items
        """
        if not self.knowledge_base:
            return []
        
        try:
            results = await self.knowledge_base.search(
                query=query,
                top_k=top_k,
            )
            return results
        except Exception as e:
            logger.error(f"Knowledge retrieval error: {e}")
            return []
    
    async def assess_confidence(
        self,
        evidence: List[str],
        quality_indicators: Dict[str, Any],
    ) -> float:
        """
        Assess confidence score based on evidence and quality indicators.
        
        Args:
            evidence: List of evidence items
            quality_indicators: Quality metrics
            
        Returns:
            Confidence score (0.0-1.0)
        """
        # Simple heuristic - in production, this would be more sophisticated
        base_confidence = 0.5
        
        # Increase confidence with more evidence
        evidence_bonus = min(len(evidence) * 0.1, 0.3)
        
        # Adjust based on quality indicators
        quality_bonus = 0.0
        if quality_indicators.get("high_quality_source"):
            quality_bonus += 0.1
        if quality_indicators.get("multiple_sources"):
            quality_bonus += 0.1
        
        confidence = min(base_confidence + evidence_bonus + quality_bonus, 1.0)
        return confidence
    
    async def analyze(self, input_data: Any) -> Dict[str, Any]:
        """
        User-defined analysis logic. Override this method in custom agents.
        
        Args:
            input_data: Input to analyze
            
        Returns:
            Analysis result dictionary
        """
        return {
            "output": {},
            "confidence": 0.5,
            "reasoning": "Base analysis placeholder",
        }
    
    async def run(self, task: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Run agent with capability enforcement.
        """
        # Enforce capabilities before execution
        if self.governance_engine:
            self.governance_engine.validate_agent(self, self.capabilities)
        
        # Call parent run method
        return await super().run(task, context)

