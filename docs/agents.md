# Agent Development Guide

## Overview

Agents in MedAgentX are specialized AI entities that perform clinical decision support tasks. They follow the ReAct (Reasoning + Acting) pattern with tool use capabilities.

## Base Agent Architecture

All agents inherit from `BaseAgent` or `SpecializedAgent`:

```python
from medagentx.core.agent import BaseAgent
from medagentx.core.types import AgentConfig

class MyAgent(BaseAgent):
    async def _generate_response(self) -> str:
        # Implement custom response generation
        pass
```

## Agent Lifecycle

1. **Initialization**: Agent created with config
2. **Execution**: `execute()` called with task
3. **Planning**: Task broken down (if enabled)
4. **ReAct Loop**:
   - Reason: Determine next action
   - Act: Execute action (tool use or response)
   - Reflect: Critique and verify
5. **Completion**: Final state returned

## Built-in Agent Templates

### SymptomAnalyzerAgent
Analyzes symptoms and generates diagnostic hypotheses.

```python
from medagentx.agents import SymptomAnalyzerAgent

agent = SymptomAnalyzerAgent(config, tool_registry, governance_engine)
result = await agent.analyze_symptoms("fever and cough", patient_context)
```

### DiagnosisSupportAgent
Provides differential diagnosis support.

### MedicalCoderAgent
Handles medical coding (ICD-10, CPT, HCPCS).

### PrescriptionReviewAgent
Reviews prescriptions for safety and interactions.

### ClinicalGuidelineAgent
Retrieves and applies clinical guidelines.

### RiskAssessmentAgent
Assesses clinical risks.

## Creating Custom Agents

```python
from medagentx.agents.base_template import SpecializedAgent
from medagentx.core.types import AgentConfig, RecommendationType

class MyCustomAgent(SpecializedAgent):
    def __init__(self, config, tool_registry, governance_engine, knowledge_base):
        super().__init__(config, tool_registry, governance_engine, knowledge_base)
    
    async def _generate_response(self) -> str:
        # Custom logic
        knowledge = await self.retrieve_clinical_knowledge(query)
        # Generate response using knowledge
        return response
```

## Agent Configuration

```python
config = AgentConfig(
    agent_id="my_agent",
    agent_name="My Custom Agent",
    description="Description of what the agent does",
    model_provider="openai",
    model_name="gpt-4",
    temperature=0.3,
    max_iterations=10,
    enable_self_critique=True,
    enable_reflection=True,
    tools=["tool1", "tool2"],
    created_by="user123",
)
```

## Tool Integration

Agents use tools through the tool registry:

```python
# Tool calls are made automatically based on reasoning
# Tools must be registered in the tool registry
# Permission checks are enforced by governance engine
```

## Memory Management

Agents maintain:
- **Episodic Memory**: Recent conversation history
- **Clinical Memory**: Patient-specific clinical data
- **Long-term Knowledge**: Persistent knowledge

## Best Practices

1. Always require human approval for clinical recommendations
2. Include confidence scores
3. Provide supporting evidence
4. Include warnings and disclaimers
5. Use knowledge base for evidence-based reasoning

