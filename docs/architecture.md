# MedAgentX Architecture

## Overview

MedAgentX is built with 7 core layers that work together to provide a programmable, safe, and extensible platform for clinical decision support.

## Architecture Layers

### 1. Agentic Orchestration Layer

**Location:** `medagentx/core/agent.py`, `medagentx/agents/`

The agentic orchestration layer implements:
- **ReAct Pattern**: Reasoning + Acting + Tool Use
- **Task Planning**: Breaking down complex tasks into steps
- **Self-Critique**: Agents evaluate their own outputs
- **Reflection**: Agents reflect on their performance
- **Memory Management**: Episodic and clinical memory
- **Human-in-the-Loop**: Checkpoints for human approval

**Key Components:**
- `BaseAgent`: Foundation for all agents
- `SpecializedAgent`: Base for medical domain agents
- Agent templates: SymptomAnalyzer, DiagnosisSupport, MedicalCoder, etc.

### 2. Clinical Intelligence & Recommendation Layer

**Location:** `medagentx/core/workflow.py`, `medagentx/agents/`

Provides E-Doctor workflows:
- Symptom analysis
- Differential diagnosis support
- Treatment recommendations
- Risk assessment
- Medical coding support

**Key Features:**
- Multi-agent workflows
- Recommendation generation with confidence scores
- Human approval gates
- Evidence-based reasoning

### 3. Knowledge, Retrieval & Medical Memory Layer

**Location:** `medagentx/knowledge/`

Implements advanced retrieval techniques:
- **RAG** (Retrieval-Augmented Generation)
- **CAG** (Context-Augmented Generation)
- **Hybrid Search** (Dense + Sparse)
- **Multi-vector Retrieval**
- **Knowledge Graph RAG** (conceptual)

**Key Components:**
- `KnowledgeBase`: Main knowledge management
- `RetrievalEngine`: Abstract retrieval interface
- `VectorRetrievalEngine`: Dense vector search
- `HybridRetrievalEngine`: Combined dense/sparse search

### 4. Model & Training Layer

**Location:** `medagentx/models/` (conceptual)

Supports:
- Multiple LLM providers (OpenAI, Anthropic, etc.)
- Model routing
- Fine-tuning hooks
- Quantization support

### 5. Safety, Governance & Clinical Compliance Layer

**Location:** `medagentx/governance/`

**Mandatory Safety Features:**
- Human approval requirement enforcement
- Disclaimer enforcement
- Confidence threshold checks
- Tool permission validation
- Audit logging

**Key Components:**
- `GovernanceEngine`: Main governance orchestrator
- `SafetyRule`: Base class for safety rules
- `ClinicalSafetyRule`: Clinical-specific rules

### 6. Tool / MCP Builder Layer

**Location:** `medagentx/tools/`

Enables user-created tools:
- `BaseTool`: Foundation for tools
- `ToolRegistry`: Tool management and execution
- `MCPServer`: MCP protocol server base
- `UserMCPServer`: Base for user-created servers

**Features:**
- Tool sandboxing
- Permission management
- Usage tracking
- Tool discovery

### 7. API, UI & Developer Platform Layer

**Location:** `medagentx/api/` (future), `medagentx/main.py`

- Platform initialization
- Agent management
- API endpoints (to be implemented)
- CLI interface (to be implemented)

## Data Flow

```
User Input
    ↓
Workflow Engine
    ↓
Agent(s) [ReAct Loop]
    ↓
Tool Registry → Tools → MCP Servers
    ↓
Knowledge Base → Retrieval Engine
    ↓
Governance Engine [Validation]
    ↓
Recommendations [Human Approval Required]
    ↓
Approved Output
```

## Safety Architecture

Every recommendation goes through:
1. **Generation**: Agent generates recommendation
2. **Validation**: Governance engine validates
3. **Human Approval Gate**: Mandatory human review
4. **Audit Logging**: All actions logged

## Extensibility Points

1. **Custom Agents**: Extend `BaseAgent` or `SpecializedAgent`
2. **Custom Tools**: Extend `BaseTool`
3. **Custom MCP Servers**: Extend `UserMCPServer`
4. **Custom Safety Rules**: Extend `SafetyRule` or `ClinicalSafetyRule`
5. **Custom Retrieval Engines**: Extend `RetrievalEngine`

## Compliance Considerations

- **HIPAA-Friendly**: Architecture supports audit logging and access control
- **Decision Traceability**: All recommendations are versioned and tracked
- **Human Oversight**: Mandatory approval gates at architecture level

