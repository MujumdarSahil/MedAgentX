"""
Main entry point for MedAgentX platform.

Initializes and runs the platform.
"""

import asyncio
import logging
from typing import Optional

from medagentx.core.types import AgentConfig
from medagentx.core.agent import BaseAgent
from medagentx.tools.tool_registry import ToolRegistry
from medagentx.governance.engine import GovernanceEngine
from medagentx.knowledge.knowledge_base import KnowledgeBase

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MedAgentXPlatform:
    """
    Main platform class for MedAgentX.
    
    Orchestrates all platform components:
    - Agent management
    - Tool registry
    - Governance engine
    - Knowledge base
    """
    
    def __init__(self):
        """Initialize the MedAgentX platform."""
        logger.info("Initializing MedAgentX Platform...")
        
        # Initialize core components
        self.tool_registry = ToolRegistry()
        self.governance_engine = GovernanceEngine()
        self.knowledge_base = KnowledgeBase()
        
        # Agent registry
        self.agents: dict[str, BaseAgent] = {}
        
        logger.info("MedAgentX Platform initialized")
    
    def register_agent(self, agent: BaseAgent) -> None:
        """
        Register an agent with the platform.
        
        Args:
            agent: Agent instance to register
        """
        self.agents[agent.config.agent_id] = agent
        logger.info(f"Registered agent: {agent.config.agent_id}")
    
    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """
        Get an agent by ID.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            Agent instance or None
        """
        return self.agents.get(agent_id)
    
    async def shutdown(self) -> None:
        """Shutdown the platform."""
        logger.info("Shutting down MedAgentX Platform...")
        # Cleanup logic here


async def main():
    """Main entry point."""
    logger.info("=" * 60)
    logger.info("🧠 MedAgentX (E-Doctor OS) Platform")
    logger.info("=" * 60)
    
    # Initialize platform
    platform = MedAgentXPlatform()
    
    # Platform is now ready for use
    logger.info("Platform ready. Use the API or CLI to interact with agents.")
    
    # Keep running (in production, this would start a server)
    try:
        await asyncio.Event().wait()  # Wait indefinitely
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        await platform.shutdown()


if __name__ == "__main__":
    asyncio.run(main())

