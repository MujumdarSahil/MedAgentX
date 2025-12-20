from dataclasses import asdict
from datetime import datetime
from typing import Any, Dict, List, Optional

from medagentx.core.types import AgentTrace


class RecommendationWorkflow:
    """Sequential workflow: symptoms -> support -> coding -> governance."""

    def __init__(self, workflow_id: str, agents: Dict[str, Any], governance_engine: Any):
        self.workflow_id = workflow_id
        self.agents = agents
        self.governance_engine = governance_engine
        self.audit_log: List[Dict[str, Any]] = []
        self.workflow_trace: List[AgentTrace] = []

    async def run(self, symptoms_text: str) -> Dict[str, Any]:
        self.audit_log.clear()
        self.workflow_trace = []

        symptom_agent = self.agents["symptom_analyzer"]
        diagnosis_agent = self.agents["diagnosis_support"]
        coder_agent = self.agents["medical_coder"]

        # Symptom structuring
        sym_input = {"args": symptoms_text, "context": {"raw_symptoms": symptoms_text}}
        sym_result = await symptom_agent.run(sym_input["args"], context=sym_input["context"])
        structured_symptoms = sym_result["output"].get("symptoms", [])
        self._audit("symptom_analyzer", sym_result)
        self._append_trace("symptom_analyzer", sym_input, sym_result)

        # Supportive diagnosis reasoning with RAG evidence
        diag_input = {
            "args": f"Supportive review for symptoms: {symptoms_text}",
            "context": {"symptoms": structured_symptoms},
        }
        diag_result = await diagnosis_agent.run(diag_input["args"], context=diag_input["context"])
        conditions = diag_result["output"].get("conditions", [])
        evidence = diag_result["output"].get("evidence", [])
        self._audit("diagnosis_support", diag_result)
        self._append_trace("diagnosis_support", diag_input, diag_result)

        # Coding suggestions (ICD-10 MCP tool)
        coder_input = {
            "args": "Map to ICD-10",
            "context": {"symptoms": structured_symptoms, "conditions": conditions},
        }
        coder_result = await coder_agent.run(coder_input["args"], context=coder_input["context"])
        codes = coder_result["output"].get("codes", [])
        self._audit("medical_coder", coder_result)
        self._append_trace("medical_coder", coder_input, coder_result)

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
            self._append_trace(
                "governance",
                {"args": "enforce", "context": {"workflow_id": self.workflow_id}},
                {"output": "safety_checked", "confidence": response.get("confidence")},
            )
        response["trace"] = [asdict(event) for event in self.workflow_trace]
        return response

    def _audit(self, step: str, result: Dict[str, Any]) -> None:
        self.audit_log.append(
            {
                "step": step,
                "timestamp": datetime.now().isoformat(),
                "detail": result,
            }
        )

    def _append_trace(self, agent_name: str, input_payload: Any, result: Dict[str, Any]) -> None:
        self.workflow_trace.append(
            AgentTrace(
                agent_name=agent_name,
                input=input_payload,
                plan=result.get("plan"),
                tools_used=result.get("tools_used", []),
                evidence=result.get("output", {}).get("evidence") if isinstance(result.get("output"), dict) else None,
                output=result.get("output"),
                confidence=result.get("confidence"),
            )
        )

    async def replay(self, trace: List[Dict[str, Any]]) -> Dict[str, Any]:
        results: List[Dict[str, Any]] = []
        success = True
        for event in trace:
            agent_name = event.get("agent_name")
            if agent_name not in self.agents:
                continue
            agent = self.agents[agent_name]
            input_payload = event.get("input", {})
            args = input_payload.get("args") if isinstance(input_payload, dict) else input_payload
            context = input_payload.get("context") if isinstance(input_payload, dict) else None
            replay_output = await agent.run(args, context=context)
            match = replay_output.get("output") == event.get("output")
            success = success and match
            results.append(
                {
                    "agent_name": agent_name,
                    "expected_output": event.get("output"),
                    "replay_output": replay_output.get("output"),
                    "match": match,
                }
            )
        return {"success": success, "details": results}

