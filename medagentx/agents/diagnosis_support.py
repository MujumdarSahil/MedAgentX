from typing import Any, Dict, List, Optional

from medagentx.agents.base_template import SpecializedAgent
from medagentx.core.types import AgentConfig


class DiagnosisSupportAgent(SpecializedAgent):
    """Supportive-only differential suggestions with evidence."""

    def __init__(
        self,
        config: AgentConfig,
        tool_registry: Optional[Any] = None,
        governance_engine: Optional[Any] = None,
        knowledge_base: Optional[Any] = None,
    ):
        if config.description == "":
            config.description = "Supportive reasoning only; no definitive diagnosis."
        super().__init__(config, tool_registry, governance_engine, knowledge_base)

    async def act(self, plan: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        ctx = context or {}
        symptoms: List[str] = ctx.get("symptoms", [])
        query = ", ".join(symptoms) if symptoms else "general symptoms"
        knowledge = await (self.knowledge_base.retrieve(query) if self.knowledge_base else [])
        evidence = [item.get("content", "") for item in knowledge]

        conditions = []
        if "cough" in query or "fever" in query:
            conditions.append("Upper respiratory infection")
            conditions.append("Influenza")
        if not conditions:
            conditions.append("Nonspecific presentation")

        statements = [
            f"{cond} may indicate involvement given symptoms: {', '.join(symptoms)}"
            for cond in conditions
        ]

        output = {
            "conditions": conditions,
            "statements": statements,
            "evidence": evidence,
            "disclaimer": "Support only; requires clinician confirmation.",
        }
        confidence = 0.55 if evidence else 0.45
        return {
            "output": output,
            "confidence": confidence,
            "reasoning": "Generated supportive possibilities without diagnostic conclusion.",
        }

