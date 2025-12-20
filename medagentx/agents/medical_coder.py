from typing import Any, Dict, List, Optional

from medagentx.agents.base_template import SpecializedAgent
from medagentx.core.types import AgentConfig
from medagentx.models.llm_engine import LLMPurpose


class MedicalCoderAgent(SpecializedAgent):
    """Suggest ICD-10 style codes using the governance-safe tool."""

    def __init__(
        self,
        config: AgentConfig,
        tool_registry: Optional[Any] = None,
        governance_engine: Optional[Any] = None,
        knowledge_base: Optional[Any] = None,
        llm_engine: Optional[Any] = None,
    ):
        if config.description == "":
            config.description = "Maps supportive findings to mock ICD-10 suggestions."
        super().__init__(config, tool_registry, governance_engine, knowledge_base, llm_engine=llm_engine)

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

        # Optionally use LLM for code explanation
        if self.llm_engine and self.llm_engine.is_available() and formatted:
            try:
                codes_text = "\n".join([f"{item['code']}: {item['description']}" for item in formatted[:3]])
                prompt = f"""Explain the following ICD-10/CPT codes in simple terms for clinical reference.
Codes:
{codes_text}

Return ONLY a JSON object with this structure:
{{"explanations": [{{"code": "code", "explanation": "brief explanation"}}, ...]}}

Remember: This is for explanation only, not diagnosis or treatment."""
                
                llm_response = await self.llm_engine.generate(
                    prompt=prompt,
                    purpose=LLMPurpose.CODE_EXPLANATION,
                    system_prompt="You are a medical coding assistant. Explain codes for clinical reference only.",
                    response_format={"type": "json_object"},
                )
                
                # Update LLM usage tracking
                self._last_llm_usage = {
                    "model": llm_response.get("model"),
                    "provider": self.llm_engine.provider.value,
                    "purpose": LLMPurpose.CODE_EXPLANATION.value,
                    "usage": llm_response.get("usage", {}),
                }
                
                # Add explanations to formatted codes if available
                if llm_response.get("structured_output"):
                    explanations = llm_response["structured_output"].get("explanations", [])
                    explanation_map = {exp.get("code"): exp.get("explanation") for exp in explanations}
                    for item in formatted:
                        if item["code"] in explanation_map:
                            item["llm_explanation"] = explanation_map[item["code"]]
            except Exception as e:
                # Fallback if LLM fails
                pass

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

