"""
BlueVektor Agents - Base Agent Class
Abstract base class for all BlueVektor agents.
"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, TypedDict

import structlog
from pydantic import BaseModel, Field

from core.llm import LLMRouter, ModelTier, get_llm_router
from core.memory import MemoryManager, get_memory_manager
from core.orchestrator import (
    AgentDefinition,
    AgentStatus,
    BaseState,
    HandoffRequest,
    HumanApprovalRequest,
    agent_registry,
)

logger = structlog.get_logger()


# =============================================================================
# Agent Configuration
# =============================================================================

class AgentConfig(BaseModel):
    """Configuration for an agent."""
    
    id: str = Field(..., description="Unique agent identifier (e.g., 'a1')")
    name: str = Field(..., description="Human-readable name")
    role: str = Field(..., description="Agent's role description")
    goal: str = Field(..., description="Primary goal of the agent")
    backstory: str = Field(..., description="Context and personality")
    
    # LLM settings
    model_tier: ModelTier = ModelTier.STANDARD
    temperature: float = 0.7
    max_tokens: int = 4096
    
    # Permissions
    tools: list[str] = Field(default_factory=list)
    allowed_handoffs: list[str] = Field(default_factory=list)
    artifacts_requiring_approval: list[str] = Field(default_factory=list)


# =============================================================================
# Agent State
# =============================================================================

class AgentState(BaseState, total=False):
    """Extended state for agent operations."""
    
    # Agent-specific context
    input_data: dict[str, Any]
    output_data: dict[str, Any]
    
    # Working memory (within session)
    working_memory: dict[str, Any]
    
    # Task tracking
    current_task: str
    completed_tasks: list[str]
    pending_tasks: list[str]


# =============================================================================
# Base Agent
# =============================================================================

class BaseAgent(ABC):
    """
    Abstract base class for all BlueVektor agents.
    
    Each agent should:
    1. Define its configuration (id, name, role, goal, backstory)
    2. Implement system_prompt() for LLM instructions
    3. Implement run() for main execution logic
    4. Register with agent_registry on instantiation
    """
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.llm = get_llm_router()
        self.memory = get_memory_manager()
        self.logger = logger.bind(agent_id=config.id)
        
        # Register with global registry
        self._register()
    
    def _register(self) -> None:
        """Register this agent with the global registry."""
        definition = AgentDefinition(
            id=self.config.id,
            name=self.config.name,
            description=self.config.goal,
            node_fn=self.run,
            allowed_handoffs=self.config.allowed_handoffs,
            requires_human_approval=self.config.artifacts_requiring_approval,
        )
        agent_registry.register(definition)
    
    # -------------------------------------------------------------------------
    # Abstract Methods (must implement)
    # -------------------------------------------------------------------------
    
    @abstractmethod
    def system_prompt(self) -> str:
        """
        Return the system prompt for this agent.
        Should include: role, goal, rules, constraints, output format.
        """
        pass
    
    @abstractmethod
    async def run(self, state: AgentState) -> AgentState:
        """
        Main execution logic for the agent.
        
        Args:
            state: Current state of the workflow
            
        Returns:
            Updated state after execution
        """
        pass
    
    # -------------------------------------------------------------------------
    # LLM Interaction
    # -------------------------------------------------------------------------
    
    async def think(
        self,
        prompt: str,
        context: dict[str, Any] | None = None,
        tier: ModelTier | None = None,
    ) -> str:
        """
        Generate a response using the agent's configured LLM.
        
        Args:
            prompt: User prompt / task description
            context: Additional context to include
            tier: Override model tier if needed
            
        Returns:
            Generated response text
        """
        messages = []
        
        # Add context if provided
        if context:
            context_str = "\n".join(f"{k}: {v}" for k, v in context.items())
            messages.append({
                "role": "user",
                "content": f"Context:\n{context_str}"
            })
        
        messages.append({"role": "user", "content": prompt})
        
        response = await self.llm.generate(
            messages=messages,
            tier=tier or self.config.model_tier,
            system=self.system_prompt(),
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )
        
        self.logger.info("Generated response", prompt_length=len(prompt))
        return response
    
    async def think_structured(
        self,
        prompt: str,
        output_schema: type[BaseModel],
        context: dict[str, Any] | None = None,
    ) -> BaseModel:
        """
        Generate a structured response conforming to a schema.
        
        Args:
            prompt: Task description
            output_schema: Pydantic model for output
            context: Additional context
            
        Returns:
            Parsed Pydantic model instance
        """
        messages = [{"role": "user", "content": prompt}]
        
        return await self.llm.generate_structured(
            messages=messages,
            output_schema=output_schema,
            tier=self.config.model_tier,
            system=self.system_prompt(),
        )
    
    # -------------------------------------------------------------------------
    # State Management
    # -------------------------------------------------------------------------
    
    def update_status(self, state: AgentState, status: AgentStatus) -> AgentState:
        """Update agent status in state."""
        state["status"] = status
        state["updated_at"] = datetime.utcnow().isoformat()
        return state
    
    def add_artifact(
        self,
        state: AgentState,
        artifact_type: str,
        name: str,
        content: Any,
        metadata: dict | None = None,
    ) -> AgentState:
        """Add an artifact to state."""
        if "artifacts" not in state:
            state["artifacts"] = []
        
        artifact = {
            "type": artifact_type,
            "name": name,
            "content": content,
            "metadata": metadata or {},
            "created_at": datetime.utcnow().isoformat(),
            "agent_id": self.config.id,
        }
        
        state["artifacts"].append(artifact)
        
        # Check if approval needed
        if artifact_type in self.config.artifacts_requiring_approval:
            state["human_approval_needed"] = True
            state["human_approval_request"] = {
                "artifact_type": artifact_type,
                "artifact_id": name,
                "description": f"Review {artifact_type}: {name}",
                "options": ["approve", "reject", "revise"],
            }
        
        self.logger.info("Artifact added", artifact_type=artifact_type, name=name)
        return state
    
    def add_decision(
        self,
        state: AgentState,
        decision_type: str,
        description: str,
        rationale: str | None = None,
    ) -> AgentState:
        """Log a decision in state."""
        if "decisions" not in state:
            state["decisions"] = []
        
        decision = {
            "type": decision_type,
            "description": description,
            "rationale": rationale,
            "timestamp": datetime.utcnow().isoformat(),
            "agent_id": self.config.id,
        }
        
        state["decisions"].append(decision)
        self.logger.info("Decision logged", decision_type=decision_type)
        return state
    
    # -------------------------------------------------------------------------
    # Handoffs
    # -------------------------------------------------------------------------
    
    def request_handoff(
        self,
        state: AgentState,
        target_agent: str,
        context: dict[str, Any],
        priority: str = "normal",
    ) -> AgentState:
        """
        Request handoff to another agent.
        
        Args:
            state: Current state
            target_agent: ID of target agent (e.g., "a6")
            context: Context to pass to target agent
            priority: low, normal, high, urgent
            
        Returns:
            Updated state with handoff request
        """
        if target_agent not in self.config.allowed_handoffs:
            self.logger.warning(
                "Handoff not allowed",
                from_agent=self.config.id,
                to_agent=target_agent
            )
            return state
        
        if "handoff_requests" not in state:
            state["handoff_requests"] = []
        
        request: HandoffRequest = {
            "target_agent": target_agent,
            "context": context,
            "priority": priority,
        }
        
        state["handoff_requests"].append(request)
        self.logger.info(
            "Handoff requested",
            target_agent=target_agent,
            priority=priority
        )
        return state
    
    # -------------------------------------------------------------------------
    # Memory Operations
    # -------------------------------------------------------------------------
    
    async def remember(self, key: str, value: Any, ttl: int = 3600) -> None:
        """Store something in short-term memory (Redis)."""
        await self.memory.set_state(f"{self.config.id}:{key}", {"value": value}, ttl)
    
    async def recall(self, key: str) -> Any | None:
        """Retrieve from short-term memory."""
        data = await self.memory.get_state(f"{self.config.id}:{key}")
        return data.get("value") if data else None
    
    async def save_artifact_to_db(
        self,
        artifact_type: str,
        name: str,
        content: str,
        context_type: str | None = None,
        context_id: str | None = None,
        metadata: dict | None = None,
    ) -> None:
        """Persist artifact to long-term storage."""
        await self.memory.save_artifact(
            agent_id=self.config.id,
            artifact_type=artifact_type,
            name=name,
            content=content,
            context_type=context_type,
            context_id=context_id,
            metadata=metadata,
        )
    
    # -------------------------------------------------------------------------
    # Utilities
    # -------------------------------------------------------------------------
    
    def build_base_prompt(self) -> str:
        """Build the base system prompt from config."""
        return f"""# Role
{self.config.role} - {self.config.name}

# Goal
{self.config.goal}

# Context
{self.config.backstory}

# Global Rules (BlueVektor)
1. Evidence first: recommendations must link to data or artifacts
2. HITL: strategic decisions and client deliverables require human approval
3. Traceability: log all decisions with rationale
4. Privacy: never expose client data outside agreed environment
5. Quality: every output has Definition of Done criteria

# Output Format
- Use JSON for structured data
- Use Markdown for narrative content
- Always include confidence level (high/medium/low) for recommendations
"""
