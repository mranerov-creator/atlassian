"""
Tests for A3 Assessment Analyst Agent
"""
import pytest

from agents.a3_assessment import (
    A3AssessmentAgent,
    A3State,
    create_a3_agent,
    # Enums
    RiskLevel,
    ImpactLevel,
    EffortLevel,
    HotspotCategory,
    ProductType,
    DeploymentType,
    # Models
    InstanceInfo,
    UserMetrics,
    JiraMetrics,
    ConfluenceMetrics,
    AppInfo,
    IntegrationInfo,
    VolumetricsReport,
    Hotspot,
    HotspotMap,
    PlanAction,
    Plan306090,
    WP1Report,
)
from core.orchestrator import AgentStatus


class TestA3AssessmentAgent:
    """Test suite for A3 Assessment agent."""
    
    def test_agent_creation(self):
        """Test agent can be created."""
        agent = create_a3_agent()
        
        assert agent.config.id == "a3"
        assert agent.config.name == "Assessment Analyst"
        assert "a2" in agent.config.allowed_handoffs
        assert "a4" in agent.config.allowed_handoffs
        assert "a6" in agent.config.allowed_handoffs
    
    def test_system_prompt_contains_rules(self):
        """Test system prompt contains required elements."""
        agent = create_a3_agent()
        prompt = agent.system_prompt()
        
        assert "evidence" in prompt.lower()
        assert "hotspot" in prompt.lower()
        assert "30/60/90" in prompt or "30-60-90" in prompt.lower()
        assert "quick win" in prompt.lower()
    
    def test_model_tier_is_standard(self):
        """Test agent uses standard model tier."""
        agent = create_a3_agent()
        from core.llm import ModelTier
        
        assert agent.config.model_tier == ModelTier.STANDARD


class TestA3Models:
    """Test A3 Pydantic models."""
    
    def test_instance_info(self):
        """Test InstanceInfo model."""
        instance = InstanceInfo(
            name="Production",
            url="https://acme.atlassian.net",
            deployment_type=DeploymentType.CLOUD,
            version="Latest",
            products=[ProductType.JIRA_SOFTWARE, ProductType.CONFLUENCE],
        )
        
        assert instance.name == "Production"
        assert instance.deployment_type == DeploymentType.CLOUD
        assert len(instance.products) == 2
    
    def test_user_metrics(self):
        """Test UserMetrics model."""
        users = UserMetrics(
            total_users=500,
            active_users_30d=350,
            licensed_users=500,
            admin_users=10,
            sso_enabled=True,
        )
        
        assert users.total_users == 500
        assert users.sso_enabled is True
    
    def test_jira_metrics(self):
        """Test JiraMetrics model."""
        jira = JiraMetrics(
            projects_count=50,
            active_projects=35,
            issues_total=25000,
            workflows_count=20,
            custom_fields_count=150,
        )
        
        assert jira.projects_count == 50
        assert jira.custom_fields_count == 150
    
    def test_app_info(self):
        """Test AppInfo model."""
        app = AppInfo(
            app_key="com.vendor.app",
            app_name="Super App",
            vendor="Vendor Inc",
            users_count=200,
            annual_cost=5000.0,
            criticality="high",
            migration_status="compatible",
        )
        
        assert app.app_name == "Super App"
        assert app.criticality == "high"
    
    def test_hotspot(self):
        """Test Hotspot model."""
        hotspot = Hotspot(
            id="HSP-001",
            title="Excessive custom fields",
            description="150 custom fields identified, 60% unused",
            category=HotspotCategory.TECHNICAL_DEBT,
            impact=ImpactLevel.MEDIUM,
            effort=EffortLevel.MEDIUM,
            risk=RiskLevel.HIGH,
            priority_score=75,
            recommendation="Audit and archive unused fields",
            quick_win=True,
            evidence=["Custom field export shows 90 fields with 0 values"],
        )
        
        assert hotspot.id == "HSP-001"
        assert hotspot.category == HotspotCategory.TECHNICAL_DEBT
        assert hotspot.quick_win is True
        assert hotspot.priority_score == 75
    
    def test_hotspot_map(self):
        """Test HotspotMap model."""
        hotspots = [
            Hotspot(
                id="HSP-001",
                title="Test",
                description="Test hotspot",
                category=HotspotCategory.GOVERNANCE,
                impact=ImpactLevel.HIGH,
                effort=EffortLevel.LOW,
                risk=RiskLevel.HIGH,
                priority_score=85,
                recommendation="Fix it",
            )
        ]
        
        heatmap = HotspotMap(
            hotspots=hotspots,
            critical_count=0,
            high_count=1,
            health_score=75,
        )
        
        assert len(heatmap.hotspots) == 1
        assert heatmap.high_count == 1
        assert heatmap.health_score == 75
    
    def test_plan_action(self):
        """Test PlanAction model."""
        action = PlanAction(
            id="A-30-001",
            title="Implement project naming convention",
            description="Define and communicate project naming standards",
            phase="30",
            week=1,
            duration_days=3,
            category="governance",
            priority="high",
            addresses_hotspots=["HSP-001"],
        )
        
        assert action.phase == "30"
        assert action.priority == "high"
        assert "HSP-001" in action.addresses_hotspots


class TestA3UtilityFunctions:
    """Test A3 utility functions."""
    
    def test_calculate_health_score_no_hotspots(self):
        """Test health score with no hotspots."""
        agent = create_a3_agent()
        score = agent.calculate_health_score([])
        
        assert score == 50  # Neutral
    
    def test_calculate_health_score_with_hotspots(self):
        """Test health score calculation."""
        agent = create_a3_agent()
        
        hotspots = [
            Hotspot(
                id="HSP-001",
                title="Critical issue",
                description="Test",
                category=HotspotCategory.SECURITY,
                impact=ImpactLevel.HIGH,
                effort=EffortLevel.HIGH,
                risk=RiskLevel.CRITICAL,
                priority_score=95,
                recommendation="Fix immediately",
            ),
            Hotspot(
                id="HSP-002",
                title="Minor issue",
                description="Test",
                category=HotspotCategory.GOVERNANCE,
                impact=ImpactLevel.LOW,
                effort=EffortLevel.LOW,
                risk=RiskLevel.LOW,
                priority_score=25,
                recommendation="Consider fixing",
            ),
        ]
        
        score = agent.calculate_health_score(hotspots)
        
        # Should be < 100 due to penalties
        assert score < 100
        assert score >= 0
    
    def test_identify_quick_wins(self):
        """Test quick wins identification."""
        agent = create_a3_agent()
        
        hotspots = [
            Hotspot(
                id="HSP-001",
                title="Quick win",
                description="Easy fix",
                category=HotspotCategory.GOVERNANCE,
                impact=ImpactLevel.MEDIUM,
                effort=EffortLevel.LOW,
                risk=RiskLevel.MEDIUM,
                priority_score=70,
                recommendation="Do it",
                quick_win=True,
            ),
            Hotspot(
                id="HSP-002",
                title="Complex fix",
                description="Hard work",
                category=HotspotCategory.ARCHITECTURE,
                impact=ImpactLevel.HIGH,
                effort=EffortLevel.HIGH,
                risk=RiskLevel.HIGH,
                priority_score=80,
                recommendation="Plan carefully",
                quick_win=False,
            ),
        ]
        
        quick_wins = agent.identify_quick_wins(hotspots)
        
        assert len(quick_wins) == 1
        assert quick_wins[0].id == "HSP-001"
    
    def test_prioritize_hotspots(self):
        """Test hotspot prioritization."""
        agent = create_a3_agent()
        
        hotspots = [
            Hotspot(
                id="HSP-001",
                title="Low priority",
                description="Test",
                category=HotspotCategory.GOVERNANCE,
                impact=ImpactLevel.LOW,
                effort=EffortLevel.LOW,
                risk=RiskLevel.LOW,
                priority_score=30,
                recommendation="Maybe",
            ),
            Hotspot(
                id="HSP-002",
                title="High priority",
                description="Test",
                category=HotspotCategory.SECURITY,
                impact=ImpactLevel.HIGH,
                effort=EffortLevel.LOW,
                risk=RiskLevel.CRITICAL,
                priority_score=95,
                recommendation="Now",
            ),
        ]
        
        sorted_hotspots = agent.prioritize_hotspots(hotspots)
        
        assert sorted_hotspots[0].id == "HSP-002"
        assert sorted_hotspots[1].id == "HSP-001"


class TestA3State:
    """Test A3 state management."""
    
    def test_state_initialization(self):
        """Test A3State can be initialized."""
        state: A3State = {
            "agent_id": "a3",
            "workflow_id": "test",
            "client_name": "Acme Corp",
            "status": AgentStatus.IDLE,
            "messages": [],
            "artifacts": [],
            "decisions": [],
            "evidence_collected": False,
            "analysis_complete": False,
            "plan_generated": False,
            "report_drafted": False,
        }
        
        assert state["agent_id"] == "a3"
        assert state["client_name"] == "Acme Corp"
        assert state["evidence_collected"] is False


class TestA3Integration:
    """Integration tests for A3 (require API key)."""
    
    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Requires API key")
    async def test_collect_evidence(self):
        """Test evidence collection."""
        agent = create_a3_agent()
        
        state: A3State = {
            "agent_id": "a3",
            "workflow_id": "test_evidence",
            "client_name": "Test Corp",
            "input_data": {
                "instance_url": "https://test.atlassian.net",
                "products": ["jira_software"],
            },
            "current_task": "collect_evidence",
            "messages": [],
            "artifacts": [],
            "decisions": [],
            "status": AgentStatus.RUNNING,
        }
        
        result = await agent.run(state)
        
        assert result.get("evidence_collected") is True
        assert len(result.get("artifacts", [])) > 0
    
    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Requires API key")
    async def test_full_wp1(self):
        """Test full WP1 execution."""
        agent = create_a3_agent()
        
        state: A3State = {
            "agent_id": "a3",
            "workflow_id": "test_wp1",
            "client_name": "Test Corp",
            "engagement_id": "WP1-TEST-001",
            "current_task": "full_wp1",
            "messages": [],
            "artifacts": [],
            "decisions": [],
            "status": AgentStatus.RUNNING,
        }
        
        result = await agent.run(state)
        
        assert result.get("report_drafted") is True
        assert len(result.get("artifacts", [])) >= 4  # Evidence, hotspots, plan, report
