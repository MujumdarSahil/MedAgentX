"""
Clinical Responsibility Firewall (CRF) for MedAgentX v2.0

Enforces responsibility boundaries for all system outputs.
Every output must be tagged with responsibility level.
Responsibility can NEVER escalate automatically.
"""

from enum import Enum
from typing import Any, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ResponsibilityTag(str, Enum):
    """Responsibility tags for all outputs."""
    AI_SUGGESTED = "ai_suggested"  # AI-generated, not validated
    DOCTOR_VALIDATED = "doctor_validated"  # Doctor reviewed and approved
    DOCTOR_OVERRIDDEN = "doctor_overridden"  # Doctor replaced AI output


@dataclass
class ResponsibilityMetadata:
    """Immutable responsibility metadata."""
    tag: ResponsibilityTag
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    validated_by: Optional[str] = None  # Doctor/user ID if validated
    validation_timestamp: Optional[str] = None
    original_tag: Optional[str] = None  # Original tag before validation
    evidence: list = field(default_factory=list)  # Evidence supporting this tag
    
    def __post_init__(self):
        """Ensure immutability by freezing after creation."""
        # Mark as immutable
        self._frozen = True
    
    def __setattr__(self, name, value):
        """Prevent modification after creation."""
        if hasattr(self, '_frozen') and self._frozen:
            raise ValueError(f"ResponsibilityMetadata is immutable. Cannot modify {name}")
        super().__setattr__(name, value)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "tag": self.tag.value,
            "timestamp": self.timestamp,
            "validated_by": self.validated_by,
            "validation_timestamp": self.validation_timestamp,
            "original_tag": self.original_tag,
            "evidence": self.evidence,
        }
    
    def is_clinical_action_allowed(self) -> bool:
        """
        Check if clinical action is allowed based on this metadata.
        
        INVARIANT: No output can reach clinical action/use without passing
        through DOCTOR_VALIDATED (or DOCTOR_OVERRIDDEN). AI_SUGGESTED outputs
        can never be used for clinical action.
        """
        return self.tag in (ResponsibilityTag.DOCTOR_VALIDATED, ResponsibilityTag.DOCTOR_OVERRIDDEN)
    
    @classmethod
    def create_ai_suggested(cls, evidence: Optional[list] = None) -> "ResponsibilityMetadata":
        """Create AI_SUGGESTED metadata."""
        return cls(
            tag=ResponsibilityTag.AI_SUGGESTED,
            evidence=evidence or [],
        )
    
    @classmethod
    def create_doctor_validated(
        cls,
        validated_by: str,
        original_tag: Optional[str] = None,
        evidence: Optional[list] = None,
    ) -> "ResponsibilityMetadata":
        """Create DOCTOR_VALIDATED metadata."""
        return cls(
            tag=ResponsibilityTag.DOCTOR_VALIDATED,
            validated_by=validated_by,
            validation_timestamp=datetime.now().isoformat(),
            original_tag=original_tag,
            evidence=evidence or [],
        )
    
    @classmethod
    def create_doctor_overridden(
        cls,
        validated_by: str,
        original_tag: Optional[str] = None,
        evidence: Optional[list] = None,
    ) -> "ResponsibilityMetadata":
        """Create DOCTOR_OVERRIDDEN metadata."""
        return cls(
            tag=ResponsibilityTag.DOCTOR_OVERRIDDEN,
            validated_by=validated_by,
            validation_timestamp=datetime.now().isoformat(),
            original_tag=original_tag,
            evidence=evidence or [],
        )


class ClinicalResponsibilityFirewall:
    """
    Clinical Responsibility Firewall.
    
    Enforces that:
    1. All outputs are tagged with responsibility
    2. Responsibility never escalates automatically
    3. AI authority never increases (even with high confidence)
    4. All metadata is immutable and auditable
    """
    
    def __init__(self):
        """Initialize CRF."""
        self.audit_log: list = []
    
    def tag_output(
        self,
        output: Any,
        source: str,  # "agent", "engine", "model", "workflow", "squad"
        source_id: str,
        confidence: Optional[float] = None,
        evidence: Optional[list] = None,
    ) -> ResponsibilityMetadata:
        """
        Tag an output with responsibility metadata.
        
        Args:
            output: Output to tag
            source: Source type (agent, engine, model, workflow, squad)
            source_id: Source identifier
            confidence: Confidence score (0.0-1.0)
            evidence: Supporting evidence
            
        Returns:
            ResponsibilityMetadata with AI_SUGGESTED tag
        """
        # All outputs start as AI_SUGGESTED
        # Responsibility NEVER escalates automatically, even with high confidence
        metadata = ResponsibilityMetadata.create_ai_suggested(evidence=evidence or [])
        
        # Add source information to evidence
        metadata.evidence.append({
            "source": source,
            "source_id": source_id,
            "confidence": confidence,
            "timestamp": metadata.timestamp,
        })
        
        # Audit
        self._audit("tag_output", {
            "source": source,
            "source_id": source_id,
            "tag": metadata.tag.value,
            "confidence": confidence,
        })
        
        return metadata
    
    def validate_output(
        self,
        metadata: ResponsibilityMetadata,
        validated_by: str,
        action: str = "validate",  # "validate" or "override"
    ) -> ResponsibilityMetadata:
        """
        Validate or override an output (doctor action).
        
        Args:
            metadata: Original responsibility metadata
            validated_by: Doctor/user ID
            action: "validate" (approve) or "override" (replace)
            
        Returns:
            New ResponsibilityMetadata with DOCTOR_VALIDATED or DOCTOR_OVERRIDDEN tag
        """
        if action == "validate":
            new_metadata = ResponsibilityMetadata.create_doctor_validated(
                validated_by=validated_by,
                original_tag=metadata.tag.value,
                evidence=metadata.evidence.copy(),
            )
        elif action == "override":
            new_metadata = ResponsibilityMetadata.create_doctor_overridden(
                validated_by=validated_by,
                original_tag=metadata.tag.value,
                evidence=metadata.evidence.copy(),
            )
        else:
            raise ValueError(f"Invalid action: {action}. Must be 'validate' or 'override'")
        
        # Audit
        self._audit("validate_output", {
            "original_tag": metadata.tag.value,
            "new_tag": new_metadata.tag.value,
            "validated_by": validated_by,
            "action": action,
        })
        
        return new_metadata
    
    def check_output(self, output: Dict[str, Any], source: str, source_id: str) -> bool:
        """
        Check if output has proper responsibility tagging.
        
        Args:
            output: Output dictionary
            source: Source type
            source_id: Source identifier
            
        Returns:
            True if properly tagged, False otherwise
        """
        # Check for responsibility_metadata
        if "responsibility_metadata" not in output:
            logger.warning(f"Output from {source}:{source_id} missing responsibility_metadata")
            return False
        
        metadata = output["responsibility_metadata"]
        if not isinstance(metadata, (dict, ResponsibilityMetadata)):
            logger.warning(f"Output from {source}:{source_id} has invalid responsibility_metadata type")
            return False
        
        # If dict, check for required fields
        if isinstance(metadata, dict):
            if "tag" not in metadata:
                logger.warning(f"Output from {source}:{source_id} responsibility_metadata missing 'tag'")
                return False
        
        return True
    
    def enforce(self, output: Dict[str, Any], source: str, source_id: str) -> Dict[str, Any]:
        """
        Enforce CRF on output (add tag if missing).
        
        Args:
            output: Output dictionary
            source: Source type
            source_id: Source identifier
            
        Returns:
            Output with responsibility_metadata added
        """
        # Reject and force overwrite of forged doctor validation tags
        if "responsibility_metadata" in output:
            metadata = output["responsibility_metadata"]
            if isinstance(metadata, dict):
                tag_val = metadata.get("tag")
                if tag_val in [ResponsibilityTag.DOCTOR_VALIDATED.value, ResponsibilityTag.DOCTOR_OVERRIDDEN.value]:
                    logger.warning(f"Rejected forged doctor responsibility tag: {tag_val}")
                    output["responsibility_metadata"] = self.tag_output(
                        output,
                        source=source,
                        source_id=source_id,
                        confidence=output.get("confidence"),
                        evidence=output.get("evidence", []),
                    ).to_dict()
            elif hasattr(metadata, "tag"):
                tag_val = getattr(metadata, "tag")
                if tag_val in [ResponsibilityTag.DOCTOR_VALIDATED, ResponsibilityTag.DOCTOR_OVERRIDDEN]:
                    logger.warning(f"Rejected forged doctor responsibility tag object: {tag_val}")
                    output["responsibility_metadata"] = self.tag_output(
                        output,
                        source=source,
                        source_id=source_id,
                        confidence=output.get("confidence"),
                        evidence=output.get("evidence", []),
                    )

        # If already tagged, verify it's valid
        if "responsibility_metadata" in output:
            if not self.check_output(output, source, source_id):
                # Invalid tag, replace it
                logger.warning(f"Replacing invalid responsibility_metadata for {source}:{source_id}")
                output["responsibility_metadata"] = self.tag_output(
                    output,
                    source=source,
                    source_id=source_id,
                    confidence=output.get("confidence"),
                    evidence=output.get("evidence", []),
                ).to_dict()
        else:
            # Not tagged, add AI_SUGGESTED tag
            output["responsibility_metadata"] = self.tag_output(
                output,
                source=source,
                source_id=source_id,
                confidence=output.get("confidence"),
                evidence=output.get("evidence", []),
            ).to_dict()
        
        # Ensure human_approval_required is True
        output["human_approval_required"] = True
        
        return output
    
    def _audit(self, event: str, data: Dict[str, Any]) -> None:
        """Log CRF event to audit log."""
        self.audit_log.append({
            "timestamp": datetime.now().isoformat(),
            "event": event,
            **data,
        })

    def is_clinical_action_allowed(self, output: Dict[str, Any]) -> bool:
        """
        Check if clinical action is allowed for the given output.
        
        INVARIANT: No output can reach clinical action/use without passing
        through DOCTOR_VALIDATED (or DOCTOR_OVERRIDDEN). AI_SUGGESTED outputs
        can never be used for clinical action.
        """
        if "responsibility_metadata" not in output:
            return False
        meta = output["responsibility_metadata"]
        if isinstance(meta, dict):
            tag = meta.get("tag")
            return tag in (ResponsibilityTag.DOCTOR_VALIDATED.value, ResponsibilityTag.DOCTOR_OVERRIDDEN.value)
        elif hasattr(meta, "tag"):
            return meta.tag in (ResponsibilityTag.DOCTOR_VALIDATED, ResponsibilityTag.DOCTOR_OVERRIDDEN)
        return False

