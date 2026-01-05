"""
BlueVektor Agents - Orchestrator
Main coordination layer using LangGraph for multi-agent workflows.
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Annotated, Any, Callable, TypedDict

import structlog
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages

from core.config import get_settings
from core.llm import LLMRouter, ModelTier, get_llm_router
from core.memory import MemoryManager, get_memory_manager

logger = structlog.get_logger()


# =============================================================================
# State Types
# =============================================================================

class AgentStatus(str, Enum):
    """Agent execution status."""
    IDLE = "idle"
    RUNNING = "running"
    WAITING_HUMAN = "waiting_human"
    COMPLETED = "completed"
    FAILED = "failed"


class HandoffRequest(TypedDict):
    """Request to hand off work to another agent."""
    target_agent: str
    context: dict[str, Any]
    priority: str  # low, normal, high, urgent


class HumanApprovalRequest(TypedDict):
    """Request for human-in-the-loop approval."""
    artifact_type: str
    artifact_id: str
    description: str
    options: list[str]


class BaseState(TypedDict, total=False):
    """Base state shared across all workflows."""
    # Conversation
    messages: Annotated[list[dict], add_messages]
    
    # Context
    agent_id: str
    workflow_id: str
    context_type: str  # opportunity, wp1, wp4, etc.
    context_id: str
    
    # Execution state
    status: AgentStatus
    current_step: str
    started_at: str
    updated_at: str
    
    # Artifacts and decisions
    artifacts: list[dict[str, Any]]
    decisions: list[dict[str, Any]]
    
    # Human-in-the-loop
    human_approval_needed: bool
    human_approval_request: HumanApprovalRequest | None
    human_response: str | None
    
    # Handoffs
    handoff_requests: list[HandoffRequest]
    
    # Error handling
    errors: list[str]
    retry_count: int


# =============================================================================
# Agent Registry
# =============================================================================

@dataclass
class AgentDefinition:
    """Definition of an agent for registration."""
    id: str
    name: str
    description: str
    node_fn: Callable
    allowed_handoffs: list[str] = field(default_factory=list)
    requires_human_approval: list[str] = field(default_factory=list)  # Artifact types


class AgentRegistry:
    """
    Central registry for all agents.
    Allows dynamic discovery and routing.
    """
    
    def __init__(self):
        self._agents: dict[str, AgentDefinition] = {}
    
    def register(self, agent: AgentDefinition) -> None:
        """Register an agent."""
        self._agents[agent.id] = agent
        logger.info(f"Registered agent: {agent.id} - {agent.name}")
    
    def get(self, agent_id: str) -> AgentDefinition | None:
        """Get agent by ID."""
        return self._agents.get(agent_id)
    
    def list_agents(self) -> list[AgentDefinition]:
        """List all registered agents."""
        return list(self._agents.values())
    
    def can_handoff(self, from_agent: str, to_agent: str) -> bool:
        """Check if handoff is allowed."""
        agent = self._agents.get(from_agent)
        return agent is not None and to_agent in agent.allowed_handoffs


# Global registry
agent_registry = AgentRegistry()


# =============================================================================
# Orchestrator
# =============================================================================

class Orchestrator:
    """
    Main orchestrator for BlueVektor agent workflows.
    Coordinates multi-agent execution with LangGraph.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.llm_router = get_llm_router()
        self.memory = get_memory_manager()
        self.checkpointer = MemorySaver()
        self._workflows: dict[str, StateGraph] = {}
    
    def create_workflow(
        self,
        workflow_id: str,
        state_schema: type[TypedDict],
    ) -> StateGraph:
        """
        Create a new workflow graph.
        
        Args:
            workflow_id: Unique identifier for the workflow
            state_schema: TypedDict defining the state shape
            
        Returns:
            StateGraph for building the workflow
        """
        graph = StateGraph(state_schema)
        self._workflows[workflow_id] = graph
        return graph
    
    def compile_workflow(self, workflow_id: str):
        """Compile a workflow for execution."""
        if workflow_id not in self._workflows:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        return self._workflows[workflow_id].compile(
            checkpointer=self.checkpointer
        )
    
    async def run_workflow(
        self,
        workflow_id: str,
        initial_state: dict[str, Any],
        thread_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Execute a compiled workflow.
        
        Args:
            workflow_id: ID of the workflow to run
            initial_state: Initial state dict
            thread_id: Optional thread ID for checkpointing
            
        Returns:
            Final state after execution
        """
        compiled = self.compile_workflow(workflow_id)
        
        config = {"configurable": {"thread_id": thread_id or workflow_id}}
        
        # Add timestamps
        initial_state["started_at"] = datetime.utcnow().isoformat()
        initial_state["status"] = AgentStatus.RUNNING
        
        logger.info(
            "Starting workflow",
            workflow_id=workflow_id,
            thread_id=thread_id
        )
        
        try:
            result = await compiled.ainvoke(initial_state, config)
            result["status"] = AgentStatus.COMPLETED
            result["updated_at"] = datetime.utcnow().isoformat()
            
            logger.info(
                "Workflow completed",
                workflow_id=workflow_id,
                status="completed"
            )
            
            return result
            
        except Exception as e:
            logger.error(
                "Workflow failed",
                workflow_id=workflow_id,
                error=str(e)
            )
            raise
    
    async def resume_workflow(
        self,
        workflow_id: str,
        thread_id: str,
        human_response: str | None = None,
    ) -> dict[str, Any]:
        """
        Resume a workflow that was waiting for human input.
        
        Args:
            workflow_id: ID of the workflow
            thread_id: Thread ID to resume
            human_response: Response from human (if applicable)
            
        Returns:
            Final state after execution
        """
        compiled = self.compile_workflow(workflow_id)
        config = {"configurable": {"thread_id": thread_id}}
        
        # Get current state
        state = compiled.get_state(config)
        
        if human_response:
            state.values["human_response"] = human_response
            state.values["human_approval_needed"] = False
        
        logger.info(
            "Resuming workflow",
            workflow_id=workflow_id,
            thread_id=thread_id
        )
        
        return await compiled.ainvoke(state.values, config)


# =============================================================================
# Helper Functions for Workflow Building
# =============================================================================

def should_continue(state: BaseState) -> str:
    """
    Conditional edge: determine if workflow should continue.
    
    Returns:
        - "human_approval" if human approval needed
        - "handoff" if handoff requested
        - "continue" to proceed
        - "end" to finish
    """
    if state.get("human_approval_needed"):
        return "human_approval"
    
    if state.get("handoff_requests"):
        return "handoff"
    
    if state.get("status") == AgentStatus.COMPLETED:
        return "end"
    
    return "continue"


def create_human_approval_node(webhook_url: str | None = None):
    """
    Create a node that pauses for human approval.
    
    Args:
        webhook_url: Optional webhook to notify human
        
    Returns:
        Node function for human approval
    """
    async def human_approval_node(state: BaseState) -> BaseState:
        request = state.get("human_approval_request")
        
        if request and webhook_url:
            import httpx
            async with httpx.AsyncClient() as client:
                await client.post(webhook_url, json={
                    "type": "approval_request",
                    "workflow_id": state.get("workflow_id"),
                    "request": request,
                })
        
        logger.info(
            "Waiting for human approval",
            artifact_type=request.get("artifact_type") if request else None
        )
        
        # Graph will pause here until resumed
        return state
    
    return human_approval_node


def create_handoff_node():
    """Create a node that handles handoffs to other agents."""
    async def handoff_node(state: BaseState) -> BaseState:
        requests = state.get("handoff_requests", [])
        
        for request in requests:
            target = request["target_agent"]
            context = request["context"]
            
            logger.info(
                "Processing handoff",
                target_agent=target,
                priority=request.get("priority", "normal")
            )
            
            # Here we would trigger the target agent's workflow
            # This is handled by the orchestrator
        
        state["handoff_requests"] = []
        return state
    
    return handoff_node


# =============================================================================
# Singleton
# =============================================================================

_orchestrator: Orchestrator | None = None


def get_orchestrator() -> Orchestrator:
    """Get the global orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = Orchestrator()
    return _orchestrator
