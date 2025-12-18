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

from medagentx.main import MedAgentXPlatform
from medagentx.core.types import AgentConfig

logger = logging.getLogger(__name__)

# Initialize platform (singleton)
platform = MedAgentXPlatform()

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
    return {
        "agents": [
            {
                "agent_id": agent.config.agent_id,
                "agent_name": agent.config.agent_name,
                "description": agent.config.description,
            }
            for agent in platform.agents.values()
        ]
    }


@app.post("/api/agents")
async def create_agent(request: AgentCreateRequest):
    """Create a new agent."""
    try:
        from medagentx.agents import (
            SymptomAnalyzerAgent,
            DiagnosisSupportAgent,
            MedicalCoderAgent,
            PrescriptionReviewAgent,
            ClinicalGuidelineAgent,
            RiskAssessmentAgent,
        )
        
        agent_map = {
            "symptom_analyzer": SymptomAnalyzerAgent,
            "diagnosis_support": DiagnosisSupportAgent,
            "medical_coder": MedicalCoderAgent,
            "prescription_reviewer": PrescriptionReviewAgent,
            "clinical_guideline": ClinicalGuidelineAgent,
            "risk_assessor": RiskAssessmentAgent,
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
            tool_registry=platform.tool_registry,
            governance_engine=platform.governance_engine,
            knowledge_base=platform.knowledge_base,
        )
        
        platform.register_agent(agent)
        
        return {"status": "created", "agent_id": request.agent_id}
    
    except Exception as e:
        logger.error(f"Error creating agent: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/agents/{agent_id}/execute")
async def execute_agent_task(agent_id: str, request: TaskRequest):
    """Execute a task with an agent."""
    agent = platform.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    
    try:
        state = await agent.execute(
            task=request.task,
            context=request.context,
            user_id="api_user",
        )
        
        return {
            "agent_id": agent_id,
            "status": state.status.value,
            "recommendations": [
                {
                    "type": rec.recommendation_type.value,
                    "content": rec.content,
                    "confidence": rec.confidence.value,
                    "confidence_score": rec.confidence_score,
                    "requires_approval": rec.requires_human_approval,
                }
                for rec in state.recommendations
            ],
        }
    
    except Exception as e:
        logger.error(f"Error executing agent task: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analyze-symptoms")
async def analyze_symptoms(request: SymptomAnalysisRequest):
    """Analyze symptoms using SymptomAnalyzerAgent."""
    # Find or create symptom analyzer agent
    agent_id = "symptom_analyzer_default"
    agent = platform.get_agent(agent_id)
    
    if not agent:
        from medagentx.agents import SymptomAnalyzerAgent
        config = AgentConfig(
            agent_id=agent_id,
            agent_name="Symptom Analyzer",
            description="Analyzes patient symptoms",
            created_by="api_user",
        )
        agent = SymptomAnalyzerAgent(
            config=config,
            tool_registry=platform.tool_registry,
            governance_engine=platform.governance_engine,
            knowledge_base=platform.knowledge_base,
        )
        platform.register_agent(agent)
    
    try:
        result = await agent.analyze_symptoms(
            symptoms=request.symptoms,
            patient_context=request.patient_context,
        )
        
        return {
            "status": "success",
            "recommendations": [
                {
                    "type": rec.recommendation_type.value,
                    "content": rec.content,
                    "confidence": rec.confidence.value,
                    "confidence_score": rec.confidence_score,
                    "supporting_evidence": rec.supporting_evidence,
                    "risks_and_warnings": rec.risks_and_warnings,
                    "requires_approval": rec.requires_human_approval,
                }
                for rec in result["state"].recommendations
            ],
        }
    
    except Exception as e:
        logger.error(f"Error analyzing symptoms: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tools")
async def list_tools():
    """List all registered tools."""
    tools = platform.tool_registry.list_tools()
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

