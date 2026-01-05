"""
Tests for A0 CEO/Strategist Agent
"""
import pytest

from agents.a0_strategist import (
    A0StrategistAgent,
    A0State,
    create_a0_agent,
    # Enums
    MarketSegment,
    EngagementType,
    PricingModel,
    DealStage,
    Priority,
    StrategicInitiative,
    # Models
    CompetitorProfile,
    MarketPosition,
    TargetPersona,
    WorkPackagePricing,
    PricingStrategy,
    DealPricing,
    Opportunity,
    PipelineAnalysis,
    PortfolioHealth,
    StrategicGoal,
    QuarterlyPlan,
    StrategicDecision,
    CompetitiveIntel,
)
from core.orchestrator import AgentStatus


class TestA0StrategistAgent:
    """Test suite for A0 Strategist agent."""
    
    def test_agent_creation(self):
        """Test agent can be created."""
        agent = create_a0_agent()
        
        assert agent.config.id == "a0"
        assert agent.config.name == "CEO / Strategist"
        assert "a1" in agent.config.allowed_handoffs
        assert "a6" in agent.config.allowed_handoffs
    
    def test_system_prompt_contains_rules(self):
        """Test system prompt contains required elements."""
        agent = create_a0_agent()
        prompt = agent.system_prompt()
        
        assert "pricing" in prompt.lower()
        assert "competitive" in prompt.lower()
        assert "margin" in prompt.lower()
        assert "discount" in prompt.lower()


class TestA0Enums:
    """Test A0 enums."""
    
    def test_market_segment(self):
        assert MarketSegment.ENTERPRISE == "enterprise"
        assert MarketSegment.MID_MARKET == "mid_market"
        assert MarketSegment.SMB == "smb"
    
    def test_engagement_type(self):
        assert EngagementType.ASSESSMENT == "assessment"
        assert EngagementType.MIGRATION == "migration"
        assert EngagementType.GOVERNANCE == "governance"
    
    def test_pricing_model(self):
        assert PricingModel.FIXED_PRICE == "fixed_price"
        assert PricingModel.VALUE_BASED == "value_based"
        assert PricingModel.RETAINER == "retainer"
    
    def test_deal_stage(self):
        assert DealStage.LEAD == "lead"
        assert DealStage.PROPOSAL == "proposal"
        assert DealStage.CLOSED_WON == "closed_won"
    
    def test_priority(self):
        assert Priority.CRITICAL == "critical"
        assert Priority.HIGH == "high"
    
    def test_strategic_initiative(self):
        assert StrategicInitiative.MARKET_EXPANSION == "market_expansion"
        assert StrategicInitiative.PARTNERSHIP == "partnership"


class TestA0Models:
    """Test A0 Pydantic models."""
    
    def test_competitor_profile(self):
        competitor = CompetitorProfile(
            name="Accenture",
            type="big4",
            strengths=["Brand", "Scale"],
            weaknesses=["Expensive", "Slow"],
            pricing_position="premium",
            target_segments=[MarketSegment.ENTERPRISE],
        )
        assert competitor.pricing_position == "premium"
    
    def test_market_position(self):
        position = MarketPosition(
            tagline="Evidence-first transformation",
            value_proposition="Enterprise expertise with startup agility",
            target_segments=[MarketSegment.MID_MARKET, MarketSegment.ENTERPRISE],
            key_differentiators=["AI-augmented", "Governance built-in"],
        )
        assert len(position.target_segments) == 2
    
    def test_target_persona(self):
        persona = TargetPersona(
            name="IT Director",
            title="IT Director",
            department="IT",
            pain_points=["Tool sprawl", "No governance"],
            goals=["Modernize stack", "Reduce costs"],
        )
        assert len(persona.pain_points) == 2
    
    def test_work_package_pricing(self):
        wp = WorkPackagePricing(
            wp_id="WP1",
            name="Diagnostic",
            description="AS-IS assessment",
            base_price_eur=12000.0,
            base_days=8,
            min_days=5,
            max_days=12,
            day_rate_eur=1500.0,
        )
        assert wp.base_price_eur == 12000.0
    
    def test_pricing_strategy(self):
        strategy = PricingStrategy(
            consultant_day_rate=1200.0,
            senior_consultant_day_rate=1500.0,
            architect_day_rate=1800.0,
            volume_discount_threshold=50000.0,
            principles=["Value-based", "Transparent"],
        )
        assert strategy.architect_day_rate == 1800.0
    
    def test_deal_pricing(self):
        deal = DealPricing(
            deal_id="DEAL-001",
            client_name="Acme Corp",
            work_packages=["WP1", "WP4"],
            base_price=25000.0,
            total_discount=2500.0,
            final_price=22500.0,
            estimated_cost=12000.0,
            gross_margin=10500.0,
            margin_percent=46.7,
            pricing_model=PricingModel.FIXED_PRICE,
        )
        assert deal.margin_percent == 46.7
    
    def test_opportunity(self):
        opp = Opportunity(
            id="OPP-001",
            name="Acme Cloud Migration",
            client_name="Acme Corp",
            segment=MarketSegment.MID_MARKET,
            engagement_type=EngagementType.MIGRATION,
            stage=DealStage.PROPOSAL,
            estimated_value=50000.0,
            probability=0.6,
            weighted_value=30000.0,
        )
        assert opp.weighted_value == 30000.0
    
    def test_pipeline_analysis(self):
        analysis = PipelineAnalysis(
            total_pipeline=500000.0,
            weighted_pipeline=175000.0,
            by_stage={"proposal": 200000.0, "negotiation": 100000.0},
            top_opportunities=["OPP-001", "OPP-002"],
        )
        assert analysis.total_pipeline == 500000.0
    
    def test_portfolio_health(self):
        health = PortfolioHealth(
            active_engagements=5,
            total_contract_value=150000.0,
            consultant_utilization=0.75,
            monthly_revenue=25000.0,
            client_satisfaction_avg=4.5,
        )
        assert health.consultant_utilization == 0.75
    
    def test_strategic_goal(self):
        goal = StrategicGoal(
            id="GOAL-001",
            name="Revenue Growth",
            description="Increase quarterly revenue",
            initiative=StrategicInitiative.MARKET_EXPANSION,
            target_metric="Quarterly Revenue",
            target_value=100000.0,
            current_value=75000.0,
            target_date="2025-03-31",
            progress_percent=75.0,
        )
        assert goal.progress_percent == 75.0
    
    def test_quarterly_plan(self):
        plan = QuarterlyPlan(
            quarter="Q1",
            year=2025,
            revenue_target=100000.0,
            pipeline_target=300000.0,
            focus_segments=[MarketSegment.MID_MARKET],
            initiatives=["Launch marketing campaign", "Hire consultant"],
        )
        assert plan.revenue_target == 100000.0
    
    def test_strategic_decision(self):
        decision = StrategicDecision(
            id="DEC-001",
            title="Enter US Market",
            context="Growing demand from US clients",
            options_considered=["Partner approach", "Direct entry", "Wait"],
            decision="Partner approach",
            rationale="Lower risk, faster entry",
            expected_impact="Access to US market with minimal investment",
            action_items=["Identify partners", "Draft agreement"],
        )
        assert decision.decision == "Partner approach"
    
    def test_competitive_intel(self):
        intel = CompetitiveIntel(
            market_trends=["Cloud-first", "AI adoption"],
            emerging_threats=["New entrant X"],
            opportunities=["Governance gap in market"],
            strategic_recommendations=["Focus on governance messaging"],
        )
        assert len(intel.market_trends) == 2


class TestA0State:
    """Test A0 state management."""
    
    def test_state_initialization(self):
        state: A0State = {
            "agent_id": "a0",
            "workflow_id": "test",
            "query_type": "pricing",
            "status": AgentStatus.IDLE,
            "messages": [],
            "artifacts": [],
            "decisions": [],
            "analysis_complete": False,
            "recommendation_ready": False,
        }
        
        assert state["agent_id"] == "a0"
        assert state["query_type"] == "pricing"


class TestA0Integration:
    """Integration tests for A0 (require API key)."""
    
    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Requires API key")
    async def test_price_deal(self):
        agent = create_a0_agent()
        
        state: A0State = {
            "agent_id": "a0",
            "workflow_id": "test_price",
            "query_type": "pricing",
            "deal_context": {
                "deal_id": "DEAL-TEST-001",
                "client_name": "Test Corp",
                "scope": "WP1 + WP4",
                "segment": "mid_market",
            },
            "current_task": "price_deal",
            "messages": [],
            "artifacts": [],
            "decisions": [],
            "status": AgentStatus.RUNNING,
        }
        
        result = await agent.run(state)
        
        assert result.get("recommendation_ready") is True
        assert len(result.get("artifacts", [])) > 0
    
    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Requires API key")
    async def test_competitive_analysis(self):
        agent = create_a0_agent()
        
        state: A0State = {
            "agent_id": "a0",
            "workflow_id": "test_competitive",
            "query_type": "competitive",
            "current_task": "competitive_analysis",
            "messages": [],
            "artifacts": [],
            "decisions": [],
            "status": AgentStatus.RUNNING,
        }
        
        result = await agent.run(state)
        
        assert result.get("analysis_complete") is True
        assert len(result.get("artifacts", [])) > 0
