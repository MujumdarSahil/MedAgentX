# MedAgentX Platform Architecture v2.0

## Architecture-Complete Clinical Intelligence Platform

MedAgentX v2.0 is a publishable, enterprise-grade, safety-first clinical intelligence system with complete architectural layers for deterministic behavior, replayability, and full auditability.

## Critical Safety Statements

**MedAgentX does not diagnose.**

**MedAgentX does not provide treatment or medication advice.**

**Patient data is not retained beyond defined TTL unless explicitly exported.**

All system outputs require human clinician review and approval. The Clinical Responsibility Firewall (CRF) ensures that responsibility never escalates automatically, and AI authority never increases. All recommendations, predictions, and analyses are tagged with responsibility metadata and require explicit human validation.

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
│   │   ├── recommendation_engine.py  # RecommendationEngine abstraction (v1.7, enhanced v2.0)
│   │   ├── prediction_model.py       # PredictionModel abstraction (v1.7, enhanced v2.0)
│   │   ├── mcp_registry.py           # Extended MCP registry (v1.7, enhanced v2.0)
│   │   ├── squad.py                  # Squad execution model (v1.7, enhanced v2.0)
│   │   ├── crf.py                    # Clinical Responsibility Firewall (v2.0)
│   │   ├── event_store.py            # Event Store + Audit Logging (v2.0)
│   │   ├── replay_engine.py          # Time-Travel Replay Engine (v2.0)
│   │   ├── chil.py                   # Contextual Health Intelligence Layer (v2.0)
│   │   ├── doctor_agents.py          # Doctor-Programmable Agents (v2.0)
│   │   ├── ps_aicp.py                # Patient-Specific AI Cognition Profiles (v2.0)
│   │   ├── patient_explanation_engine.py  # Patient Explanation Engine (v2.0)
│   │   ├── cde.py                    # Counterfactual Diagnosis Engine (v2.0)
│   │   └── bounded_store.py          # 24-Hour Bounded Persistence Layer (v2.0)
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
- **RecommendationEngines**: Governed recommendation generation (v1.7, enhanced v2.0)
  - Behavioral recommendations
  - Monitoring suggestions
  - Escalation triggers
  - Responsibility metadata (CRF)
- **PredictionModels**: Governed prediction generation (v1.7, enhanced v2.0)
  - Probability bands (not single-point)
  - Responsibility metadata (CRF)
- **SquadExecutor**: Governed multi-agent task execution (v1.7, enhanced v2.0)
  - CRF enforcement at every step
  - Full audit trail
- **Recommendation Types**: Structured recommendation outputs
- **Human Approval Gates**: Mandatory approval workflow

### 3. Knowledge & Retrieval Layer
- **KnowledgeBase**: Main knowledge management
- **RetrievalEngine**: Abstract retrieval interface
- **HybridRetrievalEngine**: Combines dense and sparse search
- Supports RAG, CAG, and other augmentation techniques

### 4. Safety & Governance Layer
- **GovernanceEngine**: Enforces safety rules and validates agent capabilities
- **ClinicalResponsibilityFirewall (CRF)**: v2.0 - Enforces responsibility boundaries
  - All outputs tagged: AI_SUGGESTED, DOCTOR_VALIDATED, DOCTOR_OVERRIDDEN
  - Responsibility never escalates automatically
  - Immutable and auditable metadata
- **AgentCapabilities**: Policy-constrained capability model for custom agents
- **CapabilityFirewall**: v2.0 - Architectural limits non-overridable
- **GovernanceException**: Raised when governance policy is violated
- **SafetyRule**: Base class for safety rules
- **ClinicalSafetyRule**: Clinical-specific safety checks
- **Audit Logging**: Complete audit trail with capability violation tracking
- **Event Store**: v2.0 - Append-only event storage for deterministic replay

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

### 8. Contextual Intelligence Layer (v2.0)
- **ContextualHealthIntelligenceLayer (CHIL)**: Context fusion for risk amplification
  - Geographic context (privacy-safe, coarse-grained)
  - Weather context (temperature, humidity, air quality)
  - Lifestyle signals (diet, activity, sleep, stress)
  - Temporal context (season, time of day)
  - Deterministic correlation and risk amplification only
  - NO diagnosis or treatment

### 9. Replay & Audit Layer (v2.0)
- **EventStore**: Append-only event storage
  - Every execution step stored as structured JSON
  - Timestamps, agent/tool IDs, responsibility tags, confidence, evidence
  - No overwrites allowed
  - JSON export functionality
- **ReplayEngine**: Time-travel replay engine
  - Re-run past workflows using stored events
  - Support modified inputs, updated guidelines, altered context
  - Delta comparison between original and replay
  - Deterministic and auditable

### 10. Patient Communication Layer (v2.0)
- **Patient-Specific AI Cognition Profiles (PS-AICP)**: Policy-based communication adaptation
  - Profiles are POLICY-BASED (not psychological or medical diagnoses)
  - Profiles affect ONLY communication style, tone, and explanation depth
  - Profiles are immutable during a session
  - Profiles NEVER affect reasoning, predictions, recommendations, or capabilities
  - Capability Firewall and CRF remain fully authoritative
  - Predefined profiles: ANXIOUS, TECH_SAVVY, ELDERLY, CHRONIC_CONDITION, DEFAULT
  - Each profile defines: verbosity_level, reassurance_level, jargon_allowed, evidence_depth, longitudinal_memory_emphasis
- **Patient Explanation Engine**: Consumes PS-AICP profiles to adapt patient-facing explanations
  - ONLY affects patient-facing communication
  - NEVER affects clinician-facing outputs
  - NEVER affects reasoning, predictions, or recommendations
  - CRF responsibility tagging remains unchanged
  - Hard safety rules: PS-AICP must NEVER influence predictions, recommendations, risk scores, or escalation logic

### 11. Counterfactual Analysis Layer (v2.0)
- **Counterfactual Diagnosis Engine (CDE)**: Non-diagnostic, bias-reduction and decision-support module
  - Generates controlled counterfactual scenarios by removing or altering EXACTLY ONE symptom or ONE contextual variable at a time
  - Executes counterfactuals via the existing deterministic Replay Engine
  - Produces structured delta reports containing:
    - What changed
    - What remained stable
    - Confidence shifts (if any)
    - Explicit uncertainty markers
  - Mandatory labeling: "Counterfactual Analysis — Non-Diagnostic Decision Support"
  - Hard constraints:
    - Must NOT generate diagnoses
    - Must NOT rank diseases
    - Must NOT suggest treatments or medications
    - Must NOT override clinician authority
  - Permitted use cases:
    - Anchoring bias reduction
    - Alternate explanation comparison
    - Rare condition surfacing WITHOUT naming conditions

### 12. Bounded Persistence Layer (v2.0)
- **Bounded Store**: 24-hour bounded persistence layer for short-term memory and logs
  - Privacy-safe, bounded persistence layer
  - ABSOLUTE CONSTRAINTS:
    - NO external databases (no SQL, MongoDB, Redis, cloud storage)
    - Local file-based encrypted storage ONLY
    - Deterministic behavior required
    - Explicit data lifecycle visibility required
  - Data types stored:
    - Event logs
    - Replay traces
    - Session memory summaries
  - Retention rules:
    - Default retention window: 24 hours (configurable constant)
    - TTL enforced on BOTH read and write
    - Auto-purge expired records deterministically
  - MANDATORY EXCEL ARCHIVAL REQUIREMENT:
    - Before ANY data is deleted due to TTL expiry:
      - Generate an Excel (.xlsx) summary file
      - Include: Timestamp, Session ID, Agent/Squad identifiers, Responsibility tags (CRF), High-level outcome summaries ONLY (no raw PHI)
      - Store Excel files in a designated /archives/ directory
      - Excel files are read-only records for compliance/audit purposes
      - After Excel export → purge in-memory and encrypted files
  - Additional features:
    - Manual purge API
    - Explicit Export-to-JSON API (full fidelity, responsibility preserved)
    - Clear separation between:
      - ephemeral operational data
      - exported compliance artifacts
  - Integration:
    - Event Store writes to bounded store
    - Replay Engine reads ONLY from bounded store or exported artifacts
    - No silent persistence allowed
    - No background retention beyond TTL

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
2. **Responsibility Boundaries**: CRF enforces that responsibility never escalates automatically; AI authority never increases
3. **Deterministic Behavior**: System must be deterministic and replayable; LLMs are optional and assistive only
4. **Extensibility**: Users can create custom agents, tools, engines, models, and squads with policy constraints
5. **Evidence-Based**: Recommendations supported by retrieved knowledge
6. **Transparency**: Full audit logging and decision traceability, including capability violations, LLM usage, and responsibility tags
7. **Modularity**: Components are loosely coupled and replaceable
8. **Policy-Constrained Customization**: Custom agents cannot bypass safety mechanisms
9. **Multi-LLM Support**: Optional LLM assistance with multiple provider adapters (v1.7, complete v2.0)
10. **Governed Execution**: Static execution graphs with no loops, no autonomy, no improvisation (v1.7, enhanced v2.0)
11. **Replayability**: All executions are stored and can be replayed deterministically (v2.0)
12. **Contextual Intelligence**: Context fusion for risk amplification without diagnosis (v2.0)
13. **Patient Communication Adaptation**: Policy-based communication profiles that NEVER affect clinical reasoning (v2.0)
14. **Counterfactual Analysis**: Non-diagnostic bias reduction and decision support (v2.0)
15. **Bounded Data Retention**: Explicit TTL with Excel archival before deletion (v2.0)

## v2.0 New Features (Architecture-Complete)

### Clinical Responsibility Firewall (CRF)
- Every output tagged with responsibility level (AI_SUGGESTED, DOCTOR_VALIDATED, DOCTOR_OVERRIDDEN)
- Responsibility NEVER escalates automatically (even with high confidence)
- AI authority never increases
- Immutable and auditable metadata
- Enforced at: Agent output, Recommendation engine output, Prediction model output, Workflow aggregation

### Event Store + Audit Logging
- Append-only event store for every execution step
- Structured JSON events with timestamps, responsibility tags, confidence, evidence
- Support for deterministic replay from stored events
- No overwrites allowed
- JSON export functionality

### Time-Travel Replay Engine
- Re-run past workflows using stored events
- Support modified inputs, updated guideline versions, altered environmental context
- Delta comparison between original and replay
- Deterministic and auditable

### Contextual Health Intelligence Layer (CHIL)
- Context fusion layer ingesting:
  - Geography (coarse, privacy-safe)
  - Weather (temperature, humidity, air quality)
  - Seasonality
  - Lifestyle signals (diet, activity, sleep, stress)
  - Temporal history
- Rules: No diagnosis, only correlation and risk amplification, fully deterministic, all logic auditable

### Enhanced Recommendation Engine Framework
- Behavioral recommendations
- Monitoring suggestions
- Escalation triggers
- Responsibility metadata (CRF)
- human_approval_required = true (always)

### Enhanced Prediction Model Framework
- Probability bands (not single-point estimates)
- Responsibility metadata (CRF)
- Explanation and evidence
- human_approval_required = true (always)

### Doctor-Programmable Agents
- Configuration-driven agents that doctors can define:
  - Agent name, role, allowed tasks, forbidden tasks, escalation rules
- Capability Firewall: Authority limits are architectural and non-overridable
- Patients can only use doctor-created agents

### Extended MCP Registry
- Support for forbidden_outputs (explicit forbidden output types)
- Enhanced governance constraints validation
- Registration of Agents, Tools, Engines, Models, Squads with full metadata

### Enhanced Squad Execution Engine
- CRF enforcement at every step
- Full audit trail with responsibility tags
- Deterministic execution with no loops

### Multi-LLM Orchestration (Complete)
- Support for: Anthropic Claude, Google Gemini, Mistral AI, Cohere, Perplexity (in addition to OpenAI, Groq, Ollama)
- LLMs assist reasoning only (no decisions, no authority)
- Track provider, model, purpose, token usage
- Deterministic mode still works without LLMs

### Streamlit UI Extensions
- New tabs: Engines, Models, Squads, Replay / Audit
- Show confidence and responsibility tags
- Clearly mark "Human Approval Required"
- Allow replay and export

### Patient-Specific AI Cognition Profiles (PS-AICP)
- Policy-based communication adaptation system
- Profiles affect ONLY communication style, tone, and explanation depth
- Profiles are immutable during a session
- Profiles NEVER affect reasoning, predictions, recommendations, or capabilities
- Integration: PS-AICP is consumed ONLY by the Patient Explanation Engine
- Clinician-facing outputs are NEVER modified
- CRF responsibility tagging (AI_SUGGESTED / DOCTOR_VALIDATED / DOCTOR_OVERRIDDEN) remains unchanged

### Counterfactual Diagnosis Engine (CDE)
- Non-diagnostic, bias-reduction and decision-support module
- Decision-science framing for anchoring bias reduction
- Bias mitigation purpose
- Explicit prohibition of diagnosis/treatment
- Mandatory labeling: "Counterfactual Analysis — Non-Diagnostic Decision Support"
- Generates controlled counterfactual scenarios (one modification at a time)
- Executes via deterministic Replay Engine
- Produces structured delta reports

### 24-Hour Bounded Persistence Layer
- Privacy-safe, bounded persistence for short-term memory and logs
- Local file-based encrypted storage ONLY (no external databases)
- 24-hour TTL policy (configurable)
- Excel archival before deletion (mandatory)
- Explicit user/doctor-controlled exports
- Privacy guarantees and PHI minimization
- Data lifecycle visibility required

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

