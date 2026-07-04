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
        self.input_signals: Dict[str, Dict[str, Any]] = {}

    def scan_input(self, agent_id: str, prompt: str) -> None:
        """
        Scan prompt using LLM Guard for PII and Prompt Injection.
        Routes flags into the governance engine audit log and active signal state.
        """
        pii_detected = False
        injection_detected = False
        degraded_mode = False
        
        try:
            # Note: Importing these here keeps them local
            from llm_guard.input_scanners import Anonymize, PromptInjection
            from llm_guard import scan_prompt
            
            scanners = [Anonymize(), PromptInjection()]
            sanitized_prompt, results_valid, results_score = scan_prompt(prompt, scanners)
            
            if not results_valid.get("Anonymize", True):
                pii_detected = True
            if not results_valid.get("PromptInjection", True):
                injection_detected = True
        except Exception as e:
            degraded_mode = True
            self.audit_log.append({
                "timestamp": datetime.now().isoformat(),
                "event": "degraded_mode",
                "agent_id": agent_id,
                "error": str(e),
                "detail": "LLM Guard failed to initialize. Falling back to rule-based scanner."
            })
            
            # Fallback scanner when model files are not local/cached or downloading fails
            import re
            email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
            phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
            ssn_pattern = r'\b\d{3}-\d{2}-\d{4}\b'
            
            if re.search(email_pattern, prompt) or re.search(phone_pattern, prompt) or re.search(ssn_pattern, prompt):
                pii_detected = True
            
            lower_prompt = prompt.lower()
            injection_indicators = [
                "ignore previous instructions",
                "ignore all instructions",
                "bypass safety",
                "system prompt",
                "forget what you were told",
                "you are now a",
                "new rules:",
            ]
            if any(indicator in lower_prompt for indicator in injection_indicators):
                injection_detected = True

        flags = {
            "pii_detected": pii_detected,
            "injection_detected": injection_detected,
            "degraded_mode": degraded_mode,
            "agent_id": agent_id,
        }
        
        self.input_signals[agent_id] = flags
        
        if pii_detected or injection_detected:
            self.audit_log.append({
                "timestamp": datetime.now().isoformat(),
                "event": "llm_guard_flagged",
                "agent_id": agent_id,
                "pii_detected": pii_detected,
                "injection_detected": injection_detected,
            })

    def enforce(self, response: Dict[str, Any]) -> None:
        from medagentx.core.telemetry import tracer
        
        with tracer.start_as_current_span("governance_enforce") as span:
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
                    span.set_attribute("governance_violated", True)
                    span.set_attribute("governance_violation_reason", detail)
                    self.audit_log.append(
                        {
                            "timestamp": datetime.now().isoformat(),
                            "event": "governance_block",
                            "reason": detail,
                        }
                    )
                    raise ValueError(detail)

            # Check input signals flagged by LLM Guard
            for agent_id, flags in list(self.input_signals.items()):
                if flags.get("injection_detected"):
                    detail = f"Governance block: Prompt injection detected on input to agent '{agent_id}'."
                    span.set_attribute("governance_violated", True)
                    span.set_attribute("governance_violation_reason", detail)
                    self.audit_log.append({
                        "timestamp": datetime.now().isoformat(),
                        "event": "governance_block",
                        "reason": detail,
                    })
                    # Clear signals after block
                    self.input_signals.clear()
                    raise ValueError(detail)
                if flags.get("pii_detected"):
                    # Feed it as additional signal in logs
                    self.audit_log.append({
                        "timestamp": datetime.now().isoformat(),
                        "event": "governance_pii_warning",
                        "reason": f"PII detected by LLM Guard in input to agent '{agent_id}'",
                    })
                if flags.get("degraded_mode"):
                    # Append warning to audit log
                    self.audit_log.append({
                        "timestamp": datetime.now().isoformat(),
                        "event": "governance_degraded_warning",
                        "reason": f"Input scanned in degraded mode (fallback rules) for agent '{agent_id}' due to LLM Guard initialization failure.",
                    })
                    response["requires_human_approval"] = True
                    if "metadata" not in response:
                        response["metadata"] = {}
                    response["metadata"]["llm_guard_degraded"] = True
                    response["metadata"]["requires_human_approval"] = True
            
            # Clear input signals after validation
            self.input_signals.clear()

            response["requires_human_approval"] = True
            self.audit_log.append(
                {"timestamp": datetime.now().isoformat(), "event": "governance_check", "result": "pass"}
            )
            span.set_attribute("governance_violated", False)

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

