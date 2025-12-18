"""
Governance Engine for MedAgentX.

Enforces safety, compliance, and clinical governance rules.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import logging

from medagentx.governance.safety_rules import (
    SafetyRule,
    ClinicalSafetyRule,
    HumanApprovalRequiredRule,
    DisclaimerRequiredRule,
    ToolPermissionRule,
    ConfidenceThresholdRule,
)
from medagentx.core.types import ToolCall, Recommendation, AgentStatus

logger = logging.getLogger(__name__)


class GovernanceEngine:
    """
    Governance engine that enforces safety and compliance rules.
    
    Responsibilities:
    - Evaluate safety rules
    - Enforce clinical compliance
    - Check tool permissions
    - Validate recommendations
    - Audit logging
    """
    
    def __init__(self):
        """Initialize governance engine with default rules."""
        self._rules: List[SafetyRule] = []
        self._audit_log: List[Dict[str, Any]] = []
        
        # Add default clinical safety rules
        self.add_rule(HumanApprovalRequiredRule())
        self.add_rule(DisclaimerRequiredRule())
        self.add_rule(ConfidenceThresholdRule(min_confidence=0.3))
    
    def add_rule(self, rule: SafetyRule) -> None:
        """
        Add a safety rule.
        
        Args:
            rule: Safety rule to add
        """
        self._rules.append(rule)
        logger.info(f"Added safety rule: {type(rule).__name__}")
    
    def remove_rule(self, rule_type: type) -> None:
        """
        Remove a safety rule by type.
        
        Args:
            rule_type: Type of rule to remove
        """
        self._rules = [r for r in self._rules if not isinstance(r, rule_type)]
        logger.info(f"Removed safety rule: {rule_type.__name__}")
    
    async def evaluate_all_rules(
        self,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Evaluate all safety rules.
        
        Args:
            context: Context for rule evaluation
            
        Returns:
            Dict with:
                - all_passed: bool
                - results: List of individual rule results
                - errors: List of failed rules
                - warnings: List of warnings
        """
        results = []
        errors = []
        warnings = []
        
        for rule in self._rules:
            try:
                result = await rule.evaluate(context)
                results.append({
                    "rule": type(rule).__name__,
                    "result": result,
                })
                
                if not result.get("passed", False):
                    if result.get("severity") == "critical" or result.get("severity") == "error":
                        errors.append(result)
                    else:
                        warnings.append(result)
            except Exception as e:
                logger.error(f"Error evaluating rule {type(rule).__name__}: {e}", exc_info=True)
                errors.append({
                    "rule": type(rule).__name__,
                    "error": str(e),
                    "severity": "error",
                })
        
        all_passed = len(errors) == 0
        
        evaluation_result = {
            "all_passed": all_passed,
            "results": results,
            "errors": errors,
            "warnings": warnings,
            "timestamp": datetime.now(),
        }
        
        # Log to audit trail
        self._audit_log.append({
            "timestamp": datetime.now(),
            "type": "rule_evaluation",
            "result": evaluation_result,
            "context_summary": self._summarize_context(context),
        })
        
        return evaluation_result
    
    async def check_tool_permission(
        self,
        agent_id: str,
        tool_name: str,
        tool_call: ToolCall,
        allowed_tools: Optional[List[str]] = None,
    ) -> bool:
        """
        Check if an agent has permission to use a tool.
        
        Args:
            agent_id: Agent ID
            tool_name: Tool name
            tool_call: Tool call object
            allowed_tools: List of allowed tool names for this agent
            
        Returns:
            True if allowed, False otherwise
        """
        # Create tool permission rule for this check
        rule = ToolPermissionRule()
        
        context = {
            "agent_id": agent_id,
            "tool_call": tool_call,
            "allowed_tools": allowed_tools or [],
        }
        
        result = await rule.evaluate(context)
        
        # Log to audit trail
        self._audit_log.append({
            "timestamp": datetime.now(),
            "type": "tool_permission_check",
            "agent_id": agent_id,
            "tool_name": tool_name,
            "allowed": result.get("passed", False),
        })
        
        return result.get("passed", False)
    
    async def validate_recommendation(
        self,
        recommendation: Recommendation,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Validate a clinical recommendation.
        
        Args:
            recommendation: Recommendation to validate
            context: Additional context
            
        Returns:
            Validation result
        """
        eval_context = {
            "recommendations": [recommendation],
            "outputs": [recommendation.content],
            **(context or {}),
        }
        
        result = await self.evaluate_all_rules(eval_context)
        
        # Log to audit trail
        self._audit_log.append({
            "timestamp": datetime.now(),
            "type": "recommendation_validation",
            "recommendation_type": recommendation.recommendation_type,
            "confidence": recommendation.confidence_score,
            "validation_result": result,
        })
        
        return result
    
    def get_audit_log(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        log_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get audit log entries.
        
        Args:
            start_time: Start time filter
            end_time: End time filter
            log_type: Type filter (e.g., "tool_permission_check")
            
        Returns:
            List of audit log entries
        """
        filtered_logs = self._audit_log
        
        if start_time:
            filtered_logs = [log for log in filtered_logs if log["timestamp"] >= start_time]
        
        if end_time:
            filtered_logs = [log for log in filtered_logs if log["timestamp"] <= end_time]
        
        if log_type:
            filtered_logs = [log for log in filtered_logs if log.get("type") == log_type]
        
        return filtered_logs
    
    def _summarize_context(self, context: Dict[str, Any]) -> str:
        """Summarize context for audit logging."""
        keys = list(context.keys())
        return f"Keys: {', '.join(keys[:5])}"

