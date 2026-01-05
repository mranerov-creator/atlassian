"""
BlueVektor Agents - Architecture Design Workflow
Complete workflow for TO-BE architecture design.
"""
from typing import Any, Literal
import structlog
from langgraph.graph import END, StateGraph
from agents.a2_architect import A2State, create_a2_agent
from core.orchestrator import AgentStatus, get_orchestrator

logger = structlog.get_logger()


class ArchitectureWorkflowState(A2State, total=False):
    """State for architecture design workflow."""
    workflow_stage: str
    stages_completed: list[str]
    deliverables: dict[str, dict[str, Any]]
    architecture_approved: bool


async def initialize(state: ArchitectureWorkflowState) -> ArchitectureWorkflowState:
    state["stages_completed"] = []
    state["deliverables"] = {}
    state["workflow_stage"] = "initialized"
    state["status"] = AgentStatus.RUNNING
    return state


async def current_state_node(state: ArchitectureWorkflowState) -> ArchitectureWorkflowState:
    a2 = create_a2_agent()
    state["current_task"] = "assess_current_state"
    state = await a2.run(state)
    state["workflow_stage"] = "current_state_complete"
    state["stages_completed"] = state.get("stages_completed", []) + ["current_state"]
    return state


async def options_node(state: ArchitectureWorkflowState) -> ArchitectureWorkflowState:
    a2 = create_a2_agent()
    state["current_task"] = "evaluate_options"
    state = await a2.run(state)
    state["workflow_stage"] = "options_complete"
    state["stages_completed"] = state.get("stages_completed", []) + ["options"]
    return state


async def target_state_node(state: ArchitectureWorkflowState) -> ArchitectureWorkflowState:
    a2 = create_a2_agent()
    state["current_task"] = "design_target_state"
    state = await a2.run(state)
    state["workflow_stage"] = "target_state_complete"
    state["stages_completed"] = state.get("stages_completed", []) + ["target_state"]
    return state


async def migration_node(state: ArchitectureWorkflowState) -> ArchitectureWorkflowState:
    a2 = create_a2_agent()
    state["current_task"] = "plan_migration"
    state = await a2.run(state)
    state["workflow_stage"] = "migration_complete"
    state["stages_completed"] = state.get("stages_completed", []) + ["migration"]
    return state


async def sizing_node(state: ArchitectureWorkflowState) -> ArchitectureWorkflowState:
    a2 = create_a2_agent()
    state["current_task"] = "calculate_sizing"
    state = await a2.run(state)
    state["workflow_stage"] = "sizing_complete"
    state["stages_completed"] = state.get("stages_completed", []) + ["sizing"]
    return state


async def document_node(state: ArchitectureWorkflowState) -> ArchitectureWorkflowState:
    a2 = create_a2_agent()
    state["current_task"] = "draft_document"
    state = await a2.run(state)
    state["workflow_stage"] = "document_drafted"
    state["stages_completed"] = state.get("stages_completed", []) + ["document"]
    return state


async def review_node(state: ArchitectureWorkflowState) -> ArchitectureWorkflowState:
    state["human_approval_needed"] = True
    state["human_approval_request"] = {
        "artifact_type": "architecture_document",
        "artifact_id": state.get("engagement_id", "unknown"),
        "description": f"Review Architecture Document for {state.get('client_name')}",
        "options": ["approve", "revise", "reject"],
    }
    state["workflow_stage"] = "pending_review"
    return state


async def process_review(state: ArchitectureWorkflowState) -> ArchitectureWorkflowState:
    response = state.get("human_response", "")
    if response == "approve":
        state["architecture_approved"] = True
        state["workflow_stage"] = "approved"
    elif response == "revise":
        state["workflow_stage"] = "revision_needed"
    else:
        state["status"] = AgentStatus.FAILED
        state["workflow_stage"] = "rejected"
    state["human_approval_needed"] = False
    state["human_response"] = None
    return state


async def finalize(state: ArchitectureWorkflowState) -> ArchitectureWorkflowState:
    state["workflow_stage"] = "finalized"
    state["status"] = AgentStatus.COMPLETED
    return state


def route_after_review(state: ArchitectureWorkflowState) -> Literal["finalize", "document", "end"]:
    if state.get("architecture_approved"):
        return "finalize"
    elif state.get("workflow_stage") == "revision_needed":
        return "document"
    return "end"


def create_architecture_workflow() -> StateGraph:
    """Create architecture design workflow graph."""
    workflow = StateGraph(ArchitectureWorkflowState)
    
    workflow.add_node("initialize", initialize)
    workflow.add_node("current_state", current_state_node)
    workflow.add_node("options", options_node)
    workflow.add_node("target_state", target_state_node)
    workflow.add_node("migration", migration_node)
    workflow.add_node("sizing", sizing_node)
    workflow.add_node("document", document_node)
    workflow.add_node("review", review_node)
    workflow.add_node("process_review", process_review)
    workflow.add_node("finalize", finalize)
    
    workflow.add_edge("initialize", "current_state")
    workflow.add_edge("current_state", "options")
    workflow.add_edge("options", "target_state")
    workflow.add_edge("target_state", "migration")
    workflow.add_edge("migration", "sizing")
    workflow.add_edge("sizing", "document")
    workflow.add_edge("document", "review")
    workflow.add_edge("review", "process_review")
    
    workflow.add_conditional_edges(
        "process_review", route_after_review,
        {"finalize": "finalize", "document": "document", "end": END}
    )
    
    workflow.add_edge("finalize", END)
    workflow.set_entry_point("initialize")
    
    return workflow


async def run_architecture_design(
    client_name: str,
    engagement_id: str | None = None,
    wp1_findings: dict[str, Any] | None = None,
    constraints: list[str] | None = None,
    thread_id: str | None = None,
) -> ArchitectureWorkflowState:
    """Execute architecture design workflow."""
    from datetime import datetime
    
    orchestrator = get_orchestrator()
    workflow = create_architecture_workflow()
    orchestrator._workflows["architecture_design"] = workflow
    
    if not engagement_id:
        engagement_id = f"ARCH-{client_name[:4].upper()}-{datetime.now().strftime('%Y%m%d')}"
    
    initial_state: ArchitectureWorkflowState = {
        "workflow_id": "architecture_design",
        "agent_id": "a2",
        "client_name": client_name,
        "engagement_id": engagement_id,
        "wp1_findings": wp1_findings or {},
        "constraints": constraints or [],
        "messages": [], "artifacts": [], "decisions": [], "errors": [],
        "status": AgentStatus.IDLE,
        "current_state_complete": False, "target_designed": False,
        "options_evaluated": False, "migration_planned": False,
        "sizing_complete": False, "document_drafted": False,
        "architecture_approved": False,
    }
    
    return await orchestrator.run_workflow("architecture_design", initial_state, thread_id=thread_id or engagement_id)


async def resume_architecture_workflow(engagement_id: str, human_response: str) -> ArchitectureWorkflowState:
    """Resume architecture workflow."""
    orchestrator = get_orchestrator()
    if "architecture_design" not in orchestrator._workflows:
        orchestrator._workflows["architecture_design"] = create_architecture_workflow()
    return await orchestrator.resume_workflow("architecture_design", thread_id=engagement_id, human_response=human_response)
