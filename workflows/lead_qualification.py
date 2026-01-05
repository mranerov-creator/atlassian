"""
BlueVektor Agents - Lead Qualification Workflow
End-to-end workflow from lead intake to proposal readiness.
"""
from typing import Any, Literal

import structlog
from langgraph.graph import END, StateGraph

from agents.a1_gtm import A1GTMAgent, A1State, create_a1_agent
from core.orchestrator import (
    AgentStatus,
    create_handoff_node,
    create_human_approval_node,
    get_orchestrator,
    should_continue,
)

logger = structlog.get_logger()


# =============================================================================
# Workflow State
# =============================================================================

class LeadQualificationState(A1State, total=False):
    """State for lead qualification workflow."""
    
    # Workflow tracking
    workflow_stage: str
    
    # Input
    lead_source: str
    lead_data: dict[str, Any]
    
    # Processing
    enriched_data: dict[str, Any]
    trigger_analysis: dict[str, Any]
    
    # Output
    is_qualified: bool
    qualification_score: int
    recommended_action: str


# =============================================================================
# Workflow Nodes
# =============================================================================

async def intake_lead(state: LeadQualificationState) -> LeadQualificationState:
    """
    Node: Intake and validate lead data.
    """
    logger.info("Intake lead", source=state.get("lead_source"))
    
    lead_data = state.get("lead_data", {})
    
    # Basic validation
    required_fields = ["company_name", "contact_email"]
    missing = [f for f in required_fields if f not in lead_data]
    
    if missing:
        state["errors"] = state.get("errors", []) + [f"Missing fields: {missing}"]
        state["status"] = AgentStatus.FAILED
        return state
    
    state["workflow_stage"] = "intake_complete"
    state["status"] = AgentStatus.RUNNING
    
    return state


async def enrich_lead(state: LeadQualificationState) -> LeadQualificationState:
    """
    Node: Enrich lead with additional data.
    Uses A1 agent to analyze and enrich.
    """
    logger.info("Enriching lead")
    
    a1 = create_a1_agent()
    lead_data = state.get("lead_data", {})
    
    # Analyze company and detect triggers
    prompt = f"""Analyze this lead and provide enrichment:

Lead Data:
{lead_data}

Provide:
1. Company type classification (partner/provider/enterprise)
2. Estimated company size
3. Likely Atlassian products in use
4. Detected trigger events
5. ICP fit score (0-100)
6. Initial priority (high/medium/low)
7. Recommended engagement model
"""
    
    enrichment = await a1.think(prompt)
    
    state["enriched_data"] = {"analysis": enrichment}
    state["workflow_stage"] = "enriched"
    
    return state


async def analyze_triggers(state: LeadQualificationState) -> LeadQualificationState:
    """
    Node: Deep analysis of trigger events.
    """
    logger.info("Analyzing triggers")
    
    a1 = create_a1_agent()
    lead_data = state.get("lead_data", {})
    enriched = state.get("enriched_data", {})
    
    prompt = f"""Perform deep trigger event analysis:

Lead: {lead_data}
Initial Enrichment: {enriched}

Analyze:
1. Which trigger events are present?
2. What's the likely urgency level?
3. What pain points can we address?
4. What's the potential scope (WP1 only? WP1+WP4? Full migration?)
5. Who are likely stakeholders?
6. What objections might we face?

Be specific and actionable.
"""
    
    analysis = await a1.think(prompt)
    
    state["trigger_analysis"] = {"analysis": analysis}
    state["workflow_stage"] = "triggers_analyzed"
    
    return state


async def qualify_lead(state: LeadQualificationState) -> LeadQualificationState:
    """
    Node: Qualify lead using BANT/CHAMP.
    """
    logger.info("Qualifying lead")
    
    a1 = create_a1_agent()
    
    # Combine all data
    context = {
        "lead_data": state.get("lead_data"),
        "enriched_data": state.get("enriched_data"),
        "trigger_analysis": state.get("trigger_analysis"),
    }
    
    state["input_data"] = context
    state["current_task"] = "qualify_opportunity"
    
    # Run A1 qualification
    state = await a1.run(state)
    
    # Parse qualification result (simplified)
    output = state.get("output_data", {})
    qualification = output.get("qualification", "")
    
    # Determine if qualified (would parse from structured output in production)
    is_qualified = "qualified: yes" in qualification.lower() or "score" in qualification.lower()
    score = 65 if is_qualified else 35  # Placeholder
    
    state["is_qualified"] = is_qualified
    state["qualification_score"] = score
    state["workflow_stage"] = "qualified"
    
    return state


async def determine_action(state: LeadQualificationState) -> LeadQualificationState:
    """
    Node: Determine next action based on qualification.
    """
    logger.info("Determining action")
    
    is_qualified = state.get("is_qualified", False)
    score = state.get("qualification_score", 0)
    
    if is_qualified and score >= 70:
        state["recommended_action"] = "schedule_discovery"
        state["workflow_stage"] = "ready_for_discovery"
    elif is_qualified and score >= 50:
        state["recommended_action"] = "nurture_sequence"
        state["workflow_stage"] = "nurture"
    else:
        state["recommended_action"] = "archive"
        state["workflow_stage"] = "archived"
    
    # Add decision log
    a1 = create_a1_agent()
    state = a1.add_decision(
        state,
        "lead_routing",
        f"Lead routed to: {state['recommended_action']}",
        f"Score: {score}, Qualified: {is_qualified}"
    )
    
    return state


async def prepare_outreach(state: LeadQualificationState) -> LeadQualificationState:
    """
    Node: Prepare outreach sequence for qualified leads.
    """
    logger.info("Preparing outreach")
    
    a1 = create_a1_agent()
    
    lead_data = state.get("lead_data", {})
    enriched = state.get("enriched_data", {})
    
    from agents.a1_gtm import Target, EngagementModel
    
    target = Target(
        company_name=lead_data.get("company_name", "Unknown"),
        company_type=enriched.get("company_type", "enterprise"),
        trigger_events=[],
    )
    
    state["targets"] = [target]
    state["current_task"] = "generate_outreach"
    
    state = await a1.run(state)
    state["workflow_stage"] = "outreach_ready"
    
    return state


async def human_review_node(state: LeadQualificationState) -> LeadQualificationState:
    """
    Node: Pause for human review of qualified lead.
    """
    logger.info("Awaiting human review")
    
    state["human_approval_needed"] = True
    state["human_approval_request"] = {
        "artifact_type": "lead_qualification",
        "artifact_id": state.get("lead_data", {}).get("company_name", "unknown"),
        "description": f"Review qualified lead: {state.get('lead_data', {}).get('company_name')}",
        "options": ["approve_discovery", "nurture", "reject"],
    }
    
    return state


# =============================================================================
# Routing Functions
# =============================================================================

def route_after_qualification(
    state: LeadQualificationState,
) -> Literal["determine_action", "archive"]:
    """Route based on qualification result."""
    if state.get("is_qualified"):
        return "determine_action"
    return "archive"


def route_after_action(
    state: LeadQualificationState,
) -> Literal["prepare_outreach", "human_review", "end"]:
    """Route based on recommended action."""
    action = state.get("recommended_action", "")
    
    if action == "schedule_discovery":
        return "human_review"
    elif action == "nurture_sequence":
        return "prepare_outreach"
    else:
        return "end"


def route_after_human(
    state: LeadQualificationState,
) -> Literal["prepare_outreach", "end"]:
    """Route based on human decision."""
    response = state.get("human_response", "")
    
    if response == "approve_discovery":
        return "prepare_outreach"
    return "end"


# =============================================================================
# Workflow Builder
# =============================================================================

def create_lead_qualification_workflow() -> StateGraph:
    """
    Create the lead qualification workflow graph.
    
    Flow:
    intake → enrich → analyze_triggers → qualify → 
    [if qualified] → determine_action → [based on score] →
    [high] → human_review → [approved] → prepare_outreach → END
    [medium] → prepare_outreach → END
    [low] → END
    """
    
    workflow = StateGraph(LeadQualificationState)
    
    # Add nodes
    workflow.add_node("intake", intake_lead)
    workflow.add_node("enrich", enrich_lead)
    workflow.add_node("analyze_triggers", analyze_triggers)
    workflow.add_node("qualify", qualify_lead)
    workflow.add_node("determine_action", determine_action)
    workflow.add_node("prepare_outreach", prepare_outreach)
    workflow.add_node("human_review", human_review_node)
    workflow.add_node("archive", lambda s: {**s, "status": AgentStatus.COMPLETED})
    
    # Define edges
    workflow.add_edge("intake", "enrich")
    workflow.add_edge("enrich", "analyze_triggers")
    workflow.add_edge("analyze_triggers", "qualify")
    
    # Conditional after qualification
    workflow.add_conditional_edges(
        "qualify",
        route_after_qualification,
        {
            "determine_action": "determine_action",
            "archive": "archive",
        }
    )
    
    # Conditional after action determination
    workflow.add_conditional_edges(
        "determine_action",
        route_after_action,
        {
            "human_review": "human_review",
            "prepare_outreach": "prepare_outreach",
            "end": END,
        }
    )
    
    # Conditional after human review
    workflow.add_conditional_edges(
        "human_review",
        route_after_human,
        {
            "prepare_outreach": "prepare_outreach",
            "end": END,
        }
    )
    
    # Terminal edges
    workflow.add_edge("prepare_outreach", END)
    workflow.add_edge("archive", END)
    
    # Set entry point
    workflow.set_entry_point("intake")
    
    return workflow


# =============================================================================
# Workflow Execution
# =============================================================================

async def run_lead_qualification(
    lead_data: dict[str, Any],
    lead_source: str = "manual",
    thread_id: str | None = None,
) -> LeadQualificationState:
    """
    Execute the lead qualification workflow.
    
    Args:
        lead_data: Lead information (company_name, contact_email, etc.)
        lead_source: Source of the lead
        thread_id: Optional thread ID for resumption
        
    Returns:
        Final workflow state
    """
    orchestrator = get_orchestrator()
    
    # Create and register workflow
    workflow = create_lead_qualification_workflow()
    orchestrator._workflows["lead_qualification"] = workflow
    
    # Initial state
    initial_state: LeadQualificationState = {
        "workflow_id": "lead_qualification",
        "lead_source": lead_source,
        "lead_data": lead_data,
        "messages": [],
        "artifacts": [],
        "decisions": [],
        "errors": [],
        "status": AgentStatus.IDLE,
    }
    
    # Run workflow
    result = await orchestrator.run_workflow(
        "lead_qualification",
        initial_state,
        thread_id=thread_id,
    )
    
    return result


# =============================================================================
# CLI Integration
# =============================================================================

if __name__ == "__main__":
    import asyncio
    
    # Example usage
    test_lead = {
        "company_name": "Acme Corp",
        "contact_email": "john@acme.com",
        "contact_name": "John Smith",
        "contact_title": "IT Director",
        "notes": "Interested in Atlassian Cloud migration, currently on Server",
    }
    
    async def main():
        result = await run_lead_qualification(test_lead)
        print(f"Result: {result.get('recommended_action')}")
        print(f"Score: {result.get('qualification_score')}")
        print(f"Stage: {result.get('workflow_stage')}")
    
    asyncio.run(main())
