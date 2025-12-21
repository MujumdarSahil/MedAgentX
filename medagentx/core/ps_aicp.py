"""
Patient-Specific AI Cognition Profiles (PS-AICP) for MedAgentX v2.0

Policy-based communication adaptation system.
Profiles affect ONLY communication style, tone, and explanation depth.
Profiles NEVER affect reasoning, predictions, recommendations, or capabilities.

Hard Safety Rules:
- PS-AICP must NEVER influence predictions
- PS-AICP must NEVER influence recommendations
- PS-AICP must NEVER influence risk scores
- PS-AICP must NEVER influence escalation logic
- PS-AICP controls phrasing ONLY
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class VerbosityLevel(str, Enum):
    """Communication verbosity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ReassuranceLevel(str, Enum):
    """Reassurance levels for patient communication."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class EvidenceDepth(str, Enum):
    """Depth of evidence explanation."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class PatientCognitionProfile(str, Enum):
    """Patient-Specific AI Cognition Profiles (policy-based, not medical diagnoses)."""
    ANXIOUS = "anxious"
    TECH_SAVVY = "tech_savvy"
    ELDERLY = "elderly"
    CHRONIC_CONDITION = "chronic_condition"
    DEFAULT = "default"


@dataclass(frozen=True)
class PS_AICPConfig:
    """
    Immutable PS-AICP configuration.
    
    This configuration affects ONLY patient-facing communication:
    - Verbosity (how much detail)
    - Reassurance (how much emotional support)
    - Jargon (technical terms allowed)
    - Evidence depth (how much scientific detail)
    - Longitudinal memory emphasis (references to past interactions)
    
    This configuration NEVER affects:
    - Clinical reasoning
    - Predictions
    - Recommendations
    - Risk scores
    - Escalation logic
    - Responsibility tags (CRF)
    """
    verbosity_level: VerbosityLevel = VerbosityLevel.MEDIUM
    reassurance_level: ReassuranceLevel = ReassuranceLevel.MEDIUM
    jargon_allowed: bool = True
    evidence_depth: EvidenceDepth = EvidenceDepth.MEDIUM
    longitudinal_memory_emphasis: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "verbosity_level": self.verbosity_level.value,
            "reassurance_level": self.reassurance_level.value,
            "jargon_allowed": self.jargon_allowed,
            "evidence_depth": self.evidence_depth.value,
            "longitudinal_memory_emphasis": self.longitudinal_memory_emphasis,
        }


class PS_AICPRegistry:
    """
    Registry for Patient-Specific AI Cognition Profiles.
    
    Profiles are policy-based communication adaptations.
    They are immutable during a session.
    """
    
    # Predefined profile configurations
    _PROFILES: Dict[PatientCognitionProfile, PS_AICPConfig] = {
        PatientCognitionProfile.ANXIOUS: PS_AICPConfig(
            verbosity_level=VerbosityLevel.HIGH,
            reassurance_level=ReassuranceLevel.HIGH,
            jargon_allowed=False,
            evidence_depth=EvidenceDepth.LOW,
            longitudinal_memory_emphasis=True,
        ),
        PatientCognitionProfile.TECH_SAVVY: PS_AICPConfig(
            verbosity_level=VerbosityLevel.HIGH,
            reassurance_level=ReassuranceLevel.LOW,
            jargon_allowed=True,
            evidence_depth=EvidenceDepth.HIGH,
            longitudinal_memory_emphasis=False,
        ),
        PatientCognitionProfile.ELDERLY: PS_AICPConfig(
            verbosity_level=VerbosityLevel.MEDIUM,
            reassurance_level=ReassuranceLevel.MEDIUM,
            jargon_allowed=False,
            evidence_depth=EvidenceDepth.LOW,
            longitudinal_memory_emphasis=True,
        ),
        PatientCognitionProfile.CHRONIC_CONDITION: PS_AICPConfig(
            verbosity_level=VerbosityLevel.MEDIUM,
            reassurance_level=ReassuranceLevel.MEDIUM,
            jargon_allowed=True,
            evidence_depth=EvidenceDepth.MEDIUM,
            longitudinal_memory_emphasis=True,
        ),
        PatientCognitionProfile.DEFAULT: PS_AICPConfig(
            verbosity_level=VerbosityLevel.MEDIUM,
            reassurance_level=ReassuranceLevel.MEDIUM,
            jargon_allowed=True,
            evidence_depth=EvidenceDepth.MEDIUM,
            longitudinal_memory_emphasis=False,
        ),
    }
    
    def __init__(self):
        """Initialize PS-AICP registry."""
        self._session_profiles: Dict[str, PatientCognitionProfile] = {}
        logger.info("PS-AICP Registry initialized")
    
    def set_profile(
        self,
        session_id: str,
        profile: PatientCognitionProfile,
    ) -> None:
        """
        Set profile for a session (immutable once set).
        
        Args:
            session_id: Session identifier
            profile: Profile to set
            
        Raises:
            ValueError: If profile already set for session
        """
        if session_id in self._session_profiles:
            raise ValueError(
                f"Profile already set for session {session_id}. "
                "Profiles are immutable during a session."
            )
        
        self._session_profiles[session_id] = profile
        logger.info(f"Set PS-AICP profile {profile.value} for session {session_id}")
    
    def get_profile(self, session_id: str) -> PS_AICPConfig:
        """
        Get profile configuration for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            PS-AICP configuration (defaults to DEFAULT if not set)
        """
        profile_enum = self._session_profiles.get(session_id, PatientCognitionProfile.DEFAULT)
        return self._PROFILES[profile_enum]
    
    def get_profile_enum(self, session_id: str) -> PatientCognitionProfile:
        """
        Get profile enum for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Profile enum (defaults to DEFAULT if not set)
        """
        return self._session_profiles.get(session_id, PatientCognitionProfile.DEFAULT)
    
    def has_profile(self, session_id: str) -> bool:
        """
        Check if session has a profile set.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if profile is set, False otherwise
        """
        return session_id in self._session_profiles
    
    def clear_session(self, session_id: str) -> None:
        """
        Clear profile for a session (for testing/cleanup).
        
        Args:
            session_id: Session identifier
        """
        if session_id in self._session_profiles:
            del self._session_profiles[session_id]
            logger.info(f"Cleared PS-AICP profile for session {session_id}")

