# MCP Tool Development Guide

## Overview

MCP (Model Context Protocol) servers allow users to create custom tools that agents can use. This enables extensibility and customization of the platform.

## Creating a Custom Tool

### Step 1: Define Tool Schema

```python
from medagentx.tools.base_tool import BaseTool, ToolSchema

class MyCustomTool(BaseTool):
    def __init__(self):
        schema = ToolSchema(
            name="my_custom_tool",
            description="What this tool does",
            parameters={
                "type": "object",
                "properties": {
                    "param1": {
                        "type": "string",
                        "description": "Parameter description"
                    }
                },
                "required": ["param1"]
            },
            is_read_only=True,  # Most tools should be read-only
        )
        super().__init__(
            tool_id="my_custom_tool",
            schema=schema,
        )
    
    async def execute(self, arguments: dict) -> Any:
        param1 = arguments.get("param1")
        # Implement tool logic
        return {"result": "tool output"}
```

### Step 2: Register Tool

```python
from medagentx.tools.tool_registry import ToolRegistry

tool_registry = ToolRegistry()
tool = MyCustomTool()
tool_registry.register_tool(tool)
```

## Creating an MCP Server

### Step 1: Create Server Class

```python
from medagentx.tools.mcp_server import UserMCPServer, MCPServerConfig

config = MCPServerConfig(
    server_id="my_mcp_server",
    server_name="My MCP Server",
    description="Description of server capabilities",
    created_by="user123",
)

class MyMCPServer(UserMCPServer):
    async def initialize(self):
        # Register tools provided by this server
        tool1 = MyCustomTool1()
        tool2 = MyCustomTool2()
        
        self.register_tool(tool1)
        self.register_tool(tool2)
        
        await super().initialize()
```

### Step 2: Initialize Server

```python
server = MyMCPServer(config)
await server.initialize()

# Tools can now be used by agents
```

## Example Tools

See `medagentx/tools/examples.py` for example implementations:
- `SymptomKnowledgeRetriever`
- `DrugInteractionChecker`
- `MedicalCodeLookup`

## Tool Permissions

Tools have permission levels:
- `READ_ONLY`: Can only read data (default)
- `READ_WRITE`: Can read and write data
- `ADMIN`: Administrative access
- `CUSTOM`: Custom permission levels

Set permissions when registering:

```python
tool_registry.set_tool_permission(
    agent_id="my_agent",
    tool_id="my_tool",
    permission=ToolPermission.READ_ONLY,
)
```

## Best Practices

1. **Safety First**: Most tools should be read-only
2. **Validate Inputs**: Always validate arguments
3. **Error Handling**: Return meaningful errors
4. **Documentation**: Provide clear descriptions
5. **Testing**: Test tools thoroughly before deployment

## Tool Execution Flow

1. Agent decides to use tool
2. Governance engine checks permissions
3. Tool arguments validated
4. Tool executed
5. Results returned to agent
6. Usage logged in audit trail

