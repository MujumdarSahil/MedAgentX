from datetime import datetime
from typing import Any, Dict, List, Optional


class RecommendationWorkflow:
    """Sequential workflow: symptoms -> support -> coding -> governance."""

    def __init__(self, workflow_id: str, agents: Dict[str, Any], governance_engine: Any):
        self.workflow_id = workflow_id
        self.agents = agents
        self.governance_engine = governance_engine
        self.audit_log: List[Dict[str, Any]] = []

    async def run(self, symptoms_text: str) -> Dict[str, Any]:
        self.audit_log.clear()

        symptom_agent = self.agents["symptom_analyzer"]
        diagnosis_agent = self.agents["diagnosis_support"]
        coder_agent = self.agents["medical_coder"]

        # Symptom structuring
        sym_result = await symptom_agent.run(symptoms_text, context={"raw_symptoms": symptoms_text})
        structured_symptoms = sym_result["output"].get("symptoms", [])
        self._audit("symptom_analyzer", sym_result)

        # Supportive diagnosis reasoning with RAG evidence
        diag_result = await diagnosis_agent.run(
            f"Supportive review for symptoms: {symptoms_text}",
            context={"symptoms": structured_symptoms},
        )
        conditions = diag_result["output"].get("conditions", [])
        evidence = diag_result["output"].get("evidence", [])
        self._audit("diagnosis_support", diag_result)

        # Coding suggestions (ICD-10 MCP tool)
        coder_result = await coder_agent.run(
            "Map to ICD-10",
            context={"symptoms": structured_symptoms, "conditions": conditions},
        )
        codes = coder_result["output"].get("codes", [])
        self._audit("medical_coder", coder_result)

        # Governance enforcement
        response = {
            "recommendations": [
                {"type": "support", "conditions": conditions, "codes": codes, "disclaimer": "Not a diagnosis."}
            ],
            "evidence": evidence,
            "confidence": min(1.0, (sym_result["confidence"] + diag_result["confidence"]) / 2),
            "requires_human_approval": True,
            "audit_log": self.audit_log,
        }
        if self.governance_engine:
            self.governance_engine.enforce(response)
            self._audit("governance", {"output": "safety_checked"})
        return response

    def _audit(self, step: str, result: Dict[str, Any]) -> None:
        self.audit_log.append(
            {
                "step": step,
                "timestamp": datetime.now().isoformat(),
                "detail": result,
            }
        )

