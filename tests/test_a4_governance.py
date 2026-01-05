"""
Tests for A4 Governance Lead Agent
"""
import pytest

from agents.a4_governance import (
    A4GovernanceAgent,
    A4State,
    create_a4_agent,
    # Enums
    PolicyStatus,
    PolicyCategory,
    StandardType,
    RACIRole,
    GovernanceMaturity,
    CommitteeCadence,
    # Models
    Role,
    RACIEntry,
    Committee,
    OperatingModel,
    Policy,
    Guardrail,
    WorkflowStandard,
    FieldStandard,
    SLAStandard,
    ProjectTemplate,
    StandardsLibrary,
    RunbookStep,
    Runbook,
    KPI,
    KPIDashboard,
    GovernanceHandbook,
)
from core.orchestrator import AgentStatus


class TestA4GovernanceAgent:
    """Test suite for A4 Governance agent."""
    
    def test_agent_creation(self):
        """Test agent can be created."""
        agent = create_a4_agent()
        
        assert agent.config.id == "a4"
        assert agent.config.name == "Governance Lead"
        assert "a2" in agent.config.allowed_handoffs
        assert "a3" in agent.config.allowed_handoffs
        assert "a6" in agent.config.allowed_handoffs
    
    def test_system_prompt_contains_rules(self):
        """Test system prompt contains required elements."""
        agent = create_a4_agent()
        prompt = agent.system_prompt()
        
        assert "RACI" in prompt
        assert "policy" in prompt.lower()
        assert "standard" in prompt.lower()
        assert "runbook" in prompt.lower()


class TestA4Enums:
    """Test A4 enums."""
    
    def test_policy_status(self):
        assert PolicyStatus.DRAFT == "draft"
        assert PolicyStatus.PUBLISHED == "published"
    
    def test_policy_category(self):
        assert PolicyCategory.ACCESS == "access_control"
        assert PolicyCategory.NAMING == "naming_conventions"
    
    def test_governance_maturity(self):
        assert GovernanceMaturity.INITIAL == "initial"
        assert GovernanceMaturity.OPTIMIZING == "optimizing"


class TestA4Models:
    """Test A4 Pydantic models."""
    
    def test_role(self):
        role = Role(
            id="platform-owner",
            name="Platform Owner",
            description="Strategic ownership of platform",
            responsibilities=["Budget", "Strategy", "Escalation"],
            time_commitment="10%",
        )
        assert role.id == "platform-owner"
        assert len(role.responsibilities) == 3
    
    def test_raci_entry(self):
        raci = RACIEntry(
            activity="User Provisioning",
            responsible=["Platform Admin"],
            accountable="Platform Owner",
            consulted=["HR"],
            informed=["Team Lead"],
        )
        assert raci.accountable == "Platform Owner"
        assert "Platform Admin" in raci.responsible
    
    def test_committee(self):
        committee = Committee(
            name="Change Advisory Board",
            purpose="Approve platform changes",
            cadence=CommitteeCadence.BIWEEKLY,
            chair="Change Manager",
            members=["Platform Admin", "App Owner"],
        )
        assert committee.cadence == CommitteeCadence.BIWEEKLY
        assert len(committee.members) == 2
    
    def test_operating_model(self):
        model = OperatingModel(
            vision="Enable business through governed platform",
            principles=["Enable, not restrict", "Automate enforcement"],
            current_maturity=GovernanceMaturity.INITIAL,
            target_maturity=GovernanceMaturity.MANAGED,
        )
        assert model.current_maturity == GovernanceMaturity.INITIAL
        assert len(model.principles) == 2
    
    def test_policy(self):
        policy = Policy(
            id="POL-001",
            name="Naming Conventions",
            category=PolicyCategory.NAMING,
            purpose="Ensure consistent naming across platform",
            scope="All Jira projects and Confluence spaces",
            policy_statement="All objects must follow naming conventions",
            guardrails=["Project keys: DEPT-NAME", "Spaces: TEAM-PURPOSE"],
            owner="Platform Admin",
        )
        assert policy.category == PolicyCategory.NAMING
        assert len(policy.guardrails) == 2
    
    def test_guardrail(self):
        guardrail = Guardrail(
            id="GR-001",
            name="Project Key Format",
            category=PolicyCategory.NAMING,
            description="Project keys must follow standard format",
            rule_type="naming",
            rule_definition="^[A-Z]{2,4}-[A-Z]+$",
            enforcement="automated",
            good_examples=["IT-HELPDESK", "ENG-PLATFORM"],
            bad_examples=["helpdesk", "IT_Help"],
        )
        assert guardrail.enforcement == "automated"
        assert len(guardrail.good_examples) == 2
    
    def test_workflow_standard(self):
        workflow = WorkflowStandard(
            name="Software Development",
            description="Standard workflow for software teams",
            use_case="Scrum/Kanban teams",
            statuses=["Backlog", "In Progress", "Done"],
        )
        assert len(workflow.statuses) == 3
    
    def test_field_standard(self):
        field = FieldStandard(
            name="Department",
            field_type="select",
            description="Business department",
            context="global",
            required=True,
        )
        assert field.required is True
    
    def test_sla_standard(self):
        sla = SLAStandard(
            name="Time to First Response",
            metric="time_to_first_response",
            goals_by_priority={
                "Critical": "15m",
                "High": "1h",
                "Medium": "4h",
                "Low": "8h",
            },
        )
        assert sla.goals_by_priority["Critical"] == "15m"
    
    def test_project_template(self):
        template = ProjectTemplate(
            name="Software Team",
            key_pattern="TEAM-{name}",
            project_type="software",
            workflow="Software Development",
            issue_types=["Epic", "Story", "Bug", "Task"],
        )
        assert len(template.issue_types) == 4
    
    def test_runbook_step(self):
        step = RunbookStep(
            step_number=1,
            title="Access Admin Console",
            action="Navigate to admin.atlassian.com",
            expected_result="Admin dashboard displayed",
        )
        assert step.step_number == 1
    
    def test_runbook(self):
        runbook = Runbook(
            id="RB-001",
            name="User Provisioning",
            category="user_management",
            purpose="Add new user to platform",
            prerequisites=["SSO configured", "Manager approval"],
            steps=[
                RunbookStep(
                    step_number=1,
                    title="Open Directory",
                    action="Navigate to Users",
                    expected_result="User list displayed",
                )
            ],
            verification=["User can log in", "User has correct access"],
        )
        assert len(runbook.steps) == 1
        assert len(runbook.verification) == 2
    
    def test_kpi(self):
        kpi = KPI(
            id="KPI-001",
            name="Active User Rate",
            category="adoption",
            formula="(active_users_30d / licensed_users) * 100",
            target=">80%",
            warning_threshold="70-80%",
            critical_threshold="<70%",
            measurement_frequency="monthly",
            owner="Platform Owner",
        )
        assert kpi.target == ">80%"
    
    def test_kpi_dashboard(self):
        dashboard = KPIDashboard(
            name="Governance Dashboard",
            kpis=[
                KPI(
                    id="KPI-001",
                    name="Active User Rate",
                    category="adoption",
                    formula="...",
                    target=">80%",
                    warning_threshold="70%",
                    critical_threshold="60%",
                    measurement_frequency="monthly",
                    owner="Admin",
                )
            ],
            review_cadence="monthly",
        )
        assert len(dashboard.kpis) == 1
    
    def test_governance_handbook(self):
        handbook = GovernanceHandbook(
            client_name="Acme Corp",
            version="1.0",
            status="draft",
        )
        assert handbook.client_name == "Acme Corp"
        assert handbook.title == "Atlassian Governance Handbook"


class TestA4State:
    """Test A4 state management."""
    
    def test_state_initialization(self):
        state: A4State = {
            "agent_id": "a4",
            "workflow_id": "test",
            "client_name": "Acme Corp",
            "status": AgentStatus.IDLE,
            "messages": [],
            "artifacts": [],
            "decisions": [],
            "operating_model_complete": False,
            "policies_complete": False,
            "standards_complete": False,
            "runbooks_complete": False,
            "kpis_complete": False,
            "handbook_drafted": False,
        }
        
        assert state["agent_id"] == "a4"
        assert state["operating_model_complete"] is False


class TestA4Integration:
    """Integration tests for A4 (require API key)."""
    
    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Requires API key")
    async def test_design_operating_model(self):
        agent = create_a4_agent()
        
        state: A4State = {
            "agent_id": "a4",
            "workflow_id": "test_model",
            "client_name": "Test Corp",
            "current_task": "design_operating_model",
            "messages": [],
            "artifacts": [],
            "decisions": [],
            "status": AgentStatus.RUNNING,
        }
        
        result = await agent.run(state)
        
        assert result.get("operating_model_complete") is True
        assert len(result.get("artifacts", [])) > 0
    
    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Requires API key")
    async def test_full_wp4(self):
        agent = create_a4_agent()
        
        state: A4State = {
            "agent_id": "a4",
            "workflow_id": "test_wp4",
            "client_name": "Test Corp",
            "engagement_id": "WP4-TEST-001",
            "current_task": "full_wp4",
            "messages": [],
            "artifacts": [],
            "decisions": [],
            "status": AgentStatus.RUNNING,
        }
        
        result = await agent.run(state)
        
        assert result.get("handbook_drafted") is True
        assert len(result.get("artifacts", [])) >= 6
