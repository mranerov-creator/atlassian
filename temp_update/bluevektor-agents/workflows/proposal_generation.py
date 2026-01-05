"""
BlueVektor Agents - Proposal Generation Workflow
End-to-end workflow from opportunity brief to client-ready proposal.
"""
from typing import Any, Literal

import structlog
from langgraph.graph import END, StateGraph

from agents.a6_delivery import A6DeliveryAgent, A6State, DeliverableType, create_a6_agent
from core.orchestrator import AgentStatus, get_orchestrator

logger = structlog.get_logger()


# =============================================================================
# Workflow State
# =============================================================================

class ProposalWorkflowState(A6State, total=False):
    """State for proposal generation workflow."""
    
    # Workflow tracking
    workflow_stage: str
    
    # Source
    source_agent: str  # a1, a3, etc.
    source_artifact: str
    
    # Outputs
    one_pager_generated: bool
    sow_generated: bool
    estimate_generated: bool
    
    # Review
    pricing_approved: bool
    content_approved: bool
    
    # Final
    final_proposal_path: str | None


# =============================================================================
# Workflow Nodes
# =============================================================================

async def validate_input(state: ProposalWorkflowState) -> ProposalWorkflowState:
    """
    Node: Validate that we have sufficient input to generate proposal.
    """
    logger.info("Validating proposal inputs")
    
    opportunity_brief = state.get("opportunity_brief", {})
    
    # Check required fields
    required = ["company_name", "problem_statement"]
    missing = []
    
    for field in required:
        if not opportunity_brief.get(field):
            # Try alternate field names
            alt_found = False
            if field == "company_name" and opportunity_brief.get("client_name"):
                alt_found = True
            if not alt_found:
                missing.append(field)
    
    if missing:
        state["errors"] = state.get("errors", []) + [f"Missing in opportunity brief: {missing}"]
        # Don't fail - proceed with what we have
        logger.warning("Proceeding with incomplete brief", missing=missing)
    
    state["workflow_stage"] = "validated"
    state["status"] = AgentStatus.RUNNING
    
    return state


async def estimate_effort_node(state: ProposalWorkflowState) -> ProposalWorkflowState:
    """
    Node: Generate effort estimate for the engagement.
    """
    logger.info("Generating effort estimate")
    
    a6 = create_a6_agent()
    
    state["current_task"] = "estimate_effort"
    state = await a6.run(state)
    
    state["workflow_stage"] = "effort_estimated"
    state["estimate_generated"] = True
    
    return state


async def generate_one_pager_node(state: ProposalWorkflowState) -> ProposalWorkflowState:
    """
    Node: Generate one-page proposal summary.
    """
    logger.info("Generating one-pager")
    
    a6 = create_a6_agent()
    
    state["current_task"] = "generate_one_pager"
    state = await a6.run(state)
    
    state["workflow_stage"] = "one_pager_generated"
    state["one_pager_generated"] = True
    
    return state


async def generate_sow_node(state: ProposalWorkflowState) -> ProposalWorkflowState:
    """
    Node: Generate full Statement of Work.
    """
    logger.info("Generating SoW")
    
    a6 = create_a6_agent()
    
    state["current_task"] = "generate_sow"
    state = await a6.run(state)
    
    state["workflow_stage"] = "sow_generated"
    state["sow_generated"] = True
    
    return state


async def qa_review_node(state: ProposalWorkflowState) -> ProposalWorkflowState:
    """
    Node: QA review of generated proposal.
    """
    logger.info("QA reviewing proposal")
    
    a6 = create_a6_agent()
    
    # Find the SoW artifact
    sow_content = ""
    for artifact in state.get("artifacts", []):
        if artifact["type"] == "sow":
            sow_content = artifact["content"]
            break
    
    if sow_content:
        state["deliverable_content"] = sow_content
        state["deliverable_type"] = DeliverableType.SOW
        state["current_task"] = "qa_review"
        state = await a6.run(state)
    
    state["workflow_stage"] = "qa_complete"
    
    return state


async def human_pricing_review(state: ProposalWorkflowState) -> ProposalWorkflowState:
    """
    Node: Human review of pricing.
    """
    logger.info("Awaiting pricing review")
    
    state["human_approval_needed"] = True
    state["human_approval_request"] = {
        "artifact_type": "proposal_pricing",
        "artifact_id": state.get("engagement_id", "unknown"),
        "description": f"Review pricing for {state.get('client_name')} proposal",
        "options": ["approve", "adjust", "reject"],
    }
    state["workflow_stage"] = "pending_pricing_review"
    
    return state


async def process_pricing_review(state: ProposalWorkflowState) -> ProposalWorkflowState:
    """
    Node: Process pricing review decision.
    """
    logger.info("Processing pricing review")
    
    response = state.get("human_response", "")
    
    if response == "approve":
        state["pricing_approved"] = True
        state["workflow_stage"] = "pricing_approved"
    elif response == "adjust":
        state["pricing_approved"] = False
        state["workflow_stage"] = "pricing_adjustment_needed"
    else:
        state["status"] = AgentStatus.FAILED
        state["workflow_stage"] = "rejected"
    
    state["human_approval_needed"] = False
    state["human_response"] = None
    
    return state


async def finalize_proposal(state: ProposalWorkflowState) -> ProposalWorkflowState:
    """
    Node: Finalize proposal package.
    """
    logger.info("Finalizing proposal")
    
    client_name = state.get("client_name", "Client")
    
    a6 = create_a6_agent()
    
    # Create proposal cover letter / email
    prompt = f"""Create a professional cover email to accompany the proposal for {client_name}.

Proposal Context:
- Client: {client_name}
- One-pager and SoW generated

Create a brief, professional email that:
1. Thanks them for the opportunity
2. Summarizes what's attached
3. Highlights key points
4. Sets clear next steps
5. Offers to discuss

Keep it concise - 3-4 short paragraphs max.
"""
    
    cover_letter = await a6.think(prompt)
    
    state = a6.add_artifact(
        state,
        "cover_letter",
        f"CoverLetter_{client_name}",
        cover_letter
    )
    
    state["workflow_stage"] = "finalized"
    state["status"] = AgentStatus.COMPLETED
    
    # Log completion
    state = a6.add_decision(
        state,
        "proposal_complete",
        f"Proposal package completed for {client_name}",
        f"Artifacts: {[a['type'] for a in state.get('artifacts', [])]}"
    )
    
    return state


# =============================================================================
# Routing Functions
# =============================================================================

def route_after_qa(
    state: ProposalWorkflowState,
) -> Literal["human_pricing_review", "generate_sow"]:
    """Route based on QA result."""
    if state.get("qa_passed", True):  # Default to True if not set
        return "human_pricing_review"
    return "generate_sow"  # Loop back for revision


def route_after_pricing(
    state: ProposalWorkflowState,
) -> Literal["finalize_proposal", "estimate_effort", "end"]:
    """Route based on pricing review."""
    if state.get("pricing_approved"):
        return "finalize_proposal"
    elif state.get("workflow_stage") == "pricing_adjustment_needed":
        return "estimate_effort"  # Re-estimate
    return "end"


# =============================================================================
# Workflow Builder
# =============================================================================

def create_proposal_workflow() -> StateGraph:
    """
    Create the proposal generation workflow graph.
    
    Flow:
    validate → estimate_effort → generate_one_pager → generate_sow →
    qa_review → [passed] → human_pricing_review → 
    [approved] → finalize → END
    [adjust] → estimate_effort (loop)
    [reject] → END
    """
    
    workflow = StateGraph(ProposalWorkflowState)
    
    # Add nodes
    workflow.add_node("validate", validate_input)
    workflow.add_node("estimate_effort", estimate_effort_node)
    workflow.add_node("generate_one_pager", generate_one_pager_node)
    workflow.add_node("generate_sow", generate_sow_node)
    workflow.add_node("qa_review", qa_review_node)
    workflow.add_node("human_pricing_review", human_pricing_review)
    workflow.add_node("process_pricing", process_pricing_review)
    workflow.add_node("finalize_proposal", finalize_proposal)
    
    # Define edges
    workflow.add_edge("validate", "estimate_effort")
    workflow.add_edge("estimate_effort", "generate_one_pager")
    workflow.add_edge("generate_one_pager", "generate_sow")
    workflow.add_edge("generate_sow", "qa_review")
    
    # After QA
    workflow.add_conditional_edges(
        "qa_review",
        route_after_qa,
        {
            "human_pricing_review": "human_pricing_review",
            "generate_sow": "generate_sow",
        }
    )
    
    # Human review
    workflow.add_edge("human_pricing_review", "process_pricing")
    
    # After pricing review
    workflow.add_conditional_edges(
        "process_pricing",
        route_after_pricing,
        {
            "finalize_proposal": "finalize_proposal",
            "estimate_effort": "estimate_effort",
            "end": END,
        }
    )
    
    workflow.add_edge("finalize_proposal", END)
    
    # Entry point
    workflow.set_entry_point("validate")
    
    return workflow


# =============================================================================
# Workflow Execution
# =============================================================================

async def run_proposal_generation(
    opportunity_brief: dict[str, Any],
    client_name: str | None = None,
    engagement_id: str | None = None,
    thread_id: str | None = None,
) -> ProposalWorkflowState:
    """
    Execute the proposal generation workflow.
    
    Args:
        opportunity_brief: Opportunity brief from A1
        client_name: Client name (optional, extracted from brief if not provided)
        engagement_id: Engagement ID (optional, generated if not provided)
        thread_id: Thread ID for checkpointing
        
    Returns:
        Final workflow state with all proposal artifacts
    """
    from datetime import datetime
    
    orchestrator = get_orchestrator()
    
    # Create and register workflow
    workflow = create_proposal_workflow()
    orchestrator._workflows["proposal_generation"] = workflow
    
    # Extract client name if not provided
    if not client_name:
        client_name = opportunity_brief.get("company_name") or \
                     opportunity_brief.get("client_name") or \
                     "Client"
    
    # Generate engagement ID if not provided
    if not engagement_id:
        engagement_id = f"PROP-{client_name[:4].upper()}-{datetime.now().strftime('%Y%m%d')}"
    
    # Initial state
    initial_state: ProposalWorkflowState = {
        "workflow_id": "proposal_generation",
        "agent_id": "a6",
        "client_name": client_name,
        "engagement_id": engagement_id,
        "opportunity_brief": opportunity_brief,
        "messages": [],
        "artifacts": [],
        "decisions": [],
        "errors": [],
        "status": AgentStatus.IDLE,
        "one_pager_generated": False,
        "sow_generated": False,
        "estimate_generated": False,
        "pricing_approved": False,
        "content_approved": False,
    }
    
    # Run workflow
    result = await orchestrator.run_workflow(
        "proposal_generation",
        initial_state,
        thread_id=thread_id or engagement_id,
    )
    
    return result


async def resume_proposal_workflow(
    engagement_id: str,
    human_response: str,
) -> ProposalWorkflowState:
    """
    Resume proposal workflow after human review.
    
    Args:
        engagement_id: Engagement ID (thread ID)
        human_response: Human decision
        
    Returns:
        Updated workflow state
    """
    orchestrator = get_orchestrator()
    
    if "proposal_generation" not in orchestrator._workflows:
        workflow = create_proposal_workflow()
        orchestrator._workflows["proposal_generation"] = workflow
    
    result = await orchestrator.resume_workflow(
        "proposal_generation",
        thread_id=engagement_id,
        human_response=human_response,
    )
    
    return result


# =============================================================================
# CLI Entry Point
# =============================================================================

if __name__ == "__main__":
    import asyncio
    
    async def main():
        # Example usage
        opportunity = {
            "company_name": "Acme Corp",
            "problem_statement": "Need to migrate from Server to Cloud",
            "proposed_workpackages": ["wp1"],
            "urgency": "high",
            "estimated_value": "€15,000 - €25,000",
        }
        
        result = await run_proposal_generation(opportunity)
        
        print(f"Status: {result.get('status')}")
        print(f"Stage: {result.get('workflow_stage')}")
        print(f"Artifacts: {[a['type'] for a in result.get('artifacts', [])]}")
        
        if result.get("human_approval_needed"):
            print("\n⚠️  Awaiting pricing approval")
    
    asyncio.run(main())
