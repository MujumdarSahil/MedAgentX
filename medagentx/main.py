import asyncio
import logging
from pprint import pprint

from medagentx.agents.symptom_analyzer import SymptomAnalyzerAgent
from medagentx.agents.diagnosis_support import DiagnosisSupportAgent
from medagentx.agents.medical_coder import MedicalCoderAgent
from medagentx.core.types import AgentConfig
from medagentx.core.workflow import RecommendationWorkflow
from medagentx.governance.engine import GovernanceEngine
from medagentx.knowledge.knowledge_base import KnowledgeBase
from medagentx.tools.mcp_server import ICD10MCPServer
from medagentx.tools.tool_registry import ToolRegistry
from medagentx.utils.logging import evaluate_trace

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def agent_config(agent_id: str, name: str) -> AgentConfig:
    return AgentConfig(
        agent_id=agent_id,
        agent_name=name,
        description="",
        created_by="system",
    )


async def main() -> None:
    symptoms_text = "fever, cough for three days"

    governance = GovernanceEngine()
    knowledge = KnowledgeBase()
    tool_registry = ToolRegistry()

    mcp_server = ICD10MCPServer()
    await tool_registry.register_mcp_server(mcp_server)

    agents = {
        "symptom_analyzer": SymptomAnalyzerAgent(agent_config("symptom_analyzer", "Symptom Analyzer"), tool_registry, governance, knowledge),
        "diagnosis_support": DiagnosisSupportAgent(agent_config("diagnosis_support", "Diagnosis Support"), tool_registry, governance, knowledge),
        "medical_coder": MedicalCoderAgent(agent_config("medical_coder", "Medical Coder"), tool_registry, governance, knowledge),
    }

    workflow = RecommendationWorkflow(workflow_id="demo_workflow", agents=agents, governance_engine=governance)
    result = await workflow.run(symptoms_text)
    replay_result = await workflow.replay(result.get("trace", []))
    evaluation = evaluate_trace(result.get("trace", []))

    print("\n--- MedAgentX Clinical Decision Support (Recommendation-Only) ---")
    pprint(result)
    print("\n--- Trace ---")
    pprint(result.get("trace", []))
    print("\n--- Deterministic Replay ---")
    pprint(replay_result)
    print("\n--- Evaluation ---")
    pprint(evaluation)
    print("\nDisclaimer: This is supportive information only. Human clinician approval required.")


if __name__ == "__main__":
    asyncio.run(main())

