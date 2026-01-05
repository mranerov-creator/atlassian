"""
BlueVektor Agents - A3: Assessment Analyst
Executes WP1: Evidence collection, hotspot mapping, 30/60/90 planning.
"""
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from agents.base import AgentConfig, AgentState, BaseAgent
from core.llm import ModelTier


# =============================================================================
# A3 Enums
# =============================================================================

class RiskLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ImpactLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class EffortLevel(str, Enum):
    HIGH = "high"      # > 2 weeks
    MEDIUM = "medium"  # 1-2 weeks
    LOW = "low"        # < 1 week


class HotspotCategory(str, Enum):
    GOVERNANCE = "governance"
    ARCHITECTURE = "architecture"
    SECURITY = "security"
    PERFORMANCE = "performance"
    COMPLIANCE = "compliance"
    COST = "cost"
    TECHNICAL_DEBT = "technical_debt"
    USER_ADOPTION = "user_adoption"


class ProductType(str, Enum):
    JIRA_SOFTWARE = "jira_software"
    JIRA_SERVICE_MANAGEMENT = "jira_service_management"
    JIRA_WORK_MANAGEMENT = "jira_work_management"
    CONFLUENCE = "confluence"
    BITBUCKET = "bitbucket"
    OPSGENIE = "opsgenie"
    STATUSPAGE = "statuspage"
    TRELLO = "trello"


class DeploymentType(str, Enum):
    SERVER = "server"
    DATA_CENTER = "data_center"
    CLOUD = "cloud"
    HYBRID = "hybrid"


# =============================================================================
# A3 Evidence Schemas
# =============================================================================

class InstanceInfo(BaseModel):
    """Basic instance information."""
    name: str
    url: str
    deployment_type: DeploymentType
    version: str | None = None
    products: list[ProductType] = Field(default_factory=list)
    data_residency: str | None = None
    created_date: str | None = None


class UserMetrics(BaseModel):
    """User-related metrics."""
    total_users: int = 0
    active_users_30d: int = 0
    active_users_90d: int = 0
    licensed_users: int = 0
    admin_users: int = 0
    groups_count: int = 0
    external_users: int = 0
    sso_enabled: bool = False
    scim_enabled: bool = False


class JiraMetrics(BaseModel):
    """Jira-specific metrics."""
    projects_count: int = 0
    active_projects: int = 0
    archived_projects: int = 0
    issues_total: int = 0
    issues_open: int = 0
    workflows_count: int = 0
    custom_workflows: int = 0
    custom_fields_count: int = 0
    screens_count: int = 0
    schemes_count: int = 0
    boards_count: int = 0
    filters_count: int = 0
    dashboards_count: int = 0
    automations_count: int = 0
    
    # JSM specific
    service_desks_count: int = 0
    request_types_count: int = 0
    sla_count: int = 0
    queues_count: int = 0


class ConfluenceMetrics(BaseModel):
    """Confluence-specific metrics."""
    spaces_count: int = 0
    active_spaces: int = 0
    archived_spaces: int = 0
    pages_total: int = 0
    blogs_total: int = 0
    attachments_size_gb: float = 0.0
    templates_count: int = 0
    macros_used: list[str] = Field(default_factory=list)


class AppInfo(BaseModel):
    """Marketplace app information."""
    app_key: str
    app_name: str
    vendor: str
    version: str | None = None
    users_count: int = 0
    hosting: str = "cloud"  # cloud, server, datacenter
    status: str = "active"  # active, disabled, evaluation
    annual_cost: float | None = None
    last_used: str | None = None
    criticality: str = "medium"  # critical, high, medium, low
    migration_status: str = "unknown"  # compatible, needs_replacement, no_equivalent, unknown
    notes: str | None = None


class IntegrationInfo(BaseModel):
    """External integration information."""
    name: str
    type: str  # api, webhook, oauth, ldap, etc.
    direction: str = "bidirectional"  # inbound, outbound, bidirectional
    target_system: str
    status: str = "active"
    owner: str | None = None
    criticality: str = "medium"
    documentation_exists: bool = False
    notes: str | None = None


class VolumetricsReport(BaseModel):
    """Complete volumetrics report."""
    instance: InstanceInfo
    users: UserMetrics
    jira: JiraMetrics | None = None
    confluence: ConfluenceMetrics | None = None
    apps: list[AppInfo] = Field(default_factory=list)
    integrations: list[IntegrationInfo] = Field(default_factory=list)
    
    # Storage
    total_storage_gb: float = 0.0
    attachments_gb: float = 0.0
    
    # Collected at
    collected_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    collection_method: str = "manual"  # manual, api, export


# =============================================================================
# A3 Hotspot Schemas
# =============================================================================

class Hotspot(BaseModel):
    """Individual hotspot / finding."""
    id: str
    title: str
    description: str
    category: HotspotCategory
    
    # Scoring
    impact: ImpactLevel
    effort: EffortLevel
    risk: RiskLevel
    priority_score: int = Field(0, ge=0, le=100)
    
    # Details
    affected_areas: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    root_cause: str | None = None
    
    # Recommendations
    recommendation: str
    quick_win: bool = False
    estimated_effort_days: int | None = None
    
    # Dependencies
    dependencies: list[str] = Field(default_factory=list)
    blocked_by: list[str] = Field(default_factory=list)
    
    # Metadata
    discovered_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    source: str | None = None


class HotspotMap(BaseModel):
    """Collection of hotspots with summary."""
    hotspots: list[Hotspot] = Field(default_factory=list)
    
    # Summary counts
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    quick_wins_count: int = 0
    
    # By category
    by_category: dict[str, int] = Field(default_factory=dict)
    
    # Overall health score
    health_score: int = Field(50, ge=0, le=100)
    
    generated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# =============================================================================
# A3 Plan Schemas
# =============================================================================

class PlanAction(BaseModel):
    """Single action in 30/60/90 plan."""
    id: str
    title: str
    description: str
    owner: str | None = None
    
    # Timeline
    phase: str  # 30, 60, 90
    week: int | None = None
    duration_days: int | None = None
    
    # Categorization
    category: str
    workstream: str | None = None
    
    # Priority
    priority: str = "medium"  # critical, high, medium, low
    
    # Dependencies
    depends_on: list[str] = Field(default_factory=list)
    enables: list[str] = Field(default_factory=list)
    
    # Status
    status: str = "planned"  # planned, in_progress, completed, blocked
    
    # Related hotspots
    addresses_hotspots: list[str] = Field(default_factory=list)
    
    # Success criteria
    acceptance_criteria: list[str] = Field(default_factory=list)
    kpis: list[str] = Field(default_factory=list)


class ThirtyPlan(BaseModel):
    """First 30 days: Quick wins and foundation."""
    theme: str = "Quick Wins & Foundation"
    objectives: list[str] = Field(default_factory=list)
    actions: list[PlanAction] = Field(default_factory=list)
    key_milestones: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)


class SixtyPlan(BaseModel):
    """Days 31-60: Core improvements."""
    theme: str = "Core Improvements"
    objectives: list[str] = Field(default_factory=list)
    actions: list[PlanAction] = Field(default_factory=list)
    key_milestones: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)


class NinetyPlan(BaseModel):
    """Days 61-90: Optimization and governance."""
    theme: str = "Optimization & Governance"
    objectives: list[str] = Field(default_factory=list)
    actions: list[PlanAction] = Field(default_factory=list)
    key_milestones: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)


class Plan306090(BaseModel):
    """Complete 30/60/90 day plan."""
    title: str
    client_name: str
    prepared_for: str
    prepared_by: str = "BlueVektor"
    
    # Executive summary
    executive_summary: str
    current_state_summary: str
    target_state_summary: str
    
    # Plans
    thirty_days: ThirtyPlan
    sixty_days: SixtyPlan
    ninety_days: NinetyPlan
    
    # Beyond 90
    beyond_90_recommendations: list[str] = Field(default_factory=list)
    
    # Resource requirements
    estimated_effort_days: int = 0
    recommended_team: list[str] = Field(default_factory=list)
    
    # Success metrics
    success_metrics: list[str] = Field(default_factory=list)
    
    # Assumptions and constraints
    assumptions: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    
    # Metadata
    version: str = "1.0"
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# =============================================================================
# A3 WP1 Report Schema
# =============================================================================

class WP1Report(BaseModel):
    """Complete WP1 Diagnostic Report."""
    
    # Header
    title: str = "Cloud Transformation Diagnostic"
    client_name: str
    engagement_id: str
    version: str = "1.0"
    status: str = "draft"  # draft, review, final
    
    # Dates
    engagement_start: str
    engagement_end: str
    report_date: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    
    # Executive Summary
    executive_summary: str
    key_findings: list[str] = Field(default_factory=list)
    key_recommendations: list[str] = Field(default_factory=list)
    
    # Scope
    in_scope: list[str] = Field(default_factory=list)
    out_of_scope: list[str] = Field(default_factory=list)
    
    # Evidence
    volumetrics: VolumetricsReport | None = None
    
    # Analysis
    hotspot_map: HotspotMap | None = None
    
    # Options (if applicable)
    architecture_options: list[dict] | None = None
    recommended_option: str | None = None
    
    # Plan
    plan_30_60_90: Plan306090 | None = None
    
    # Appendices
    appendices: dict[str, Any] = Field(default_factory=dict)
    
    # Sign-off
    prepared_by: str = "BlueVektor"
    reviewed_by: str | None = None
    approved_by: str | None = None


# =============================================================================
# A3 Agent State
# =============================================================================

class A3State(AgentState, total=False):
    """State specific to A3 agent."""
    
    # Inputs
    client_name: str
    engagement_id: str
    instance_url: str
    api_credentials: dict[str, str]
    existing_exports: list[str]
    scope_definition: dict[str, Any]
    
    # Working data
    raw_evidence: dict[str, Any]
    volumetrics: VolumetricsReport | None
    
    # Analysis outputs
    hotspot_map: HotspotMap | None
    plan_30_60_90: Plan306090 | None
    
    # Final output
    wp1_report: WP1Report | None
    
    # Progress tracking
    evidence_collected: bool
    analysis_complete: bool
    plan_generated: bool
    report_drafted: bool


# =============================================================================
# A3 Agent
# =============================================================================

class A3AssessmentAgent(BaseAgent):
    """
    A3 - Assessment Analyst Agent
    
    Purpose: Execute WP1 Diagnostic - build factual baseline with evidence,
    hotspot map, and 30/60/90 plan ready for executive approval.
    
    Key functions:
    - Evidence collection and normalization
    - Volumetrics calculation
    - App inventory and CSK 4R analysis
    - Hotspot identification and prioritization
    - Quick wins identification
    - 30/60/90 plan generation
    - WP1 report drafting
    """
    
    def __init__(self):
        config = AgentConfig(
            id="a3",
            name="Assessment Analyst",
            role="WP1 Diagnostic Execution",
            goal="Build factual baseline with evidence, hotspot map, and 30/60/90 plan",
            backstory="""You are the analytical engine of BlueVektor's WP1 Diagnostic. 
You turn raw data into actionable insights.

Your expertise includes:
- Atlassian Cloud architecture and best practices
- Server/DC to Cloud migration patterns
- Governance and compliance frameworks
- App rationalization (CSK 4R methodology)
- Risk assessment and prioritization

You are meticulous about evidence. Every finding must be traceable to data.
You prioritize by impact × effort × risk, always identifying quick wins.

Your outputs are executive-ready: clear, visual, decision-oriented.
Never make recommendations without supporting evidence.""",
            model_tier=ModelTier.STANDARD,
            temperature=0.5,  # Lower for more consistent analysis
            max_tokens=8192,  # Larger for detailed reports
            tools=["atlassian_api", "filesystem", "spreadsheet"],
            allowed_handoffs=["a2", "a4", "a6"],
            artifacts_requiring_approval=["wp1_report", "plan_30_60_90"],
        )
        super().__init__(config)
    
    def system_prompt(self) -> str:
        """System prompt for A3."""
        base = self.build_base_prompt()
        
        return f"""{base}

# A3-Specific Rules

## Evidence Standards
- Every finding MUST link to specific data point or export
- Quantify everything: users, projects, issues, apps, integrations
- Use consistent units and formats
- Flag data gaps explicitly
- Include collection timestamp and method

## Volumetrics Collection
Collect for each instance:
1. **Users**: total, active (30/90d), licensed, admins, groups, external
2. **Jira**: projects, issues, workflows, custom fields, screens, boards, filters
3. **JSM**: service desks, request types, SLAs, queues, customers
4. **Confluence**: spaces, pages, blogs, attachments size, macros
5. **Apps**: name, vendor, cost, users, criticality, migration status
6. **Integrations**: type, direction, target, owner, criticality

## Hotspot Identification
Hotspot categories:
- Governance: missing policies, unclear ownership, no standards
- Architecture: sprawl, over-customization, technical debt
- Security: permissions issues, data exposure, access control gaps
- Performance: large instances, slow queries, storage issues
- Compliance: audit gaps, data residency, retention
- Cost: unused licenses, redundant apps, over-provisioning
- User Adoption: low usage, shadow tools, training gaps

Scoring (0-100):
- Impact (40%): business impact if not addressed
- Effort (30%): resources needed to fix
- Risk (30%): probability and severity

## Quick Wins Criteria
A quick win must be:
- Low effort (< 1 week)
- High visibility impact
- No dependencies on other work
- Demonstrable value

## 30/60/90 Plan Structure
**Days 1-30: Quick Wins & Foundation**
- Address critical hotspots
- Implement governance basics
- Quick wins to build momentum

**Days 31-60: Core Improvements**
- Architecture decisions
- App rationalization
- Security hardening

**Days 61-90: Optimization & Governance**
- Process maturity
- Monitoring & KPIs
- Documentation & training

## Report Structure
1. Executive Summary (1 page)
2. Scope & Methodology
3. Current State Assessment
   - Environment overview
   - Volumetrics summary
   - App landscape
4. Findings & Hotspots
   - Prioritized heatmap
   - Detail by category
5. Recommendations
   - Quick wins
   - Strategic initiatives
6. 30/60/90 Plan
7. Resource & Timeline Estimates
8. Appendices (detailed data)

## Handoff Rules
- To A2: For architecture options and TO-BE design
- To A4: For governance framework and policies
- To A6: For report QA and client presentation prep
"""

    async def run(self, state: A3State) -> A3State:
        """
        Main execution logic for A3.
        Routes to appropriate function based on task.
        """
        current_task = state.get("current_task", "")
        
        self.logger.info("A3 executing", task=current_task)
        
        if current_task == "collect_evidence":
            return await self._collect_evidence(state)
        elif current_task == "analyze_volumetrics":
            return await self._analyze_volumetrics(state)
        elif current_task == "analyze_apps":
            return await self._analyze_apps(state)
        elif current_task == "identify_hotspots":
            return await self._identify_hotspots(state)
        elif current_task == "generate_plan":
            return await self._generate_plan(state)
        elif current_task == "draft_report":
            return await self._draft_report(state)
        elif current_task == "full_wp1":
            return await self._execute_full_wp1(state)
        else:
            return await self._analyze_and_route(state)
    
    # -------------------------------------------------------------------------
    # Core Functions
    # -------------------------------------------------------------------------
    
    async def _analyze_and_route(self, state: A3State) -> A3State:
        """Analyze input and determine appropriate action."""
        input_data = state.get("input_data", {})
        
        # Check what's already done
        evidence_collected = state.get("evidence_collected", False)
        analysis_complete = state.get("analysis_complete", False)
        plan_generated = state.get("plan_generated", False)
        
        if not evidence_collected:
            state["current_task"] = "collect_evidence"
        elif not analysis_complete:
            state["current_task"] = "identify_hotspots"
        elif not plan_generated:
            state["current_task"] = "generate_plan"
        else:
            state["current_task"] = "draft_report"
        
        return await self.run(state)
    
    async def _collect_evidence(self, state: A3State) -> A3State:
        """Collect and normalize evidence from various sources."""
        self.logger.info("Collecting evidence")
        
        input_data = state.get("input_data", {})
        existing_exports = state.get("existing_exports", [])
        
        prompt = f"""Analyze the available evidence sources and create a structured evidence collection plan.

Available inputs:
{input_data}

Existing exports:
{existing_exports}

Create a comprehensive evidence collection checklist:

1. **Instance Information**
   - What instance details do we have?
   - What's missing?

2. **User Data**
   - User counts and activity
   - Groups and permissions
   - SSO/SCIM status

3. **Jira Data**
   - Projects inventory
   - Workflow analysis
   - Custom field audit
   - Automation inventory

4. **Confluence Data** (if applicable)
   - Spaces inventory
   - Content metrics
   - Macro usage

5. **Apps & Integrations**
   - Marketplace apps list
   - External integrations
   - API usage

6. **Data Gaps**
   - What evidence is missing?
   - How critical is each gap?
   - Recommended actions to fill gaps

For each data point, note:
- Source (export, API, manual)
- Confidence level
- Collection date
"""
        
        response = await self.think(prompt)
        
        state["raw_evidence"] = {"collection_plan": response}
        state = self.add_artifact(
            state,
            "evidence_collection",
            f"evidence_plan_{datetime.utcnow().strftime('%Y%m%d_%H%M')}",
            response
        )
        
        state["evidence_collected"] = True
        return state
    
    async def _analyze_volumetrics(self, state: A3State) -> A3State:
        """Analyze and summarize volumetrics from evidence."""
        self.logger.info("Analyzing volumetrics")
        
        raw_evidence = state.get("raw_evidence", {})
        input_data = state.get("input_data", {})
        
        prompt = f"""Based on the collected evidence, create a comprehensive volumetrics analysis.

Evidence:
{raw_evidence}

Additional context:
{input_data}

Generate a complete volumetrics report covering:

## 1. Instance Overview
- Deployment type and version
- Products in use
- Data residency location

## 2. User Metrics
- Total users vs active users (calculate activity rate)
- License utilization
- Admin count (flag if >5% of users)
- External users percentage
- SSO/SCIM adoption

## 3. Jira Metrics
- Projects: total, active, archived (calculate archive rate)
- Issues: total, open rate
- Customization level: custom workflows, fields, screens
- Automation adoption
- JSM: service desks, SLA compliance

## 4. Confluence Metrics (if applicable)
- Spaces: total, active
- Content volume
- Attachment storage
- Macro dependency analysis

## 5. Key Ratios & Benchmarks
Compare against industry benchmarks:
- Users per project
- Issues per user
- Custom fields ratio
- App density

## 6. Red Flags
Identify any metrics that indicate problems:
- Over-customization
- Low adoption
- Governance gaps
- Cost inefficiency

Format as structured data with clear metrics and observations.
"""
        
        response = await self.think(prompt, tier=ModelTier.REASONING)
        
        state["raw_evidence"]["volumetrics_analysis"] = response
        state = self.add_artifact(
            state,
            "volumetrics_analysis",
            f"volumetrics_{datetime.utcnow().strftime('%Y%m%d_%H%M')}",
            response
        )
        
        return state
    
    async def _analyze_apps(self, state: A3State) -> A3State:
        """Analyze apps using CSK 4R methodology."""
        self.logger.info("Analyzing apps with CSK 4R")
        
        raw_evidence = state.get("raw_evidence", {})
        
        prompt = f"""Perform a CSK 4R analysis on the app landscape.

Evidence:
{raw_evidence}

## CSK 4R Framework

For each app, categorize as:

### 1. RETIRE
Apps to remove because:
- No longer used (<10% active users)
- Duplicate functionality
- Security/compliance risk
- Excessive cost vs value

### 2. REPLACE
Apps to swap for:
- Better cloud-native alternative exists
- Current app not cloud-compatible
- Vendor no longer supported
- Cost optimization opportunity

### 3. RETAIN
Apps to keep because:
- Business critical
- Good cloud compatibility
- No better alternative
- Cost-effective

### 4. REMEDIATE
Apps needing action:
- Upgrade required
- Configuration changes needed
- User training required
- Integration updates

## Analysis Structure

For each app provide:
- App name and vendor
- Current usage metrics
- CSK 4R classification
- Rationale
- Recommended action
- Priority (critical/high/medium/low)
- Estimated effort
- Cost impact

## Summary
- Apps to retire: count and annual savings
- Apps to replace: count and migration effort
- Apps to retain: count
- Apps to remediate: count and effort

Generate actionable app rationalization plan.
"""
        
        response = await self.think(prompt)
        
        state["raw_evidence"]["app_analysis"] = response
        state = self.add_artifact(
            state,
            "app_analysis",
            f"csk_4r_analysis_{datetime.utcnow().strftime('%Y%m%d_%H%M')}",
            response
        )
        
        return state
    
    async def _identify_hotspots(self, state: A3State) -> A3State:
        """Identify and prioritize hotspots."""
        self.logger.info("Identifying hotspots")
        
        raw_evidence = state.get("raw_evidence", {})
        volumetrics = state.get("volumetrics")
        
        prompt = f"""Based on all collected evidence, identify and prioritize hotspots.

Evidence Summary:
{raw_evidence}

## Hotspot Identification

For each finding, create a hotspot entry:

### Categories to analyze:
1. **Governance**: policies, ownership, standards, compliance
2. **Architecture**: sprawl, customization, technical debt, scalability
3. **Security**: permissions, access control, data protection
4. **Performance**: response times, storage, query efficiency
5. **Cost**: license optimization, app spend, over-provisioning
6. **User Adoption**: training, shadow IT, change management

### For each hotspot provide:

**ID**: HSP-001, HSP-002, etc.
**Title**: Clear, actionable title
**Category**: From list above
**Description**: Detailed explanation

**Impact** (HIGH/MEDIUM/LOW):
- Business impact if not addressed
- Users/teams affected
- Compliance/risk implications

**Effort** (HIGH/MEDIUM/LOW):
- Resources required
- Duration estimate
- Dependencies

**Risk** (CRITICAL/HIGH/MEDIUM/LOW):
- Probability of issue occurring
- Severity if it occurs

**Priority Score**: Calculate 0-100 based on:
- Impact (40%)
- Effort inverse (30%) 
- Risk (30%)

**Evidence**: Specific data points supporting this finding

**Recommendation**: What to do about it

**Quick Win?**: Yes if <1 week effort AND high visibility

## Output Format

1. Hotspot heatmap (table with all hotspots sorted by priority)
2. Quick wins list (top 5-10)
3. Critical issues requiring immediate attention
4. Category summary with counts
5. Overall health score (0-100)

Be specific and evidence-based. Every hotspot needs data backing.
"""
        
        response = await self.think(prompt, tier=ModelTier.REASONING)
        
        state["raw_evidence"]["hotspot_analysis"] = response
        state = self.add_artifact(
            state,
            "hotspot_map",
            f"hotspot_map_{datetime.utcnow().strftime('%Y%m%d_%H%M')}",
            response
        )
        
        state["analysis_complete"] = True
        return state
    
    async def _generate_plan(self, state: A3State) -> A3State:
        """Generate 30/60/90 day plan."""
        self.logger.info("Generating 30/60/90 plan")
        
        raw_evidence = state.get("raw_evidence", {})
        client_name = state.get("client_name", "Client")
        
        prompt = f"""Create a comprehensive 30/60/90 day transformation plan.

Client: {client_name}

Evidence & Analysis:
{raw_evidence}

## 30/60/90 PLAN

### DAYS 1-30: QUICK WINS & FOUNDATION
Theme: Build momentum with visible wins while establishing governance foundation

**Objectives:**
- Address critical hotspots
- Implement quick wins
- Establish baseline governance
- Build stakeholder confidence

**Actions:**
For each action include:
- ID (e.g., A-30-001)
- Title
- Description
- Owner role
- Duration (days)
- Dependencies
- Success criteria
- Addresses hotspots (IDs)

**Key Milestones:**
- Week 1: ...
- Week 2: ...
- Week 3: ...
- Week 4: ...

**Risks & Mitigations:**

---

### DAYS 31-60: CORE IMPROVEMENTS
Theme: Address structural issues and implement key improvements

**Objectives:**
- Resolve architecture issues
- Complete app rationalization
- Strengthen security posture
- Improve operational efficiency

**Actions:**
(Same format as above with IDs like A-60-001)

**Key Milestones:**
**Risks & Mitigations:**

---

### DAYS 61-90: OPTIMIZATION & GOVERNANCE
Theme: Mature processes and ensure sustainable operations

**Objectives:**
- Establish ongoing governance
- Optimize performance and cost
- Complete documentation
- Enable self-sufficiency

**Actions:**
(Same format as above with IDs like A-90-001)

**Key Milestones:**
**Risks & Mitigations:**

---

### BEYOND 90 DAYS
Recommendations for continued improvement:
- Next phase initiatives
- Long-term transformation roadmap
- Capability building

### RESOURCE REQUIREMENTS
- Estimated total effort (person-days)
- Recommended team composition
- Client resource requirements

### SUCCESS METRICS
- KPIs to track
- Target values
- Measurement frequency

### ASSUMPTIONS & CONSTRAINTS
- Key assumptions made
- Known constraints
- Dependencies on client

Make the plan realistic, actionable, and clearly tied to hotspots.
"""
        
        response = await self.think(prompt, tier=ModelTier.REASONING)
        
        state = self.add_artifact(
            state,
            "plan_30_60_90",
            f"plan_30_60_90_{datetime.utcnow().strftime('%Y%m%d_%H%M')}",
            response
        )
        
        state["plan_generated"] = True
        return state
    
    async def _draft_report(self, state: A3State) -> A3State:
        """Draft the complete WP1 report."""
        self.logger.info("Drafting WP1 report")
        
        raw_evidence = state.get("raw_evidence", {})
        client_name = state.get("client_name", "Client")
        engagement_id = state.get("engagement_id", f"WP1-{datetime.utcnow().strftime('%Y%m%d')}")
        
        prompt = f"""Create the complete WP1 Diagnostic Report.

Client: {client_name}
Engagement ID: {engagement_id}

All Evidence & Analysis:
{raw_evidence}

## WP1 DIAGNOSTIC REPORT

Create a professional, executive-ready report with:

### 1. COVER PAGE
- Title: Cloud Transformation Diagnostic
- Client name
- Prepared by: BlueVektor
- Date
- Version: 1.0 DRAFT

### 2. EXECUTIVE SUMMARY (1 page max)
- Engagement overview
- Key findings (top 5, bullet points)
- Key recommendations (top 5)
- Overall assessment (health score)
- Recommended next steps

### 3. SCOPE & METHODOLOGY
- Engagement timeline
- In-scope systems and processes
- Out-of-scope items
- Data collection methods
- Analysis frameworks used

### 4. CURRENT STATE ASSESSMENT

#### 4.1 Environment Overview
- Instance summary
- Products and versions
- Deployment architecture

#### 4.2 Volumetrics Summary
- User metrics with benchmarks
- Content metrics
- Key ratios

#### 4.3 App Landscape
- App inventory summary
- CSK 4R classification
- Cost analysis

#### 4.4 Integration Landscape
- External integrations
- API usage
- Data flows

### 5. FINDINGS & HOTSPOTS

#### 5.1 Hotspot Heatmap
Visual summary of all findings

#### 5.2 Critical Issues
Immediate attention required

#### 5.3 Findings by Category
Detailed analysis per category

### 6. RECOMMENDATIONS

#### 6.1 Quick Wins
Immediate actions for fast value

#### 6.2 Strategic Initiatives
Longer-term improvements

#### 6.3 Architecture Options (if applicable)
Options analysis with trade-offs

### 7. 30/60/90 DAY PLAN
Complete action plan

### 8. RESOURCE & TIMELINE ESTIMATES
- Effort estimates
- Team requirements
- Timeline with milestones

### 9. APPENDICES
- A: Detailed Volumetrics
- B: Complete App Inventory
- C: Hotspot Detail Cards
- D: Glossary

Format as a professional document suitable for executive presentation.
Use clear headings, bullet points, and tables where appropriate.
Include placeholders for charts/visuals [CHART: description].
"""
        
        response = await self.think(prompt, tier=ModelTier.REASONING)
        
        state = self.add_artifact(
            state,
            "wp1_report",
            f"WP1_Report_{client_name}_{datetime.utcnow().strftime('%Y%m%d')}",
            response,
            {"requires_review": True}
        )
        
        state["report_drafted"] = True
        
        # Request handoff to A6 for QA
        state = self.request_handoff(
            state,
            target_agent="a6",
            context={
                "task": "qa_report",
                "report_type": "wp1",
                "client_name": client_name,
                "source": "a3"
            },
            priority="high"
        )
        
        return state
    
    async def _execute_full_wp1(self, state: A3State) -> A3State:
        """Execute complete WP1 diagnostic flow."""
        self.logger.info("Executing full WP1 diagnostic")
        
        # Step 1: Collect evidence
        state["current_task"] = "collect_evidence"
        state = await self._collect_evidence(state)
        
        # Step 2: Analyze volumetrics
        state = await self._analyze_volumetrics(state)
        
        # Step 3: Analyze apps
        state = await self._analyze_apps(state)
        
        # Step 4: Identify hotspots
        state["current_task"] = "identify_hotspots"
        state = await self._identify_hotspots(state)
        
        # Step 5: Generate plan
        state["current_task"] = "generate_plan"
        state = await self._generate_plan(state)
        
        # Step 6: Draft report
        state["current_task"] = "draft_report"
        state = await self._draft_report(state)
        
        return state
    
    # -------------------------------------------------------------------------
    # Utility Functions
    # -------------------------------------------------------------------------
    
    def calculate_health_score(self, hotspots: list[Hotspot]) -> int:
        """Calculate overall health score from hotspots."""
        if not hotspots:
            return 50  # Neutral if no data
        
        # Weight by severity
        weights = {
            RiskLevel.CRITICAL: 25,
            RiskLevel.HIGH: 15,
            RiskLevel.MEDIUM: 8,
            RiskLevel.LOW: 3,
        }
        
        total_penalty = sum(weights.get(h.risk, 5) for h in hotspots)
        
        # Start at 100, subtract penalties, floor at 0
        score = max(0, 100 - total_penalty)
        
        return score
    
    def prioritize_hotspots(self, hotspots: list[Hotspot]) -> list[Hotspot]:
        """Sort hotspots by priority score descending."""
        return sorted(hotspots, key=lambda h: h.priority_score, reverse=True)
    
    def identify_quick_wins(self, hotspots: list[Hotspot]) -> list[Hotspot]:
        """Filter hotspots to only quick wins."""
        return [h for h in hotspots if h.quick_win]


# =============================================================================
# Agent Factory
# =============================================================================

def create_a3_agent() -> A3AssessmentAgent:
    """Factory function to create A3 agent."""
    return A3AssessmentAgent()
