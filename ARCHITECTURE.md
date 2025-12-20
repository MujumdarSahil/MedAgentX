# MedAgentX Platform Architecture v1.7

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
│   │   ├── workflow.py     # Workflow engine
│   │   ├── recommendation_engine.py  # RecommendationEngine abstraction (v1.7)
│   │   ├── prediction_model.py       # PredictionModel abstraction (v1.7)
│   │   ├── mcp_registry.py           # Extended MCP registry (v1.7)
│   │   └── squad.py                  # Squad execution model (v1.7)
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
│   ├── models/             # LLM model layer
│   │   ├── __init__.py
│   │   └── llm_engine.py   # Multi-LLM orchestration (v1.7)
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
- **RecommendationEngines**: Governed recommendation generation (v1.7)
- **PredictionModels**: Governed prediction generation (v1.7)
- **SquadExecutor**: Governed multi-agent task execution (v1.7)
- **Recommendation Types**: Structured recommendation outputs
- **Human Approval Gates**: Mandatory approval workflow

### 3. Knowledge & Retrieval Layer
- **KnowledgeBase**: Main knowledge management
- **RetrievalEngine**: Abstract retrieval interface
- **HybridRetrievalEngine**: Combines dense and sparse search
- Supports RAG, CAG, and other augmentation techniques

### 4. Safety & Governance Layer
- **GovernanceEngine**: Enforces safety rules and validates agent capabilities
- **AgentCapabilities**: Policy-constrained capability model for custom agents
- **GovernanceException**: Raised when governance policy is violated
- **SafetyRule**: Base class for safety rules
- **ClinicalSafetyRule**: Clinical-specific safety checks
- **Audit Logging**: Complete audit trail with capability violation tracking

### 5. Tool & MCP Layer
- **ToolRegistry**: Tool management and execution
- **MCPRegistry**: Extended registry for Agents, Tools, Engines, Models, Squads (v1.7)
- **BaseTool**: Foundation for tools
- **MCPServer**: MCP protocol implementation
- **UserMCPServer**: Base for user-created servers

### 6. LLM Orchestration Layer (v1.7)
- **LLMEngine**: Abstract interface for LLM providers
- **Multi-Provider Support**: OpenAI, Groq, Ollama, Anthropic, Google Gemini, Mistral, Cohere, Perplexity
- **LLMEngineFactory**: Factory for creating LLM engines
- **LLM Usage Tracking**: All LLM calls logged with provider, model, purpose, token usage

### 7. Platform Layer
- **MedAgentXPlatform**: Main platform orchestrator
- Initializes and coordinates all components

## Custom Agent Capabilities System

### Overview
The platform allows doctors/users to create custom agents safely using policy-constrained templates. All custom agents are validated against governance policies to prevent unsafe operations.

### AgentCapabilities Model
Defined in `medagentx/core/types.py`:
- `can_diagnose: bool` - Whether agent can perform diagnosis (default: False, hard-blocked)
- `can_prescribe: bool` - Whether agent can prescribe treatments (default: False, hard-blocked)
- `can_use_tools: bool` - Whether agent can use tools (default: True)
- `requires_human_approval: bool` - Whether human approval is required (default: True, cannot be disabled)

### Policy Enforcement
1. **Initialization Validation**: `GovernanceEngine.validate_agent()` checks capabilities when agent is created
2. **Runtime Enforcement**: `BaseAgent._check_capabilities()` monitors plan/act phases for violations
3. **Hard Blocks**: Diagnosis, prescription, and governance override attempts are blocked and audited

### Custom Agent Template
`SpecializedAgent` provides:
- `analyze(input_data)` - User-defined analysis logic (override in custom agents)
- Automatic capability validation on initialization and execution
- Integration with governance engine for audit logging

### Example: RiskAssessorAgent
Demonstrates a doctor-created agent for cardiac risk scoring:
- Safe capabilities: no diagnosis, no prescription, requires approval
- Implements `analyze()` method for risk calculation
- All violations are blocked and logged to audit trail

## Key Design Principles

1. **Safety First**: Human approval mandatory at architecture level; capabilities enforced at multiple layers
2. **Extensibility**: Users can create custom agents, tools, engines, models, and squads with policy constraints
3. **Evidence-Based**: Recommendations supported by retrieved knowledge
4. **Transparency**: Full audit logging and decision traceability, including capability violations and LLM usage
5. **Modularity**: Components are loosely coupled and replaceable
6. **Policy-Constrained Customization**: Custom agents cannot bypass safety mechanisms
7. **Multi-LLM Support**: Optional LLM assistance with multiple provider adapters (v1.7)
8. **Governed Execution**: Static execution graphs with no loops, no autonomy, no improvisation (v1.7)

## v1.7 New Features

### Multi-LLM Orchestration
- Support for 8+ LLM providers as interchangeable adapters
- All LLM calls logged with provider, model, purpose, and token usage
- LLMs are optional and assistive only (never decision authorities)

### Recommendation Engines
- Governed interface for clinical recommendation generation
- Deterministic and LLM-backed implementations
- MUST NOT emit diagnosis or treatment

### Prediction Models
- Governed interface for clinical prediction generation
- Deterministic and ML-backed implementations
- MUST NOT emit diagnosis or treatment

### Extended MCP Registry
- Unified registry for Agents, Tools, Engines, Models, and Squads
- Metadata validation prevents unsafe registrations
- Discovery and execution coordination

### Governed Squad Execution
- Static execution graphs (no loops)
- Explicit roles and fixed instructions
- Deterministic execution order
- Governance checks at every step

