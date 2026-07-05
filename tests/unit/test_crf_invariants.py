#!/usr/bin/env python3
"""
Property-based Unit Tests for Clinical Responsibility Firewall (CRF) Invariants.
"""

import pytest
from hypothesis import given, strategies as st
from medagentx.core.crf import ResponsibilityMetadata, ResponsibilityTag, ClinicalResponsibilityFirewall


@given(st.lists(st.text()))
def test_ai_suggested_cannot_act(evidence):
    """
    Property: An AI_SUGGESTED output must never be allowed for clinical action.
    """
    meta = ResponsibilityMetadata.create_ai_suggested(evidence=evidence)
    assert meta.tag == ResponsibilityTag.AI_SUGGESTED
    assert meta.is_clinical_action_allowed() is False


@given(st.text(), st.lists(st.text()))
def test_doctor_validated_can_act(doctor_id, evidence):
    """
    Property: A DOCTOR_VALIDATED output is allowed for clinical action and has validator signature.
    """
    meta = ResponsibilityMetadata.create_ai_suggested(evidence=evidence)
    val_meta = ResponsibilityMetadata.create_doctor_validated(
        validated_by=doctor_id,
        original_tag=meta.tag.value,
        evidence=meta.evidence
    )
    assert val_meta.tag == ResponsibilityTag.DOCTOR_VALIDATED
    assert val_meta.validated_by == doctor_id
    assert val_meta.is_clinical_action_allowed() is True


@given(st.text(), st.lists(st.text()))
def test_doctor_overridden_can_act(doctor_id, evidence):
    """
    Property: A DOCTOR_OVERRIDDEN output is allowed for clinical action and has validator signature.
    """
    meta = ResponsibilityMetadata.create_ai_suggested(evidence=evidence)
    over_meta = ResponsibilityMetadata.create_doctor_overridden(
        validated_by=doctor_id,
        original_tag=meta.tag.value,
        evidence=meta.evidence
    )
    assert over_meta.tag == ResponsibilityTag.DOCTOR_OVERRIDDEN
    assert over_meta.validated_by == doctor_id
    assert over_meta.is_clinical_action_allowed() is True


@given(st.text(min_size=1), st.lists(st.text()))
def test_immutability_invariant(doctor_id, evidence):
    """
    Property: ResponsibilityMetadata attributes are frozen and cannot be directly modified.
    """
    meta = ResponsibilityMetadata.create_ai_suggested(evidence=evidence)
    with pytest.raises(ValueError):
        meta.tag = ResponsibilityTag.DOCTOR_VALIDATED

    val_meta = ResponsibilityMetadata.create_doctor_validated(
        validated_by=doctor_id,
        original_tag=meta.tag.value,
        evidence=meta.evidence
    )
    with pytest.raises(ValueError):
        val_meta.tag = ResponsibilityTag.AI_SUGGESTED

    with pytest.raises(ValueError):
        val_meta.validated_by = "another_doctor"


@given(st.text(), st.text(), st.floats(min_value=0.0, max_value=1.0), st.lists(st.text()))
def test_firewall_enforce_always_ai_suggested(source, source_id, confidence, evidence):
    """
    Property: ClinicalResponsibilityFirewall.enforce always tags raw/invalid outputs as AI_SUGGESTED
    and blocks clinical action, requiring human approval.
    """
    firewall = ClinicalResponsibilityFirewall()
    output = {
        "confidence": confidence,
        "evidence": evidence
    }
    enforced = firewall.enforce(output, source=source, source_id=source_id)
    assert firewall.is_clinical_action_allowed(enforced) is False
    assert enforced["responsibility_metadata"]["tag"] == ResponsibilityTag.AI_SUGGESTED.value
    assert enforced["human_approval_required"] is True


@given(st.text(), st.text(), st.text())
def test_firewall_validation_transitions(doctor_id, source, source_id):
    """
    Property: Transitioning outputs via validate_output successfully updates the tag and allows clinical action.
    """
    firewall = ClinicalResponsibilityFirewall()
    output = {}
    enforced = firewall.enforce(output, source=source, source_id=source_id)

    # Extract metadata dict
    meta_dict = enforced["responsibility_metadata"]
    meta = ResponsibilityMetadata(
        tag=ResponsibilityTag(meta_dict["tag"]),
        timestamp=meta_dict["timestamp"],
        validated_by=meta_dict["validated_by"],
        validation_timestamp=meta_dict["validation_timestamp"],
        original_tag=meta_dict["original_tag"],
        evidence=meta_dict["evidence"]
    )

    # Validate output transition
    new_meta = firewall.validate_output(meta, validated_by=doctor_id, action="validate")
    assert new_meta.tag == ResponsibilityTag.DOCTOR_VALIDATED
    assert new_meta.is_clinical_action_allowed() is True

    # Override transition
    over_meta = firewall.validate_output(meta, validated_by=doctor_id, action="override")
    assert over_meta.tag == ResponsibilityTag.DOCTOR_OVERRIDDEN
    assert over_meta.is_clinical_action_allowed() is True


@given(st.text(min_size=1), st.text(), st.text())
def test_firewall_positive_path_validated(doctor_id, source, source_id):
    """
    Property: An enforced output that is successfully validated by a doctor
    must return True for is_clinical_action_allowed().
    """
    firewall = ClinicalResponsibilityFirewall()
    output = {}
    enforced = firewall.enforce(output, source=source, source_id=source_id)
    
    # Transition to validated
    meta_dict = enforced["responsibility_metadata"]
    meta = ResponsibilityMetadata(
        tag=ResponsibilityTag(meta_dict["tag"]),
        timestamp=meta_dict["timestamp"],
        validated_by=meta_dict["validated_by"],
        validation_timestamp=meta_dict["validation_timestamp"],
        original_tag=meta_dict["original_tag"],
        evidence=meta_dict["evidence"]
    )
    new_meta = firewall.validate_output(meta, validated_by=doctor_id, action="validate")
    
    # Update enforced with the new metadata
    enforced["responsibility_metadata"] = new_meta.to_dict()
    assert firewall.is_clinical_action_allowed(enforced) is True


@given(st.text(min_size=1), st.text(), st.text())
def test_firewall_positive_path_overridden(doctor_id, source, source_id):
    """
    Property: An enforced output that is successfully overridden by a doctor
    must return True for is_clinical_action_allowed().
    """
    firewall = ClinicalResponsibilityFirewall()
    output = {}
    enforced = firewall.enforce(output, source=source, source_id=source_id)
    
    # Transition to overridden
    meta_dict = enforced["responsibility_metadata"]
    meta = ResponsibilityMetadata(
        tag=ResponsibilityTag(meta_dict["tag"]),
        timestamp=meta_dict["timestamp"],
        validated_by=meta_dict["validated_by"],
        validation_timestamp=meta_dict["validation_timestamp"],
        original_tag=meta_dict["original_tag"],
        evidence=meta_dict["evidence"]
    )
    new_meta = firewall.validate_output(meta, validated_by=doctor_id, action="override")
    
    # Update enforced with the new metadata
    enforced["responsibility_metadata"] = new_meta.to_dict()
    assert firewall.is_clinical_action_allowed(enforced) is True


def test_execution_context_forgery_prevention():
    """
    Test that unexpected/novel field names attempting responsibility forgery
    (both at the root level and nested inside dictionaries) are structurally
    ignored and excluded by AgentExecutionContext.
    """
    from medagentx.core.types import AgentExecutionContext
    
    payload = {
        "symptoms": ["cough"],
        "unexpected_novel_responsibility_field": "doctor_validated",
        "some_random_key": {"responsibility_tag": "doctor_validated"},
        "patient_context": {
            "age": 30,
            "forged_nested_responsibility_metadata": {"tag": "doctor_validated"},
        },
        "additional_metadata": {
            "custom_responsibility_override": "doctor_validated",
            "safe_meta": "safe"
        }
    }
    
    ctx = AgentExecutionContext(**payload)
    
    # Assert root-level extra fields are ignored
    assert not hasattr(ctx, "unexpected_novel_responsibility_field")
    assert not hasattr(ctx, "some_random_key")
    
    # Assert nested responsibility fields are stripped
    assert "forged_nested_responsibility_metadata" not in ctx.patient_context
    assert ctx.patient_context["age"] == 30
    
    # Assert additional_metadata responsibility fields are stripped
    assert "custom_responsibility_override" not in ctx.additional_metadata
    assert ctx.additional_metadata["safe_meta"] == "safe"
    
    # Assert model_dump excludes it structurally
    dumped = ctx.model_dump()
    assert "unexpected_novel_responsibility_field" not in dumped
    assert "some_random_key" not in dumped
    assert "forged_nested_responsibility_metadata" not in dumped["patient_context"]
    assert "custom_responsibility_override" not in dumped["additional_metadata"]
