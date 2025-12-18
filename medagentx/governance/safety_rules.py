"""
Safety Rules for MedAgentX Governance Engine.

Defines rules and constraints for clinical safety and compliance.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from medagentx.core.types import ToolCall, Recommendation


class SafetyRule(ABC):
    """
    Base class for safety rules.
    
    Safety rules are evaluated to ensure clinical safety and compliance.
    """
    
    @abstractmethod
    async def evaluate(
        self,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Evaluate the safety rule.
        
        Args:
            context: Context for evaluation
            
        Returns:
            Dict with:
                - passed: bool
                - message: str
                - severity: str (info, warning, error, critical)
        """
        pass


class ClinicalSafetyRule(SafetyRule):
    """
    Clinical safety rule base class.
    
    Specialized for clinical decision support safety.
    """
    
    async def evaluate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate clinical safety rule."""
        return await self.evaluate_clinical(context)
    
    @abstractmethod
    async def evaluate_clinical(
        self,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Evaluate in clinical context."""
        pass


class HumanApprovalRequiredRule(ClinicalSafetyRule):
    """
    Rule that enforces human approval for recommendations.
    
    This is a critical safety rule that ensures all clinical recommendations
    require human (doctor) approval before being used.
    """
    
    async def evaluate_clinical(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ensure recommendations require human approval.
        
        Args:
            context: Context containing recommendations
            
        Returns:
            Evaluation result
        """
        recommendations = context.get("recommendations", [])
        
        for rec in recommendations:
            if isinstance(rec, Recommendation):
                if not rec.requires_human_approval:
                    return {
                        "passed": False,
                        "message": "All recommendations must require human approval",
                        "severity": "critical",
                    }
        
        return {
            "passed": True,
            "message": "All recommendations require human approval",
            "severity": "info",
        }


class DisclaimerRequiredRule(ClinicalSafetyRule):
    """
    Rule that enforces disclaimers on all outputs.
    
    Ensures that all AI-generated recommendations include appropriate
    disclaimers about their nature (decision support, not final diagnosis).
    """
    
    async def evaluate_clinical(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ensure disclaimers are present.
        
        Args:
            context: Context containing outputs
            
        Returns:
            Evaluation result
        """
        outputs = context.get("outputs", [])
        required_disclaimer_keywords = [
            "decision support",
            "recommendation",
            "not a final diagnosis",
        ]
        
        for output in outputs:
            if isinstance(output, str):
                has_disclaimer = any(
                    keyword.lower() in output.lower()
                    for keyword in required_disclaimer_keywords
                )
                if not has_disclaimer:
                    return {
                        "passed": False,
                        "message": "Outputs must include appropriate disclaimers",
                        "severity": "warning",
                    }
        
        return {
            "passed": True,
            "message": "Disclaimers present",
            "severity": "info",
        }


class ToolPermissionRule(SafetyRule):
    """
    Rule that checks tool permissions.
    
    Ensures agents only use tools they have permission for.
    """
    
    async def evaluate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check tool permissions.
        
        Args:
            context: Context with tool_call and agent_id
            
        Returns:
            Evaluation result
        """
        tool_call = context.get("tool_call")
        agent_id = context.get("agent_id")
        allowed_tools = context.get("allowed_tools", [])
        
        if tool_call and isinstance(tool_call, ToolCall):
            if tool_call.tool_name not in allowed_tools:
                return {
                    "passed": False,
                    "message": f"Agent {agent_id} does not have permission for tool {tool_call.tool_name}",
                    "severity": "error",
                }
        
        return {
            "passed": True,
            "message": "Tool permissions valid",
            "severity": "info",
        }


class ConfidenceThresholdRule(ClinicalSafetyRule):
    """
    Rule that enforces minimum confidence thresholds.
    
    Recommendations with very low confidence should be flagged or rejected.
    """
    
    def __init__(self, min_confidence: float = 0.3):
        """
        Initialize rule.
        
        Args:
            min_confidence: Minimum confidence threshold (0.0-1.0)
        """
        self.min_confidence = min_confidence
    
    async def evaluate_clinical(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check confidence thresholds.
        
        Args:
            context: Context with recommendations
            
        Returns:
            Evaluation result
        """
        recommendations = context.get("recommendations", [])
        
        for rec in recommendations:
            if isinstance(rec, Recommendation):
                if rec.confidence_score < self.min_confidence:
                    return {
                        "passed": False,
                        "message": f"Recommendation has confidence {rec.confidence_score} below threshold {self.min_confidence}",
                        "severity": "warning",
                    }
        
        return {
            "passed": True,
            "message": "All recommendations meet confidence threshold",
            "severity": "info",
        }

