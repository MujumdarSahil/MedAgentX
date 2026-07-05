#!/usr/bin/env python3
"""
Unit Tests for REST API Authentication.
"""

from fastapi.testclient import TestClient
import pytest
from medagentx.api.server import app

client = TestClient(app)


def test_public_endpoints_accessible():
    """
    Test that root and health check endpoints remain public.
    """
    res = client.get("/api/health")
    assert res.status_code == 200
    json_res = res.json()
    assert json_res["status"] == "healthy"
    assert json_res["platform"] == "MedAgentX"
    assert json_res["chain_valid"] is True


def test_protected_endpoint_no_token():
    """
    Test that requesting a protected endpoint without authentication returns 401.
    """
    res = client.get("/api/agents")
    assert res.status_code == 401
    assert "Not authenticated" in res.json()["detail"]


def test_protected_endpoint_invalid_token():
    """
    Test that requesting a protected endpoint with an invalid token returns 401.
    """
    res = client.get("/api/agents", headers={"Authorization": "Bearer invalid-token"})
    assert res.status_code == 401
    assert "Could not validate credentials" in res.json()["detail"]


import secrets
import medagentx.api.server as server


@pytest.fixture
def setup_test_token():
    # Generate dynamic test token
    token = secrets.token_hex(16)
    server.TEST_TOKEN = token
    yield token
    # Reset back to None
    server.TEST_TOKEN = None


def test_protected_endpoint_dynamic_mock_token(setup_test_token):
    """
    Test that the dynamically injected test token successfully authenticates.
    """
    dynamic_token = setup_test_token
    res = client.get("/api/agents", headers={"Authorization": f"Bearer {dynamic_token}"})
    assert res.status_code == 200
    assert "agents" in res.json()


def test_literal_mock_token_rejected_outside_pytest():
    """
    Confirm that the literal string 'mock-valid-token' does NOT authenticate
    when not explicitly set as the active TEST_TOKEN.
    """
    # Force TEST_TOKEN to None (simulating normal operation)
    original = server.TEST_TOKEN
    server.TEST_TOKEN = None
    try:
        res = client.get("/api/agents", headers={"Authorization": "Bearer mock-valid-token"})
        assert res.status_code == 401
        assert "Could not validate credentials" in res.json()["detail"]
    finally:
        server.TEST_TOKEN = original


def test_token_endpoint_invalid_credentials():
    """
    Test that token endpoint rejects invalid login credentials with 400.
    """
    res = client.post("/token", data={"username": "wrong", "password": "wrong"})
    assert res.status_code == 400
    assert "Incorrect username or password" in res.json()["detail"]


def test_token_endpoint_valid_credentials_and_flow():
    """
    Test generating a token with valid login credentials and using it to authenticate.
    """
    # 1. Get token
    res = client.post("/token", data={"username": "admin", "password": "secret"})
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

    # 2. Authenticate using the generated token
    token = data["access_token"]
    res2 = client.get("/api/agents", headers={"Authorization": f"Bearer {token}"})
    assert res2.status_code == 200
    assert "agents" in res2.json()


def test_api_health_performance():
    """
    Verify that the /api/health endpoint executes extremely fast (<50ms)
    under repeated calls, indicating optimization works correctly.
    """
    import time
    
    # Run warmup iterations
    for _ in range(5):
        client.get("/api/health")
        
    start_time = time.perf_counter()
    iterations = 20
    for _ in range(iterations):
        res = client.get("/api/health")
        assert res.status_code == 200
        assert res.json()["status"] == "healthy"
    end_time = time.perf_counter()
    
    total_duration_ms = (end_time - start_time) * 1000
    average_duration_ms = total_duration_ms / iterations
    
    # Assert the average latency is well below 50ms
    assert average_duration_ms < 50.0


def test_fixture_cleanup_on_failure():
    """
    Simulate a failing test case and verify that TEST_TOKEN is still reset to None.
    """
    # We manually simulate the setup_test_token fixture generator lifecycle
    gen = setup_test_token.__wrapped__()
    try:
        token = next(gen)
        assert server.TEST_TOKEN == token
        # Simulate a test assertion failure
        raise AssertionError("Simulated test failure")
    except AssertionError:
        pass
    finally:
        # Complete the generator teardown
        try:
            next(gen)
        except StopIteration:
            pass
            
    # Verify that TEST_TOKEN was successfully reset to None
    assert server.TEST_TOKEN is None


def test_health_endpoint_tampering_503():
    """
    Force a chain tampering condition and confirm that /api/health returns
    HTTP 503 with status degraded and reason chain_integrity_failure.
    """
    # Simulating background validation failure
    server._full_chain_valid = False
    try:
        res = client.get("/api/health")
        assert res.status_code == 503
        data = res.json()
        assert data["status"] == "degraded"
        assert data["reason"] == "chain_integrity_failure"
    finally:
        # Restore state
        server._full_chain_valid = True
