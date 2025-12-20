from typing import Any, Dict, List, Optional

from medagentx.agents.base_template import SpecializedAgent
from medagentx.core.types import AgentConfig, AgentCapabilities


class RiskAssessorAgent(SpecializedAgent):
    """Cardiac Risk Scoring (support only) - Example doctor-created agent.
    
    This agent demonstrates how doctors can create custom agents with
    policy-constrained capabilities. It provides risk assessment support
    but cannot diagnose or prescribe.
    """

    def __init__(
        self,
        config: AgentConfig,
        tool_registry: Optional[Any] = None,
        governance_engine: Optional[Any] = None,
        knowledge_base: Optional[Any] = None,
    ):
        if config.description == "":
            config.description = "Cardiac risk scoring support only; no diagnosis or treatment."
        
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
        User-defined analysis: Cardiac risk scoring.
        
        Args:
            input_data: Patient data (age, BP, cholesterol, etc.)
            
        Returns:
            Risk assessment result
        """
        # Extract patient data
        if isinstance(input_data, dict):
            age = input_data.get("age", 50)
            systolic_bp = input_data.get("systolic_bp", 120)
            cholesterol = input_data.get("cholesterol", 200)
            smoker = input_data.get("smoker", False)
            diabetes = input_data.get("diabetes", False)
        else:
            # Default values if input is not structured
            age = 50
            systolic_bp = 120
            cholesterol = 200
            smoker = False
            diabetes = False
        
        # Simple risk scoring (Framingham-like)
        risk_score = 0
        risk_factors = []
        
        if age >= 65:
            risk_score += 2
            risk_factors.append("Age ≥ 65")
        elif age >= 55:
            risk_score += 1
            risk_factors.append("Age ≥ 55")
        
        if systolic_bp >= 140:
            risk_score += 2
            risk_factors.append("Elevated BP")
        elif systolic_bp >= 130:
            risk_score += 1
            risk_factors.append("Borderline BP")
        
        if cholesterol >= 240:
            risk_score += 2
            risk_factors.append("High cholesterol")
        elif cholesterol >= 200:
            risk_score += 1
            risk_factors.append("Borderline cholesterol")
        
        if smoker:
            risk_score += 2
            risk_factors.append("Smoking")
        
        if diabetes:
            risk_score += 3
            risk_factors.append("Diabetes")
        
        # Risk categories
        if risk_score >= 7:
            risk_level = "High"
            confidence = 0.75
        elif risk_score >= 4:
            risk_level = "Moderate"
            confidence = 0.65
        else:
            risk_level = "Low"
            confidence = 0.70
        
        return {
            "output": {
                "risk_score": risk_score,
                "risk_level": risk_level,
                "risk_factors": risk_factors,
                "recommendation": f"Supportive risk assessment suggests {risk_level.lower()} cardiac risk. Clinical evaluation recommended.",
                "disclaimer": "This is supportive information only. Not a diagnosis or treatment recommendation.",
            },
            "confidence": confidence,
            "reasoning": f"Calculated risk score of {risk_score} based on {len(risk_factors)} identified factors.",
        }

    async def act(self, plan: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute risk assessment using analyze method.
        """
        ctx = context or {}
        input_data = ctx.get("patient_data", ctx.get("input", {}))
        
        # Use user-defined analyze method
        result = await self.analyze(input_data)
        
        return {
            "output": result["output"],
            "confidence": result["confidence"],
            "reasoning": result["reasoning"],
        }
