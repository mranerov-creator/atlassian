"""
BlueVektor Agents - A5: Migration Factory
WP2/WP5 execution: Cloud migrations, wave planning, and migration execution.
"""
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from agents.base import AgentConfig, AgentState, BaseAgent
from core.llm import ModelTier


# =============================================================================
# A5 Enums
# =============================================================================

class MigrationType(str, Enum):
    SERVER_TO_CLOUD = "server_to_cloud"  # WP2
    DC_TO_CLOUD = "dc_to_cloud"  # WP2
    CLOUD_TO_CLOUD = "cloud_to_cloud"  # WP5
    CONSOLIDATION = "consolidation"  # Multiple to one
    SPLIT = "split"  # One to multiple


class MigrationPhase(str, Enum):
    PLANNING = "planning"
    PREPARATION = "preparation"
    PRE_MIGRATION = "pre_migration"
    MIGRATION = "migration"
    VALIDATION = "validation"
    HYPERCARE = "hypercare"
    CLOSURE = "closure"


class WaveStatus(str, Enum):
    PLANNED = "planned"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    VALIDATING = "validating"
    COMPLETED = "completed"
    ROLLED_BACK = "rolled_back"


class ItemStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    MIGRATED = "migrated"
    VALIDATED = "validated"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class ValidationStatus(str, Enum):
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"
    PARTIAL = "partial"


class CleanupAction(str, Enum):
    ARCHIVE = "archive"
    DELETE = "delete"
    RETAIN = "retain"
    REDIRECT = "redirect"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# =============================================================================
# A5 Source/Target Schemas
# =============================================================================

class SourceSystem(BaseModel):
    """Source system for migration."""
    name: str
    type: str  # server, dc, cloud
    url: str
    version: str | None = None
    products: list[str] = Field(default_factory=list)
    total_projects: int = 0
    total_spaces: int = 0
    total_users: int = 0
    total_issues: int = 0
    total_pages: int = 0
    total_attachments_gb: float = 0.0
    apps_installed: list[str] = Field(default_factory=list)


class TargetSystem(BaseModel):
    """Target system for migration."""
    name: str
    type: str = "cloud"
    url: str
    organization_id: str | None = None
    products: list[str] = Field(default_factory=list)
    tier: str = "standard"
    data_residency: str = "eu"
    sso_configured: bool = False
    scim_configured: bool = False


# =============================================================================
# A5 Migration Item Schemas
# =============================================================================

class ProjectMigrationItem(BaseModel):
    """Jira project to migrate."""
    id: str
    key: str
    name: str
    project_type: str  # software, business, service_desk
    lead: str | None = None
    
    # Metrics
    issue_count: int = 0
    attachment_size_mb: float = 0.0
    workflow_count: int = 0
    custom_field_count: int = 0
    automation_count: int = 0
    
    # Migration details
    wave: int = 1
    priority: int = 1
    status: ItemStatus = ItemStatus.NOT_STARTED
    dependencies: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    
    # Mapping
    target_key: str | None = None
    target_project_type: str | None = None
    
    # Notes
    special_considerations: list[str] = Field(default_factory=list)
    cleanup_actions: list[str] = Field(default_factory=list)


class SpaceMigrationItem(BaseModel):
    """Confluence space to migrate."""
    id: str
    key: str
    name: str
    space_type: str  # global, personal
    
    # Metrics
    page_count: int = 0
    attachment_size_mb: float = 0.0
    blog_count: int = 0
    
    # Migration details
    wave: int = 1
    priority: int = 1
    status: ItemStatus = ItemStatus.NOT_STARTED
    dependencies: list[str] = Field(default_factory=list)
    
    # Mapping
    target_key: str | None = None
    
    # Notes
    special_considerations: list[str] = Field(default_factory=list)


class UserMigrationItem(BaseModel):
    """User to migrate."""
    username: str
    email: str
    display_name: str
    
    # Status
    status: ItemStatus = ItemStatus.NOT_STARTED
    target_account_id: str | None = None
    
    # Notes
    groups: list[str] = Field(default_factory=list)
    is_admin: bool = False


class AppMigrationItem(BaseModel):
    """Marketplace app to migrate."""
    app_key: str
    app_name: str
    vendor: str
    
    # Source details
    source_version: str | None = None
    source_data_stored: bool = False
    
    # Target details
    cloud_compatible: bool = True
    cloud_app_key: str | None = None
    migration_path: str = "install_fresh"  # install_fresh, migrate_data, replace, discontinue
    
    # Status
    status: ItemStatus = ItemStatus.NOT_STARTED
    
    # Notes
    data_migration_notes: str | None = None
    alternative_app: str | None = None


# =============================================================================
# A5 Wave Schemas
# =============================================================================

class WaveChecklist(BaseModel):
    """Pre/post migration checklist for a wave."""
    item: str
    category: str  # pre_migration, migration, post_migration, validation
    responsible: str
    completed: bool = False
    completed_at: str | None = None
    notes: str | None = None


class Wave(BaseModel):
    """Migration wave."""
    id: str
    number: int
    name: str
    description: str
    
    # Timing
    planned_start: str | None = None
    planned_end: str | None = None
    actual_start: str | None = None
    actual_end: str | None = None
    
    # Content
    projects: list[str] = Field(default_factory=list)  # Project keys
    spaces: list[str] = Field(default_factory=list)  # Space keys
    users: list[str] = Field(default_factory=list)  # Usernames
    apps: list[str] = Field(default_factory=list)  # App keys
    
    # Status
    status: WaveStatus = WaveStatus.PLANNED
    progress_percent: int = 0
    
    # Checklist
    checklist: list[WaveChecklist] = Field(default_factory=list)
    
    # Success criteria
    success_criteria: list[str] = Field(default_factory=list)
    
    # Rollback
    rollback_plan: str | None = None
    rollback_deadline: str | None = None


# =============================================================================
# A5 Validation Schemas
# =============================================================================

class ValidationCheck(BaseModel):
    """Single validation check."""
    id: str
    name: str
    category: str  # data_integrity, functionality, permissions, performance
    description: str
    
    # Execution
    automated: bool = False
    script: str | None = None
    
    # Results
    status: ValidationStatus = ValidationStatus.PENDING
    expected_value: str | None = None
    actual_value: str | None = None
    passed: bool | None = None
    notes: str | None = None


class ValidationReport(BaseModel):
    """Validation report for a wave or item."""
    wave_id: str | None = None
    item_id: str | None = None
    item_type: str | None = None  # project, space, user
    
    # Checks
    checks: list[ValidationCheck] = Field(default_factory=list)
    
    # Summary
    total_checks: int = 0
    passed_checks: int = 0
    failed_checks: int = 0
    pass_rate: float = 0.0
    
    # Status
    overall_status: ValidationStatus = ValidationStatus.PENDING
    
    # Sign-off
    validated_by: str | None = None
    validated_at: str | None = None


# =============================================================================
# A5 Communication Schemas
# =============================================================================

class CommunicationTemplate(BaseModel):
    """Communication template for migration."""
    id: str
    name: str
    type: str  # announcement, reminder, go_live, completion
    audience: str  # all_users, admins, wave_users, stakeholders
    
    subject: str
    body: str
    
    # Timing
    send_timing: str  # e.g., "2 weeks before wave", "day of migration"
    
    # Status
    sent: bool = False
    sent_at: str | None = None


class CommunicationPlan(BaseModel):
    """Complete communication plan."""
    templates: list[CommunicationTemplate] = Field(default_factory=list)
    stakeholder_list: list[str] = Field(default_factory=list)


# =============================================================================
# A5 Migration Plan Schema
# =============================================================================

class MigrationRisk(BaseModel):
    """Migration-specific risk."""
    id: str
    description: str
    level: RiskLevel
    probability: str  # low, medium, high
    impact: str  # low, medium, high
    mitigation: str
    contingency: str | None = None
    owner: str


class MigrationPlan(BaseModel):
    """Complete migration plan."""
    id: str
    name: str
    client_name: str
    migration_type: MigrationType
    
    # Systems
    source: SourceSystem
    target: TargetSystem
    
    # Scope
    total_projects: int = 0
    total_spaces: int = 0
    total_users: int = 0
    total_apps: int = 0
    
    # Items
    projects: list[ProjectMigrationItem] = Field(default_factory=list)
    spaces: list[SpaceMigrationItem] = Field(default_factory=list)
    users: list[UserMigrationItem] = Field(default_factory=list)
    apps: list[AppMigrationItem] = Field(default_factory=list)
    
    # Waves
    waves: list[Wave] = Field(default_factory=list)
    
    # Timeline
    planned_start: str | None = None
    planned_end: str | None = None
    current_phase: MigrationPhase = MigrationPhase.PLANNING
    
    # Risks
    risks: list[MigrationRisk] = Field(default_factory=list)
    
    # Communication
    communication_plan: CommunicationPlan | None = None
    
    # Metadata
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# =============================================================================
# A5 Execution Schemas
# =============================================================================

class MigrationTask(BaseModel):
    """Individual migration task."""
    id: str
    name: str
    description: str
    wave_id: str
    
    # Timing
    planned_start: str | None = None
    planned_duration_hours: int = 1
    actual_start: str | None = None
    actual_end: str | None = None
    
    # Assignment
    assigned_to: str | None = None
    
    # Status
    status: str = "pending"  # pending, in_progress, completed, blocked, failed
    progress_percent: int = 0
    
    # Dependencies
    depends_on: list[str] = Field(default_factory=list)
    
    # Notes
    notes: str | None = None
    blockers: list[str] = Field(default_factory=list)


class MigrationLog(BaseModel):
    """Migration execution log entry."""
    timestamp: str
    wave_id: str | None = None
    item_type: str | None = None
    item_id: str | None = None
    action: str
    status: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class ExecutionDashboard(BaseModel):
    """Migration execution dashboard."""
    migration_id: str
    
    # Overall progress
    current_phase: MigrationPhase
    overall_progress: int = 0
    
    # Wave progress
    total_waves: int = 0
    completed_waves: int = 0
    current_wave: str | None = None
    
    # Item progress
    projects_migrated: int = 0
    projects_total: int = 0
    spaces_migrated: int = 0
    spaces_total: int = 0
    users_migrated: int = 0
    users_total: int = 0
    
    # Health
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    
    # Recent activity
    recent_logs: list[MigrationLog] = Field(default_factory=list)


# =============================================================================
# A5 Runbook Schemas
# =============================================================================

class RunbookStep(BaseModel):
    """Step in migration runbook."""
    number: int
    title: str
    description: str
    action: str
    expected_result: str
    rollback: str | None = None
    estimated_duration_min: int = 5
    notes: str | None = None


class MigrationRunbook(BaseModel):
    """Migration runbook for a specific scenario."""
    id: str
    name: str
    description: str
    migration_type: MigrationType
    
    # Prerequisites
    prerequisites: list[str] = Field(default_factory=list)
    tools_required: list[str] = Field(default_factory=list)
    
    # Steps
    pre_migration_steps: list[RunbookStep] = Field(default_factory=list)
    migration_steps: list[RunbookStep] = Field(default_factory=list)
    post_migration_steps: list[RunbookStep] = Field(default_factory=list)
    validation_steps: list[RunbookStep] = Field(default_factory=list)
    
    # Rollback
    rollback_steps: list[RunbookStep] = Field(default_factory=list)
    
    # Troubleshooting
    common_issues: list[dict[str, str]] = Field(default_factory=list)


# =============================================================================
# A5 Agent State
# =============================================================================

class A5State(AgentState, total=False):
    """State specific to A5 agent."""
    client_name: str
    engagement_id: str
    migration_type: MigrationType
    
    # Inputs
    architecture_design: dict[str, Any]  # From A2
    source_system: SourceSystem | None
    target_system: TargetSystem | None
    
    # Working data
    migration_plan: MigrationPlan | None
    current_wave: Wave | None
    validation_reports: list[ValidationReport]
    
    # Progress
    inventory_complete: bool
    waves_planned: bool
    runbooks_created: bool
    communications_ready: bool
    execution_started: bool
    migration_complete: bool


# =============================================================================
# A5 Agent
# =============================================================================

class A5MigrationAgent(BaseAgent):
    """
    A5 - Migration Factory Agent
    
    Purpose: Execute WP2 (Cloud migration) and WP5 (instance migration).
    """
    
    def __init__(self):
        config = AgentConfig(
            id="a5",
            name="Migration Factory",
            role="WP2/WP5 Migration Execution",
            goal="Execute migrations with zero data loss, minimal downtime, and full validation",
            backstory="""You are the migration specialist of BlueVektor. You execute
complex Atlassian migrations with precision and care.

Your expertise includes:
- Server/DC to Cloud migrations (JCMA, CCMA)
- Cloud-to-cloud migrations
- Instance consolidations
- Data validation and integrity
- User migration and provisioning
- App migration strategies

You understand that migrations are high-risk operations that require
meticulous planning, clear communication, and thorough validation.

Key principles:
- No data left behind
- Validate at every step
- Clear rollback plans
- Communicate proactively
- Document everything""",
            model_tier=ModelTier.STANDARD,
            temperature=0.4,
            max_tokens=8192,
            tools=["filesystem", "atlassian", "validation"],
            allowed_handoffs=["a2", "a4", "a6"],
            artifacts_requiring_approval=["migration_plan", "wave_execution"],
        )
        super().__init__(config)
    
    def system_prompt(self) -> str:
        """System prompt for A5."""
        base = self.build_base_prompt()
        
        return f"""{base}

# A5-Specific Rules

## Migration Types

### WP2: Server/DC to Cloud
- Use Jira Cloud Migration Assistant (JCMA)
- Use Confluence Cloud Migration Assistant (CCMA)
- Plan for feature parity gaps
- Handle app migrations carefully

### WP5: Cloud to Cloud
- Cross-site project moves
- User migration between orgs
- Data export/import strategies

### Consolidation
- Multiple sources to single target
- Namespace conflict resolution
- Permission harmonization

## Wave Planning Strategy

### Wave Sizing
- Pilot wave: 1-3 small projects, limited users
- Standard wave: 5-15 projects, ~100 users
- Large wave: Up to 30 projects, ~500 users

### Wave Criteria
Group by:
1. Business unit / team
2. Dependencies (linked projects)
3. Risk level (low risk first)
4. User overlap

### Wave Sequence
1. **Pilot**: Low-risk, representative sample
2. **Early adopters**: Engaged teams, feedback providers
3. **Main waves**: Bulk of migration
4. **Complex**: High-risk, complex projects
5. **Cleanup**: Stragglers, archives

## Migration Checklist

### Pre-Migration
- [ ] Source system audit complete
- [ ] User mapping validated
- [ ] App compatibility checked
- [ ] SSO/SCIM configured
- [ ] Communication sent
- [ ] Rollback plan documented

### Migration Day
- [ ] Change freeze in source
- [ ] Final backup taken
- [ ] Migration assistant run
- [ ] Progress monitored
- [ ] Issues logged

### Post-Migration
- [ ] Data validation complete
- [ ] User access verified
- [ ] Functionality tested
- [ ] Performance acceptable
- [ ] Sign-off obtained

## Validation Framework

### Data Integrity
- Issue count matches
- Attachment checksums
- History preserved
- Links maintained

### Functionality
- Workflows operate correctly
- Automations fire
- Permissions enforced
- Integrations work

### User Acceptance
- Users can log in
- Users find their data
- Users can perform tasks

## Communication Templates

### Pre-Migration (2 weeks)
Subject: Upcoming migration - [Project/Team] to Cloud
Content: What, when, impact, preparation needed

### Day Before
Subject: Migration tomorrow - [Project/Team]
Content: Timeline, access changes, support contacts

### Go-Live
Subject: Migration complete - Welcome to Cloud!
Content: New URLs, login instructions, support

### Post-Migration (1 week)
Subject: Migration follow-up - How are things going?
Content: Feedback request, known issues, support

## Handoff Rules
- From A2: Architecture design with migration plan
- To A4: Governance setup in new environment
- To A6: Migration documentation for QA
"""

    async def run(self, state: A5State) -> A5State:
        """Main execution logic for A5."""
        current_task = state.get("current_task", "")
        
        self.logger.info("A5 executing", task=current_task)
        
        if current_task == "create_inventory":
            return await self._create_inventory(state)
        elif current_task == "plan_waves":
            return await self._plan_waves(state)
        elif current_task == "create_runbooks":
            return await self._create_runbooks(state)
        elif current_task == "prepare_communications":
            return await self._prepare_communications(state)
        elif current_task == "generate_checklists":
            return await self._generate_checklists(state)
        elif current_task == "create_validation_plan":
            return await self._create_validation_plan(state)
        elif current_task == "draft_migration_plan":
            return await self._draft_migration_plan(state)
        elif current_task == "full_wp2" or current_task == "full_wp5":
            return await self._execute_full_migration_planning(state)
        else:
            return await self._analyze_and_route(state)
    
    async def _analyze_and_route(self, state: A5State) -> A5State:
        """Route to next task."""
        if not state.get("inventory_complete"):
            state["current_task"] = "create_inventory"
        elif not state.get("waves_planned"):
            state["current_task"] = "plan_waves"
        elif not state.get("runbooks_created"):
            state["current_task"] = "create_runbooks"
        elif not state.get("communications_ready"):
            state["current_task"] = "prepare_communications"
        else:
            state["current_task"] = "draft_migration_plan"
        return await self.run(state)
    
    async def _create_inventory(self, state: A5State) -> A5State:
        """Create migration inventory."""
        self.logger.info("Creating migration inventory")
        
        client_name = state.get("client_name", "Client")
        architecture = state.get("architecture_design", {})
        migration_type = state.get("migration_type", MigrationType.SERVER_TO_CLOUD)
        
        prompt = f"""Create a migration inventory for {client_name}.

Migration Type: {migration_type}
Architecture Context: {architecture}

## Migration Inventory

### 1. SOURCE SYSTEM SUMMARY
| Attribute | Value |
|-----------|-------|
| Type | Server/DC/Cloud |
| URL | ... |
| Version | ... |
| Products | ... |

### 2. PROJECT INVENTORY
Create a table of all projects to migrate:

| Key | Name | Type | Issues | Attachments | Complexity | Wave | Priority | Notes |
|-----|------|------|--------|-------------|------------|------|----------|-------|
| IT-HD | IT Helpdesk | Service Desk | 5,000 | 2GB | Medium | 2 | High | ... |
| ENG-PLAT | Engineering | Software | 15,000 | 10GB | High | 3 | High | ... |

For each project note:
- Custom workflows
- Special automations
- Integration dependencies
- Known issues

### 3. SPACE INVENTORY (Confluence)
| Key | Name | Pages | Attachments | Complexity | Wave | Notes |
|-----|------|-------|-------------|------------|------|-------|

### 4. USER INVENTORY
- Total users: X
- Active users (90 days): X
- Admin users: X
- External users: X
- Service accounts: X

User migration considerations:
- Email domain changes?
- Username format changes?
- Group structure changes?

### 5. APP INVENTORY
| App | Vendor | Cloud Compatible | Migration Path | Data to Migrate | Priority |
|-----|--------|------------------|----------------|-----------------|----------|
| ScriptRunner | Adaptavist | Yes | Migrate scripts | Config only | High |
| Tempo | Tempo | Yes | Data migration | Worklogs | Critical |

Migration paths:
- **Native migration**: App supports data migration
- **Manual recreation**: Recreate configuration
- **Replace**: Use different cloud app
- **Discontinue**: Not needed in cloud

### 6. INTEGRATION INVENTORY
| Integration | Source | Target | Type | Migration Impact |
|-------------|--------|--------|------|------------------|

### 7. DATA SUMMARY
- Total issues: X
- Total pages: X
- Total attachments: X GB
- Total users: X
- Estimated migration time: X hours

### 8. COMPLEXITY ASSESSMENT
- Low complexity items: X
- Medium complexity items: X
- High complexity items: X
- Critical items: X

### 9. DEPENDENCIES MAP
Document key dependencies:
- Project A depends on Project B (linked issues)
- Space X referenced by Project Y

### 10. EXCLUSIONS
Items NOT to migrate:
- Archived projects older than X years
- Test/sandbox projects
- Deprecated spaces

Be thorough and specific."""
        
        response = await self.think(prompt, tier=ModelTier.REASONING)
        
        state = self.add_artifact(
            state, "migration_inventory",
            f"MigrationInventory_{client_name}_{datetime.utcnow().strftime('%Y%m%d')}",
            response
        )
        state["inventory_complete"] = True
        return state
    
    async def _plan_waves(self, state: A5State) -> A5State:
        """Plan migration waves."""
        self.logger.info("Planning waves")
        
        client_name = state.get("client_name", "Client")
        
        # Get inventory
        inventory = ""
        for artifact in state.get("artifacts", []):
            if artifact["type"] == "migration_inventory":
                inventory = artifact["content"][:3000]
                break
        
        prompt = f"""Create a wave plan for {client_name} migration.

Inventory Summary:
{inventory}

## Wave Plan

### WAVE STRATEGY
- Total waves recommended: X
- Wave duration: X days each
- Buffer between waves: X days
- Total timeline: X weeks

### WAVE 0: Preparation
**Objective**: Setup target environment

**Tasks**:
- Configure cloud organization
- Setup SSO/SCIM
- Install required apps
- Create permission schemes
- Test migration tooling

**Duration**: 1-2 weeks
**Go/No-Go Criteria**: All prerequisites complete

---

### WAVE 1: Pilot
**Objective**: Validate migration approach

**Scope**:
| Type | Items | Count |
|------|-------|-------|
| Projects | [List keys] | X |
| Spaces | [List keys] | X |
| Users | [Description] | X |
| Apps | [List] | X |

**Selection Criteria**:
- Low business risk
- Representative of larger population
- Engaged stakeholders
- Simple dependencies

**Success Criteria**:
- All data migrated
- Users can access
- Workflows function
- <24h downtime

**Timeline**:
- Prep: Day 1-2
- Migration: Day 3
- Validation: Day 4-5
- Sign-off: Day 5

**Risks & Mitigations**:
| Risk | Mitigation |
|------|------------|
| Data mismatch | Pre-migration validation |
| User access issues | Test SSO before migration |

---

### WAVE 2: Early Adopters
**Objective**: Build momentum, gather feedback

**Scope**: [Similar table]

**Selection Criteria**:
- Teams requesting migration
- Good technical champions
- Medium complexity

**Timeline**: [Similar breakdown]

---

### WAVE 3-N: Main Waves
[Repeat structure for each wave]

---

### FINAL WAVE: Cleanup
**Objective**: Complete migration, decommission source

**Scope**:
- Remaining stragglers
- Archive projects
- Historical data

**Tasks**:
- Final data sync
- Redirect setup
- Source decommission plan
- Documentation handover

---

## WAVE SUMMARY TABLE
| Wave | Name | Projects | Spaces | Users | Start | End | Status |
|------|------|----------|--------|-------|-------|-----|--------|
| 0 | Preparation | - | - | - | W1 | W2 | Planned |
| 1 | Pilot | X | X | X | W3 | W3 | Planned |
| 2 | Early Adopters | X | X | X | W4 | W4 | Planned |
| ... | ... | ... | ... | ... | ... | ... | ... |

## CRITICAL PATH
1. SSO configuration (blocker for all)
2. App installation (before Wave 1)
3. Pilot success (gate for Wave 2+)
4. [Other dependencies]

## CONTINGENCY
- If pilot fails: 2-week remediation window
- If major issues: Pause and assess
- Rollback window: 48 hours post-wave

Be practical and risk-aware."""
        
        response = await self.think(prompt, tier=ModelTier.REASONING)
        
        state = self.add_artifact(
            state, "wave_plan",
            f"WavePlan_{client_name}_{datetime.utcnow().strftime('%Y%m%d')}",
            response
        )
        state["waves_planned"] = True
        return state
    
    async def _create_runbooks(self, state: A5State) -> A5State:
        """Create migration runbooks."""
        self.logger.info("Creating runbooks")
        
        client_name = state.get("client_name", "Client")
        migration_type = state.get("migration_type", MigrationType.SERVER_TO_CLOUD)
        
        prompt = f"""Create migration runbooks for {client_name}.

Migration Type: {migration_type}

## Migration Runbooks

### RUNBOOK 1: Project Migration (Jira)

**Purpose**: Migrate a Jira project from source to cloud

**Prerequisites**:
- [ ] Cloud site configured
- [ ] User mapping complete
- [ ] JCMA installed and configured
- [ ] Target project key available
- [ ] Stakeholder notified

**Pre-Migration Steps**:
1. **Announce freeze** (30 min before)
   - Notify users of read-only mode
   - Disable webhooks/integrations
   
2. **Final backup**
   - Export project XML
   - Store in secure location
   
3. **Pre-flight checks**
   - Verify user mapping
   - Check custom field mapping
   - Confirm workflow compatibility

**Migration Steps**:
1. **Open JCMA**
   - Navigate to Settings > System > Migration Assistant
   
2. **Select project**
   - Check project in migration list
   - Review assessment results
   
3. **Configure mapping**
   - Map users
   - Map custom fields
   - Map workflow statuses
   
4. **Start migration**
   - Click "Migrate"
   - Monitor progress
   - Note any warnings/errors
   
5. **Verify completion**
   - Check migration log
   - Confirm all issues migrated

**Post-Migration Steps**:
1. **Validate data**
   - Compare issue counts
   - Check random sample
   - Verify attachments
   
2. **Test functionality**
   - Create test issue
   - Execute workflow transition
   - Check automations
   
3. **User verification**
   - Invite key user to test
   - Confirm access
   
4. **Update integrations**
   - Point to new project
   - Test data flow

**Rollback Procedure**:
1. Delete migrated project in cloud
2. Restore source project access
3. Notify users of rollback
4. Document issues for remediation

**Troubleshooting**:
| Issue | Cause | Solution |
|-------|-------|----------|
| Users not mapped | Email mismatch | Manual mapping |
| Attachments missing | Size limit | Migrate separately |
| Workflow error | Incompatible status | Map to valid status |

---

### RUNBOOK 2: Space Migration (Confluence)

**Purpose**: Migrate a Confluence space to cloud

[Similar structure to Jira runbook]

**Special Considerations**:
- Page macros compatibility
- Space templates
- Blog posts
- Page restrictions

---

### RUNBOOK 3: User Migration

**Purpose**: Provision users in cloud and map identities

**Steps**:
1. Export user list from source
2. Verify email addresses
3. Configure SCIM (if applicable)
4. Invite users to cloud site
5. Map user accounts in JCMA/CCMA
6. Verify login capability

**Troubleshooting**:
| Issue | Solution |
|-------|----------|
| Duplicate email | Merge accounts |
| Invalid email | Update before migration |
| Missing from IdP | Add to identity provider |

---

### RUNBOOK 4: App Migration

**Purpose**: Migrate or reconfigure marketplace apps

**By App Type**:

**ScriptRunner**:
- Export scripts from source
- Install in cloud
- Recreate scripts (syntax differences)
- Test thoroughly

**Tempo Timesheets**:
- Install cloud version
- Use Tempo migration tool
- Migrate worklogs
- Verify time data

**[Other common apps...]**

---

### RUNBOOK 5: Rollback Procedure

**Purpose**: Restore source system if migration fails

**Triggers**:
- Critical data loss
- Unacceptable downtime
- Business-critical blockers

**Steps**:
1. Communicate rollback decision
2. Disable cloud access
3. Restore source access
4. Re-enable integrations
5. Document what went wrong
6. Plan remediation

---

### RUNBOOK 6: Cutover Checklist

**D-7 (One week before)**:
- [ ] Final communication sent
- [ ] User mapping validated
- [ ] Test migration completed
- [ ] Rollback plan reviewed

**D-1 (Day before)**:
- [ ] Change freeze announced
- [ ] Final backup scheduled
- [ ] War room scheduled
- [ ] Stakeholders confirmed

**D-Day**:
- [ ] Source set to read-only
- [ ] Backup completed
- [ ] Migration started
- [ ] Progress monitored
- [ ] Validation started
- [ ] Access granted
- [ ] Go-live announced

**D+1**:
- [ ] Hypercare support active
- [ ] Issues tracked
- [ ] User feedback collected

Create comprehensive, step-by-step runbooks."""
        
        response = await self.think(prompt, tier=ModelTier.REASONING)
        
        state = self.add_artifact(
            state, "migration_runbooks",
            f"MigrationRunbooks_{client_name}_{datetime.utcnow().strftime('%Y%m%d')}",
            response
        )
        state["runbooks_created"] = True
        return state
    
    async def _prepare_communications(self, state: A5State) -> A5State:
        """Prepare migration communications."""
        self.logger.info("Preparing communications")
        
        client_name = state.get("client_name", "Client")
        
        prompt = f"""Create migration communication templates for {client_name}.

## Communication Plan

### COMMUNICATION CALENDAR
| Timing | Audience | Message Type | Channel |
|--------|----------|--------------|---------|
| 4 weeks before | All users | Migration announcement | Email, Slack |
| 2 weeks before | Wave users | Preparation instructions | Email |
| 1 week before | Wave users | Final reminder | Email, Slack |
| Day before | Wave users | Last call | Email, Slack |
| Migration day | Wave users | Go-live notification | Email, Slack |
| Day after | Wave users | Welcome & support | Email |
| 1 week after | Wave users | Feedback request | Survey |

---

### TEMPLATE 1: Initial Announcement (All Users)

**Subject**: Important: {client_name} Atlassian Cloud Migration

**Body**:
Dear Team,

We are excited to announce that we will be migrating our Atlassian tools (Jira and Confluence) to Atlassian Cloud over the coming weeks.

**Why are we migrating?**
- Improved performance and reliability
- Access to latest features
- Better mobile experience
- Enhanced security

**Timeline**:
- Migration begins: [Date]
- Expected completion: [Date]

**What does this mean for you?**
- Your data will be migrated automatically
- You will receive specific instructions before your team's migration
- There will be minimal disruption to your work

**Next Steps**:
- No action required at this time
- Watch for team-specific communications
- Questions? Contact [migration-support@company.com]

Best regards,
The IT Team

---

### TEMPLATE 2: Wave Notification (2 Weeks Before)

**Subject**: Action Required: Your Jira/Confluence Migration - [Date]

**Body**:
Hello [Team/User],

Your team's Atlassian tools are scheduled for migration to Cloud on **[Date]**.

**What you need to do before [Date]:**
1. Save any work in progress
2. Complete any critical issues/pages
3. Note any concerns and report to [contact]

**What will happen:**
- [Projects/Spaces] will be migrated
- Your data will be preserved
- You'll receive new login instructions

**Access during migration:**
- [Source] will be read-only during migration
- Migration typically takes 4-8 hours
- You'll be notified when complete

**Questions?** Reply to this email or contact [support]

---

### TEMPLATE 3: Day Before Reminder

**Subject**: Tomorrow: Your Atlassian Migration

**Body**:
Hi [Name],

This is a reminder that your migration is **tomorrow, [Date]**.

**Timeline:**
- [Time]: Source becomes read-only
- [Time]: Migration begins
- [Time] (estimated): Migration complete
- [Time]: Access to Cloud available

**Checklist:**
✓ Save all work today
✓ Note any issues you're working on
✓ Bookmark new Cloud URL: [URL]

**Support:**
- During migration: [Contact]
- After migration: [Support channel]

See you in the Cloud!

---

### TEMPLATE 4: Go-Live Notification

**Subject**: ✅ Migration Complete - Welcome to Atlassian Cloud!

**Body**:
Great news! Your migration is complete.

**Your new URLs:**
- Jira: [new-url.atlassian.net]
- Confluence: [new-url.atlassian.net/wiki]

**How to log in:**
1. Go to [URL]
2. Click "Log in with SSO"
3. Use your company credentials

**What's new:**
- Faster performance
- New mobile apps
- Updated interface (quick tour: [link])

**Need help?**
- Quick start guide: [link]
- Known issues: [link]
- Support: [channel/email]

Welcome to Cloud!

---

### TEMPLATE 5: Post-Migration Survey (1 Week)

**Subject**: Quick Survey: How's the new Cloud experience?

**Body**:
Hi [Name],

It's been a week since your migration. We'd love your feedback!

**Quick Survey (2 minutes):** [Survey link]

**Questions?** Still having issues? Let us know: [support]

Thanks for your patience during the migration!

---

### TEMPLATE 6: Issue/Delay Notification

**Subject**: Update: Atlassian Migration Delay

**Body**:
We encountered an issue during migration that requires additional time.

**Status**: [Brief description]
**New timeline**: [Updated estimate]
**Impact**: [What users should expect]

We apologize for the inconvenience. Updates will follow.

Contact [support] with questions.

---

### STAKEHOLDER COMMUNICATIONS

**Executive Update Template**:
- Status summary
- Key metrics
- Risk summary
- Upcoming milestones
- Decisions needed

**Weekly Status Report**:
- Waves completed
- Issues encountered
- Next week plan
- Blockers

Create clear, actionable communications."""
        
        response = await self.think(prompt)
        
        state = self.add_artifact(
            state, "communication_templates",
            f"Communications_{client_name}_{datetime.utcnow().strftime('%Y%m%d')}",
            response
        )
        state["communications_ready"] = True
        return state
    
    async def _create_validation_plan(self, state: A5State) -> A5State:
        """Create validation plan."""
        self.logger.info("Creating validation plan")
        
        client_name = state.get("client_name", "Client")
        
        prompt = f"""Create a validation plan for {client_name} migration.

## Validation Plan

### 1. DATA INTEGRITY CHECKS

#### Jira Projects
| Check | Method | Expected | Automated |
|-------|--------|----------|-----------|
| Issue count | API comparison | Match | Yes |
| Attachment count | API comparison | Match | Yes |
| Comment count | API comparison | Match | Yes |
| Worklog entries | API comparison | Match | Yes |
| Issue links | Sample check | 95%+ intact | Partial |
| History records | Sample check | Preserved | Manual |

**Validation Script**:
```
For each project:
  source_count = source.getIssueCount(project)
  target_count = target.getIssueCount(project)
  assert source_count == target_count
```

#### Confluence Spaces
| Check | Method | Expected | Automated |
|-------|--------|----------|-----------|
| Page count | API comparison | Match | Yes |
| Attachment count | API comparison | Match | Yes |
| Page hierarchy | Sample check | Preserved | Manual |
| Macros rendered | Sample check | 90%+ working | Manual |

### 2. FUNCTIONALITY CHECKS

#### Jira
| Check | Test Method | Pass Criteria |
|-------|-------------|---------------|
| Create issue | Manual test | Issue created |
| Workflow transition | Manual test | Transition works |
| Search | Query test | Results match |
| Automation | Trigger test | Automation fires |
| Dashboard | Load test | Displays correctly |
| Filter | Execute | Returns expected |

#### Confluence
| Check | Test Method | Pass Criteria |
|-------|-------------|---------------|
| Create page | Manual test | Page created |
| Edit page | Manual test | Save works |
| Macros | Load test | Render correctly |
| Search | Query test | Finds content |
| Permissions | Access test | Enforced |

### 3. PERMISSION CHECKS

| Check | Method | Pass Criteria |
|-------|--------|---------------|
| Project admin access | Login test | Can configure |
| Team member access | Login test | Can view/edit |
| Restricted access | Login test | Cannot access |
| Guest access | Login test | Limited view |

### 4. INTEGRATION CHECKS

| Integration | Check | Pass Criteria |
|-------------|-------|---------------|
| SSO | Login flow | Successful auth |
| SCIM | User sync | Users provisioned |
| Slack | Notification | Message received |
| CI/CD | Build trigger | Issue updated |

### 5. PERFORMANCE CHECKS

| Metric | Threshold | Method |
|--------|-----------|--------|
| Page load | <3 seconds | Browser dev tools |
| Search response | <2 seconds | Stopwatch |
| API response | <500ms | API test |

### 6. USER ACCEPTANCE

**Checklist for Key Users**:
- [ ] Can log in successfully
- [ ] Can find my projects/spaces
- [ ] Can view my issues/pages
- [ ] Can create new content
- [ ] Can perform normal tasks
- [ ] Performance is acceptable

### 7. VALIDATION REPORT TEMPLATE

**Wave X Validation Report**

**Summary**:
- Total checks: X
- Passed: X (X%)
- Failed: X (X%)
- Pending: X

**Data Integrity**: PASS/FAIL
- Issue count: ✓
- Attachments: ✓
- Links: ⚠ (95% intact)

**Functionality**: PASS/FAIL
- Workflows: ✓
- Automations: ✓
- Search: ✓

**Permissions**: PASS/FAIL
- Admin access: ✓
- User access: ✓
- Restrictions: ✓

**User Acceptance**: PASS/FAIL
- Sign-offs received: X/X

**Issues Found**:
1. [Issue description] - [Severity] - [Resolution]

**Recommendation**: APPROVE / REMEDIATE / ROLLBACK

**Sign-off**:
- Technical Lead: _________ Date: _____
- Business Owner: _________ Date: _____

Create comprehensive validation framework."""
        
        response = await self.think(prompt)
        
        state = self.add_artifact(
            state, "validation_plan",
            f"ValidationPlan_{client_name}_{datetime.utcnow().strftime('%Y%m%d')}",
            response
        )
        return state
    
    async def _generate_checklists(self, state: A5State) -> A5State:
        """Generate migration checklists."""
        self.logger.info("Generating checklists")
        
        client_name = state.get("client_name", "Client")
        
        prompt = f"""Create comprehensive checklists for {client_name} migration.

## Migration Checklists

### MASTER CHECKLIST

#### Phase 1: Planning
- [ ] Migration assessment complete
- [ ] Architecture design approved
- [ ] Wave plan approved
- [ ] Timeline agreed
- [ ] Resources allocated
- [ ] Tools/licenses procured

#### Phase 2: Preparation
- [ ] Cloud site created
- [ ] SSO configured and tested
- [ ] SCIM configured (if applicable)
- [ ] Apps installed and configured
- [ ] Permission schemes created
- [ ] Test migration completed
- [ ] Runbooks created
- [ ] Communication plan ready

#### Phase 3: Execution
- [ ] Wave 1 (Pilot) complete
- [ ] Wave 2 complete
- [ ] Wave N complete
- [ ] All data migrated
- [ ] All users migrated
- [ ] All apps migrated

#### Phase 4: Validation
- [ ] Data integrity verified
- [ ] Functionality tested
- [ ] User acceptance obtained
- [ ] Performance acceptable

#### Phase 5: Closure
- [ ] Source decommissioned
- [ ] Documentation complete
- [ ] Lessons learned captured
- [ ] Project closed

---

### PRE-WAVE CHECKLIST (Per Wave)

**T-2 Weeks**:
- [ ] Wave scope confirmed
- [ ] User list finalized
- [ ] Communication scheduled
- [ ] Dependencies checked

**T-1 Week**:
- [ ] Initial communication sent
- [ ] User mapping validated
- [ ] App configurations ready
- [ ] Test run successful

**T-1 Day**:
- [ ] Final reminder sent
- [ ] War room scheduled
- [ ] Support team briefed
- [ ] Rollback plan reviewed

---

### MIGRATION DAY CHECKLIST

**Start (T-0)**:
- [ ] Team assembled
- [ ] Communication channels open
- [ ] Source set to read-only
- [ ] Backup initiated

**Execute (T+1h)**:
- [ ] Migration assistant started
- [ ] Progress monitored
- [ ] Issues logged

**Validate (T+4h)**:
- [ ] Migration complete
- [ ] Data validation started
- [ ] Sample checks passed

**Go-Live (T+6h)**:
- [ ] Access enabled
- [ ] Users notified
- [ ] Hypercare started

---

### POST-WAVE CHECKLIST

**Day 1**:
- [ ] All users can access
- [ ] Critical issues tracked
- [ ] Support requests monitored

**Day 3**:
- [ ] Validation complete
- [ ] Sign-offs obtained
- [ ] Issues remediated

**Day 7**:
- [ ] Feedback survey sent
- [ ] Lessons captured
- [ ] Ready for next wave

---

### ROLLBACK DECISION CHECKLIST

**Trigger Assessment**:
- [ ] Data loss > 5%?
- [ ] Critical functionality broken?
- [ ] Downtime > 24 hours?
- [ ] Business-stopping issue?

**If YES to any**:
- [ ] Escalate to steering committee
- [ ] Assess rollback feasibility
- [ ] Communicate decision
- [ ] Execute rollback runbook

Create practical, usable checklists."""
        
        response = await self.think(prompt)
        
        state = self.add_artifact(
            state, "migration_checklists",
            f"Checklists_{client_name}_{datetime.utcnow().strftime('%Y%m%d')}",
            response
        )
        return state
    
    async def _draft_migration_plan(self, state: A5State) -> A5State:
        """Draft complete migration plan."""
        self.logger.info("Drafting migration plan")
        
        client_name = state.get("client_name", "Client")
        migration_type = state.get("migration_type", MigrationType.SERVER_TO_CLOUD)
        
        artifacts_summary = {a["type"]: a["name"] for a in state.get("artifacts", [])}
        
        prompt = f"""Create the complete Migration Plan document for {client_name}.

Migration Type: {migration_type}
Artifacts created: {list(artifacts_summary.keys())}

## MIGRATION PLAN DOCUMENT

### COVER PAGE
- Title: Atlassian Migration Plan
- Client: {client_name}
- Migration Type: {migration_type}
- Version: 1.0
- Date: {datetime.utcnow().strftime('%Y-%m-%d')}
- Prepared by: BlueVektor

### EXECUTIVE SUMMARY
- Current state summary
- Migration objectives
- Approach overview
- Timeline summary
- Key risks and mitigations
- Resource requirements

### 1. SCOPE
#### In Scope
- Products to migrate
- Projects/spaces count
- Users count
- Apps count

#### Out of Scope
- What's not included
- Future phases

### 2. APPROACH
- Migration type justification
- Tooling (JCMA, CCMA, etc.)
- Wave strategy
- Validation approach

### 3. SOURCE & TARGET
#### Source System
- Details from inventory

#### Target System
- Cloud configuration
- Tier and features
- Data residency

### 4. WAVE PLAN
- Summary from wave plan artifact
- Wave schedule
- Dependencies

### 5. TIMELINE
| Phase | Duration | Start | End |
|-------|----------|-------|-----|
| Preparation | X weeks | ... | ... |
| Wave 1 (Pilot) | X days | ... | ... |
| Wave 2-N | X weeks | ... | ... |
| Hypercare | X weeks | ... | ... |

### 6. RISKS & MITIGATIONS
| Risk | Level | Mitigation |
|------|-------|------------|
| Data loss | High | Multiple backups, validation |
| Extended downtime | Medium | Wave approach, off-hours |
| User adoption | Medium | Training, communications |

### 7. RESOURCE REQUIREMENTS
| Role | Responsibility | Commitment |
|------|----------------|------------|
| Project Manager | Coordination | 50% |
| Migration Lead | Execution | 100% |
| Technical SME | Support | 25% |
| Client Admin | Approvals | 20% |

### 8. COMMUNICATION PLAN
- Summary of communication approach
- Key milestones
- Channels

### 9. VALIDATION APPROACH
- Summary of validation plan
- Sign-off requirements

### 10. ROLLBACK STRATEGY
- Triggers for rollback
- Procedure summary
- Decision authority

### 11. SUCCESS CRITERIA
- Data integrity: 100%
- Functionality: 100%
- User access: 100%
- Downtime: <X hours per wave
- User satisfaction: >80%

### 12. APPENDICES
- A: Detailed inventory
- B: Wave plan details
- C: Runbooks
- D: Communication templates
- E: Validation checklists

Create a professional, comprehensive plan."""
        
        response = await self.think(prompt, tier=ModelTier.REASONING)
        
        state = self.add_artifact(
            state, "migration_plan",
            f"MigrationPlan_{client_name}_{datetime.utcnow().strftime('%Y%m%d')}",
            response, {"requires_review": True}
        )
        
        # Request handoff to A6 for QA
        state = self.request_handoff(
            state, target_agent="a6",
            context={"task": "qa_report", "report_type": "migration_plan", "client_name": client_name},
            priority="high"
        )
        
        return state
    
    async def _execute_full_migration_planning(self, state: A5State) -> A5State:
        """Execute complete migration planning."""
        self.logger.info("Executing full migration planning")
        
        for task in ["create_inventory", "plan_waves", "create_runbooks", 
                     "prepare_communications", "create_validation_plan",
                     "generate_checklists", "draft_migration_plan"]:
            state["current_task"] = task
            state = await self.run(state)
        
        return state


def create_a5_agent() -> A5MigrationAgent:
    """Factory function to create A5 agent."""
    return A5MigrationAgent()
