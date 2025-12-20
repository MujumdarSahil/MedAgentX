from dataclasses import asdict
from datetime import datetime
from typing import Any, Dict, List, Optional

from medagentx.core.types import AgentTrace
from medagentx.core.recommendation_engine import RecommendationEngine, RecommendationOutput
from medagentx.core.prediction_model import PredictionModel, PredictionOutput
from medagentx.core.mcp_registry import MCPRegistry
from medagentx.core.squad import SquadExecutor, SquadStep


class RecommendationWorkflow:
    """
    Sequential workflow: symptoms -> support -> coding -> governance.
    
    Extended in v1.7 to support:
    - Agents → RecommendationEngines → PredictionModels chaining
    - Squad execution integration
    - Enhanced confidence aggregation
    - Visualization-ready JSON execution traces
    """

    def __init__(
        self,
        workflow_id: str,
        agents: Dict[str, Any],
        governance_engine: Any,
        engines: Optional[Dict[str, RecommendationEngine]] = None,
        models: Optional[Dict[str, PredictionModel]] = None,
        mcp_registry: Optional[MCPRegistry] = None,
    ):
        self.workflow_id = workflow_id
        self.agents = agents
        self.engines = engines or {}
        self.models = models or {}
        self.governance_engine = governance_engine
        self.mcp_registry = mcp_registry
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
    
    async def run_extended(
        self,
        symptoms_text: str,
        use_engines: bool = False,
        use_models: bool = False,
    ) -> Dict[str, Any]:
        """
        Extended workflow execution with optional engines and models.
        
        Args:
            symptoms_text: Input symptoms text
            use_engines: Whether to use recommendation engines
            use_models: Whether to use prediction models
            
        Returns:
            Extended workflow result with engines and models outputs
        """
        # Run base workflow
        base_result = await self.run(symptoms_text)
        
        # Add engines if available
        if use_engines and self.engines:
            engine_outputs = {}
            for engine_id, engine in self.engines.items():
                if engine.is_available():
                    try:
                        clinical_context = {
                            "symptoms": base_result.get("structured_symptoms", []),
                            "conditions": base_result.get("support", {}).get("conditions", []),
                            "patient_data": {"symptoms": base_result.get("structured_symptoms", [])},
                        }
                        engine_result = await engine.recommend(clinical_context)
                        engine_outputs[engine_id] = {
                            "insights": engine_result.insights,
                            "risk_modifiers": engine_result.risk_modifiers,
                            "evidence": engine_result.evidence,
                            "confidence": engine_result.confidence,
                            "human_approval_required": engine_result.human_approval_required,
                        }
                        self._append_trace(
                            f"engine:{engine_id}",
                            {"args": "recommend", "context": clinical_context},
                            {
                                "output": engine_outputs[engine_id],
                                "confidence": engine_result.confidence,
                            },
                            visualization_metadata={
                                "step": len(self.workflow_trace) + 1,
                                "step_name": f"Engine: {engine_id}",
                                "agent_type": "engine",
                                "input_type": "clinical_context",
                                "output_type": "recommendations",
                            },
                        )
                    except Exception as e:
                        logger.error(f"Engine {engine_id} execution failed: {e}")
                        engine_outputs[engine_id] = {"error": str(e)}
            
            base_result["engines"] = engine_outputs
        
        # Add models if available
        if use_models and self.models:
            model_outputs = {}
            for model_id, model in self.models.items():
                if model.is_available():
                    try:
                        # Extract features from workflow result
                        features = {
                            "symptom_count": len(base_result.get("structured_symptoms", [])),
                            "condition_count": len(base_result.get("support", {}).get("conditions", [])),
                            "risk_score": base_result.get("risk_assessment", {}).get("total_risk_score", 0) if base_result.get("risk_assessment") else 0,
                        }
                        model_result = await model.predict(features)
                        model_outputs[model_id] = {
                            "probability": model_result.probability,
                            "confidence": model_result.confidence,
                            "explanation": model_result.explanation,
                            "evidence": model_result.evidence,
                            "human_approval_required": model_result.human_approval_required,
                        }
                        self._append_trace(
                            f"model:{model_id}",
                            {"args": "predict", "context": {"features": features}},
                            {
                                "output": model_outputs[model_id],
                                "confidence": model_result.confidence,
                            },
                            visualization_metadata={
                                "step": len(self.workflow_trace) + 1,
                                "step_name": f"Model: {model_id}",
                                "agent_type": "model",
                                "input_type": "features",
                                "output_type": "prediction",
                            },
                        )
                    except Exception as e:
                        logger.error(f"Model {model_id} execution failed: {e}")
                        model_outputs[model_id] = {"error": str(e)}
            
            base_result["models"] = model_outputs
        
        # Re-aggregate confidence with engines and models
        confidence_scores = [
            base_result.get("confidence", 0.5),
        ]
        if base_result.get("engines"):
            for engine_output in base_result["engines"].values():
                if isinstance(engine_output, dict) and "confidence" in engine_output:
                    confidence_scores.append(engine_output["confidence"])
        if base_result.get("models"):
            for model_output in base_result["models"].values():
                if isinstance(model_output, dict) and "confidence" in model_output:
                    confidence_scores.append(model_output["confidence"])
        
        base_result["aggregated_confidence"] = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.5
        base_result["workflow_confidence"]["aggregated"] = base_result["aggregated_confidence"]
        
        # Update trace
        base_result["trace"] = [asdict(event) for event in self.workflow_trace]
        
        return base_result
    
    async def run_squad(
        self,
        squad_id: str,
        initial_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute a squad workflow.
        
        Args:
            squad_id: Squad identifier
            initial_context: Initial clinical context
            
        Returns:
            Squad execution result
        """
        if not self.mcp_registry:
            raise ValueError("MCP registry required for squad execution")
        
        squad_definition = self.mcp_registry.get_squad(squad_id)
        if not squad_definition:
            raise ValueError(f"Squad {squad_id} not found")
        
        # Build execution graph from squad definition
        execution_graph = []
        for step_def in squad_definition.get("execution_graph", []):
            step = SquadStep(
                step_id=step_def["step_id"],
                step_type=step_def["step_type"],
                entity_id=step_def["entity_id"],
                role=step_def.get("role", ""),
                instructions=step_def.get("instructions", ""),
                dependencies=step_def.get("dependencies", []),
                input_mapping=step_def.get("input_mapping", {}),
            )
            execution_graph.append(step)
        
        # Create squad executor
        executor = SquadExecutor(
            squad_id=squad_id,
            execution_graph=execution_graph,
            mcp_registry=self.mcp_registry,
            governance_engine=self.governance_engine,
        )
        
        # Execute squad
        squad_result = await executor.execute(initial_context)
        
        # Convert to workflow result format
        result = {
            "squad_id": squad_id,
            "execution_id": squad_result.execution_id,
            "outputs": squad_result.outputs,
            "confidence": squad_result.aggregated_confidence,
            "requires_human_approval": squad_result.requires_human_approval,
            "trace": [asdict(event) for event in squad_result.execution_trace],
            "metadata": squad_result.metadata,
        }
        
        # Add to workflow trace
        self.workflow_trace.extend(squad_result.execution_trace)
        
        return result

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
        
        # Get LLM usage from agent if available
        llm_usage = result.get("llm_usage")
        agent = self.agents.get(agent_name)
        if agent and hasattr(agent, "get_last_llm_usage"):
            llm_usage = agent.get_last_llm_usage() or llm_usage
        
        # Create trace with optional visualization metadata and LLM usage
        trace = AgentTrace(
            agent_name=agent_name,
            input=input_payload,
            plan=result.get("plan"),
            tools_used=result.get("tools_used", []),
            evidence=evidence_field,
            output=output_payload,
            confidence=result.get("confidence"),
            visualization_metadata=visualization_metadata,
            llm_usage=llm_usage,
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

