"""
BlueVektor Agents - A4: Governance Lead
WP4 execution: Operating model, policies, standards, and runbooks.
"""
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from agents.base import AgentConfig, AgentState, BaseAgent
from core.llm import ModelTier


# =============================================================================
# A4 Enums
# =============================================================================

class PolicyStatus(str, Enum):
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    PUBLISHED = "published"
    DEPRECATED = "deprecated"


class PolicyCategory(str, Enum):
    ACCESS = "access_control"
    NAMING = "naming_conventions"
    LIFECYCLE = "lifecycle_management"
    ARCHIVING = "archiving"
    PERMISSIONS = "permissions"
    DATA = "data_governance"
    SECURITY = "security"
    CHANGE = "change_management"
    INTEGRATION = "integration"
    APP = "app_governance"


class StandardType(str, Enum):
    WORKFLOW = "workflow"
    FIELD = "field"
    SCREEN = "screen"
    SCHEME = "scheme"
    PROJECT_TEMPLATE = "project_template"
    SPACE_TEMPLATE = "space_template"
    SLA = "sla"
    REQUEST_TYPE = "request_type"
    AUTOMATION = "automation"
    DASHBOARD = "dashboard"


class RACIRole(str, Enum):
    RESPONSIBLE = "R"
    ACCOUNTABLE = "A"
    CONSULTED = "C"
    INFORMED = "I"


class GovernanceMaturity(str, Enum):
    INITIAL = "initial"
    DEVELOPING = "developing"
    DEFINED = "defined"
    MANAGED = "managed"
    OPTIMIZING = "optimizing"


class CommitteeCadence(str, Enum):
    WEEKLY = "weekly"
    BIWEEKLY = "bi-weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"


# =============================================================================
# A4 Operating Model Schemas
# =============================================================================

class Role(BaseModel):
    """Governance role definition."""
    id: str
    name: str
    description: str
    responsibilities: list[str] = Field(default_factory=list)
    skills_required: list[str] = Field(default_factory=list)
    time_commitment: str | None = None
    reports_to: str | None = None


class RACIEntry(BaseModel):
    """Single RACI matrix entry."""
    activity: str
    responsible: list[str] = Field(default_factory=list)
    accountable: str
    consulted: list[str] = Field(default_factory=list)
    informed: list[str] = Field(default_factory=list)


class Committee(BaseModel):
    """Governance committee definition."""
    name: str
    purpose: str
    cadence: CommitteeCadence
    chair: str
    members: list[str] = Field(default_factory=list)
    standing_agenda: list[str] = Field(default_factory=list)
    decision_authority: list[str] = Field(default_factory=list)


class OperatingModel(BaseModel):
    """Complete operating model."""
    name: str = "Atlassian Governance Operating Model"
    version: str = "1.0"
    vision: str
    principles: list[str] = Field(default_factory=list)
    roles: list[Role] = Field(default_factory=list)
    raci_entries: list[RACIEntry] = Field(default_factory=list)
    committees: list[Committee] = Field(default_factory=list)
    current_maturity: GovernanceMaturity = GovernanceMaturity.INITIAL
    target_maturity: GovernanceMaturity = GovernanceMaturity.MANAGED
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# =============================================================================
# A4 Policy Schemas
# =============================================================================

class Policy(BaseModel):
    """Governance policy document."""
    id: str
    name: str
    category: PolicyCategory
    version: str = "1.0"
    status: PolicyStatus = PolicyStatus.DRAFT
    purpose: str
    scope: str
    policy_statement: str
    guardrails: list[str] = Field(default_factory=list)
    exceptions_process: str | None = None
    enforcement: str | None = None
    owner: str
    review_date: str | None = None
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class Guardrail(BaseModel):
    """Specific guardrail / rule."""
    id: str
    name: str
    category: PolicyCategory
    description: str
    rule_type: str
    rule_definition: str
    enforcement: str = "manual"
    good_examples: list[str] = Field(default_factory=list)
    bad_examples: list[str] = Field(default_factory=list)


# =============================================================================
# A4 Standards Schemas
# =============================================================================

class WorkflowStandard(BaseModel):
    """Standard workflow definition."""
    name: str
    description: str
    use_case: str
    statuses: list[str] = Field(default_factory=list)
    transitions: list[dict[str, str]] = Field(default_factory=list)


class FieldStandard(BaseModel):
    """Standard field definition."""
    name: str
    field_type: str
    description: str
    context: str
    required: bool = False


class SLAStandard(BaseModel):
    """Standard SLA definition."""
    name: str
    metric: str
    goals_by_priority: dict[str, str] = Field(default_factory=dict)


class ProjectTemplate(BaseModel):
    """Standard project template."""
    name: str
    key_pattern: str
    project_type: str
    workflow: str
    issue_types: list[str] = Field(default_factory=list)


class StandardsLibrary(BaseModel):
    """Complete standards library."""
    workflows: list[WorkflowStandard] = Field(default_factory=list)
    fields: list[FieldStandard] = Field(default_factory=list)
    slas: list[SLAStandard] = Field(default_factory=list)
    project_templates: list[ProjectTemplate] = Field(default_factory=list)
    naming_conventions: dict[str, str] = Field(default_factory=dict)


# =============================================================================
# A4 Runbook Schemas
# =============================================================================

class RunbookStep(BaseModel):
    """Single step in a runbook."""
    step_number: int
    title: str
    action: str
    expected_result: str
    notes: str | None = None


class Runbook(BaseModel):
    """Administrative runbook."""
    id: str
    name: str
    category: str
    purpose: str
    prerequisites: list[str] = Field(default_factory=list)
    steps: list[RunbookStep] = Field(default_factory=list)
    verification: list[str] = Field(default_factory=list)
    troubleshooting: list[dict[str, str]] = Field(default_factory=list)
    version: str = "1.0"


# =============================================================================
# A4 KPI Schemas
# =============================================================================

class KPI(BaseModel):
    """Key Performance Indicator."""
    id: str
    name: str
    category: str
    formula: str
    target: str
    warning_threshold: str
    critical_threshold: str
    measurement_frequency: str
    owner: str


class KPIDashboard(BaseModel):
    """KPI dashboard configuration."""
    name: str
    kpis: list[KPI] = Field(default_factory=list)
    review_cadence: str = "monthly"


# =============================================================================
# A4 Handbook Schema
# =============================================================================

class GovernanceHandbook(BaseModel):
    """Complete WP4 Governance Handbook."""
    title: str = "Atlassian Governance Handbook"
    client_name: str
    version: str = "1.0"
    status: str = "draft"
    operating_model: OperatingModel | None = None
    policies: list[Policy] = Field(default_factory=list)
    standards: StandardsLibrary | None = None
    runbooks: list[Runbook] = Field(default_factory=list)
    kpi_dashboard: KPIDashboard | None = None
    implementation_roadmap: list[dict[str, Any]] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# =============================================================================
# A4 Agent State
# =============================================================================

class A4State(AgentState, total=False):
    """State specific to A4 agent."""
    client_name: str
    engagement_id: str
    wp1_findings: dict[str, Any]
    architecture_target: dict[str, Any]
    current_maturity: GovernanceMaturity
    target_maturity: GovernanceMaturity
    operating_model_complete: bool
    policies_complete: bool
    standards_complete: bool
    runbooks_complete: bool
    kpis_complete: bool
    handbook_drafted: bool


# =============================================================================
# A4 Agent
# =============================================================================

class A4GovernanceAgent(BaseAgent):
    """
    A4 - Governance Lead Agent
    
    Purpose: Execute WP4 - Governance Office-in-a-Box.
    """
    
    def __init__(self):
        config = AgentConfig(
            id="a4",
            name="Governance Lead",
            role="WP4 Governance Office-in-a-Box",
            goal="Establish sustainable Atlassian governance with operating model, policies, standards, and runbooks",
            backstory="""You are the governance architect of BlueVektor. You transform 
chaotic Atlassian environments into well-governed, sustainable platforms.

Your expertise includes:
- ITIL and IT governance frameworks
- Atlassian platform administration
- Policy and standards development
- Change management and adoption
- RACI and operating model design

Key principles:
- Governance enables, not restricts
- Standards reduce cognitive load
- Automation enforces where possible
- Exceptions have a process
- Continuous improvement built-in""",
            model_tier=ModelTier.STANDARD,
            temperature=0.5,
            max_tokens=8192,
            tools=["filesystem", "templates"],
            allowed_handoffs=["a2", "a3", "a6"],
            artifacts_requiring_approval=["governance_handbook", "policy_library"],
        )
        super().__init__(config)
    
    def system_prompt(self) -> str:
        """System prompt for A4."""
        base = self.build_base_prompt()
        
        return f"""{base}

# A4-Specific Rules

## Operating Model Design
- Define roles: Platform Owner, Platform Admin, Project Admin, App Owner, Data Steward
- Create RACI for all governance activities
- Establish committees: Steering, CAB, Architecture Review

## Policy Framework
Categories: Access, Naming, Lifecycle, Permissions, Data, Security, Change, App Governance

Each policy needs:
- Purpose and scope
- Policy statement
- Guardrails (specific rules)
- Exceptions process
- Enforcement mechanism

## Standards Library
- Workflow standards by project type
- Field naming conventions
- Screen configurations
- SLA definitions for JSM
- Project templates

## Runbooks
Essential runbooks:
- User provisioning/deprovisioning
- Project creation
- Permission updates
- App installation
- Incident response

## KPI Framework
Track: Adoption, Compliance, Performance, Cost, Quality

## Handoff Rules
- From A3: WP1 findings to address
- From A2: Architecture to codify
- To A6: Handbook for QA
"""

    async def run(self, state: A4State) -> A4State:
        """Main execution logic for A4."""
        current_task = state.get("current_task", "")
        
        self.logger.info("A4 executing", task=current_task)
        
        if current_task == "design_operating_model":
            return await self._design_operating_model(state)
        elif current_task == "create_policies":
            return await self._create_policies(state)
        elif current_task == "create_standards":
            return await self._create_standards(state)
        elif current_task == "create_runbooks":
            return await self._create_runbooks(state)
        elif current_task == "define_kpis":
            return await self._define_kpis(state)
        elif current_task == "draft_handbook":
            return await self._draft_handbook(state)
        elif current_task == "full_wp4":
            return await self._execute_full_wp4(state)
        else:
            return await self._analyze_and_route(state)
    
    async def _analyze_and_route(self, state: A4State) -> A4State:
        """Route to next task."""
        if not state.get("operating_model_complete"):
            state["current_task"] = "design_operating_model"
        elif not state.get("policies_complete"):
            state["current_task"] = "create_policies"
        elif not state.get("standards_complete"):
            state["current_task"] = "create_standards"
        elif not state.get("runbooks_complete"):
            state["current_task"] = "create_runbooks"
        elif not state.get("kpis_complete"):
            state["current_task"] = "define_kpis"
        else:
            state["current_task"] = "draft_handbook"
        return await self.run(state)
    
    async def _design_operating_model(self, state: A4State) -> A4State:
        """Design governance operating model."""
        self.logger.info("Designing operating model")
        
        client_name = state.get("client_name", "Client")
        wp1_findings = state.get("wp1_findings", {})
        
        prompt = f"""Design a governance operating model for {client_name}.

Context: {wp1_findings}

Create:
1. Vision statement for Atlassian governance
2. 5-7 guiding principles
3. Role definitions (Platform Owner, Admin, Project Admin, App Owner, Data Steward)
4. RACI matrix for key activities
5. Committee structure (Steering, CAB, Architecture Review)
6. Decision rights matrix
7. Escalation paths
8. Maturity assessment (current vs target)

Be practical and actionable."""
        
        response = await self.think(prompt, tier=ModelTier.REASONING)
        
        state = self.add_artifact(
            state, "operating_model",
            f"OperatingModel_{client_name}_{datetime.utcnow().strftime('%Y%m%d')}",
            response
        )
        state["operating_model_complete"] = True
        return state
    
    async def _create_policies(self, state: A4State) -> A4State:
        """Create governance policies."""
        self.logger.info("Creating policies")
        
        client_name = state.get("client_name", "Client")
        
        prompt = f"""Create governance policies for {client_name}.

Create policies for:
1. Access Control - SSO, account types, access requests
2. Naming Conventions - projects, spaces, groups, fields
3. Project Lifecycle - creation, maintenance, archival
4. Permissions - role-based access control
5. Data Governance - classification, retention
6. Security - authentication, API tokens, audit
7. Change Management - change categories, approvals
8. App Governance - intake, evaluation, renewal

Each policy needs:
- Purpose
- Scope
- Policy statement
- Specific guardrails/rules
- Exceptions process
- Enforcement mechanism"""
        
        response = await self.think(prompt, tier=ModelTier.REASONING)
        
        state = self.add_artifact(
            state, "policy_library",
            f"PolicyLibrary_{client_name}_{datetime.utcnow().strftime('%Y%m%d')}",
            response
        )
        state["policies_complete"] = True
        return state
    
    async def _create_standards(self, state: A4State) -> A4State:
        """Create standards library."""
        self.logger.info("Creating standards")
        
        client_name = state.get("client_name", "Client")
        
        prompt = f"""Create standards library for {client_name}.

Include:
1. Workflow Standards
   - Software Development workflow
   - ITSM Incident workflow
   - Business Process workflow
   
2. Field Standards
   - Global standard fields
   - Naming conventions
   - Field hygiene rules

3. Screen Standards
   - Create/Edit/View screens by type

4. Issue Type Standards
   - Software, Service Desk, Business types

5. SLA Standards (JSM)
   - By priority for incidents
   - By priority for service requests

6. Project Templates
   - Software Team template
   - Service Desk template
   - Business Project template

7. Automation Standards
   - Standard automations
   - Naming conventions

8. Dashboard Standards
   - Team dashboard
   - Service desk dashboard"""
        
        response = await self.think(prompt, tier=ModelTier.REASONING)
        
        state = self.add_artifact(
            state, "standards_library",
            f"StandardsLibrary_{client_name}_{datetime.utcnow().strftime('%Y%m%d')}",
            response
        )
        state["standards_complete"] = True
        return state
    
    async def _create_runbooks(self, state: A4State) -> A4State:
        """Create admin runbooks."""
        self.logger.info("Creating runbooks")
        
        client_name = state.get("client_name", "Client")
        
        prompt = f"""Create admin runbooks for {client_name}.

Create detailed runbooks for:
1. User Provisioning
2. User Deprovisioning
3. Project Creation
4. Permission Scheme Update
5. App Installation
6. Workflow Modification
7. Custom Field Creation
8. Backup & Recovery
9. Incident Response
10. Annual Review

Each runbook needs:
- Purpose
- Prerequisites
- Step-by-step instructions
- Verification steps
- Troubleshooting guide
- Rollback procedure (if applicable)"""
        
        response = await self.think(prompt, tier=ModelTier.REASONING)
        
        state = self.add_artifact(
            state, "runbook_library",
            f"RunbookLibrary_{client_name}_{datetime.utcnow().strftime('%Y%m%d')}",
            response
        )
        state["runbooks_complete"] = True
        return state
    
    async def _define_kpis(self, state: A4State) -> A4State:
        """Define KPI framework."""
        self.logger.info("Defining KPIs")
        
        client_name = state.get("client_name", "Client")
        
        prompt = f"""Create KPI framework for {client_name}.

Define KPIs for:

ADOPTION
- Active User Rate
- Feature Adoption

COMPLIANCE
- Naming Convention Compliance
- Permission Standard Compliance
- Orphaned Items

PERFORMANCE
- Platform Availability
- Issue Resolution Time

COST
- License Utilization
- App ROI
- Cost per User

QUALITY
- Data Quality Score
- Stale Content Rate

GOVERNANCE
- Change Success Rate
- Policy Exception Rate
- Maturity Score

For each KPI:
- Formula
- Target
- Warning/Critical thresholds
- Measurement frequency
- Data source
- Owner

Also create dashboard layouts for:
- Executive (monthly)
- Operations (weekly)
- Governance (monthly)"""
        
        response = await self.think(prompt)
        
        state = self.add_artifact(
            state, "kpi_framework",
            f"KPIFramework_{client_name}_{datetime.utcnow().strftime('%Y%m%d')}",
            response
        )
        state["kpis_complete"] = True
        return state
    
    async def _draft_handbook(self, state: A4State) -> A4State:
        """Draft complete governance handbook."""
        self.logger.info("Drafting handbook")
        
        client_name = state.get("client_name", "Client")
        
        artifacts_content = {a["type"]: a["content"] for a in state.get("artifacts", [])}
        
        prompt = f"""Create the complete WP4 Governance Handbook for {client_name}.

Compile from these components:
{list(artifacts_content.keys())}

Structure:
1. Cover Page
2. Table of Contents
3. Introduction (purpose, scope, how to use)
4. Operating Model (summary)
5. Policy Library (summary with key rules)
6. Standards Library (reference guide)
7. Runbook Library (index with links)
8. KPI Framework (dashboard overview)
9. Implementation Roadmap (30/60/90)
10. Quick Wins
11. Appendices

Make it professional, comprehensive, and actionable."""
        
        response = await self.think(prompt, tier=ModelTier.REASONING)
        
        state = self.add_artifact(
            state, "governance_handbook",
            f"GovernanceHandbook_{client_name}_{datetime.utcnow().strftime('%Y%m%d')}",
            response, {"requires_review": True}
        )
        state["handbook_drafted"] = True
        
        state = self.request_handoff(
            state, target_agent="a6",
            context={"task": "qa_report", "report_type": "wp4_handbook", "client_name": client_name},
            priority="high"
        )
        return state
    
    async def _execute_full_wp4(self, state: A4State) -> A4State:
        """Execute complete WP4 flow."""
        self.logger.info("Executing full WP4")
        
        for task in ["design_operating_model", "create_policies", "create_standards", 
                     "create_runbooks", "define_kpis", "draft_handbook"]:
            state["current_task"] = task
            state = await self.run(state)
        
        return state


def create_a4_agent() -> A4GovernanceAgent:
    """Factory function to create A4 agent."""
    return A4GovernanceAgent()
