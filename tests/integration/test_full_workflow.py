"""
Integration tests for full MedAgentX workflow execution.
Requires a running MedAgentX server at http://localhost:8000.

Run with:
    pytest tests/integration/test_full_workflow.py -v --integration
"""

import pytest


@pytest.mark.integration
def test_full_workflow_placeholder():
    """Placeholder — requires live server. Run with --integration flag."""
    pytest.skip("Integration tests require a live MedAgentX server. See EVALUATION.md.")
