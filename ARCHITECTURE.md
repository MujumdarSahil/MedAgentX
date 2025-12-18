# MedAgentX Platform Architecture

## Project Structure

```
MedAgentX/
├── medagentx/              # Main package
│   ├── __init__.py
│   ├── main.py             # Platform entry point
│   ├── core/               # Core components
│   │   ├── __init__.py
│   │   ├── agent.py        # Base Agent class
│   │   ├── types.py        # Type definitions
│   │   └── workflow.py     # Workflow engine
│   ├── agents/             # Agent templates
│   │   ├── __init__.py
│   │   ├── base_template.py
│   │   ├── symptom_analyzer.py
│   │   ├── diagnosis_support.py
│   │   ├── medical_coder.py
│   │   ├── prescription_reviewer.py
│   │   ├── clinical_guideline.py
│   │   └── risk_assessor.py
│   ├── tools/              # Tools & MCP
│   │   ├── __init__.py
│   │   ├── base_tool.py
│   │   ├── tool_registry.py
│   │   ├── mcp_server.py
│   │   └── examples.py
│   ├── governance/         # Safety & compliance
│   │   ├── __init__.py
│   │   ├── engine.py
│   │   └── safety_rules.py
│   ├── knowledge/          # Knowledge & retrieval
│   │   ├── __init__.py
│   │   ├── knowledge_base.py
│   │   └── retrieval.py
│   ├── models/             # Model layer (conceptual)
│   │   └── __init__.py
│   ├── api/                # API layer (future)
│   │   └── __init__.py
│   └── utils/              # Utilities
│       ├── __init__.py
│       ├── config.py
│       └── logging.py
├── config/                 # Configuration
│   └── config.example.yaml
├── docs/                   # Documentation
│   ├── architecture.md
│   ├── agents.md
│   ├── mcp_tools.md
│   └── safety.md
├── tests/                  # Tests
│   ├── unit/
│   ├── integration/
│   └── examples/
├── README.md
├── requirements.txt
├── setup.py
└── .gitignore
```

## Core Components Overview

### 1. Agentic Orchestration Layer
- **BaseAgent**: Implements ReAct pattern with planning, reflection, and tool use
- **SpecializedAgent**: Base for medical domain agents
- **Agent Templates**: Pre-built agents for common medical tasks

### 2. Clinical Intelligence Layer
- **RecommendationWorkflow**: Orchestrates multi-agent workflows
- **Recommendation Types**: Structured recommendation outputs
- **Human Approval Gates**: Mandatory approval workflow

### 3. Knowledge & Retrieval Layer
- **KnowledgeBase**: Main knowledge management
- **RetrievalEngine**: Abstract retrieval interface
- **HybridRetrievalEngine**: Combines dense and sparse search
- Supports RAG, CAG, and other augmentation techniques

### 4. Safety & Governance Layer
- **GovernanceEngine**: Enforces safety rules
- **SafetyRule**: Base class for safety rules
- **ClinicalSafetyRule**: Clinical-specific safety checks
- **Audit Logging**: Complete audit trail

### 5. Tool & MCP Layer
- **ToolRegistry**: Tool management and execution
- **BaseTool**: Foundation for tools
- **MCPServer**: MCP protocol implementation
- **UserMCPServer**: Base for user-created servers

### 6. Platform Layer
- **MedAgentXPlatform**: Main platform orchestrator
- Initializes and coordinates all components

## Key Design Principles

1. **Safety First**: Human approval mandatory at architecture level
2. **Extensibility**: Users can create custom agents, tools, and MCP servers
3. **Evidence-Based**: Recommendations supported by retrieved knowledge
4. **Transparency**: Full audit logging and decision traceability
5. **Modularity**: Components are loosely coupled and replaceable

