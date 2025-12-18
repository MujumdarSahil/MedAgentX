"""
Base Agent Class for MedAgentX Platform.

Implements ReAct (Reason + Act + Tool Use) pattern with:
- Task planning
- Tool invocation
- Self-critique and reflection
- Memory management
- Human-in-the-loop checkpoints
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime
import logging

from medagentx.core.types import (
    AgentState,
    AgentMessage,
    AgentConfig,
    AgentStatus,
    MessageRole,
    ToolCall,
    ToolResult,
    Recommendation,
    ClinicalConfidence,
)

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Base class for all agents in MedAgentX.
    
    Implements the ReAct (Reasoning + Acting) pattern with:
    - Tool use capabilities
    - Memory management (episodic + clinical)
    - Self-critique and reflection
    - Planning and task decomposition
    - Human-in-the-loop checkpoints
    """
    
    def __init__(
        self,
        config: AgentConfig,
        tool_registry: Optional[Any] = None,
        governance_engine: Optional[Any] = None,
    ):
        """
        Initialize the agent.
        
        Args:
            config: Agent configuration
            tool_registry: Registry of available tools
            governance_engine: Safety and compliance engine
        """
        self.config = config
        self.tool_registry = tool_registry
        self.governance_engine = governance_engine
        
        self.state = AgentState(
            agent_id=config.agent_id,
            status=AgentStatus.IDLE,
        )
        
        self._iteration_count = 0
        
    async def execute(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
    ) -> AgentState:
        """
        Execute a task using the ReAct pattern.
        
        Steps:
        1. Plan: Break down task into steps
        2. Act: Execute steps with tool use
        3. Reflect: Critique and verify results
        4. Repeat until completion or max iterations
        
        Args:
            task: Task description
            context: Additional context (patient data, etc.)
            user_id: ID of user requesting execution
            
        Returns:
            Final agent state
        """
        self.state.status = AgentStatus.THINKING
        self.state.current_task = task
        self.state.current_iteration = 0
        
        # Add user message to conversation
        user_message = AgentMessage(
            role=MessageRole.USER,
            content=task,
            metadata={"context": context or {}, "user_id": user_id},
        )
        self.state.messages.append(user_message)
        
        try:
            # Plan phase
            if self.config.enable_planning:
                plan = await self._plan(task, context)
                self.state.plan = plan
                logger.info(f"Agent {self.config.agent_id} created plan: {plan}")
            
            # Execute ReAct loop
            while (
                self.state.current_iteration < self.config.max_iterations
                and self.state.status not in [AgentStatus.COMPLETED, AgentStatus.ERROR, AgentStatus.REJECTED]
            ):
                self.state.current_iteration += 1
                self._iteration_count += 1
                
                # Reason: Think about next action
                self.state.status = AgentStatus.THINKING
                reasoning = await self._reason()
                
                if reasoning.get("requires_human_approval"):
                    self.state.status = AgentStatus.WAITING_FOR_HUMAN
                    # Wait for human approval (in real implementation, this would
                    # be handled by the workflow engine)
                    logger.info(f"Agent {self.config.agent_id} requires human approval")
                    break
                
                # Act: Invoke tools or generate response
                self.state.status = AgentStatus.ACTING
                action_result = await self._act(reasoning)
                
                # Check if we need tool results
                if action_result.get("tool_calls"):
                    self.state.status = AgentStatus.WAITING_FOR_TOOL
                    tool_results = await self._execute_tools(action_result["tool_calls"])
                    action_result["tool_results"] = tool_results
                
                # Reflect: Critique the action and results
                if self.config.enable_reflection:
                    self.state.status = AgentStatus.REFLECTING
                    reflection = await self._reflect(action_result)
                    
                    if reflection.get("is_complete"):
                        self.state.status = AgentStatus.COMPLETED
                        break
                    elif reflection.get("should_retry"):
                        continue
                
                # Update state with action result
                agent_message = AgentMessage(
                    role=MessageRole.AGENT,
                    content=action_result.get("response", ""),
                    tool_calls=action_result.get("tool_calls", []),
                    tool_results=action_result.get("tool_results", []),
                    metadata=action_result.get("metadata", {}),
                )
                self.state.messages.append(agent_message)
                
                # Self-critique if enabled
                if self.config.enable_self_critique:
                    critique = await self._critique()
                    if critique.get("needs_correction"):
                        logger.warning(
                            f"Agent {self.config.agent_id} self-critique identified issues"
                        )
            
            # Final status check
            if self.state.status == AgentStatus.ACTING:
                self.state.status = AgentStatus.COMPLETED
            
        except Exception as e:
            logger.error(f"Agent {self.config.agent_id} execution error: {e}", exc_info=True)
            self.state.status = AgentStatus.ERROR
            error_message = AgentMessage(
                role=MessageRole.SYSTEM,
                content=f"Error: {str(e)}",
                metadata={"error": True},
            )
            self.state.messages.append(error_message)
        
        finally:
            self.state.last_updated = datetime.now()
            # Store in episodic memory
            self.state.memory.episodic_memory.extend(self.state.messages[-10:])  # Last 10 messages
            
        return self.state
    
    async def _plan(self, task: str, context: Optional[Dict[str, Any]] = None) -> List[str]:
        """
        Create a plan for executing the task.
        
        Args:
            task: Task description
            context: Additional context
            
        Returns:
            List of plan steps
        """
        # This is a placeholder. In real implementation, this would use
        # an LLM to generate a plan based on the task.
        plan_prompt = f"""
        Task: {task}
        Context: {context or {}}
        
        Break this task down into specific steps.
        """
        
        # For now, return a simple plan
        # In production, this would call the LLM
        return [
            "Analyze the input",
            "Retrieve relevant knowledge",
            "Generate recommendations",
            "Validate and critique",
            "Format output",
        ]
    
    async def _reason(self) -> Dict[str, Any]:
        """
        Reasoning step: Determine next action.
        
        Returns:
            Dict with reasoning and next action
        """
        # Get recent conversation context
        recent_messages = self.state.messages[-5:]
        
        # Determine what to do next
        # In production, this would use an LLM to generate reasoning
        reasoning = {
            "thought": "Analyzing the current state and determining next action",
            "action": "continue",
            "requires_human_approval": False,
        }
        
        return reasoning
    
    async def _act(self, reasoning: Dict[str, Any]) -> Dict[str, Any]:
        """
        Act step: Execute the planned action.
        
        Args:
            reasoning: Reasoning from _reason step
            
        Returns:
            Action result with response and/or tool calls
        """
        # Determine if we need to call tools
        tool_calls = []
        
        if self.tool_registry and self.config.tools:
            # Check if we need to use tools based on current state
            # This is simplified; real implementation would use LLM to decide
            pass
        
        response = await self._generate_response()
        
        return {
            "response": response,
            "tool_calls": tool_calls,
            "tool_results": [],
            "metadata": {},
        }
    
    async def _generate_response(self) -> str:
        """
        Generate a response using the LLM.
        
        Returns:
            Generated response text
        """
        # Placeholder - in production, this would call the configured LLM
        # with the conversation history and context
        return "Response generated by agent"
    
    async def _execute_tools(self, tool_calls: List[ToolCall]) -> List[ToolResult]:
        """
        Execute tool calls through the tool registry.
        
        Args:
            tool_calls: List of tool calls to execute
            
        Returns:
            List of tool results
        """
        if not self.tool_registry:
            return []
        
        results = []
        for tool_call in tool_calls:
            try:
                # Governance check
                if self.governance_engine:
                    allowed = await self.governance_engine.check_tool_permission(
                        agent_id=self.config.agent_id,
                        tool_name=tool_call.tool_name,
                        tool_call=tool_call,
                    )
                    if not allowed:
                        results.append(ToolResult(
                            tool_call_id=tool_call.tool_id,
                            success=False,
                            result=None,
                            error="Tool permission denied by governance engine",
                        ))
                        continue
                
                # Execute tool
                result = await self.tool_registry.execute_tool(
                    tool_name=tool_call.tool_name,
                    arguments=tool_call.arguments,
                )
                
                results.append(ToolResult(
                    tool_call_id=tool_call.tool_id,
                    success=True,
                    result=result,
                ))
                
            except Exception as e:
                logger.error(f"Tool execution error: {e}", exc_info=True)
                results.append(ToolResult(
                    tool_call_id=tool_call.tool_id,
                    success=False,
                    result=None,
                    error=str(e),
                ))
        
        return results
    
    async def _reflect(self, action_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Reflection step: Critique the action and determine if task is complete.
        
        Args:
            action_result: Result from _act step
            
        Returns:
            Reflection with completion status
        """
        # Check if we have enough information to complete
        is_complete = False
        should_retry = False
        
        # Simple heuristic: if we've made several iterations and have a response
        if self.state.current_iteration >= 3:
            is_complete = True
        
        return {
            "is_complete": is_complete,
            "should_retry": should_retry,
            "reflection": "Task appears complete",
        }
    
    async def _critique(self) -> Dict[str, Any]:
        """
        Self-critique: Review own performance and outputs.
        
        Returns:
            Critique results
        """
        # Placeholder for self-critique logic
        # In production, this would use an LLM to critique the agent's outputs
        return {
            "needs_correction": False,
            "critique": "Outputs appear reasonable",
        }
    
    def add_recommendation(self, recommendation: Recommendation) -> None:
        """
        Add a clinical recommendation to the agent state.
        
        Args:
            recommendation: Recommendation to add
        """
        self.state.recommendations.append(recommendation)
    
    def get_state(self) -> AgentState:
        """Get current agent state."""
        return self.state
    
    def reset(self) -> None:
        """Reset agent state for new task."""
        self.state = AgentState(
            agent_id=self.config.agent_id,
            status=AgentStatus.IDLE,
        )
        self._iteration_count = 0

