"""
Base Tool class for MedAgentX.

Tools are callable functions that agents can invoke to perform actions.
Tools are sandboxed and subject to governance checks.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class ToolSchema(BaseModel):
    """Schema definition for a tool."""
    name: str
    description: str
    parameters: Dict[str, Any] = Field(default_factory=dict)  # JSON Schema format
    returns: Dict[str, Any] = Field(default_factory=dict)  # Return type description
    requires_permission: Optional[str] = None
    is_read_only: bool = True  # Most tools are read-only for safety


class BaseTool(ABC):
    """
    Base class for all tools in MedAgentX.
    
    Tools are the building blocks that agents use to interact with
    external systems, knowledge bases, and APIs.
    """
    
    def __init__(
        self,
        tool_id: str,
        schema: ToolSchema,
        created_by: Optional[str] = None,
    ):
        """
        Initialize tool.
        
        Args:
            tool_id: Unique tool identifier
            schema: Tool schema definition
            created_by: User ID who created this tool
        """
        self.tool_id = tool_id
        self.schema = schema
        self.created_by = created_by
        self.created_at = datetime.now()
        self.call_count = 0
        self.last_called = None
    
    @abstractmethod
    async def execute(self, arguments: Dict[str, Any]) -> Any:
        """
        Execute the tool with given arguments.
        
        Args:
            arguments: Tool arguments as specified in schema
            
        Returns:
            Tool execution result
            
        Raises:
            ValueError: If arguments are invalid
            PermissionError: If execution is not allowed
        """
        pass
    
    def validate_arguments(self, arguments: Dict[str, Any]) -> bool:
        """
        Validate tool arguments against schema.
        
        Args:
            arguments: Arguments to validate
            
        Returns:
            True if valid, False otherwise
        """
        # Basic validation - in production, use jsonschema
        required_params = self.schema.parameters.get("required", [])
        for param in required_params:
            if param not in arguments:
                return False
        return True
    
    async def __call__(self, arguments: Dict[str, Any]) -> Any:
        """Make tool callable."""
        if not self.validate_arguments(arguments):
            raise ValueError(f"Invalid arguments for tool {self.tool_id}")
        
        self.call_count += 1
        self.last_called = datetime.now()
        
        result = await self.execute(arguments)
        return result

