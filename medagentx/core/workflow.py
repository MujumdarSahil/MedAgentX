"""
Recommendation Workflow Engine for MedAgentX.

Orchestrates multi-agent workflows for clinical decision support.
Manages human-in-the-loop approval processes.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum
import logging
from pydantic import BaseModel, Field

from medagentx.core.types import (
    AgentState,
    Recommendation,
    AgentStatus,
    MessageRole,
    AgentMessage,
)

logger = logging.getLogger(__name__)


class WorkflowStatus(str, Enum):
    """Workflow execution status."""
    PENDING = "pending"
    RUNNING = "running"
    WAITING_FOR_APPROVAL = "waiting_for_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"
    ERROR = "error"


class WorkflowStep(BaseModel):
    """A step in a workflow."""
    step_id: str
    agent_id: str
    task: str
    depends_on: List[str] = Field(default_factory=list)  # Step IDs this depends on
    status: str = "pending"
    result: Optional[Dict[str, Any]] = None


class RecommendationWorkflow:
    """
    Workflow engine for clinical recommendation generation.
    
    Orchestrates multiple agents to generate recommendations and
    manages the human approval process.
    """
    
    def __init__(
        self,
        workflow_id: str,
        agents: Dict[str, Any],  # agent_id -> Agent instance
        governance_engine: Optional[Any] = None,
    ):
        """
        Initialize workflow.
        
        Args:
            workflow_id: Unique workflow ID
            agents: Dictionary of available agents
            governance_engine: Governance engine for validation
        """
        self.workflow_id = workflow_id
        self.agents = agents
        self.governance_engine = governance_engine
        self.status = WorkflowStatus.PENDING
        self.steps: List[WorkflowStep] = []
        self.recommendations: List[Recommendation] = []
        self.created_at = datetime.now()
        self.approved_by: Optional[str] = None
        self.approved_at: Optional[datetime] = None
    
    async def execute(
        self,
        initial_task: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute the workflow.
        
        Args:
            initial_task: Initial task description
            context: Workflow context
            
        Returns:
            Workflow execution results
        """
        self.status = WorkflowStatus.RUNNING
        
        try:
            # Example workflow: Symptom Analysis -> Diagnosis Support -> Recommendations
            # In production, this would be configurable
            
            # Step 1: Symptom Analysis
            symptom_agent = self.agents.get("symptom_analyzer")
            if symptom_agent:
                step1 = WorkflowStep(
                    step_id="step1_symptom_analysis",
                    agent_id="symptom_analyzer",
                    task=initial_task,
                )
                step1.status = "running"
                
                result = await symptom_agent.execute(initial_task, context)
                step1.result = {"state": result, "recommendations": result.recommendations}
                step1.status = "completed"
                self.steps.append(step1)
                
                # Collect recommendations
                self.recommendations.extend(result.recommendations)
            
            # Step 2: Diagnosis Support (if needed)
            diagnosis_agent = self.agents.get("diagnosis_support")
            if diagnosis_agent and context:
                step2 = WorkflowStep(
                    step_id="step2_diagnosis_support",
                    agent_id="diagnosis_support",
                    task=f"Generate differential diagnosis based on: {initial_task}",
                    depends_on=["step1_symptom_analysis"],
                )
                step2.status = "running"
                
                result = await diagnosis_agent.execute(step2.task, context)
                step2.result = {"state": result, "recommendations": result.recommendations}
                step2.status = "completed"
                self.steps.append(step2)
                
                self.recommendations.extend(result.recommendations)
            
            # Validate all recommendations
            if self.governance_engine:
                for rec in self.recommendations:
                    validation = await self.governance_engine.validate_recommendation(rec)
                    if not validation.get("all_passed"):
                        logger.warning(f"Recommendation validation failed: {validation}")
            
            # All recommendations require human approval
            self.status = WorkflowStatus.WAITING_FOR_APPROVAL
            
            return {
                "workflow_id": self.workflow_id,
                "status": self.status,
                "steps": [s.dict() for s in self.steps],
                "recommendations": self.recommendations,
                "requires_approval": True,
            }
        
        except Exception as e:
            logger.error(f"Workflow execution error: {e}", exc_info=True)
            self.status = WorkflowStatus.ERROR
            raise
    
    async def approve(
        self,
        reviewer_id: str,
        approved_recommendations: Optional[List[str]] = None,  # Recommendation IDs
    ) -> Dict[str, Any]:
        """
        Approve workflow recommendations.
        
        Args:
            reviewer_id: ID of human reviewer
            approved_recommendations: List of recommendation IDs to approve (None = all)
            
        Returns:
            Approval result
        """
        if self.status != WorkflowStatus.WAITING_FOR_APPROVAL:
            raise ValueError(f"Cannot approve workflow in status: {self.status}")
        
        # Mark approved recommendations
        if approved_recommendations is None:
            # Approve all
            for rec in self.recommendations:
                rec.approval_status = "approved"
        else:
            # Approve specific ones
            rec_dict = {rec.metadata.get("id", ""): rec for rec in self.recommendations}
            for rec_id in approved_recommendations:
                if rec_id in rec_dict:
                    rec_dict[rec_id].approval_status = "approved"
        
        self.approved_by = reviewer_id
        self.approved_at = datetime.now()
        self.status = WorkflowStatus.APPROVED
        
        return {
            "workflow_id": self.workflow_id,
            "status": self.status,
            "approved_by": reviewer_id,
            "approved_at": self.approved_at,
            "approved_recommendations": approved_recommendations or "all",
        }
    
    async def reject(
        self,
        reviewer_id: str,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Reject workflow recommendations.
        
        Args:
            reviewer_id: ID of human reviewer
            reason: Rejection reason
            
        Returns:
            Rejection result
        """
        if self.status != WorkflowStatus.WAITING_FOR_APPROVAL:
            raise ValueError(f"Cannot reject workflow in status: {self.status}")
        
        for rec in self.recommendations:
            rec.approval_status = "rejected"
        
        self.status = WorkflowStatus.REJECTED
        
        return {
            "workflow_id": self.workflow_id,
            "status": self.status,
            "rejected_by": reviewer_id,
            "rejection_reason": reason,
            "rejected_at": datetime.now(),
        }
    
    def get_results(self) -> Dict[str, Any]:
        """Get workflow results."""
        return {
            "workflow_id": self.workflow_id,
            "status": self.status,
            "steps": [s.dict() for s in self.steps],
            "recommendations": self.recommendations,
            "created_at": self.created_at,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at,
        }

