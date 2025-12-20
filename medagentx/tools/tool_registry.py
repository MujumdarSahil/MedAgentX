"""
Tool Registry for MedAgentX.

Manages registration, discovery, and execution of tools.
Supports user-created tools and MCP servers.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import logging

from medagentx.tools.base_tool import BaseTool, ToolSchema
from medagentx.core.types import ToolPermission

logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    Central registry for all tools in the platform.
    
    Responsibilities:
    - Tool registration and discovery
    - Tool execution coordination
    - Permission management
    - Usage tracking
    """
    
    def __init__(self):
        """Initialize tool registry."""
        self._tools: Dict[str, BaseTool] = {}
        self._tool_permissions: Dict[str, Dict[str, ToolPermission]] = {}  # agent_id -> tool_id -> permission
        self._usage_log: List[Dict[str, Any]] = []

    async def register_mcp_server(self, server: Any) -> None:
        """Register all tools exposed by an MCP server."""
        if hasattr(server, "initialize"):
            await server.initialize()
        for tool in getattr(server, "_tools", {}).values():
            self.register_tool(tool)
    
    def register_tool(
        self,
        tool: BaseTool,
        default_permission: ToolPermission = ToolPermission.READ_ONLY,
    ) -> None:
        """
        Register a tool in the registry.
        
        Args:
            tool: Tool instance to register
            default_permission: Default permission level for this tool
        """
        if tool.tool_id in self._tools:
            logger.warning(f"Tool {tool.tool_id} already registered, overwriting")
        
        self._tools[tool.tool_id] = tool
        
        # Initialize permissions dict if needed
        if tool.tool_id not in self._tool_permissions:
            self._tool_permissions[tool.tool_id] = {}
        
        logger.info(f"Registered tool: {tool.tool_id} ({tool.schema.name})")
    
    def unregister_tool(self, tool_id: str) -> None:
        """
        Unregister a tool.
        
        Args:
            tool_id: Tool ID to unregister
        """
        if tool_id in self._tools:
            del self._tools[tool_id]
            if tool_id in self._tool_permissions:
                del self._tool_permissions[tool_id]
            logger.info(f"Unregistered tool: {tool_id}")
        else:
            logger.warning(f"Tool {tool_id} not found, cannot unregister")
    
    def get_tool(self, tool_id: str) -> Optional[BaseTool]:
        """
        Get a tool by ID.
        
        Args:
            tool_id: Tool ID
            
        Returns:
            Tool instance or None if not found
        """
        return self._tools.get(tool_id)
    
    def list_tools(self, agent_id: Optional[str] = None) -> List[BaseTool]:
        """
        List all available tools, optionally filtered by agent permissions.
        
        Args:
            agent_id: Optional agent ID to filter by permissions
            
        Returns:
            List of available tools
        """
        if agent_id is None:
            return list(self._tools.values())
        
        # Filter by agent permissions
        available_tools = []
        for tool_id, tool in self._tools.items():
            permission = self.get_tool_permission(agent_id, tool_id)
            if permission is not None:  # Agent has permission
                available_tools.append(tool)
        
        return available_tools
    
    def set_tool_permission(
        self,
        agent_id: str,
        tool_id: str,
        permission: ToolPermission,
    ) -> None:
        """
        Set permission for an agent to use a tool.
        
        Args:
            agent_id: Agent ID
            tool_id: Tool ID
            permission: Permission level
        """
        if tool_id not in self._tool_permissions:
            self._tool_permissions[tool_id] = {}
        
        self._tool_permissions[tool_id][agent_id] = permission
        logger.info(f"Set permission {permission} for agent {agent_id} on tool {tool_id}")
    
    def get_tool_permission(
        self,
        agent_id: str,
        tool_id: str,
    ) -> Optional[ToolPermission]:
        """
        Get permission for an agent to use a tool.
        
        Args:
            agent_id: Agent ID
            tool_id: Tool ID
            
        Returns:
            Permission level or None if no permission set
        """
        return self._tool_permissions.get(tool_id, {}).get(agent_id)
    
    async def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        agent_id: Optional[str] = None,
    ) -> Any:
        """
        Execute a tool by name.
        
        Args:
            tool_name: Tool name or ID
            arguments: Tool arguments
            agent_id: ID of agent requesting execution (for permission check)
            
        Returns:
            Tool execution result
            
        Raises:
            ValueError: If tool not found or invalid arguments
            PermissionError: If agent doesn't have permission
        """
        # Find tool by name or ID
        tool = None
        for t in self._tools.values():
            if t.tool_id == tool_name or t.schema.name == tool_name:
                tool = t
                break
        
        if tool is None:
            raise ValueError(f"Tool '{tool_name}' not found")
        
        # Check permissions
        if agent_id:
            permission = self.get_tool_permission(agent_id, tool.tool_id)
            if permission is None:
                raise PermissionError(f"Agent {agent_id} does not have permission to use tool {tool.tool_id}")
        
        # Log usage
        usage_entry = {
            "timestamp": datetime.now(),
            "tool_id": tool.tool_id,
            "tool_name": tool.schema.name,
            "agent_id": agent_id,
            "arguments": arguments,
        }
        self._usage_log.append(usage_entry)
        
        # Execute tool
        try:
            result = await tool.execute(arguments)
            usage_entry["success"] = True
            return result
        except Exception as e:
            usage_entry["success"] = False
            usage_entry["error"] = str(e)
            logger.error(f"Tool execution error: {e}", exc_info=True)
            raise
    
    def get_usage_stats(self, tool_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get usage statistics for tools.
        
        Args:
            tool_id: Optional tool ID to filter by
            
        Returns:
            Usage statistics
        """
        if tool_id:
            tool_logs = [entry for entry in self._usage_log if entry.get("tool_id") == tool_id]
        else:
            tool_logs = self._usage_log
        
        total_calls = len(tool_logs)
        successful_calls = sum(1 for entry in tool_logs if entry.get("success", False))
        
        return {
            "total_calls": total_calls,
            "successful_calls": successful_calls,
            "failed_calls": total_calls - successful_calls,
            "recent_calls": tool_logs[-10:] if tool_logs else [],
        }

