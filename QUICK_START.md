# MedAgentX Quick Start Guide

## Installation

1. **Clone or navigate to the project directory**

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Set up configuration:**
```bash
cp config/config.example.yaml config/config.yaml
# Edit config/config.yaml with your API keys and settings
```

## Basic Usage

### Running the Platform

```python
from medagentx.main import MedAgentXPlatform

platform = MedAgentXPlatform()
# Platform is now ready for use
```

### Creating an Agent

```python
from medagentx.core.types import AgentConfig
from medagentx.agents import SymptomAnalyzerAgent

config = AgentConfig(
    agent_id="my_agent",
    agent_name="My Symptom Analyzer",
    description="Analyzes patient symptoms",
    model_provider="openai",
    model_name="gpt-4",
    created_by="your_user_id",
)

agent = SymptomAnalyzerAgent(
    config=config,
    tool_registry=platform.tool_registry,
    governance_engine=platform.governance_engine,
    knowledge_base=platform.knowledge_base,
)

platform.register_agent(agent)
```

### Using an Agent

```python
result = await agent.analyze_symptoms(
    symptoms="fever and cough",
    patient_context={"age": 35, "gender": "male"},
)

# Access recommendations
recommendations = result["state"].recommendations
```

### Creating a Custom Tool

```python
from medagentx.tools.base_tool import BaseTool, ToolSchema

class MyTool(BaseTool):
    def __init__(self):
        schema = ToolSchema(
            name="my_tool",
            description="Description of what the tool does",
            parameters={
                "type": "object",
                "properties": {
                    "param1": {"type": "string"}
                },
                "required": ["param1"]
            },
        )
        super().__init__(tool_id="my_tool", schema=schema)
    
    async def execute(self, arguments):
        # Tool logic here
        return {"result": "success"}

# Register tool
tool = MyTool()
platform.tool_registry.register_tool(tool)
```

## Example Workflow

See `examples/quick_start.py` for a complete working example.

## Key Concepts

1. **Agents**: Specialized AI entities that perform clinical tasks
2. **Tools**: Functions that agents can call
3. **MCP Servers**: Custom tool servers that users can create
4. **Governance**: Safety rules and compliance enforcement
5. **Knowledge Base**: Medical knowledge storage and retrieval
6. **Workflows**: Multi-agent orchestration

## Safety & Compliance

⚠️ **IMPORTANT**: All recommendations require human (doctor) approval before use.

The platform enforces this at the architecture level - recommendations cannot be used without approval.

## Next Steps

- Read [Architecture Guide](docs/architecture.md)
- Learn about [Agent Development](docs/agents.md)
- Explore [MCP Tools](docs/mcp_tools.md)
- Understand [Safety & Compliance](docs/safety.md)

