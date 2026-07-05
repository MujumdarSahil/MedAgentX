#!/usr/bin/env python3
"""
Unit Tests for EVAL_MODE gating on FastAPI server.
"""

import sys
import os
import pytest
from fastapi.testclient import TestClient


def test_eval_mode_disabled_gating():
    """
    Confirm /api/v1/analyze and /api/agents/{agent_id}/reset return 404 when EVAL_MODE is not "true".
    """
    # Save original EVAL_MODE env var
    orig_eval_mode = os.environ.get("EVAL_MODE")
    
    # Force it to false
    os.environ["EVAL_MODE"] = "false"
    
    # Remove server from sys.modules to force reload with the new env var
    modules_to_reload = [m for m in sys.modules if m.startswith("medagentx.api.server")]
    saved_modules = {m: sys.modules[m] for m in modules_to_reload}
    for m in modules_to_reload:
        del sys.modules[m]
        
    try:
        # Re-import server and construct TestClient
        from medagentx.api.server import app
        
        client = TestClient(app)
        
        # 1. Verify /api/v1/analyze returns 404
        res1 = client.post("/api/v1/analyze", json={"user_input": "test"})
        assert res1.status_code == 404, f"Expected 404, got {res1.status_code}"
        
        # 2. Verify /api/agents/symptom_analyzer/reset returns 404
        res2 = client.post("/api/agents/symptom_analyzer/reset")
        assert res2.status_code == 404, f"Expected 404, got {res2.status_code}"
        
    finally:
        # Restore environment variable
        if orig_eval_mode is not None:
            os.environ["EVAL_MODE"] = orig_eval_mode
        else:
            if "EVAL_MODE" in os.environ:
                del os.environ["EVAL_MODE"]
            
        # Clear reloaded modules and restore original modules
        for m in list(sys.modules.keys()):
            if m.startswith("medagentx.api.server"):
                del sys.modules[m]
        for m, mod in saved_modules.items():
            sys.modules[m] = mod
