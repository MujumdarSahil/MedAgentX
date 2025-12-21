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
        
        # Blocked phrases that suggest actual recommendations
        # Note: We allow these words in negative contexts (e.g., "no treatment", "not treatment")
        blocked_phrases = [
            ("prescribe", None),  # Always block "prescribe" in any context
            ("definitive diagnosis", None),
            ("final diagnosis", None),
            ("confirmed disease", None),
            ("treatment plan", None),
            # For "treatment", check that it's not in a negative context
            ("treatment", ["no ", "not ", "does not", "do not", "cannot", "should not", "must not"]),
        ]
        
        for phrase, allowed_contexts in blocked_phrases:
            if phrase in lower_out:
                # If this phrase has allowed negative contexts, check for them
                if allowed_contexts:
                    # Check all occurrences of the phrase
                    phrase_pos = 0
                    found_blockable = False
                    while True:
                        phrase_pos = lower_out.find(phrase, phrase_pos)
                        if phrase_pos < 0:
                            break
                        
                        # Look for negative context before the phrase (up to 50 chars before for broader context)
                        context_start = max(0, phrase_pos - 50)
                        context = lower_out[context_start:phrase_pos]
                        
                        # Check if this occurrence is in a negative context
                        if not any(neg in context for neg in allowed_contexts):
                            # Found occurrence without negative context - this is blockable
                            found_blockable = True
                            break
                        
                        phrase_pos += len(phrase)
                    
                    # If all occurrences were in negative contexts, allow it
                    if not found_blockable:
                        continue
                
                # Phrase found and not in allowed negative context - block it
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

