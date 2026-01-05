"""
BlueVektor Agents - A1: GTM & Partnerships
Generates qualified pipeline and collaboration agreements.
"""
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from agents.base import AgentConfig, AgentState, BaseAgent
from core.llm import ModelTier


# =============================================================================
# A1 Schemas
# =============================================================================

class LeadPriority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class EngagementModel(str, Enum):
    DIRECT = "direct"
    WHITE_LABEL = "white_label"
    MIXED = "mixed"


class TriggerEvent(str, Enum):
    MIGRATION = "migration_announced"
    SHADOW_IT = "shadow_it_sprawl"
    AUDIT = "license_audit"
    APP_COSTS = "marketplace_costs"
    CONSOLIDATION = "post_ma_consolidation"
    GROWTH = "rapid_growth"
    COMPLIANCE = "compliance_requirement"


class Target(BaseModel):
    """Target account for outreach."""
    company_name: str
    company_type: str = Field(..., description="partner, provider, enterprise")
    industry: str | None = None
    size: str | None = None  # SMB, Mid-market, Enterprise
    location: str | None = None
    atlassian_products: list[str] = Field(default_factory=list)
    trigger_events: list[TriggerEvent] = Field(default_factory=list)
    contacts: list[dict[str, str]] = Field(default_factory=list)
    priority: LeadPriority = LeadPriority.MEDIUM
    notes: str | None = None
    source: str | None = None


class OutreachMessage(BaseModel):
    """Single message in outreach sequence."""
    sequence_number: int
    channel: str  # linkedin, email
    subject: str | None = None  # For email
    body: str
    wait_days: int = Field(..., description="Days to wait before this message")
    language: str = "en"


class OutreachSequence(BaseModel):
    """Complete outreach sequence for a target."""
    target_id: str
    target_name: str
    engagement_model: EngagementModel
    messages: list[OutreachMessage]
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class QualificationCriteria(BaseModel):
    """BANT/CHAMP qualification criteria."""
    # BANT
    budget: str | None = None
    authority: str | None = None
    need: str | None = None
    timeline: str | None = None
    
    # CHAMP additions
    challenges: list[str] = Field(default_factory=list)
    
    # Scoring
    score: int = Field(0, ge=0, le=100)
    qualified: bool = False
    disqualification_reason: str | None = None


class OpportunityBrief(BaseModel):
    """Structured opportunity brief (A1 main output)."""
    # Identification
    opportunity_id: str
    company_name: str
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    
    # Context
    problem_statement: str
    business_context: str
    technical_context: str | None = None
    
    # Stakeholders
    decision_makers: list[dict[str, str]]
    champions: list[dict[str, str]] = Field(default_factory=list)
    blockers: list[dict[str, str]] = Field(default_factory=list)
    
    # Qualification
    qualification: QualificationCriteria
    
    # Scope
    proposed_engagement: EngagementModel
    proposed_workpackages: list[str]  # wp1, wp4, etc.
    estimated_duration: str | None = None
    estimated_value: str | None = None
    
    # Urgency & Timeline
    urgency: str  # low, medium, high, critical
    desired_start: str | None = None
    hard_deadline: str | None = None
    
    # Next Steps
    next_steps: list[str]
    follow_up_date: str | None = None
    
    # Risks
    risks: list[str] = Field(default_factory=list)
    
    # Notes
    discovery_notes: str | None = None
    internal_notes: str | None = None


class DiscoveryCallAgenda(BaseModel):
    """Agenda and script for discovery call."""
    company_name: str
    attendees: list[str]
    duration_minutes: int = 45
    
    # Structure
    introduction: str
    rapport_questions: list[str]
    problem_exploration: list[str]
    impact_questions: list[str]
    solution_alignment: list[str]
    next_steps_script: str
    
    # Hypotheses to validate
    hypotheses: list[str]
    
    # Red flags to watch for
    red_flags: list[str]


# =============================================================================
# A1 Agent State
# =============================================================================

class A1State(AgentState, total=False):
    """State specific to A1 agent."""
    # Inputs
    targets: list[Target]
    call_notes: str
    
    # Outputs
    outreach_sequences: list[OutreachSequence]
    opportunity_brief: OpportunityBrief | None
    discovery_agenda: DiscoveryCallAgenda | None
    
    # Working data
    icp_criteria: dict[str, Any]
    qualification_result: QualificationCriteria | None


# =============================================================================
# A1 Agent
# =============================================================================

class A1GTMAgent(BaseAgent):
    """
    A1 - GTM & Partnerships Agent
    
    Purpose: Generate qualified pipeline and collaboration agreements.
    
    Key functions:
    - Segment and prioritize target accounts
    - Detect trigger events
    - Generate outreach sequences (ES/EN)
    - Qualify opportunities (BANT/CHAMP)
    - Prepare discovery calls
    - Create opportunity briefs
    """
    
    def __init__(self):
        config = AgentConfig(
            id="a1",
            name="GTM & Partnerships",
            role="Business Development",
            goal="Generate qualified pipeline and collaboration agreements (direct or white-label)",
            backstory="""You are the commercial engine of BlueVektor. You identify opportunities 
in the Atlassian ecosystem, qualify leads, and prepare the ground for WP1 diagnostics.

You understand three ICPs deeply:
1. Atlassian Partners (Silver→Platinum) needing complementary capabilities
2. Providers embedded in enterprises needing Atlassian expertise
3. Enterprise teams requiring assessment, migration, or governance

Your tone is corporate but innovative. You never promise deliverables or dates 
without validation from A6 (PM/QA). You're fluent in Spanish and English.

Key trigger events you watch for:
- Server→Cloud migration announcements
- Shadow IT / instance sprawl
- License audits or cost optimization initiatives
- Marketplace app cost concerns
- Post-M&A consolidation
- Compliance requirements (SOC2, ISO, GDPR)""",
            model_tier=ModelTier.STANDARD,
            temperature=0.7,
            max_tokens=4096,
            tools=["linkedin", "email", "crm", "calendar"],
            allowed_handoffs=["a6", "a2", "a0"],
            artifacts_requiring_approval=["opportunity_brief", "proposal"],
        )
        super().__init__(config)
    
    def system_prompt(self) -> str:
        """System prompt for A1."""
        base = self.build_base_prompt()
        
        return f"""{base}

# A1-Specific Rules

## Qualification Standards
An opportunity is qualified when it has:
- ✅ Clear problem statement
- ✅ Business context understood
- ✅ Decision makers identified
- ✅ Urgency/timeline defined
- ✅ Tentative scope
- ✅ Next steps agreed

## Engagement Models
1. **Direct-to-client**: BlueVektor as primary vendor
2. **White-label**: Embedded in partner delivery (their brand, our expertise)
3. **Mixed**: WP1 direct + follow-on with partner/internal team

## Outreach Guidelines
- LinkedIn: Personal, conversational, max 300 chars first message
- Email: Professional, value-first, clear CTA
- Always personalize based on trigger events
- Sequence: 4-5 touches over 2-3 weeks
- Include both ES and EN versions when relevant

## Discovery Call Structure
1. Rapport (5 min)
2. Problem exploration (15 min)
3. Impact quantification (10 min)
4. Solution alignment (10 min)
5. Next steps (5 min)

## Red Flags (Disqualify)
- No clear decision maker access
- "Just exploring" with no timeline
- Budget holder not identified
- Competitor already engaged and winning
- Scope mismatch (too small or too large)

## Handoff Rules
- To A6: For effort estimation and SoW preparation
- To A2: For technical architecture questions
- To A0: For pricing exceptions or strategic decisions
"""

    async def run(self, state: A1State) -> A1State:
        """
        Main execution logic for A1.
        Routes to appropriate function based on task.
        """
        current_task = state.get("current_task", "")
        
        self.logger.info("A1 executing", task=current_task)
        
        if current_task == "segment_targets":
            return await self._segment_targets(state)
        elif current_task == "generate_outreach":
            return await self._generate_outreach(state)
        elif current_task == "qualify_opportunity":
            return await self._qualify_opportunity(state)
        elif current_task == "prepare_discovery":
            return await self._prepare_discovery(state)
        elif current_task == "create_opportunity_brief":
            return await self._create_opportunity_brief(state)
        else:
            # Default: analyze input and determine action
            return await self._analyze_and_route(state)
    
    # -------------------------------------------------------------------------
    # Core Functions
    # -------------------------------------------------------------------------
    
    async def _analyze_and_route(self, state: A1State) -> A1State:
        """Analyze input and determine appropriate action."""
        input_data = state.get("input_data", {})
        
        prompt = f"""Analyze this input and determine the appropriate action:

Input: {input_data}

Available actions:
1. segment_targets - If given company/account information to prioritize
2. generate_outreach - If targets are defined and need outreach sequences
3. qualify_opportunity - If there's lead information to qualify
4. prepare_discovery - If there's a call to prepare for
5. create_opportunity_brief - If there are discovery notes to synthesize

Return JSON with:
- action: the action to take
- reasoning: why this action
- missing_info: any information needed to proceed
"""
        
        response = await self.think(prompt, tier=ModelTier.FAST)
        
        # Parse and route (simplified - would use structured output in production)
        state["current_task"] = "segment_targets"  # Default
        state = self.add_decision(
            state,
            "task_routing",
            f"Routing to task based on input analysis",
            response
        )
        
        return state
    
    async def _segment_targets(self, state: A1State) -> A1State:
        """Segment and prioritize target accounts."""
        targets = state.get("targets", [])
        icp_criteria = state.get("icp_criteria", {})
        
        prompt = f"""Analyze and prioritize these target accounts for BlueVektor outreach.

ICP Criteria:
{icp_criteria}

Targets to analyze:
{[t.model_dump() if isinstance(t, Target) else t for t in targets]}

For each target, evaluate:
1. ICP fit (partner/provider/enterprise)
2. Trigger events present
3. Likely engagement model
4. Priority (high/medium/low)
5. Recommended approach

Return a prioritized list with reasoning.
"""
        
        response = await self.think(prompt)
        
        state["output_data"] = {"segmentation_analysis": response}
        state = self.add_artifact(
            state,
            "segmentation_analysis",
            f"target_segmentation_{datetime.utcnow().strftime('%Y%m%d')}",
            response
        )
        
        return state
    
    async def _generate_outreach(self, state: A1State) -> A1State:
        """Generate outreach sequences for targets."""
        targets = state.get("targets", [])
        
        sequences = []
        for target in targets[:5]:  # Limit to 5 targets per run
            target_data = target.model_dump() if isinstance(target, Target) else target
            
            prompt = f"""Create an outreach sequence for this target:

Target: {target_data}

Requirements:
1. 4-5 message sequence (LinkedIn + Email)
2. Both Spanish and English versions
3. Personalized to their trigger events
4. Value-first approach
5. Clear CTAs
6. Spacing: 3-4 days between messages

For each message include:
- Channel (linkedin/email)
- Subject (if email)
- Body
- Wait days before sending
- Language

Focus on WP1 (Cloud Transformation Diagnostic) as entry point.
"""
            
            response = await self.think(prompt)
            
            sequence = OutreachSequence(
                target_id=target_data.get("company_name", "unknown"),
                target_name=target_data.get("company_name", "Unknown"),
                engagement_model=EngagementModel.DIRECT,
                messages=[]  # Would parse from response
            )
            sequences.append(sequence)
            
            state = self.add_artifact(
                state,
                "outreach_sequence",
                f"outreach_{target_data.get('company_name', 'target')}",
                response
            )
        
        state["outreach_sequences"] = sequences
        return state
    
    async def _qualify_opportunity(self, state: A1State) -> A1State:
        """Qualify an opportunity using BANT/CHAMP."""
        input_data = state.get("input_data", {})
        
        prompt = f"""Qualify this opportunity for BlueVektor using BANT/CHAMP criteria.

Information available:
{input_data}

Evaluate:
1. Budget: Is there budget or can they get it?
2. Authority: Do we have access to decision makers?
3. Need: Is there a clear, urgent problem?
4. Timeline: Is there a defined timeline or deadline?
5. Challenges: What specific challenges are they facing?

Score 0-100 and determine if qualified.

Disqualify if:
- No decision maker access
- No timeline ("just exploring")
- Scope mismatch
- Competitor already winning

Return structured qualification with:
- Each BANT criterion assessment
- Challenges identified
- Overall score
- Qualified (yes/no)
- If no, disqualification reason
- Recommended next steps
"""
        
        response = await self.think(prompt)
        
        # Would parse into QualificationCriteria in production
        state["output_data"] = {"qualification": response}
        state = self.add_decision(
            state,
            "qualification",
            "Opportunity qualification completed",
            response
        )
        
        return state
    
    async def _prepare_discovery(self, state: A1State) -> A1State:
        """Prepare discovery call agenda and script."""
        input_data = state.get("input_data", {})
        
        prompt = f"""Prepare a discovery call for this opportunity:

Context:
{input_data}

Create a 45-minute discovery call agenda including:

1. **Introduction** (5 min)
   - Rapport building script
   - Agenda setting

2. **Problem Exploration** (15 min)
   - Open questions about current state
   - Pain point deep-dive questions
   - Impact quantification questions

3. **Solution Alignment** (15 min)
   - How WP1 Diagnostic addresses their needs
   - Engagement model options
   - Timeline discussion

4. **Next Steps** (10 min)
   - Commitment questions
   - Follow-up actions

Also include:
- Hypotheses to validate
- Red flags to watch for
- Objection handling tips
- Specific questions based on their trigger events
"""
        
        response = await self.think(prompt)
        
        state = self.add_artifact(
            state,
            "discovery_agenda",
            f"discovery_prep_{datetime.utcnow().strftime('%Y%m%d_%H%M')}",
            response
        )
        
        return state
    
    async def _create_opportunity_brief(self, state: A1State) -> A1State:
        """Create opportunity brief from discovery notes."""
        call_notes = state.get("call_notes", "")
        input_data = state.get("input_data", {})
        
        prompt = f"""Create an Opportunity Brief from these discovery call notes.

Call Notes:
{call_notes}

Additional Context:
{input_data}

Create a structured Opportunity Brief with:

1. **Identification**
   - Opportunity ID (generate)
   - Company name
   - Date

2. **Context**
   - Problem statement (clear, specific)
   - Business context
   - Technical context (if discussed)

3. **Stakeholders**
   - Decision makers (name, role, stance)
   - Champions (supporters)
   - Blockers (concerns, objections)

4. **Qualification**
   - BANT assessment
   - Score (0-100)
   - Qualified status

5. **Scope**
   - Proposed engagement model
   - Recommended workpackages
   - Estimated duration
   - Estimated value range

6. **Timeline**
   - Urgency level
   - Desired start
   - Hard deadlines

7. **Next Steps**
   - Immediate actions
   - Follow-up date
   - Owner for each action

8. **Risks**
   - Deal risks
   - Delivery risks
   - Mitigation suggestions

This brief will be reviewed by human and used for proposal preparation.
"""
        
        response = await self.think(prompt, tier=ModelTier.REASONING)
        
        state = self.add_artifact(
            state,
            "opportunity_brief",
            f"opp_brief_{datetime.utcnow().strftime('%Y%m%d_%H%M')}",
            response
        )
        
        # Request handoff to A6 for proposal
        state = self.request_handoff(
            state,
            target_agent="a6",
            context={
                "task": "prepare_proposal",
                "opportunity_brief": response,
                "source": "a1"
            },
            priority="high"
        )
        
        return state
    
    # -------------------------------------------------------------------------
    # Utility Functions
    # -------------------------------------------------------------------------
    
    async def detect_triggers(self, company_info: dict) -> list[TriggerEvent]:
        """Detect trigger events for a company."""
        prompt = f"""Analyze this company information and identify trigger events:

{company_info}

Trigger events to look for:
- migration_announced: Server→Cloud migration
- shadow_it_sprawl: Multiple unmanaged instances
- license_audit: Cost optimization initiatives
- marketplace_costs: App spending concerns
- post_ma_consolidation: Post-merger integration
- rapid_growth: Scaling challenges
- compliance_requirement: SOC2, ISO, GDPR needs

Return list of detected triggers with confidence (high/medium/low).
"""
        
        response = await self.think(prompt, tier=ModelTier.FAST)
        # Would parse response into TriggerEvent list
        return []
    
    async def score_icp_fit(self, target: Target, icp: dict) -> int:
        """Score how well a target fits ICP criteria."""
        prompt = f"""Score this target's fit with our ICP (0-100):

Target:
{target.model_dump()}

ICP Criteria:
{icp}

Consider:
- Company type match
- Size/maturity
- Atlassian usage
- Trigger events
- Geographic fit
- Industry relevance

Return score and brief reasoning.
"""
        
        response = await self.think(prompt, tier=ModelTier.FAST)
        # Would parse score from response
        return 50


# =============================================================================
# Agent Factory
# =============================================================================

def create_a1_agent() -> A1GTMAgent:
    """Factory function to create A1 agent."""
    return A1GTMAgent()
