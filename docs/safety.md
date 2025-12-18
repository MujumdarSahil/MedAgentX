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

