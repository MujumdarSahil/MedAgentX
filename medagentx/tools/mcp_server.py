"""
MCP (Model Context Protocol) Server Implementation for MedAgentX.

MCP servers allow users (doctors) to create custom tool servers that
agents can use. This enables extensibility and customization.
"""

from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field
from datetime import datetime
import logging

from medagentx.tools.base_tool import BaseTool, ToolSchema

logger = logging.getLogger(__name__)


class MCPTool(BaseModel):
    """MCP tool definition."""
    name: str
    description: str
    inputSchema: Dict[str, Any] = Field(default_factory=dict)  # JSON Schema
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MCPServerConfig(BaseModel):
    """Configuration for an MCP server."""
    server_id: str
    server_name: str
    description: str
    version: str = "1.0.0"
    created_by: str
    created_at: datetime = Field(default_factory=datetime.now)
    tools: List[MCPTool] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MCPServer(ABC):
    """
    Base class for MCP servers.
    
    MCP servers provide a standardized way to expose tools to agents.
    Users can create custom MCP servers to extend platform capabilities.
    """
    
    def __init__(self, config: MCPServerConfig):
        """
        Initialize MCP server.
        
        Args:
            config: Server configuration
        """
        self.config = config
        self._tools: Dict[str, BaseTool] = {}
        self._initialized = False
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the MCP server and register its tools."""
        pass
    
    def register_tool(self, tool: BaseTool) -> None:
        """
        Register a tool provided by this MCP server.
        
        Args:
            tool: Tool instance to register
        """
        self._tools[tool.tool_id] = tool
        logger.info(f"MCP server {self.config.server_id} registered tool: {tool.tool_id}")
    
    def list_tools(self) -> List[MCPTool]:
        """
        List all tools provided by this server.
        
        Returns:
            List of MCP tool definitions
        """
        tools = []
        for tool_id, tool in self._tools.items():
            mcp_tool = MCPTool(
                name=tool.schema.name,
                description=tool.schema.description,
                inputSchema=tool.schema.parameters,
                metadata={"tool_id": tool_id},
            )
            tools.append(mcp_tool)
        return tools
    
    async def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
    ) -> Any:
        """
        Execute a tool by name.
        
        Args:
            tool_name: Tool name or ID
            arguments: Tool arguments
            
        Returns:
            Tool execution result
        """
        tool = None
        for t in self._tools.values():
            if t.tool_id == tool_name or t.schema.name == tool_name:
                tool = t
                break
        
        if tool is None:
            raise ValueError(f"Tool '{tool_name}' not found in MCP server {self.config.server_id}")
        
        return await tool.execute(arguments)
    
    def get_info(self) -> Dict[str, Any]:
        """Get MCP server information."""
        return {
            "server_id": self.config.server_id,
            "server_name": self.config.server_name,
            "description": self.config.description,
            "version": self.config.version,
            "tools_count": len(self._tools),
            "created_by": self.config.created_by,
        }


class UserMCPServer(MCPServer):
    """
    User-created MCP server.
    
    This is the base class that users extend to create custom MCP servers.
    """
    
    async def initialize(self) -> None:
        """
        Initialize user MCP server.
        
        Users override this method to register their custom tools.
        """
        if self._initialized:
            return
        
        # Users should override this to register tools
        # Example:
        # tool = MyCustomTool(tool_id="my_tool", schema=my_schema)
        # self.register_tool(tool)
        
        self._initialized = True
        logger.info(f"User MCP server {self.config.server_id} initialized")

