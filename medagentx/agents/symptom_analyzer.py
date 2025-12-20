from typing import Any, Dict, Optional

from medagentx.agents.base_template import SpecializedAgent
from medagentx.core.types import AgentConfig


class SymptomAnalyzerAgent(SpecializedAgent):
    """Parse raw symptom text into a structured list (no diagnosis)."""

    def __init__(
        self,
        config: AgentConfig,
        tool_registry: Optional[Any] = None,
        governance_engine: Optional[Any] = None,
        knowledge_base: Optional[Any] = None,
    ):
        if config.description == "":
            config.description = "Symptom structuring only; no diagnosis."
        super().__init__(config, tool_registry, governance_engine, knowledge_base)

    async def act(self, plan: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        text = (context or {}).get("raw_symptoms", "")
        tokens = [s.strip().lower() for s in text.replace(";", ",").split(",") if s.strip()]
        output = {"symptoms": tokens, "note": "Structured for downstream support; not a diagnosis."}
        confidence = 0.6 if tokens else 0.3
        return {
            "output": output,
            "confidence": confidence,
            "reasoning": "Parsed free-text symptoms into a clean list.",
        }

