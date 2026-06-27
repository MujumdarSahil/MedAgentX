from typing import Any, Dict, List, Optional
import json

from medagentx.agents.base_template import SpecializedAgent
from medagentx.core.types import AgentConfig, AgentCapabilities
from medagentx.models.llm_engine import LLMPurpose


class DiagnosisSupportAgent(SpecializedAgent):
    """Supportive-only differential suggestions with evidence."""

    def __init__(
        self,
        config: AgentConfig,
        tool_registry: Optional[Any] = None,
        governance_engine: Optional[Any] = None,
        knowledge_base: Optional[Any] = None,
        capabilities: Optional[AgentCapabilities] = None,
        llm_engine: Optional[Any] = None,
    ):
        if config.description == "":
            config.description = "Supportive reasoning only; no definitive diagnosis."
        super().__init__(config, tool_registry, governance_engine, knowledge_base, capabilities=capabilities, llm_engine=llm_engine)

    async def plan(self, task: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate reasoning plan, optionally using LLM."""
        ctx = context or {}
        symptoms: List[str] = ctx.get("symptoms", [])
        
        # Try LLM for reasoning plan generation if available
        if self.llm_engine and self.llm_engine.is_available():
            try:
                prompt = f"""Generate a reasoning plan for supportive differential diagnosis review.
Symptoms: {', '.join(symptoms) if symptoms else 'general symptoms'}

Return ONLY a JSON object with this structure:
{{"steps": ["step1", "step2", ...], "reasoning": "brief explanation"}}

Remember: This is SUPPORTIVE reasoning only. Do not provide definitive diagnosis."""
                
                llm_response = await self.llm_engine.generate(
                    prompt=prompt,
                    purpose=LLMPurpose.REASONING_PLAN,
                    system_prompt="You are a medical reasoning assistant. Generate supportive reasoning plans only. Never provide definitive diagnosis.",
                    response_format={"type": "json_object"},
                )
                
                # Update LLM usage tracking
                self._last_llm_usage = {
                    "model": llm_response.get("model"),
                    "provider": self.llm_engine.provider.value,
                    "purpose": LLMPurpose.REASONING_PLAN.value,
                    "usage": llm_response.get("usage", {}),
                }
                
                # Parse structured output
                if llm_response.get("structured_output"):
                    structured = llm_response["structured_output"]
                    return {
                        "steps": structured.get("steps", ["review_input", "apply_rules", "prepare_output"]),
                        "reasoning": structured.get("reasoning", "LLM-generated reasoning plan"),
                    }
            except Exception as e:
                # Fallback to default plan
                pass
        
        # Fallback: default plan
        return {"steps": ["review_input", "apply_rules", "prepare_output"], "reasoning": f"Planning for {task}"}

    async def act(self, plan: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        ctx = context or {}
        symptoms: List[str] = ctx.get("symptoms", [])
        query = ", ".join(symptoms) if symptoms else "general symptoms"
        knowledge = await (self.knowledge_base.retrieve(query) if self.knowledge_base else [])
        evidence = [item.get("content", "") for item in knowledge]

        # Optionally use LLM for evidence summarization
        if self.llm_engine and self.llm_engine.is_available() and evidence:
            try:
                evidence_text = "\n".join(evidence[:5])  # Limit to top 5
                prompt = f"""Summarize the following clinical evidence for supportive reasoning.
Symptoms: {', '.join(symptoms)}
Evidence:
{evidence_text}

Return ONLY a JSON object with this structure:
{{"summary": "brief summary", "key_points": ["point1", "point2", ...]}}

Remember: This is SUPPORTIVE reasoning only. Do not provide definitive diagnosis."""
                
                llm_response = await self.llm_engine.generate(
                    prompt=prompt,
                    purpose=LLMPurpose.EVIDENCE_SUMMARIZATION,
                    system_prompt="You are a medical evidence summarizer. Summarize evidence for supportive reasoning only.",
                    response_format={"type": "json_object"},
                )
                
                # Update LLM usage tracking (merge with existing if any)
                if self._last_llm_usage:
                    # Multiple LLM calls in same agent execution
                    self._last_llm_usage["additional_calls"] = self._last_llm_usage.get("additional_calls", [])
                    self._last_llm_usage["additional_calls"].append({
                        "purpose": LLMPurpose.EVIDENCE_SUMMARIZATION.value,
                        "usage": llm_response.get("usage", {}),
                    })
                else:
                    self._last_llm_usage = {
                        "model": llm_response.get("model"),
                        "provider": self.llm_engine.provider.value,
                        "purpose": LLMPurpose.EVIDENCE_SUMMARIZATION.value,
                        "usage": llm_response.get("usage", {}),
                    }
                
                # Use LLM summary if available
                if llm_response.get("structured_output"):
                    structured = llm_response["structured_output"]
                    evidence = [structured.get("summary", "")] + structured.get("key_points", [])
            except Exception as e:
                # Fallback to original evidence
                pass

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

