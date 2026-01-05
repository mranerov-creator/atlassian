"""
Tests for A6 Delivery PM/QA Agent
"""
import pytest

from agents.a6_delivery import (
    A6DeliveryAgent,
    A6State,
    create_a6_agent,
    # Enums
    DeliverableStatus,
    DeliverableType,
    QACheckResult,
    RiskLevel,
    RiskCategory,
    WorkpackageType,
    EngagementType,
    # Models
    QACheck,
    QAChecklist,
    DefinitionOfDone,
    Milestone,
    Risk,
    Issue,
    Decision,
    RAIDLog,
    ProjectPlan,
    LineItem,
    PricingSection,
    PaymentTerms,
    StatementOfWork,
    ProposalOnePager,
    CapacitySlot,
    CapacityPlan,
)
from core.orchestrator import AgentStatus


class TestA6DeliveryAgent:
    """Test suite for A6 Delivery agent."""
    
    def test_agent_creation(self):
        """Test agent can be created."""
        agent = create_a6_agent()
        
        assert agent.config.id == "a6"
        assert agent.config.name == "Delivery PM/QA"
        assert "a1" in agent.config.allowed_handoffs
        assert "a3" in agent.config.allowed_handoffs
        assert "a4" in agent.config.allowed_handoffs
    
    def test_system_prompt_contains_rules(self):
        """Test system prompt contains required elements."""
        agent = create_a6_agent()
        prompt = agent.system_prompt()
        
        assert "QA" in prompt or "quality" in prompt.lower()
        assert "SoW" in prompt or "Statement of Work" in prompt
        assert "RAID" in prompt
        assert "DoD" in prompt or "Definition of Done" in prompt
    
    def test_dod_templates_initialized(self):
        """Test DoD templates are available."""
        agent = create_a6_agent()
        
        # Check some key deliverable types have DoD
        assert agent.get_dod(DeliverableType.SOW) is not None
        assert agent.get_dod(DeliverableType.WP1_REPORT) is not None
        assert agent.get_dod(DeliverableType.OPPORTUNITY_BRIEF) is not None
    
    def test_dod_has_criteria(self):
        """Test DoD templates have criteria."""
        agent = create_a6_agent()
        
        sow_dod = agent.get_dod(DeliverableType.SOW)
        assert sow_dod is not None
        assert len(sow_dod.criteria) > 0
        assert len(sow_dod.mandatory_sections) > 0


class TestA6Models:
    """Test A6 Pydantic models."""
    
    def test_qa_check(self):
        """Test QACheck model."""
        check = QACheck(
            id="QA-001",
            category="structure",
            check_name="Executive Summary Present",
            description="Verify exec summary exists",
            result=QACheckResult.PASS,
        )
        
        assert check.id == "QA-001"
        assert check.result == QACheckResult.PASS
    
    def test_qa_checklist(self):
        """Test QAChecklist model."""
        checklist = QAChecklist(
            deliverable_type=DeliverableType.SOW,
            deliverable_name="SOW-ACME-001",
            total_checks=10,
            passed=8,
            failed=1,
            warnings=1,
            qa_score=85,
            approved=True,
        )
        
        assert checklist.deliverable_type == DeliverableType.SOW
        assert checklist.qa_score == 85
        assert checklist.approved is True
    
    def test_risk(self):
        """Test Risk model."""
        risk = Risk(
            id="R-001",
            category=RiskCategory.SCOPE,
            description="Scope creep due to unclear requirements",
            probability="medium",
            impact="high",
            level=RiskLevel.HIGH,
            mitigation="Weekly scope reviews with client",
            owner="PM",
        )
        
        assert risk.category == RiskCategory.SCOPE
        assert risk.level == RiskLevel.HIGH
    
    def test_milestone(self):
        """Test Milestone model."""
        milestone = Milestone(
            id="M1",
            name="Discovery Complete",
            due_date="2025-02-15",
            deliverables=["Discovery Report", "Stakeholder Map"],
            status="planned",
        )
        
        assert milestone.id == "M1"
        assert len(milestone.deliverables) == 2
    
    def test_raid_log(self):
        """Test RAIDLog model."""
        raid = RAIDLog(
            engagement_id="ENG-001",
            risks=[
                Risk(
                    id="R-001",
                    category=RiskCategory.TIMELINE,
                    description="Tight deadline",
                    probability="high",
                    impact="medium",
                    level=RiskLevel.MEDIUM,
                    mitigation="Buffer time",
                )
            ],
        )
        
        assert raid.engagement_id == "ENG-001"
        assert len(raid.risks) == 1
    
    def test_line_item(self):
        """Test LineItem model."""
        item = LineItem(
            id="LI-001",
            description="Discovery & Planning",
            quantity=2,
            unit="days",
            unit_price=1500.0,
            total=3000.0,
        )
        
        assert item.total == 3000.0
    
    def test_statement_of_work(self):
        """Test StatementOfWork model."""
        sow = StatementOfWork(
            document_id="SOW-ACME-2025-001",
            client_name="Acme Corp",
            engagement_name="Cloud Transformation Diagnostic",
            workpackages=[WorkpackageType.WP1],
            engagement_type=EngagementType.FIXED_PRICE,
            executive_summary="We will help Acme assess their Atlassian landscape.",
            background="Acme is migrating from Server to Cloud.",
            total_investment=15000.0,
        )
        
        assert sow.document_id == "SOW-ACME-2025-001"
        assert WorkpackageType.WP1 in sow.workpackages
        assert sow.total_investment == 15000.0
    
    def test_proposal_one_pager(self):
        """Test ProposalOnePager model."""
        one_pager = ProposalOnePager(
            client_name="Acme Corp",
            engagement_name="WP1 Diagnostic",
            headline="Transform Your Atlassian Platform",
            problem_statement="Migration complexity is blocking your cloud journey.",
            approach_summary="4-week diagnostic with actionable roadmap.",
            key_deliverables=["Assessment Report", "30/60/90 Plan"],
            why_bluevektor=["Deep expertise", "Proven methodology"],
            investment_range="€15,000 - €20,000",
            timeline_summary="4 weeks",
            next_steps=["Schedule kickoff", "Provide access"],
            call_to_action="Let's schedule a 30-minute call.",
        )
        
        assert one_pager.client_name == "Acme Corp"
        assert len(one_pager.key_deliverables) == 2


class TestA6QAScoring:
    """Test QA scoring functionality."""
    
    def test_calculate_qa_score_all_pass(self):
        """Test QA score with all passed checks."""
        agent = create_a6_agent()
        
        checklist = QAChecklist(
            deliverable_type=DeliverableType.SOW,
            deliverable_name="Test",
            total_checks=10,
            passed=10,
            failed=0,
            warnings=0,
        )
        
        score = agent.calculate_qa_score(checklist)
        assert score == 100
    
    def test_calculate_qa_score_mixed(self):
        """Test QA score with mixed results."""
        agent = create_a6_agent()
        
        checklist = QAChecklist(
            deliverable_type=DeliverableType.SOW,
            deliverable_name="Test",
            total_checks=10,
            passed=6,
            failed=2,
            warnings=2,
        )
        
        score = agent.calculate_qa_score(checklist)
        # (6*100 + 2*70 + 2*0) / 10 = 74
        assert score == 74
    
    def test_calculate_qa_score_empty(self):
        """Test QA score with no checks."""
        agent = create_a6_agent()
        
        checklist = QAChecklist(
            deliverable_type=DeliverableType.SOW,
            deliverable_name="Test",
            total_checks=0,
            passed=0,
            failed=0,
            warnings=0,
        )
        
        score = agent.calculate_qa_score(checklist)
        assert score == 0


class TestA6State:
    """Test A6 state management."""
    
    def test_state_initialization(self):
        """Test A6State can be initialized."""
        state: A6State = {
            "agent_id": "a6",
            "workflow_id": "test",
            "client_name": "Acme Corp",
            "status": AgentStatus.IDLE,
            "messages": [],
            "artifacts": [],
            "decisions": [],
            "qa_passed": False,
            "proposal_generated": False,
            "plan_created": False,
        }
        
        assert state["agent_id"] == "a6"
        assert state["qa_passed"] is False


class TestA6Integration:
    """Integration tests for A6 (require API key)."""
    
    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Requires API key")
    async def test_qa_review(self):
        """Test QA review flow."""
        agent = create_a6_agent()
        
        state: A6State = {
            "agent_id": "a6",
            "workflow_id": "test_qa",
            "deliverable_content": """
# Executive Summary
This is a test document.

# Scope
In scope: Testing
Out of scope: Production
            """,
            "deliverable_type": DeliverableType.SOW,
            "current_task": "qa_review",
            "messages": [],
            "artifacts": [],
            "decisions": [],
            "status": AgentStatus.RUNNING,
        }
        
        result = await agent.run(state)
        
        assert "qa_feedback" in result
        assert len(result.get("artifacts", [])) > 0
    
    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Requires API key")
    async def test_generate_sow(self):
        """Test SoW generation."""
        agent = create_a6_agent()
        
        state: A6State = {
            "agent_id": "a6",
            "workflow_id": "test_sow",
            "client_name": "Test Corp",
            "opportunity_brief": {
                "company_name": "Test Corp",
                "problem_statement": "Need to migrate to Cloud",
                "proposed_workpackages": ["wp1"],
            },
            "current_task": "generate_sow",
            "messages": [],
            "artifacts": [],
            "decisions": [],
            "status": AgentStatus.RUNNING,
        }
        
        result = await agent.run(state)
        
        assert result.get("proposal_generated") is True
        assert any(a["type"] == "sow" for a in result.get("artifacts", []))
