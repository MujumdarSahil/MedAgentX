"""
Extended MCP Registry for MedAgentX v1.7

Supports registration and discovery of:
- Agents
- Tools
- RecommendationEngines
- PredictionModels
- Squads

Each entity must declare metadata:
- purpose
- scope
- allowed_outputs
- governance_constraints
"""

from typing import Any, Dict, List, Optional, Set
from datetime import datetime
import logging
from abc import ABC

from medagentx.core.agent import BaseAgent
from medagentx.tools.base_tool import BaseTool
from medagentx.core.recommendation_engine import RecommendationEngine
from medagentx.core.prediction_model import PredictionModel

logger = logging.getLogger(__name__)


class MCPEntityMetadata:
    """Metadata for MCP-registered entities."""
    
    def __init__(
        self,
        entity_id: str,
        entity_type: str,  # "agent", "tool", "engine", "model", "squad"
        name: str,
        description: str,
        purpose: str,
        scope: str,
        allowed_outputs: List[str],
        governance_constraints: Dict[str, Any],
        created_by: str,
        created_at: Optional[str] = None,
    ):
        self.entity_id = entity_id
        self.entity_type = entity_type
        self.name = name
        self.description = description
        self.purpose = purpose
        self.scope = scope
        self.allowed_outputs = allowed_outputs
        self.governance_constraints = governance_constraints
        self.created_by = created_by
        self.created_at = created_at or datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "name": self.name,
            "description": self.description,
            "purpose": self.purpose,
            "scope": self.scope,
            "allowed_outputs": self.allowed_outputs,
            "governance_constraints": self.governance_constraints,
            "created_by": self.created_by,
            "created_at": self.created_at,
        }
    
    def validate(self) -> List[str]:
        """
        Validate metadata for safety.
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Check forbidden outputs
        forbidden = ["diagnosis", "treatment", "prescription"]
        allowed_str = " ".join(self.allowed_outputs).lower()
        if any(f in allowed_str for f in forbidden):
            errors.append(f"Entity {self.entity_id} has forbidden output type in allowed_outputs")
        
        # Check required fields
        if not self.entity_id:
            errors.append("entity_id is required")
        if not self.entity_type:
            errors.append("entity_type is required")
        if self.entity_type not in ["agent", "tool", "engine", "model", "squad"]:
            errors.append(f"Invalid entity_type: {self.entity_type}")
        
        return errors


class MCPRegistry:
    """
    Extended MCP registry for Agents, Tools, Engines, Models, and Squads.
    """
    
    def __init__(self):
        """Initialize MCP registry."""
        self._agents: Dict[str, BaseAgent] = {}
        self._tools: Dict[str, BaseTool] = {}
        self._engines: Dict[str, RecommendationEngine] = {}
        self._models: Dict[str, PredictionModel] = {}
        self._squads: Dict[str, Dict[str, Any]] = {}  # Squad definitions
        
        self._metadata: Dict[str, MCPEntityMetadata] = {}  # entity_id -> metadata
        self._usage_log: List[Dict[str, Any]] = []
    
    def register_agent(
        self,
        agent: BaseAgent,
        metadata: MCPEntityMetadata,
    ) -> None:
        """
        Register an agent.
        
        Args:
            agent: Agent instance
            metadata: Entity metadata
        """
        if metadata.entity_type != "agent":
            raise ValueError(f"Metadata entity_type must be 'agent', got: {metadata.entity_type}")
        
        errors = metadata.validate()
        if errors:
            raise ValueError(f"Metadata validation failed: {errors}")
        
        self._agents[metadata.entity_id] = agent
        self._metadata[metadata.entity_id] = metadata
        logger.info(f"Registered agent: {metadata.entity_id} ({metadata.name})")
    
    def register_tool(
        self,
        tool: BaseTool,
        metadata: MCPEntityMetadata,
    ) -> None:
        """
        Register a tool.
        
        Args:
            tool: Tool instance
            metadata: Entity metadata
        """
        if metadata.entity_type != "tool":
            raise ValueError(f"Metadata entity_type must be 'tool', got: {metadata.entity_type}")
        
        errors = metadata.validate()
        if errors:
            raise ValueError(f"Metadata validation failed: {errors}")
        
        self._tools[metadata.entity_id] = tool
        self._metadata[metadata.entity_id] = metadata
        logger.info(f"Registered tool: {metadata.entity_id} ({metadata.name})")
    
    def register_engine(
        self,
        engine: RecommendationEngine,
        metadata: MCPEntityMetadata,
    ) -> None:
        """
        Register a recommendation engine.
        
        Args:
            engine: RecommendationEngine instance
            metadata: Entity metadata
        """
        if metadata.entity_type != "engine":
            raise ValueError(f"Metadata entity_type must be 'engine', got: {metadata.entity_type}")
        
        errors = metadata.validate()
        if errors:
            raise ValueError(f"Metadata validation failed: {errors}")
        
        self._engines[metadata.entity_id] = engine
        self._metadata[metadata.entity_id] = metadata
        logger.info(f"Registered engine: {metadata.entity_id} ({metadata.name})")
    
    def register_model(
        self,
        model: PredictionModel,
        metadata: MCPEntityMetadata,
    ) -> None:
        """
        Register a prediction model.
        
        Args:
            model: PredictionModel instance
            metadata: Entity metadata
        """
        if metadata.entity_type != "model":
            raise ValueError(f"Metadata entity_type must be 'model', got: {metadata.entity_type}")
        
        errors = metadata.validate()
        if errors:
            raise ValueError(f"Metadata validation failed: {errors}")
        
        self._models[metadata.entity_id] = model
        self._metadata[metadata.entity_id] = metadata
        logger.info(f"Registered model: {metadata.entity_id} ({metadata.name})")
    
    def register_squad(
        self,
        squad_id: str,
        squad_definition: Dict[str, Any],
        metadata: MCPEntityMetadata,
    ) -> None:
        """
        Register a squad (multi-agent workflow).
        
        Args:
            squad_id: Squad identifier
            squad_definition: Squad execution graph definition
            metadata: Entity metadata
        """
        if metadata.entity_type != "squad":
            raise ValueError(f"Metadata entity_type must be 'squad', got: {metadata.entity_type}")
        
        errors = metadata.validate()
        if errors:
            raise ValueError(f"Metadata validation failed: {errors}")
        
        # Validate squad definition
        self._validate_squad_definition(squad_definition)
        
        self._squads[squad_id] = squad_definition
        self._metadata[squad_id] = metadata
        logger.info(f"Registered squad: {squad_id} ({metadata.name})")
    
    def _validate_squad_definition(self, squad_definition: Dict[str, Any]) -> None:
        """
        Validate squad definition for safety.
        
        Args:
            squad_definition: Squad definition to validate
            
        Raises:
            ValueError: If squad definition is invalid
        """
        # Must have execution graph
        if "execution_graph" not in squad_definition:
            raise ValueError("Squad definition must include 'execution_graph'")
        
        graph = squad_definition["execution_graph"]
        
        # Must be a list of steps (no loops)
        if not isinstance(graph, list):
            raise ValueError("Execution graph must be a list")
        
        # Check for loops (simple check - no step can reference a previous step)
        step_ids = [step.get("step_id") for step in graph if isinstance(step, dict)]
        for i, step in enumerate(graph):
            if isinstance(step, dict):
                dependencies = step.get("dependencies", [])
                for dep in dependencies:
                    if dep in step_ids[:i]:
                        raise ValueError(f"Squad execution graph contains loop: step {step.get('step_id')} depends on {dep}")
    
    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """Get agent by ID."""
        return self._agents.get(agent_id)
    
    def get_tool(self, tool_id: str) -> Optional[BaseTool]:
        """Get tool by ID."""
        return self._tools.get(tool_id)
    
    def get_engine(self, engine_id: str) -> Optional[RecommendationEngine]:
        """Get engine by ID."""
        return self._engines.get(engine_id)
    
    def get_model(self, model_id: str) -> Optional[PredictionModel]:
        """Get model by ID."""
        return self._models.get(model_id)
    
    def get_squad(self, squad_id: str) -> Optional[Dict[str, Any]]:
        """Get squad by ID."""
        return self._squads.get(squad_id)
    
    def list_agents(self) -> List[BaseAgent]:
        """List all registered agents."""
        return list(self._agents.values())
    
    def list_tools(self) -> List[BaseTool]:
        """List all registered tools."""
        return list(self._tools.values())
    
    def list_engines(self) -> List[RecommendationEngine]:
        """List all registered engines."""
        return list(self._engines.values())
    
    def list_models(self) -> List[PredictionModel]:
        """List all registered models."""
        return list(self._models.values())
    
    def list_squads(self) -> List[str]:
        """List all registered squad IDs."""
        return list(self._squads.keys())
    
    def get_metadata(self, entity_id: str) -> Optional[MCPEntityMetadata]:
        """Get metadata for entity."""
        return self._metadata.get(entity_id)
    
    def list_metadata(self, entity_type: Optional[str] = None) -> List[MCPEntityMetadata]:
        """
        List metadata for all entities, optionally filtered by type.
        
        Args:
            entity_type: Optional filter by entity type
            
        Returns:
            List of metadata objects
        """
        if entity_type:
            return [meta for meta in self._metadata.values() if meta.entity_type == entity_type]
        return list(self._metadata.values())
    
    def unregister(self, entity_id: str) -> None:
        """
        Unregister an entity.
        
        Args:
            entity_id: Entity ID to unregister
        """
        metadata = self._metadata.get(entity_id)
        if not metadata:
            logger.warning(f"Entity {entity_id} not found, cannot unregister")
            return
        
        entity_type = metadata.entity_type
        if entity_type == "agent":
            self._agents.pop(entity_id, None)
        elif entity_type == "tool":
            self._tools.pop(entity_id, None)
        elif entity_type == "engine":
            self._engines.pop(entity_id, None)
        elif entity_type == "model":
            self._models.pop(entity_id, None)
        elif entity_type == "squad":
            self._squads.pop(entity_id, None)
        
        self._metadata.pop(entity_id, None)
        logger.info(f"Unregistered {entity_type}: {entity_id}")

