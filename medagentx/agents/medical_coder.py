from typing import Any, Dict, List, Optional

from medagentx.agents.base_template import SpecializedAgent
from medagentx.core.types import AgentConfig


class MedicalCoderAgent(SpecializedAgent):
    """Suggest ICD-10 style codes using the governance-safe tool."""

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
        symptom_text = ", ".join(symptoms)
        suggestions: List[Dict[str, Any]] = []
        tools_used: List[str] = []

        if self.tool_registry:
            try:
                tools_used.append("icd10_coding")
                suggestions = await self.tool_registry.execute_tool(
                    tool_name="icd10_coding",
                    arguments={"symptoms_text": symptom_text, "max_results": 5},
                )
            except Exception:
                suggestions = []

        formatted = [
            {
                "code": item.get("code"),
                "description": item.get("description"),
                "confidence": float(item.get("confidence", 0.55)),
                "evidence": item.get("evidence"),
                "matched_keywords": item.get("matched_keywords", []),
            }
            for item in suggestions
        ]

        disclaimer = (
            "ICD-10 coding suggestions only; not a diagnosis or billing decision. "
            "Requires clinician review and approval."
        )

        output = {
            "codes": formatted,
            "disclaimer": disclaimer,
            "evidence": [entry.get("evidence") for entry in formatted if entry.get("evidence")],
        }
        confidence = max([entry["confidence"] for entry in formatted], default=0.42)
        return {
            "output": output,
            "confidence": confidence,
            "reasoning": "Mapped structured symptoms to ICD-10 style codes via governed tool.",
            "tools_used": tools_used,
        }

