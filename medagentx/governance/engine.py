from typing import Any, Dict, List
from datetime import datetime


class GovernanceEngine:
    """Enforce safety: no direct diagnosis or treatment; always human approval."""

    def __init__(self):
        self.audit_log: List[Dict[str, Any]] = []

    def enforce(self, response: Dict[str, Any]) -> None:
        outputs = str(response)
        if "treatment" in outputs.lower() or "prescribe" in outputs.lower():
            raise ValueError("Governance block: treatment or prescriptions not allowed.")
        if "definitive diagnosis" in outputs.lower():
            raise ValueError("Governance block: direct diagnosis prohibited.")

        response["requires_human_approval"] = True
        self.audit_log.append(
            {"timestamp": datetime.now().isoformat(), "event": "governance_check", "result": "pass"}
        )

    def get_audit_log(self) -> List[Dict[str, Any]]:
        return self.audit_log

