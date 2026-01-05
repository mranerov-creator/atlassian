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
# A2 Solution Architect Commands
# =============================================================================

a2_app = typer.Typer(help="A2 Solution Architect agent commands")
app.add_typer(a2_app, name="a2")


@a2_app.command("design")
def a2_design(
    client: str = typer.Option(..., "--client", "-c", help="Client name"),
    engagement_id: str = typer.Option(None, "--engagement", "-e", help="Engagement ID"),
    wp1_file: Optional[Path] = typer.Option(None, "--wp1", help="WP1 findings file (JSON)"),
    output_dir: Optional[Path] = typer.Option(None, "--output", "-o", help="Output directory"),
):
    """Execute full architecture design workflow."""
    async def _design():
        from workflows.architecture_design import run_architecture_design
        from datetime import datetime
        import json
        
        eng_id = engagement_id or f"ARCH-{client.upper()[:4]}-{datetime.now().strftime('%Y%m%d')}"
        
        wp1_findings = {}
        if wp1_file and wp1_file.exists():
            try:
                wp1_findings = json.loads(wp1_file.read_text())
            except json.JSONDecodeError:
                wp1_findings = {"context": wp1_file.read_text()}
        
        console.print(Panel(
            f"[bold]Architecture Design[/bold]\n"
            f"Client: [cyan]{client}[/cyan]\n"
            f"Engagement: [cyan]{eng_id}[/cyan]",
            title="Starting Architecture Design"
        ))
        
        with console.status("[yellow]Executing architecture workflow...[/yellow]"):
            result = await run_architecture_design(
                client_name=client,
                engagement_id=eng_id,
                wp1_findings=wp1_findings,
            )
        
        console.print(f"\n[bold]Status:[/bold] {result.get('status')}")
        console.print(f"[bold]Stage:[/bold] {result.get('workflow_stage')}")
        console.print(f"[bold]Stages completed:[/bold] {result.get('stages_completed')}")
        
        if result.get("artifacts"):
            console.print(f"\n[bold]Artifacts generated:[/bold] {len(result['artifacts'])}")
            
            if output_dir:
                output_dir.mkdir(parents=True, exist_ok=True)
                for artifact in result["artifacts"]:
                    artifact_path = output_dir / f"{artifact['name']}.md"
                    artifact_path.write_text(artifact["content"])
                console.print(f"[green]Saved artifacts to {output_dir}[/green]")
        
        if result.get("human_approval_needed"):
            console.print("\n[yellow]⚠ Workflow paused - awaiting review[/yellow]")
            console.print(f"Resume with: bv a2 resume --engagement {eng_id} --response approve")
    
    asyncio.run(_design())


@a2_app.command("current-state")
def a2_current_state(
    client: str = typer.Option(..., "--client", "-c", help="Client name"),
    wp1_file: Optional[Path] = typer.Option(None, "--wp1", help="WP1 findings file"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file"),
):
    """Assess current state architecture."""
    async def _assess():
        from agents.a2_architect import create_a2_agent, A2State
        from core.orchestrator import AgentStatus
        import json
        
        a2 = create_a2_agent()
        
        wp1_findings = {}
        if wp1_file and wp1_file.exists():
            try:
                wp1_findings = json.loads(wp1_file.read_text())
            except:
                wp1_findings = {"context": wp1_file.read_text()}
        
        state: A2State = {
            "agent_id": "a2",
            "workflow_id": "current_state",
            "client_name": client,
            "wp1_findings": wp1_findings,
            "current_task": "assess_current_state",
            "messages": [], "artifacts": [], "decisions": [],
            "status": AgentStatus.RUNNING,
        }
        
        console.print(Panel(f"Assessing current state for: [cyan]{client}[/cyan]"))
        
        with console.status("[yellow]Analyzing current architecture...[/yellow]"):
            result = await a2.run(state)
        
        if result.get("artifacts"):
            for artifact in result["artifacts"]:
                if artifact["type"] == "current_state_assessment":
                    console.print(f"\n[bold green]Current State Assessment[/bold green]")
                    content = artifact["content"]
                    console.print(content[:3000] + "..." if len(content) > 3000 else content)
                    
                    if output:
                        output.write_text(content)
                        console.print(f"\n[green]Saved to {output}[/green]")
    
    asyncio.run(_assess())


@a2_app.command("options")
def a2_options(
    client: str = typer.Option(..., "--client", "-c", help="Client name"),
    wp1_file: Optional[Path] = typer.Option(None, "--wp1", help="WP1 findings file"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file"),
):
    """Evaluate architecture options."""
    async def _options():
        from agents.a2_architect import create_a2_agent, A2State
        from core.orchestrator import AgentStatus
        import json
        
        a2 = create_a2_agent()
        
        wp1_findings = {}
        if wp1_file and wp1_file.exists():
            try:
                wp1_findings = json.loads(wp1_file.read_text())
            except:
                wp1_findings = {"context": wp1_file.read_text()}
        
        state: A2State = {
            "agent_id": "a2",
            "workflow_id": "options",
            "client_name": client,
            "wp1_findings": wp1_findings,
            "current_task": "evaluate_options",
            "messages": [], "artifacts": [], "decisions": [],
            "status": AgentStatus.RUNNING,
        }
        
        console.print(Panel(f"Evaluating architecture options for: [cyan]{client}[/cyan]"))
        
        with console.status("[yellow]Analyzing options...[/yellow]"):
            result = await a2.run(state)
        
        if result.get("artifacts"):
            for artifact in result["artifacts"]:
                if artifact["type"] == "architecture_options":
                    console.print(f"\n[bold green]Architecture Options[/bold green]")
                    content = artifact["content"]
                    console.print(content[:4000] + "..." if len(content) > 4000 else content)
                    
                    if output:
                        output.write_text(content)
                        console.print(f"\n[green]Saved to {output}[/green]")
    
    asyncio.run(_options())


@a2_app.command("target")
def a2_target(
    client: str = typer.Option(..., "--client", "-c", help="Client name"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file"),
):
    """Design target state architecture."""
    async def _target():
        from agents.a2_architect import create_a2_agent, A2State
        from core.orchestrator import AgentStatus
        
        a2 = create_a2_agent()
        
        state: A2State = {
            "agent_id": "a2",
            "workflow_id": "target_state",
            "client_name": client,
            "current_task": "design_target_state",
            "messages": [], "artifacts": [], "decisions": [],
            "status": AgentStatus.RUNNING,
            "options_evaluated": True,  # Assume options done
        }
        
        console.print(Panel(f"Designing target state for: [cyan]{client}[/cyan]"))
        
        with console.status("[yellow]Creating target architecture...[/yellow]"):
            result = await a2.run(state)
        
        if result.get("artifacts"):
            for artifact in result["artifacts"]:
                if artifact["type"] == "target_state_design":
                    console.print(f"\n[bold green]Target State Design[/bold green]")
                    content = artifact["content"]
                    console.print(content[:4000] + "..." if len(content) > 4000 else content)
                    
                    if output:
                        output.write_text(content)
                        console.print(f"\n[green]Saved to {output}[/green]")
    
    asyncio.run(_target())


@a2_app.command("sizing")
def a2_sizing(
    client: str = typer.Option(..., "--client", "-c", help="Client name"),
    users: int = typer.Option(100, "--users", "-u", help="Estimated user count"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file"),
):
    """Calculate sizing and licensing."""
    async def _sizing():
        from agents.a2_architect import create_a2_agent, A2State
        from core.orchestrator import AgentStatus
        
        a2 = create_a2_agent()
        
        state: A2State = {
            "agent_id": "a2",
            "workflow_id": "sizing",
            "client_name": client,
            "wp1_findings": {"estimated_users": users},
            "current_task": "calculate_sizing",
            "messages": [], "artifacts": [], "decisions": [],
            "status": AgentStatus.RUNNING,
        }
        
        console.print(Panel(f"Calculating sizing for: [cyan]{client}[/cyan] (~{users} users)"))
        
        with console.status("[yellow]Calculating sizing...[/yellow]"):
            result = await a2.run(state)
        
        if result.get("artifacts"):
            for artifact in result["artifacts"]:
                if artifact["type"] == "sizing_recommendation":
                    console.print(f"\n[bold green]Sizing Recommendation[/bold green]")
                    content = artifact["content"]
                    console.print(content)
                    
                    if output:
                        output.write_text(content)
                        console.print(f"\n[green]Saved to {output}[/green]")
    
    asyncio.run(_sizing())


@a2_app.command("resume")
def a2_resume(
    engagement_id: str = typer.Option(..., "--engagement", "-e", help="Engagement ID"),
    response: str = typer.Option(..., "--response", "-r", help="Review response: approve/revise/reject"),
):
    """Resume architecture workflow after review."""
    async def _resume():
        from workflows.architecture_design import resume_architecture_workflow
        
        if response not in ["approve", "revise", "reject"]:
            console.print(f"[red]Invalid response. Use: approve, revise, or reject[/red]")
            raise typer.Exit(1)
        
        console.print(Panel(f"Resuming architecture: [cyan]{engagement_id}[/cyan] with [{response}]"))
        
        with console.status("[yellow]Resuming workflow...[/yellow]"):
            result = await resume_architecture_workflow(engagement_id, response)
        
        console.print(f"\n[bold]Status:[/bold] {result.get('status')}")
        console.print(f"[bold]Stage:[/bold] {result.get('workflow_stage')}")
        
        if result.get("artifacts"):
            console.print(f"\n[bold]Artifacts:[/bold]")
            for artifact in result["artifacts"]:
                console.print(f"  - {artifact['type']}: {artifact['name']}")
    
    asyncio.run(_resume())


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
# A5 Migration Factory Commands
# =============================================================================

a5_app = typer.Typer(help="A5 Migration Factory agent commands")
app.add_typer(a5_app, name="a5")


@a5_app.command("wp2")
def a5_wp2(
    client: str = typer.Option(..., "--client", "-c", help="Client name"),
    engagement_id: str = typer.Option(None, "--engagement", "-e", help="Engagement ID"),
    arch_file: Optional[Path] = typer.Option(None, "--arch", help="Architecture design file (JSON)"),
    output_dir: Optional[Path] = typer.Option(None, "--output", "-o", help="Output directory"),
):
    """Execute WP2 Cloud Migration planning."""
    async def _wp2():
        from workflows.migration_execution import run_migration_planning
        from agents.a5_migration import MigrationType
        from datetime import datetime
        import json
        
        eng_id = engagement_id or f"WP2-{client.upper()[:4]}-{datetime.now().strftime('%Y%m%d')}"
        
        arch_design = {}
        if arch_file and arch_file.exists():
            try:
                arch_design = json.loads(arch_file.read_text())
            except:
                arch_design = {"context": arch_file.read_text()}
        
        console.print(Panel(
            f"[bold]WP2 Cloud Migration Planning[/bold]\n"
            f"Client: [cyan]{client}[/cyan]\n"
            f"Engagement: [cyan]{eng_id}[/cyan]",
            title="Starting WP2"
        ))
        
        with console.status("[yellow]Executing migration planning...[/yellow]"):
            result = await run_migration_planning(
                client_name=client,
                migration_type=MigrationType.SERVER_TO_CLOUD,
                engagement_id=eng_id,
                architecture_design=arch_design,
            )
        
        console.print(f"\n[bold]Status:[/bold] {result.get('status')}")
        console.print(f"[bold]Stage:[/bold] {result.get('workflow_stage')}")
        console.print(f"[bold]Stages completed:[/bold] {result.get('stages_completed')}")
        
        if result.get("artifacts"):
            console.print(f"\n[bold]Artifacts:[/bold] {len(result['artifacts'])}")
            
            if output_dir:
                output_dir.mkdir(parents=True, exist_ok=True)
                for artifact in result["artifacts"]:
                    artifact_path = output_dir / f"{artifact['name']}.md"
                    artifact_path.write_text(artifact["content"])
                console.print(f"[green]Saved to {output_dir}[/green]")
        
        if result.get("human_approval_needed"):
            console.print("\n[yellow]⚠ Awaiting review[/yellow]")
            console.print(f"Resume: bv a5 resume --engagement {eng_id} --response approve")
    
    asyncio.run(_wp2())


@a5_app.command("wp5")
def a5_wp5(
    client: str = typer.Option(..., "--client", "-c", help="Client name"),
    engagement_id: str = typer.Option(None, "--engagement", "-e", help="Engagement ID"),
    output_dir: Optional[Path] = typer.Option(None, "--output", "-o", help="Output directory"),
):
    """Execute WP5 Cloud-to-Cloud Migration planning."""
    async def _wp5():
        from workflows.migration_execution import run_migration_planning
        from agents.a5_migration import MigrationType
        from datetime import datetime
        
        eng_id = engagement_id or f"WP5-{client.upper()[:4]}-{datetime.now().strftime('%Y%m%d')}"
        
        console.print(Panel(
            f"[bold]WP5 Cloud-to-Cloud Migration[/bold]\n"
            f"Client: [cyan]{client}[/cyan]\n"
            f"Engagement: [cyan]{eng_id}[/cyan]",
            title="Starting WP5"
        ))
        
        with console.status("[yellow]Executing migration planning...[/yellow]"):
            result = await run_migration_planning(
                client_name=client,
                migration_type=MigrationType.CLOUD_TO_CLOUD,
                engagement_id=eng_id,
            )
        
        console.print(f"\n[bold]Status:[/bold] {result.get('status')}")
        
        if output_dir and result.get("artifacts"):
            output_dir.mkdir(parents=True, exist_ok=True)
            for artifact in result["artifacts"]:
                artifact_path = output_dir / f"{artifact['name']}.md"
                artifact_path.write_text(artifact["content"])
            console.print(f"[green]Saved to {output_dir}[/green]")
    
    asyncio.run(_wp5())


@a5_app.command("inventory")
def a5_inventory(
    client: str = typer.Option(..., "--client", "-c", help="Client name"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file"),
):
    """Create migration inventory."""
    async def _inventory():
        from agents.a5_migration import create_a5_agent, A5State, MigrationType
        from core.orchestrator import AgentStatus
        
        a5 = create_a5_agent()
        
        state: A5State = {
            "agent_id": "a5",
            "workflow_id": "inventory",
            "client_name": client,
            "migration_type": MigrationType.SERVER_TO_CLOUD,
            "current_task": "create_inventory",
            "messages": [], "artifacts": [], "decisions": [],
            "status": AgentStatus.RUNNING,
        }
        
        console.print(Panel(f"Creating inventory for: [cyan]{client}[/cyan]"))
        
        with console.status("[yellow]Analyzing source systems...[/yellow]"):
            result = await a5.run(state)
        
        if result.get("artifacts"):
            for artifact in result["artifacts"]:
                if artifact["type"] == "migration_inventory":
                    content = artifact["content"]
                    console.print(content[:4000] + "..." if len(content) > 4000 else content)
                    if output:
                        output.write_text(content)
                        console.print(f"\n[green]Saved to {output}[/green]")
    
    asyncio.run(_inventory())


@a5_app.command("waves")
def a5_waves(
    client: str = typer.Option(..., "--client", "-c", help="Client name"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file"),
):
    """Plan migration waves."""
    async def _waves():
        from agents.a5_migration import create_a5_agent, A5State, MigrationType
        from core.orchestrator import AgentStatus
        
        a5 = create_a5_agent()
        
        state: A5State = {
            "agent_id": "a5",
            "workflow_id": "waves",
            "client_name": client,
            "migration_type": MigrationType.SERVER_TO_CLOUD,
            "current_task": "plan_waves",
            "messages": [], "artifacts": [], "decisions": [],
            "status": AgentStatus.RUNNING,
            "inventory_complete": True,
        }
        
        console.print(Panel(f"Planning waves for: [cyan]{client}[/cyan]"))
        
        with console.status("[yellow]Creating wave plan...[/yellow]"):
            result = await a5.run(state)
        
        if result.get("artifacts"):
            for artifact in result["artifacts"]:
                if artifact["type"] == "wave_plan":
                    content = artifact["content"]
                    console.print(content[:4000] + "..." if len(content) > 4000 else content)
                    if output:
                        output.write_text(content)
                        console.print(f"\n[green]Saved to {output}[/green]")
    
    asyncio.run(_waves())


@a5_app.command("runbooks")
def a5_runbooks(
    client: str = typer.Option(..., "--client", "-c", help="Client name"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file"),
):
    """Create migration runbooks."""
    async def _runbooks():
        from agents.a5_migration import create_a5_agent, A5State, MigrationType
        from core.orchestrator import AgentStatus
        
        a5 = create_a5_agent()
        
        state: A5State = {
            "agent_id": "a5",
            "workflow_id": "runbooks",
            "client_name": client,
            "migration_type": MigrationType.SERVER_TO_CLOUD,
            "current_task": "create_runbooks",
            "messages": [], "artifacts": [], "decisions": [],
            "status": AgentStatus.RUNNING,
        }
        
        console.print(Panel(f"Creating runbooks for: [cyan]{client}[/cyan]"))
        
        with console.status("[yellow]Generating runbooks...[/yellow]"):
            result = await a5.run(state)
        
        if result.get("artifacts"):
            for artifact in result["artifacts"]:
                if artifact["type"] == "migration_runbooks":
                    content = artifact["content"]
                    console.print(content[:4000] + "..." if len(content) > 4000 else content)
                    if output:
                        output.write_text(content)
                        console.print(f"\n[green]Saved to {output}[/green]")
    
    asyncio.run(_runbooks())


@a5_app.command("resume")
def a5_resume(
    engagement_id: str = typer.Option(..., "--engagement", "-e", help="Engagement ID"),
    response: str = typer.Option(..., "--response", "-r", help="Review response: approve/revise/reject"),
):
    """Resume migration workflow after review."""
    async def _resume():
        from workflows.migration_execution import resume_migration_workflow
        
        if response not in ["approve", "revise", "reject"]:
            console.print(f"[red]Invalid response. Use: approve, revise, or reject[/red]")
            raise typer.Exit(1)
        
        console.print(Panel(f"Resuming: [cyan]{engagement_id}[/cyan] with [{response}]"))
        
        with console.status("[yellow]Resuming workflow...[/yellow]"):
            result = await resume_migration_workflow(engagement_id, response)
        
        console.print(f"\n[bold]Status:[/bold] {result.get('status')}")
        console.print(f"[bold]Stage:[/bold] {result.get('workflow_stage')}")
    
    asyncio.run(_resume())


# =============================================================================
# A0 CEO/Strategist Commands
# =============================================================================

a0_app = typer.Typer(help="A0 CEO/Strategist agent commands")
app.add_typer(a0_app, name="a0")


@a0_app.command("price")
def a0_price(
    client: str = typer.Option(..., "--client", "-c", help="Client name"),
    deal_id: str = typer.Option(None, "--deal", "-d", help="Deal ID"),
    scope: str = typer.Option(..., "--scope", "-s", help="Scope description or WP codes (e.g., 'WP1+WP4')"),
    segment: str = typer.Option("mid_market", "--segment", help="Market segment: enterprise/mid_market/smb"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file"),
):
    """Price a deal."""
    async def _price():
        from agents.a0_strategist import create_a0_agent, A0State
        from core.orchestrator import AgentStatus
        from datetime import datetime
        
        a0 = create_a0_agent()
        
        d_id = deal_id or f"DEAL-{client[:4].upper()}-{datetime.now().strftime('%Y%m%d')}"
        
        state: A0State = {
            "agent_id": "a0",
            "workflow_id": "pricing",
            "query_type": "pricing",
            "deal_context": {
                "deal_id": d_id,
                "client_name": client,
                "scope": scope,
                "segment": segment,
            },
            "current_task": "price_deal",
            "messages": [], "artifacts": [], "decisions": [],
            "status": AgentStatus.RUNNING,
        }
        
        console.print(Panel(
            f"[bold]Deal Pricing[/bold]\n"
            f"Client: [cyan]{client}[/cyan]\n"
            f"Scope: [cyan]{scope}[/cyan]\n"
            f"Segment: [cyan]{segment}[/cyan]",
            title="Pricing Analysis"
        ))
        
        with console.status("[yellow]Analyzing pricing...[/yellow]"):
            result = await a0.run(state)
        
        if result.get("artifacts"):
            for artifact in result["artifacts"]:
                if artifact["type"] == "deal_pricing":
                    content = artifact["content"]
                    console.print(content[:5000] + "..." if len(content) > 5000 else content)
                    if output:
                        output.write_text(content)
                        console.print(f"\n[green]Saved to {output}[/green]")
    
    asyncio.run(_price())


@a0_app.command("pipeline")
def a0_pipeline(
    data_file: Optional[Path] = typer.Option(None, "--data", "-d", help="Pipeline data file (JSON)"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file"),
):
    """Analyze sales pipeline."""
    async def _pipeline():
        from agents.a0_strategist import create_a0_agent, A0State
        from core.orchestrator import AgentStatus
        import json
        
        a0 = create_a0_agent()
        
        pipeline_data = []
        if data_file and data_file.exists():
            try:
                pipeline_data = json.loads(data_file.read_text())
            except:
                pass
        
        state: A0State = {
            "agent_id": "a0",
            "workflow_id": "pipeline",
            "query_type": "pipeline",
            "pipeline_data": pipeline_data,
            "current_task": "analyze_pipeline",
            "messages": [], "artifacts": [], "decisions": [],
            "status": AgentStatus.RUNNING,
        }
        
        console.print(Panel("[bold]Pipeline Analysis[/bold]", title="Strategic Review"))
        
        with console.status("[yellow]Analyzing pipeline...[/yellow]"):
            result = await a0.run(state)
        
        if result.get("artifacts"):
            for artifact in result["artifacts"]:
                if artifact["type"] == "pipeline_analysis":
                    content = artifact["content"]
                    console.print(content[:5000] + "..." if len(content) > 5000 else content)
                    if output:
                        output.write_text(content)
                        console.print(f"\n[green]Saved to {output}[/green]")
    
    asyncio.run(_pipeline())


@a0_app.command("competitive")
def a0_competitive(
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file"),
):
    """Perform competitive analysis."""
    async def _competitive():
        from agents.a0_strategist import create_a0_agent, A0State
        from core.orchestrator import AgentStatus
        
        a0 = create_a0_agent()
        
        state: A0State = {
            "agent_id": "a0",
            "workflow_id": "competitive",
            "query_type": "competitive",
            "current_task": "competitive_analysis",
            "messages": [], "artifacts": [], "decisions": [],
            "status": AgentStatus.RUNNING,
        }
        
        console.print(Panel("[bold]Competitive Intelligence[/bold]", title="Market Analysis"))
        
        with console.status("[yellow]Analyzing competition...[/yellow]"):
            result = await a0.run(state)
        
        if result.get("artifacts"):
            for artifact in result["artifacts"]:
                if artifact["type"] == "competitive_analysis":
                    content = artifact["content"]
                    console.print(content[:5000] + "..." if len(content) > 5000 else content)
                    if output:
                        output.write_text(content)
                        console.print(f"\n[green]Saved to {output}[/green]")
    
    asyncio.run(_competitive())


@a0_app.command("quarterly")
def a0_quarterly(
    quarter: str = typer.Option(None, "--quarter", "-q", help="Quarter (e.g., Q1)"),
    year: int = typer.Option(None, "--year", "-y", help="Year"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file"),
):
    """Create quarterly strategic plan."""
    async def _quarterly():
        from agents.a0_strategist import create_a0_agent, A0State
        from core.orchestrator import AgentStatus
        from datetime import datetime
        
        a0 = create_a0_agent()
        
        q = quarter or f"Q{(datetime.now().month - 1) // 3 + 1}"
        y = year or datetime.now().year
        
        state: A0State = {
            "agent_id": "a0",
            "workflow_id": "planning",
            "query_type": "planning",
            "market_context": {"quarter": q, "year": y},
            "current_task": "quarterly_planning",
            "messages": [], "artifacts": [], "decisions": [],
            "status": AgentStatus.RUNNING,
        }
        
        console.print(Panel(f"[bold]Quarterly Plan: {q} {y}[/bold]", title="Strategic Planning"))
        
        with console.status("[yellow]Creating quarterly plan...[/yellow]"):
            result = await a0.run(state)
        
        if result.get("artifacts"):
            for artifact in result["artifacts"]:
                if artifact["type"] == "quarterly_plan":
                    content = artifact["content"]
                    console.print(content[:5000] + "..." if len(content) > 5000 else content)
                    if output:
                        output.write_text(content)
                        console.print(f"\n[green]Saved to {output}[/green]")
    
    asyncio.run(_quarterly())


@a0_app.command("positioning")
def a0_positioning(
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file"),
):
    """Define market positioning strategy."""
    async def _positioning():
        from agents.a0_strategist import create_a0_agent, A0State
        from core.orchestrator import AgentStatus
        
        a0 = create_a0_agent()
        
        state: A0State = {
            "agent_id": "a0",
            "workflow_id": "positioning",
            "query_type": "positioning",
            "current_task": "market_positioning",
            "messages": [], "artifacts": [], "decisions": [],
            "status": AgentStatus.RUNNING,
        }
        
        console.print(Panel("[bold]Market Positioning[/bold]", title="Brand Strategy"))
        
        with console.status("[yellow]Defining positioning...[/yellow]"):
            result = await a0.run(state)
        
        if result.get("artifacts"):
            for artifact in result["artifacts"]:
                if artifact["type"] == "market_positioning":
                    content = artifact["content"]
                    console.print(content[:5000] + "..." if len(content) > 5000 else content)
                    if output:
                        output.write_text(content)
                        console.print(f"\n[green]Saved to {output}[/green]")
    
    asyncio.run(_positioning())


@a0_app.command("portfolio")
def a0_portfolio(
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file"),
):
    """Review portfolio health."""
    async def _portfolio():
        from agents.a0_strategist import create_a0_agent, A0State
        from core.orchestrator import AgentStatus
        
        a0 = create_a0_agent()
        
        state: A0State = {
            "agent_id": "a0",
            "workflow_id": "portfolio",
            "current_task": "portfolio_review",
            "messages": [], "artifacts": [], "decisions": [],
            "status": AgentStatus.RUNNING,
        }
        
        console.print(Panel("[bold]Portfolio Review[/bold]", title="Business Health"))
        
        with console.status("[yellow]Reviewing portfolio...[/yellow]"):
            result = await a0.run(state)
        
        if result.get("artifacts"):
            for artifact in result["artifacts"]:
                if artifact["type"] == "portfolio_review":
                    content = artifact["content"]
                    console.print(content[:5000] + "..." if len(content) > 5000 else content)
                    if output:
                        output.write_text(content)
                        console.print(f"\n[green]Saved to {output}[/green]")
    
    asyncio.run(_portfolio())


@a0_app.command("decide")
def a0_decide(
    question: str = typer.Option(..., "--question", "-q", help="Decision question"),
    context: str = typer.Option(None, "--context", "-c", help="Additional context"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file"),
):
    """Get strategic decision recommendation."""
    async def _decide():
        from agents.a0_strategist import create_a0_agent, A0State
        from core.orchestrator import AgentStatus
        
        a0 = create_a0_agent()
        
        state: A0State = {
            "agent_id": "a0",
            "workflow_id": "decision",
            "query_type": "decision",
            "deal_context": {
                "question": question,
                "context": context or "",
            },
            "current_task": "strategic_decision",
            "messages": [], "artifacts": [], "decisions": [],
            "status": AgentStatus.RUNNING,
        }
        
        console.print(Panel(f"[bold]Strategic Decision[/bold]\n{question}", title="Decision Analysis"))
        
        with console.status("[yellow]Analyzing options...[/yellow]"):
            result = await a0.run(state)
        
        if result.get("artifacts"):
            for artifact in result["artifacts"]:
                if artifact["type"] == "strategic_decision":
                    content = artifact["content"]
                    console.print(content[:5000] + "..." if len(content) > 5000 else content)
                    if output:
                        output.write_text(content)
                        console.print(f"\n[green]Saved to {output}[/green]")
    
    asyncio.run(_decide())


# =============================================================================
# A7 Builder Commands
# =============================================================================

a7_app = typer.Typer(help="A7 Builder agent commands")
app.add_typer(a7_app, name="a7")


@a7_app.command("build")
def a7_build(
    client: str = typer.Option(..., "--client", "-c", help="Client name"),
    engagement_id: str = typer.Option(None, "--engagement", "-e", help="Engagement ID"),
    requirements_file: Optional[Path] = typer.Option(None, "--requirements", "-r", help="Requirements file (JSON)"),
    output_dir: Optional[Path] = typer.Option(None, "--output", "-o", help="Output directory"),
):
    """Execute full implementation workflow."""
    async def _build():
        from workflows.implementation import run_implementation
        from datetime import datetime
        import json
        
        eng_id = engagement_id or f"IMPL-{client.upper()[:4]}-{datetime.now().strftime('%Y%m%d')}"
        
        requirements = {}
        if requirements_file and requirements_file.exists():
            try:
                requirements = json.loads(requirements_file.read_text())
            except:
                requirements = {"context": requirements_file.read_text()}
        
        console.print(Panel(
            f"[bold]Implementation Build[/bold]\n"
            f"Client: [cyan]{client}[/cyan]\n"
            f"Engagement: [cyan]{eng_id}[/cyan]",
            title="Starting Implementation"
        ))
        
        with console.status("[yellow]Executing implementation workflow...[/yellow]"):
            result = await run_implementation(
                client_name=client,
                engagement_id=eng_id,
                requirements=requirements,
            )
        
        console.print(f"\n[bold]Status:[/bold] {result.get('status')}")
        console.print(f"[bold]Stage:[/bold] {result.get('workflow_stage')}")
        console.print(f"[bold]Stages completed:[/bold] {result.get('stages_completed')}")
        
        if result.get("artifacts"):
            console.print(f"\n[bold]Artifacts:[/bold] {len(result['artifacts'])}")
            
            if output_dir:
                output_dir.mkdir(parents=True, exist_ok=True)
                for artifact in result["artifacts"]:
                    artifact_path = output_dir / f"{artifact['name']}.md"
                    artifact_path.write_text(artifact["content"])
                console.print(f"[green]Saved to {output_dir}[/green]")
        
        if result.get("human_approval_needed"):
            console.print("\n[yellow]⚠ Awaiting review[/yellow]")
            console.print(f"Resume: bv a7 resume --engagement {eng_id} --response approve")
    
    asyncio.run(_build())


@a7_app.command("automations")
def a7_automations(
    client: str = typer.Option(..., "--client", "-c", help="Client name"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file"),
):
    """Design automation rules."""
    async def _automations():
        from agents.a7_builder import create_a7_agent, A7State
        from core.orchestrator import AgentStatus
        
        a7 = create_a7_agent()
        
        state: A7State = {
            "agent_id": "a7",
            "workflow_id": "automations",
            "client_name": client,
            "current_task": "design_automations",
            "messages": [], "artifacts": [], "decisions": [],
            "status": AgentStatus.RUNNING,
            "requirements_analyzed": True,
        }
        
        console.print(Panel(f"Designing automations for: [cyan]{client}[/cyan]"))
        
        with console.status("[yellow]Creating automation library...[/yellow]"):
            result = await a7.run(state)
        
        if result.get("artifacts"):
            for artifact in result["artifacts"]:
                if artifact["type"] == "automation_library":
                    content = artifact["content"]
                    console.print(content[:4000] + "..." if len(content) > 4000 else content)
                    if output:
                        output.write_text(content)
                        console.print(f"\n[green]Saved to {output}[/green]")
    
    asyncio.run(_automations())


@a7_app.command("integrations")
def a7_integrations(
    client: str = typer.Option(..., "--client", "-c", help="Client name"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file"),
):
    """Design integrations."""
    async def _integrations():
        from agents.a7_builder import create_a7_agent, A7State
        from core.orchestrator import AgentStatus
        
        a7 = create_a7_agent()
        
        state: A7State = {
            "agent_id": "a7",
            "workflow_id": "integrations",
            "client_name": client,
            "current_task": "design_integrations",
            "messages": [], "artifacts": [], "decisions": [],
            "status": AgentStatus.RUNNING,
        }
        
        console.print(Panel(f"Designing integrations for: [cyan]{client}[/cyan]"))
        
        with console.status("[yellow]Creating integration catalog...[/yellow]"):
            result = await a7.run(state)
        
        if result.get("artifacts"):
            for artifact in result["artifacts"]:
                if artifact["type"] == "integration_catalog":
                    content = artifact["content"]
                    console.print(content[:4000] + "..." if len(content) > 4000 else content)
                    if output:
                        output.write_text(content)
                        console.print(f"\n[green]Saved to {output}[/green]")
    
    asyncio.run(_integrations())


@a7_app.command("dashboards")
def a7_dashboards(
    client: str = typer.Option(..., "--client", "-c", help="Client name"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file"),
):
    """Create dashboard specifications."""
    async def _dashboards():
        from agents.a7_builder import create_a7_agent, A7State
        from core.orchestrator import AgentStatus
        
        a7 = create_a7_agent()
        
        state: A7State = {
            "agent_id": "a7",
            "workflow_id": "dashboards",
            "client_name": client,
            "current_task": "create_dashboards",
            "messages": [], "artifacts": [], "decisions": [],
            "status": AgentStatus.RUNNING,
        }
        
        console.print(Panel(f"Creating dashboards for: [cyan]{client}[/cyan]"))
        
        with console.status("[yellow]Generating dashboard specs...[/yellow]"):
            result = await a7.run(state)
        
        if result.get("artifacts"):
            for artifact in result["artifacts"]:
                if artifact["type"] == "dashboard_library":
                    content = artifact["content"]
                    console.print(content[:4000] + "..." if len(content) > 4000 else content)
                    if output:
                        output.write_text(content)
                        console.print(f"\n[green]Saved to {output}[/green]")
    
    asyncio.run(_dashboards())


@a7_app.command("forge")
def a7_forge(
    client: str = typer.Option(..., "--client", "-c", help="Client name"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file"),
):
    """Design a Forge app."""
    async def _forge():
        from agents.a7_builder import create_a7_agent, A7State
        from core.orchestrator import AgentStatus
        
        a7 = create_a7_agent()
        
        state: A7State = {
            "agent_id": "a7",
            "workflow_id": "forge",
            "client_name": client,
            "current_task": "design_forge_app",
            "messages": [], "artifacts": [], "decisions": [],
            "status": AgentStatus.RUNNING,
        }
        
        console.print(Panel(f"Designing Forge app for: [cyan]{client}[/cyan]"))
        
        with console.status("[yellow]Creating Forge app spec...[/yellow]"):
            result = await a7.run(state)
        
        if result.get("artifacts"):
            for artifact in result["artifacts"]:
                if artifact["type"] == "forge_app_spec":
                    content = artifact["content"]
                    console.print(content[:4000] + "..." if len(content) > 4000 else content)
                    if output:
                        output.write_text(content)
                        console.print(f"\n[green]Saved to {output}[/green]")
    
    asyncio.run(_forge())


@a7_app.command("resume")
def a7_resume(
    engagement_id: str = typer.Option(..., "--engagement", "-e", help="Engagement ID"),
    response: str = typer.Option(..., "--response", "-r", help="Review response: approve/revise/reject"),
):
    """Resume implementation workflow after review."""
    async def _resume():
        from workflows.implementation import resume_implementation_workflow
        
        if response not in ["approve", "revise", "reject"]:
            console.print(f"[red]Invalid response. Use: approve, revise, or reject[/red]")
            raise typer.Exit(1)
        
        console.print(Panel(f"Resuming: [cyan]{engagement_id}[/cyan] with [{response}]"))
        
        with console.status("[yellow]Resuming workflow...[/yellow]"):
            result = await resume_implementation_workflow(engagement_id, response)
        
        console.print(f"\n[bold]Status:[/bold] {result.get('status')}")
        console.print(f"[bold]Stage:[/bold] {result.get('workflow_stage')}")
    
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
    agent_id: str = typer.Option("a1", "--agent", "-a", help="Agent to chat with (a0, a1, a2, a3, a4, a5, a6, a7)"),
):
    """Interactive chat with an agent."""
    async def _chat():
        from agents.a0_strategist import create_a0_agent
        from agents.a1_gtm import create_a1_agent
        from agents.a2_architect import create_a2_agent
        from agents.a3_assessment import create_a3_agent
        from agents.a4_governance import create_a4_agent
        from agents.a5_migration import create_a5_agent
        from agents.a6_delivery import create_a6_agent
        from agents.a7_builder import create_a7_agent
        
        agents_map = {
            "a0": create_a0_agent,
            "a1": create_a1_agent,
            "a2": create_a2_agent,
            "a3": create_a3_agent,
            "a4": create_a4_agent,
            "a5": create_a5_agent,
            "a6": create_a6_agent,
            "a7": create_a7_agent,
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
