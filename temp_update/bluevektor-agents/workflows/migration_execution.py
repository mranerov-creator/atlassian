"""
BlueVektor Agents - Migration Execution Workflow
Complete workflow for WP2/WP5 migration planning and execution.
"""
from typing import Any, Literal
import structlog
from langgraph.graph import END, StateGraph
from agents.a5_migration import A5State, MigrationType, create_a5_agent
from core.orchestrator import AgentStatus, get_orchestrator

logger = structlog.get_logger()


class MigrationWorkflowState(A5State, total=False):
    """State for migration workflow."""
    workflow_stage: str
    stages_completed: list[str]
    deliverables: dict[str, dict[str, Any]]
    plan_approved: bool


async def initialize(state: MigrationWorkflowState) -> MigrationWorkflowState:
    state["stages_completed"] = []
    state["deliverables"] = {}
    state["workflow_stage"] = "initialized"
    state["status"] = AgentStatus.RUNNING
    return state


async def inventory_node(state: MigrationWorkflowState) -> MigrationWorkflowState:
    a5 = create_a5_agent()
    state["current_task"] = "create_inventory"
    state = await a5.run(state)
    state["workflow_stage"] = "inventory_complete"
    state["stages_completed"] = state.get("stages_completed", []) + ["inventory"]
    return state


async def waves_node(state: MigrationWorkflowState) -> MigrationWorkflowState:
    a5 = create_a5_agent()
    state["current_task"] = "plan_waves"
    state = await a5.run(state)
    state["workflow_stage"] = "waves_planned"
    state["stages_completed"] = state.get("stages_completed", []) + ["waves"]
    return state


async def runbooks_node(state: MigrationWorkflowState) -> MigrationWorkflowState:
    a5 = create_a5_agent()
    state["current_task"] = "create_runbooks"
    state = await a5.run(state)
    state["workflow_stage"] = "runbooks_created"
    state["stages_completed"] = state.get("stages_completed", []) + ["runbooks"]
    return state


async def communications_node(state: MigrationWorkflowState) -> MigrationWorkflowState:
    a5 = create_a5_agent()
    state["current_task"] = "prepare_communications"
    state = await a5.run(state)
    state["workflow_stage"] = "communications_ready"
    state["stages_completed"] = state.get("stages_completed", []) + ["communications"]
    return state


async def validation_node(state: MigrationWorkflowState) -> MigrationWorkflowState:
    a5 = create_a5_agent()
    state["current_task"] = "create_validation_plan"
    state = await a5.run(state)
    state["workflow_stage"] = "validation_planned"
    state["stages_completed"] = state.get("stages_completed", []) + ["validation"]
    return state


async def checklists_node(state: MigrationWorkflowState) -> MigrationWorkflowState:
    a5 = create_a5_agent()
    state["current_task"] = "generate_checklists"
    state = await a5.run(state)
    state["workflow_stage"] = "checklists_ready"
    state["stages_completed"] = state.get("stages_completed", []) + ["checklists"]
    return state


async def plan_node(state: MigrationWorkflowState) -> MigrationWorkflowState:
    a5 = create_a5_agent()
    state["current_task"] = "draft_migration_plan"
    state = await a5.run(state)
    state["workflow_stage"] = "plan_drafted"
    state["stages_completed"] = state.get("stages_completed", []) + ["plan"]
    return state


async def review_node(state: MigrationWorkflowState) -> MigrationWorkflowState:
    state["human_approval_needed"] = True
    state["human_approval_request"] = {
        "artifact_type": "migration_plan",
        "artifact_id": state.get("engagement_id", "unknown"),
        "description": f"Review Migration Plan for {state.get('client_name')}",
        "options": ["approve", "revise", "reject"],
    }
    state["workflow_stage"] = "pending_review"
    return state


async def process_review(state: MigrationWorkflowState) -> MigrationWorkflowState:
    response = state.get("human_response", "")
    if response == "approve":
        state["plan_approved"] = True
        state["workflow_stage"] = "approved"
    elif response == "revise":
        state["workflow_stage"] = "revision_needed"
    else:
        state["status"] = AgentStatus.FAILED
        state["workflow_stage"] = "rejected"
    state["human_approval_needed"] = False
    state["human_response"] = None
    return state


async def finalize(state: MigrationWorkflowState) -> MigrationWorkflowState:
    state["workflow_stage"] = "finalized"
    state["status"] = AgentStatus.COMPLETED
    return state


def route_after_review(state: MigrationWorkflowState) -> Literal["finalize", "plan", "end"]:
    if state.get("plan_approved"):
        return "finalize"
    elif state.get("workflow_stage") == "revision_needed":
        return "plan"
    return "end"


def create_migration_workflow() -> StateGraph:
    """Create migration workflow graph."""
    workflow = StateGraph(MigrationWorkflowState)
    
    workflow.add_node("initialize", initialize)
    workflow.add_node("inventory", inventory_node)
    workflow.add_node("waves", waves_node)
    workflow.add_node("runbooks", runbooks_node)
    workflow.add_node("communications", communications_node)
    workflow.add_node("validation", validation_node)
    workflow.add_node("checklists", checklists_node)
    workflow.add_node("plan", plan_node)
    workflow.add_node("review", review_node)
    workflow.add_node("process_review", process_review)
    workflow.add_node("finalize", finalize)
    
    workflow.add_edge("initialize", "inventory")
    workflow.add_edge("inventory", "waves")
    workflow.add_edge("waves", "runbooks")
    workflow.add_edge("runbooks", "communications")
    workflow.add_edge("communications", "validation")
    workflow.add_edge("validation", "checklists")
    workflow.add_edge("checklists", "plan")
    workflow.add_edge("plan", "review")
    workflow.add_edge("review", "process_review")
    
    workflow.add_conditional_edges(
        "process_review", route_after_review,
        {"finalize": "finalize", "plan": "plan", "end": END}
    )
    
    workflow.add_edge("finalize", END)
    workflow.set_entry_point("initialize")
    
    return workflow


async def run_migration_planning(
    client_name: str,
    migration_type: MigrationType = MigrationType.SERVER_TO_CLOUD,
    engagement_id: str | None = None,
    architecture_design: dict[str, Any] | None = None,
    thread_id: str | None = None,
) -> MigrationWorkflowState:
    """Execute migration planning workflow."""
    from datetime import datetime
    
    orchestrator = get_orchestrator()
    workflow = create_migration_workflow()
    orchestrator._workflows["migration_planning"] = workflow
    
    wp_prefix = "WP2" if migration_type in [MigrationType.SERVER_TO_CLOUD, MigrationType.DC_TO_CLOUD] else "WP5"
    if not engagement_id:
        engagement_id = f"{wp_prefix}-{client_name[:4].upper()}-{datetime.now().strftime('%Y%m%d')}"
    
    initial_state: MigrationWorkflowState = {
        "workflow_id": "migration_planning",
        "agent_id": "a5",
        "client_name": client_name,
        "engagement_id": engagement_id,
        "migration_type": migration_type,
        "architecture_design": architecture_design or {},
        "messages": [], "artifacts": [], "decisions": [], "errors": [],
        "status": AgentStatus.IDLE,
        "inventory_complete": False, "waves_planned": False,
        "runbooks_created": False, "communications_ready": False,
        "execution_started": False, "migration_complete": False,
        "plan_approved": False,
    }
    
    return await orchestrator.run_workflow("migration_planning", initial_state, thread_id=thread_id or engagement_id)


async def resume_migration_workflow(engagement_id: str, human_response: str) -> MigrationWorkflowState:
    """Resume migration workflow."""
    orchestrator = get_orchestrator()
    if "migration_planning" not in orchestrator._workflows:
        orchestrator._workflows["migration_planning"] = create_migration_workflow()
    return await orchestrator.resume_workflow("migration_planning", thread_id=engagement_id, human_response=human_response)
