from typing import Any, Dict, List, Optional

from medagentx.agents.base_template import SpecializedAgent
from medagentx.core.types import AgentConfig


class MedicalCoderAgent(SpecializedAgent):
    """Suggest ICD-10 style codes using the MCP lookup tool."""

    def __init__(
        self,
        config: AgentConfig,
        tool_registry: Optional[Any] = None,
        governance_engine: Optional[Any] = None,
        knowledge_base: Optional[Any] = None,
    ):
        if config.description == "":
            config.description = "Maps supportive findings to mock ICD-10 suggestions."
        super().__init__(config, tool_registry, governance_engine, knowledge_base)

    async def act(self, plan: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        ctx = context or {}
        symptoms: List[str] = ctx.get("symptoms", [])
        codes: List[Dict[str, Any]] = []
        if self.tool_registry:
            try:
                codes = await self.tool_registry.execute_tool(
                    tool_name="lookup_icd10",
                    arguments={"symptoms": symptoms},
                )
            except Exception:
                codes = []

        formatted = [
            {
                "code": item.get("code"),
                "description": item.get("description"),
                "confidence": 0.72,
                "justification": f"Based on symptoms: {', '.join(symptoms)}",
            }
            for item in codes
        ]

        output = {
            "codes": formatted,
            "note": "Suggestions only; verify with official ICD-10 guidance.",
        }
        confidence = 0.6 if formatted else 0.4
        return {
            "output": output,
            "confidence": confidence,
            "reasoning": "Mapped symptoms to mock ICD-10 codes via MCP tool.",
        }

