"""
FastAPI server for MedAgentX platform.

Provides REST API endpoints for:
- Agent management
- Task execution
- Recommendation approval
- Tool management
- Workflow orchestration
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import logging
from pathlib import Path

from medagentx.core.types import AgentConfig
from medagentx.core.workflow import RecommendationWorkflow
from medagentx.governance.engine import GovernanceEngine
from medagentx.knowledge.knowledge_base import KnowledgeBase
from medagentx.knowledge.medical_coding import MedicalCodingKB
from medagentx.tools.tool_registry import ToolRegistry
from medagentx.tools.examples import ICD10CodingTool
from medagentx.agents import (
    SymptomAnalyzerAgent,
    DiagnosisSupportAgent,
    MedicalCoderAgent,
    RiskScorerAgent,
)

logger = logging.getLogger(__name__)

# Global state for API (initialized lazily)
_platform_state = {
    "governance": None,
    "knowledge": None,
    "coding_kb": None,
    "tool_registry": None,
    "agents": {},
    "workflow": None,
}


def get_platform():
    """Initialize and return platform components."""
    if _platform_state["governance"] is None:
        _platform_state["governance"] = GovernanceEngine()
        _platform_state["knowledge"] = KnowledgeBase()
        _platform_state["coding_kb"] = MedicalCodingKB()
        _platform_state["tool_registry"] = ToolRegistry()
        _platform_state["tool_registry"].register_tool(ICD10CodingTool(_platform_state["coding_kb"]))
        
        # Create default agents
        _platform_state["agents"] = {
            "symptom_analyzer": SymptomAnalyzerAgent(
                AgentConfig(
                    agent_id="symptom_analyzer",
                    agent_name="Symptom Analyzer",
                    description="Symptom structuring only; no diagnosis.",
                    created_by="api",
                ),
                _platform_state["tool_registry"],
                _platform_state["governance"],
                _platform_state["knowledge"],
            ),
            "diagnosis_support": DiagnosisSupportAgent(
                AgentConfig(
                    agent_id="diagnosis_support",
                    agent_name="Diagnosis Support",
                    description="Supportive reasoning only; no definitive diagnosis.",
                    created_by="api",
                ),
                _platform_state["tool_registry"],
                _platform_state["governance"],
                _platform_state["knowledge"],
            ),
            "medical_coder": MedicalCoderAgent(
                AgentConfig(
                    agent_id="medical_coder",
                    agent_name="Medical Coder",
                    description="Maps supportive findings to ICD-10/CPT suggestions.",
                    created_by="api",
                ),
                _platform_state["tool_registry"],
                _platform_state["governance"],
                _platform_state["knowledge"],
            ),
            "risk_scorer": RiskScorerAgent(
                AgentConfig(
                    agent_id="risk_scorer",
                    agent_name="Risk Scorer",
                    description="Numeric risk scoring support only; no diagnosis or treatment.",
                    created_by="api",
                ),
                _platform_state["tool_registry"],
                _platform_state["governance"],
                _platform_state["knowledge"],
            ),
        }
        
        # Create workflow
        _platform_state["workflow"] = RecommendationWorkflow(
            workflow_id="api_workflow",
            agents=_platform_state["agents"],
            governance_engine=_platform_state["governance"],
        )
    
    return _platform_state

app = FastAPI(
    title="MedAgentX API",
    description="E-Doctor OS: Programmable Agentic AI Platform for Clinical Decision Support",
    version="0.1.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class TaskRequest(BaseModel):
    agent_id: str
    task: str
    context: Optional[Dict[str, Any]] = None


class SymptomAnalysisRequest(BaseModel):
    symptoms: str
    patient_context: Optional[Dict[str, Any]] = None


class ApprovalRequest(BaseModel):
    workflow_id: str
    reviewer_id: str
    approved_recommendations: Optional[List[str]] = None


class AgentCreateRequest(BaseModel):
    agent_id: str
    agent_name: str
    description: str
    agent_type: str = "symptom_analyzer"  # symptom_analyzer, diagnosis_support, etc.
    model_provider: str = "openai"
    model_name: str = "gpt-4"


# Serve static files
static_dir = Path(__file__).parent.parent.parent / "ui"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main UI."""
    ui_file = Path(__file__).parent.parent.parent / "ui" / "index.html"
    if ui_file.exists():
        return FileResponse(ui_file)
    return HTMLResponse("""
    <html>
        <head><title>MedAgentX</title></head>
        <body>
            <h1>🧠 MedAgentX (E-Doctor OS)</h1>
            <p>API is running. Visit <a href="/docs">/docs</a> for API documentation.</p>
            <p>UI will be available when the frontend is built.</p>
        </body>
    </html>
    """)


@app.get("/api/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "platform": "MedAgentX"}


@app.get("/api/agents")
async def list_agents():
    """List all registered agents."""
    platform = get_platform()
    return {
        "agents": [
            {
                "agent_id": agent.config.agent_id,
                "agent_name": agent.config.agent_name,
                "description": agent.config.description,
            }
            for agent in platform["agents"].values()
        ]
    }


@app.post("/api/agents")
async def create_agent(request: AgentCreateRequest):
    """Create a new agent."""
    try:
        platform = get_platform()
        
        agent_map = {
            "symptom_analyzer": SymptomAnalyzerAgent,
            "diagnosis_support": DiagnosisSupportAgent,
            "medical_coder": MedicalCoderAgent,
            "risk_scorer": RiskScorerAgent,
        }
        
        agent_class = agent_map.get(request.agent_type)
        if not agent_class:
            raise HTTPException(status_code=400, detail=f"Unknown agent type: {request.agent_type}")
        
        config = AgentConfig(
            agent_id=request.agent_id,
            agent_name=request.agent_name,
            description=request.description,
            model_provider=request.model_provider,
            model_name=request.model_name,
            created_by="api_user",
        )
        
        agent = agent_class(
            config=config,
            tool_registry=platform["tool_registry"],
            governance_engine=platform["governance"],
            knowledge_base=platform["knowledge"],
        )
        
        platform["agents"][request.agent_id] = agent
        
        return {"status": "created", "agent_id": request.agent_id}
    
    except Exception as e:
        logger.error(f"Error creating agent: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/agents/{agent_id}/execute")
async def execute_agent_task(agent_id: str, request: TaskRequest):
    """Execute a task with an agent."""
    platform = get_platform()
    agent = platform["agents"].get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    
    try:
        result = await agent.run(request.task, context=request.context)
        
        return {
            "agent_id": agent_id,
            "status": "completed",
            "output": result.get("output"),
            "confidence": result.get("confidence"),
            "reasoning": result.get("reasoning"),
            "requires_human_approval": result.get("requires_human_approval", True),
        }
    
    except Exception as e:
        logger.error(f"Error executing agent task: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analyze-symptoms")
async def analyze_symptoms(request: SymptomAnalysisRequest):
    """Analyze symptoms using SymptomAnalyzerAgent."""
    platform = get_platform()
    agent = platform["agents"].get("symptom_analyzer")
    
    if not agent:
        raise HTTPException(status_code=500, detail="Symptom analyzer agent not available")
    
    try:
        result = await agent.run(request.symptoms, context={"patient_context": request.patient_context})
        
        return {
            "status": "success",
            "output": result.get("output"),
            "confidence": result.get("confidence"),
            "reasoning": result.get("reasoning"),
            "requires_human_approval": result.get("requires_human_approval", True),
        }
    
    except Exception as e:
        logger.error(f"Error analyzing symptoms: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tools")
async def list_tools():
    """List all registered tools."""
    platform = get_platform()
    tools = platform["tool_registry"].list_tools()
    return {
        "tools": [
            {
                "tool_id": tool.tool_id,
                "name": tool.schema.name,
                "description": tool.schema.description,
            }
            for tool in tools
        ]
    }


@app.post("/api/recommend")
async def recommend(request: SymptomAnalysisRequest):
    """Run full recommendation workflow."""
    try:
        platform = get_platform()
        workflow = platform["workflow"]
        
        # Run workflow
        result = await workflow.run(request.symptoms)
        
        return {
            "status": "success",
            "result": result,
            "requires_human_approval": result.get("requires_human_approval", True),
        }
    
    except Exception as e:
        logger.error(f"Error in recommendation workflow: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/workflows")
async def list_workflows():
    """List available workflows."""
    return {
        "workflows": [
            {
                "workflow_id": "recommendation_workflow",
                "name": "Recommendation Workflow",
                "description": "Full symptom analysis, diagnosis support, coding, and risk assessment",
            }
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

