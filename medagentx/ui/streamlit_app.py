"""
Streamlit-based UI for MedAgentX v1.5

Features:
- Dashboard
- Symptom Analysis
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


# Page configuration
st.set_page_config(
    page_title="MedAgentX v1.5",
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
        
        # Create agents
        agents = {
            "symptom_analyzer": SymptomAnalyzerAgent(
                AgentConfig(
                    agent_id="symptom_analyzer",
                    agent_name="Symptom Analyzer",
                    description="Symptom structuring only; no diagnosis.",
                    created_by="system",
                ),
                tool_registry,
                governance,
                knowledge,
            ),
            "diagnosis_support": DiagnosisSupportAgent(
                AgentConfig(
                    agent_id="diagnosis_support",
                    agent_name="Diagnosis Support",
                    description="Supportive reasoning only; no definitive diagnosis.",
                    created_by="system",
                ),
                tool_registry,
                governance,
                knowledge,
            ),
            "medical_coder": MedicalCoderAgent(
                AgentConfig(
                    agent_id="medical_coder",
                    agent_name="Medical Coder",
                    description="Maps supportive findings to ICD-10/CPT suggestions.",
                    created_by="system",
                ),
                tool_registry,
                governance,
                knowledge,
            ),
            "risk_scorer": RiskScorerAgent(
                AgentConfig(
                    agent_id="risk_scorer",
                    agent_name="Risk Scorer",
                    description="Numeric risk scoring support only; no diagnosis or treatment.",
                    created_by="system",
                ),
                tool_registry,
                governance,
                knowledge,
            ),
        }
        
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
st.sidebar.title("🏥 MedAgentX v1.5")
st.sidebar.markdown("**Clinical Decision Support Platform**")

page = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "Symptom Analysis", "Agents", "Tools", "Workflows", "Audit Logs"],
)

# Initialize system
initialize_system()

# Dashboard
if page == "Dashboard":
    st.title("📊 Dashboard")
    st.markdown("### Welcome to MedAgentX v1.5")
    
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
    
    if analyze_button and symptoms_text:
        with st.spinner("Analyzing symptoms..."):
            try:
                result = run_async(st.session_state.workflow.run(symptoms_text))
                
                # Store in audit logs
                st.session_state.audit_logs.append({
                    "timestamp": datetime.now().isoformat(),
                    "action": "symptom_analysis",
                    "input": symptoms_text,
                    "result": result,
                })
                
                # Display results
                st.markdown("---")
                st.markdown("### 📋 Analysis Results")
                
                # Structured Symptoms
                st.markdown("#### Structured Symptoms")
                structured_symptoms = result.get("structured_symptoms", [])
                st.json(structured_symptoms)
                
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
                st.error(f"Error during analysis: {str(e)}")
                st.exception(e)

# Agents
elif page == "Agents":
    st.title("🤖 Agents")
    
    st.markdown("### Available Agents")
    
    agents = st.session_state.agents
    for agent_id, agent in agents.items():
        with st.expander(f"**{agent_id.replace('_', ' ').title()}**"):
            config = agent.config
            st.markdown(f"**Name**: {config.agent_name}")
            st.markdown(f"**Description**: {config.description}")
            st.markdown(f"**ID**: {config.agent_id}")
            st.markdown(f"**Created By**: {config.created_by}")
            
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
    st.markdown("### Create New Agent")
    
    with st.form("create_agent_form"):
        agent_id = st.text_input("Agent ID")
        agent_name = st.text_input("Agent Name")
        description = st.text_area("Description")
        
        if st.form_submit_button("Create Agent"):
            st.info("Agent creation feature - placeholder for future implementation")

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
st.sidebar.markdown("**MedAgentX v1.5**")
st.sidebar.markdown("Clinical Decision Support")
st.sidebar.markdown("⚠️ All outputs require human approval")

