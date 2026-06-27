# Safety & Compliance Guide

## Clinical Safety Disclaimer

**⚠️ IMPORTANT**: MedAgentX provides **clinical decision support**, NOT autonomous diagnosis.

- All outputs are **recommendations**, not final decisions
- Human (doctor) approval is **mandatory** before any diagnosis or treatment suggestion
- The system enforces this at the architecture level

## Safety Architecture

### Mandatory Safety Features

1. **Human Approval Gates**
   - All recommendations require human approval
   - Cannot be bypassed at the architecture level
   - Enforced by `HumanApprovalRequiredRule`

2. **Disclaimers**
   - All outputs must include appropriate disclaimers
   - Enforced by `DisclaimerRequiredRule`

3. **Confidence Thresholds**
   - Recommendations below threshold are flagged
   - Enforced by `ConfidenceThresholdRule`

4. **Tool Permissions**
   - Agents can only use tools they have permission for
   - Enforced by `ToolPermissionRule`

## Governance Engine

The governance engine evaluates all recommendations:

```python
from medagentx.governance import GovernanceEngine

governance = GovernanceEngine()

# Validate recommendation
validation = await governance.validate_recommendation(recommendation)
if not validation["all_passed"]:
    # Handle validation failures
    pass
```

## Custom Safety Rules

Create custom safety rules:

```python
from medagentx.governance.safety_rules import ClinicalSafetyRule

class MySafetyRule(ClinicalSafetyRule):
    async def evaluate_clinical(self, context: dict) -> dict:
        # Implement safety check
        return {
            "passed": True,
            "message": "Check passed",
            "severity": "info",
        }

# Add to governance engine
governance.add_rule(MySafetyRule())
```

## Audit Logging

All actions are logged for compliance:

```python
# Get audit log
audit_log = governance.get_audit_log(
    start_time=start_date,
    end_time=end_date,
    log_type="recommendation_validation",
)
```

## Compliance Considerations

### HIPAA-Friendly Architecture

- Audit logs track all actions
- Access control through tool permissions
- Data encryption support (implementation-specific)

### Decision Traceability

- All recommendations are versioned
- Approval/rejection tracked
- Full decision history maintained

### Human Oversight

- Mandatory approval gates
- Cannot be disabled
- Built into architecture

## Best Practices

1. **Always require human approval** for clinical decisions
2. **Include disclaimers** in all outputs
3. **Report confidence scores** honestly
4. **Provide evidence** for recommendations
5. **Log all actions** for audit trails
6. **Test safety rules** thoroughly
7. **Review audit logs** regularly

## Risk Mitigation

The platform includes multiple layers of risk mitigation:

1. **Architecture Level**: Human approval gates
2. **Rule Level**: Safety rules validate outputs
3. **Agent Level**: Self-critique and reflection
4. **Tool Level**: Permission checks
5. **Knowledge Level**: Evidence-based retrieval

## Regulatory & Clinical Safety Positioning

### Clinical Decision Support (CDS) Classification

MedAgentX is designed and positioned as **Clinical Decision Support (CDS) software**, not a diagnostic or treatment system. This classification is architecturally enforced and cannot be overridden.

**Key Distinctions**:

- **CDS (MedAgentX)**: Provides information, recommendations, and supportive reasoning to assist clinicians in making decisions
- **Diagnostic System**: Makes autonomous diagnostic determinations without human oversight
- **Treatment System**: Prescribes or administers treatments without human approval

MedAgentX explicitly does **not** perform diagnosis or treatment. All outputs are recommendations that require human clinician review and approval.

### Mandatory Human Approval Guarantees

MedAgentX enforces human approval at multiple architectural levels:

1. **Agent Capability Constraints**: All agents are initialized with `requires_human_approval=True`, which cannot be disabled without modifying source code
2. **Workflow-Level Enforcement**: The `RecommendationWorkflow` sets `requires_human_approval=True` in all responses
3. **Governance Engine Validation**: The `GovernanceEngine.enforce()` method validates that human approval is required and blocks outputs that attempt to bypass this requirement
4. **Type System Enforcement**: The `AgentCapabilities` dataclass makes human approval a mandatory field, preventing unsafe configurations

**Architectural Guarantee**: There is no code path in MedAgentX that allows autonomous decision-making without human approval. This is enforced at the type system level, not through runtime checks that could be bypassed.

### No Autonomous Treatment or Prescription

MedAgentX architecturally prevents autonomous treatment or prescription through:

1. **Capability Restrictions**: All agents have `can_prescribe=False` by default, and this capability is validated during agent initialization
2. **Governance Blocking**: The `GovernanceEngine` blocks outputs containing phrases like "prescribe", "treatment plan", "definitive diagnosis"
3. **Tool Restrictions**: Medical coding tools provide suggestions only, not billing or treatment decisions
4. **Output Disclaimers**: All outputs include explicit disclaimers stating that recommendations require clinician review

**Example Blocking Behavior**:
```python
# Attempt to generate prescription output
response = {"output": "Prescribe antibiotics for patient"}

# Governance engine blocks this
governance.enforce(response)  # Raises ValueError: "Governance block: phrase 'prescribe' not allowed."
```

### Offline Learning Only (No Live Model Drift)

MedAgentX is designed for **offline learning and deployment**, not continuous online learning:

- **Static Model Configuration**: Agents use fixed model configurations (e.g., `model_name="gpt-4"`, `temperature=0.3`) that do not change during runtime
- **No Online Fine-Tuning**: The system does not perform online fine-tuning or model updates during clinical use
- **Deterministic Workflows**: Workflow behavior is deterministic and traceable, preventing unexpected model drift
- **Versioned Deployments**: Model updates require explicit versioning and redeployment, not automatic updates

**Rationale**: Clinical CDS systems must maintain consistent behavior for regulatory compliance and patient safety. Online learning introduces risks of:
- Unpredictable model behavior changes
- Loss of auditability (model state changes are difficult to trace)
- Regulatory non-compliance (unclear which model version made which decision)

MedAgentX's offline-only approach ensures that system behavior is stable, traceable, and compliant with regulatory requirements for medical software.

### Alignment with FDA SaMD CDS Guidance

MedAgentX's architecture aligns with the FDA's guidance for Software as a Medical Device (SaMD) in the CDS category (high-level, non-legal positioning):

1. **Human Oversight Requirement**: FDA guidance emphasizes that CDS systems must require human oversight. MedAgentX enforces this architecturally through mandatory human approval gates.

2. **Transparency and Explainability**: FDA guidance requires CDS systems to provide evidence and reasoning for recommendations. MedAgentX includes:
   - Evidence fields in all agent outputs
   - RAG-retrieved knowledge as supporting evidence
   - Confidence scores and disclaimers
   - Complete traceability through `AgentTrace`

3. **Safety and Effectiveness**: FDA guidance requires CDS systems to demonstrate safety mechanisms. MedAgentX provides:
   - Architectural safety constraints (capability restrictions)
   - Governance engine validation
   - Audit logging for compliance
   - Deterministic replay for validation

4. **Non-Diagnostic Positioning**: FDA guidance distinguishes CDS from diagnostic systems. MedAgentX explicitly positions itself as CDS, not diagnosis, through:
   - Architectural blocks on diagnostic capabilities
   - Output disclaimers stating "supportive reasoning only"
   - Mandatory human approval for all recommendations

**Important Note**: This alignment discussion is high-level and conceptual. Actual FDA regulatory submission requires:
- Formal regulatory review
- Clinical validation studies
- Quality management system (QMS) documentation
- Risk management documentation
- Legal and regulatory counsel

MedAgentX's architecture is designed to support regulatory compliance, but formal FDA clearance or approval requires additional steps beyond system design.

### Clinical Safety Positioning Summary

MedAgentX is positioned as:

- ✅ **Clinical Decision Support (CDS)**: Provides recommendations to assist clinicians
- ✅ **Human-Overseen**: Mandatory human approval for all outputs
- ✅ **Non-Diagnostic**: Does not perform autonomous diagnosis
- ✅ **Non-Prescriptive**: Does not prescribe or treat autonomously
- ✅ **Auditable**: Complete traceability and deterministic replay
- ✅ **Stable**: Offline learning only, no live model drift
- ❌ **Not a Diagnostic System**: Does not make diagnostic determinations
- ❌ **Not a Treatment System**: Does not prescribe or administer treatments
- ❌ **Not Autonomous**: Cannot operate without human oversight

This positioning is architecturally enforced and cannot be changed without modifying the core system code, ensuring that MedAgentX remains a safe, compliant CDS platform.

