"""
Quick Start Example for MedAgentX Platform.

This example demonstrates how to:
1. Initialize the platform
2. Create and register agents
3. Create and register tools
4. Execute a workflow
"""

import asyncio
import logging
from datetime import datetime

from medagentx.main import MedAgentXPlatform
from medagentx.core.types import AgentConfig
from medagentx.agents import SymptomAnalyzerAgent
from medagentx.tools.tool_registry import ToolRegistry
from medagentx.tools.examples import SymptomKnowledgeRetriever
from medagentx.governance.engine import GovernanceEngine
from medagentx.knowledge.knowledge_base import KnowledgeBase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Quick start example."""
    logger.info("=" * 60)
    logger.info("MedAgentX Quick Start Example")
    logger.info("=" * 60)
    
    # 1. Initialize platform
    platform = MedAgentXPlatform()
    
    # 2. Create and register tools
    symptom_tool = SymptomKnowledgeRetriever()
    platform.tool_registry.register_tool(symptom_tool)
    logger.info("Registered tool: symptom_knowledge_retriever")
    
    # 3. Create agent configuration
    agent_config = AgentConfig(
        agent_id="example_symptom_analyzer",
        agent_name="Example Symptom Analyzer",
        description="Analyzes symptoms and generates diagnostic hypotheses",
        model_provider="openai",
        model_name="gpt-4",
        temperature=0.3,
        tools=[symptom_tool.tool_id],
        created_by="example_user",
    )
    
    # 4. Create and register agent
    agent = SymptomAnalyzerAgent(
        config=agent_config,
        tool_registry=platform.tool_registry,
        governance_engine=platform.governance_engine,
        knowledge_base=platform.knowledge_base,
    )
    platform.register_agent(agent)
    logger.info("Registered agent: example_symptom_analyzer")
    
    # 5. Execute a task
    logger.info("\nExecuting symptom analysis task...")
    result = await agent.analyze_symptoms(
        symptoms="fever, cough, and shortness of breath for 3 days",
        patient_context={
            "age": 45,
            "gender": "male",
            "previous_conditions": [],
        },
    )
    
    # 6. Display results
    logger.info("\n" + "=" * 60)
    logger.info("Results:")
    logger.info("=" * 60)
    logger.info(f"Agent Status: {result['state'].status}")
    logger.info(f"Recommendations Generated: {len(result['state'].recommendations)}")
    
    for i, rec in enumerate(result['state'].recommendations, 1):
        logger.info(f"\nRecommendation {i}:")
        logger.info(f"  Type: {rec.recommendation_type}")
        logger.info(f"  Confidence: {rec.confidence} ({rec.confidence_score:.2f})")
        logger.info(f"  Requires Approval: {rec.requires_human_approval}")
        logger.info(f"  Content: {rec.content[:100]}...")
    
    logger.info("\n" + "=" * 60)
    logger.info("⚠️  IMPORTANT: All recommendations require human approval")
    logger.info("=" * 60)
    
    # 7. Cleanup
    await platform.shutdown()


if __name__ == "__main__":
    asyncio.run(main())

