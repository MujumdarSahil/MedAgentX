"""
Streamlit-based UI for MedAgentX v1.6

Features:
- Dashboard
- Symptom Analysis
- LLM Configuration
- Agents
- Tools
- Workflows
- Audit Logs
"""

import streamlit as st
import json
import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional
import sys
import os
import logging

logger = logging.getLogger(__name__)

# Load .env file if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, use system environment variables

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from medagentx.core.workflow import RecommendationWorkflow
from medagentx.core.types import AgentConfig
from medagentx.governance.engine import GovernanceEngine
from medagentx.knowledge.knowledge_base import KnowledgeBase
from medagentx.knowledge.medical_coding import MedicalCodingKB
from medagentx.knowledge.embeddings import AdaptiveMemory, EmbeddingEngine
from medagentx.tools.tool_registry import ToolRegistry
from medagentx.agents import (
    SymptomAnalyzerAgent,
    DiagnosisSupportAgent,
    MedicalCoderAgent,
    RiskScorerAgent,
)
from medagentx.tools.examples import ICD10CodingTool
from medagentx.models.llm_engine import (
    LLMEngineFactory,
    LLMProvider,
    LLMEngine,
)


# Page configuration
st.set_page_config(
    page_title="MedAgentX v1.6",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize session state
if "workflow" not in st.session_state:
    st.session_state.workflow = None
if "audit_logs" not in st.session_state:
    st.session_state.audit_logs = []
if "agents" not in st.session_state:
    st.session_state.agents = {}
if "tools" not in st.session_state:
    st.session_state.tools = {}
if "memory" not in st.session_state:
    st.session_state.memory = None
if "llm_configs" not in st.session_state:
    st.session_state.llm_configs = {}  # Agent ID -> LLM config
if "llm_engines" not in st.session_state:
    st.session_state.llm_engines = {}  # Provider -> LLM engine instance


def get_llm_engine_for_agent(agent_id: str) -> Optional[LLMEngine]:
    """Get LLM engine for agent based on configuration."""
    config = st.session_state.llm_configs.get(agent_id)
    if not config or config.get("provider") == "none":
        return None
    
    provider_str = config.get("provider", "none")
    try:
        provider = LLMProvider(provider_str)
    except ValueError:
        return None
    
    # Cache engine instances
    cache_key = f"{provider.value}_{config.get('model', 'default')}"
    if cache_key not in st.session_state.llm_engines:
        try:
            engine = LLMEngineFactory.create(provider, **{k: v for k, v in config.items() if k != "provider"})
            if engine.is_available():
                st.session_state.llm_engines[cache_key] = engine
            else:
                return None
        except Exception as e:
            logger.warning(f"Failed to create LLM engine: {e}")
            return None
    
    return st.session_state.llm_engines.get(cache_key)


def initialize_system():
    """Initialize MedAgentX system components."""
    if st.session_state.workflow is None:
        governance = GovernanceEngine()
        knowledge = KnowledgeBase()
        coding_kb = MedicalCodingKB()
        tool_registry = ToolRegistry()
        
        # Register tools
        tool_registry.register_tool(ICD10CodingTool(coding_kb))
        
        # Initialize embeddings/memory
        embedding_engine = EmbeddingEngine()
        memory = AdaptiveMemory(embedding_engine)
        st.session_state.memory = memory
        
        # Initialize LLM engines if not already done
        if not st.session_state.llm_engines:
            available_providers = LLMEngineFactory.get_available_providers()
            for provider in available_providers:
                if provider != LLMProvider.NONE:
                    try:
                        engine = LLMEngineFactory.create(provider)
                        if engine.is_available():
                            cache_key = f"{provider.value}_default"
                            st.session_state.llm_engines[cache_key] = engine
                    except Exception:
                        pass
        
        # Create agents with optional LLM engines
        agents = {}
        agent_configs = [
            {
                "id": "symptom_analyzer",
                "name": "Symptom Analyzer",
                "desc": "Symptom structuring only; no diagnosis.",
                "class": SymptomAnalyzerAgent,
            },
            {
                "id": "diagnosis_support",
                "name": "Diagnosis Support",
                "desc": "Supportive reasoning only; no definitive diagnosis.",
                "class": DiagnosisSupportAgent,
            },
            {
                "id": "medical_coder",
                "name": "Medical Coder",
                "desc": "Maps supportive findings to ICD-10/CPT suggestions.",
                "class": MedicalCoderAgent,
            },
            {
                "id": "risk_scorer",
                "name": "Risk Scorer",
                "desc": "Numeric risk scoring support only; no diagnosis or treatment.",
                "class": RiskScorerAgent,
            },
        ]
        
        for agent_cfg in agent_configs:
            llm_engine = get_llm_engine_for_agent(agent_cfg["id"])
            agents[agent_cfg["id"]] = agent_cfg["class"](
                AgentConfig(
                    agent_id=agent_cfg["id"],
                    agent_name=agent_cfg["name"],
                    description=agent_cfg["desc"],
                    created_by="system",
                ),
                tool_registry,
                governance,
                knowledge,
                llm_engine=llm_engine,
            )
        
        # Create workflow
        workflow = RecommendationWorkflow(
            workflow_id="main_workflow",
            agents=agents,
            governance_engine=governance,
        )
        
        st.session_state.workflow = workflow
        st.session_state.agents = agents
        st.session_state.tools = {
            "icd10_coding": ICD10CodingTool(coding_kb),
        }


def run_async(coro):
    """Run async function in Streamlit."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


# Sidebar navigation
st.sidebar.title("🏥 MedAgentX v1.6")
st.sidebar.markdown("**Clinical Decision Support Platform**")

page = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "Symptom Analysis", "LLM Configuration", "Agents", "Tools", "Workflows", "Audit Logs"],
)

# Initialize system
initialize_system()

# Dashboard
if page == "Dashboard":
    st.title("📊 Dashboard")
    st.markdown("### Welcome to MedAgentX v1.6")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Active Agents", len(st.session_state.agents))
    
    with col2:
        st.metric("Available Tools", len(st.session_state.tools))
    
    with col3:
        st.metric("Audit Log Entries", len(st.session_state.audit_logs))
    
    with col4:
        memory_stats = st.session_state.memory.get_stats() if st.session_state.memory else {}
        st.metric("Memory Entries", memory_stats.get("total_entries", 0))
    
    st.markdown("---")
    st.markdown("### System Status")
    st.success("✅ All systems operational")
    st.info("ℹ️ This is a supportive tool. All outputs require human approval.")

# Symptom Analysis
elif page == "Symptom Analysis":
    st.title("🔍 Symptom Analysis")
    
    with st.form("symptom_analysis_form"):
        symptoms_text = st.text_area(
            "Enter Symptoms",
            placeholder="e.g., fever, cough for three days, chest pain",
            height=100,
        )
        
        col1, col2 = st.columns(2)
        with col1:
            age = st.number_input("Age", min_value=0, max_value=120, value=50)
            systolic_bp = st.number_input("Systolic BP", min_value=0, max_value=300, value=120)
        with col2:
            cholesterol = st.number_input("Cholesterol", min_value=0, max_value=500, value=200)
            smoker = st.checkbox("Smoker")
            diabetes = st.checkbox("Diabetes")
        
        analyze_button = st.form_submit_button("🔬 Analyze Symptoms", use_container_width=True)
    
    if analyze_button:
        if not symptoms_text:
            st.error("⚠️ Please enter symptoms to analyze.")
        else:
            with st.spinner("Analyzing symptoms..."):
                try:
                    # Ensure workflow is initialized
                    if st.session_state.workflow is None:
                        initialize_system()
                    
                    # Run workflow
                    result = run_async(st.session_state.workflow.run(symptoms_text))
                    
                    # Store in audit logs
                    st.session_state.audit_logs.append({
                        "timestamp": datetime.now().isoformat(),
                        "action": "symptom_analysis",
                        "input": symptoms_text,
                        "result": result,
                    })
                    
                    # Display results - Clinical JSON Output
                    st.markdown("---")
                    st.markdown("### 📋 Clinical Analysis Results")
                    st.info("ℹ️ **LLMs assist reasoning only. All outputs require human approval.**")
                    
                    # Show full clinical JSON output
                    st.markdown("#### Complete Clinical JSON Output")
                    st.json(result)
                    
                    st.markdown("---")
                    
                    # Structured Symptoms
                    st.markdown("#### Structured Symptoms")
                    structured_symptoms = result.get("structured_symptoms", [])
                    if structured_symptoms:
                        st.json(structured_symptoms)
                    else:
                        st.warning("No structured symptoms found.")
                    
                    # Supportive Conditions
                    st.markdown("#### Supportive Conditions")
                    support = result.get("support", {})
                    conditions = support.get("conditions", [])
                    evidence = support.get("evidence", [])
                    
                    for condition in conditions:
                        st.markdown(f"- **{condition}**")
                    
                    if evidence:
                        with st.expander("Evidence"):
                            for ev in evidence:
                                st.markdown(f"- {ev}")
                    
                    # ICD-10 Codes
                    st.markdown("#### ICD-10 Recommendations")
                    coding = result.get("coding", {})
                    icd10_codes = coding.get("icd10_recommendations", [])
                    
                    if icd10_codes:
                        for code_entry in icd10_codes[:5]:  # Show top 5
                            st.markdown(f"**{code_entry.get('code')}**: {code_entry.get('description')}")
                            st.markdown(f"  - Confidence: {code_entry.get('confidence', 0):.2%}")
                            st.markdown(f"  - Evidence: {code_entry.get('evidence', 'N/A')}")
                    
                    # CPT/HCPCS Codes
                    cpt_hcpcs = coding.get("cpt_hcpcs_recommendations", [])
                    if cpt_hcpcs:
                        st.markdown("#### CPT/HCPCS Recommendations")
                        for code_entry in cpt_hcpcs[:5]:  # Show top 5
                            st.markdown(f"**{code_entry.get('code')}** ({code_entry.get('code_type')}): {code_entry.get('description')}")
                            st.markdown(f"  - Confidence: {code_entry.get('confidence', 0):.2%}")
                    
                    # Risk Assessment
                    risk_assessment = result.get("risk_assessment")
                    if risk_assessment:
                        st.markdown("#### Risk Assessment")
                        risk_score = risk_assessment.get("risk_score", 0)
                        normalized_score = risk_assessment.get("normalized_score", 0)
                        risk_level = risk_assessment.get("risk_level", "Unknown")
                        
                        st.metric("Risk Score", f"{normalized_score:.1f}/100", f"{risk_level} Risk")
                        st.markdown(f"**Risk Level**: {risk_level}")
                        st.markdown(f"**Total Risk Score**: {risk_score:.2f}")
                        
                        risk_factors = risk_assessment.get("risk_factors", [])
                        if risk_factors:
                            st.markdown("**Risk Factors**:")
                            for factor in risk_factors:
                                st.markdown(f"- {factor}")
                        
                        evidence_list = risk_assessment.get("evidence", [])
                        if evidence_list:
                            with st.expander("Risk Assessment Evidence"):
                                for ev in evidence_list:
                                    st.markdown(f"- {ev}")
                    
                    # Confidence Scores
                    st.markdown("#### Confidence Scores")
                    workflow_confidence = result.get("workflow_confidence", {})
                    st.json(workflow_confidence)
                    
                    # Human Approval Flag
                    st.markdown("#### ⚠️ Human Approval Required")
                    requires_approval = result.get("requires_human_approval", True)
                    if requires_approval:
                        st.warning("⚠️ This analysis requires human clinician approval before use.")
                    
                    # Evidence Trace
                    st.markdown("#### Evidence Trace")
                    trace = result.get("trace", [])
                    with st.expander("View Full Trace"):
                        st.json(trace)
                    
                    # LLM Usage Display
                    st.markdown("#### LLM Usage")
                    llm_usage_found = False
                    for event in trace:
                        if isinstance(event, dict) and event.get("llm_usage"):
                            llm_usage_found = True
                            agent_name = event.get("agent_name", "Unknown")
                            llm_info = event["llm_usage"]
                            with st.expander(f"LLM Usage: {agent_name}"):
                                st.json(llm_info)
                                if llm_info.get("model"):
                                    st.info(f"**Model**: {llm_info.get('model')} | **Provider**: {llm_info.get('provider')} | **Purpose**: {llm_info.get('purpose')}")
                    if not llm_usage_found:
                        st.info("No LLM usage in this analysis (deterministic mode).")
                    
                    # Visualization Metadata
                    if trace:
                        st.markdown("#### Workflow Visualization")
                        visualization_data = []
                        for event in trace:
                            if isinstance(event, dict) and event.get("visualization_metadata"):
                                visualization_data.append(event["visualization_metadata"])
                        
                        if visualization_data:
                            st.json(visualization_data)
                
                except Exception as e:
                    st.error(f"❌ **Error during analysis**")
                    st.error(f"Error message: {str(e)}")
                    with st.expander("🔍 Technical Details"):
                        st.exception(e)
                    st.info("💡 **Tip**: Check that the workflow is properly initialized and all agents are available.")
                    
                    # Show LLM usage if available
                    if result and "trace" in result:
                        st.markdown("#### LLM Usage")
                        llm_usage_found = False
                        for event in result.get("trace", []):
                            if isinstance(event, dict) and event.get("llm_usage"):
                                llm_usage_found = True
                                llm_info = event["llm_usage"]
                                st.json(llm_info)
                        if not llm_usage_found:
                            st.info("No LLM usage in this analysis (deterministic mode).")

# LLM Configuration
elif page == "LLM Configuration":
    st.title("⚙️ LLM Configuration")
    st.markdown("### Multi-LLM Orchestration Layer")
    st.info("ℹ️ **LLMs are optional. System runs in deterministic mode without LLMs.**")
    st.warning("⚠️ **LLMs assist reasoning only. They do NOT provide diagnosis or treatment.**")
    
    # Show available providers
    st.markdown("### Available LLM Providers")
    available_providers = LLMEngineFactory.get_available_providers()
    
    provider_status = {}
    for provider in [LLMProvider.OPENAI, LLMProvider.GROQ, LLMProvider.OLLAMA, LLMProvider.NONE]:
        is_available = provider in available_providers
        provider_status[provider.value] = is_available
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("OpenAI", "✅" if provider_status.get("openai") else "❌")
    with col2:
        st.metric("Groq", "✅" if provider_status.get("groq") else "❌")
    with col3:
        st.metric("Ollama", "✅" if provider_status.get("ollama") else "❌")
    with col4:
        st.metric("None (Default)", "✅ Always")
    
    st.markdown("---")
    st.markdown("### Configure LLM per Agent")
    
    # Agent LLM configuration
    agents = st.session_state.agents
    if not agents:
        st.info("Initialize system first by visiting Dashboard or Symptom Analysis.")
    else:
        for agent_id, agent in agents.items():
            with st.expander(f"**{agent_id.replace('_', ' ').title()}**"):
                current_config = st.session_state.llm_configs.get(agent_id, {"provider": "none"})
                
                provider_options = ["none"] + [p.value for p in available_providers if p != LLMProvider.NONE]
                selected_provider = st.selectbox(
                    f"LLM Provider for {agent_id}",
                    provider_options,
                    index=provider_options.index(current_config.get("provider", "none")),
                    key=f"llm_provider_{agent_id}",
                )
                
                model_name = current_config.get("model", "")
                if selected_provider == "openai":
                    model_name = st.text_input(
                        "Model Name",
                        value=model_name or "gpt-4o-mini",
                        key=f"llm_model_{agent_id}",
                    )
                elif selected_provider == "groq":
                    model_name = st.text_input(
                        "Model Name",
                        value=model_name or "llama-3.1-8b-instant",
                        key=f"llm_model_{agent_id}",
                    )
                elif selected_provider == "ollama":
                    model_name = st.text_input(
                        "Model Name",
                        value=model_name or "llama3.2",
                        key=f"llm_model_{agent_id}",
                    )
                    base_url = st.text_input(
                        "Ollama Base URL",
                        value=current_config.get("base_url", "http://localhost:11434"),
                        key=f"ollama_url_{agent_id}",
                    )
                
                if st.button(f"Apply Configuration", key=f"apply_{agent_id}"):
                    config = {"provider": selected_provider}
                    if model_name:
                        config["model"] = model_name
                    if selected_provider == "ollama" and "base_url" in locals():
                        config["base_url"] = base_url
                    
                    st.session_state.llm_configs[agent_id] = config
                    st.success(f"✅ Configuration saved for {agent_id}")
                    st.info("🔄 **Restart the system** (reload page) for changes to take effect.")
    
    st.markdown("---")
    st.markdown("### LLM Usage Constraints")
    st.markdown("""
    LLMs may **ONLY** be used for:
    - ✅ Symptom normalization
    - ✅ Reasoning plan generation
    - ✅ Evidence summarization
    - ✅ Explanation of ICD/CPT codes
    
    LLMs **CANNOT** be used for:
    - ❌ Final diagnosis
    - ❌ Treatment recommendations
    - ❌ Prescription decisions
    
    All LLM outputs:
    - Pass through governance
    - Require human approval
    - Are tracked in audit logs
    """)

# Agents
elif page == "Agents":
    st.title("🤖 Agents")
    st.markdown("### Agent Builder & Management")
    st.info("ℹ️ **Create custom support agents. All agents are validated against governance policies.**")
    
    st.markdown("### Available Agents")
    
    agents = st.session_state.agents
    if not agents:
        st.info("No agents available. Initialize system first.")
    else:
        for agent_id, agent in agents.items():
            with st.expander(f"**{agent_id.replace('_', ' ').title()}**"):
                config = agent.config
                st.markdown(f"**Name**: {config.agent_name}")
                st.markdown(f"**Description**: {config.description}")
                st.markdown(f"**ID**: {config.agent_id}")
                st.markdown(f"**Created By**: {config.created_by}")
                
                # Show capabilities
                if hasattr(agent, "capabilities"):
                    caps = agent.capabilities
                    st.markdown("**Capabilities**:")
                    st.markdown(f"- Can Diagnose: ❌ (hard-blocked)")
                    st.markdown(f"- Can Prescribe: ❌ (hard-blocked)")
                    st.markdown(f"- Can Use Tools: {'✅' if caps.can_use_tools else '❌'}")
                    st.markdown(f"- Requires Approval: ✅ (always)")
                
                # Show LLM usage
                if hasattr(agent, "llm_engine") and agent.llm_engine:
                    llm_info = f"{agent.llm_engine.provider.value} - {agent.llm_engine.model_name}"
                    st.markdown(f"**LLM**: {llm_info}")
                else:
                    st.markdown("**LLM**: None (deterministic mode)")
                
                # Agent state
                state = agent.get_state()
                st.markdown(f"**Status**: {state.status.value}")
                
                # Execute agent
                if st.button(f"Execute {agent_id}", key=f"exec_{agent_id}"):
                    task_input = st.text_input(f"Task for {agent_id}", key=f"task_{agent_id}")
                    if task_input:
                        with st.spinner(f"Executing {agent_id}..."):
                            try:
                                result = run_async(agent.run(task_input))
                                st.json(result)
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
    
    st.markdown("---")
    st.markdown("### Create New Agent (MCP & Agent Builder)")
    st.warning("⚠️ **All custom agents are support-only. Diagnosis and prescription are hard-blocked.**")
    
    with st.form("create_agent_form"):
        col1, col2 = st.columns(2)
        with col1:
            agent_id = st.text_input("Agent ID", placeholder="e.g., custom_support_agent")
            agent_name = st.text_input("Agent Name", placeholder="Custom Support Agent")
        with col2:
            agent_type = st.selectbox(
                "Agent Type",
                ["symptom_analyzer", "diagnosis_support", "medical_coder", "risk_scorer"],
                help="Select base agent template"
            )
        
        description = st.text_area(
            "Description",
            placeholder="Supportive agent for...",
            help="Describe the agent's purpose (support-only, no diagnosis)"
        )
        
        # Tool assignment
        st.markdown("#### Assign Tools")
        available_tools = list(st.session_state.tools.keys()) if st.session_state.tools else []
        selected_tools = st.multiselect(
            "Select Tools",
            available_tools,
            help="Select MCP tools this agent can use"
        )
        
        # LLM assignment
        st.markdown("#### Assign LLM (Optional)")
        available_providers = LLMEngineFactory.get_available_providers()
        llm_provider = st.selectbox(
            "LLM Provider",
            [p.value for p in available_providers],
            index=0 if LLMProvider.NONE in available_providers else 1,
            help="Select LLM provider (None = deterministic mode)"
        )
        
        llm_model = ""
        if llm_provider != "none":
            if llm_provider == "openai":
                llm_model = st.text_input("Model Name", value="gpt-4o-mini", key="create_llm_model")
            elif llm_provider == "groq":
                llm_model = st.text_input("Model Name", value="llama-3.1-8b-instant", key="create_llm_model")
            elif llm_provider == "ollama":
                llm_model = st.text_input("Model Name", value="llama3.2", key="create_llm_model")
        
        if st.form_submit_button("🔨 Create Agent", use_container_width=True):
            if not agent_id or not agent_name:
                st.error("⚠️ Agent ID and Name are required.")
            elif agent_id in agents:
                st.error(f"⚠️ Agent with ID '{agent_id}' already exists.")
            else:
                try:
                    # Get agent class
                    agent_map = {
                        "symptom_analyzer": SymptomAnalyzerAgent,
                        "diagnosis_support": DiagnosisSupportAgent,
                        "medical_coder": MedicalCoderAgent,
                        "risk_scorer": RiskScorerAgent,
                    }
                    agent_class = agent_map.get(agent_type)
                    
                    if not agent_class:
                        st.error(f"⚠️ Unknown agent type: {agent_type}")
                    else:
                        # Get system components
                        if st.session_state.workflow is None:
                            initialize_system()
                        
                        governance = st.session_state.workflow.governance_engine
                        knowledge = KnowledgeBase()
                        tool_registry = ToolRegistry()
                        
                        # Register selected tools
                        for tool_id in selected_tools:
                            if tool_id in st.session_state.tools:
                                tool_registry.register_tool(st.session_state.tools[tool_id])
                        
                        # Create LLM engine if specified
                        llm_engine = None
                        if llm_provider != "none":
                            try:
                                provider = LLMProvider(llm_provider)
                                llm_config = {"provider": llm_provider}
                                if llm_model:
                                    llm_config["model"] = llm_model
                                llm_engine = LLMEngineFactory.create_from_config(llm_config)
                                if not llm_engine.is_available():
                                    st.warning(f"⚠️ LLM engine not available, creating agent without LLM.")
                                    llm_engine = None
                            except Exception as e:
                                st.warning(f"⚠️ Failed to create LLM engine: {e}. Creating agent without LLM.")
                                llm_engine = None
                        
                        # Create agent config
                        config = AgentConfig(
                            agent_id=agent_id,
                            agent_name=agent_name,
                            description=description or "Custom support agent",
                            created_by="user",
                        )
                        
                        # Create agent with safe capabilities
                        from medagentx.core.types import AgentCapabilities
                        capabilities = AgentCapabilities(
                            can_diagnose=False,  # Hard-blocked
                            can_prescribe=False,  # Hard-blocked
                            can_use_tools=len(selected_tools) > 0,
                            requires_human_approval=True,  # Always required
                        )
                        
                        # Create agent instance
                        agent = agent_class(
                            config=config,
                            tool_registry=tool_registry,
                            governance_engine=governance,
                            knowledge_base=knowledge,
                            capabilities=capabilities,
                            llm_engine=llm_engine,
                        )
                        
                        # Validate agent (governance check)
                        try:
                            governance.validate_agent(agent, capabilities)
                            
                            # Add to agents
                            agents[agent_id] = agent
                            st.session_state.agents = agents
                            
                            # Store LLM config if LLM assigned
                            if llm_engine:
                                st.session_state.llm_configs[agent_id] = {
                                    "provider": llm_provider,
                                    "model": llm_model,
                                }
                            
                            st.success(f"✅ Agent '{agent_id}' created successfully!")
                            st.info("🔄 **Note**: Agent is ready to use. Restart system to include in workflow.")
                        except Exception as gov_error:
                            st.error(f"❌ Governance validation failed: {str(gov_error)}")
                            st.info("💡 All agents must comply with governance policies (no diagnosis, no prescription).")
                
                except Exception as e:
                    st.error(f"❌ Error creating agent: {str(e)}")
                    with st.expander("🔍 Technical Details"):
                        st.exception(e)

# Tools
elif page == "Tools":
    st.title("🔧 Tools")
    
    st.markdown("### Available MCP Tools")
    
    tools = st.session_state.tools
    for tool_id, tool in tools.items():
        with st.expander(f"**{tool_id.replace('_', ' ').title()}**"):
            schema = tool.schema
            st.markdown(f"**Name**: {schema.name}")
            st.markdown(f"**Description**: {schema.description}")
            st.markdown(f"**Created By**: {tool.created_by}")
    
    st.markdown("---")
    st.markdown("### Create New Tool")
    
    with st.form("create_tool_form"):
        tool_id = st.text_input("Tool ID")
        tool_name = st.text_input("Tool Name")
        description = st.text_area("Description")
        
        if st.form_submit_button("Create Tool"):
            st.info("Tool creation feature - placeholder for future implementation")

# Workflows
elif page == "Workflows":
    st.title("⚙️ Workflows")
    
    st.markdown("### Run Workflow")
    
    with st.form("workflow_form"):
        symptoms_text = st.text_area("Symptoms", height=100)
        
        if st.form_submit_button("🚀 Run Workflow", use_container_width=True):
            if symptoms_text:
                with st.spinner("Running workflow..."):
                    try:
                        result = run_async(st.session_state.workflow.run(symptoms_text))
                        
                        st.markdown("### Workflow Results")
                        st.json(result)
                        
                        # JSON Trace
                        st.markdown("### JSON Trace")
                        trace = result.get("trace", [])
                        st.json(trace)
                        
                        # Aggregated Confidence
                        st.markdown("### Aggregated Confidence")
                        workflow_confidence = result.get("workflow_confidence", {})
                        st.json(workflow_confidence)
                        
                        # Visualization
                        if trace:
                            st.markdown("### Workflow Visualization")
                            visualization_data = []
                            for event in trace:
                                if isinstance(event, dict) and event.get("visualization_metadata"):
                                    visualization_data.append(event["visualization_metadata"])
                            
                            if visualization_data:
                                st.json(visualization_data)
                                
                                # Simple visualization
                                steps = [v.get("step", 0) for v in visualization_data]
                                step_names = [v.get("step_name", "Unknown") for v in visualization_data]
                                
                                if steps:
                                    st.markdown("#### Workflow Steps")
                                    for i, (step, name) in enumerate(zip(steps, step_names)):
                                        st.markdown(f"{step}. {name}")
                        
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
                        st.exception(e)

# Audit Logs
elif page == "Audit Logs":
    st.title("📝 Audit Logs")
    
    st.markdown("### Workflow & Audit Logs")
    
    audit_logs = st.session_state.audit_logs
    
    if audit_logs:
        for i, log_entry in enumerate(reversed(audit_logs[-20:])):  # Show last 20
            with st.expander(f"**{log_entry.get('timestamp', 'Unknown')}** - {log_entry.get('action', 'Unknown')}"):
                st.json(log_entry)
    
    # Workflow audit log
    if st.session_state.workflow:
        workflow_audit = st.session_state.workflow.audit_log
        if workflow_audit:
            st.markdown("### Workflow Audit Log")
            for entry in reversed(workflow_audit[-20:]):  # Show last 20
                with st.expander(f"**{entry.get('timestamp', 'Unknown')}** - {entry.get('step', 'Unknown')}"):
                    st.json(entry)
    
    # Governance blocks
    if st.session_state.workflow:
        governance = st.session_state.workflow.governance_engine
        if governance:
            governance_logs = governance.get_audit_log()
            if governance_logs:
                st.markdown("### Governance Logs")
                for entry in reversed(governance_logs[-20:]):  # Show last 20
                    with st.expander(f"**{entry.get('timestamp', 'Unknown')}** - {entry.get('event', 'Unknown')}"):
                        st.json(entry)
    
    if not audit_logs and (not st.session_state.workflow or not st.session_state.workflow.audit_log):
        st.info("No audit logs available yet. Run a workflow to generate logs.")

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("**MedAgentX v1.6**")
st.sidebar.markdown("Clinical Decision Support")
st.sidebar.markdown("⚠️ All outputs require human approval")
st.sidebar.markdown("🤖 LLMs assist reasoning only")

