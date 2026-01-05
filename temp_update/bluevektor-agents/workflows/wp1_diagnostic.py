"""
BlueVektor Agents - WP1 Diagnostic Workflow
Complete workflow for executing WP1 Cloud Transformation Diagnostic.
"""
from typing import Any, Literal

import structlog
from langgraph.graph import END, StateGraph

from agents.a3_assessment import A3AssessmentAgent, A3State, create_a3_agent
from core.orchestrator import AgentStatus, get_orchestrator

logger = structlog.get_logger()


# =============================================================================
# Workflow State
# =============================================================================

class WP1WorkflowState(A3State, total=False):
    """State for WP1 diagnostic workflow."""
    
    # Workflow tracking
    workflow_stage: str
    stages_completed: list[str]
    
    # Client context
    engagement_start_date: str
    engagement_end_date: str
    stakeholders: list[dict[str, str]]
    
    # Deliverables tracking
    deliverables: dict[str, dict[str, Any]]
    
    # Review status
    internal_review_complete: bool
    client_review_complete: bool
    
    # Final outputs
    final_report_path: str | None
    presentation_path: str | None


# =============================================================================
# Workflow Nodes
# =============================================================================

async def initialize_engagement(state: WP1WorkflowState) -> WP1WorkflowState:
    """
    Node: Initialize WP1 engagement.
    Sets up engagement context and validates inputs.
    """
    logger.info("Initializing WP1 engagement", client=state.get("client_name"))
    
    # Validate required inputs
    required = ["client_name", "engagement_id"]
    missing = [f for f in required if not state.get(f)]
    
    if missing:
        state["errors"] = state.get("errors", []) + [f"Missing required: {missing}"]
        state["status"] = AgentStatus.FAILED
        return state
    
    # Initialize tracking
    state["stages_completed"] = []
    state["deliverables"] = {}
    state["workflow_stage"] = "initialized"
    state["status"] = AgentStatus.RUNNING
    
    logger.info("WP1 engagement initialized", engagement_id=state.get("engagement_id"))
    
    return state


async def collect_evidence_node(state: WP1WorkflowState) -> WP1WorkflowState:
    """
    Node: Evidence collection phase.
    Collects all available evidence and identifies gaps.
    """
    logger.info("Evidence collection phase")
    
    a3 = create_a3_agent()
    
    state["current_task"] = "collect_evidence"
    state = await a3.run(state)
    
    state["workflow_stage"] = "evidence_collected"
    state["stages_completed"] = state.get("stages_completed", []) + ["evidence"]
    
    # Track deliverable
    for artifact in state.get("artifacts", []):
        if artifact["type"] == "evidence_collection":
            state["deliverables"]["evidence_plan"] = {
                "name": artifact["name"],
                "status": "complete",
                "timestamp": artifact["created_at"]
            }
    
    return state


async def analyze_volumetrics_node(state: WP1WorkflowState) -> WP1WorkflowState:
    """
    Node: Volumetrics analysis phase.
    Analyzes all collected metrics and benchmarks.
    """
    logger.info("Volumetrics analysis phase")
    
    a3 = create_a3_agent()
    state = await a3._analyze_volumetrics(state)
    
    state["workflow_stage"] = "volumetrics_analyzed"
    state["stages_completed"] = state.get("stages_completed", []) + ["volumetrics"]
    
    # Track deliverable
    for artifact in state.get("artifacts", []):
        if artifact["type"] == "volumetrics_analysis":
            state["deliverables"]["volumetrics"] = {
                "name": artifact["name"],
                "status": "complete",
                "timestamp": artifact["created_at"]
            }
    
    return state


async def analyze_apps_node(state: WP1WorkflowState) -> WP1WorkflowState:
    """
    Node: App analysis phase.
    Performs CSK 4R analysis on marketplace apps.
    """
    logger.info("App analysis phase (CSK 4R)")
    
    a3 = create_a3_agent()
    state = await a3._analyze_apps(state)
    
    state["workflow_stage"] = "apps_analyzed"
    state["stages_completed"] = state.get("stages_completed", []) + ["apps"]
    
    # Track deliverable
    for artifact in state.get("artifacts", []):
        if artifact["type"] == "app_analysis":
            state["deliverables"]["app_analysis"] = {
                "name": artifact["name"],
                "status": "complete",
                "timestamp": artifact["created_at"]
            }
    
    return state


async def identify_hotspots_node(state: WP1WorkflowState) -> WP1WorkflowState:
    """
    Node: Hotspot identification phase.
    Identifies, scores, and prioritizes all findings.
    """
    logger.info("Hotspot identification phase")
    
    a3 = create_a3_agent()
    
    state["current_task"] = "identify_hotspots"
    state = await a3.run(state)
    
    state["workflow_stage"] = "hotspots_identified"
    state["stages_completed"] = state.get("stages_completed", []) + ["hotspots"]
    
    # Track deliverable
    for artifact in state.get("artifacts", []):
        if artifact["type"] == "hotspot_map":
            state["deliverables"]["hotspot_map"] = {
                "name": artifact["name"],
                "status": "complete",
                "timestamp": artifact["created_at"]
            }
    
    return state


async def generate_plan_node(state: WP1WorkflowState) -> WP1WorkflowState:
    """
    Node: Plan generation phase.
    Creates 30/60/90 day transformation plan.
    """
    logger.info("Plan generation phase")
    
    a3 = create_a3_agent()
    
    state["current_task"] = "generate_plan"
    state = await a3.run(state)
    
    state["workflow_stage"] = "plan_generated"
    state["stages_completed"] = state.get("stages_completed", []) + ["plan"]
    
    # Track deliverable
    for artifact in state.get("artifacts", []):
        if artifact["type"] == "plan_30_60_90":
            state["deliverables"]["plan_30_60_90"] = {
                "name": artifact["name"],
                "status": "complete",
                "timestamp": artifact["created_at"]
            }
    
    return state


async def draft_report_node(state: WP1WorkflowState) -> WP1WorkflowState:
    """
    Node: Report drafting phase.
    Creates complete WP1 diagnostic report.
    """
    logger.info("Report drafting phase")
    
    a3 = create_a3_agent()
    
    state["current_task"] = "draft_report"
    state = await a3.run(state)
    
    state["workflow_stage"] = "report_drafted"
    state["stages_completed"] = state.get("stages_completed", []) + ["report"]
    
    # Track deliverable
    for artifact in state.get("artifacts", []):
        if artifact["type"] == "wp1_report":
            state["deliverables"]["wp1_report"] = {
                "name": artifact["name"],
                "status": "draft",
                "requires_review": True,
                "timestamp": artifact["created_at"]
            }
    
    return state


async def internal_review_node(state: WP1WorkflowState) -> WP1WorkflowState:
    """
    Node: Internal review checkpoint.
    Pauses for BlueVektor internal QA.
    """
    logger.info("Internal review checkpoint")
    
    state["human_approval_needed"] = True
    state["human_approval_request"] = {
        "artifact_type": "wp1_report",
        "artifact_id": state.get("engagement_id", "unknown"),
        "description": f"Review WP1 Report for {state.get('client_name')}",
        "options": ["approve", "revise", "reject"],
    }
    state["workflow_stage"] = "pending_internal_review"
    
    return state


async def process_internal_review(state: WP1WorkflowState) -> WP1WorkflowState:
    """
    Node: Process internal review decision.
    """
    logger.info("Processing internal review")
    
    response = state.get("human_response", "")
    
    if response == "approve":
        state["internal_review_complete"] = True
        state["workflow_stage"] = "internal_review_approved"
        
        # Update deliverable status
        if "wp1_report" in state.get("deliverables", {}):
            state["deliverables"]["wp1_report"]["status"] = "reviewed"
    
    elif response == "revise":
        state["workflow_stage"] = "revision_needed"
        state["internal_review_complete"] = False
    
    else:  # reject
        state["status"] = AgentStatus.FAILED
        state["workflow_stage"] = "rejected"
    
    state["human_approval_needed"] = False
    state["human_response"] = None
    
    return state


async def finalize_deliverables(state: WP1WorkflowState) -> WP1WorkflowState:
    """
    Node: Finalize all deliverables for client.
    """
    logger.info("Finalizing deliverables")
    
    client_name = state.get("client_name", "Client")
    engagement_id = state.get("engagement_id", "WP1")
    
    a3 = create_a3_agent()
    
    # Create executive summary / readout
    prompt = f"""Create an executive slide readout for WP1 delivery to {client_name}.

Engagement: {engagement_id}

Based on all analysis:
{state.get('raw_evidence', {})}

Create a 10-slide executive presentation outline:

1. **Cover Slide**
   - Title, client, date, BlueVektor branding

2. **Agenda**
   - What we'll cover

3. **Engagement Overview**
   - Scope, timeline, methodology

4. **Current State Summary**
   - Key metrics at a glance
   - Visual dashboard

5. **Key Findings**
   - Top 5 findings with impact
   - Traffic light status

6. **Hotspot Heatmap**
   - Visual prioritization matrix
   - Quick wins highlighted

7. **Recommendations Overview**
   - Strategic initiatives
   - Effort vs impact visual

8. **30/60/90 Plan Summary**
   - Timeline visual
   - Key milestones

9. **Resource & Investment**
   - Effort estimates
   - Team requirements
   - ROI potential

10. **Next Steps & Discussion**
    - Immediate actions
    - Decision points
    - Q&A

For each slide, include:
- Title
- Key message (1 sentence)
- Content bullets (3-5)
- Visual suggestion
- Speaker notes
"""
    
    presentation_outline = await a3.think(prompt)
    
    state = a3.add_artifact(
        state,
        "presentation_outline",
        f"WP1_Presentation_{client_name}_{engagement_id}",
        presentation_outline
    )
    
    state["deliverables"]["presentation"] = {
        "name": f"WP1_Presentation_{client_name}",
        "status": "complete",
        "timestamp": state["artifacts"][-1]["created_at"]
    }
    
    state["workflow_stage"] = "deliverables_finalized"
    state["stages_completed"] = state.get("stages_completed", []) + ["finalized"]
    
    return state


async def complete_engagement(state: WP1WorkflowState) -> WP1WorkflowState:
    """
    Node: Mark engagement as complete.
    """
    logger.info("Completing WP1 engagement", client=state.get("client_name"))
    
    state["status"] = AgentStatus.COMPLETED
    state["workflow_stage"] = "complete"
    
    # Log completion
    a3 = create_a3_agent()
    state = a3.add_decision(
        state,
        "engagement_complete",
        f"WP1 Diagnostic completed for {state.get('client_name')}",
        f"Deliverables: {list(state.get('deliverables', {}).keys())}"
    )
    
    return state


# =============================================================================
# Routing Functions
# =============================================================================

def route_after_internal_review(
    state: WP1WorkflowState,
) -> Literal["finalize_deliverables", "draft_report", "end"]:
    """Route based on internal review decision."""
    
    if state.get("internal_review_complete"):
        return "finalize_deliverables"
    elif state.get("workflow_stage") == "revision_needed":
        return "draft_report"  # Go back to drafting
    else:
        return "end"  # Rejected


def check_workflow_health(
    state: WP1WorkflowState,
) -> Literal["continue", "error"]:
    """Check if workflow should continue or has errors."""
    
    if state.get("errors"):
        return "error"
    return "continue"


# =============================================================================
# Workflow Builder
# =============================================================================

def create_wp1_workflow() -> StateGraph:
    """
    Create the WP1 Diagnostic workflow graph.
    
    Flow:
    initialize → collect_evidence → analyze_volumetrics → analyze_apps →
    identify_hotspots → generate_plan → draft_report →
    internal_review → [approved] → finalize_deliverables → complete → END
                   → [revise] → draft_report (loop)
                   → [reject] → END
    """
    
    workflow = StateGraph(WP1WorkflowState)
    
    # Add nodes
    workflow.add_node("initialize", initialize_engagement)
    workflow.add_node("collect_evidence", collect_evidence_node)
    workflow.add_node("analyze_volumetrics", analyze_volumetrics_node)
    workflow.add_node("analyze_apps", analyze_apps_node)
    workflow.add_node("identify_hotspots", identify_hotspots_node)
    workflow.add_node("generate_plan", generate_plan_node)
    workflow.add_node("draft_report", draft_report_node)
    workflow.add_node("internal_review", internal_review_node)
    workflow.add_node("process_review", process_internal_review)
    workflow.add_node("finalize_deliverables", finalize_deliverables)
    workflow.add_node("complete", complete_engagement)
    workflow.add_node("error", lambda s: {**s, "status": AgentStatus.FAILED})
    
    # Define edges - main flow
    workflow.add_edge("initialize", "collect_evidence")
    workflow.add_edge("collect_evidence", "analyze_volumetrics")
    workflow.add_edge("analyze_volumetrics", "analyze_apps")
    workflow.add_edge("analyze_apps", "identify_hotspots")
    workflow.add_edge("identify_hotspots", "generate_plan")
    workflow.add_edge("generate_plan", "draft_report")
    workflow.add_edge("draft_report", "internal_review")
    
    # Human review checkpoint - workflow pauses here
    workflow.add_edge("internal_review", "process_review")
    
    # Conditional after review processing
    workflow.add_conditional_edges(
        "process_review",
        route_after_internal_review,
        {
            "finalize_deliverables": "finalize_deliverables",
            "draft_report": "draft_report",
            "end": END,
        }
    )
    
    # Final steps
    workflow.add_edge("finalize_deliverables", "complete")
    workflow.add_edge("complete", END)
    workflow.add_edge("error", END)
    
    # Set entry point
    workflow.set_entry_point("initialize")
    
    return workflow


# =============================================================================
# Workflow Execution
# =============================================================================

async def run_wp1_diagnostic(
    client_name: str,
    engagement_id: str,
    input_data: dict[str, Any] | None = None,
    existing_exports: list[str] | None = None,
    thread_id: str | None = None,
) -> WP1WorkflowState:
    """
    Execute the WP1 Diagnostic workflow.
    
    Args:
        client_name: Name of the client
        engagement_id: Unique engagement identifier
        input_data: Additional input data (instance info, exports, etc.)
        existing_exports: List of available export files
        thread_id: Optional thread ID for resumption
        
    Returns:
        Final workflow state
    """
    orchestrator = get_orchestrator()
    
    # Create and register workflow
    workflow = create_wp1_workflow()
    orchestrator._workflows["wp1_diagnostic"] = workflow
    
    # Initial state
    initial_state: WP1WorkflowState = {
        "workflow_id": "wp1_diagnostic",
        "agent_id": "a3",
        "client_name": client_name,
        "engagement_id": engagement_id,
        "input_data": input_data or {},
        "existing_exports": existing_exports or [],
        "messages": [],
        "artifacts": [],
        "decisions": [],
        "errors": [],
        "status": AgentStatus.IDLE,
        "evidence_collected": False,
        "analysis_complete": False,
        "plan_generated": False,
        "report_drafted": False,
        "internal_review_complete": False,
        "client_review_complete": False,
    }
    
    # Run workflow
    result = await orchestrator.run_workflow(
        "wp1_diagnostic",
        initial_state,
        thread_id=thread_id or engagement_id,
    )
    
    return result


async def resume_wp1_diagnostic(
    engagement_id: str,
    human_response: str,
) -> WP1WorkflowState:
    """
    Resume WP1 workflow after human review.
    
    Args:
        engagement_id: Engagement ID (used as thread_id)
        human_response: Human decision (approve/revise/reject)
        
    Returns:
        Updated workflow state
    """
    orchestrator = get_orchestrator()
    
    # Ensure workflow is registered
    if "wp1_diagnostic" not in orchestrator._workflows:
        workflow = create_wp1_workflow()
        orchestrator._workflows["wp1_diagnostic"] = workflow
    
    result = await orchestrator.resume_workflow(
        "wp1_diagnostic",
        thread_id=engagement_id,
        human_response=human_response,
    )
    
    return result


# =============================================================================
# CLI Integration
# =============================================================================

if __name__ == "__main__":
    import asyncio
    
    async def main():
        # Example usage
        result = await run_wp1_diagnostic(
            client_name="Acme Corp",
            engagement_id="WP1-ACME-001",
            input_data={
                "instance_url": "https://acme.atlassian.net",
                "products": ["jira_software", "confluence"],
                "user_count": 500,
                "notes": "Migration from Server planned for Q2"
            }
        )
        
        print(f"Status: {result.get('status')}")
        print(f"Stage: {result.get('workflow_stage')}")
        print(f"Stages completed: {result.get('stages_completed')}")
        print(f"Deliverables: {list(result.get('deliverables', {}).keys())}")
        
        if result.get("human_approval_needed"):
            print("\n⚠️  Workflow paused - awaiting human review")
            print(f"Request: {result.get('human_approval_request')}")
    
    asyncio.run(main())
