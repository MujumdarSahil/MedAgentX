"""
Doctor-Programmable Agents for MedAgentX v2.0

Configuration-driven agents that doctors can define:
- Agent name
- Role
- Allowed tasks
- Forbidden tasks
- Escalation rules

Enforces Capability Firewall:
- Authority limits are architectural and non-overridable
- Patients can only use doctor-created agents
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import logging

from medagentx.core.agent import BaseAgent
from medagentx.core.types import AgentConfig, AgentCapabilities
from medagentx.governance.engine import GovernanceEngine

logger = logging.getLogger(__name__)


@dataclass
class AgentConfiguration:
    """Doctor-defined agent configuration."""
    agent_id: str
    agent_name: str
    role: str  # e.g., "symptom_analyzer", "risk_assessor"
    description: str
    allowed_tasks: List[str]  # List of allowed task types
    forbidden_tasks: List[str]  # List of forbidden task types
    escalation_rules: Dict[str, Any]  # Escalation conditions
    created_by: str  # Doctor/user ID
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    capabilities: AgentCapabilities = field(default_factory=lambda: AgentCapabilities())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "role": self.role,
            "description": self.description,
            "allowed_tasks": self.allowed_tasks,
            "forbidden_tasks": self.forbidden_tasks,
            "escalation_rules": self.escalation_rules,
            "created_by": self.created_by,
            "created_at": self.created_at,
            "capabilities": {
                "can_diagnose": self.capabilities.can_diagnose,
                "can_prescribe": self.capabilities.can_prescribe,
                "can_use_tools": self.capabilities.can_use_tools,
                "requires_human_approval": self.capabilities.requires_human_approval,
            },
        }


class CapabilityFirewall:
    """
    Capability Firewall.
    
    Enforces that authority limits are architectural and non-overridable.
    """
    
    def __init__(self, governance_engine: Optional[GovernanceEngine] = None):
        """
        Initialize capability firewall.
        
        Args:
            governance_engine: Optional governance engine for validation
        """
        self.governance_engine = governance_engine
        self.audit_log: List[Dict[str, Any]] = []
    
    def validate_configuration(self, config: AgentConfiguration) -> List[str]:
        """
        Validate agent configuration.
        
        Args:
            config: Agent configuration
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Check that diagnosis is not in allowed_tasks
        if "diagnosis" in config.allowed_tasks or any("diagnos" in task.lower() for task in config.allowed_tasks):
            errors.append("Diagnosis tasks are forbidden and cannot be in allowed_tasks")
        
        # Check that prescription is not in allowed_tasks
        if "prescription" in config.allowed_tasks or any("prescrib" in task.lower() for task in config.allowed_tasks):
            errors.append("Prescription tasks are forbidden and cannot be in allowed_tasks")
        
        # Check that capabilities are safe
        if config.capabilities.can_diagnose:
            errors.append("can_diagnose must be False (architectural constraint)")
        
        if config.capabilities.can_prescribe:
            errors.append("can_prescribe must be False (architectural constraint)")
        
        if not config.capabilities.requires_human_approval:
            errors.append("requires_human_approval must be True (architectural constraint)")
        
        # Check escalation rules
        if not config.escalation_rules:
            errors.append("escalation_rules must be defined")
        
        # Audit
        self._audit("validate_configuration", {
            "agent_id": config.agent_id,
            "errors": errors,
        })
        
        return errors
    
    def enforce_capabilities(
        self,
        agent: BaseAgent,
        task: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Enforce capability limits on agent execution.
        
        Args:
            agent: Agent instance
            task: Task to execute
            context: Optional context
            
        Returns:
            True if allowed, False otherwise
        """
        if not hasattr(agent, "capabilities"):
            logger.warning(f"Agent {agent.config.agent_id} missing capabilities")
            return False
        
        capabilities: AgentCapabilities = agent.capabilities
        
        # Check diagnosis
        if not capabilities.can_diagnose:
            if any(term in task.lower() for term in ["diagnose", "diagnosis", "definitive diagnosis"]):
                self._audit("capability_violation", {
                    "agent_id": agent.config.agent_id,
                    "task": task,
                    "violation": "diagnosis_attempt",
                })
                return False
        
        # Check prescription
        if not capabilities.can_prescribe:
            if any(term in task.lower() for term in ["prescribe", "prescription", "medication", "treatment"]):
                self._audit("capability_violation", {
                    "agent_id": agent.config.agent_id,
                    "task": task,
                    "violation": "prescription_attempt",
                })
                return False
        
        return True
    
    def _audit(self, event: str, data: Dict[str, Any]) -> None:
        """Log firewall event to audit log."""
        self.audit_log.append({
            "timestamp": datetime.now().isoformat(),
            "event": event,
            **data,
        })


class DoctorAgentRegistry:
    """
    Registry for doctor-created agents.
    
    Patients can only use doctor-created agents.
    """
    
    def __init__(self, capability_firewall: CapabilityFirewall):
        """
        Initialize doctor agent registry.
        
        Args:
            capability_firewall: Capability firewall instance
        """
        self.capability_firewall = capability_firewall
        self._agents: Dict[str, BaseAgent] = {}  # agent_id -> agent
        self._configurations: Dict[str, AgentConfiguration] = {}  # agent_id -> config
        self._doctor_agents: Dict[str, List[str]] = {}  # doctor_id -> [agent_ids]
    
    def register_agent(
        self,
        config: AgentConfiguration,
        agent: BaseAgent,
    ) -> None:
        """
        Register a doctor-created agent.
        
        Args:
            config: Agent configuration
            agent: Agent instance
            
        Raises:
            ValueError: If configuration is invalid
        """
        # Validate configuration
        errors = self.capability_firewall.validate_configuration(config)
        if errors:
            raise ValueError(f"Invalid agent configuration: {errors}")
        
        # Ensure capabilities match configuration
        agent.capabilities = config.capabilities
        
        # Register
        self._agents[config.agent_id] = agent
        self._configurations[config.agent_id] = config
        
        # Track by doctor
        if config.created_by not in self._doctor_agents:
            self._doctor_agents[config.created_by] = []
        self._doctor_agents[config.created_by].append(config.agent_id)
        
        logger.info(f"Registered doctor-created agent: {config.agent_id} by {config.created_by}")
    
    def get_agent(self, agent_id: str, patient_id: Optional[str] = None) -> Optional[BaseAgent]:
        """
        Get agent by ID (with patient access check).
        
        Args:
            agent_id: Agent ID
            patient_id: Optional patient ID (for access control)
            
        Returns:
            Agent instance or None
        """
        if agent_id not in self._agents:
            return None
        
        # Check if patient has access (if patient_id provided)
        if patient_id:
            config = self._configurations.get(agent_id)
            if config:
                # For now, all doctor-created agents are accessible to all patients
                # This can be extended with more granular access control
                pass
        
        return self._agents[agent_id]
    
    def list_doctor_agents(self, doctor_id: str) -> List[str]:
        """
        List agent IDs created by a doctor.
        
        Args:
            doctor_id: Doctor ID
            
        Returns:
            List of agent IDs
        """
        return self._doctor_agents.get(doctor_id, [])
    
    def list_all_agents(self) -> List[str]:
        """
        List all registered agent IDs.
        
        Returns:
            List of agent IDs
        """
        return list(self._agents.keys())
    
    def get_configuration(self, agent_id: str) -> Optional[AgentConfiguration]:
        """
        Get agent configuration.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            Agent configuration or None
        """
        return self._configurations.get(agent_id)

