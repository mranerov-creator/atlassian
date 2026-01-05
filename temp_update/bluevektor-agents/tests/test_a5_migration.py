"""
Tests for A5 Migration Factory Agent
"""
import pytest

from agents.a5_migration import (
    A5MigrationAgent,
    A5State,
    create_a5_agent,
    # Enums
    MigrationType,
    MigrationPhase,
    WaveStatus,
    ItemStatus,
    ValidationStatus,
    CleanupAction,
    RiskLevel,
    # Models
    SourceSystem,
    TargetSystem,
    ProjectMigrationItem,
    SpaceMigrationItem,
    UserMigrationItem,
    AppMigrationItem,
    WaveChecklist,
    Wave,
    ValidationCheck,
    ValidationReport,
    CommunicationTemplate,
    CommunicationPlan,
    MigrationRisk,
    MigrationPlan,
    MigrationTask,
    MigrationLog,
    ExecutionDashboard,
    RunbookStep,
    MigrationRunbook,
)
from core.orchestrator import AgentStatus


class TestA5MigrationAgent:
    """Test suite for A5 Migration agent."""
    
    def test_agent_creation(self):
        """Test agent can be created."""
        agent = create_a5_agent()
        
        assert agent.config.id == "a5"
        assert agent.config.name == "Migration Factory"
        assert "a2" in agent.config.allowed_handoffs
        assert "a4" in agent.config.allowed_handoffs
        assert "a6" in agent.config.allowed_handoffs
    
    def test_system_prompt_contains_rules(self):
        """Test system prompt contains required elements."""
        agent = create_a5_agent()
        prompt = agent.system_prompt()
        
        assert "migration" in prompt.lower()
        assert "wave" in prompt.lower()
        assert "validation" in prompt.lower()
        assert "JCMA" in prompt or "migration assistant" in prompt.lower()


class TestA5Enums:
    """Test A5 enums."""
    
    def test_migration_type(self):
        assert MigrationType.SERVER_TO_CLOUD == "server_to_cloud"
        assert MigrationType.CLOUD_TO_CLOUD == "cloud_to_cloud"
    
    def test_migration_phase(self):
        assert MigrationPhase.PLANNING == "planning"
        assert MigrationPhase.HYPERCARE == "hypercare"
    
    def test_wave_status(self):
        assert WaveStatus.PLANNED == "planned"
        assert WaveStatus.COMPLETED == "completed"
    
    def test_item_status(self):
        assert ItemStatus.NOT_STARTED == "not_started"
        assert ItemStatus.MIGRATED == "migrated"


class TestA5Models:
    """Test A5 Pydantic models."""
    
    def test_source_system(self):
        source = SourceSystem(
            name="Production Server",
            type="server",
            url="https://jira.acme.com",
            version="8.20.0",
            products=["Jira Software", "Confluence"],
            total_projects=150,
            total_users=500,
        )
        assert source.type == "server"
        assert source.total_projects == 150
    
    def test_target_system(self):
        target = TargetSystem(
            name="Cloud Instance",
            type="cloud",
            url="https://acme.atlassian.net",
            tier="premium",
            data_residency="eu",
            sso_configured=True,
        )
        assert target.tier == "premium"
        assert target.sso_configured is True
    
    def test_project_migration_item(self):
        project = ProjectMigrationItem(
            id="10001",
            key="IT-HD",
            name="IT Helpdesk",
            project_type="service_desk",
            issue_count=5000,
            attachment_size_mb=2048,
            wave=2,
            priority=1,
            status=ItemStatus.NOT_STARTED,
        )
        assert project.wave == 2
        assert project.issue_count == 5000
    
    def test_space_migration_item(self):
        space = SpaceMigrationItem(
            id="20001",
            key="ENG",
            name="Engineering",
            space_type="global",
            page_count=500,
            wave=1,
        )
        assert space.page_count == 500
    
    def test_user_migration_item(self):
        user = UserMigrationItem(
            username="jdoe",
            email="jdoe@acme.com",
            display_name="John Doe",
            groups=["jira-users", "confluence-users"],
            is_admin=False,
        )
        assert len(user.groups) == 2
    
    def test_app_migration_item(self):
        app = AppMigrationItem(
            app_key="com.tempoplugin.tempo-planner",
            app_name="Tempo Planner",
            vendor="Tempo",
            cloud_compatible=True,
            migration_path="migrate_data",
        )
        assert app.migration_path == "migrate_data"
    
    def test_wave_checklist(self):
        checklist = WaveChecklist(
            item="User mapping validated",
            category="pre_migration",
            responsible="Migration Lead",
            completed=True,
        )
        assert checklist.completed is True
    
    def test_wave(self):
        wave = Wave(
            id="wave-1",
            number=1,
            name="Pilot",
            description="Pilot migration wave",
            projects=["IT-HD", "IT-OPS"],
            users=["jdoe", "asmith"],
            status=WaveStatus.PLANNED,
            success_criteria=["All data migrated", "Users can access"],
        )
        assert wave.number == 1
        assert len(wave.projects) == 2
    
    def test_validation_check(self):
        check = ValidationCheck(
            id="val-001",
            name="Issue Count Match",
            category="data_integrity",
            description="Verify issue counts match",
            automated=True,
            status=ValidationStatus.PASSED,
            expected_value="5000",
            actual_value="5000",
            passed=True,
        )
        assert check.passed is True
    
    def test_validation_report(self):
        report = ValidationReport(
            wave_id="wave-1",
            total_checks=10,
            passed_checks=9,
            failed_checks=1,
            pass_rate=90.0,
            overall_status=ValidationStatus.PARTIAL,
        )
        assert report.pass_rate == 90.0
    
    def test_communication_template(self):
        template = CommunicationTemplate(
            id="comm-001",
            name="Pre-Migration Announcement",
            type="announcement",
            audience="all_users",
            subject="Upcoming Migration",
            body="Dear Team...",
            send_timing="2 weeks before",
        )
        assert template.audience == "all_users"
    
    def test_migration_risk(self):
        risk = MigrationRisk(
            id="risk-001",
            description="Data loss during migration",
            level=RiskLevel.HIGH,
            probability="low",
            impact="high",
            mitigation="Multiple backups, validation checks",
            owner="Migration Lead",
        )
        assert risk.level == RiskLevel.HIGH
    
    def test_migration_plan(self):
        plan = MigrationPlan(
            id="mig-001",
            name="Acme Cloud Migration",
            client_name="Acme Corp",
            migration_type=MigrationType.SERVER_TO_CLOUD,
            source=SourceSystem(
                name="Source",
                type="server",
                url="https://jira.acme.com",
            ),
            target=TargetSystem(
                name="Target",
                type="cloud",
                url="https://acme.atlassian.net",
            ),
            total_projects=150,
            total_users=500,
        )
        assert plan.migration_type == MigrationType.SERVER_TO_CLOUD
        assert plan.total_projects == 150
    
    def test_migration_task(self):
        task = MigrationTask(
            id="task-001",
            name="Migrate IT-HD project",
            description="Full migration of IT Helpdesk",
            wave_id="wave-1",
            status="pending",
        )
        assert task.status == "pending"
    
    def test_migration_log(self):
        log = MigrationLog(
            timestamp="2025-01-05T10:00:00Z",
            wave_id="wave-1",
            item_type="project",
            item_id="IT-HD",
            action="migrate",
            status="completed",
            message="Project migrated successfully",
        )
        assert log.status == "completed"
    
    def test_execution_dashboard(self):
        dashboard = ExecutionDashboard(
            migration_id="mig-001",
            current_phase=MigrationPhase.MIGRATION,
            overall_progress=45,
            total_waves=5,
            completed_waves=2,
            projects_migrated=60,
            projects_total=150,
        )
        assert dashboard.overall_progress == 45
        assert dashboard.completed_waves == 2
    
    def test_runbook_step(self):
        step = RunbookStep(
            number=1,
            title="Open JCMA",
            description="Access the migration assistant",
            action="Navigate to Settings > System > Migration Assistant",
            expected_result="Migration dashboard displayed",
            estimated_duration_min=5,
        )
        assert step.number == 1
    
    def test_migration_runbook(self):
        runbook = MigrationRunbook(
            id="rb-001",
            name="Project Migration Runbook",
            description="Step-by-step project migration",
            migration_type=MigrationType.SERVER_TO_CLOUD,
            prerequisites=["JCMA installed", "User mapping complete"],
            tools_required=["JCMA", "Browser"],
        )
        assert len(runbook.prerequisites) == 2


class TestA5State:
    """Test A5 state management."""
    
    def test_state_initialization(self):
        state: A5State = {
            "agent_id": "a5",
            "workflow_id": "test",
            "client_name": "Acme Corp",
            "migration_type": MigrationType.SERVER_TO_CLOUD,
            "status": AgentStatus.IDLE,
            "messages": [],
            "artifacts": [],
            "decisions": [],
            "inventory_complete": False,
            "waves_planned": False,
            "runbooks_created": False,
            "communications_ready": False,
            "execution_started": False,
            "migration_complete": False,
        }
        
        assert state["agent_id"] == "a5"
        assert state["migration_type"] == MigrationType.SERVER_TO_CLOUD


class TestA5Integration:
    """Integration tests for A5 (require API key)."""
    
    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Requires API key")
    async def test_create_inventory(self):
        agent = create_a5_agent()
        
        state: A5State = {
            "agent_id": "a5",
            "workflow_id": "test_inv",
            "client_name": "Test Corp",
            "migration_type": MigrationType.SERVER_TO_CLOUD,
            "current_task": "create_inventory",
            "messages": [],
            "artifacts": [],
            "decisions": [],
            "status": AgentStatus.RUNNING,
        }
        
        result = await agent.run(state)
        
        assert result.get("inventory_complete") is True
        assert len(result.get("artifacts", [])) > 0
    
    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Requires API key")
    async def test_full_migration_planning(self):
        agent = create_a5_agent()
        
        state: A5State = {
            "agent_id": "a5",
            "workflow_id": "test_wp2",
            "client_name": "Test Corp",
            "engagement_id": "WP2-TEST-001",
            "migration_type": MigrationType.SERVER_TO_CLOUD,
            "current_task": "full_wp2",
            "messages": [],
            "artifacts": [],
            "decisions": [],
            "status": AgentStatus.RUNNING,
        }
        
        result = await agent.run(state)
        
        assert len(result.get("artifacts", [])) >= 5
