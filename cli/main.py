"""
BlueVektor Agents - Command Line Interface
Main entry point for interacting with agents.
"""
import asyncio
import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

app = typer.Typer(
    name="bv",
    help="BlueVektor AI Agents CLI",
    add_completion=False,
)

console = Console()


# =============================================================================
# Agent Commands
# =============================================================================

@app.command()
def agents():
    """List all registered agents."""
    from core.orchestrator import agent_registry
    
    table = Table(title="BlueVektor Agents")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Description")
    table.add_column("Handoffs", style="yellow")
    
    for agent in agent_registry.list_agents():
        table.add_row(
            agent.id,
            agent.name,
            agent.description[:50] + "..." if len(agent.description) > 50 else agent.description,
            ", ".join(agent.allowed_handoffs) or "-"
        )
    
    console.print(table)


@app.command()
def init():
    """Initialize the database and services."""
    async def _init():
        from core.memory import get_memory_manager
        
        console.print("[yellow]Initializing database...[/yellow]")
        memory = get_memory_manager()
        await memory.init_db()
        console.print("[green]✓ Database initialized[/green]")
    
    asyncio.run(_init())


# =============================================================================
# A1 GTM Commands
# =============================================================================

a1_app = typer.Typer(help="A1 GTM & Partnerships agent commands")
app.add_typer(a1_app, name="a1")


@a1_app.command("qualify")
def a1_qualify(
    company: str = typer.Option(..., "--company", "-c", help="Company name"),
    email: str = typer.Option(..., "--email", "-e", help="Contact email"),
    notes: Optional[str] = typer.Option(None, "--notes", "-n", help="Additional notes"),
):
    """Qualify a lead using A1 agent."""
    async def _qualify():
        from workflows.lead_qualification import run_lead_qualification
        
        lead_data = {
            "company_name": company,
            "contact_email": email,
            "notes": notes or "",
        }
        
        console.print(Panel(f"Qualifying lead: [cyan]{company}[/cyan]"))
        
        with console.status("[yellow]Running qualification workflow...[/yellow]"):
            result = await run_lead_qualification(lead_data)
        
        # Display results
        console.print("\n[bold]Results:[/bold]")
        console.print(f"  Status: [{'green' if result.get('is_qualified') else 'red'}]{result.get('workflow_stage')}[/]")
        console.print(f"  Qualified: {result.get('is_qualified')}")
        console.print(f"  Score: {result.get('qualification_score')}")
        console.print(f"  Action: [cyan]{result.get('recommended_action')}[/cyan]")
        
        if result.get("artifacts"):
            console.print("\n[bold]Artifacts generated:[/bold]")
            for artifact in result["artifacts"]:
                console.print(f"  - {artifact['type']}: {artifact['name']}")
        
        if result.get("decisions"):
            console.print("\n[bold]Decisions logged:[/bold]")
            for decision in result["decisions"]:
                console.print(f"  - {decision['type']}: {decision['description']}")
    
    asyncio.run(_qualify())


@a1_app.command("outreach")
def a1_outreach(
    company: str = typer.Option(..., "--company", "-c", help="Company name"),
    company_type: str = typer.Option("enterprise", "--type", "-t", help="partner/provider/enterprise"),
    language: str = typer.Option("en", "--lang", "-l", help="Language (en/es)"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file"),
):
    """Generate outreach sequence for a target."""
    async def _outreach():
        from agents.a1_gtm import create_a1_agent, Target, A1State
        from core.orchestrator import AgentStatus
        
        a1 = create_a1_agent()
        
        target = Target(
            company_name=company,
            company_type=company_type,
        )
        
        state: A1State = {
            "agent_id": "a1",
            "workflow_id": "outreach_generation",
            "targets": [target],
            "current_task": "generate_outreach",
            "messages": [],
            "artifacts": [],
            "decisions": [],
            "status": AgentStatus.RUNNING,
        }
        
        console.print(Panel(f"Generating outreach for: [cyan]{company}[/cyan]"))
        
        with console.status("[yellow]Generating sequences...[/yellow]"):
            result = await a1.run(state)
        
        # Display results
        if result.get("artifacts"):
            for artifact in result["artifacts"]:
                console.print(f"\n[bold]{artifact['name']}[/bold]")
                console.print(artifact["content"])
                
                if output:
                    output.write_text(artifact["content"])
                    console.print(f"\n[green]Saved to {output}[/green]")
    
    asyncio.run(_outreach())


@a1_app.command("discovery")
def a1_discovery(
    company: str = typer.Option(..., "--company", "-c", help="Company name"),
    context: Optional[str] = typer.Option(None, "--context", help="Additional context"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file"),
):
    """Prepare discovery call agenda."""
    async def _discovery():
        from agents.a1_gtm import create_a1_agent, A1State
        from core.orchestrator import AgentStatus
        
        a1 = create_a1_agent()
        
        state: A1State = {
            "agent_id": "a1",
            "workflow_id": "discovery_prep",
            "input_data": {
                "company_name": company,
                "context": context or "",
            },
            "current_task": "prepare_discovery",
            "messages": [],
            "artifacts": [],
            "decisions": [],
            "status": AgentStatus.RUNNING,
        }
        
        console.print(Panel(f"Preparing discovery call for: [cyan]{company}[/cyan]"))
        
        with console.status("[yellow]Generating agenda...[/yellow]"):
            result = await a1.run(state)
        
        if result.get("artifacts"):
            for artifact in result["artifacts"]:
                console.print(f"\n[bold]{artifact['name']}[/bold]")
                console.print(artifact["content"])
                
                if output:
                    output.write_text(artifact["content"])
                    console.print(f"\n[green]Saved to {output}[/green]")
    
    asyncio.run(_discovery())


@a1_app.command("brief")
def a1_brief(
    notes_file: Path = typer.Argument(..., help="Path to discovery call notes file"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file"),
):
    """Create opportunity brief from discovery notes."""
    async def _brief():
        from agents.a1_gtm import create_a1_agent, A1State
        from core.orchestrator import AgentStatus
        
        if not notes_file.exists():
            console.print(f"[red]File not found: {notes_file}[/red]")
            raise typer.Exit(1)
        
        notes = notes_file.read_text()
        
        a1 = create_a1_agent()
        
        state: A1State = {
            "agent_id": "a1",
            "workflow_id": "opportunity_brief",
            "call_notes": notes,
            "current_task": "create_opportunity_brief",
            "messages": [],
            "artifacts": [],
            "decisions": [],
            "status": AgentStatus.RUNNING,
        }
        
        console.print(Panel("Creating Opportunity Brief"))
        
        with console.status("[yellow]Analyzing notes and generating brief...[/yellow]"):
            result = await a1.run(state)
        
        if result.get("artifacts"):
            for artifact in result["artifacts"]:
                if artifact["type"] == "opportunity_brief":
                    console.print(f"\n[bold green]Opportunity Brief Generated[/bold green]")
                    console.print(artifact["content"])
                    
                    if output:
                        output.write_text(artifact["content"])
                        console.print(f"\n[green]Saved to {output}[/green]")
        
        if result.get("human_approval_needed"):
            console.print("\n[yellow]⚠ This brief requires human approval before proceeding[/yellow]")
        
        if result.get("handoff_requests"):
            console.print("\n[cyan]Handoff requested to A6 for proposal preparation[/cyan]")
    
    asyncio.run(_brief())


# =============================================================================
# A3 Assessment Commands
# =============================================================================

a3_app = typer.Typer(help="A3 Assessment Analyst agent commands")
app.add_typer(a3_app, name="a3")


@a3_app.command("wp1")
def a3_wp1(
    client: str = typer.Option(..., "--client", "-c", help="Client name"),
    engagement_id: str = typer.Option(None, "--engagement", "-e", help="Engagement ID"),
    instance_url: str = typer.Option(None, "--url", "-u", help="Atlassian instance URL"),
    output_dir: Optional[Path] = typer.Option(None, "--output", "-o", help="Output directory"),
):
    """Execute full WP1 Diagnostic workflow."""
    async def _wp1():
        from workflows.wp1_diagnostic import run_wp1_diagnostic
        from datetime import datetime
        
        eng_id = engagement_id or f"WP1-{client.upper()[:4]}-{datetime.now().strftime('%Y%m%d')}"
        
        input_data = {}
        if instance_url:
            input_data["instance_url"] = instance_url
        
        console.print(Panel(
            f"[bold]WP1 Diagnostic[/bold]\n"
            f"Client: [cyan]{client}[/cyan]\n"
            f"Engagement: [cyan]{eng_id}[/cyan]",
            title="Starting WP1"
        ))
        
        with console.status("[yellow]Executing WP1 workflow...[/yellow]"):
            result = await run_wp1_diagnostic(
                client_name=client,
                engagement_id=eng_id,
                input_data=input_data,
            )
        
        # Display results
        console.print(f"\n[bold]Status:[/bold] {result.get('status')}")
        console.print(f"[bold]Stage:[/bold] {result.get('workflow_stage')}")
        console.print(f"[bold]Stages completed:[/bold] {result.get('stages_completed')}")
        
        if result.get("deliverables"):
            console.print("\n[bold]Deliverables:[/bold]")
            for name, info in result["deliverables"].items():
                status_color = "green" if info.get("status") == "complete" else "yellow"
                console.print(f"  - {name}: [{status_color}]{info.get('status')}[/]")
        
        if result.get("artifacts"):
            console.print(f"\n[bold]Artifacts generated:[/bold] {len(result['artifacts'])}")
            
            if output_dir:
                output_dir.mkdir(parents=True, exist_ok=True)
                for artifact in result["artifacts"]:
                    artifact_path = output_dir / f"{artifact['name']}.md"
                    artifact_path.write_text(artifact["content"])
                console.print(f"[green]Saved artifacts to {output_dir}[/green]")
        
        if result.get("human_approval_needed"):
            console.print("\n[yellow]⚠ Workflow paused - awaiting human review[/yellow]")
            console.print(f"Resume with: bv a3 resume --engagement {eng_id} --response approve")
    
    asyncio.run(_wp1())


@a3_app.command("evidence")
def a3_evidence(
    client: str = typer.Option(..., "--client", "-c", help="Client name"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file"),
):
    """Collect and analyze evidence for assessment."""
    async def _evidence():
        from agents.a3_assessment import create_a3_agent, A3State
        from core.orchestrator import AgentStatus
        
        a3 = create_a3_agent()
        
        state: A3State = {
            "agent_id": "a3",
            "workflow_id": "evidence_collection",
            "client_name": client,
            "current_task": "collect_evidence",
            "messages": [],
            "artifacts": [],
            "decisions": [],
            "status": AgentStatus.RUNNING,
        }
        
        console.print(Panel(f"Collecting evidence for: [cyan]{client}[/cyan]"))
        
        with console.status("[yellow]Analyzing evidence sources...[/yellow]"):
            result = await a3.run(state)
        
        if result.get("artifacts"):
            for artifact in result["artifacts"]:
                console.print(f"\n[bold]{artifact['name']}[/bold]")
                console.print(artifact["content"])
                
                if output:
                    output.write_text(artifact["content"])
                    console.print(f"\n[green]Saved to {output}[/green]")
    
    asyncio.run(_evidence())


@a3_app.command("hotspots")
def a3_hotspots(
    client: str = typer.Option(..., "--client", "-c", help="Client name"),
    evidence_file: Optional[Path] = typer.Option(None, "--evidence", "-e", help="Evidence file"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file"),
):
    """Identify and prioritize hotspots from evidence."""
    async def _hotspots():
        from agents.a3_assessment import create_a3_agent, A3State
        from core.orchestrator import AgentStatus
        
        a3 = create_a3_agent()
        
        raw_evidence = {}
        if evidence_file and evidence_file.exists():
            raw_evidence["provided_evidence"] = evidence_file.read_text()
        
        state: A3State = {
            "agent_id": "a3",
            "workflow_id": "hotspot_analysis",
            "client_name": client,
            "raw_evidence": raw_evidence,
            "current_task": "identify_hotspots",
            "messages": [],
            "artifacts": [],
            "decisions": [],
            "status": AgentStatus.RUNNING,
            "evidence_collected": True,
        }
        
        console.print(Panel(f"Identifying hotspots for: [cyan]{client}[/cyan]"))
        
        with console.status("[yellow]Analyzing and prioritizing findings...[/yellow]"):
            result = await a3.run(state)
        
        if result.get("artifacts"):
            for artifact in result["artifacts"]:
                if artifact["type"] == "hotspot_map":
                    console.print(f"\n[bold green]Hotspot Map Generated[/bold green]")
                    console.print(artifact["content"])
                    
                    if output:
                        output.write_text(artifact["content"])
                        console.print(f"\n[green]Saved to {output}[/green]")
    
    asyncio.run(_hotspots())


@a3_app.command("plan")
def a3_plan(
    client: str = typer.Option(..., "--client", "-c", help="Client name"),
    evidence_file: Optional[Path] = typer.Option(None, "--evidence", "-e", help="Evidence/analysis file"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file"),
):
    """Generate 30/60/90 day transformation plan."""
    async def _plan():
        from agents.a3_assessment import create_a3_agent, A3State
        from core.orchestrator import AgentStatus
        
        a3 = create_a3_agent()
        
        raw_evidence = {}
        if evidence_file and evidence_file.exists():
            raw_evidence["analysis"] = evidence_file.read_text()
        
        state: A3State = {
            "agent_id": "a3",
            "workflow_id": "plan_generation",
            "client_name": client,
            "raw_evidence": raw_evidence,
            "current_task": "generate_plan",
            "messages": [],
            "artifacts": [],
            "decisions": [],
            "status": AgentStatus.RUNNING,
            "evidence_collected": True,
            "analysis_complete": True,
        }
        
        console.print(Panel(f"Generating 30/60/90 plan for: [cyan]{client}[/cyan]"))
        
        with console.status("[yellow]Creating transformation plan...[/yellow]"):
            result = await a3.run(state)
        
        if result.get("artifacts"):
            for artifact in result["artifacts"]:
                if artifact["type"] == "plan_30_60_90":
                    console.print(f"\n[bold green]30/60/90 Plan Generated[/bold green]")
                    console.print(artifact["content"])
                    
                    if output:
                        output.write_text(artifact["content"])
                        console.print(f"\n[green]Saved to {output}[/green]")
    
    asyncio.run(_plan())


@a3_app.command("resume")
def a3_resume(
    engagement_id: str = typer.Option(..., "--engagement", "-e", help="Engagement ID"),
    response: str = typer.Option(..., "--response", "-r", help="Review response: approve/revise/reject"),
):
    """Resume WP1 workflow after human review."""
    async def _resume():
        from workflows.wp1_diagnostic import resume_wp1_diagnostic
        
        if response not in ["approve", "revise", "reject"]:
            console.print(f"[red]Invalid response. Use: approve, revise, or reject[/red]")
            raise typer.Exit(1)
        
        console.print(Panel(f"Resuming WP1: [cyan]{engagement_id}[/cyan] with [{response}]"))
        
        with console.status("[yellow]Resuming workflow...[/yellow]"):
            result = await resume_wp1_diagnostic(engagement_id, response)
        
        console.print(f"\n[bold]Status:[/bold] {result.get('status')}")
        console.print(f"[bold]Stage:[/bold] {result.get('workflow_stage')}")
        
        if result.get("deliverables"):
            console.print("\n[bold]Deliverables:[/bold]")
            for name, info in result["deliverables"].items():
                console.print(f"  - {name}: {info.get('status')}")
    
    asyncio.run(_resume())


# =============================================================================
# A6 Delivery PM/QA Commands
# =============================================================================

a6_app = typer.Typer(help="A6 Delivery PM/QA agent commands")
app.add_typer(a6_app, name="a6")


@a6_app.command("qa")
def a6_qa(
    file: Path = typer.Argument(..., help="Path to deliverable file to review"),
    deliverable_type: str = typer.Option("other", "--type", "-t", help="Deliverable type: sow, wp1_report, opportunity_brief, plan_30_60_90"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file for QA report"),
):
    """Perform QA review on a deliverable."""
    async def _qa():
        from agents.a6_delivery import create_a6_agent, A6State, DeliverableType
        from core.orchestrator import AgentStatus
        
        if not file.exists():
            console.print(f"[red]File not found: {file}[/red]")
            raise typer.Exit(1)
        
        content = file.read_text()
        
        # Map string to enum
        type_map = {
            "sow": DeliverableType.SOW,
            "wp1_report": DeliverableType.WP1_REPORT,
            "opportunity_brief": DeliverableType.OPPORTUNITY_BRIEF,
            "plan_30_60_90": DeliverableType.PLAN_30_60_90,
            "other": DeliverableType.OTHER,
        }
        dtype = type_map.get(deliverable_type, DeliverableType.OTHER)
        
        a6 = create_a6_agent()
        
        state: A6State = {
            "agent_id": "a6",
            "workflow_id": "qa_review",
            "deliverable_content": content,
            "deliverable_type": dtype,
            "current_task": "qa_review",
            "messages": [],
            "artifacts": [],
            "decisions": [],
            "status": AgentStatus.RUNNING,
        }
        
        console.print(Panel(f"QA Review: [cyan]{file.name}[/cyan] ({deliverable_type})"))
        
        with console.status("[yellow]Performing QA review...[/yellow]"):
            result = await a6.run(state)
        
        # Display results
        if result.get("qa_feedback"):
            console.print(f"\n[bold]QA Feedback:[/bold]")
            console.print(result["qa_feedback"])
        
        status_color = "green" if result.get("qa_passed") else "yellow"
        console.print(f"\n[bold]QA Result:[/bold] [{status_color}]{'PASSED' if result.get('qa_passed') else 'NEEDS REVISION'}[/]")
        
        if output and result.get("artifacts"):
            for artifact in result["artifacts"]:
                if artifact["type"] == "qa_review":
                    output.write_text(artifact["content"])
                    console.print(f"\n[green]QA report saved to {output}[/green]")
    
    asyncio.run(_qa())


@a6_app.command("proposal")
def a6_proposal(
    client: str = typer.Option(..., "--client", "-c", help="Client name"),
    brief_file: Optional[Path] = typer.Option(None, "--brief", "-b", help="Opportunity brief file (JSON or text)"),
    output_dir: Optional[Path] = typer.Option(None, "--output", "-o", help="Output directory for proposal files"),
):
    """Generate proposal package (one-pager + SoW) from opportunity brief."""
    async def _proposal():
        from workflows.proposal_generation import run_proposal_generation
        import json
        
        # Load brief if provided
        opportunity_brief = {"company_name": client}
        if brief_file and brief_file.exists():
            content = brief_file.read_text()
            try:
                opportunity_brief = json.loads(content)
            except json.JSONDecodeError:
                opportunity_brief["context"] = content
        
        console.print(Panel(
            f"[bold]Proposal Generation[/bold]\n"
            f"Client: [cyan]{client}[/cyan]",
            title="Starting Proposal Workflow"
        ))
        
        with console.status("[yellow]Generating proposal package...[/yellow]"):
            result = await run_proposal_generation(
                opportunity_brief=opportunity_brief,
                client_name=client,
            )
        
        # Display results
        console.print(f"\n[bold]Status:[/bold] {result.get('status')}")
        console.print(f"[bold]Stage:[/bold] {result.get('workflow_stage')}")
        
        if result.get("artifacts"):
            console.print(f"\n[bold]Artifacts generated:[/bold]")
            for artifact in result["artifacts"]:
                console.print(f"  - {artifact['type']}: {artifact['name']}")
            
            if output_dir:
                output_dir.mkdir(parents=True, exist_ok=True)
                for artifact in result["artifacts"]:
                    artifact_path = output_dir / f"{artifact['name']}.md"
                    artifact_path.write_text(artifact["content"])
                console.print(f"\n[green]Saved artifacts to {output_dir}[/green]")
        
        if result.get("human_approval_needed"):
            console.print("\n[yellow]⚠ Awaiting pricing approval[/yellow]")
            console.print(f"Resume with: bv a6 resume --engagement {result.get('engagement_id')} --response approve")
    
    asyncio.run(_proposal())


@a6_app.command("sow")
def a6_sow(
    client: str = typer.Option(..., "--client", "-c", help="Client name"),
    brief_file: Optional[Path] = typer.Option(None, "--brief", "-b", help="Opportunity brief file"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file"),
):
    """Generate Statement of Work from opportunity brief."""
    async def _sow():
        from agents.a6_delivery import create_a6_agent, A6State
        from core.orchestrator import AgentStatus
        import json
        
        opportunity_brief = {"company_name": client}
        if brief_file and brief_file.exists():
            content = brief_file.read_text()
            try:
                opportunity_brief = json.loads(content)
            except json.JSONDecodeError:
                opportunity_brief["context"] = content
        
        a6 = create_a6_agent()
        
        state: A6State = {
            "agent_id": "a6",
            "workflow_id": "sow_generation",
            "client_name": client,
            "opportunity_brief": opportunity_brief,
            "current_task": "generate_sow",
            "messages": [],
            "artifacts": [],
            "decisions": [],
            "status": AgentStatus.RUNNING,
        }
        
        console.print(Panel(f"Generating SoW for: [cyan]{client}[/cyan]"))
        
        with console.status("[yellow]Creating Statement of Work...[/yellow]"):
            result = await a6.run(state)
        
        if result.get("artifacts"):
            for artifact in result["artifacts"]:
                if artifact["type"] == "sow":
                    console.print(f"\n[bold green]SoW Generated[/bold green]")
                    console.print(artifact["content"][:2000] + "..." if len(artifact["content"]) > 2000 else artifact["content"])
                    
                    if output:
                        output.write_text(artifact["content"])
                        console.print(f"\n[green]Saved to {output}[/green]")
    
    asyncio.run(_sow())


@a6_app.command("estimate")
def a6_estimate(
    client: str = typer.Option(..., "--client", "-c", help="Client name"),
    workpackage: str = typer.Option("wp1", "--wp", "-w", help="Workpackage type: wp1, wp4, custom"),
    users: int = typer.Option(100, "--users", "-u", help="Approximate user count"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file"),
):
    """Generate effort estimate for an engagement."""
    async def _estimate():
        from agents.a6_delivery import create_a6_agent, A6State
        from core.orchestrator import AgentStatus
        
        a6 = create_a6_agent()
        
        state: A6State = {
            "agent_id": "a6",
            "workflow_id": "effort_estimate",
            "client_name": client,
            "input_data": {
                "workpackage": workpackage,
                "user_count": users,
                "client_name": client,
            },
            "current_task": "estimate_effort",
            "messages": [],
            "artifacts": [],
            "decisions": [],
            "status": AgentStatus.RUNNING,
        }
        
        console.print(Panel(f"Estimating effort for: [cyan]{client}[/cyan] ({workpackage}, ~{users} users)"))
        
        with console.status("[yellow]Calculating estimate...[/yellow]"):
            result = await a6.run(state)
        
        if result.get("output_data", {}).get("effort_estimate"):
            console.print(f"\n[bold green]Effort Estimate[/bold green]")
            console.print(result["output_data"]["effort_estimate"])
        
        if output and result.get("artifacts"):
            for artifact in result["artifacts"]:
                if artifact["type"] == "effort_estimate":
                    output.write_text(artifact["content"])
                    console.print(f"\n[green]Saved to {output}[/green]")
    
    asyncio.run(_estimate())


@a6_app.command("plan")
def a6_plan(
    client: str = typer.Option(..., "--client", "-c", help="Client name"),
    engagement_id: str = typer.Option(None, "--engagement", "-e", help="Engagement ID"),
    workpackage: str = typer.Option("wp1", "--wp", "-w", help="Workpackage type"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file"),
):
    """Create project plan for an engagement."""
    async def _plan():
        from agents.a6_delivery import create_a6_agent, A6State
        from core.orchestrator import AgentStatus
        from datetime import datetime
        
        eng_id = engagement_id or f"ENG-{client[:4].upper()}-{datetime.now().strftime('%Y%m%d')}"
        
        a6 = create_a6_agent()
        
        state: A6State = {
            "agent_id": "a6",
            "workflow_id": "project_plan",
            "client_name": client,
            "engagement_id": eng_id,
            "input_data": {
                "workpackage": workpackage,
                "client_name": client,
            },
            "current_task": "create_project_plan",
            "messages": [],
            "artifacts": [],
            "decisions": [],
            "status": AgentStatus.RUNNING,
        }
        
        console.print(Panel(f"Creating project plan: [cyan]{eng_id}[/cyan]"))
        
        with console.status("[yellow]Generating project plan...[/yellow]"):
            result = await a6.run(state)
        
        if result.get("artifacts"):
            for artifact in result["artifacts"]:
                if artifact["type"] == "project_plan":
                    console.print(f"\n[bold green]Project Plan Generated[/bold green]")
                    console.print(artifact["content"])
                    
                    if output:
                        output.write_text(artifact["content"])
                        console.print(f"\n[green]Saved to {output}[/green]")
    
    asyncio.run(_plan())


@a6_app.command("resume")
def a6_resume(
    engagement_id: str = typer.Option(..., "--engagement", "-e", help="Engagement ID"),
    response: str = typer.Option(..., "--response", "-r", help="Review response: approve/adjust/reject"),
):
    """Resume proposal workflow after pricing review."""
    async def _resume():
        from workflows.proposal_generation import resume_proposal_workflow
        
        if response not in ["approve", "adjust", "reject"]:
            console.print(f"[red]Invalid response. Use: approve, adjust, or reject[/red]")
            raise typer.Exit(1)
        
        console.print(Panel(f"Resuming proposal: [cyan]{engagement_id}[/cyan] with [{response}]"))
        
        with console.status("[yellow]Resuming workflow...[/yellow]"):
            result = await resume_proposal_workflow(engagement_id, response)
        
        console.print(f"\n[bold]Status:[/bold] {result.get('status')}")
        console.print(f"[bold]Stage:[/bold] {result.get('workflow_stage')}")
        
        if result.get("artifacts"):
            console.print(f"\n[bold]Artifacts:[/bold]")
            for artifact in result["artifacts"]:
                console.print(f"  - {artifact['type']}: {artifact['name']}")
    
    asyncio.run(_resume())


# =============================================================================
# A4 Governance Lead Commands
# =============================================================================

a4_app = typer.Typer(help="A4 Governance Lead agent commands")
app.add_typer(a4_app, name="a4")


@a4_app.command("wp4")
def a4_wp4(
    client: str = typer.Option(..., "--client", "-c", help="Client name"),
    engagement_id: str = typer.Option(None, "--engagement", "-e", help="Engagement ID"),
    wp1_file: Optional[Path] = typer.Option(None, "--wp1", help="WP1 findings file (JSON)"),
    output_dir: Optional[Path] = typer.Option(None, "--output", "-o", help="Output directory"),
):
    """Execute full WP4 Governance Office-in-a-Box workflow."""
    async def _wp4():
        from workflows.wp4_governance import run_wp4_governance
        from datetime import datetime
        import json
        
        eng_id = engagement_id or f"WP4-{client.upper()[:4]}-{datetime.now().strftime('%Y%m%d')}"
        
        wp1_findings = {}
        if wp1_file and wp1_file.exists():
            try:
                wp1_findings = json.loads(wp1_file.read_text())
            except json.JSONDecodeError:
                wp1_findings = {"context": wp1_file.read_text()}
        
        console.print(Panel(
            f"[bold]WP4 Governance Office-in-a-Box[/bold]\n"
            f"Client: [cyan]{client}[/cyan]\n"
            f"Engagement: [cyan]{eng_id}[/cyan]",
            title="Starting WP4"
        ))
        
        with console.status("[yellow]Executing WP4 workflow...[/yellow]"):
            result = await run_wp4_governance(
                client_name=client,
                engagement_id=eng_id,
                wp1_findings=wp1_findings,
            )
        
        # Display results
        console.print(f"\n[bold]Status:[/bold] {result.get('status')}")
        console.print(f"[bold]Stage:[/bold] {result.get('workflow_stage')}")
        console.print(f"[bold]Stages completed:[/bold] {result.get('stages_completed')}")
        
        if result.get("deliverables"):
            console.print("\n[bold]Deliverables:[/bold]")
            for name, info in result["deliverables"].items():
                status_color = "green" if info.get("status") == "complete" else "yellow"
                console.print(f"  - {name}: [{status_color}]{info.get('status')}[/]")
        
        if result.get("artifacts"):
            console.print(f"\n[bold]Artifacts generated:[/bold] {len(result['artifacts'])}")
            
            if output_dir:
                output_dir.mkdir(parents=True, exist_ok=True)
                for artifact in result["artifacts"]:
                    artifact_path = output_dir / f"{artifact['name']}.md"
                    artifact_path.write_text(artifact["content"])
                console.print(f"[green]Saved artifacts to {output_dir}[/green]")
        
        if result.get("human_approval_needed"):
            console.print("\n[yellow]⚠ Workflow paused - awaiting human review[/yellow]")
            console.print(f"Resume with: bv a4 resume --engagement {eng_id} --response approve")
    
    asyncio.run(_wp4())


@a4_app.command("operating-model")
def a4_operating_model(
    client: str = typer.Option(..., "--client", "-c", help="Client name"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file"),
):
    """Define operating model for platform governance."""
    async def _model():
        from agents.a4_governance import create_a4_agent, A4State
        from core.orchestrator import AgentStatus
        
        a4 = create_a4_agent()
        
        state: A4State = {
            "agent_id": "a4",
            "workflow_id": "operating_model",
            "client_name": client,
            "current_task": "define_operating_model",
            "messages": [],
            "artifacts": [],
            "decisions": [],
            "status": AgentStatus.RUNNING,
        }
        
        console.print(Panel(f"Defining operating model for: [cyan]{client}[/cyan]"))
        
        with console.status("[yellow]Creating operating model...[/yellow]"):
            result = await a4.run(state)
        
        if result.get("artifacts"):
            for artifact in result["artifacts"]:
                if artifact["type"] == "operating_model":
                    console.print(f"\n[bold green]Operating Model Generated[/bold green]")
                    console.print(artifact["content"][:3000] + "..." if len(artifact["content"]) > 3000 else artifact["content"])
                    
                    if output:
                        output.write_text(artifact["content"])
                        console.print(f"\n[green]Saved to {output}[/green]")
    
    asyncio.run(_model())


@a4_app.command("policies")
def a4_policies(
    client: str = typer.Option(..., "--client", "-c", help="Client name"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file"),
):
    """Create governance policies."""
    async def _policies():
        from agents.a4_governance import create_a4_agent, A4State
        from core.orchestrator import AgentStatus
        
        a4 = create_a4_agent()
        
        state: A4State = {
            "agent_id": "a4",
            "workflow_id": "policies",
            "client_name": client,
            "current_task": "create_policies",
            "messages": [],
            "artifacts": [],
            "decisions": [],
            "status": AgentStatus.RUNNING,
        }
        
        console.print(Panel(f"Creating policies for: [cyan]{client}[/cyan]"))
        
        with console.status("[yellow]Generating governance policies...[/yellow]"):
            result = await a4.run(state)
        
        if result.get("artifacts"):
            for artifact in result["artifacts"]:
                if artifact["type"] == "policy_set":
                    console.print(f"\n[bold green]Policies Generated[/bold green]")
                    console.print(artifact["content"][:3000] + "..." if len(artifact["content"]) > 3000 else artifact["content"])
                    
                    if output:
                        output.write_text(artifact["content"])
                        console.print(f"\n[green]Saved to {output}[/green]")
    
    asyncio.run(_policies())


@a4_app.command("standards")
def a4_standards(
    client: str = typer.Option(..., "--client", "-c", help="Client name"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file"),
):
    """Build standards library."""
    async def _standards():
        from agents.a4_governance import create_a4_agent, A4State
        from core.orchestrator import AgentStatus
        
        a4 = create_a4_agent()
        
        state: A4State = {
            "agent_id": "a4",
            "workflow_id": "standards",
            "client_name": client,
            "current_task": "build_standards",
            "messages": [],
            "artifacts": [],
            "decisions": [],
            "status": AgentStatus.RUNNING,
        }
        
        console.print(Panel(f"Building standards for: [cyan]{client}[/cyan]"))
        
        with console.status("[yellow]Generating standards library...[/yellow]"):
            result = await a4.run(state)
        
        if result.get("artifacts"):
            for artifact in result["artifacts"]:
                if artifact["type"] == "standards_library":
                    console.print(f"\n[bold green]Standards Library Generated[/bold green]")
                    console.print(artifact["content"][:3000] + "..." if len(artifact["content"]) > 3000 else artifact["content"])
                    
                    if output:
                        output.write_text(artifact["content"])
                        console.print(f"\n[green]Saved to {output}[/green]")
    
    asyncio.run(_standards())


@a4_app.command("runbooks")
def a4_runbooks(
    client: str = typer.Option(..., "--client", "-c", help="Client name"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file"),
):
    """Create admin runbooks."""
    async def _runbooks():
        from agents.a4_governance import create_a4_agent, A4State
        from core.orchestrator import AgentStatus
        
        a4 = create_a4_agent()
        
        state: A4State = {
            "agent_id": "a4",
            "workflow_id": "runbooks",
            "client_name": client,
            "current_task": "create_runbooks",
            "messages": [],
            "artifacts": [],
            "decisions": [],
            "status": AgentStatus.RUNNING,
        }
        
        console.print(Panel(f"Creating runbooks for: [cyan]{client}[/cyan]"))
        
        with console.status("[yellow]Generating runbooks...[/yellow]"):
            result = await a4.run(state)
        
        if result.get("artifacts"):
            for artifact in result["artifacts"]:
                if artifact["type"] == "runbook_library":
                    console.print(f"\n[bold green]Runbooks Generated[/bold green]")
                    console.print(artifact["content"][:3000] + "..." if len(artifact["content"]) > 3000 else artifact["content"])
                    
                    if output:
                        output.write_text(artifact["content"])
                        console.print(f"\n[green]Saved to {output}[/green]")
    
    asyncio.run(_runbooks())


@a4_app.command("kpis")
def a4_kpis(
    client: str = typer.Option(..., "--client", "-c", help="Client name"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file"),
):
    """Define KPIs and metrics dashboard."""
    async def _kpis():
        from agents.a4_governance import create_a4_agent, A4State
        from core.orchestrator import AgentStatus
        
        a4 = create_a4_agent()
        
        state: A4State = {
            "agent_id": "a4",
            "workflow_id": "kpis",
            "client_name": client,
            "current_task": "define_kpis",
            "messages": [],
            "artifacts": [],
            "decisions": [],
            "status": AgentStatus.RUNNING,
        }
        
        console.print(Panel(f"Defining KPIs for: [cyan]{client}[/cyan]"))
        
        with console.status("[yellow]Generating KPI framework...[/yellow]"):
            result = await a4.run(state)
        
        if result.get("artifacts"):
            for artifact in result["artifacts"]:
                if artifact["type"] == "kpi_dashboard":
                    console.print(f"\n[bold green]KPI Dashboard Generated[/bold green]")
                    console.print(artifact["content"])
                    
                    if output:
                        output.write_text(artifact["content"])
                        console.print(f"\n[green]Saved to {output}[/green]")
    
    asyncio.run(_kpis())


@a4_app.command("resume")
def a4_resume(
    engagement_id: str = typer.Option(..., "--engagement", "-e", help="Engagement ID"),
    response: str = typer.Option(..., "--response", "-r", help="Review response: approve/revise/reject"),
):
    """Resume WP4 workflow after human review."""
    async def _resume():
        from workflows.wp4_governance import resume_wp4_governance
        
        if response not in ["approve", "revise", "reject"]:
            console.print(f"[red]Invalid response. Use: approve, revise, or reject[/red]")
            raise typer.Exit(1)
        
        console.print(Panel(f"Resuming WP4: [cyan]{engagement_id}[/cyan] with [{response}]"))
        
        with console.status("[yellow]Resuming workflow...[/yellow]"):
            result = await resume_wp4_governance(engagement_id, response)
        
        console.print(f"\n[bold]Status:[/bold] {result.get('status')}")
        console.print(f"[bold]Stage:[/bold] {result.get('workflow_stage')}")
        
        if result.get("deliverables"):
            console.print("\n[bold]Deliverables:[/bold]")
            for name, info in result["deliverables"].items():
                console.print(f"  - {name}: {info.get('status')}")
    
    asyncio.run(_resume())


# =============================================================================
# Workflow Commands
# =============================================================================

workflow_app = typer.Typer(help="Workflow management commands")
app.add_typer(workflow_app, name="workflow")


@workflow_app.command("run")
def workflow_run(
    workflow_id: str = typer.Argument(..., help="Workflow ID to run"),
    input_file: Path = typer.Option(..., "--input", "-i", help="JSON input file"),
    thread_id: Optional[str] = typer.Option(None, "--thread", "-t", help="Thread ID for checkpointing"),
):
    """Run a workflow with input data."""
    async def _run():
        from core.orchestrator import get_orchestrator
        
        if not input_file.exists():
            console.print(f"[red]File not found: {input_file}[/red]")
            raise typer.Exit(1)
        
        input_data = json.loads(input_file.read_text())
        
        orchestrator = get_orchestrator()
        
        console.print(Panel(f"Running workflow: [cyan]{workflow_id}[/cyan]"))
        
        with console.status("[yellow]Executing workflow...[/yellow]"):
            result = await orchestrator.run_workflow(
                workflow_id,
                input_data,
                thread_id=thread_id,
            )
        
        console.print(f"\n[bold]Status:[/bold] {result.get('status')}")
        console.print(f"[bold]Stage:[/bold] {result.get('workflow_stage', 'N/A')}")
        
        if result.get("output_data"):
            console.print("\n[bold]Output:[/bold]")
            console.print_json(json.dumps(result["output_data"], indent=2))
    
    asyncio.run(_run())


# =============================================================================
# Chat Mode
# =============================================================================

@app.command()
def chat(
    agent_id: str = typer.Option("a1", "--agent", "-a", help="Agent to chat with (a1, a3, a4, a6)"),
):
    """Interactive chat with an agent."""
    async def _chat():
        from agents.a1_gtm import create_a1_agent
        from agents.a3_assessment import create_a3_agent
        from agents.a4_governance import create_a4_agent
        from agents.a6_delivery import create_a6_agent
        
        agents_map = {
            "a1": create_a1_agent,
            "a3": create_a3_agent,
            "a4": create_a4_agent,
            "a6": create_a6_agent,
        }
        
        if agent_id not in agents_map:
            console.print(f"[red]Agent not found: {agent_id}[/red]")
            console.print(f"Available: {', '.join(agents_map.keys())}")
            raise typer.Exit(1)
        
        agent = agents_map[agent_id]()
        
        console.print(Panel(
            f"[bold]Chat with {agent.config.name}[/bold]\n"
            f"{agent.config.goal}\n\n"
            "[dim]Type 'exit' or 'quit' to end, 'clear' to reset[/dim]",
            title=f"Agent {agent_id.upper()}",
        ))
        
        history = []
        
        while True:
            try:
                user_input = console.input("\n[bold cyan]You:[/bold cyan] ")
            except (KeyboardInterrupt, EOFError):
                console.print("\n[yellow]Goodbye![/yellow]")
                break
            
            if user_input.lower() in ("exit", "quit"):
                console.print("[yellow]Goodbye![/yellow]")
                break
            
            if user_input.lower() == "clear":
                history = []
                console.print("[dim]History cleared[/dim]")
                continue
            
            if not user_input.strip():
                continue
            
            history.append({"role": "user", "content": user_input})
            
            with console.status("[yellow]Thinking...[/yellow]"):
                response = await agent.think(user_input, context={"history": history[-10:]})
            
            history.append({"role": "assistant", "content": response})
            
            console.print(f"\n[bold green]{agent.config.name}:[/bold green]")
            console.print(response)
    
    asyncio.run(_chat())


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    app()
