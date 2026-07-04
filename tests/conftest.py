"""
pytest configuration for MedAgentX test suite.

Shared fixtures and test settings for unit and integration tests.
"""

import pytest


@pytest.fixture
def sample_clinical_context():
    """Standard clinical context fixture for tests."""
    return {
        "patient_age": 45,
        "sex": "M",
        "symptoms": ["chest pain", "shortness of breath"],
        "bp": "160/95",
        "hr": 110,
    }


@pytest.fixture
def sample_ai_output_text():
    """Safe AI output text (no governance violations)."""
    return (
        "Based on the symptoms described, this presentation is consistent with patterns "
        "associated with cardiac events. I strongly recommend immediate evaluation by an "
        "emergency physician. Clinician review is required before any clinical action."
    )


@pytest.fixture
def violating_output_text():
    """AI output text containing a governance violation."""
    return "The diagnosis is acute myocardial infarction. You should take aspirin immediately."
