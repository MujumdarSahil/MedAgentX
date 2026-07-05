from datetime import datetime
import logging
from abc import ABC
from typing import Any, Dict, List, Optional, Union

from medagentx.core.types import (
    AgentConfig,
    AgentMessage,
    AgentState,
    AgentStatus,
    MessageRole,
    Recommendation,
    AgentCapabilities,
    AgentExecutionContext,
)
from medagentx.governance.engine import GovernanceException

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Minimal ReAct-style base agent (rule-based, human-in-loop)."""

    def __init__(
        self,
        config: AgentConfig,
        tool_registry: Optional[Any] = None,
        governance_engine: Optional[Any] = None,
        llm_engine: Optional[Any] = None,
    ):
        self.config = config
        self.tool_registry = tool_registry
        self.governance_engine = governance_engine
        self.llm_engine = llm_engine  # Optional LLM engine
        self.state = AgentState(agent_id=config.agent_id, status=AgentStatus.IDLE)
        self._last_llm_usage: Optional[Dict[str, Any]] = None  # Track LLM usage for trace

    async def plan(self, task: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        # Check capabilities if available
        if hasattr(self, "capabilities"):
            self._check_capabilities("plan", task, context)
        return {"steps": ["review_input", "apply_rules", "prepare_output"], "reasoning": f"Planning for {task}"}

    async def act(self, plan: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        # Check capabilities if available
        if hasattr(self, "capabilities"):
            self._check_capabilities("act", plan, context)
        return {"output": {}, "confidence": 0.5, "reasoning": "Base action placeholder"}
    
    def _check_capabilities(self, phase: str, data: Any, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Check capabilities during plan/act phases.
        Raises GovernanceException if violation detected.
        """
        if not hasattr(self, "capabilities"):
            return
        
        capabilities: AgentCapabilities = self.capabilities
        violations = []
        
        # Check for diagnosis attempts
        if not capabilities.can_diagnose:
            data_str = str(data).lower()
            if any(term in data_str for term in ["diagnose", "diagnosis", "definitive diagnosis", "patient has"]):
                violations.append(f"Diagnosis attempt detected in {phase}")
        
        # Check for prescription attempts
        if not capabilities.can_prescribe:
            data_str = str(data).lower()
            if any(term in data_str for term in ["prescribe", "prescription", "medication", "treatment"]):
                violations.append(f"Prescription attempt detected in {phase}")
        
        # Check tool usage
        if not capabilities.can_use_tools and context:
            if context.get("tool_calls") or context.get("tools_used"):
                violations.append(f"Tool usage not permitted in {phase}")
        
        if violations:
            violation_msg = "; ".join(violations)
            # Log to audit trace
            if self.governance_engine:
                self.governance_engine.audit_log.append({
                    "timestamp": datetime.now().isoformat(),
                    "event": "capability_violation",
                    "agent_id": self.config.agent_id,
                    "phase": phase,
                    "violations": violations,
                })
            raise GovernanceException(f"Capability violation in {phase}: {violation_msg}")

    async def reflect(self, action_result: Dict[str, Any]) -> Dict[str, Any]:
        return {"reflection": "Human approval required before use.", "requires_human_approval": True}

    async def run(self, task: str, context: Optional[Union[Dict[str, Any], AgentExecutionContext]] = None) -> Dict[str, Any]:
        from medagentx.core.telemetry import tracer, _task_hash
        
        if isinstance(context, dict):
            context = AgentExecutionContext(**context)
        elif context is None:
            context = AgentExecutionContext()

        # Log structured starting execution
        logger.info("Agent run execution started", extra={"agent_id": self.config.agent_id, "task": task})

        with tracer.start_as_current_span(f"agent_{self.config.agent_id}_run") as span:
            span.set_attribute("agent_id", self.config.agent_id)
            # Use a hash of the task to avoid PII leakage in span names
            span.set_attribute("task_hash", _task_hash(task))
            span.set_attribute("agent.type", type(self).__name__)

            # Pre-processing input scan with LLM Guard
            if self.governance_engine:
                self.governance_engine.scan_input(self.config.agent_id, task)
                # Route and handle prompt injection immediately
                if hasattr(self.governance_engine, "input_signals"):
                    flags = self.governance_engine.input_signals.get(self.config.agent_id, {})
                    if flags.get("injection_detected"):
                        detail = f"Governance block: Prompt injection detected on input to agent '{self.config.agent_id}'."
                        span.set_attribute("governance_violation", True)
                        span.set_attribute("governance_violation_reason", detail)
                        raise ValueError(detail)

            self.state.status = AgentStatus.THINKING
            self.state.current_task = task
            self._last_llm_usage = None  # Reset LLM usage tracking
            metadata_dict = context.model_dump(exclude_none=True) if isinstance(context, AgentExecutionContext) else (context or {})
            self.state.messages.append(
                AgentMessage(role=MessageRole.USER, content=task, metadata=metadata_dict)
            )

            plan = await self.plan(task, context)
            action_result = await self.act(plan, context)
            reflection = await self.reflect(action_result)

            output = {
                "output": action_result.get("output", {}),
                "confidence": float(action_result.get("confidence", 0.5)),
                "reasoning": " | ".join(
                    filter(None, [plan.get("reasoning"), action_result.get("reasoning"), reflection.get("reflection")])
                ),
                "requires_human_approval": True,
                "audit": [
                    {"step": "plan", "detail": plan},
                    {"step": "act", "detail": action_result},
                    {"step": "reflect", "detail": reflection},
                ],
                "llm_usage": self._last_llm_usage,  # Include LLM usage metadata
            }

            self.state.status = AgentStatus.COMPLETED
            self.state.messages.append(
                AgentMessage(
                    role=MessageRole.AGENT,
                    content=str(output.get("output")),
                    metadata={"confidence": output["confidence"], "llm_usage": self._last_llm_usage},
                )
            )
            self.state.last_updated = datetime.now()

            span.set_attribute("confidence", output["confidence"])

            # Emit LLM generation span for Langfuse prompt/completion tracking
            if self._last_llm_usage:
                with tracer.start_as_current_span(f"llm.{self.config.agent_id}.generation") as llm_span:
                    llm_span.set_attribute("llm.agent_id", self.config.agent_id)
                    model = self._last_llm_usage.get("model", "unknown")
                    llm_span.set_attribute("llm.model", str(model))
                    prompt_tokens = self._last_llm_usage.get("prompt_tokens", 0)
                    completion_tokens = self._last_llm_usage.get("completion_tokens", 0)
                    total_tokens = self._last_llm_usage.get("total_tokens", 0)
                    llm_span.set_attribute("llm.usage.prompt_tokens", int(prompt_tokens or 0))
                    llm_span.set_attribute("llm.usage.completion_tokens", int(completion_tokens or 0))
                    llm_span.set_attribute("llm.usage.total_tokens", int(total_tokens or 0))
                    llm_span.set_attribute("llm.confidence", output["confidence"])

            logger.info("Agent run execution completed", extra={"agent_id": self.config.agent_id, "confidence": output["confidence"]})

            return output
    
    def get_last_llm_usage(self) -> Optional[Dict[str, Any]]:
        """Get last LLM usage metadata for trace."""
        return self._last_llm_usage

    def add_recommendation(self, recommendation: Recommendation) -> None:
        self.state.recommendations.append(recommendation)

    def get_state(self) -> AgentState:
        return self.state

    def reset(self) -> None:
        self.state = AgentState(agent_id=self.config.agent_id, status=AgentStatus.IDLE)

