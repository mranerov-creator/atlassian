"""
BlueVektor Agents - A0: CEO / Strategist
Strategic decisions, pricing, positioning, and portfolio management.
"""
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from agents.base import AgentConfig, AgentState, BaseAgent
from core.llm import ModelTier


# =============================================================================
# A0 Enums
# =============================================================================

class MarketSegment(str, Enum):
    ENTERPRISE = "enterprise"
    MID_MARKET = "mid_market"
    SMB = "smb"
    STARTUP = "startup"


class EngagementType(str, Enum):
    ASSESSMENT = "assessment"  # WP1
    MIGRATION = "migration"  # WP2/WP5
    IMPLEMENTATION = "implementation"  # WP3
    GOVERNANCE = "governance"  # WP4
    OPTIMIZATION = "optimization"
    ADVISORY = "advisory"
    TRAINING = "training"
    SUPPORT = "support"


class PricingModel(str, Enum):
    FIXED_PRICE = "fixed_price"
    TIME_MATERIALS = "time_and_materials"
    VALUE_BASED = "value_based"
    RETAINER = "retainer"
    SUBSCRIPTION = "subscription"
    HYBRID = "hybrid"


class DealStage(str, Enum):
    LEAD = "lead"
    QUALIFIED = "qualified"
    DISCOVERY = "discovery"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"


class Priority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class StrategicInitiative(str, Enum):
    MARKET_EXPANSION = "market_expansion"
    PRODUCT_DEVELOPMENT = "product_development"
    PARTNERSHIP = "partnership"
    OPERATIONAL_EXCELLENCE = "operational_excellence"
    TALENT_ACQUISITION = "talent_acquisition"


# =============================================================================
# A0 Market & Positioning Schemas
# =============================================================================

class CompetitorProfile(BaseModel):
    """Competitor analysis."""
    name: str
    type: str  # big4, boutique, system_integrator, freelance
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    pricing_position: str = "market"  # premium, market, discount
    target_segments: list[MarketSegment] = Field(default_factory=list)
    key_differentiators: list[str] = Field(default_factory=list)


class MarketPosition(BaseModel):
    """BlueVektor market positioning."""
    tagline: str
    value_proposition: str
    target_segments: list[MarketSegment] = Field(default_factory=list)
    key_differentiators: list[str] = Field(default_factory=list)
    proof_points: list[str] = Field(default_factory=list)
    competitors: list[CompetitorProfile] = Field(default_factory=list)
    competitive_advantages: list[str] = Field(default_factory=list)


class TargetPersona(BaseModel):
    """Target buyer persona."""
    name: str
    title: str
    department: str
    pain_points: list[str] = Field(default_factory=list)
    goals: list[str] = Field(default_factory=list)
    objections: list[str] = Field(default_factory=list)
    buying_triggers: list[str] = Field(default_factory=list)
    preferred_channels: list[str] = Field(default_factory=list)


# =============================================================================
# A0 Pricing Schemas
# =============================================================================

class WorkPackagePricing(BaseModel):
    """Pricing for a work package."""
    wp_id: str
    name: str
    description: str
    
    # Pricing tiers
    base_price_eur: float
    enterprise_multiplier: float = 1.5
    smb_discount: float = 0.8
    
    # Effort basis
    base_days: int
    min_days: int
    max_days: int
    
    # Rate card
    day_rate_eur: float = 1200.0
    
    # Value drivers
    value_drivers: list[str] = Field(default_factory=list)
    
    # Inclusions/exclusions
    inclusions: list[str] = Field(default_factory=list)
    exclusions: list[str] = Field(default_factory=list)
    
    # Optional add-ons
    add_ons: list[dict[str, Any]] = Field(default_factory=list)


class PricingStrategy(BaseModel):
    """Overall pricing strategy."""
    name: str = "BlueVektor Pricing Strategy"
    version: str = "1.0"
    effective_date: str = Field(default_factory=lambda: datetime.utcnow().strftime('%Y-%m-%d'))
    
    # Rate card
    consultant_day_rate: float = 1200.0
    senior_consultant_day_rate: float = 1500.0
    architect_day_rate: float = 1800.0
    principal_day_rate: float = 2200.0
    
    # Work packages
    work_packages: list[WorkPackagePricing] = Field(default_factory=list)
    
    # Discounting rules
    volume_discount_threshold: float = 50000.0
    volume_discount_percent: float = 10.0
    multi_wp_discount_percent: float = 15.0
    
    # Payment terms
    payment_terms: str = "30 days net"
    deposit_required: bool = True
    deposit_percent: float = 30.0
    
    # Pricing principles
    principles: list[str] = Field(default_factory=list)


class DealPricing(BaseModel):
    """Pricing for a specific deal."""
    deal_id: str
    client_name: str
    
    # Components
    work_packages: list[str] = Field(default_factory=list)
    
    # Calculations
    base_price: float = 0.0
    discounts: list[dict[str, float]] = Field(default_factory=list)
    total_discount: float = 0.0
    final_price: float = 0.0
    
    # Margin analysis
    estimated_cost: float = 0.0
    gross_margin: float = 0.0
    margin_percent: float = 0.0
    
    # Pricing model
    pricing_model: PricingModel = PricingModel.FIXED_PRICE
    
    # Rationale
    pricing_rationale: str | None = None
    competitive_context: str | None = None
    
    # Approval
    requires_approval: bool = False
    approval_reason: str | None = None


# =============================================================================
# A0 Portfolio & Pipeline Schemas
# =============================================================================

class Opportunity(BaseModel):
    """Sales opportunity."""
    id: str
    name: str
    client_name: str
    
    # Classification
    segment: MarketSegment
    engagement_type: EngagementType
    stage: DealStage
    
    # Value
    estimated_value: float = 0.0
    weighted_value: float = 0.0
    probability: float = 0.0
    
    # Timeline
    expected_close_date: str | None = None
    
    # Details
    pain_points: list[str] = Field(default_factory=list)
    decision_criteria: list[str] = Field(default_factory=list)
    competitors: list[str] = Field(default_factory=list)
    champion: str | None = None
    
    # Status
    next_action: str | None = None
    blockers: list[str] = Field(default_factory=list)


class PipelineAnalysis(BaseModel):
    """Pipeline analysis."""
    analysis_date: str = Field(default_factory=lambda: datetime.utcnow().strftime('%Y-%m-%d'))
    
    # Summary
    total_pipeline: float = 0.0
    weighted_pipeline: float = 0.0
    
    # By stage
    by_stage: dict[str, float] = Field(default_factory=dict)
    
    # By segment
    by_segment: dict[str, float] = Field(default_factory=dict)
    
    # By type
    by_engagement_type: dict[str, float] = Field(default_factory=dict)
    
    # Opportunities
    opportunities: list[Opportunity] = Field(default_factory=list)
    
    # Insights
    top_opportunities: list[str] = Field(default_factory=list)
    at_risk: list[str] = Field(default_factory=list)
    quick_wins: list[str] = Field(default_factory=list)


class PortfolioHealth(BaseModel):
    """Current portfolio health."""
    analysis_date: str = Field(default_factory=lambda: datetime.utcnow().strftime('%Y-%m-%d'))
    
    # Active engagements
    active_engagements: int = 0
    total_contract_value: float = 0.0
    
    # Utilization
    consultant_utilization: float = 0.0
    
    # Revenue
    monthly_revenue: float = 0.0
    quarterly_revenue: float = 0.0
    annual_revenue_target: float = 0.0
    revenue_vs_target: float = 0.0
    
    # Health indicators
    client_satisfaction_avg: float = 0.0
    on_time_delivery_rate: float = 0.0
    scope_change_rate: float = 0.0
    
    # Risks
    at_risk_engagements: list[str] = Field(default_factory=list)


# =============================================================================
# A0 Strategic Planning Schemas
# =============================================================================

class StrategicGoal(BaseModel):
    """Strategic goal."""
    id: str
    name: str
    description: str
    initiative: StrategicInitiative
    
    # Target
    target_metric: str
    target_value: float
    current_value: float = 0.0
    
    # Timeline
    target_date: str
    
    # Progress
    progress_percent: float = 0.0
    status: str = "on_track"  # on_track, at_risk, behind, achieved
    
    # Actions
    key_actions: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)


class QuarterlyPlan(BaseModel):
    """Quarterly strategic plan."""
    quarter: str  # Q1 2025
    year: int
    
    # Revenue targets
    revenue_target: float = 0.0
    pipeline_target: float = 0.0
    
    # Goals
    goals: list[StrategicGoal] = Field(default_factory=list)
    
    # Focus areas
    focus_segments: list[MarketSegment] = Field(default_factory=list)
    focus_offerings: list[EngagementType] = Field(default_factory=list)
    
    # Key initiatives
    initiatives: list[str] = Field(default_factory=list)
    
    # Resource plan
    headcount_target: int = 0
    hiring_needs: list[str] = Field(default_factory=list)


class StrategicDecision(BaseModel):
    """Strategic decision record."""
    id: str
    title: str
    date: str = Field(default_factory=lambda: datetime.utcnow().strftime('%Y-%m-%d'))
    
    # Context
    context: str
    options_considered: list[str] = Field(default_factory=list)
    
    # Decision
    decision: str
    rationale: str
    
    # Impact
    expected_impact: str
    risks: list[str] = Field(default_factory=list)
    
    # Follow-up
    action_items: list[str] = Field(default_factory=list)
    review_date: str | None = None


# =============================================================================
# A0 Competitive Intelligence Schemas
# =============================================================================

class CompetitiveIntel(BaseModel):
    """Competitive intelligence report."""
    report_date: str = Field(default_factory=lambda: datetime.utcnow().strftime('%Y-%m-%d'))
    
    # Market overview
    market_trends: list[str] = Field(default_factory=list)
    emerging_threats: list[str] = Field(default_factory=list)
    opportunities: list[str] = Field(default_factory=list)
    
    # Competitor updates
    competitor_moves: list[dict[str, str]] = Field(default_factory=list)
    
    # Pricing intelligence
    pricing_trends: list[str] = Field(default_factory=list)
    
    # Recommendations
    strategic_recommendations: list[str] = Field(default_factory=list)


# =============================================================================
# A0 Agent State
# =============================================================================

class A0State(AgentState, total=False):
    """State specific to A0 agent."""
    # Context
    query_type: str  # pricing, strategy, pipeline, competitive, decision
    
    # Inputs
    deal_context: dict[str, Any]
    market_context: dict[str, Any]
    pipeline_data: list[dict[str, Any]]
    
    # Working data
    pricing_strategy: PricingStrategy | None
    market_position: MarketPosition | None
    pipeline_analysis: PipelineAnalysis | None
    quarterly_plan: QuarterlyPlan | None
    
    # Progress
    analysis_complete: bool
    recommendation_ready: bool


# =============================================================================
# A0 Agent
# =============================================================================

class A0StrategistAgent(BaseAgent):
    """
    A0 - CEO / Strategist Agent
    
    Purpose: Strategic decisions, pricing, positioning, and portfolio management.
    """
    
    def __init__(self):
        config = AgentConfig(
            id="a0",
            name="CEO / Strategist",
            role="Strategic Leadership",
            goal="Make data-driven strategic decisions that maximize BlueVektor's growth and profitability",
            backstory="""You are the strategic brain of BlueVektor. You think like a 
CEO of a boutique consulting firm - balancing growth ambitions with 
operational realities.

Your expertise includes:
- Pricing strategy and deal economics
- Market positioning and competitive analysis
- Pipeline management and forecasting
- Strategic planning and goal setting
- Partnership and growth opportunities

You understand that:
- Every deal must be profitable
- Brand positioning matters as much as price
- Sustainable growth beats quick wins
- Client relationships are long-term assets
- Data should drive decisions, not gut feelings

Key principles:
- Price for value, not just cost
- Protect the brand - no race to the bottom
- Invest in what differentiates us
- Build repeatable, scalable offerings
- Measure what matters""",
            model_tier=ModelTier.REASONING,
            temperature=0.5,
            max_tokens=8192,
            tools=["filesystem", "analytics"],
            allowed_handoffs=["a1", "a6"],
            artifacts_requiring_approval=["pricing_decision", "strategic_plan"],
        )
        super().__init__(config)
    
    def system_prompt(self) -> str:
        """System prompt for A0."""
        base = self.build_base_prompt()
        
        return f"""{base}

# A0-Specific Rules

## BlueVektor Positioning

### Who We Are
- Boutique Atlassian Cloud consultancy
- Evidence-first transformation approach
- Enterprise-grade expertise, startup agility
- Based in Spain, serving EU enterprises

### Our Differentiators
1. **Evidence-First**: We prove before we propose
2. **AI-Augmented**: Faster insights, better outcomes
3. **Governance Built-In**: Not an afterthought
4. **Transparent Pricing**: No surprises
5. **Senior-Led**: No bait-and-switch

### Target Segments
- **Primary**: Mid-market (500-5000 users)
- **Secondary**: Enterprise (5000+ users)
- **Opportunistic**: SMB (high-growth tech companies)

## Pricing Framework

### Work Package Pricing

| WP | Name | Base Price (EUR) | Days | Description |
|----|------|------------------|------|-------------|
| WP1 | Diagnostic | 8,000-15,000 | 5-10 | AS-IS assessment |
| WP2 | Cloud Migration | 25,000-100,000 | 15-60 | Server/DC to Cloud |
| WP3 | Implementation | 15,000-50,000 | 10-30 | New implementations |
| WP4 | Governance | 12,000-25,000 | 8-15 | Governance office-in-a-box |
| WP5 | Optimization | 10,000-30,000 | 7-20 | Cloud-to-cloud, optimization |

### Rate Card

| Role | Day Rate (EUR) | Use Case |
|------|----------------|----------|
| Consultant | 1,200 | Standard delivery |
| Senior Consultant | 1,500 | Complex work, client-facing |
| Solution Architect | 1,800 | Design, architecture |
| Principal | 2,200 | Strategic advisory |

### Pricing Principles

1. **Value-Based**: Price reflects value delivered, not just hours
2. **Segment-Adjusted**: Enterprise pays premium, SMB gets efficiency
3. **Bundled**: Multi-WP deals get discount (encourage full journey)
4. **Transparent**: No hidden fees, clear scope
5. **Profitable**: Minimum 40% gross margin target

### Discounting Guidelines

| Scenario | Max Discount |
|----------|--------------|
| Multi-WP bundle | 15% |
| Volume (>50K) | 10% |
| Strategic account | 20% |
| Competitive pressure | 10% |
| **Combined maximum** | **25%** |

**Never discount below 35% margin.**

### Deal Approval Thresholds

| Condition | Approval Required |
|-----------|-------------------|
| >20% discount | A0 approval |
| <40% margin | A0 approval |
| >100K deal | A0 review |
| New pricing model | A0 approval |
| Strategic terms | A0 approval |

## Competitive Intelligence

### Key Competitors

**Big 4 / Large SIs**:
- Accenture, NTT DATA, Deloitte
- Pros: Scale, brand, resources
- Cons: Expensive, slow, junior staffing
- Our counter: Speed, senior team, value

**Atlassian Partners**:
- Eficode, Valiantys, Adaptavist
- Pros: Deep Atlassian expertise
- Cons: Less business context
- Our counter: Evidence-first, governance

**Freelancers/Small Shops**:
- Individual consultants
- Pros: Cheap, flexible
- Cons: Limited scale, no support
- Our counter: Reliability, methodology

### Win/Loss Patterns

**We win when**:
- Client values methodology over price
- Governance is a requirement
- Complex, multi-product environment
- Previous bad experience with big SI

**We lose when**:
- Pure price competition
- Client wants big brand for politics
- Very small scope (<5K)
- Relationship-based decision

## Strategic Planning

### Quarterly Review Template

1. **Results vs Plan**
   - Revenue actual vs target
   - Pipeline actual vs target
   - Win rate trends

2. **Market Insights**
   - Competitive moves
   - Pricing trends
   - Emerging opportunities

3. **Portfolio Health**
   - Active engagements status
   - Client satisfaction
   - Delivery quality

4. **Next Quarter Focus**
   - Revenue target
   - Key initiatives
   - Resource needs

## Output Standards

### Pricing Recommendation
- Clear price with rationale
- Margin analysis
- Competitive context
- Risk assessment
- Approval requirements

### Strategic Decision
- Context and options
- Recommended decision
- Expected impact
- Action items

## Handoff Rules
- To A1: Pipeline priorities, target accounts
- To A6: Pricing parameters for proposals
- From A1: Lead qualification, market intel
- From A6: Deal economics, win/loss data
"""

    async def run(self, state: A0State) -> A0State:
        """Main execution logic for A0."""
        current_task = state.get("current_task", "")
        
        self.logger.info("A0 executing", task=current_task)
        
        if current_task == "price_deal":
            return await self._price_deal(state)
        elif current_task == "analyze_pipeline":
            return await self._analyze_pipeline(state)
        elif current_task == "competitive_analysis":
            return await self._competitive_analysis(state)
        elif current_task == "quarterly_planning":
            return await self._quarterly_planning(state)
        elif current_task == "strategic_decision":
            return await self._strategic_decision(state)
        elif current_task == "market_positioning":
            return await self._market_positioning(state)
        elif current_task == "portfolio_review":
            return await self._portfolio_review(state)
        else:
            return await self._analyze_and_route(state)
    
    async def _analyze_and_route(self, state: A0State) -> A0State:
        """Route based on query type."""
        query_type = state.get("query_type", "")
        
        if query_type == "pricing":
            state["current_task"] = "price_deal"
        elif query_type == "pipeline":
            state["current_task"] = "analyze_pipeline"
        elif query_type == "competitive":
            state["current_task"] = "competitive_analysis"
        elif query_type == "planning":
            state["current_task"] = "quarterly_planning"
        elif query_type == "decision":
            state["current_task"] = "strategic_decision"
        elif query_type == "positioning":
            state["current_task"] = "market_positioning"
        else:
            state["current_task"] = "portfolio_review"
        
        return await self.run(state)
    
    async def _price_deal(self, state: A0State) -> A0State:
        """Price a specific deal."""
        self.logger.info("Pricing deal")
        
        deal_context = state.get("deal_context", {})
        
        prompt = f"""Price this deal for BlueVektor.

Deal Context:
{deal_context}

## Deal Pricing Analysis

### 1. DEAL SUMMARY
- Client: [Name]
- Segment: [Enterprise/Mid-Market/SMB]
- Engagement Type: [WP1/WP2/etc.]
- Scope: [Brief description]

### 2. SCOPE BREAKDOWN
| Component | Description | Base Days | Complexity |
|-----------|-------------|-----------|------------|
| ... | ... | ... | Low/Med/High |

### 3. EFFORT ESTIMATE
| Role | Days | Rate | Total |
|------|------|------|-------|
| Solution Architect | X | €1,800 | €X,XXX |
| Senior Consultant | X | €1,500 | €X,XXX |
| Consultant | X | €1,200 | €X,XXX |
| **Total** | **X** | - | **€XX,XXX** |

### 4. PRICING RECOMMENDATION

**Base Price**: €XX,XXX

**Adjustments**:
| Factor | Adjustment | Amount |
|--------|------------|--------|
| Segment (Enterprise/SMB) | +X% / -X% | €X,XXX |
| Complexity | +X% | €X,XXX |
| Multi-WP Bundle | -X% | -€X,XXX |
| Strategic Value | -X% | -€X,XXX |

**Final Price**: €XX,XXX

### 5. MARGIN ANALYSIS
| Metric | Value |
|--------|-------|
| Revenue | €XX,XXX |
| Estimated Cost | €XX,XXX |
| Gross Margin | €XX,XXX |
| Margin % | XX% |

**Margin Status**: ✅ Healthy / ⚠️ Review Required / ❌ Below Threshold

### 6. COMPETITIVE CONTEXT
- Expected competitor range: €XX,XXX - €XX,XXX
- Our positioning: [Premium/Competitive/Value]
- Key differentiators to emphasize: [List]

### 7. RISK FACTORS
| Risk | Impact | Mitigation |
|------|--------|------------|
| Scope creep | Medium | Clear scope doc |
| ... | ... | ... |

### 8. PRICING MODEL
- Recommended: [Fixed Price / T&M / Hybrid]
- Rationale: [Why this model]
- Payment terms: [30% deposit, milestones, etc.]

### 9. APPROVAL REQUIREMENTS
- [ ] Standard pricing - No approval needed
- [ ] >20% discount - A0 approval required
- [ ] <40% margin - A0 approval required
- [ ] Strategic terms - A0 review

### 10. RECOMMENDATION
[Final recommendation with confidence level]

**Confidence**: High/Medium/Low
**Valid Until**: [Date]

Provide a thorough, justified pricing recommendation."""
        
        response = await self.think(prompt, tier=ModelTier.REASONING)
        
        deal_id = deal_context.get("deal_id", "unknown")
        state = self.add_artifact(
            state, "deal_pricing",
            f"DealPricing_{deal_id}_{datetime.utcnow().strftime('%Y%m%d')}",
            response, {"requires_review": True}
        )
        state["recommendation_ready"] = True
        return state
    
    async def _analyze_pipeline(self, state: A0State) -> A0State:
        """Analyze sales pipeline."""
        self.logger.info("Analyzing pipeline")
        
        pipeline_data = state.get("pipeline_data", [])
        
        prompt = f"""Analyze the BlueVektor sales pipeline.

Pipeline Data:
{pipeline_data}

## Pipeline Analysis Report

### 1. EXECUTIVE SUMMARY
- Total Pipeline: €XXX,XXX
- Weighted Pipeline: €XXX,XXX
- Expected Revenue (90-day): €XXX,XXX
- Pipeline Health: [Strong/Adequate/Weak]

### 2. PIPELINE BY STAGE
| Stage | Count | Value | Weighted | Avg Age |
|-------|-------|-------|----------|---------|
| Lead | X | €XX,XXX | €X,XXX | X days |
| Qualified | X | €XX,XXX | €XX,XXX | X days |
| Discovery | X | €XX,XXX | €XX,XXX | X days |
| Proposal | X | €XX,XXX | €XX,XXX | X days |
| Negotiation | X | €XX,XXX | €XX,XXX | X days |
| **Total** | **X** | **€XXX,XXX** | **€XX,XXX** | - |

### 3. PIPELINE BY SEGMENT
| Segment | Count | Value | % of Total |
|---------|-------|-------|------------|
| Enterprise | X | €XX,XXX | XX% |
| Mid-Market | X | €XX,XXX | XX% |
| SMB | X | €XX,XXX | XX% |

### 4. PIPELINE BY OFFERING
| Engagement Type | Count | Value |
|-----------------|-------|-------|
| WP1 Diagnostic | X | €XX,XXX |
| WP2 Migration | X | €XX,XXX |
| WP4 Governance | X | €XX,XXX |
| Other | X | €XX,XXX |

### 5. TOP OPPORTUNITIES
| Rank | Opportunity | Client | Value | Stage | Expected Close |
|------|-------------|--------|-------|-------|----------------|
| 1 | ... | ... | €XX,XXX | ... | MM/DD |
| 2 | ... | ... | €XX,XXX | ... | MM/DD |
| 3 | ... | ... | €XX,XXX | ... | MM/DD |

### 6. AT-RISK OPPORTUNITIES
| Opportunity | Risk | Action Required |
|-------------|------|-----------------|
| ... | Stalled >30 days | Follow-up call |
| ... | Competitor threat | Differentiation |

### 7. QUICK WINS
| Opportunity | Value | Close In | Action |
|-------------|-------|----------|--------|
| ... | €X,XXX | <2 weeks | Send proposal |

### 8. PIPELINE GAPS
- **Segment gaps**: [e.g., Low enterprise coverage]
- **Stage gaps**: [e.g., Not enough in Discovery]
- **Offering gaps**: [e.g., No WP4 opportunities]

### 9. CONVERSION METRICS
| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| Lead to Qualified | XX% | 30% | ... |
| Qualified to Proposal | XX% | 50% | ... |
| Proposal to Won | XX% | 40% | ... |
| Overall Win Rate | XX% | 25% | ... |
| Avg Deal Size | €XX,XXX | €20,000 | ... |

### 10. RECOMMENDATIONS
1. **Immediate**: [Action for this week]
2. **Short-term**: [Actions for this month]
3. **Strategic**: [Longer-term improvements]

### 11. FORECAST
| Period | Conservative | Expected | Optimistic |
|--------|--------------|----------|------------|
| This Month | €XX,XXX | €XX,XXX | €XX,XXX |
| Next Month | €XX,XXX | €XX,XXX | €XX,XXX |
| This Quarter | €XX,XXX | €XX,XXX | €XX,XXX |

Provide actionable pipeline insights."""
        
        response = await self.think(prompt, tier=ModelTier.REASONING)
        
        state = self.add_artifact(
            state, "pipeline_analysis",
            f"PipelineAnalysis_{datetime.utcnow().strftime('%Y%m%d')}",
            response
        )
        state["analysis_complete"] = True
        return state
    
    async def _competitive_analysis(self, state: A0State) -> A0State:
        """Perform competitive analysis."""
        self.logger.info("Competitive analysis")
        
        market_context = state.get("market_context", {})
        
        prompt = f"""Provide competitive intelligence for BlueVektor.

Market Context:
{market_context}

## Competitive Intelligence Report

### 1. MARKET OVERVIEW
- Market size estimate: €XX billion (Atlassian services EU)
- Growth rate: X% annually
- Key trends:
  1. [Trend 1]
  2. [Trend 2]
  3. [Trend 3]

### 2. COMPETITIVE LANDSCAPE

#### Tier 1: Large System Integrators
| Competitor | Strengths | Weaknesses | Pricing | Win Against |
|------------|-----------|------------|---------|-------------|
| Accenture | Brand, scale | Expensive, slow | Premium+ | Speed, value |
| NTT DATA | Technical | Less Atlassian focus | Premium | Specialization |
| Deloitte | Relationships | Junior staffing | Premium | Senior team |

#### Tier 2: Atlassian Specialists
| Competitor | Strengths | Weaknesses | Pricing | Win Against |
|------------|-----------|------------|---------|-------------|
| Eficode | Nordic presence | Less EU-wide | Market | Local presence |
| Valiantys | Experience | Large company feel | Market | Agility |
| Adaptavist | App expertise | Less consulting | Market | Methodology |

#### Tier 3: Boutiques & Freelancers
| Competitor | Strengths | Weaknesses | Pricing | Win Against |
|------------|-----------|------------|---------|-------------|
| Local boutiques | Price, relationships | Limited scale | Discount | Reliability |
| Freelancers | Very cheap | No support | Deep discount | Quality, support |

### 3. COMPETITIVE POSITIONING MAP

```
                    HIGH PRICE
                        |
    Big 4/SIs           |
         X              |
                        |
                   BlueVektor
                      (here)
                        |
LOW EXPERTISE --------- | --------- HIGH EXPERTISE
                        |
                        |     Atlassian Partners
                        |           X
                        |
    Freelancers         |
         X              |
                    LOW PRICE
```

### 4. WIN/LOSS ANALYSIS

**Recent Wins**:
| Deal | Competitor | Why We Won |
|------|------------|------------|
| ... | ... | ... |

**Recent Losses**:
| Deal | Competitor | Why We Lost | Lesson |
|------|------------|-------------|--------|
| ... | ... | ... | ... |

### 5. PRICING INTELLIGENCE
- Big 4 rates: €2,000-3,500/day
- Atlassian Partners: €1,200-2,000/day
- Boutiques: €800-1,500/day
- Freelancers: €400-800/day

**Our position**: Upper mid-market (€1,200-2,200/day)

### 6. EMERGING THREATS
1. [Threat 1]: [Description and mitigation]
2. [Threat 2]: [Description and mitigation]

### 7. OPPORTUNITIES
1. [Opportunity 1]: [How to capitalize]
2. [Opportunity 2]: [How to capitalize]

### 8. BATTLE CARDS

#### vs. Accenture/Big 4
- **Their pitch**: Brand, global scale, one-stop-shop
- **Our counter**: Faster delivery, senior team, 40% less cost
- **Key question to ask**: "How many of their proposed team have actual Atlassian Cloud experience?"

#### vs. Atlassian Partners
- **Their pitch**: Deep technical expertise
- **Our counter**: Business-first approach, governance included
- **Key question to ask**: "Do they include governance in their methodology?"

### 9. RECOMMENDATIONS
1. [Strategic recommendation 1]
2. [Strategic recommendation 2]
3. [Strategic recommendation 3]

Provide actionable competitive intelligence."""
        
        response = await self.think(prompt, tier=ModelTier.REASONING)
        
        state = self.add_artifact(
            state, "competitive_analysis",
            f"CompetitiveAnalysis_{datetime.utcnow().strftime('%Y%m%d')}",
            response
        )
        state["analysis_complete"] = True
        return state
    
    async def _quarterly_planning(self, state: A0State) -> A0State:
        """Create quarterly plan."""
        self.logger.info("Quarterly planning")
        
        market_context = state.get("market_context", {})
        
        prompt = f"""Create a quarterly strategic plan for BlueVektor.

Context:
{market_context}

## Quarterly Strategic Plan

### QUARTER: Q[X] {datetime.utcnow().year}

### 1. EXECUTIVE SUMMARY
- Revenue Target: €XXX,XXX
- Pipeline Target: €XXX,XXX (3x coverage)
- Key Theme: [e.g., "Foundation for Scale"]

### 2. FINANCIAL TARGETS
| Metric | Target | Stretch |
|--------|--------|---------|
| Revenue | €XXX,XXX | €XXX,XXX |
| New Clients | X | X |
| Avg Deal Size | €XX,XXX | €XX,XXX |
| Win Rate | XX% | XX% |
| Gross Margin | XX% | XX% |

### 3. STRATEGIC PRIORITIES

#### Priority 1: [Name]
- **Objective**: [What we want to achieve]
- **Key Results**:
  - KR1: [Measurable result]
  - KR2: [Measurable result]
- **Owner**: [Who]
- **Resources**: [What's needed]

#### Priority 2: [Name]
[Same structure]

#### Priority 3: [Name]
[Same structure]

### 4. GO-TO-MARKET FOCUS

**Target Segments**:
- Primary: [Segment] - XX% of effort
- Secondary: [Segment] - XX% of effort

**Target Offerings**:
- Lead with: WP1 (land strategy)
- Expand to: WP2, WP4 (expand strategy)

**Target Industries**:
1. [Industry 1]
2. [Industry 2]

### 5. KEY INITIATIVES

| Initiative | Owner | Timeline | Investment |
|------------|-------|----------|------------|
| ... | ... | ... | ... |

### 6. RESOURCE PLAN

**Current Team**: X FTEs
**Target Team**: X FTEs

**Hiring Needs**:
| Role | When | Priority |
|------|------|----------|
| ... | ... | ... |

**Capacity Planning**:
| Month | Available Days | Committed | Utilization |
|-------|----------------|-----------|-------------|
| M1 | XX | XX | XX% |
| M2 | XX | XX | XX% |
| M3 | XX | XX | XX% |

### 7. INVESTMENT PRIORITIES

| Investment | Amount | Expected Return |
|------------|--------|-----------------|
| Marketing | €X,XXX | X leads |
| Tools | €X,XXX | X% efficiency |
| Training | €X,XXX | Capability |

### 8. RISKS & MITIGATIONS

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| ... | High/Med/Low | High/Med/Low | ... |

### 9. KEY MILESTONES

| Date | Milestone | Success Criteria |
|------|-----------|------------------|
| Week 2 | ... | ... |
| Week 6 | ... | ... |
| Week 10 | ... | ... |
| Week 13 | ... | ... |

### 10. SUCCESS METRICS

**Leading Indicators** (weekly):
- Pipeline added
- Meetings held
- Proposals sent

**Lagging Indicators** (monthly):
- Revenue closed
- Win rate
- Client satisfaction

### 11. REVIEW CADENCE
- Weekly: Pipeline review
- Bi-weekly: Delivery review
- Monthly: Full business review
- End of quarter: Strategic review

Create an actionable, measurable plan."""
        
        response = await self.think(prompt, tier=ModelTier.REASONING)
        
        state = self.add_artifact(
            state, "quarterly_plan",
            f"QuarterlyPlan_{datetime.utcnow().strftime('%Y%m%d')}",
            response, {"requires_review": True}
        )
        state["recommendation_ready"] = True
        return state
    
    async def _strategic_decision(self, state: A0State) -> A0State:
        """Make a strategic decision."""
        self.logger.info("Strategic decision")
        
        deal_context = state.get("deal_context", {})
        
        prompt = f"""Analyze and recommend on this strategic decision.

Context:
{deal_context}

## Strategic Decision Analysis

### 1. DECISION CONTEXT
**Question**: [What decision needs to be made?]
**Urgency**: [Critical/High/Medium/Low]
**Reversibility**: [Easy/Moderate/Difficult to reverse]

### 2. SITUATION ANALYSIS
[Describe the current situation and why a decision is needed]

### 3. OPTIONS ANALYSIS

#### Option A: [Name]
**Description**: [What this option entails]

**Pros**:
- [Pro 1]
- [Pro 2]

**Cons**:
- [Con 1]
- [Con 2]

**Financial Impact**: [Revenue/cost implications]
**Risk Level**: High/Medium/Low
**Effort Required**: High/Medium/Low

#### Option B: [Name]
[Same structure]

#### Option C: [Name]
[Same structure]

### 4. DECISION MATRIX

| Criteria | Weight | Option A | Option B | Option C |
|----------|--------|----------|----------|----------|
| Revenue Impact | 30% | X/5 | X/5 | X/5 |
| Strategic Fit | 25% | X/5 | X/5 | X/5 |
| Risk | 20% | X/5 | X/5 | X/5 |
| Effort | 15% | X/5 | X/5 | X/5 |
| Time to Value | 10% | X/5 | X/5 | X/5 |
| **Weighted Score** | 100% | X.X | X.X | X.X |

### 5. RECOMMENDATION

**Recommended Option**: [Option X]

**Rationale**:
[Why this is the best choice]

**Key Assumptions**:
1. [Assumption 1]
2. [Assumption 2]

**Confidence Level**: High/Medium/Low

### 6. IMPLEMENTATION PLAN

**If approved**:
| Action | Owner | Timeline |
|--------|-------|----------|
| ... | ... | ... |

### 7. SUCCESS METRICS
- [How we'll know this was the right decision]

### 8. CONTINGENCY
- [What we'll do if this doesn't work]

### 9. DECISION RECORD

**Decision**: [Approved option]
**Date**: {datetime.utcnow().strftime('%Y-%m-%d')}
**Review Date**: [When to revisit]

Provide a clear, well-reasoned recommendation."""
        
        response = await self.think(prompt, tier=ModelTier.REASONING)
        
        state = self.add_artifact(
            state, "strategic_decision",
            f"StrategicDecision_{datetime.utcnow().strftime('%Y%m%d')}",
            response, {"requires_review": True}
        )
        state["recommendation_ready"] = True
        return state
    
    async def _market_positioning(self, state: A0State) -> A0State:
        """Define market positioning."""
        self.logger.info("Market positioning")
        
        prompt = f"""Define BlueVektor's market positioning.

## Market Positioning Strategy

### 1. POSITIONING STATEMENT

**For** [target customer]
**Who** [has this need/problem]
**BlueVektor is** [category]
**That** [key benefit]
**Unlike** [competitors]
**We** [key differentiator]

### 2. VALUE PROPOSITION

**Primary Value Proposition**:
[One sentence that captures our core value]

**Supporting Messages**:
1. [Message 1]
2. [Message 2]
3. [Message 3]

### 3. TARGET PERSONAS

#### Persona 1: IT Director
- **Title**: IT Director / Head of IT
- **Company**: Mid-market (500-2000 employees)
- **Pain Points**:
  - [Pain 1]
  - [Pain 2]
- **Goals**:
  - [Goal 1]
  - [Goal 2]
- **Objections**:
  - [Objection 1] → [Counter]
  - [Objection 2] → [Counter]
- **Buying Triggers**:
  - [Trigger 1]
  - [Trigger 2]

#### Persona 2: CTO / VP Engineering
[Same structure]

#### Persona 3: Platform Owner
[Same structure]

### 4. COMPETITIVE DIFFERENTIATION

| Attribute | BlueVektor | Big 4 | Atlassian Partners |
|-----------|------------|-------|-------------------|
| Methodology | Evidence-first | Process-heavy | Technical-first |
| Team | All senior | Junior-heavy | Mixed |
| Speed | Fast | Slow | Medium |
| Price | Value | Premium | Market |
| Governance | Built-in | Add-on | Afterthought |
| AI-Augmented | Yes | Limited | No |

### 5. KEY MESSAGES BY SEGMENT

**Enterprise**:
- "Enterprise-grade methodology without enterprise-level bureaucracy"
- Key proof: [Case study/credential]

**Mid-Market**:
- "Right-sized expertise for growing companies"
- Key proof: [Case study/credential]

**SMB**:
- "Get it right the first time - avoid expensive mistakes"
- Key proof: [Case study/credential]

### 6. PROOF POINTS
1. [Proof point 1]
2. [Proof point 2]
3. [Proof point 3]

### 7. BRAND VOICE
- **Tone**: Professional but approachable
- **Style**: Clear, jargon-free, confident
- **Personality**: Trusted advisor, not vendor

### 8. KEY PHRASES TO USE
- "Evidence-first transformation"
- "Governance by design"
- "Senior-led delivery"
- "Prove before we propose"

### 9. PHRASES TO AVOID
- "Best practices" (overused)
- "Synergy" (corporate speak)
- "Leverage" (jargon)
- "Cutting-edge" (cliché)

### 10. CHANNEL STRATEGY
| Channel | Priority | Use Case |
|---------|----------|----------|
| LinkedIn | High | Thought leadership, outreach |
| Website | High | Credibility, conversion |
| Events | Medium | Networking, visibility |
| Email | Medium | Nurture, follow-up |

Create a distinctive, defensible position."""
        
        response = await self.think(prompt, tier=ModelTier.REASONING)
        
        state = self.add_artifact(
            state, "market_positioning",
            f"MarketPositioning_{datetime.utcnow().strftime('%Y%m%d')}",
            response
        )
        state["analysis_complete"] = True
        return state
    
    async def _portfolio_review(self, state: A0State) -> A0State:
        """Review current portfolio health."""
        self.logger.info("Portfolio review")
        
        prompt = f"""Provide a portfolio health review for BlueVektor.

## Portfolio Health Review

### 1. EXECUTIVE SUMMARY
- Active Engagements: X
- Total Contract Value: €XXX,XXX
- Overall Health: [Healthy/At Risk/Critical]
- Key Actions Required: [List]

### 2. ACTIVE ENGAGEMENTS

| Client | Project | Value | Status | Health | Next Milestone |
|--------|---------|-------|--------|--------|----------------|
| ... | WP1 | €X,XXX | In Progress | 🟢 | ... |
| ... | WP2 | €XX,XXX | In Progress | 🟡 | ... |
| ... | WP4 | €X,XXX | Completing | 🟢 | ... |

### 3. HEALTH INDICATORS

| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| On-Time Delivery | XX% | 90% | 🟢/🟡/🔴 |
| Client Satisfaction | X.X/5 | 4.5/5 | 🟢/🟡/🔴 |
| Scope Changes | XX% | <10% | 🟢/🟡/🔴 |
| Budget Variance | XX% | <5% | 🟢/🟡/🔴 |
| Resource Utilization | XX% | 80% | 🟢/🟡/🔴 |

### 4. AT-RISK ENGAGEMENTS

| Engagement | Risk | Impact | Mitigation |
|------------|------|--------|------------|
| ... | [Description] | High/Med/Low | [Action] |

### 5. REVENUE TRACKING

| Period | Target | Actual | Variance |
|--------|--------|--------|----------|
| This Month | €XX,XXX | €XX,XXX | +/-XX% |
| This Quarter | €XXX,XXX | €XXX,XXX | +/-XX% |
| YTD | €XXX,XXX | €XXX,XXX | +/-XX% |

### 6. RESOURCE UTILIZATION

| Consultant | Allocated | Utilization | Notes |
|------------|-----------|-------------|-------|
| ... | XX% | Optimal/High/Low | ... |

### 7. CLIENT SATISFACTION

**Recent Feedback**:
- [Client A]: [Feedback summary]
- [Client B]: [Feedback summary]

**NPS Score**: XX (Target: >50)

### 8. EXPANSION OPPORTUNITIES

| Client | Current | Opportunity | Est. Value | Next Step |
|--------|---------|-------------|------------|-----------|
| ... | WP1 | WP2 + WP4 | €XX,XXX | Propose |

### 9. LESSONS LEARNED
1. [Lesson 1]
2. [Lesson 2]

### 10. ACTIONS REQUIRED
| Action | Owner | Due | Priority |
|--------|-------|-----|----------|
| ... | ... | ... | High/Med/Low |

Provide actionable portfolio insights."""
        
        response = await self.think(prompt, tier=ModelTier.REASONING)
        
        state = self.add_artifact(
            state, "portfolio_review",
            f"PortfolioReview_{datetime.utcnow().strftime('%Y%m%d')}",
            response
        )
        state["analysis_complete"] = True
        return state


def create_a0_agent() -> A0StrategistAgent:
    """Factory function to create A0 agent."""
    return A0StrategistAgent()
