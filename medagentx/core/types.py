"""
Type definitions for MedAgentX core components.

This module defines the foundational data structures used throughout
the platform for agents, tools, messages, and state management.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    """Roles in agent conversations."""
    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"
    TOOL = "tool"
    HUMAN_REVIEWER = "human_reviewer"


class AgentStatus(str, Enum):
    """Agent execution status."""
    IDLE = "idle"
    THINKING = "thinking"
    ACTING = "acting"
    WAITING_FOR_TOOL = "waiting_for_tool"
    WAITING_FOR_HUMAN = "waiting_for_human"
    REFLECTING = "reflecting"
    COMPLETED = "completed"
    ERROR = "error"
    REJECTED = "rejected"  # Human rejected the recommendation


class ToolPermission(str, Enum):
    """Tool permission levels."""
    READ_ONLY = "read_only"
    READ_WRITE = "read_write"
    ADMIN = "admin"
    CUSTOM = "custom"


class RecommendationType(str, Enum):
    """Types of medical recommendations."""
    DIAGNOSIS_HYPOTHESIS = "diagnosis_hypothesis"
    DIFFERENTIAL_DIAGNOSIS = "differential_diagnosis"
    TREATMENT_SUGGESTION = "treatment_suggestion"
    TEST_RECOMMENDATION = "test_recommendation"
    MEDICATION_REVIEW = "medication_review"
    RISK_ASSESSMENT = "risk_assessment"
    FOLLOW_UP = "follow_up"
    CODING_SUGGESTION = "coding_suggestion"


class ClinicalConfidence(str, Enum):
    """Confidence levels for clinical recommendations."""
    VERY_LOW = "very_low"  # < 30%
    LOW = "low"  # 30-50%
    MODERATE = "moderate"  # 50-70%
    HIGH = "high"  # 70-90%
    VERY_HIGH = "very_high"  # > 90%


class AgentMessage(BaseModel):
    """Message in agent conversation."""
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    tool_calls: List["ToolCall"] = Field(default_factory=list)
    tool_results: List["ToolResult"] = Field(default_factory=list)
    requires_human_approval: bool = False
    approval_status: Optional[str] = None  # "pending", "approved", "rejected"


class ToolCall(BaseModel):
    """Tool invocation call."""
    tool_name: str
    tool_id: str  # Unique ID for this tool call
    arguments: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)
    caller_agent_id: Optional[str] = None


class ToolResult(BaseModel):
    """Result from tool execution."""
    tool_call_id: str
    success: bool
    result: Any
    error: Optional[str] = None
    execution_time_ms: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentMemory(BaseModel):
    """Agent memory structure."""
    episodic_memory: List[AgentMessage] = Field(default_factory=list)
    clinical_memory: Dict[str, Any] = Field(default_factory=dict)
    long_term_knowledge: Dict[str, Any] = Field(default_factory=dict)
    last_updated: datetime = Field(default_factory=datetime.now)


class Recommendation(BaseModel):
    """Clinical recommendation output."""
    recommendation_type: RecommendationType
    content: str
    confidence: ClinicalConfidence
    confidence_score: float = Field(ge=0.0, le=1.0)
    supporting_evidence: List[str] = Field(default_factory=list)
    alternative_options: List[str] = Field(default_factory=list)
    risks_and_warnings: List[str] = Field(default_factory=list)
    requires_human_approval: bool = True
    approval_status: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentConfig(BaseModel):
    """Configuration for an agent."""
    agent_id: str
    agent_name: str
    description: str
    model_provider: str = "openai"  # openai, anthropic, etc.
    model_name: str = "gpt-4"
    temperature: float = Field(default=0.3, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2000, gt=0)
    max_iterations: int = Field(default=10, gt=0)
    enable_self_critique: bool = True
    enable_reflection: bool = True
    enable_planning: bool = True
    tools: List[str] = Field(default_factory=list)  # Tool IDs
    permissions: Dict[str, ToolPermission] = Field(default_factory=dict)
    safety_rules: List[str] = Field(default_factory=list)
    created_by: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class AgentState(BaseModel):
    """Complete agent state."""
    agent_id: str
    status: AgentStatus = AgentStatus.IDLE
    current_task: Optional[str] = None
    messages: List[AgentMessage] = Field(default_factory=list)
    memory: AgentMemory = Field(default_factory=AgentMemory)
    recommendations: List[Recommendation] = Field(default_factory=list)
    plan: Optional[List[str]] = None
    current_iteration: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)
    last_updated: datetime = Field(default_factory=datetime.now)

