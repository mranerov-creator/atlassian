"""
BlueVektor Agents - API
FastAPI endpoints for agent interaction.
"""
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from core.config import get_settings
from core.memory import get_memory_manager
from core.orchestrator import agent_registry, get_orchestrator


# =============================================================================
# Lifespan
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    settings = get_settings()
    memory = get_memory_manager()
    await memory.init_db()
    
    # Import agents to register them
    from agents.a1_gtm import create_a1_agent
    from agents.a3_assessment import create_a3_agent
    from agents.a4_governance import create_a4_agent
    from agents.a6_delivery import create_a6_agent
    create_a1_agent()
    create_a3_agent()
    create_a4_agent()
    create_a6_agent()
    
    yield
    
    # Shutdown
    await memory.close()


# =============================================================================
# App
# =============================================================================

settings = get_settings()

app = FastAPI(
    title="BlueVektor Agents API",
    description="AI-native workforce for Atlassian Cloud consulting",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Schemas
# =============================================================================

class AgentTaskRequest(BaseModel):
    task: str
    input_data: dict[str, Any] = {}


class WorkflowRunRequest(BaseModel):
    input_data: dict[str, Any]
    thread_id: str | None = None


class WorkflowResumeRequest(BaseModel):
    thread_id: str
    human_response: str | None = None


# =============================================================================
# Endpoints
# =============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "0.1.0"}


@app.get("/agents")
async def list_agents():
    """List all registered agents."""
    agents = agent_registry.list_agents()
    return {
        "agents": [
            {
                "id": a.id,
                "name": a.name,
                "description": a.description,
                "allowed_handoffs": a.allowed_handoffs,
            }
            for a in agents
        ]
    }


@app.get("/agents/{agent_id}")
async def get_agent(agent_id: str):
    """Get agent details."""
    agent = agent_registry.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    
    return {
        "id": agent.id,
        "name": agent.name,
        "description": agent.description,
        "allowed_handoffs": agent.allowed_handoffs,
        "requires_human_approval": agent.requires_human_approval,
    }


@app.post("/agents/{agent_id}/run")
async def run_agent_task(agent_id: str, request: AgentTaskRequest):
    """Run a task with a specific agent."""
    agent_def = agent_registry.get(agent_id)
    if not agent_def:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    
    from core.orchestrator import AgentStatus
    
    # Import and instantiate agent
    if agent_id == "a1":
        from agents.a1_gtm import create_a1_agent, A1State
        
        agent = create_a1_agent()
        state: A1State = {
            "agent_id": agent_id,
            "workflow_id": f"{agent_id}_{request.task}",
            "input_data": request.input_data,
            "current_task": request.task,
            "messages": [],
            "artifacts": [],
            "decisions": [],
            "status": AgentStatus.RUNNING,
        }
        
        result = await agent.run(state)
        
        return {
            "status": result.get("status"),
            "artifacts": result.get("artifacts", []),
            "decisions": result.get("decisions", []),
            "output_data": result.get("output_data"),
            "human_approval_needed": result.get("human_approval_needed", False),
        }
    
    elif agent_id == "a3":
        from agents.a3_assessment import create_a3_agent, A3State
        
        agent = create_a3_agent()
        state: A3State = {
            "agent_id": agent_id,
            "workflow_id": f"{agent_id}_{request.task}",
            "client_name": request.input_data.get("client_name", "Client"),
            "input_data": request.input_data,
            "current_task": request.task,
            "messages": [],
            "artifacts": [],
            "decisions": [],
            "status": AgentStatus.RUNNING,
            "evidence_collected": False,
            "analysis_complete": False,
            "plan_generated": False,
            "report_drafted": False,
        }
        
        result = await agent.run(state)
        
        return {
            "status": result.get("status"),
            "artifacts": result.get("artifacts", []),
            "decisions": result.get("decisions", []),
            "output_data": result.get("output_data"),
            "human_approval_needed": result.get("human_approval_needed", False),
            "workflow_stage": result.get("workflow_stage"),
        }
    
    elif agent_id == "a4":
        from agents.a4_governance import create_a4_agent, A4State
        
        agent = create_a4_agent()
        state: A4State = {
            "agent_id": agent_id,
            "workflow_id": f"{agent_id}_{request.task}",
            "client_name": request.input_data.get("client_name", "Client"),
            "wp1_findings": request.input_data.get("wp1_findings", {}),
            "input_data": request.input_data,
            "current_task": request.task,
            "messages": [],
            "artifacts": [],
            "decisions": [],
            "status": AgentStatus.RUNNING,
            "operating_model_complete": False,
            "policies_complete": False,
            "standards_complete": False,
            "kpis_complete": False,
            "runbooks_complete": False,
            "handbook_drafted": False,
        }
        
        result = await agent.run(state)
        
        return {
            "status": result.get("status"),
            "artifacts": result.get("artifacts", []),
            "decisions": result.get("decisions", []),
            "output_data": result.get("output_data"),
            "human_approval_needed": result.get("human_approval_needed", False),
            "workflow_stage": result.get("workflow_stage"),
        }
    
    elif agent_id == "a6":
        from agents.a6_delivery import create_a6_agent, A6State
        
        agent = create_a6_agent()
        state: A6State = {
            "agent_id": agent_id,
            "workflow_id": f"{agent_id}_{request.task}",
            "client_name": request.input_data.get("client_name", "Client"),
            "opportunity_brief": request.input_data.get("opportunity_brief", {}),
            "deliverable_content": request.input_data.get("deliverable_content", ""),
            "input_data": request.input_data,
            "current_task": request.task,
            "messages": [],
            "artifacts": [],
            "decisions": [],
            "status": AgentStatus.RUNNING,
        }
        
        result = await agent.run(state)
        
        return {
            "status": result.get("status"),
            "artifacts": result.get("artifacts", []),
            "decisions": result.get("decisions", []),
            "output_data": result.get("output_data"),
            "qa_passed": result.get("qa_passed"),
            "human_approval_needed": result.get("human_approval_needed", False),
        }
    
    raise HTTPException(status_code=501, detail=f"Agent {agent_id} not implemented")


@app.post("/workflows/{workflow_id}/run")
async def run_workflow(workflow_id: str, request: WorkflowRunRequest):
    """Execute a workflow."""
    if workflow_id == "lead_qualification":
        from workflows.lead_qualification import run_lead_qualification
        
        result = await run_lead_qualification(
            request.input_data,
            thread_id=request.thread_id,
        )
        
        return {
            "status": result.get("status"),
            "stage": result.get("workflow_stage"),
            "qualified": result.get("is_qualified"),
            "score": result.get("qualification_score"),
            "action": result.get("recommended_action"),
            "artifacts": result.get("artifacts", []),
            "human_approval_needed": result.get("human_approval_needed", False),
        }
    
    elif workflow_id == "wp1_diagnostic":
        from workflows.wp1_diagnostic import run_wp1_diagnostic
        
        result = await run_wp1_diagnostic(
            client_name=request.input_data.get("client_name", "Client"),
            engagement_id=request.input_data.get("engagement_id", "WP1-001"),
            input_data=request.input_data,
            thread_id=request.thread_id,
        )
        
        return {
            "status": result.get("status"),
            "stage": result.get("workflow_stage"),
            "stages_completed": result.get("stages_completed", []),
            "deliverables": result.get("deliverables", {}),
            "artifacts": result.get("artifacts", []),
            "human_approval_needed": result.get("human_approval_needed", False),
        }
    
    elif workflow_id == "wp4_governance":
        from workflows.wp4_governance import run_wp4_governance
        
        result = await run_wp4_governance(
            client_name=request.input_data.get("client_name", "Client"),
            engagement_id=request.input_data.get("engagement_id", "WP4-001"),
            wp1_findings=request.input_data.get("wp1_findings"),
            architecture_target=request.input_data.get("architecture_target"),
            thread_id=request.thread_id,
        )
        
        return {
            "status": result.get("status"),
            "stage": result.get("workflow_stage"),
            "stages_completed": result.get("stages_completed", []),
            "deliverables": result.get("deliverables", {}),
            "artifacts": result.get("artifacts", []),
            "human_approval_needed": result.get("human_approval_needed", False),
        }
    
    elif workflow_id == "proposal_generation":
        from workflows.proposal_generation import run_proposal_generation
        
        result = await run_proposal_generation(
            opportunity_brief=request.input_data.get("opportunity_brief", {}),
            client_name=request.input_data.get("client_name"),
            engagement_id=request.input_data.get("engagement_id"),
            thread_id=request.thread_id,
        )
        
        return {
            "status": result.get("status"),
            "stage": result.get("workflow_stage"),
            "artifacts": result.get("artifacts", []),
            "one_pager_generated": result.get("one_pager_generated", False),
            "sow_generated": result.get("sow_generated", False),
            "pricing_approved": result.get("pricing_approved", False),
            "human_approval_needed": result.get("human_approval_needed", False),
        }
    
    raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found")


@app.post("/workflows/{workflow_id}/resume")
async def resume_workflow(workflow_id: str, request: WorkflowResumeRequest):
    """Resume a paused workflow."""
    orchestrator = get_orchestrator()
    
    try:
        result = await orchestrator.resume_workflow(
            workflow_id,
            request.thread_id,
            request.human_response,
        )
        
        return {
            "status": result.get("status"),
            "stage": result.get("workflow_stage"),
            "artifacts": result.get("artifacts", []),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
    )
