from datetime import datetime
import logging
from abc import ABC
from typing import Any, Dict, List, Optional

from medagentx.core.types import (
    AgentConfig,
    AgentMessage,
    AgentState,
    AgentStatus,
    MessageRole,
    Recommendation,
)

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Minimal ReAct-style base agent (rule-based, human-in-loop)."""

    def __init__(
        self,
        config: AgentConfig,
        tool_registry: Optional[Any] = None,
        governance_engine: Optional[Any] = None,
    ):
        self.config = config
        self.tool_registry = tool_registry
        self.governance_engine = governance_engine
        self.state = AgentState(agent_id=config.agent_id, status=AgentStatus.IDLE)

    async def plan(self, task: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return {"steps": ["review_input", "apply_rules", "prepare_output"], "reasoning": f"Planning for {task}"}

    async def act(self, plan: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return {"output": {}, "confidence": 0.5, "reasoning": "Base action placeholder"}

    async def reflect(self, action_result: Dict[str, Any]) -> Dict[str, Any]:
        return {"reflection": "Human approval required before use.", "requires_human_approval": True}

    async def run(self, task: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        self.state.status = AgentStatus.THINKING
        self.state.current_task = task
        self.state.messages.append(
            AgentMessage(role=MessageRole.USER, content=task, metadata=context or {})
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
        }

        self.state.status = AgentStatus.COMPLETED
        self.state.messages.append(
            AgentMessage(
                role=MessageRole.AGENT,
                content=str(output.get("output")),
                metadata={"confidence": output["confidence"]},
            )
        )
        self.state.last_updated = datetime.now()
        return output

    def add_recommendation(self, recommendation: Recommendation) -> None:
        self.state.recommendations.append(recommendation)

    def get_state(self) -> AgentState:
        return self.state

    def reset(self) -> None:
        self.state = AgentState(agent_id=self.config.agent_id, status=AgentStatus.IDLE)

