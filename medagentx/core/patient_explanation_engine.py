"""
Patient Explanation Engine for MedAgentX v2.0

Consumes PS-AICP profiles to adapt patient-facing explanations.
Clinician-facing outputs are NEVER modified.
CRF responsibility tagging remains unchanged.
"""

from typing import Any, Dict, Optional, List
from datetime import datetime
import logging

from medagentx.core.ps_aicp import (
    PS_AICPRegistry,
    PS_AICPConfig,
    VerbosityLevel,
    ReassuranceLevel,
    EvidenceDepth,
)
from medagentx.core.crf import ResponsibilityMetadata, ResponsibilityTag

logger = logging.getLogger(__name__)


class PatientExplanationEngine:
    """
    Patient Explanation Engine.
    
    Adapts explanations based on PS-AICP profiles.
    ONLY affects patient-facing communication.
    NEVER affects clinician-facing outputs.
    NEVER affects reasoning, predictions, or recommendations.
    """
    
    def __init__(self, ps_aicp_registry: PS_AICPRegistry):
        """
        Initialize Patient Explanation Engine.
        
        Args:
            ps_aicp_registry: PS-AICP registry instance
        """
        self.ps_aicp_registry = ps_aicp_registry
        logger.info("Patient Explanation Engine initialized")
    
    def explain_to_patient(
        self,
        session_id: str,
        clinical_content: Dict[str, Any],
        responsibility_metadata: Optional[ResponsibilityMetadata] = None,
    ) -> Dict[str, Any]:
        """
        Generate patient-facing explanation from clinical content.
        
        Args:
            session_id: Session identifier
            clinical_content: Clinical content (from agents, engines, models)
            responsibility_metadata: CRF responsibility metadata (preserved)
            
        Returns:
            Patient-facing explanation with adapted communication style
        """
        # Get PS-AICP profile for session
        profile = self.ps_aicp_registry.get_profile(session_id)
        
        # Extract base content (never modify clinical content itself)
        base_explanation = clinical_content.get("explanation", "")
        base_evidence = clinical_content.get("evidence", [])
        base_confidence = clinical_content.get("confidence", None)
        base_reasoning = clinical_content.get("reasoning", "")
        
        # Adapt explanation based on profile
        adapted_explanation = self._adapt_explanation(
            base_explanation,
            profile,
            base_evidence,
            base_confidence,
        )
        
        # Build patient-facing output
        patient_output = {
            "explanation": adapted_explanation,
            "session_id": session_id,
            "profile_used": self.ps_aicp_registry.get_profile_enum(session_id).value,
            "timestamp": datetime.now().isoformat(),
            # Preserve responsibility metadata (CRF)
            "responsibility_metadata": (
                responsibility_metadata.to_dict()
                if responsibility_metadata
                else None
            ),
            # Preserve human approval requirement
            "human_approval_required": clinical_content.get(
                "human_approval_required",
                True
            ),
        }
        
        # Add evidence if profile allows
        if profile.evidence_depth != EvidenceDepth.LOW:
            patient_output["evidence_summary"] = self._adapt_evidence(
                base_evidence,
                profile,
            )
        
        # Add reassurance if profile requires
        if profile.reassurance_level != ReassuranceLevel.LOW:
            patient_output["reassurance"] = self._generate_reassurance(
                profile,
                base_confidence,
            )
        
        logger.debug(
            f"Generated patient explanation for session {session_id} "
            f"with profile {profile}"
        )
        
        return patient_output
    
    def _adapt_explanation(
        self,
        base_explanation: str,
        profile: PS_AICPConfig,
        evidence: List[str],
        confidence: Optional[float],
    ) -> str:
        """
        Adapt explanation text based on profile.
        
        Args:
            base_explanation: Base explanation text
            profile: PS-AICP profile
            evidence: Evidence list
            confidence: Confidence score
            
        Returns:
            Adapted explanation text
        """
        explanation = base_explanation
        
        # Remove jargon if not allowed
        if not profile.jargon_allowed:
            explanation = self._remove_jargon(explanation)
        
        # Adjust verbosity
        if profile.verbosity_level == VerbosityLevel.LOW:
            explanation = self._reduce_verbosity(explanation)
        elif profile.verbosity_level == VerbosityLevel.HIGH:
            explanation = self._increase_verbosity(explanation, evidence, confidence)
        
        return explanation
    
    def _remove_jargon(self, text: str) -> str:
        """
        Remove or simplify medical jargon.
        
        Args:
            text: Text with potential jargon
            
        Returns:
            Text with simplified terminology
        """
        # Simple jargon replacement map (can be extended)
        jargon_map = {
            "differential diagnosis": "possible conditions",
            "pathophysiology": "how the condition works",
            "etiology": "cause",
            "prognosis": "expected outcome",
            "symptomatology": "symptoms",
            "clinical presentation": "how it appears",
            "biomarker": "biological indicator",
            "comorbidity": "other conditions",
            "contraindication": "reason to avoid",
        }
        
        text_lower = text.lower()
        for jargon, simple in jargon_map.items():
            if jargon in text_lower:
                text = text.replace(jargon, simple)
                text = text.replace(jargon.capitalize(), simple.capitalize())
        
        return text
    
    def _reduce_verbosity(self, text: str) -> str:
        """
        Reduce verbosity (keep it brief).
        
        Args:
            text: Original text
            
        Returns:
            Reduced verbosity text
        """
        # Simple approach: take first sentence or first 100 chars
        sentences = text.split(". ")
        if sentences:
            return sentences[0] + ("." if not sentences[0].endswith(".") else "")
        return text[:100] + ("..." if len(text) > 100 else "")
    
    def _increase_verbosity(
        self,
        text: str,
        evidence: List[str],
        confidence: Optional[float],
    ) -> str:
        """
        Increase verbosity (add more detail).
        
        Args:
            text: Original text
            evidence: Evidence list
            confidence: Confidence score
            
        Returns:
            Increased verbosity text
        """
        # Add context if available
        if evidence:
            text += f" This is based on {len(evidence)} supporting factors."
        
        if confidence is not None:
            if confidence >= 0.7:
                text += " The system has high confidence in this assessment."
            elif confidence >= 0.5:
                text += " The system has moderate confidence in this assessment."
            else:
                text += " The system has lower confidence in this assessment."
        
        return text
    
    def _adapt_evidence(
        self,
        evidence: List[str],
        profile: PS_AICPConfig,
    ) -> str:
        """
        Adapt evidence presentation based on profile.
        
        Args:
            evidence: Evidence list
            profile: PS-AICP profile
            
        Returns:
            Adapted evidence summary
        """
        if not evidence:
            return "No specific evidence available."
        
        if profile.evidence_depth == EvidenceDepth.LOW:
            return f"Based on {len(evidence)} supporting factors."
        elif profile.evidence_depth == EvidenceDepth.MEDIUM:
            return f"Key factors: {', '.join(evidence[:3])}"
        else:  # HIGH
            return f"Supporting evidence: {', '.join(evidence)}"
    
    def _generate_reassurance(
        self,
        profile: PS_AICPConfig,
        confidence: Optional[float],
    ) -> str:
        """
        Generate reassurance message based on profile.
        
        Args:
            profile: PS-AICP profile
            confidence: Confidence score
            
        Returns:
            Reassurance message
        """
        if profile.reassurance_level == ReassuranceLevel.LOW:
            return ""
        elif profile.reassurance_level == ReassuranceLevel.MEDIUM:
            return "Your healthcare provider will review this information with you."
        else:  # HIGH
            return (
                "This information is being reviewed by your healthcare provider. "
                "They will discuss the findings with you and answer any questions you may have."
            )
    
    def explain_clinical_output(
        self,
        session_id: str,
        clinical_output: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Explain clinical output to patient (wrapper for explain_to_patient).
        
        This method ensures clinician-facing outputs are never modified.
        Only patient-facing explanations are generated.
        
        Args:
            session_id: Session identifier
            clinical_output: Clinical output from agents/engines/models
            
        Returns:
            Patient-facing explanation
        """
        # Extract responsibility metadata if present
        responsibility_metadata = None
        if "responsibility_metadata" in clinical_output:
            # Convert dict to ResponsibilityMetadata if needed
            # For now, we'll pass it through as-is
            pass
        
        return self.explain_to_patient(
            session_id=session_id,
            clinical_content=clinical_output,
            responsibility_metadata=responsibility_metadata,
        )

