"""
Tests for A2 Solution Architect Agent
"""
import pytest

from agents.a2_architect import (
    A2ArchitectAgent,
    A2State,
    create_a2_agent,
    # Enums
    DeploymentModel,
    InstanceStrategy,
    ProductTier,
    IntegrationType,
    MigrationApproach,
    DataResidency,
    ArchitecturePattern,
    # Models
    CurrentInstance,
    CurrentIntegration,
    CurrentStateAssessment,
    TargetInstance,
    TargetIntegration,
    ProductConfiguration,
    SecurityArchitecture,
    TargetStateDesign,
    ArchitectureOption,
    ArchitectureComparison,
    MigrationItem,
    MigrationWave,
    MigrationPlan,
    TechnicalDecision,
    DecisionLog,
    LicenseRecommendation,
    SizingRecommendation,
    ArchitectureDocument,
)
from core.orchestrator import AgentStatus


class TestA2ArchitectAgent:
    """Test suite for A2 Architect agent."""
    
    def test_agent_creation(self):
        """Test agent can be created."""
        agent = create_a2_agent()
        
        assert agent.config.id == "a2"
        assert agent.config.name == "Solution Architect"
        assert "a3" in agent.config.allowed_handoffs
        assert "a4" in agent.config.allowed_handoffs
        assert "a5" in agent.config.allowed_handoffs
        assert "a6" in agent.config.allowed_handoffs
    
    def test_system_prompt_contains_rules(self):
        """Test system prompt contains required elements."""
        agent = create_a2_agent()
        prompt = agent.system_prompt()
        
        assert "architecture" in prompt.lower()
        assert "migration" in prompt.lower()
        assert "sizing" in prompt.lower()
        assert "ADR" in prompt or "decision" in prompt.lower()


class TestA2Enums:
    """Test A2 enums."""
    
    def test_deployment_model(self):
        assert DeploymentModel.CLOUD == "cloud"
        assert DeploymentModel.DATA_CENTER == "data_center"
    
    def test_instance_strategy(self):
        assert InstanceStrategy.SINGLE == "single_instance"
        assert InstanceStrategy.FEDERATED == "federated"
    
    def test_product_tier(self):
        assert ProductTier.STANDARD == "standard"
        assert ProductTier.ENTERPRISE == "enterprise"
    
    def test_migration_approach(self):
        assert MigrationApproach.LIFT_AND_SHIFT == "lift_and_shift"
        assert MigrationApproach.REFACTOR == "refactor"


class TestA2Models:
    """Test A2 Pydantic models."""
    
    def test_current_instance(self):
        instance = CurrentInstance(
            name="Production Jira",
            url="https://acme.atlassian.net",
            deployment=DeploymentModel.CLOUD,
            products=["Jira Software", "Confluence"],
            users=500,
            projects=150,
        )
        assert instance.deployment == DeploymentModel.CLOUD
        assert instance.users == 500
    
    def test_current_integration(self):
        integration = CurrentIntegration(
            name="Jira-ServiceNow",
            source="Jira",
            target="ServiceNow",
            integration_type=IntegrationType.API,
            criticality="high",
        )
        assert integration.integration_type == IntegrationType.API
    
    def test_current_state_assessment(self):
        assessment = CurrentStateAssessment(
            total_users=500,
            total_projects=150,
            pain_points=["Performance issues", "Governance gaps"],
        )
        assert assessment.total_users == 500
        assert len(assessment.pain_points) == 2
    
    def test_target_instance(self):
        instance = TargetInstance(
            name="Enterprise Jira",
            purpose="Consolidated platform",
            deployment=DeploymentModel.CLOUD,
            products=["Jira Software", "Jira Service Management"],
            tier=ProductTier.PREMIUM,
            data_residency=DataResidency.EU,
            estimated_users=1000,
        )
        assert instance.tier == ProductTier.PREMIUM
        assert instance.data_residency == DataResidency.EU
    
    def test_security_architecture(self):
        security = SecurityArchitecture(
            authentication="SAML SSO",
            identity_provider="Okta",
            mfa_required=True,
            compliance_frameworks=["SOC2", "ISO27001"],
        )
        assert security.mfa_required is True
        assert len(security.compliance_frameworks) == 2
    
    def test_target_state_design(self):
        design = TargetStateDesign(
            instance_strategy=InstanceStrategy.SINGLE,
            pattern=ArchitecturePattern.CENTRALIZED,
            design_principles=["Simplicity", "Security by design"],
        )
        assert design.instance_strategy == InstanceStrategy.SINGLE
        assert len(design.design_principles) == 2
    
    def test_architecture_option(self):
        option = ArchitectureOption(
            id="opt-a",
            name="Conservative",
            description="Minimal change approach",
            instance_strategy=InstanceStrategy.SINGLE,
            pattern=ArchitecturePattern.CENTRALIZED,
            pros=["Low risk", "Fast implementation"],
            cons=["Technical debt remains"],
            score_scalability=4,
            score_simplicity=5,
            score_cost=4,
            score_security=3,
            score_governance=3,
            total_score=19,
            recommended=True,
        )
        assert option.total_score == 19
        assert option.recommended is True
    
    def test_migration_item(self):
        item = MigrationItem(
            id="mig-001",
            name="IT-HELPDESK",
            source="server.acme.com",
            target="acme.atlassian.net",
            item_type="project",
            approach=MigrationApproach.REPLATFORM,
            wave=1,
        )
        assert item.approach == MigrationApproach.REPLATFORM
    
    def test_migration_wave(self):
        wave = MigrationWave(
            wave_number=1,
            name="Pilot",
            description="Initial pilot migration",
            items=[
                MigrationItem(
                    id="mig-001",
                    name="Pilot Project",
                    source="old",
                    target="new",
                    item_type="project",
                    approach=MigrationApproach.REPLATFORM,
                    wave=1,
                )
            ],
            success_criteria=["All issues migrated", "Users can access"],
        )
        assert wave.wave_number == 1
        assert len(wave.items) == 1
    
    def test_technical_decision(self):
        decision = TechnicalDecision(
            id="ADR-001",
            title="Use Single Instance Strategy",
            status="accepted",
            context="Need to consolidate multiple instances",
            decision="We will use a single Jira Cloud instance",
            consequences=["Simpler governance", "Migration complexity"],
            alternatives_considered=["Multi-instance", "Federation"],
        )
        assert decision.status == "accepted"
        assert len(decision.alternatives_considered) == 2
    
    def test_license_recommendation(self):
        license_rec = LicenseRecommendation(
            product="Jira Software",
            tier=ProductTier.PREMIUM,
            users=500,
            annual_cost_eur=60000.0,
            rationale="Advanced features required",
            features_used=["Advanced Roadmaps", "Sandbox"],
        )
        assert license_rec.annual_cost_eur == 60000.0
    
    def test_sizing_recommendation(self):
        sizing = SizingRecommendation(
            client_name="Acme Corp",
            total_annual_cost_eur=100000.0,
            apps_budget_eur=20000.0,
            implementation_budget_eur=50000.0,
            total_first_year_eur=170000.0,
        )
        assert sizing.total_first_year_eur == 170000.0
    
    def test_architecture_document(self):
        doc = ArchitectureDocument(
            client_name="Acme Corp",
            version="1.0",
            status="draft",
            executive_summary="Consolidate to single cloud instance",
        )
        assert doc.client_name == "Acme Corp"
        assert doc.title == "Solution Architecture Document"


class TestA2State:
    """Test A2 state management."""
    
    def test_state_initialization(self):
        state: A2State = {
            "agent_id": "a2",
            "workflow_id": "test",
            "client_name": "Acme Corp",
            "status": AgentStatus.IDLE,
            "messages": [],
            "artifacts": [],
            "decisions": [],
            "current_state_complete": False,
            "target_designed": False,
            "options_evaluated": False,
            "migration_planned": False,
            "sizing_complete": False,
            "document_drafted": False,
        }
        
        assert state["agent_id"] == "a2"
        assert state["current_state_complete"] is False


class TestA2Integration:
    """Integration tests for A2 (require API key)."""
    
    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Requires API key")
    async def test_assess_current_state(self):
        agent = create_a2_agent()
        
        state: A2State = {
            "agent_id": "a2",
            "workflow_id": "test_current",
            "client_name": "Test Corp",
            "wp1_findings": {"total_users": 500},
            "current_task": "assess_current_state",
            "messages": [],
            "artifacts": [],
            "decisions": [],
            "status": AgentStatus.RUNNING,
        }
        
        result = await agent.run(state)
        
        assert result.get("current_state_complete") is True
        assert len(result.get("artifacts", [])) > 0
    
    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Requires API key")
    async def test_full_architecture(self):
        agent = create_a2_agent()
        
        state: A2State = {
            "agent_id": "a2",
            "workflow_id": "test_arch",
            "client_name": "Test Corp",
            "engagement_id": "ARCH-TEST-001",
            "current_task": "full_architecture",
            "messages": [],
            "artifacts": [],
            "decisions": [],
            "status": AgentStatus.RUNNING,
        }
        
        result = await agent.run(state)
        
        assert result.get("document_drafted") is True
        assert len(result.get("artifacts", [])) >= 5
