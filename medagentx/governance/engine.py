from typing import Any, Dict, List
from datetime import datetime

from medagentx.core.types import AgentCapabilities


class GovernanceException(Exception):
    """Raised when governance policy is violated."""
    pass


class GovernanceEngine:
    """Enforce safety: no direct diagnosis or treatment; always human approval."""

    def __init__(self):
        self.audit_log: List[Dict[str, Any]] = []

    def enforce(self, response: Dict[str, Any]) -> None:
        outputs = str(response)
        lower_out = outputs.lower()
        blocked_phrases = [
            "treatment",
            "prescribe",
            "definitive diagnosis",
            "final diagnosis",
            "confirmed disease",
            "treatment plan",
        ]
        for phrase in blocked_phrases:
            if phrase in lower_out:
                detail = f"Governance block: phrase '{phrase}' not allowed."
                self.audit_log.append(
                    {
                        "timestamp": datetime.now().isoformat(),
                        "event": "governance_block",
                        "reason": detail,
                    }
                )
                raise ValueError(detail)

        response["requires_human_approval"] = True
        self.audit_log.append(
            {"timestamp": datetime.now().isoformat(), "event": "governance_check", "result": "pass"}
        )

    def get_audit_log(self) -> List[Dict[str, Any]]:
        return self.audit_log

    def validate_agent(self, agent: Any, capabilities: AgentCapabilities) -> None:
        """
        Validate agent capabilities against governance policy.
        Hard-blocks: diagnosis, prescription, governance override.
        
        Args:
            agent: Agent instance to validate
            capabilities: Agent capabilities
            
        Raises:
            GovernanceException: If capabilities violate policy
        """
        violations = []
        
        # Hard-block: diagnosis capability
        if capabilities.can_diagnose:
            violations.append("Diagnosis capability is prohibited")
        
        # Hard-block: prescription capability
        if capabilities.can_prescribe:
            violations.append("Prescription capability is prohibited")
        
        # Hard-block: governance override (requires_human_approval must be True)
        if not capabilities.requires_human_approval:
            violations.append("Human approval requirement cannot be disabled")
        
        if violations:
            violation_msg = "; ".join(violations)
            agent_id = "unknown"
            if hasattr(agent, "config") and agent.config:
                agent_id = getattr(agent.config, "agent_id", "unknown")
            self.audit_log.append({
                "timestamp": datetime.now().isoformat(),
                "event": "governance_validation_failed",
                "agent_id": agent_id,
                "violations": violations,
            })
            raise GovernanceException(f"Governance block: {violation_msg}")
        
        agent_id = "unknown"
        if hasattr(agent, "config") and agent.config:
            agent_id = getattr(agent.config, "agent_id", "unknown")
        self.audit_log.append({
            "timestamp": datetime.now().isoformat(),
            "event": "governance_validation_passed",
            "agent_id": agent_id,
            "capabilities": {
                "can_diagnose": capabilities.can_diagnose,
                "can_prescribe": capabilities.can_prescribe,
                "can_use_tools": capabilities.can_use_tools,
                "requires_human_approval": capabilities.requires_human_approval,
            },
        })

