#!/usr/bin/env python3
"""
Unit Tests for Output Guardrails Validation Layer.
"""

import pytest
from medagentx.core.output_guardrails import validate_agent_output
from medagentx.core.crf import ClinicalResponsibilityFirewall, ResponsibilityTag


def test_safe_output_passes():
    """
    Test that a normal, safe output passes guardrails.
    """
    output = {
        "output": {
            "explanation": "The patient presented with mild seasonal allergies. Avoid pollen."
        },
        "confidence": 0.9,
    }
    
    validated = validate_agent_output(output)
    
    assert validated["metadata"]["guardrails_passed"] is True
    assert "guardrails_warnings" not in validated["metadata"]


def test_risky_output_flagged():
    """
    Test that risky output containing forbidden definitive claims triggers warnings.
    """
    output = {
        "output": {
            "explanation": "I diagnose you with diabetes and you must take insulin immediately."
        },
        "confidence": 0.85,
    }
    
    validated = validate_agent_output(output)
    
    assert validated["metadata"]["guardrails_passed"] is False
    assert len(validated["metadata"]["guardrails_warnings"]) > 0
    assert "Fallback Guard" in validated["metadata"]["guardrails_warnings"][0]


def test_crf_remains_sole_enforcer():
    """
    Test that Guardrails AI does not override the CRF state machine.
    Even if output fails guardrails, CRF remains the transition and tagging authority.
    """
    firewall = ClinicalResponsibilityFirewall()
    
    # Risky output
    output = {
        "output": {
            "explanation": "I diagnose you with acute appendicitis."
        },
        "confidence": 0.9,
    }
    
    # Validate with guardrails first
    validated = validate_agent_output(output)
    assert validated["metadata"]["guardrails_passed"] is False
    
    # Run through CRF enforce next
    enforced = firewall.enforce(validated, source="agent", source_id="diagnosis_support")
    
    # Check that CRF enforced tagging is still AI_SUGGESTED
    assert enforced["responsibility_metadata"]["tag"] == ResponsibilityTag.AI_SUGGESTED.value
    assert enforced["human_approval_required"] is True
    
    # Verify that transitioning via CRF validate_output works even for flagged inputs
    meta_dict = enforced["responsibility_metadata"]
    from medagentx.core.crf import ResponsibilityMetadata
    meta = ResponsibilityMetadata(
        tag=ResponsibilityTag(meta_dict["tag"]),
        timestamp=meta_dict["timestamp"],
        validated_by=meta_dict["validated_by"],
        validation_timestamp=meta_dict["validation_timestamp"],
        original_tag=meta_dict["original_tag"],
        evidence=meta_dict["evidence"]
    )
    
    new_meta = firewall.validate_output(meta, validated_by="dr_smith", action="validate")
    assert new_meta.tag == ResponsibilityTag.DOCTOR_VALIDATED
    assert new_meta.is_clinical_action_allowed() is True
