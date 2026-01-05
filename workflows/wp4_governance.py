"""
BlueVektor Agents - WP4 Governance Workflow
"""
from typing import Any, Literal
import structlog
from langgraph.graph import END, StateGraph
from agents.a4_governance import A4State, create_a4_agent
from core.orchestrator import AgentStatus, get_orchestrator

logger = structlog.get_logger()


class WP4WorkflowState(A4State, total=False):
    """State for WP4 workflow."""
    workflow_stage: str
    stages_completed: list[str]
    deliverables: dict[str, dict[str, Any]]
    internal_review_complete: bool


async def initialize(state: WP4WorkflowState) -> WP4WorkflowState:
    state["stages_completed"] = []
    state["deliverables"] = {}
    state["workflow_stage"] = "initialized"
    state["status"] = AgentStatus.RUNNING
    return state


async def operating_model_node(state: WP4WorkflowState) -> WP4WorkflowState:
    a4 = create_a4_agent()
    state["current_task"] = "design_operating_model"
    state = await a4.run(state)
    state["workflow_stage"] = "operating_model_complete"
    state["stages_completed"] = state.get("stages_completed", []) + ["operating_model"]
    return state


async def policies_node(state: WP4WorkflowState) -> WP4WorkflowState:
    a4 = create_a4_agent()
    state["current_task"] = "create_policies"
    state = await a4.run(state)
    state["workflow_stage"] = "policies_complete"
    state["stages_completed"] = state.get("stages_completed", []) + ["policies"]
    return state


async def standards_node(state: WP4WorkflowState) -> WP4WorkflowState:
    a4 = create_a4_agent()
    state["current_task"] = "create_standards"
    state = await a4.run(state)
    state["workflow_stage"] = "standards_complete"
    state["stages_completed"] = state.get("stages_completed", []) + ["standards"]
    return state


async def runbooks_node(state: WP4WorkflowState) -> WP4WorkflowState:
    a4 = create_a4_agent()
    state["current_task"] = "create_runbooks"
    state = await a4.run(state)
    state["workflow_stage"] = "runbooks_complete"
    state["stages_completed"] = state.get("stages_completed", []) + ["runbooks"]
    return state


async def kpis_node(state: WP4WorkflowState) -> WP4WorkflowState:
    a4 = create_a4_agent()
    state["current_task"] = "define_kpis"
    state = await a4.run(state)
    state["workflow_stage"] = "kpis_complete"
    state["stages_completed"] = state.get("stages_completed", []) + ["kpis"]
    return state


async def handbook_node(state: WP4WorkflowState) -> WP4WorkflowState:
    a4 = create_a4_agent()
    state["current_task"] = "draft_handbook"
    state = await a4.run(state)
    state["workflow_stage"] = "handbook_drafted"
    state["stages_completed"] = state.get("stages_completed", []) + ["handbook"]
    return state


async def review_node(state: WP4WorkflowState) -> WP4WorkflowState:
    state["human_approval_needed"] = True
    state["human_approval_request"] = {
        "artifact_type": "governance_handbook",
        "artifact_id": state.get("engagement_id", "unknown"),
        "description": f"Review WP4 Handbook for {state.get('client_name')}",
        "options": ["approve", "revise", "reject"],
    }
    state["workflow_stage"] = "pending_review"
    return state


async def process_review(state: WP4WorkflowState) -> WP4WorkflowState:
    response = state.get("human_response", "")
    if response == "approve":
        state["internal_review_complete"] = True
        state["workflow_stage"] = "approved"
    elif response == "revise":
        state["workflow_stage"] = "revision_needed"
    else:
        state["status"] = AgentStatus.FAILED
        state["workflow_stage"] = "rejected"
    state["human_approval_needed"] = False
    state["human_response"] = None
    return state


async def finalize(state: WP4WorkflowState) -> WP4WorkflowState:
    state["workflow_stage"] = "finalized"
    state["status"] = AgentStatus.COMPLETED
    return state


def route_after_review(state: WP4WorkflowState) -> Literal["finalize", "handbook", "end"]:
    if state.get("internal_review_complete"):
        return "finalize"
    elif state.get("workflow_stage") == "revision_needed":
        return "handbook"
    return "end"


def create_wp4_workflow() -> StateGraph:
    """Create WP4 workflow graph."""
    workflow = StateGraph(WP4WorkflowState)
    
    workflow.add_node("initialize", initialize)
    workflow.add_node("operating_model", operating_model_node)
    workflow.add_node("policies", policies_node)
    workflow.add_node("standards", standards_node)
    workflow.add_node("runbooks", runbooks_node)
    workflow.add_node("kpis", kpis_node)
    workflow.add_node("handbook", handbook_node)
    workflow.add_node("review", review_node)
    workflow.add_node("process_review", process_review)
    workflow.add_node("finalize", finalize)
    
    workflow.add_edge("initialize", "operating_model")
    workflow.add_edge("operating_model", "policies")
    workflow.add_edge("policies", "standards")
    workflow.add_edge("standards", "runbooks")
    workflow.add_edge("runbooks", "kpis")
    workflow.add_edge("kpis", "handbook")
    workflow.add_edge("handbook", "review")
    workflow.add_edge("review", "process_review")
    
    workflow.add_conditional_edges(
        "process_review", route_after_review,
        {"finalize": "finalize", "handbook": "handbook", "end": END}
    )
    
    workflow.add_edge("finalize", END)
    workflow.set_entry_point("initialize")
    
    return workflow


async def run_wp4_governance(
    client_name: str,
    engagement_id: str | None = None,
    wp1_findings: dict[str, Any] | None = None,
    thread_id: str | None = None,
) -> WP4WorkflowState:
    """Execute WP4 workflow."""
    from datetime import datetime
    
    orchestrator = get_orchestrator()
    workflow = create_wp4_workflow()
    orchestrator._workflows["wp4_governance"] = workflow
    
    if not engagement_id:
        engagement_id = f"WP4-{client_name[:4].upper()}-{datetime.now().strftime('%Y%m%d')}"
    
    initial_state: WP4WorkflowState = {
        "workflow_id": "wp4_governance",
        "agent_id": "a4",
        "client_name": client_name,
        "engagement_id": engagement_id,
        "wp1_findings": wp1_findings or {},
        "messages": [], "artifacts": [], "decisions": [], "errors": [],
        "status": AgentStatus.IDLE,
        "operating_model_complete": False, "policies_complete": False,
        "standards_complete": False, "runbooks_complete": False,
        "kpis_complete": False, "handbook_drafted": False,
        "internal_review_complete": False,
    }
    
    return await orchestrator.run_workflow("wp4_governance", initial_state, thread_id=thread_id or engagement_id)


async def resume_wp4_workflow(engagement_id: str, human_response: str) -> WP4WorkflowState:
    """Resume WP4 workflow."""
    orchestrator = get_orchestrator()
    if "wp4_governance" not in orchestrator._workflows:
        orchestrator._workflows["wp4_governance"] = create_wp4_workflow()
    return await orchestrator.resume_workflow("wp4_governance", thread_id=engagement_id, human_response=human_response)
