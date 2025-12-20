from typing import Any, Dict, Optional
import json

from medagentx.agents.base_template import SpecializedAgent
from medagentx.core.types import AgentConfig
from medagentx.models.llm_engine import LLMPurpose

class SymptomAnalyzerAgent(SpecializedAgent):
    """Parse raw symptom text into a structured list (no diagnosis)."""

    def __init__(
        self,
        config: AgentConfig,
        tool_registry: Optional[Any] = None,
        governance_engine: Optional[Any] = None,
        knowledge_base: Optional[Any] = None,
        llm_engine: Optional[Any] = None,
    ):
        if config.description == "":
            config.description = "Symptom structuring only; no diagnosis."
        super().__init__(config, tool_registry, governance_engine, knowledge_base, llm_engine=llm_engine)

    async def act(self, plan: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        text = (context or {}).get("raw_symptoms", "")
        
        # Try LLM for symptom normalization if available
        if self.llm_engine and self.llm_engine.is_available():
            try:
                prompt = f"""Normalize and structure the following symptoms into a clean JSON list.
Input: {text}

Return ONLY a JSON object with this structure:
{{"symptoms": ["symptom1", "symptom2", ...]}}

Do not diagnose, only normalize symptom names."""
                
                llm_response = await self.llm_engine.generate(
                    prompt=prompt,
                    purpose=LLMPurpose.SYMPTOM_NORMALIZATION,
                    system_prompt="You are a medical symptom normalizer. Extract and normalize symptom names only. Do not diagnose.",
                    response_format={"type": "json_object"},
                )
                
                # Update LLM usage tracking
                self._last_llm_usage = {
                    "model": llm_response.get("model"),
                    "provider": self.llm_engine.provider.value,
                    "purpose": LLMPurpose.SYMPTOM_NORMALIZATION.value,
                    "usage": llm_response.get("usage", {}),
                }
                
                # Parse structured output
                if llm_response.get("structured_output"):
                    structured = llm_response["structured_output"]
                    tokens = structured.get("symptoms", [])
                    if tokens:
                        output = {"symptoms": tokens, "note": "Structured for downstream support; not a diagnosis."}
                        confidence = 0.7  # Higher confidence with LLM normalization
                        return {
                            "output": output,
                            "confidence": confidence,
                            "reasoning": "LLM-assisted symptom normalization.",
                        }
            except Exception as e:
                # Fallback to rule-based if LLM fails
                pass
        
        # Fallback: rule-based parsing
        tokens = [s.strip().lower() for s in text.replace(";", ",").split(",") if s.strip()]
        output = {"symptoms": tokens, "note": "Structured for downstream support; not a diagnosis."}
        confidence = 0.6 if tokens else 0.3
        return {
            "output": output,
            "confidence": confidence,
            "reasoning": "Parsed free-text symptoms into a clean list.",
        }

