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


def test_protected_endpoint_mock_token():
    """
    Test that the mock-valid-token successfully authenticates.
    """
    res = client.get("/api/agents", headers={"Authorization": "Bearer mock-valid-token"})
    assert res.status_code == 200
    assert "agents" in res.json()


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
