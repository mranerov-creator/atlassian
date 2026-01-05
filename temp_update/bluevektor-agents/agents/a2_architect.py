"""
BlueVektor Agents - A2: Solution Architect
TO-BE design, architecture options, and technical decisions.
"""
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from agents.base import AgentConfig, AgentState, BaseAgent
from core.llm import ModelTier


# =============================================================================
# A2 Enums
# =============================================================================

class DeploymentModel(str, Enum):
    CLOUD = "cloud"
    DATA_CENTER = "data_center"
    SERVER = "server"
    HYBRID = "hybrid"


class InstanceStrategy(str, Enum):
    SINGLE = "single_instance"
    MULTI = "multi_instance"
    CONSOLIDATED = "consolidated"
    FEDERATED = "federated"


class ProductTier(str, Enum):
    FREE = "free"
    STANDARD = "standard"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class IntegrationType(str, Enum):
    NATIVE = "native"
    MARKETPLACE = "marketplace"
    CUSTOM = "custom"
    API = "api"
    WEBHOOK = "webhook"
    MCP = "mcp"


class MigrationApproach(str, Enum):
    LIFT_AND_SHIFT = "lift_and_shift"
    REPLATFORM = "replatform"
    REFACTOR = "refactor"
    RETIRE = "retire"
    RETAIN = "retain"


class DataResidency(str, Enum):
    US = "us"
    EU = "eu"
    AU = "au"
    DE = "de"
    SG = "sg"
    GLOBAL = "global"


class ArchitecturePattern(str, Enum):
    CENTRALIZED = "centralized"
    DISTRIBUTED = "distributed"
    HUB_SPOKE = "hub_and_spoke"
    MESH = "mesh"


# =============================================================================
# A2 Current State Schemas
# =============================================================================

class CurrentInstance(BaseModel):
    """Current Atlassian instance."""
    name: str
    url: str
    deployment: DeploymentModel
    version: str | None = None
    products: list[str] = Field(default_factory=list)
    users: int = 0
    projects: int = 0
    spaces: int = 0
    apps_count: int = 0
    data_size_gb: float = 0.0
    age_years: float = 0.0


class CurrentIntegration(BaseModel):
    """Current integration."""
    name: str
    source: str
    target: str
    integration_type: IntegrationType
    direction: str = "bidirectional"  # inbound, outbound, bidirectional
    criticality: str = "medium"  # low, medium, high, critical
    data_exchanged: list[str] = Field(default_factory=list)


class CurrentStateAssessment(BaseModel):
    """Complete AS-IS architecture assessment."""
    instances: list[CurrentInstance] = Field(default_factory=list)
    integrations: list[CurrentIntegration] = Field(default_factory=list)
    total_users: int = 0
    total_projects: int = 0
    total_spaces: int = 0
    total_apps: int = 0
    total_data_gb: float = 0.0
    pain_points: list[str] = Field(default_factory=list)
    technical_debt: list[str] = Field(default_factory=list)
    compliance_requirements: list[str] = Field(default_factory=list)


# =============================================================================
# A2 Target State Schemas
# =============================================================================

class TargetInstance(BaseModel):
    """Target Atlassian instance configuration."""
    name: str
    purpose: str
    deployment: DeploymentModel = DeploymentModel.CLOUD
    products: list[str] = Field(default_factory=list)
    tier: ProductTier = ProductTier.STANDARD
    data_residency: DataResidency = DataResidency.EU
    estimated_users: int = 0
    sso_provider: str | None = None
    scim_enabled: bool = False
    ip_allowlist: bool = False


class TargetIntegration(BaseModel):
    """Target integration design."""
    name: str
    source: str
    target: str
    integration_type: IntegrationType
    implementation: str  # Tool/method to implement
    priority: str = "medium"
    complexity: str = "medium"
    estimated_effort_days: int = 1


class ProductConfiguration(BaseModel):
    """Product-specific configuration."""
    product: str
    tier: ProductTier
    key_features: list[str] = Field(default_factory=list)
    configurations: dict[str, Any] = Field(default_factory=dict)
    automations: list[str] = Field(default_factory=list)
    apps_required: list[str] = Field(default_factory=list)


class SecurityArchitecture(BaseModel):
    """Security architecture design."""
    authentication: str = "SAML SSO"
    identity_provider: str | None = None
    user_provisioning: str = "SCIM"
    mfa_required: bool = True
    ip_allowlisting: bool = False
    api_token_policy: str = "90-day expiry"
    audit_log_retention: str = "1 year"
    data_classification: list[str] = Field(default_factory=list)
    compliance_frameworks: list[str] = Field(default_factory=list)


class TargetStateDesign(BaseModel):
    """Complete TO-BE architecture design."""
    name: str = "Target Architecture"
    version: str = "1.0"
    
    # Instance strategy
    instance_strategy: InstanceStrategy = InstanceStrategy.SINGLE
    pattern: ArchitecturePattern = ArchitecturePattern.CENTRALIZED
    
    # Instances
    instances: list[TargetInstance] = Field(default_factory=list)
    
    # Products
    products: list[ProductConfiguration] = Field(default_factory=list)
    
    # Integrations
    integrations: list[TargetIntegration] = Field(default_factory=list)
    
    # Security
    security: SecurityArchitecture | None = None
    
    # Rationale
    design_principles: list[str] = Field(default_factory=list)
    key_decisions: list[dict[str, str]] = Field(default_factory=list)
    
    # Metadata
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# =============================================================================
# A2 Architecture Options
# =============================================================================

class ArchitectureOption(BaseModel):
    """Single architecture option for comparison."""
    id: str
    name: str
    description: str
    
    # Design
    instance_strategy: InstanceStrategy
    pattern: ArchitecturePattern
    instances: list[TargetInstance] = Field(default_factory=list)
    
    # Evaluation
    pros: list[str] = Field(default_factory=list)
    cons: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    mitigations: list[str] = Field(default_factory=list)
    
    # Scores (1-5)
    score_scalability: int = Field(3, ge=1, le=5)
    score_simplicity: int = Field(3, ge=1, le=5)
    score_cost: int = Field(3, ge=1, le=5)
    score_security: int = Field(3, ge=1, le=5)
    score_governance: int = Field(3, ge=1, le=5)
    total_score: int = 15
    
    # Effort
    estimated_effort_weeks: int = 4
    estimated_cost_eur: float = 0.0
    
    # Recommendation
    recommended: bool = False
    recommendation_rationale: str | None = None


class ArchitectureComparison(BaseModel):
    """Comparison of architecture options."""
    client_name: str
    options: list[ArchitectureOption] = Field(default_factory=list)
    evaluation_criteria: list[str] = Field(default_factory=list)
    recommended_option: str | None = None
    recommendation_summary: str | None = None
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# =============================================================================
# A2 Migration Planning
# =============================================================================

class MigrationItem(BaseModel):
    """Item to migrate."""
    id: str
    name: str
    source: str
    target: str
    item_type: str  # project, space, app, user, etc.
    approach: MigrationApproach
    complexity: str = "medium"
    dependencies: list[str] = Field(default_factory=list)
    estimated_effort_hours: int = 1
    wave: int = 1
    notes: str | None = None


class MigrationWave(BaseModel):
    """Migration wave."""
    wave_number: int
    name: str
    description: str
    start_date: str | None = None
    end_date: str | None = None
    items: list[MigrationItem] = Field(default_factory=list)
    success_criteria: list[str] = Field(default_factory=list)
    rollback_plan: str | None = None


class MigrationPlan(BaseModel):
    """High-level migration plan."""
    name: str
    client_name: str
    approach: MigrationApproach
    
    # Scope
    total_projects: int = 0
    total_spaces: int = 0
    total_users: int = 0
    total_apps: int = 0
    
    # Waves
    waves: list[MigrationWave] = Field(default_factory=list)
    
    # Timeline
    estimated_duration_weeks: int = 4
    
    # Dependencies
    prerequisites: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# =============================================================================
# A2 Technical Decision Records
# =============================================================================

class TechnicalDecision(BaseModel):
    """Architecture Decision Record (ADR)."""
    id: str
    title: str
    status: str = "proposed"  # proposed, accepted, deprecated, superseded
    context: str
    decision: str
    consequences: list[str] = Field(default_factory=list)
    alternatives_considered: list[str] = Field(default_factory=list)
    decided_by: list[str] = Field(default_factory=list)
    date: str = Field(default_factory=lambda: datetime.utcnow().strftime('%Y-%m-%d'))


class DecisionLog(BaseModel):
    """Collection of technical decisions."""
    client_name: str
    decisions: list[TechnicalDecision] = Field(default_factory=list)


# =============================================================================
# A2 Sizing & Licensing
# =============================================================================

class LicenseRecommendation(BaseModel):
    """License recommendation."""
    product: str
    tier: ProductTier
    users: int
    annual_cost_eur: float
    rationale: str
    features_used: list[str] = Field(default_factory=list)


class SizingRecommendation(BaseModel):
    """Overall sizing and licensing."""
    client_name: str
    licenses: list[LicenseRecommendation] = Field(default_factory=list)
    total_annual_cost_eur: float = 0.0
    apps_budget_eur: float = 0.0
    implementation_budget_eur: float = 0.0
    total_first_year_eur: float = 0.0
    notes: list[str] = Field(default_factory=list)


# =============================================================================
# A2 Architecture Document
# =============================================================================

class ArchitectureDocument(BaseModel):
    """Complete architecture document."""
    title: str = "Solution Architecture Document"
    client_name: str
    version: str = "1.0"
    status: str = "draft"
    
    # Contents
    executive_summary: str | None = None
    current_state: CurrentStateAssessment | None = None
    target_state: TargetStateDesign | None = None
    architecture_options: ArchitectureComparison | None = None
    migration_plan: MigrationPlan | None = None
    sizing: SizingRecommendation | None = None
    decisions: DecisionLog | None = None
    
    # Appendices
    diagrams: list[str] = Field(default_factory=list)
    references: list[str] = Field(default_factory=list)
    
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    created_by: str = "BlueVektor"


# =============================================================================
# A2 Agent State
# =============================================================================

class A2State(AgentState, total=False):
    """State specific to A2 agent."""
    client_name: str
    engagement_id: str
    
    # Inputs
    wp1_findings: dict[str, Any]
    requirements: dict[str, Any]
    constraints: list[str]
    
    # Working data
    current_state: CurrentStateAssessment | None
    target_state: TargetStateDesign | None
    architecture_options: ArchitectureComparison | None
    migration_plan: MigrationPlan | None
    sizing: SizingRecommendation | None
    decisions: list[TechnicalDecision]
    
    # Progress
    current_state_complete: bool
    target_designed: bool
    options_evaluated: bool
    migration_planned: bool
    sizing_complete: bool
    document_drafted: bool


# =============================================================================
# A2 Agent
# =============================================================================

class A2ArchitectAgent(BaseAgent):
    """
    A2 - Solution Architect Agent
    
    Purpose: Design TO-BE architecture, evaluate options, and plan migrations.
    """
    
    def __init__(self):
        config = AgentConfig(
            id="a2",
            name="Solution Architect",
            role="TO-BE Architecture Design",
            goal="Design optimal Atlassian Cloud architecture with clear options, decisions, and migration path",
            backstory="""You are the technical visionary of BlueVektor. You transform 
complex requirements into elegant, scalable Atlassian architectures.

Your expertise includes:
- Atlassian Cloud architecture patterns
- Enterprise integration design
- Migration strategy and planning
- Security and compliance architecture
- Sizing and licensing optimization

You think in systems, not products. You balance ideal architecture
with practical constraints like budget, timeline, and organizational
readiness.

Key principles:
- Start with the end in mind
- Simplify where possible, federate where necessary
- Security and governance by design
- Document decisions and rationale
- Plan for scale and evolution""",
            model_tier=ModelTier.REASONING,
            temperature=0.6,
            max_tokens=8192,
            tools=["filesystem", "diagrams"],
            allowed_handoffs=["a3", "a4", "a5", "a6"],
            artifacts_requiring_approval=["architecture_document", "target_state"],
        )
        super().__init__(config)
    
    def system_prompt(self) -> str:
        """System prompt for A2."""
        base = self.build_base_prompt()
        
        return f"""{base}

# A2-Specific Rules

## Architecture Design Process

### 1. Understand Current State
- Document all instances, products, versions
- Map integrations and data flows
- Identify pain points and technical debt
- Note compliance requirements

### 2. Define Target State
- Choose instance strategy (single, multi, consolidated, federated)
- Select products and tiers
- Design security architecture
- Plan integrations

### 3. Evaluate Options
Present 2-3 architecture options with:
- Description and rationale
- Pros and cons
- Risk assessment
- Effort and cost estimates
- Scoring across criteria

### 4. Document Decisions
Use ADR format:
- Context: Why is this decision needed?
- Decision: What was decided?
- Consequences: What are the implications?
- Alternatives: What else was considered?

## Architecture Patterns

### Single Instance (Recommended for most)
- One Jira, one Confluence
- Simplest governance
- Best for <5000 users

### Multi-Instance
- Separate instances by BU/region
- Required for data residency
- Higher admin overhead

### Consolidated
- Merge multiple instances to one
- Complex migration
- Long-term simplification

### Hub & Spoke
- Central governance instance
- Federated operational instances
- Balance of control and autonomy

## Product Tiers

### Standard
- Most common choice
- 250GB storage
- Basic automation

### Premium
- Advanced features (sandbox, analytics)
- 24/7 support
- Unlimited storage
- Required for: >500 users, complex compliance

### Enterprise
- Data residency controls
- BYOK encryption
- Atlassian Access included
- Required for: regulated industries, global orgs

## Integration Patterns

### Native
- Atlassian-to-Atlassian (Jira ↔ Confluence)
- Always preferred

### Marketplace Apps
- Vetted, supported
- Consider CSK status

### Custom (API/Webhook)
- Maximum flexibility
- Higher maintenance

### iPaaS
- Workato, Zapier, etc.
- Good for non-technical teams

## Migration Approaches

### Lift and Shift
- Minimal changes
- Fastest
- Technical debt carried forward

### Replatform
- Clean up during migration
- Moderate effort
- Recommended for most

### Refactor
- Major restructuring
- Highest effort
- Best long-term outcome

## Sizing Guidelines

### User Counts
| Tier | Users | Monthly/User (EUR) |
|------|-------|-------------------|
| Standard | 1-500 | ~7-10 |
| Premium | 500-2000 | ~12-15 |
| Enterprise | 2000+ | Custom |

### App Budget
- Typical: 20-30% of license cost
- Critical apps: budget separately

## Handoff Rules
- From A3: WP1 findings as input
- To A4: Architecture decisions to codify
- To A5: Migration plan for execution
- To A6: Architecture document for QA
"""

    async def run(self, state: A2State) -> A2State:
        """Main execution logic for A2."""
        current_task = state.get("current_task", "")
        
        self.logger.info("A2 executing", task=current_task)
        
        if current_task == "assess_current_state":
            return await self._assess_current_state(state)
        elif current_task == "design_target_state":
            return await self._design_target_state(state)
        elif current_task == "evaluate_options":
            return await self._evaluate_options(state)
        elif current_task == "plan_migration":
            return await self._plan_migration(state)
        elif current_task == "calculate_sizing":
            return await self._calculate_sizing(state)
        elif current_task == "draft_document":
            return await self._draft_document(state)
        elif current_task == "full_architecture":
            return await self._execute_full_architecture(state)
        else:
            return await self._analyze_and_route(state)
    
    async def _analyze_and_route(self, state: A2State) -> A2State:
        """Route to next task."""
        if not state.get("current_state_complete"):
            state["current_task"] = "assess_current_state"
        elif not state.get("options_evaluated"):
            state["current_task"] = "evaluate_options"
        elif not state.get("target_designed"):
            state["current_task"] = "design_target_state"
        elif not state.get("migration_planned"):
            state["current_task"] = "plan_migration"
        elif not state.get("sizing_complete"):
            state["current_task"] = "calculate_sizing"
        else:
            state["current_task"] = "draft_document"
        return await self.run(state)
    
    async def _assess_current_state(self, state: A2State) -> A2State:
        """Assess current state architecture."""
        self.logger.info("Assessing current state")
        
        client_name = state.get("client_name", "Client")
        wp1_findings = state.get("wp1_findings", {})
        
        prompt = f"""Analyze the current state architecture for {client_name}.

Input from WP1:
{wp1_findings}

Create a comprehensive AS-IS assessment:

## 1. INSTANCE INVENTORY
For each instance:
- Name and URL
- Deployment type (Cloud/DC/Server)
- Products installed
- Version (if applicable)
- User count
- Project/space count
- Apps installed
- Data size estimate
- Age (years in production)

## 2. INTEGRATION MAP
Document all integrations:
- Source and target systems
- Integration type (native, app, API, webhook)
- Data exchanged
- Direction (inbound, outbound, bidirectional)
- Criticality

## 3. PAIN POINTS
List current architecture pain points:
- Performance issues
- Governance gaps
- Integration challenges
- User experience problems

## 4. TECHNICAL DEBT
Identify technical debt:
- Outdated configurations
- Unused customizations
- Workarounds that need fixing
- Security concerns

## 5. COMPLIANCE REQUIREMENTS
Note any compliance needs:
- Data residency
- Audit requirements
- Industry regulations

## 6. KEY OBSERVATIONS
Summarize critical findings that will influence the target architecture.

Be specific and evidence-based."""
        
        response = await self.think(prompt, tier=ModelTier.REASONING)
        
        state = self.add_artifact(
            state, "current_state_assessment",
            f"CurrentState_{client_name}_{datetime.utcnow().strftime('%Y%m%d')}",
            response
        )
        state["current_state_complete"] = True
        return state
    
    async def _evaluate_options(self, state: A2State) -> A2State:
        """Evaluate architecture options."""
        self.logger.info("Evaluating architecture options")
        
        client_name = state.get("client_name", "Client")
        wp1_findings = state.get("wp1_findings", {})
        constraints = state.get("constraints", [])
        
        prompt = f"""Create architecture options for {client_name}.

Context:
{wp1_findings}

Constraints:
{constraints}

## Architecture Options Analysis

Present 3 architecture options:

### OPTION A: Conservative
- Minimal change approach
- Lower risk, faster implementation
- May carry forward some technical debt

### OPTION B: Balanced (Recommended)
- Optimal balance of improvement and effort
- Addresses key pain points
- Manageable risk profile

### OPTION C: Transformational
- Maximum improvement
- Higher effort and risk
- Best long-term outcome

---

For EACH option, provide:

## 1. DESCRIPTION
- Instance strategy (single/multi/consolidated)
- Architecture pattern
- Key characteristics

## 2. INSTANCE DESIGN
| Instance | Purpose | Products | Tier | Users |
|----------|---------|----------|------|-------|

## 3. PROS
- List 4-6 advantages

## 4. CONS
- List 3-5 disadvantages

## 5. RISKS
- List key risks with severity

## 6. MITIGATIONS
- How to address each risk

## 7. SCORING (1-5, 5=best)
| Criterion | Score | Rationale |
|-----------|-------|-----------|
| Scalability | X | ... |
| Simplicity | X | ... |
| Cost Efficiency | X | ... |
| Security | X | ... |
| Governance | X | ... |
| **Total** | XX/25 | |

## 8. EFFORT & COST
- Implementation weeks
- Estimated cost range (EUR)

---

## RECOMMENDATION
- Which option is recommended and why
- Under what circumstances other options might be preferred

Be thorough but practical."""
        
        response = await self.think(prompt, tier=ModelTier.REASONING)
        
        state = self.add_artifact(
            state, "architecture_options",
            f"ArchitectureOptions_{client_name}_{datetime.utcnow().strftime('%Y%m%d')}",
            response
        )
        state["options_evaluated"] = True
        return state
    
    async def _design_target_state(self, state: A2State) -> A2State:
        """Design target state architecture."""
        self.logger.info("Designing target state")
        
        client_name = state.get("client_name", "Client")
        
        # Get previous artifacts
        options_content = ""
        for artifact in state.get("artifacts", []):
            if artifact["type"] == "architecture_options":
                options_content = artifact["content"]
                break
        
        prompt = f"""Design the detailed TO-BE architecture for {client_name}.

Based on the recommended option from:
{options_content[:3000]}

Create the complete target state design:

## 1. DESIGN PRINCIPLES
List 5-7 guiding principles for this architecture.

## 2. INSTANCE ARCHITECTURE

### Primary Instance(s)
For each instance:
- Name and purpose
- Products included
- Tier (Standard/Premium/Enterprise)
- Data residency
- Estimated users
- Key configurations

### Instance Relationship
If multiple instances, describe:
- How they relate
- What is shared vs separate
- Cross-instance integrations

## 3. PRODUCT CONFIGURATION

### Jira
- Project types to enable
- Issue type scheme
- Workflow strategy
- Automation approach
- Key apps required

### Confluence
- Space structure
- Template strategy
- Permissions approach
- Key apps required

### JSM (if applicable)
- Service desk structure
- SLA configuration
- Customer portal design
- ITSM features

### Other Products
- Jira Product Discovery
- Compass
- Atlas
- etc.

## 4. SECURITY ARCHITECTURE
- Authentication (SAML SSO)
- Identity provider integration
- User provisioning (SCIM)
- MFA requirements
- IP allowlisting
- API token policy
- Audit logging
- Data classification

## 5. INTEGRATION ARCHITECTURE
| Integration | Source | Target | Method | Priority |
|-------------|--------|--------|--------|----------|

For critical integrations, provide:
- Data flow description
- Implementation approach
- Error handling

## 6. GOVERNANCE INTEGRATION
How this architecture enables governance:
- Admin structure
- Permission model
- Change control
- Monitoring

## 7. KEY DESIGN DECISIONS
Document as ADRs:

### ADR-001: [Decision Title]
**Context**: Why is this decision needed?
**Decision**: What was decided?
**Consequences**: What are the implications?
**Alternatives**: What else was considered?

(Repeat for 3-5 key decisions)

## 8. ARCHITECTURE DIAGRAM (Description)
Describe the architecture diagram that should be created:
- Components to show
- Relationships to illustrate
- Data flows to indicate

Be detailed and implementation-ready."""
        
        response = await self.think(prompt, tier=ModelTier.REASONING)
        
        state = self.add_artifact(
            state, "target_state_design",
            f"TargetState_{client_name}_{datetime.utcnow().strftime('%Y%m%d')}",
            response, {"requires_review": True}
        )
        state["target_designed"] = True
        return state
    
    async def _plan_migration(self, state: A2State) -> A2State:
        """Plan migration approach."""
        self.logger.info("Planning migration")
        
        client_name = state.get("client_name", "Client")
        wp1_findings = state.get("wp1_findings", {})
        
        prompt = f"""Create a high-level migration plan for {client_name}.

Context:
{wp1_findings}

## Migration Plan

### 1. MIGRATION APPROACH
- Overall approach (lift-and-shift, replatform, refactor)
- Rationale for approach
- Key principles

### 2. SCOPE SUMMARY
| Category | Count | Complexity |
|----------|-------|------------|
| Projects | X | Low/Med/High |
| Spaces | X | Low/Med/High |
| Users | X | Low/Med/High |
| Apps | X | Low/Med/High |

### 3. WAVE STRATEGY
Recommend number of waves and criteria for grouping.

### WAVE 1: Pilot
- Purpose: Validate approach
- Scope: Low-risk, representative projects
- Success criteria
- Duration: X weeks

### WAVE 2: [Name]
- Scope and rationale
- Dependencies
- Duration

### WAVE 3: [Name]
(Continue as needed)

### FINAL WAVE: Cleanup
- Decommissioning old systems
- Data archival
- Documentation

### 4. CRITICAL PATH
Identify the critical path items:
- Hard dependencies
- Long lead-time items
- Risk mitigation activities

### 5. PREREQUISITES
What must be in place before migration:
- Cloud environment setup
- SSO configuration
- User communication
- Training
- Tooling

### 6. BLOCKERS & RISKS
| Risk | Impact | Mitigation |
|------|--------|------------|

### 7. TIMELINE OVERVIEW
| Phase | Duration | Key Activities |
|-------|----------|----------------|
| Preparation | X weeks | ... |
| Wave 1 | X weeks | ... |
| Wave 2 | X weeks | ... |
| Hypercare | X weeks | ... |

### 8. SUCCESS CRITERIA
How will we know migration is successful?
- Technical criteria
- User adoption criteria
- Business criteria

Be practical and risk-aware."""
        
        response = await self.think(prompt, tier=ModelTier.REASONING)
        
        state = self.add_artifact(
            state, "migration_plan",
            f"MigrationPlan_{client_name}_{datetime.utcnow().strftime('%Y%m%d')}",
            response
        )
        state["migration_planned"] = True
        return state
    
    async def _calculate_sizing(self, state: A2State) -> A2State:
        """Calculate sizing and licensing."""
        self.logger.info("Calculating sizing")
        
        client_name = state.get("client_name", "Client")
        wp1_findings = state.get("wp1_findings", {})
        
        # Get target state
        target_content = ""
        for artifact in state.get("artifacts", []):
            if artifact["type"] == "target_state_design":
                target_content = artifact["content"][:2000]
                break
        
        prompt = f"""Calculate sizing and licensing for {client_name}.

Context:
{wp1_findings}

Target State Summary:
{target_content}

## Sizing & Licensing Recommendation

### 1. LICENSE RECOMMENDATIONS

For each product:

#### Jira
- Tier: [Standard/Premium/Enterprise]
- User count: X
- Rationale: Why this tier?
- Key features needed:
  - Feature 1
  - Feature 2
- Annual cost estimate: €X,XXX

#### Confluence
- Tier: [Standard/Premium/Enterprise]
- User count: X
- Rationale
- Key features
- Annual cost: €X,XXX

#### JSM (if applicable)
- Tier and agent count
- Annual cost: €X,XXX

#### Atlassian Access (if needed)
- Required for: SSO, SCIM, security policies
- Annual cost: €X per user

### 2. APP BUDGET
| App Category | Estimated Annual Cost |
|--------------|----------------------|
| Essential (migration) | €X,XXX |
| Productivity | €X,XXX |
| Governance | €X,XXX |
| Integration | €X,XXX |
| **Total** | **€X,XXX** |

### 3. COST SUMMARY
| Category | Year 1 | Ongoing |
|----------|--------|---------|
| Jira licenses | €X,XXX | €X,XXX |
| Confluence licenses | €X,XXX | €X,XXX |
| JSM licenses | €X,XXX | €X,XXX |
| Atlassian Access | €X,XXX | €X,XXX |
| Marketplace apps | €X,XXX | €X,XXX |
| Implementation (BlueVektor) | €X,XXX | - |
| Training | €X,XXX | - |
| **Total** | **€XX,XXX** | **€XX,XXX** |

### 4. OPTIMIZATION OPPORTUNITIES
- License right-sizing
- App consolidation
- Feature utilization

### 5. NOTES & ASSUMPTIONS
- Pricing based on public rates
- Volume discounts may apply
- Subject to Atlassian pricing changes

Provide realistic estimates based on current Atlassian pricing."""
        
        response = await self.think(prompt)
        
        state = self.add_artifact(
            state, "sizing_recommendation",
            f"Sizing_{client_name}_{datetime.utcnow().strftime('%Y%m%d')}",
            response
        )
        state["sizing_complete"] = True
        return state
    
    async def _draft_document(self, state: A2State) -> A2State:
        """Draft complete architecture document."""
        self.logger.info("Drafting architecture document")
        
        client_name = state.get("client_name", "Client")
        
        artifacts_summary = {a["type"]: a["name"] for a in state.get("artifacts", [])}
        
        prompt = f"""Create the Solution Architecture Document for {client_name}.

Compile from these artifacts:
{list(artifacts_summary.keys())}

## SOLUTION ARCHITECTURE DOCUMENT

### COVER PAGE
- Title: Solution Architecture Document
- Client: {client_name}
- Version: 1.0
- Date: {datetime.utcnow().strftime('%Y-%m-%d')}
- Prepared by: BlueVektor

### TABLE OF CONTENTS
1. Executive Summary
2. Current State Assessment
3. Architecture Options
4. Target State Design
5. Migration Approach
6. Sizing & Licensing
7. Key Decisions (ADRs)
8. Next Steps
9. Appendices

---

### 1. EXECUTIVE SUMMARY
- Current situation (2-3 sentences)
- Recommended approach (2-3 sentences)
- Expected outcomes (3-4 bullets)
- Investment summary (high-level)
- Timeline summary

### 2. CURRENT STATE ASSESSMENT
(Summarize key findings from assessment)

### 3. ARCHITECTURE OPTIONS
(Summarize options and recommendation)

### 4. TARGET STATE DESIGN
(Summarize target architecture)
- Architecture diagram description
- Key components
- Security model

### 5. MIGRATION APPROACH
(Summarize migration plan)
- Wave strategy
- Timeline
- Key milestones

### 6. SIZING & LICENSING
(Summarize costs)
- License recommendations
- Cost summary

### 7. KEY DECISIONS
(List key ADRs)

### 8. NEXT STEPS
Recommended next actions:
1. Review and approve architecture
2. Finalize timeline
3. Begin Wave 1 preparation

### 9. APPENDICES
- A: Detailed current state
- B: Full option analysis
- C: Complete ADR log
- D: Glossary

---

Create a professional, executive-ready document."""
        
        response = await self.think(prompt, tier=ModelTier.REASONING)
        
        state = self.add_artifact(
            state, "architecture_document",
            f"ArchitectureDocument_{client_name}_{datetime.utcnow().strftime('%Y%m%d')}",
            response, {"requires_review": True}
        )
        state["document_drafted"] = True
        
        # Request handoff to A6 for QA
        state = self.request_handoff(
            state, target_agent="a6",
            context={"task": "qa_report", "report_type": "architecture_document", "client_name": client_name},
            priority="high"
        )
        
        return state
    
    async def _execute_full_architecture(self, state: A2State) -> A2State:
        """Execute complete architecture design process."""
        self.logger.info("Executing full architecture design")
        
        for task in ["assess_current_state", "evaluate_options", "design_target_state", 
                     "plan_migration", "calculate_sizing", "draft_document"]:
            state["current_task"] = task
            state = await self.run(state)
        
        return state


def create_a2_agent() -> A2ArchitectAgent:
    """Factory function to create A2 agent."""
    return A2ArchitectAgent()
