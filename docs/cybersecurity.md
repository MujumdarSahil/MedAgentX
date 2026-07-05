# MedAgentX Cybersecurity & Hardening Documentation

This document describes the security controls, hardening measures, and threat mitigations implemented within the MedAgentX clinical decision-support platform.

---

## 1. Clinical Responsibility Firewall (CRF) Invariants
The core safety invariant of MedAgentX is that no clinical recommendation or diagnostic output can reach patient-facing or clinical action status without being signed/validated by a licensed clinician.

- **Immutable Metadata**: Once created, the responsibility metadata tag (defined in `medagentx.core.crf.ResponsibilityMetadata`) is frozen and cannot be mutated or changed directly.
- **Fail-Safe Transition Path**: All raw agent, engine, or squad workflow outputs are initially tagged as `AI_SUGGESTED`. They can only transition to `DOCTOR_VALIDATED` or `DOCTOR_OVERRIDDEN` through explicit doctor validation functions.
- **Bypass Protection**: The firewall checks `is_clinical_action_allowed()` before any recommendation is finalized.

---

## 2. API Authentication & Token Gating
All REST API endpoints are protected using OIDC/Keycloak-compatible JWT bearer tokens. 

- **Protected Routes**: `/api/agents`, `/api/agents/{agent_id}/execute`, `/api/recommend`, and all other agent execution and tool query routes reject requests lacking a valid, verified signature with `401 Unauthorized` or `403 Forbidden`.
- **Local Fallback**: A local OAuth2 password flow is supported under `/token` for test and local development.
- **Session Tokens in Tests**: Hardcoded tokens (e.g. `"mock-valid-token"`) are prohibited. Instead, the test suite setup generates a random per-session token in pytest fixture setup, injects it into the server state, and automatically resets it to `None` upon test teardown (using `yield` inside a `try/finally` block to ensure execution even on test failures).

---

## 3. Environment-Gated Evaluation Endpoints
To prevent exposure of administrative and debugging features in production deployments, specific testing and evaluation endpoints are strictly gated behind an environment variable.

- **Configuration**: Set the environment variable `EVAL_MODE=true` to enable the registration of these routes:
  - `POST /api/v1/analyze`: Legacy evaluation analysis route.
  - `POST /api/agents/{agent_id}/reset`: Clears agent message history to isolate multi-turn scenarios.
- **Production Safety**: If `EVAL_MODE` is not explicitly set to `"true"` (default behavior in staging and production), the server will not register these routes, causing requests to them to fail with a standard `404 Not Found` response.

---

## 4. Defense Against Data-Layer Forgery
An adversary might attempt a data-layer forgery by submitting forged metadata (e.g. `"responsibility_state": "DOCTOR_VALIDATED"`) inside request context payloads to bypass review prompts.

- **Context Scrubbing**: The API router automatically strips and rejects `responsibility_metadata` and `responsibility_state` keys from client-submitted context payloads before calling the agent execution layer.
- **CRF Overwrite Invariant**: In `ClinicalResponsibilityFirewall.enforce()`, if an output dict contains an existing `responsibility_metadata` field claiming to be `DOCTOR_VALIDATED` or `DOCTOR_OVERRIDDEN`, the tag is immediately identified as forged/invalid, rejected, logged, and overwritten with the default `AI_SUGGESTED` status.

---

## 5. Structured Audit Logging & LLM Guard Fail-Closed
- **LLM Guard Integration**: Scans all incoming prompts for PII and prompt injection. If prompt injection is detected, it raises a `ValueError` blocking execution.
- **Fail-Closed Fallback**: If the HuggingFace models fail to initialize (due to network drops or resource constraints), the system falls back to rule-based regex check filters, registers a distinct `"degraded_mode"` warning event in the structured audit logs, and sets `requires_human_approval = True` and `llm_guard_degraded = True` to mandate human review.
