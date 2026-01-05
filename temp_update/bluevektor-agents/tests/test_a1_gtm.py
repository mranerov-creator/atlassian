"""
Tests for A1 GTM Agent
"""
import pytest

from agents.a1_gtm import (
    A1GTMAgent,
    A1State,
    LeadPriority,
    EngagementModel,
    Target,
    QualificationCriteria,
    OpportunityBrief,
    create_a1_agent,
)
from core.orchestrator import AgentStatus


class TestA1GTMAgent:
    """Test suite for A1 GTM agent."""
    
    def test_agent_creation(self):
        """Test agent can be created."""
        agent = create_a1_agent()
        
        assert agent.config.id == "a1"
        assert agent.config.name == "GTM & Partnerships"
        assert "a6" in agent.config.allowed_handoffs
    
    def test_system_prompt_contains_rules(self):
        """Test system prompt contains required elements."""
        agent = create_a1_agent()
        prompt = agent.system_prompt()
        
        assert "ICP" in prompt
        assert "BANT" in prompt or "qualification" in prompt.lower()
        assert "handoff" in prompt.lower()
    
    def test_target_model(self):
        """Test Target pydantic model."""
        target = Target(
            company_name="Acme Corp",
            company_type="enterprise",
            priority=LeadPriority.HIGH,
        )
        
        assert target.company_name == "Acme Corp"
        assert target.priority == LeadPriority.HIGH
    
    def test_qualification_criteria(self):
        """Test QualificationCriteria model."""
        criteria = QualificationCriteria(
            budget="$50k-100k approved",
            authority="CTO is decision maker",
            need="Migration from Server required by EOL",
            timeline="Q2 2025",
            score=85,
            qualified=True,
        )
        
        assert criteria.qualified is True
        assert criteria.score == 85
    
    def test_state_initialization(self):
        """Test A1State can be initialized."""
        state: A1State = {
            "agent_id": "a1",
            "workflow_id": "test",
            "status": AgentStatus.IDLE,
            "messages": [],
            "artifacts": [],
            "decisions": [],
        }
        
        assert state["agent_id"] == "a1"
        assert state["status"] == AgentStatus.IDLE


class TestA1Integration:
    """Integration tests for A1 (require API key)."""
    
    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Requires API key")
    async def test_qualify_lead(self):
        """Test lead qualification flow."""
        agent = create_a1_agent()
        
        state: A1State = {
            "agent_id": "a1",
            "workflow_id": "test_qualify",
            "input_data": {
                "company_name": "Test Corp",
                "contact_email": "test@test.com",
                "notes": "Interested in Cloud migration",
            },
            "current_task": "qualify_opportunity",
            "messages": [],
            "artifacts": [],
            "decisions": [],
            "status": AgentStatus.RUNNING,
        }
        
        result = await agent.run(state)
        
        assert "output_data" in result
        assert len(result.get("decisions", [])) > 0
