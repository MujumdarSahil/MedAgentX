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
        risk_scorer = self.agents.get("risk_scorer")  # Optional risk scorer

        # Symptom structuring
        sym_input = {"args": symptoms_text, "context": {"raw_symptoms": symptoms_text}}
        sym_result = await symptom_agent.run(sym_input["args"], context=sym_input["context"])
        structured_symptoms = sym_result["output"].get("symptoms", [])
        self._audit("symptom_analyzer", sym_result)
        self._append_trace("symptom_analyzer", sym_input, sym_result, visualization_metadata={
            "step": 1,
            "step_name": "Symptom Analysis",
            "agent_type": "analyzer",
            "input_type": "free_text",
            "output_type": "structured_list",
        })

        # Supportive diagnosis reasoning with RAG evidence
        diag_input = {
            "args": f"Supportive review for symptoms: {symptoms_text}",
            "context": {"symptoms": structured_symptoms},
        }
        diag_result = await diagnosis_agent.run(diag_input["args"], context=diag_input["context"])
        conditions = diag_result["output"].get("conditions", [])
        evidence = diag_result["output"].get("evidence", [])
        self._audit("diagnosis_support", diag_result)
        self._append_trace("diagnosis_support", diag_input, diag_result, visualization_metadata={
            "step": 2,
            "step_name": "Diagnosis Support",
            "agent_type": "reasoning",
            "input_type": "structured_symptoms",
            "output_type": "conditions_with_evidence",
        })

        # Risk scoring (if risk scorer agent available)
        risk_result = None
        if risk_scorer:
            risk_input = {
                "args": "Calculate risk score",
                "context": {
                    "structured_symptoms": structured_symptoms,
                    "symptoms": structured_symptoms,
                    "patient_data": {"symptoms": structured_symptoms},
                },
            }
            risk_result = await risk_scorer.run(risk_input["args"], context=risk_input["context"])
            self._audit("risk_scorer", risk_result)
            self._append_trace("risk_scorer", risk_input, risk_result, visualization_metadata={
                "step": 3,
                "step_name": "Risk Assessment",
                "agent_type": "scorer",
                "input_type": "structured_symptoms",
                "output_type": "risk_scores",
            })

        # Coding suggestions (ICD-10 and CPT/HCPCS)
        coder_input = {
            "args": "Map to ICD-10 and CPT/HCPCS",
            "context": {"symptoms": structured_symptoms, "conditions": conditions},
        }
        coder_result = await coder_agent.run(coder_input["args"], context=coder_input["context"])
        codes = coder_result["output"].get("codes", [])
        coding_disclaimer = coder_result["output"].get("disclaimer")
        
        # Get CPT/HCPCS codes through tool registry
        cpt_hcpcs_codes = []
        if coder_agent.tool_registry:
            symptom_text = ", ".join(structured_symptoms) if structured_symptoms else symptoms_text
            try:
                # Try to get CPT/HCPCS codes from ICD10CodingTool's knowledge base
                icd10_tool = coder_agent.tool_registry.get_tool("icd10_coding")
                if icd10_tool and hasattr(icd10_tool, "knowledge_base"):
                    kb = icd10_tool.knowledge_base
                    if hasattr(kb, "search_cpt_hcpcs"):
                        cpt_hcpcs_codes = kb.search_cpt_hcpcs(symptom_text)
            except Exception:
                pass
        
        self._audit("medical_coder", coder_result)
        self._append_trace("medical_coder", coder_input, coder_result, visualization_metadata={
            "step": 4,
            "step_name": "Medical Coding",
            "agent_type": "coder",
            "input_type": "symptoms_and_conditions",
            "output_type": "icd10_cpt_codes",
        })

        # Aggregate confidence scores
        confidence_scores = [
            sym_result.get("confidence", 0.5),
            diag_result.get("confidence", 0.5),
            coder_result.get("confidence", 0.5),
        ]
        if risk_result:
            confidence_scores.append(risk_result.get("confidence", 0.5))
        
        aggregated_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.5

        # Governance enforcement
        response = {
            "structured_symptoms": structured_symptoms,
            "support": {
                "conditions": conditions,
                "evidence": evidence,
                "disclaimer": diag_result["output"].get("disclaimer", "Supportive reasoning only."),
                "confidence": diag_result.get("confidence"),
            },
            "coding": {
                "icd10_recommendations": codes,
                "cpt_hcpcs_recommendations": cpt_hcpcs_codes,
                "disclaimer": coding_disclaimer,
                "confidence": coder_result.get("confidence"),
            },
            "risk_assessment": risk_result["output"] if risk_result else None,
            "confidence": min(1.0, aggregated_confidence),
            "workflow_confidence": {
                "symptom_analyzer": sym_result.get("confidence", 0.5),
                "diagnosis_support": diag_result.get("confidence", 0.5),
                "medical_coder": coder_result.get("confidence", 0.5),
                "risk_scorer": risk_result.get("confidence", 0.5) if risk_result else None,
                "aggregated": min(1.0, aggregated_confidence),
            },
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
                visualization_metadata={
                    "step": 5,
                    "step_name": "Governance Check",
                    "agent_type": "governance",
                    "input_type": "workflow_output",
                    "output_type": "safety_validated",
                },
            )
        # Convert traces to dicts for JSON serialization
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

    def _append_trace(
        self,
        agent_name: str,
        input_payload: Any,
        result: Dict[str, Any],
        visualization_metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        evidence_field = None
        output_payload = result.get("output")
        if isinstance(output_payload, dict):
            evidence_field = output_payload.get("evidence") or output_payload.get("codes")
        
        # Create trace with optional visualization metadata
        trace = AgentTrace(
            agent_name=agent_name,
            input=input_payload,
            plan=result.get("plan"),
            tools_used=result.get("tools_used", []),
            evidence=evidence_field,
            output=output_payload,
            confidence=result.get("confidence"),
            visualization_metadata=visualization_metadata,
        )
        
        self.workflow_trace.append(trace)

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

