from typing import Any, Dict, List, Optional

from medagentx.agents.base_template import SpecializedAgent
from medagentx.core.types import AgentConfig, AgentCapabilities


class RiskScorerAgent(SpecializedAgent):
    """Enhanced Risk Scoring Agent with numeric scores, evidence, confidence, and tool usage trace.
    
    This agent calculates numeric risk scores from structured symptoms and provides
    comprehensive risk assessment with evidence, confidence, and human-approval flags.
    """

    def __init__(
        self,
        config: AgentConfig,
        tool_registry: Optional[Any] = None,
        governance_engine: Optional[Any] = None,
        knowledge_base: Optional[Any] = None,
    ):
        if config.description == "":
            config.description = "Numeric risk scoring support only; no diagnosis or treatment."
        
        # Define safe capabilities: no diagnosis, no prescription, requires approval
        safe_capabilities = AgentCapabilities(
            can_diagnose=False,
            can_prescribe=False,
            can_use_tools=True,
            requires_human_approval=True,
        )
        
        super().__init__(config, tool_registry, governance_engine, knowledge_base, capabilities=safe_capabilities)

    async def analyze(self, input_data: Any) -> Dict[str, Any]:
        """
        Enhanced risk analysis with numeric scores, evidence, and tool usage.
        
        Args:
            input_data: Patient data (symptoms, age, BP, cholesterol, etc.)
            
        Returns:
            Comprehensive risk assessment result with evidence and confidence
        """
        tools_used: List[str] = []
        evidence: List[str] = []
        
        # Extract structured symptoms if available
        if isinstance(input_data, dict):
            symptoms = input_data.get("symptoms", [])
            if isinstance(symptoms, str):
                symptoms = [s.strip() for s in symptoms.split(",")]
            age = input_data.get("age", 50)
            systolic_bp = input_data.get("systolic_bp", input_data.get("bp", 120))
            cholesterol = input_data.get("cholesterol", 200)
            smoker = input_data.get("smoker", False)
            diabetes = input_data.get("diabetes", False)
            structured_symptoms = input_data.get("structured_symptoms", symptoms)
        else:
            # Try to extract from string or use defaults
            symptoms = []
            structured_symptoms = []
            age = 50
            systolic_bp = 120
            cholesterol = 200
            smoker = False
            diabetes = False
        
        # Calculate symptom-based risk score
        symptom_risk_score = 0
        symptom_evidence = []
        
        symptom_keywords_high_risk = {
            "chest pain": 3,
            "shortness of breath": 2,
            "dyspnea": 2,
            "syncope": 3,
            "fainting": 3,
            "seizure": 3,
            "convulsion": 3,
            "severe": 2,
            "acute": 1,
        }
        
        symptom_keywords_moderate_risk = {
            "fever": 1,
            "cough": 1,
            "headache": 1,
            "dizziness": 1,
            "nausea": 1,
            "fatigue": 1,
        }
        
        symptom_text = " ".join(structured_symptoms).lower() if structured_symptoms else ""
        if not symptom_text and isinstance(input_data, str):
            symptom_text = input_data.lower()
        
        for keyword, risk_value in symptom_keywords_high_risk.items():
            if keyword in symptom_text:
                symptom_risk_score += risk_value
                symptom_evidence.append(f"High-risk symptom keyword detected: '{keyword}' (risk value: {risk_value})")
        
        for keyword, risk_value in symptom_keywords_moderate_risk.items():
            if keyword in symptom_text:
                symptom_risk_score += risk_value
                symptom_evidence.append(f"Moderate-risk symptom keyword detected: '{keyword}' (risk value: {risk_value})")
        
        # Cardiovascular risk scoring (Framingham-like)
        cv_risk_score = 0
        cv_risk_factors = []
        cv_evidence = []
        
        if age >= 65:
            cv_risk_score += 2
            cv_risk_factors.append("Age ≥ 65")
            cv_evidence.append("Age ≥ 65 years (risk factor: +2 points)")
        elif age >= 55:
            cv_risk_score += 1
            cv_risk_factors.append("Age ≥ 55")
            cv_evidence.append("Age ≥ 55 years (risk factor: +1 point)")
        
        if systolic_bp >= 140:
            cv_risk_score += 2
            cv_risk_factors.append("Elevated BP")
            cv_evidence.append(f"Systolic BP ≥ 140 mmHg (current: {systolic_bp}, risk factor: +2 points)")
        elif systolic_bp >= 130:
            cv_risk_score += 1
            cv_risk_factors.append("Borderline BP")
            cv_evidence.append(f"Systolic BP ≥ 130 mmHg (current: {systolic_bp}, risk factor: +1 point)")
        
        if cholesterol >= 240:
            cv_risk_score += 2
            cv_risk_factors.append("High cholesterol")
            cv_evidence.append(f"Total cholesterol ≥ 240 mg/dL (current: {cholesterol}, risk factor: +2 points)")
        elif cholesterol >= 200:
            cv_risk_score += 1
            cv_risk_factors.append("Borderline cholesterol")
            cv_evidence.append(f"Total cholesterol ≥ 200 mg/dL (current: {cholesterol}, risk factor: +1 point)")
        
        if smoker:
            cv_risk_score += 2
            cv_risk_factors.append("Smoking")
            cv_evidence.append("Current smoking status (risk factor: +2 points)")
        
        if diabetes:
            cv_risk_score += 3
            cv_risk_factors.append("Diabetes")
            cv_evidence.append("Diabetes mellitus (risk factor: +3 points)")
        
        # Combine scores
        total_risk_score = symptom_risk_score + cv_risk_score
        max_possible_score = 20  # Theoretical maximum
        
        # Normalize to 0-100 scale
        normalized_score = min(100, (total_risk_score / max_possible_score) * 100)
        
        # Risk categories based on normalized score
        if normalized_score >= 70:
            risk_level = "High"
            risk_category = "HIGH_RISK"
            confidence = 0.80
        elif normalized_score >= 40:
            risk_level = "Moderate"
            risk_category = "MODERATE_RISK"
            confidence = 0.70
        else:
            risk_level = "Low"
            risk_category = "LOW_RISK"
            confidence = 0.75
        
        # Aggregate evidence
        all_evidence = symptom_evidence + cv_evidence
        if not all_evidence:
            all_evidence.append("No specific risk factors identified from provided data")
        
        # Calculate confidence based on data completeness
        data_completeness = 0.0
        if age > 0:
            data_completeness += 0.2
        if systolic_bp > 0:
            data_completeness += 0.2
        if cholesterol > 0:
            data_completeness += 0.2
        if structured_symptoms or symptom_text:
            data_completeness += 0.2
        if smoker is not None or diabetes is not None:
            data_completeness += 0.2
        
        # Adjust confidence based on data completeness
        confidence = min(0.95, confidence * (0.5 + data_completeness))
        
        return {
            "output": {
                "risk_score": round(total_risk_score, 2),
                "normalized_score": round(normalized_score, 2),
                "risk_level": risk_level,
                "risk_category": risk_category,
                "symptom_risk_score": round(symptom_risk_score, 2),
                "cardiovascular_risk_score": round(cv_risk_score, 2),
                "risk_factors": cv_risk_factors,
                "evidence": all_evidence,
                "recommendation": f"Supportive risk assessment suggests {risk_level.lower()} risk (score: {normalized_score:.1f}/100). Clinical evaluation recommended.",
                "disclaimer": "This is supportive information only. Not a diagnosis or treatment recommendation. Human approval required.",
                "requires_human_approval": True,
            },
            "confidence": round(confidence, 3),
            "reasoning": f"Calculated total risk score of {total_risk_score:.1f} (normalized: {normalized_score:.1f}/100) based on {len(cv_risk_factors)} cardiovascular factors and {len(symptom_evidence)} symptom-based indicators.",
            "tools_used": tools_used,
        }

    async def act(self, plan: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute risk assessment using analyze method with tool usage tracking.
        """
        ctx = context or {}
        input_data = ctx.get("patient_data", ctx.get("input", ctx.get("structured_symptoms", {})))
        
        # Use knowledge base if available for additional context
        if self.knowledge_base and isinstance(input_data, dict):
            symptoms = input_data.get("symptoms", [])
            if symptoms:
                symptom_text = ", ".join(symptoms) if isinstance(symptoms, list) else str(symptoms)
                try:
                    knowledge_results = await self.knowledge_base.retrieve(symptom_text, top_k=3)
                    if knowledge_results:
                        input_data["knowledge_context"] = knowledge_results
                except Exception:
                    pass
        
        # Use user-defined analyze method
        result = await self.analyze(input_data)
        
        return {
            "output": result["output"],
            "confidence": result["confidence"],
            "reasoning": result["reasoning"],
            "tools_used": result.get("tools_used", []),
        }
