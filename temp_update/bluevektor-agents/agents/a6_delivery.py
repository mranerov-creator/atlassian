"""
BlueVektor Agents - A6: Delivery PM/QA
Quality assurance, project management, and proposal generation.
"""
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from agents.base import AgentConfig, AgentState, BaseAgent
from core.llm import ModelTier


# =============================================================================
# A6 Enums
# =============================================================================

class DeliverableStatus(str, Enum):
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    REVISION_NEEDED = "revision_needed"
    APPROVED = "approved"
    FINAL = "final"


class DeliverableType(str, Enum):
    OPPORTUNITY_BRIEF = "opportunity_brief"
    SOW = "sow"
    PROPOSAL = "proposal"
    WP1_REPORT = "wp1_report"
    WP4_HANDBOOK = "wp4_handbook"
    PRESENTATION = "presentation"
    PLAN_30_60_90 = "plan_30_60_90"
    RUNBOOK = "runbook"
    OTHER = "other"


class QACheckResult(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    NOT_APPLICABLE = "n/a"


class RiskLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RiskCategory(str, Enum):
    SCOPE = "scope"
    TIMELINE = "timeline"
    RESOURCE = "resource"
    TECHNICAL = "technical"
    COMMERCIAL = "commercial"
    DEPENDENCY = "dependency"
    CLIENT = "client"


class WorkpackageType(str, Enum):
    WP1 = "wp1"  # Cloud Transformation Diagnostic
    WP2 = "wp2"  # Migration Execution
    WP3 = "wp3"  # Custom Development
    WP4 = "wp4"  # Governance Office-in-a-Box
    WP5 = "wp5"  # Hypercare & Support
    CUSTOM = "custom"


class EngagementType(str, Enum):
    FIXED_PRICE = "fixed_price"
    TIME_AND_MATERIALS = "time_and_materials"
    RETAINER = "retainer"
    HYBRID = "hybrid"


# =============================================================================
# A6 QA Schemas
# =============================================================================

class QACheck(BaseModel):
    """Individual QA check item."""
    id: str
    category: str
    check_name: str
    description: str
    result: QACheckResult = QACheckResult.PASS
    notes: str | None = None
    auto_fixable: bool = False
    fix_suggestion: str | None = None


class QAChecklist(BaseModel):
    """Complete QA checklist for a deliverable."""
    deliverable_type: DeliverableType
    deliverable_name: str
    version: str = "1.0"
    
    # Checks by category
    structure_checks: list[QACheck] = Field(default_factory=list)
    content_checks: list[QACheck] = Field(default_factory=list)
    style_checks: list[QACheck] = Field(default_factory=list)
    accuracy_checks: list[QACheck] = Field(default_factory=list)
    compliance_checks: list[QACheck] = Field(default_factory=list)
    
    # Summary
    total_checks: int = 0
    passed: int = 0
    failed: int = 0
    warnings: int = 0
    
    # Overall
    qa_score: int = Field(0, ge=0, le=100)
    approved: bool = False
    reviewer: str | None = None
    
    # Timestamps
    reviewed_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class DefinitionOfDone(BaseModel):
    """Definition of Done criteria for deliverables."""
    deliverable_type: DeliverableType
    criteria: list[str] = Field(default_factory=list)
    mandatory_sections: list[str] = Field(default_factory=list)
    quality_standards: list[str] = Field(default_factory=list)
    approval_required_from: list[str] = Field(default_factory=list)


# =============================================================================
# A6 Project Management Schemas
# =============================================================================

class Milestone(BaseModel):
    """Project milestone."""
    id: str
    name: str
    description: str | None = None
    due_date: str
    deliverables: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    status: str = "planned"  # planned, in_progress, completed, delayed
    completion_date: str | None = None


class Risk(BaseModel):
    """Project risk."""
    id: str
    category: RiskCategory
    description: str
    probability: str  # high, medium, low
    impact: str  # high, medium, low
    level: RiskLevel
    mitigation: str
    owner: str | None = None
    status: str = "open"  # open, mitigated, closed, accepted


class Issue(BaseModel):
    """Project issue / action item."""
    id: str
    title: str
    description: str
    priority: str  # critical, high, medium, low
    owner: str | None = None
    due_date: str | None = None
    status: str = "open"  # open, in_progress, resolved, closed
    resolution: str | None = None


class Decision(BaseModel):
    """Project decision log entry."""
    id: str
    date: str
    topic: str
    decision: str
    rationale: str
    decided_by: list[str] = Field(default_factory=list)
    impacts: list[str] = Field(default_factory=list)


class RAIDLog(BaseModel):
    """RAID log (Risks, Actions, Issues, Decisions)."""
    engagement_id: str
    risks: list[Risk] = Field(default_factory=list)
    actions: list[Issue] = Field(default_factory=list)  # Action items
    issues: list[Issue] = Field(default_factory=list)
    decisions: list[Decision] = Field(default_factory=list)
    last_updated: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class ProjectPlan(BaseModel):
    """Project plan for a workpackage engagement."""
    engagement_id: str
    engagement_name: str
    client_name: str
    workpackage: WorkpackageType
    
    # Timeline
    start_date: str
    end_date: str
    duration_weeks: int
    
    # Milestones
    milestones: list[Milestone] = Field(default_factory=list)
    
    # Team
    bluevektor_team: list[dict[str, str]] = Field(default_factory=list)
    client_team: list[dict[str, str]] = Field(default_factory=list)
    
    # Governance
    status_cadence: str = "weekly"
    steering_cadence: str = "bi-weekly"
    
    # RAID
    raid_log: RAIDLog | None = None
    
    # Status
    overall_status: str = "green"  # green, amber, red
    percent_complete: int = 0
    
    # Metadata
    version: str = "1.0"
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# =============================================================================
# A6 Proposal / SoW Schemas
# =============================================================================

class LineItem(BaseModel):
    """Pricing line item."""
    id: str
    description: str
    quantity: float
    unit: str  # days, hours, units
    unit_price: float
    total: float
    notes: str | None = None


class PricingSection(BaseModel):
    """Pricing section in proposal."""
    section_name: str
    line_items: list[LineItem] = Field(default_factory=list)
    subtotal: float = 0.0
    discount_percent: float = 0.0
    discount_amount: float = 0.0
    section_total: float = 0.0


class PaymentTerms(BaseModel):
    """Payment terms."""
    payment_type: EngagementType
    currency: str = "EUR"
    
    # For fixed price
    milestones_payments: list[dict[str, Any]] = Field(default_factory=list)
    
    # For T&M
    daily_rate: float | None = None
    monthly_cap: float | None = None
    
    # General
    payment_terms_days: int = 30
    invoicing_frequency: str = "monthly"  # monthly, milestone, completion
    
    # Expenses
    expenses_included: bool = True
    expenses_cap: float | None = None


class ScopeItem(BaseModel):
    """Scope item (in-scope or out-of-scope)."""
    item: str
    details: str | None = None


class Assumption(BaseModel):
    """Project assumption."""
    id: str
    assumption: str
    impact_if_wrong: str | None = None


class StatementOfWork(BaseModel):
    """Complete Statement of Work document."""
    
    # Header
    document_id: str
    version: str = "1.0"
    status: DeliverableStatus = DeliverableStatus.DRAFT
    
    # Parties
    client_name: str
    client_contact: str | None = None
    client_address: str | None = None
    
    # Engagement overview
    engagement_name: str
    workpackages: list[WorkpackageType]
    engagement_type: EngagementType
    
    # Executive summary
    executive_summary: str
    
    # Background & objectives
    background: str
    objectives: list[str] = Field(default_factory=list)
    success_criteria: list[str] = Field(default_factory=list)
    
    # Scope
    in_scope: list[ScopeItem] = Field(default_factory=list)
    out_of_scope: list[ScopeItem] = Field(default_factory=list)
    
    # Deliverables
    deliverables: list[dict[str, Any]] = Field(default_factory=list)
    
    # Timeline
    start_date: str | None = None
    end_date: str | None = None
    duration_weeks: int | None = None
    milestones: list[Milestone] = Field(default_factory=list)
    
    # Team & responsibilities
    bluevektor_responsibilities: list[str] = Field(default_factory=list)
    client_responsibilities: list[str] = Field(default_factory=list)
    
    # Pricing
    pricing_sections: list[PricingSection] = Field(default_factory=list)
    total_investment: float = 0.0
    payment_terms: PaymentTerms | None = None
    
    # Terms
    assumptions: list[Assumption] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    risks: list[Risk] = Field(default_factory=list)
    
    # Change control
    change_control_process: str | None = None
    
    # Acceptance
    acceptance_criteria: list[str] = Field(default_factory=list)
    
    # Signatures (placeholders)
    client_signatory: str | None = None
    bluevektor_signatory: str = "BlueVektor"
    
    # Metadata
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    valid_until: str | None = None


class ProposalOnePager(BaseModel):
    """One-page proposal summary."""
    client_name: str
    engagement_name: str
    
    # The hook
    headline: str
    problem_statement: str
    
    # The solution
    approach_summary: str
    key_deliverables: list[str]
    
    # The proof
    why_bluevektor: list[str]
    relevant_experience: str | None = None
    
    # The ask
    investment_range: str
    timeline_summary: str
    next_steps: list[str]
    
    # CTA
    call_to_action: str
    contact_info: str = "hello@bluevektor.com"
    
    # Metadata
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# =============================================================================
# A6 Capacity Management
# =============================================================================

class CapacitySlot(BaseModel):
    """Available capacity slot."""
    start_date: str
    end_date: str
    available_days: int
    engagement_id: str | None = None
    status: str = "available"  # available, tentative, booked


class CapacityPlan(BaseModel):
    """Capacity and availability planning."""
    resource_name: str = "BlueVektor"
    
    # Capacity settings
    days_per_week: float = 4.0  # Assumes 1 day for admin/sales
    max_concurrent_engagements: int = 2
    
    # Current commitments
    current_engagements: list[dict[str, Any]] = Field(default_factory=list)
    
    # Available slots
    available_slots: list[CapacitySlot] = Field(default_factory=list)
    
    # Next available
    next_available_date: str | None = None
    
    # Utilization
    current_utilization_percent: float = 0.0
    
    as_of: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# =============================================================================
# A6 Agent State
# =============================================================================

class A6State(AgentState, total=False):
    """State specific to A6 agent."""
    
    # Inputs
    client_name: str
    engagement_id: str
    opportunity_brief: dict[str, Any]
    deliverable_content: str
    deliverable_type: DeliverableType
    
    # QA
    qa_checklist: QAChecklist | None
    qa_feedback: str
    revision_requests: list[str]
    
    # Project management
    project_plan: ProjectPlan | None
    raid_log: RAIDLog | None
    
    # Proposals
    sow: StatementOfWork | None
    one_pager: ProposalOnePager | None
    
    # Capacity
    capacity_plan: CapacityPlan | None
    
    # Workflow tracking
    qa_passed: bool
    proposal_generated: bool
    plan_created: bool


# =============================================================================
# A6 Agent
# =============================================================================

class A6DeliveryAgent(BaseAgent):
    """
    A6 - Delivery PM/QA Agent
    
    Purpose: Ensure quality of all deliverables, manage project execution,
    and generate professional proposals and SoWs.
    
    Key functions:
    - QA review of deliverables against DoD
    - Project planning and RAID management
    - SoW and proposal generation
    - Capacity planning
    - Effort estimation
    """
    
    def __init__(self):
        config = AgentConfig(
            id="a6",
            name="Delivery PM/QA",
            role="Quality Assurance & Project Management",
            goal="Ensure delivery excellence through quality control, professional proposals, and effective project management",
            backstory="""You are the quality guardian and delivery backbone of BlueVektor.
Every deliverable passes through your rigorous review before reaching clients.

Your expertise includes:
- Professional services delivery methodology
- Quality assurance frameworks and checklists
- Statement of Work and proposal writing
- Project planning and risk management
- Effort estimation and capacity planning

You have high standards but are pragmatic. You balance thoroughness with 
delivery speed. Your feedback is constructive and specific.

Key principles:
- Every deliverable has a Definition of Done
- Evidence-based recommendations only
- Client-ready quality on first delivery
- Clear, professional communication
- Realistic timelines and estimates

You work closely with A1 (for proposals), A3 (for WP1 reports), 
and A4 (for WP4 handbooks).""",
            model_tier=ModelTier.STANDARD,
            temperature=0.5,  # Lower for consistency
            max_tokens=8192,
            tools=["filesystem", "templates", "calendar"],
            allowed_handoffs=["a1", "a3", "a4", "a0"],
            artifacts_requiring_approval=["sow", "proposal", "project_plan"],
        )
        super().__init__(config)
        
        # Initialize DoD templates
        self._dod_templates = self._init_dod_templates()
    
    def _init_dod_templates(self) -> dict[DeliverableType, DefinitionOfDone]:
        """Initialize Definition of Done templates."""
        return {
            DeliverableType.OPPORTUNITY_BRIEF: DefinitionOfDone(
                deliverable_type=DeliverableType.OPPORTUNITY_BRIEF,
                criteria=[
                    "Problem statement is clear and specific",
                    "Business context is documented",
                    "Decision makers identified with roles",
                    "Qualification criteria assessed (BANT/CHAMP)",
                    "Proposed scope and workpackages defined",
                    "Timeline and urgency captured",
                    "Next steps are actionable",
                ],
                mandatory_sections=[
                    "Problem Statement",
                    "Business Context",
                    "Stakeholders",
                    "Qualification",
                    "Proposed Scope",
                    "Next Steps",
                ],
                quality_standards=[
                    "No spelling or grammar errors",
                    "Professional tone",
                    "Consistent formatting",
                    "All claims evidence-based",
                ],
                approval_required_from=["human"],
            ),
            DeliverableType.WP1_REPORT: DefinitionOfDone(
                deliverable_type=DeliverableType.WP1_REPORT,
                criteria=[
                    "Executive summary is <1 page",
                    "All findings linked to evidence",
                    "Hotspots scored and prioritized",
                    "Quick wins clearly identified",
                    "30/60/90 plan is actionable",
                    "Resource estimates provided",
                    "Recommendations are specific",
                ],
                mandatory_sections=[
                    "Executive Summary",
                    "Scope & Methodology",
                    "Current State Assessment",
                    "Volumetrics",
                    "Findings & Hotspots",
                    "Recommendations",
                    "30/60/90 Plan",
                ],
                quality_standards=[
                    "Executive-ready language",
                    "Visual-friendly formatting",
                    "Consistent terminology",
                    "All data sourced",
                    "Actionable recommendations",
                ],
                approval_required_from=["human", "internal_review"],
            ),
            DeliverableType.SOW: DefinitionOfDone(
                deliverable_type=DeliverableType.SOW,
                criteria=[
                    "Scope is unambiguous",
                    "Deliverables are specific and measurable",
                    "Timeline is realistic",
                    "Pricing is complete and accurate",
                    "Assumptions are documented",
                    "Change control defined",
                    "Acceptance criteria clear",
                ],
                mandatory_sections=[
                    "Executive Summary",
                    "Background & Objectives",
                    "Scope (In/Out)",
                    "Deliverables",
                    "Timeline & Milestones",
                    "Pricing & Payment",
                    "Assumptions & Constraints",
                    "Acceptance Criteria",
                ],
                quality_standards=[
                    "Legal review compatible",
                    "No ambiguous language",
                    "Consistent terminology",
                    "Professional formatting",
                    "Complete pricing breakdown",
                ],
                approval_required_from=["human", "pricing_review"],
            ),
            DeliverableType.PLAN_30_60_90: DefinitionOfDone(
                deliverable_type=DeliverableType.PLAN_30_60_90,
                criteria=[
                    "Each phase has clear objectives",
                    "Actions are specific and assignable",
                    "Dependencies identified",
                    "Success criteria defined",
                    "Resource requirements stated",
                    "Risks acknowledged",
                ],
                mandatory_sections=[
                    "Days 1-30",
                    "Days 31-60",
                    "Days 61-90",
                    "Success Metrics",
                    "Resource Requirements",
                ],
                quality_standards=[
                    "Realistic timeline",
                    "Actionable items",
                    "Clear ownership",
                    "Measurable outcomes",
                ],
                approval_required_from=["human"],
            ),
        }
    
    def system_prompt(self) -> str:
        """System prompt for A6."""
        base = self.build_base_prompt()
        
        return f"""{base}

# A6-Specific Rules

## Quality Assurance Standards

### QA Review Process
1. Check against Definition of Done (DoD)
2. Verify mandatory sections present
3. Assess content quality
4. Check formatting and style
5. Validate accuracy and evidence
6. Provide specific, actionable feedback

### QA Categories
- **Structure**: Document organization, sections, flow
- **Content**: Completeness, accuracy, relevance
- **Style**: Tone, language, readability
- **Accuracy**: Facts, figures, evidence linking
- **Compliance**: BlueVektor standards, client requirements

### Scoring
- 90-100: Excellent, ready for client
- 80-89: Good, minor polish needed
- 70-79: Acceptable, some revisions required
- 60-69: Needs work, significant revisions
- <60: Not acceptable, major rewrite needed

## Proposal Writing Standards

### SoW Structure
1. Executive Summary (half page max)
2. Background & Context
3. Objectives (SMART format)
4. Scope Definition (crystal clear)
5. Deliverables (specific, measurable)
6. Timeline with milestones
7. Investment (transparent breakdown)
8. Assumptions & Dependencies
9. Terms & Conditions

### Pricing Guidelines
- WP1 Diagnostic: 5-10 days depending on complexity
- WP4 Governance: 10-20 days depending on scope
- Always break down by activity
- Include assumptions affecting price
- State validity period (typically 30 days)

### One-Pager Format
- Hook: Problem statement (2-3 sentences)
- Solution: Our approach (3-4 bullets)
- Proof: Why BlueVektor (3 bullets)
- Investment: Range (not exact)
- CTA: Clear next step

## Project Management Standards

### RAID Log
- **R**isks: Probability × Impact scoring
- **A**ctions: Owner, due date, status
- **I**ssues: Priority, escalation path
- **D**ecisions: Rationale documented

### Status Reporting
- Green: On track
- Amber: Minor concerns, mitigation in place
- Red: Significant risk, escalation needed

## Effort Estimation

### Standard Estimates (days)
| Activity | Small | Medium | Large |
|----------|-------|--------|-------|
| Discovery | 0.5 | 1 | 2 |
| Evidence Collection | 1 | 2 | 4 |
| Analysis | 1 | 2 | 4 |
| Report Writing | 1 | 2 | 3 |
| Review & Revision | 0.5 | 1 | 2 |
| Presentation | 0.5 | 1 | 1 |

### Complexity Factors
- Multi-instance: +50%
- JSM included: +30%
- Complex integrations: +25%
- Tight timeline: +20%

## Handoff Rules
- From A1: Review opportunity briefs, generate proposals
- From A3: QA WP1 reports before client delivery
- From A4: QA WP4 handbooks
- To A0: Pricing exceptions, strategic decisions
"""

    async def run(self, state: A6State) -> A6State:
        """Main execution logic for A6."""
        current_task = state.get("current_task", "")
        
        self.logger.info("A6 executing", task=current_task)
        
        if current_task == "qa_review":
            return await self._qa_review(state)
        elif current_task == "generate_sow":
            return await self._generate_sow(state)
        elif current_task == "generate_one_pager":
            return await self._generate_one_pager(state)
        elif current_task == "create_project_plan":
            return await self._create_project_plan(state)
        elif current_task == "estimate_effort":
            return await self._estimate_effort(state)
        elif current_task == "update_raid":
            return await self._update_raid(state)
        elif current_task == "check_capacity":
            return await self._check_capacity(state)
        else:
            return await self._analyze_and_route(state)
    
    # -------------------------------------------------------------------------
    # Core Functions
    # -------------------------------------------------------------------------
    
    async def _analyze_and_route(self, state: A6State) -> A6State:
        """Analyze input and determine appropriate action."""
        input_data = state.get("input_data", {})
        
        # Check what type of request this is
        if state.get("deliverable_content"):
            state["current_task"] = "qa_review"
        elif state.get("opportunity_brief"):
            state["current_task"] = "generate_sow"
        else:
            state["current_task"] = "estimate_effort"
        
        return await self.run(state)
    
    async def _qa_review(self, state: A6State) -> A6State:
        """Perform QA review on a deliverable."""
        self.logger.info("Performing QA review")
        
        content = state.get("deliverable_content", "")
        deliverable_type = state.get("deliverable_type", DeliverableType.OTHER)
        
        # Get DoD template
        dod = self._dod_templates.get(deliverable_type)
        dod_criteria = dod.criteria if dod else ["General quality check"]
        dod_sections = dod.mandatory_sections if dod else []
        dod_standards = dod.quality_standards if dod else []
        
        prompt = f"""Perform a comprehensive QA review of this deliverable.

Deliverable Type: {deliverable_type}
Content:
---
{content}
---

## Definition of Done Criteria:
{chr(10).join(f"- {c}" for c in dod_criteria)}

## Mandatory Sections:
{chr(10).join(f"- {s}" for s in dod_sections)}

## Quality Standards:
{chr(10).join(f"- {s}" for s in dod_standards)}

## Review Instructions

Evaluate each category and provide specific feedback:

### 1. STRUCTURE CHECKS
- Are all mandatory sections present?
- Is the document well-organized?
- Is the flow logical?

### 2. CONTENT CHECKS
- Is the content complete?
- Are recommendations specific and actionable?
- Is evidence linked to claims?

### 3. STYLE CHECKS
- Is the tone professional and appropriate?
- Is language clear and concise?
- Is formatting consistent?

### 4. ACCURACY CHECKS
- Are facts and figures correct?
- Are sources cited?
- Are calculations accurate?

### 5. COMPLIANCE CHECKS
- Does it meet DoD criteria?
- Are BlueVektor standards followed?

## Output Format

For each check, provide:
- Check name
- Result: PASS / FAIL / WARNING
- Specific feedback (if not PASS)
- Fix suggestion (if applicable)

Then provide:
- Overall QA Score (0-100)
- Summary of critical issues
- Summary of improvements needed
- Recommendation: APPROVED / REVISION NEEDED / MAJOR REWRITE

Be thorough but constructive. Provide specific, actionable feedback.
"""
        
        response = await self.think(prompt, tier=ModelTier.REASONING)
        
        state["qa_feedback"] = response
        state = self.add_artifact(
            state,
            "qa_review",
            f"qa_review_{deliverable_type}_{datetime.utcnow().strftime('%Y%m%d_%H%M')}",
            response
        )
        
        # Determine if passed (simplified - would parse from response)
        state["qa_passed"] = "APPROVED" in response.upper()
        
        return state
    
    async def _generate_sow(self, state: A6State) -> A6State:
        """Generate Statement of Work from opportunity brief."""
        self.logger.info("Generating SoW")
        
        opportunity_brief = state.get("opportunity_brief", {})
        client_name = state.get("client_name", opportunity_brief.get("company_name", "Client"))
        
        prompt = f"""Generate a professional Statement of Work based on this opportunity.

Opportunity Brief:
{opportunity_brief}

Client: {client_name}

## SoW Structure

Create a complete, professional Statement of Work with:

### 1. DOCUMENT HEADER
- Document ID: SOW-[CLIENT]-[YYYY]-[NNN]
- Version: 1.0 DRAFT
- Date

### 2. EXECUTIVE SUMMARY
- 3-4 sentences max
- Problem, solution, expected outcome

### 3. BACKGROUND & OBJECTIVES
- Client context
- Business drivers
- SMART objectives (3-5)
- Success criteria

### 4. SCOPE DEFINITION

#### In Scope
- Be specific and measurable
- List each component/activity

#### Out of Scope
- Explicitly state exclusions
- Prevent scope creep

### 5. DELIVERABLES
For each deliverable:
- Name
- Description
- Format
- Acceptance criteria

### 6. APPROACH & METHODOLOGY
- High-level approach
- Key activities by phase
- Tools and frameworks used

### 7. TIMELINE & MILESTONES
- Start and end dates
- Key milestones with dates
- Dependencies

### 8. TEAM & GOVERNANCE
- BlueVektor team composition
- Client team requirements
- Meeting cadence
- Communication channels

### 9. INVESTMENT

#### Pricing Breakdown
| Item | Days | Rate | Total |
|------|------|------|-------|
| Discovery | X | €X | €X |
| etc. | | | |
| **Total** | | | **€X** |

#### Payment Terms
- Payment schedule
- Invoicing
- Expenses

### 10. ASSUMPTIONS & CONSTRAINTS
- Key assumptions
- Known constraints
- Dependencies on client

### 11. CHANGE CONTROL
- Process for changes
- Impact assessment
- Approval requirements

### 12. ACCEPTANCE
- Acceptance criteria
- Sign-off process

### 13. TERMS
- Validity period
- Confidentiality reference
- Standard terms reference

## Style Guidelines
- Professional, clear language
- No jargon without explanation
- Specific, not vague
- Measurable where possible
- Conservative estimates

Generate the complete SoW document.
"""
        
        response = await self.think(prompt, tier=ModelTier.REASONING)
        
        state = self.add_artifact(
            state,
            "sow",
            f"SOW_{client_name}_{datetime.utcnow().strftime('%Y%m%d')}",
            response,
            {"requires_review": True}
        )
        
        state["proposal_generated"] = True
        
        return state
    
    async def _generate_one_pager(self, state: A6State) -> A6State:
        """Generate one-page proposal summary."""
        self.logger.info("Generating one-pager")
        
        opportunity_brief = state.get("opportunity_brief", {})
        client_name = state.get("client_name", "Client")
        
        prompt = f"""Create a compelling one-page proposal for {client_name}.

Opportunity Context:
{opportunity_brief}

## One-Pager Structure

### THE HOOK (top of page)
**Headline**: Compelling, benefit-focused statement
**Problem Statement**: 2-3 sentences capturing the pain

### THE SOLUTION (middle)
**Our Approach**: 3-4 bullet points
- What we'll do
- How we'll do it
- Key differentiators

**Key Deliverables**: 4-5 bullets
- Tangible outputs they'll receive

### THE PROOF (why us)
**Why BlueVektor**: 3 compelling reasons
- Relevant expertise
- Unique approach
- Track record

### THE ASK (bottom)
**Investment**: Range (e.g., "€15,000 - €25,000")
**Timeline**: Summary (e.g., "4-6 weeks")

**Next Steps**: 3 clear actions
1. Immediate next step
2. Following step
3. Final step

**Call to Action**: Single, clear CTA

**Contact**: hello@bluevektor.com

## Style Guidelines
- Scannable in 60 seconds
- Benefit-focused language
- No jargon
- Compelling but honest
- Professional but approachable

Generate the one-pager content formatted for a single page.
"""
        
        response = await self.think(prompt)
        
        state = self.add_artifact(
            state,
            "one_pager",
            f"OnePager_{client_name}_{datetime.utcnow().strftime('%Y%m%d')}",
            response
        )
        
        return state
    
    async def _create_project_plan(self, state: A6State) -> A6State:
        """Create project plan for engagement."""
        self.logger.info("Creating project plan")
        
        engagement_id = state.get("engagement_id", "ENG-001")
        client_name = state.get("client_name", "Client")
        input_data = state.get("input_data", {})
        
        prompt = f"""Create a detailed project plan for this engagement.

Engagement: {engagement_id}
Client: {client_name}
Context: {input_data}

## Project Plan Structure

### 1. ENGAGEMENT OVERVIEW
- Engagement name
- Workpackage type
- Duration
- Team composition

### 2. TIMELINE
Create a week-by-week breakdown:

| Week | Phase | Key Activities | Deliverables | Milestones |
|------|-------|----------------|--------------|------------|
| 1 | | | | |
| 2 | | | | |
| ... | | | | |

### 3. MILESTONES
For each milestone:
- ID (M1, M2, etc.)
- Name
- Due date
- Deliverables included
- Dependencies
- Acceptance criteria

### 4. GOVERNANCE
- Status meeting cadence and attendees
- Steering committee cadence
- Escalation path
- Communication channels

### 5. RAID LOG (Initial)

#### Risks
| ID | Risk | Probability | Impact | Mitigation | Owner |
|----|------|-------------|--------|------------|-------|

#### Assumptions
| ID | Assumption | Impact if Wrong |
|----|------------|-----------------|

#### Issues
(None at project start, template for tracking)

#### Decisions
(None at project start, template for tracking)

### 6. TEAM & RESPONSIBILITIES

BlueVektor Team:
| Role | Responsibilities | Allocation |
|------|------------------|------------|

Client Team (required):
| Role | Responsibilities | Commitment |
|------|------------------|------------|

### 7. QUALITY GATES
- What needs to be reviewed/approved before proceeding
- Definition of Done for key deliverables

### 8. SUCCESS METRICS
- How we'll measure success
- KPIs to track

Generate a comprehensive, realistic project plan.
"""
        
        response = await self.think(prompt, tier=ModelTier.REASONING)
        
        state = self.add_artifact(
            state,
            "project_plan",
            f"ProjectPlan_{engagement_id}_{datetime.utcnow().strftime('%Y%m%d')}",
            response
        )
        
        state["plan_created"] = True
        
        return state
    
    async def _estimate_effort(self, state: A6State) -> A6State:
        """Estimate effort for an engagement."""
        self.logger.info("Estimating effort")
        
        input_data = state.get("input_data", {})
        opportunity_brief = state.get("opportunity_brief", {})
        
        context = {**input_data, **opportunity_brief}
        
        prompt = f"""Estimate the effort required for this engagement.

Context:
{context}

## Estimation Framework

### Standard Baselines (days)

**WP1 - Cloud Transformation Diagnostic**
| Activity | Small (<100 users) | Medium (100-500) | Large (500+) |
|----------|-------------------|------------------|--------------|
| Discovery & Planning | 0.5 | 1 | 1.5 |
| Evidence Collection | 1 | 2 | 3 |
| Volumetrics Analysis | 0.5 | 1 | 2 |
| App Analysis (CSK 4R) | 0.5 | 1 | 2 |
| Hotspot Mapping | 1 | 1.5 | 2 |
| 30/60/90 Planning | 0.5 | 1 | 1.5 |
| Report Writing | 1 | 1.5 | 2 |
| Review & Revision | 0.5 | 1 | 1 |
| Presentation | 0.5 | 0.5 | 1 |
| **Baseline Total** | **6** | **10.5** | **16** |

**Complexity Multipliers**
- Multiple instances: ×1.5
- JSM/ITSM included: ×1.3
- Complex integrations: ×1.25
- Tight timeline (<2 weeks): ×1.2
- Multiple stakeholder groups: ×1.15

### Your Estimate

Based on the context provided:

1. **Size Classification**: Small / Medium / Large
   - Reasoning: ...

2. **Baseline Effort**: X days

3. **Complexity Factors**:
   - Factor 1: +X%
   - Factor 2: +X%

4. **Adjusted Effort**: X days

5. **Contingency** (10-20%): X days

6. **Total Estimated Effort**: X days

### Effort Breakdown
| Phase | Activities | Days |
|-------|------------|------|
| Discovery | | |
| Analysis | | |
| Delivery | | |
| **Total** | | **X** |

### Pricing Estimate
- Daily rate assumption: €1,500 - €2,000
- Estimated investment: €X,XXX - €X,XXX

### Key Assumptions
- List assumptions affecting this estimate

### Risks to Estimate
- What could make this take longer

Provide a detailed, defensible estimate.
"""
        
        response = await self.think(prompt)
        
        state["output_data"] = {"effort_estimate": response}
        state = self.add_artifact(
            state,
            "effort_estimate",
            f"Estimate_{datetime.utcnow().strftime('%Y%m%d_%H%M')}",
            response
        )
        
        return state
    
    async def _update_raid(self, state: A6State) -> A6State:
        """Update RAID log with new items."""
        self.logger.info("Updating RAID log")
        
        existing_raid = state.get("raid_log", {})
        input_data = state.get("input_data", {})
        
        prompt = f"""Update the RAID log based on new information.

Existing RAID Log:
{existing_raid}

New Information:
{input_data}

## RAID Update

Review the new information and update each section:

### RISKS
- Are there new risks to add?
- Should any existing risks be updated?
- Can any risks be closed?

For new risks:
| ID | Category | Risk | Probability | Impact | Level | Mitigation | Owner | Status |
|----|----------|------|-------------|--------|-------|------------|-------|--------|

### ACTIONS
- New action items identified
- Status updates on existing actions

For new actions:
| ID | Action | Priority | Owner | Due Date | Status |
|----|--------|----------|-------|----------|--------|

### ISSUES
- New issues to log
- Resolution of existing issues

For new issues:
| ID | Issue | Priority | Owner | Status | Resolution |
|----|-------|----------|-------|--------|------------|

### DECISIONS
- New decisions made
- Decisions pending

For new decisions:
| ID | Date | Topic | Decision | Rationale | Decided By |
|----|------|-------|----------|-----------|------------|

Provide the updated RAID log.
"""
        
        response = await self.think(prompt)
        
        state = self.add_artifact(
            state,
            "raid_update",
            f"RAID_Update_{datetime.utcnow().strftime('%Y%m%d_%H%M')}",
            response
        )
        
        return state
    
    async def _check_capacity(self, state: A6State) -> A6State:
        """Check and report on capacity."""
        self.logger.info("Checking capacity")
        
        input_data = state.get("input_data", {})
        requested_start = input_data.get("requested_start", "ASAP")
        estimated_days = input_data.get("estimated_days", 10)
        
        prompt = f"""Assess capacity for a new engagement.

Request:
- Requested start: {requested_start}
- Estimated effort: {estimated_days} days
- Additional context: {input_data}

## Capacity Assessment

### Current Assumptions
- Working days per week: 4 (1 day reserved for admin/sales)
- Max concurrent engagements: 2
- Buffer between engagements: 2-3 days

### Assessment

1. **Availability Check**
   - Can we accommodate this request?
   - If not immediately, when?

2. **Proposed Timeline**
   - Recommended start date
   - Estimated end date
   - Any conflicts or concerns

3. **Capacity Impact**
   - Current utilization
   - Projected utilization with this engagement

4. **Recommendations**
   - Accept as-is
   - Propose alternative dates
   - Discuss scope reduction
   - Decline (with reasoning)

5. **Contingency Notes**
   - What if timeline slips
   - Backup options

Provide a realistic capacity assessment.
"""
        
        response = await self.think(prompt, tier=ModelTier.FAST)
        
        state["output_data"] = {"capacity_assessment": response}
        state = self.add_artifact(
            state,
            "capacity_check",
            f"Capacity_{datetime.utcnow().strftime('%Y%m%d_%H%M')}",
            response
        )
        
        return state
    
    # -------------------------------------------------------------------------
    # Utility Functions
    # -------------------------------------------------------------------------
    
    def get_dod(self, deliverable_type: DeliverableType) -> DefinitionOfDone | None:
        """Get Definition of Done for a deliverable type."""
        return self._dod_templates.get(deliverable_type)
    
    def calculate_qa_score(self, checklist: QAChecklist) -> int:
        """Calculate QA score from checklist."""
        if checklist.total_checks == 0:
            return 0
        
        # Weight: Pass=100, Warning=70, Fail=0
        score = (
            (checklist.passed * 100) +
            (checklist.warnings * 70) +
            (checklist.failed * 0)
        ) / checklist.total_checks
        
        return int(score)


# =============================================================================
# Agent Factory
# =============================================================================

def create_a6_agent() -> A6DeliveryAgent:
    """Factory function to create A6 agent."""
    return A6DeliveryAgent()
