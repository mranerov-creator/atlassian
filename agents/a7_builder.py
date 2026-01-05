"""
BlueVektor Agents - A7: Builder
Automation development, Forge apps, integrations, and technical implementations.
"""
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from agents.base import AgentConfig, AgentState, BaseAgent
from core.llm import ModelTier


# =============================================================================
# A7 Enums
# =============================================================================

class AutomationType(str, Enum):
    JIRA_AUTOMATION = "jira_automation"
    CONFLUENCE_AUTOMATION = "confluence_automation"
    JSM_AUTOMATION = "jsm_automation"
    SCRIPTRUNNER = "scriptrunner"
    FORGE = "forge"
    CONNECT = "connect"
    WEBHOOK = "webhook"
    REST_API = "rest_api"


class TriggerType(str, Enum):
    ISSUE_CREATED = "issue_created"
    ISSUE_UPDATED = "issue_updated"
    ISSUE_TRANSITIONED = "issue_transitioned"
    COMMENT_ADDED = "comment_added"
    SCHEDULED = "scheduled"
    MANUAL = "manual"
    WEBHOOK = "webhook"
    PAGE_CREATED = "page_created"
    PAGE_UPDATED = "page_updated"
    SLA_BREACHED = "sla_breached"


class ActionType(str, Enum):
    UPDATE_FIELD = "update_field"
    TRANSITION = "transition"
    SEND_EMAIL = "send_email"
    SEND_SLACK = "send_slack"
    CREATE_ISSUE = "create_issue"
    CREATE_PAGE = "create_page"
    ADD_COMMENT = "add_comment"
    ASSIGN_USER = "assign_user"
    LOG_WORK = "log_work"
    CALL_API = "call_api"
    RUN_SCRIPT = "run_script"


class ForgeModuleType(str, Enum):
    UI_KIT = "ui_kit"
    CUSTOM_UI = "custom_ui"
    TRIGGER = "trigger"
    FUNCTION = "function"
    RESOLVER = "resolver"
    SCHEDULED_TRIGGER = "scheduled_trigger"
    WEB_TRIGGER = "web_trigger"


class IntegrationPattern(str, Enum):
    SYNC = "sync"
    ASYNC = "async"
    EVENT_DRIVEN = "event_driven"
    POLLING = "polling"
    WEBHOOK = "webhook"
    BATCH = "batch"


class ComplexityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# =============================================================================
# A7 Automation Schemas
# =============================================================================

class AutomationCondition(BaseModel):
    """Condition for automation rule."""
    type: str  # field_condition, user_condition, jql, etc.
    field: str | None = None
    operator: str = "equals"
    value: str | None = None
    jql: str | None = None


class AutomationAction(BaseModel):
    """Action in automation rule."""
    type: ActionType
    target: str | None = None
    value: str | None = None
    template: str | None = None
    config: dict[str, Any] = Field(default_factory=dict)


class AutomationRule(BaseModel):
    """Jira/Confluence automation rule."""
    id: str
    name: str
    description: str
    automation_type: AutomationType = AutomationType.JIRA_AUTOMATION
    
    # Rule structure
    trigger: TriggerType
    trigger_config: dict[str, Any] = Field(default_factory=dict)
    conditions: list[AutomationCondition] = Field(default_factory=list)
    actions: list[AutomationAction] = Field(default_factory=list)
    
    # Scope
    project_scope: str = "all"  # all, specific, project_category
    projects: list[str] = Field(default_factory=list)
    
    # Settings
    enabled: bool = True
    run_as: str = "rule_actor"  # rule_actor, trigger_user
    notify_on_error: bool = True
    
    # Metadata
    complexity: ComplexityLevel = ComplexityLevel.LOW
    estimated_runs_per_day: int = 0
    
    # Documentation
    use_case: str | None = None
    test_scenario: str | None = None


class AutomationLibrary(BaseModel):
    """Collection of automation rules."""
    name: str
    client_name: str
    rules: list[AutomationRule] = Field(default_factory=list)
    categories: dict[str, list[str]] = Field(default_factory=dict)  # category -> rule IDs
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# =============================================================================
# A7 Script Schemas (ScriptRunner/Groovy)
# =============================================================================

class ScriptType(str, Enum):
    LISTENER = "listener"
    BEHAVIOR = "behavior"
    VALIDATOR = "validator"
    POST_FUNCTION = "post_function"
    CONDITION = "condition"
    ESCALATION = "escalation"
    JQL_FUNCTION = "jql_function"
    REST_ENDPOINT = "rest_endpoint"
    CONSOLE_SCRIPT = "console_script"


class GroovyScript(BaseModel):
    """ScriptRunner Groovy script."""
    id: str
    name: str
    description: str
    script_type: ScriptType
    
    # Code
    code: str
    imports: list[str] = Field(default_factory=list)
    
    # Configuration
    event: str | None = None  # For listeners
    project: str | None = None
    issue_type: str | None = None
    
    # Metadata
    complexity: ComplexityLevel = ComplexityLevel.MEDIUM
    cloud_compatible: bool = False  # ScriptRunner Cloud vs Server
    
    # Testing
    test_script: str | None = None
    test_data: dict[str, Any] = Field(default_factory=dict)


class ScriptLibrary(BaseModel):
    """Collection of scripts."""
    name: str
    client_name: str
    scripts: list[GroovyScript] = Field(default_factory=list)
    shared_functions: list[str] = Field(default_factory=list)


# =============================================================================
# A7 Forge App Schemas
# =============================================================================

class ForgeModule(BaseModel):
    """Forge app module."""
    key: str
    name: str
    module_type: ForgeModuleType
    description: str
    
    # Configuration
    function: str | None = None
    resource: str | None = None
    
    # For UI modules
    title: str | None = None
    icon: str | None = None
    
    # For triggers
    events: list[str] = Field(default_factory=list)
    interval: str | None = None  # For scheduled


class ForgeFunction(BaseModel):
    """Forge function code."""
    key: str
    name: str
    handler: str
    code: str
    
    # Dependencies
    imports: list[str] = Field(default_factory=list)
    api_calls: list[str] = Field(default_factory=list)


class ForgeApp(BaseModel):
    """Complete Forge app specification."""
    id: str
    name: str
    description: str
    
    # Manifest
    app_id: str | None = None
    permissions: list[str] = Field(default_factory=list)
    
    # Modules
    modules: list[ForgeModule] = Field(default_factory=list)
    
    # Functions
    functions: list[ForgeFunction] = Field(default_factory=list)
    
    # Resources (for Custom UI)
    static_resources: list[str] = Field(default_factory=list)
    
    # Metadata
    complexity: ComplexityLevel = ComplexityLevel.HIGH
    estimated_dev_days: int = 5
    
    # Documentation
    use_cases: list[str] = Field(default_factory=list)
    installation_guide: str | None = None


# =============================================================================
# A7 Integration Schemas
# =============================================================================

class APIEndpoint(BaseModel):
    """API endpoint specification."""
    method: str  # GET, POST, PUT, DELETE
    path: str
    description: str
    
    # Request
    headers: dict[str, str] = Field(default_factory=dict)
    query_params: list[str] = Field(default_factory=list)
    body_schema: dict[str, Any] | None = None
    
    # Response
    response_schema: dict[str, Any] | None = None
    error_codes: dict[str, str] = Field(default_factory=dict)
    
    # Auth
    auth_type: str = "bearer"  # bearer, basic, api_key


class WebhookConfig(BaseModel):
    """Webhook configuration."""
    id: str
    name: str
    url: str
    
    # Trigger
    events: list[str] = Field(default_factory=list)
    jql_filter: str | None = None
    
    # Request
    method: str = "POST"
    headers: dict[str, str] = Field(default_factory=dict)
    body_template: str | None = None
    
    # Settings
    enabled: bool = True
    retry_on_failure: bool = True


class Integration(BaseModel):
    """Integration specification."""
    id: str
    name: str
    description: str
    
    # Systems
    source: str
    target: str
    pattern: IntegrationPattern
    
    # Direction
    direction: str = "bidirectional"  # inbound, outbound, bidirectional
    
    # Implementation
    endpoints: list[APIEndpoint] = Field(default_factory=list)
    webhooks: list[WebhookConfig] = Field(default_factory=list)
    
    # Data mapping
    field_mappings: dict[str, str] = Field(default_factory=dict)
    transformations: list[str] = Field(default_factory=list)
    
    # Error handling
    retry_policy: str = "exponential_backoff"
    error_notification: str | None = None
    
    # Metadata
    complexity: ComplexityLevel = ComplexityLevel.MEDIUM
    estimated_dev_days: int = 3


class IntegrationCatalog(BaseModel):
    """Catalog of integrations."""
    client_name: str
    integrations: list[Integration] = Field(default_factory=list)


# =============================================================================
# A7 Workflow Enhancement Schemas
# =============================================================================

class WorkflowValidator(BaseModel):
    """Workflow validator."""
    id: str
    name: str
    description: str
    
    # When to apply
    transition: str | None = None  # All or specific
    
    # Validation logic
    validation_type: str  # field_required, regex, jql, script
    field: str | None = None
    expression: str | None = None
    error_message: str


class WorkflowPostFunction(BaseModel):
    """Workflow post-function."""
    id: str
    name: str
    description: str
    
    # When to apply
    transition: str | None = None
    
    # Function type
    function_type: str  # update_field, add_comment, send_email, script
    config: dict[str, Any] = Field(default_factory=dict)


class WorkflowEnhancement(BaseModel):
    """Complete workflow enhancement spec."""
    workflow_name: str
    description: str
    
    # Enhancements
    validators: list[WorkflowValidator] = Field(default_factory=list)
    post_functions: list[WorkflowPostFunction] = Field(default_factory=list)
    conditions: list[dict[str, Any]] = Field(default_factory=list)
    
    # Documentation
    transitions_affected: list[str] = Field(default_factory=list)


# =============================================================================
# A7 Dashboard & Report Schemas
# =============================================================================

class GadgetConfig(BaseModel):
    """Dashboard gadget configuration."""
    gadget_type: str  # filter_results, pie_chart, two_dimensional, etc.
    title: str
    
    # Data source
    filter_id: str | None = None
    jql: str | None = None
    
    # Display
    columns: list[str] = Field(default_factory=list)
    chart_type: str | None = None
    
    # Size
    column_span: int = 1
    row_span: int = 1


class DashboardSpec(BaseModel):
    """Dashboard specification."""
    id: str
    name: str
    description: str
    
    # Layout
    columns: int = 2
    gadgets: list[GadgetConfig] = Field(default_factory=list)
    
    # Sharing
    visibility: str = "private"  # private, project, global
    shared_with: list[str] = Field(default_factory=list)


class JQLFilter(BaseModel):
    """JQL filter specification."""
    id: str
    name: str
    description: str
    jql: str
    
    # Sharing
    visibility: str = "private"
    shared_with: list[str] = Field(default_factory=list)
    
    # Subscriptions
    subscriptions: list[dict[str, str]] = Field(default_factory=list)


# =============================================================================
# A7 Implementation Package
# =============================================================================

class ImplementationPackage(BaseModel):
    """Complete implementation package."""
    name: str
    client_name: str
    version: str = "1.0"
    
    # Contents
    automation_rules: list[AutomationRule] = Field(default_factory=list)
    scripts: list[GroovyScript] = Field(default_factory=list)
    forge_apps: list[ForgeApp] = Field(default_factory=list)
    integrations: list[Integration] = Field(default_factory=list)
    workflow_enhancements: list[WorkflowEnhancement] = Field(default_factory=list)
    dashboards: list[DashboardSpec] = Field(default_factory=list)
    filters: list[JQLFilter] = Field(default_factory=list)
    
    # Implementation plan
    dependencies: list[str] = Field(default_factory=list)
    installation_order: list[str] = Field(default_factory=list)
    
    # Documentation
    readme: str | None = None
    
    # Metadata
    total_items: int = 0
    estimated_implementation_days: int = 0
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# =============================================================================
# A7 Agent State
# =============================================================================

class A7State(AgentState, total=False):
    """State specific to A7 agent."""
    client_name: str
    engagement_id: str
    
    # Inputs
    requirements: dict[str, Any]
    governance_policies: dict[str, Any]  # From A4
    architecture: dict[str, Any]  # From A2
    
    # Working data
    automation_library: AutomationLibrary | None
    script_library: ScriptLibrary | None
    forge_apps: list[ForgeApp]
    integrations: list[Integration]
    implementation_package: ImplementationPackage | None
    
    # Progress
    requirements_analyzed: bool
    automations_designed: bool
    scripts_created: bool
    integrations_designed: bool
    package_compiled: bool


# =============================================================================
# A7 Agent
# =============================================================================

class A7BuilderAgent(BaseAgent):
    """
    A7 - Builder Agent
    
    Purpose: Build automations, scripts, Forge apps, and integrations.
    """
    
    def __init__(self):
        config = AgentConfig(
            id="a7",
            name="Builder",
            role="Automation & Integration Development",
            goal="Build robust, maintainable automations and integrations that solve real business problems",
            backstory="""You are the technical craftsman of BlueVektor. You translate
requirements into working code and configurations.

Your expertise includes:
- Jira/Confluence/JSM Automation rules
- ScriptRunner (Groovy) development
- Forge app development (UI Kit, Custom UI)
- REST API integrations
- Webhook configurations
- Dashboard and filter creation

You believe in:
- Clean, documented code
- Reusable patterns
- Error handling and logging
- Testing before deployment
- Progressive enhancement

You create solutions that are maintainable by the client's
team, not just clever hacks that only you understand.""",
            model_tier=ModelTier.STANDARD,
            temperature=0.3,  # Lower temp for code generation
            max_tokens=8192,
            tools=["filesystem", "code", "atlassian"],
            allowed_handoffs=["a2", "a4", "a6"],
            artifacts_requiring_approval=["forge_app", "integration"],
        )
        super().__init__(config)
    
    def system_prompt(self) -> str:
        """System prompt for A7."""
        base = self.build_base_prompt()
        
        return f"""{base}

# A7-Specific Rules

## Automation Best Practices

### Jira Automation
- Use descriptive rule names
- Add conditions to limit scope
- Consider performance (avoid heavy JQL in high-volume triggers)
- Use smart values effectively
- Test with audit log before enabling
- Document expected behavior

### Common Automation Patterns
1. **Auto-assign**: Assign based on component/label
2. **SLA escalation**: Transition/notify on SLA breach
3. **Sync fields**: Keep related issues in sync
4. **Notifications**: Custom Slack/email alerts
5. **Cleanup**: Archive stale issues
6. **Onboarding**: Create linked tasks on hire

### Smart Values Reference
- Issue: {{{{issue.key}}}}, {{{{issue.summary}}}}
- User: {{{{assignee.displayName}}}}, {{{{reporter.emailAddress}}}}
- Dates: {{{{now.plusDays(7)}}}}, {{{{issue.created.format("yyyy-MM-dd")}}}}
- Lookups: {{{{lookupIssues(issue.parent.key)}}}}

## Script Development

### ScriptRunner Patterns
```groovy
// Listener template
import com.atlassian.jira.component.ComponentAccessor

def issue = event.issue
def customFieldManager = ComponentAccessor.customFieldManager
def cf = customFieldManager.getCustomFieldObjectByName("My Field")
def value = issue.getCustomFieldValue(cf)

// Update field
def issueService = ComponentAccessor.issueService
def user = ComponentAccessor.jiraAuthenticationContext.loggedInUser
def inputParams = issueService.newIssueInputParameters()
inputParams.setCustomFieldValue(cf.idAsLong, newValue)
```

### Cloud vs Server
- Cloud: Limited ScriptRunner, use Automation + Forge
- Server/DC: Full ScriptRunner, Groovy scripts

## Forge Development

### Manifest Structure
```yaml
app:
  id: ari:cloud:ecosystem::app/xxx
  name: My Forge App
  
permissions:
  scopes:
    - read:jira-work
    - write:jira-work

modules:
  jira:issuePanel:
    - key: my-panel
      title: My Panel
      function: main
```

### UI Kit Components
- Text, Button, Form, Table
- Use Fragment for layouts
- useState for local state
- useProductContext for context

### Best Practices
- Handle errors gracefully
- Use async/await properly
- Minimize API calls
- Cache when possible
- Log for debugging

## Integration Patterns

### Webhook Design
- Validate incoming payloads
- Use secrets for auth
- Implement idempotency
- Handle retries gracefully

### API Integration
- Use OAuth 2.0 when available
- Implement rate limiting
- Cache tokens
- Log all requests/responses

### Error Handling
```javascript
try {{
  const response = await api.fetch(url);
  if (!response.ok) {{
    throw new Error(`HTTP ${{response.status}}`);
  }}
  return await response.json();
}} catch (error) {{
  console.error('API call failed:', error);
  // Notify, retry, or fail gracefully
}}
```

## Dashboard & Filters

### JQL Best Practices
- Use indexed fields (project, status, assignee)
- Avoid text searches in high-volume filters
- Use functions (currentUser(), startOfDay())
- Order by indexed fields

### Dashboard Layout
- Key metrics at top
- Related gadgets grouped
- Progressive detail (summary → drill-down)
- Consistent color coding

## Output Standards

### Automation Rule Format
```json
{{
  "name": "Auto-assign to component lead",
  "trigger": "issue_created",
  "conditions": [
    {{"type": "field_condition", "field": "component", "operator": "not_empty"}}
  ],
  "actions": [
    {{"type": "assign_user", "value": "{{{{component.lead}}}}"}}
  ]
}}
```

### Code Comments
- Explain WHY, not WHAT
- Document inputs/outputs
- Note any gotchas
- Include example usage

## Handoff Rules
- From A2: Architecture design for integration points
- From A4: Governance policies to enforce via automation
- To A6: Implementation package for QA
"""

    async def run(self, state: A7State) -> A7State:
        """Main execution logic for A7."""
        current_task = state.get("current_task", "")
        
        self.logger.info("A7 executing", task=current_task)
        
        if current_task == "analyze_requirements":
            return await self._analyze_requirements(state)
        elif current_task == "design_automations":
            return await self._design_automations(state)
        elif current_task == "create_scripts":
            return await self._create_scripts(state)
        elif current_task == "design_integrations":
            return await self._design_integrations(state)
        elif current_task == "create_dashboards":
            return await self._create_dashboards(state)
        elif current_task == "design_forge_app":
            return await self._design_forge_app(state)
        elif current_task == "compile_package":
            return await self._compile_package(state)
        elif current_task == "full_implementation":
            return await self._execute_full_implementation(state)
        else:
            return await self._analyze_and_route(state)
    
    async def _analyze_and_route(self, state: A7State) -> A7State:
        """Route to next task."""
        if not state.get("requirements_analyzed"):
            state["current_task"] = "analyze_requirements"
        elif not state.get("automations_designed"):
            state["current_task"] = "design_automations"
        elif not state.get("integrations_designed"):
            state["current_task"] = "design_integrations"
        else:
            state["current_task"] = "compile_package"
        return await self.run(state)
    
    async def _analyze_requirements(self, state: A7State) -> A7State:
        """Analyze automation/integration requirements."""
        self.logger.info("Analyzing requirements")
        
        client_name = state.get("client_name", "Client")
        requirements = state.get("requirements", {})
        governance = state.get("governance_policies", {})
        
        prompt = f"""Analyze automation and integration requirements for {client_name}.

Input Requirements:
{requirements}

Governance Policies to Enforce:
{governance}

## Requirements Analysis

### 1. AUTOMATION OPPORTUNITIES

Identify automation opportunities in these categories:

#### Workflow Automation
| Use Case | Trigger | Actions | Priority | Complexity |
|----------|---------|---------|----------|------------|
| Auto-assign on create | Issue Created | Assign based on component | High | Low |
| ... | ... | ... | ... | ... |

#### Notification Automation
| Use Case | Trigger | Recipients | Channel | Priority |
|----------|---------|------------|---------|----------|

#### Data Sync Automation
| Use Case | Source | Target | Frequency | Complexity |
|----------|--------|--------|-----------|------------|

#### Governance Enforcement
| Policy | Automation Approach | Trigger | Enforcement |
|--------|---------------------|---------|-------------|

### 2. INTEGRATION REQUIREMENTS

| Integration | Source | Target | Pattern | Data Flow | Priority |
|-------------|--------|--------|---------|-----------|----------|
| Jira-Slack | Jira | Slack | Webhook | Notifications | High |
| ... | ... | ... | ... | ... | ... |

### 3. CUSTOM DEVELOPMENT NEEDS

#### Scripts Needed
| Script | Type | Purpose | Complexity |
|--------|------|---------|------------|

#### Forge Apps Needed
| App | Modules | Purpose | Complexity |
|-----|---------|---------|------------|

### 4. DASHBOARD REQUIREMENTS

| Dashboard | Audience | Key Metrics | Gadgets |
|-----------|----------|-------------|---------|

### 5. IMPLEMENTATION PRIORITIES

**Phase 1 (Quick Wins)**:
- Low complexity, high value
- Native automation only

**Phase 2 (Core)**:
- Medium complexity
- Integrations

**Phase 3 (Advanced)**:
- Custom development
- Forge apps

### 6. EFFORT ESTIMATE

| Category | Items | Est. Days |
|----------|-------|-----------|
| Automation Rules | X | X |
| Scripts | X | X |
| Integrations | X | X |
| Dashboards | X | X |
| Forge Apps | X | X |
| **Total** | **X** | **X** |

### 7. RISKS & CONSIDERATIONS
- Performance impacts
- Maintenance requirements
- Skill requirements for ongoing support

Be thorough and practical."""
        
        response = await self.think(prompt, tier=ModelTier.REASONING)
        
        state = self.add_artifact(
            state, "requirements_analysis",
            f"RequirementsAnalysis_{client_name}_{datetime.utcnow().strftime('%Y%m%d')}",
            response
        )
        state["requirements_analyzed"] = True
        return state
    
    async def _design_automations(self, state: A7State) -> A7State:
        """Design automation rules."""
        self.logger.info("Designing automations")
        
        client_name = state.get("client_name", "Client")
        
        # Get requirements analysis
        req_analysis = ""
        for artifact in state.get("artifacts", []):
            if artifact["type"] == "requirements_analysis":
                req_analysis = artifact["content"][:2000]
                break
        
        prompt = f"""Design automation rules for {client_name}.

Requirements:
{req_analysis}

## Automation Library

Create a comprehensive automation library with rules for each category.

### WORKFLOW AUTOMATIONS

#### Rule 1: Auto-Assign Based on Component
**Name**: Auto-assign to component lead
**Description**: Automatically assign new issues to the component lead

**Trigger**: Issue Created
**Conditions**:
- Issue has component(s) set
- Assignee is empty

**Actions**:
1. Assign issue to: {{{{issue.components.first.lead}}}}
2. Add comment: "Auto-assigned to component lead"

**Scope**: All projects
**Smart Values Used**: {{{{issue.components.first.lead}}}}
**Complexity**: Low

---

#### Rule 2: SLA Breach Escalation
**Name**: Escalate on SLA breach
**Description**: Transition and notify on SLA breach

**Trigger**: SLA breach
**Conditions**:
- Issue type = Incident OR Bug
- Priority = High OR Critical

**Actions**:
1. Transition to: Escalated
2. Send Slack: @oncall - SLA breached for {{{{issue.key}}}}
3. Add label: sla-breached

**Scope**: Support projects
**Complexity**: Medium

---

### NOTIFICATION AUTOMATIONS

#### Rule 3: Slack Notification on Critical Bug
**Name**: Alert Slack on critical bug
**Trigger**: Issue Created
**Conditions**:
- Issue type = Bug
- Priority = Critical

**Actions**:
1. Send Slack to #engineering-alerts:
   "🚨 Critical Bug: {{{{issue.key}}}} - {{{{issue.summary}}}}"

---

### DATA SYNC AUTOMATIONS

#### Rule 4: Sync Parent-Child Status
**Name**: Update parent on subtask complete
**Trigger**: Issue Transitioned to Done
**Conditions**:
- Issue is subtask
- All sibling subtasks are Done

**Actions**:
1. Transition parent to: Ready for Review

---

### GOVERNANCE AUTOMATIONS

#### Rule 5: Enforce Required Fields
**Name**: Block transition without required fields
**Trigger**: Issue Transitioned (any)
**Conditions**:
- Target status = Done
- Description is empty OR Acceptance Criteria is empty

**Actions**:
1. Block transition
2. Show error: "Please fill in Description and Acceptance Criteria before closing"

---

#### Rule 6: Auto-Archive Stale Issues
**Name**: Archive inactive issues
**Trigger**: Scheduled (weekly)
**Conditions**:
- Status = Open or In Progress
- Updated > 90 days ago
- NOT Priority = Critical

**Actions**:
1. Add label: stale
2. Add comment: "This issue has been inactive for 90 days"
3. (After 30 more days): Transition to Archived

---

### ONBOARDING AUTOMATIONS

#### Rule 7: Create Onboarding Tasks
**Name**: Generate onboarding checklist
**Trigger**: Issue Created
**Conditions**:
- Issue type = New Hire
- Project = HR

**Actions**:
1. Create linked issue: IT Equipment Setup
2. Create linked issue: Access Provisioning
3. Create linked issue: Training Schedule
4. Assign to: {{{{issue.reporter}}}}

---

### ADVANCED AUTOMATIONS

[Add 3-5 more complex automations specific to client needs]

---

## AUTOMATION SUMMARY

| Category | Count | Complexity |
|----------|-------|------------|
| Workflow | X | Low-Medium |
| Notification | X | Low |
| Data Sync | X | Medium |
| Governance | X | Medium |
| Onboarding | X | Medium |
| Advanced | X | High |
| **Total** | **X** | - |

## IMPLEMENTATION NOTES
- Start with low-complexity rules
- Test thoroughly in sandbox
- Monitor audit log for first week
- Document expected behavior

Create detailed, implementable automation rules."""
        
        response = await self.think(prompt, tier=ModelTier.REASONING)
        
        state = self.add_artifact(
            state, "automation_library",
            f"AutomationLibrary_{client_name}_{datetime.utcnow().strftime('%Y%m%d')}",
            response
        )
        state["automations_designed"] = True
        return state
    
    async def _create_scripts(self, state: A7State) -> A7State:
        """Create scripts for advanced functionality."""
        self.logger.info("Creating scripts")
        
        client_name = state.get("client_name", "Client")
        
        prompt = f"""Create scripts for advanced automation needs for {client_name}.

## Script Library

### SCRIPTRUNNER SCRIPTS (Cloud)

#### Script 1: Bulk Field Update
**Name**: Bulk update custom field
**Type**: REST Endpoint
**Use Case**: Allow admins to bulk update a custom field across multiple issues

```groovy
// ScriptRunner Cloud - REST Endpoint
import com.atlassian.jira.component.ComponentAccessor
import com.onresolve.scriptrunner.runner.rest.common.CustomEndpointDelegate
import groovy.json.JsonSlurper
import groovy.transform.BaseScript

@BaseScript CustomEndpointDelegate delegate

bulkUpdate(httpMethod: "POST") {{ MultivaluedMap queryParams, String body ->
    def jsonSlurper = new JsonSlurper()
    def data = jsonSlurper.parseText(body)
    
    def issueManager = ComponentAccessor.issueManager
    def customFieldManager = ComponentAccessor.customFieldManager
    def user = ComponentAccessor.jiraAuthenticationContext.loggedInUser
    
    def cf = customFieldManager.getCustomFieldObjectByName(data.fieldName)
    def updated = []
    
    data.issueKeys.each {{ issueKey ->
        def issue = issueManager.getIssueObject(issueKey)
        if (issue) {{
            // Update logic here
            updated << issueKey
        }}
    }}
    
    return Response.ok([updated: updated, count: updated.size()]).build()
}}
```

---

#### Script 2: Custom Validator
**Name**: Validate estimate vs actual
**Type**: Validator
**Use Case**: Ensure time logged doesn't exceed estimate

```groovy
// Workflow Validator
import com.atlassian.jira.component.ComponentAccessor

def issue = issue
def originalEstimate = issue.originalEstimate ?: 0
def timeSpent = issue.timeSpent ?: 0

if (timeSpent > originalEstimate * 1.5) {{
    return false // Block transition
}}
return true
```

**Error Message**: "Time logged exceeds 150% of estimate. Please update estimate or get approval."

---

### AUTOMATION RULE SCRIPTS

#### Script 3: Smart Value Function
**Name**: Calculate business days
**Use Case**: Calculate business days between dates

```javascript
// Automation Rule - Send Web Request (Script)
const startDate = new Date('{{{{issue.created}}}}');
const endDate = new Date();
let businessDays = 0;

for (let d = new Date(startDate); d <= endDate; d.setDate(d.getDate() + 1)) {{
    const day = d.getDay();
    if (day !== 0 && day !== 6) businessDays++;
}}

return {{ businessDays }};
```

---

### FORGE FUNCTIONS

#### Script 4: Issue Panel Function
**Name**: Related Issues Panel
**Use Case**: Show related issues from external system

```typescript
// Forge Function - Issue Panel
import Resolver from '@forge/resolver';
import api, {{ route }} from '@forge/api';

const resolver = new Resolver();

resolver.define('getRelatedIssues', async ({{ context }}) => {{
  const issueKey = context.extension.issue.key;
  
  // Fetch from external API
  const response = await api.fetch('https://external-api.com/related', {{
    method: 'POST',
    headers: {{ 'Content-Type': 'application/json' }},
    body: JSON.stringify({{ issueKey }})
  }});
  
  if (!response.ok) {{
    return {{ error: 'Failed to fetch related issues' }};
  }}
  
  return await response.json();
}});

export const handler = resolver.getDefinitions();
```

---

### UTILITY SCRIPTS

#### Script 5: JQL Function
**Name**: issuesInSprint()
**Use Case**: Custom JQL function to find issues in sprint

```groovy
// ScriptRunner JQL Function
import com.atlassian.jira.jql.query.*
import com.atlassian.query.clause.*
import com.atlassian.query.operand.*

class IssuesInSprintFunction extends AbstractScriptedJqlFunction {{
    @Override
    String getFunctionName() {{
        return "issuesInSprint"
    }}
    
    @Override
    List<String> getArguments() {{
        return ["Sprint Name"]
    }}
    
    @Override
    Query getQuery(QueryCreationContext context, OperandResolver opResolver, 
                   List<String> args, TerminalClause clause) {{
        def sprintName = args[0]
        // Build query for sprint
        return new QueryImpl(/* clause */)
    }}
}}
```

---

## SCRIPT SUMMARY

| Script | Type | Complexity | Cloud Compatible |
|--------|------|------------|------------------|
| Bulk Field Update | REST Endpoint | High | Partial |
| Validate Estimate | Validator | Low | Yes |
| Business Days | Automation | Low | Yes |
| Related Issues | Forge | High | Yes |
| Sprint JQL | JQL Function | Medium | No (Server) |

## TESTING GUIDELINES
1. Test in sandbox environment first
2. Use test issues, not production data
3. Check performance with realistic data volumes
4. Verify error handling

Create practical, well-documented scripts."""
        
        response = await self.think(prompt, tier=ModelTier.REASONING)
        
        state = self.add_artifact(
            state, "script_library",
            f"ScriptLibrary_{client_name}_{datetime.utcnow().strftime('%Y%m%d')}",
            response
        )
        state["scripts_created"] = True
        return state
    
    async def _design_integrations(self, state: A7State) -> A7State:
        """Design integrations."""
        self.logger.info("Designing integrations")
        
        client_name = state.get("client_name", "Client")
        architecture = state.get("architecture", {})
        
        prompt = f"""Design integrations for {client_name}.

Architecture Context:
{architecture}

## Integration Catalog

### INTEGRATION 1: Jira ↔ Slack

**Name**: Jira-Slack Notification Integration
**Pattern**: Event-driven (Webhook)
**Direction**: Outbound

#### Use Cases
1. Notify channel on critical bug creation
2. Alert on-call on SLA breach
3. Celebrate when sprint goals met

#### Webhook Configuration
**URL**: https://hooks.slack.com/services/XXX
**Events**: 
- Issue Created (Bug, Critical)
- Issue Transitioned (to Done)
- SLA Breached

**Payload Template**:
```json
{{
  "channel": "#jira-alerts",
  "username": "Jira Bot",
  "icon_emoji": ":jira:",
  "attachments": [{{
    "color": "{{{{#if issue.priority.name == 'Critical'}}}}danger{{{{else}}}}good{{{{/if}}}}",
    "title": "{{{{issue.key}}}}: {{{{issue.summary}}}}",
    "title_link": "{{{{issue.url}}}}",
    "fields": [
      {{"title": "Type", "value": "{{{{issue.type}}}}", "short": true}},
      {{"title": "Priority", "value": "{{{{issue.priority}}}}", "short": true}}
    ]
  }}]
}}
```

#### Error Handling
- Retry: 3 attempts with exponential backoff
- Fallback: Log to audit, email admin

---

### INTEGRATION 2: Jira ↔ ServiceNow

**Name**: Incident Sync Integration
**Pattern**: Bidirectional Sync
**Direction**: Bidirectional

#### Data Flow
**Jira → ServiceNow**:
- Issue Created (type=Incident) → Create SNOW Incident
- Issue Updated → Update SNOW Incident
- Issue Resolved → Resolve SNOW Incident

**ServiceNow → Jira**:
- Incident Created → Create Jira Issue
- Incident Updated → Update Jira Issue
- Notes Added → Add Jira Comment

#### Field Mapping
| Jira Field | ServiceNow Field | Direction |
|------------|------------------|-----------|
| Summary | short_description | Bidirectional |
| Description | description | Bidirectional |
| Priority | priority | Bidirectional (mapped) |
| Assignee | assigned_to | Bidirectional |
| Status | state | Bidirectional (mapped) |
| Comments | work_notes | Bidirectional |

#### Priority Mapping
| Jira | ServiceNow |
|------|------------|
| Critical | 1 - Critical |
| High | 2 - High |
| Medium | 3 - Moderate |
| Low | 4 - Low |

#### API Endpoints
**Create Incident**:
```
POST /api/now/table/incident
Authorization: Bearer {{token}}
Content-Type: application/json

{{
  "short_description": "{{summary}}",
  "description": "{{description}}",
  "priority": "{{mapped_priority}}",
  "caller_id": "{{reporter}}"
}}
```

#### Sync Strategy
- Real-time for critical incidents
- Polling (5 min) for standard updates
- Conflict resolution: Last update wins

---

### INTEGRATION 3: Jira ↔ GitHub

**Name**: Development Workflow Integration
**Pattern**: Event-driven
**Direction**: Bidirectional

#### GitHub → Jira
- Commit message with issue key → Link commit to issue
- PR created with issue key → Add link, update status
- PR merged → Transition to "Ready for QA"
- Branch created → Update issue

#### Jira → GitHub
- Issue created (Epic/Story) → Create branch (optional)
- Smart commits: `PROJ-123 #comment Fixed the bug #time 2h`

#### Implementation
- Use Jira's native GitHub integration
- Configure in Project Settings → Development Tools
- Webhook: https://api.atlassian.com/github/webhook

---

### INTEGRATION 4: Jira ↔ CI/CD (Jenkins/GitHub Actions)

**Name**: Build Status Integration
**Pattern**: Webhook + API
**Direction**: Inbound

#### Events from CI/CD
- Build started → Update custom field "Build Status" = "In Progress"
- Build success → Update to "Success", add comment with link
- Build failed → Update to "Failed", notify assignee

#### Webhook Payload (Jenkins)
```json
{{
  "issueKey": "${{JIRA_ISSUE}}",
  "buildNumber": "${{BUILD_NUMBER}}",
  "buildUrl": "${{BUILD_URL}}",
  "status": "${{BUILD_STATUS}}",
  "branch": "${{GIT_BRANCH}}"
}}
```

#### Jira Automation Rule
**Trigger**: Incoming webhook
**Actions**: Update build status field, add comment

---

### INTEGRATION 5: Confluence ↔ Jira

**Name**: Documentation Sync
**Pattern**: Native + Automation
**Direction**: Bidirectional

#### Features
- Link Jira issues in Confluence pages
- Create Confluence page from Jira issue
- Embed Jira roadmaps in Confluence
- Auto-update release notes page

#### Automation Rules
1. On Epic complete → Update linked Confluence page
2. On Sprint start → Generate sprint page from template
3. On Release → Compile release notes

---

## INTEGRATION SUMMARY

| Integration | Pattern | Complexity | Est. Days |
|-------------|---------|------------|-----------|
| Jira-Slack | Webhook | Low | 0.5 |
| Jira-ServiceNow | Bidirectional | High | 5 |
| Jira-GitHub | Native + Webhook | Medium | 1 |
| Jira-CI/CD | Webhook + API | Medium | 2 |
| Confluence-Jira | Native + Automation | Low | 1 |
| **Total** | - | - | **9.5** |

## SECURITY CONSIDERATIONS
- Use OAuth 2.0 where available
- Store credentials in secure vault
- Rotate API tokens regularly
- Limit scope of permissions
- Audit integration activity

Create detailed, implementable integration designs."""
        
        response = await self.think(prompt, tier=ModelTier.REASONING)
        
        state = self.add_artifact(
            state, "integration_catalog",
            f"IntegrationCatalog_{client_name}_{datetime.utcnow().strftime('%Y%m%d')}",
            response
        )
        state["integrations_designed"] = True
        return state
    
    async def _create_dashboards(self, state: A7State) -> A7State:
        """Create dashboard specifications."""
        self.logger.info("Creating dashboards")
        
        client_name = state.get("client_name", "Client")
        
        prompt = f"""Create dashboard and filter specifications for {client_name}.

## Dashboard & Filter Library

### FILTERS

#### Filter 1: My Open Issues
**JQL**: `assignee = currentUser() AND resolution = Unresolved ORDER BY priority DESC, updated DESC`
**Audience**: All users
**Subscriptions**: Daily digest

#### Filter 2: Team Backlog
**JQL**: `project = PROJ AND sprint is EMPTY AND resolution = Unresolved AND type in (Story, Bug) ORDER BY rank ASC`
**Audience**: Team leads

#### Filter 3: Stale Issues
**JQL**: `resolution = Unresolved AND updated < -30d AND priority not in (Critical, Highest) ORDER BY updated ASC`
**Audience**: Project managers

#### Filter 4: Release Readiness
**JQL**: `fixVersion = "Release X.Y" AND resolution = Unresolved ORDER BY priority DESC`
**Audience**: Release managers

#### Filter 5: SLA At Risk
**JQL**: `"Time to resolution" > 80% AND resolution = Unresolved`
**Audience**: Support leads

---

### DASHBOARDS

#### Dashboard 1: Team Sprint Dashboard
**Audience**: Development team
**Columns**: 2

**Row 1 - Sprint Overview**:
| Gadget | Config |
|--------|--------|
| Sprint Health | Current sprint, burndown |
| Sprint Velocity | Last 5 sprints |

**Row 2 - Work Distribution**:
| Gadget | Config |
|--------|--------|
| Pie Chart | By Status |
| Pie Chart | By Assignee |

**Row 3 - Details**:
| Gadget | Config |
|--------|--------|
| Filter Results | Sprint issues (full width) |

---

#### Dashboard 2: Executive Summary
**Audience**: Leadership
**Columns**: 3

**Row 1 - KPIs**:
| Gadget | Config |
|--------|--------|
| Stats | Issues closed this week |
| Stats | Avg resolution time |
| Stats | SLA compliance % |

**Row 2 - Trends**:
| Gadget | Config |
|--------|--------|
| Created vs Resolved | Last 30 days |
| Pie Chart | By Priority (full width) |

**Row 3 - Focus Areas**:
| Gadget | Config |
|--------|--------|
| Filter Results | Critical open issues |

---

#### Dashboard 3: Support Queue
**Audience**: Support team
**Columns**: 2

**Row 1 - Queue Status**:
| Gadget | Config |
|--------|--------|
| Stats | Tickets awaiting response |
| Stats | Avg first response time |

**Row 2 - SLA Tracking**:
| Gadget | Config |
|--------|--------|
| SLA Goals | Time to first response |
| SLA Goals | Time to resolution |

**Row 3 - Queue Details**:
| Gadget | Config |
|--------|--------|
| Filter Results | Unassigned tickets |
| Filter Results | SLA at risk |

---

#### Dashboard 4: Release Tracking
**Audience**: Product/Release managers
**Columns**: 2

**Row 1 - Release Progress**:
| Gadget | Config |
|--------|--------|
| Version Report | Next release |
| Pie Chart | By Status |

**Row 2 - Blockers**:
| Gadget | Config |
|--------|--------|
| Filter Results | Blockers for release |
| Two-Dimensional | Priority x Component |

---

## IMPLEMENTATION NOTES

### Filter Best Practices
- Use indexed fields for performance
- Avoid `text ~` searches
- Use `ORDER BY` for consistent results
- Document filter purpose

### Dashboard Best Practices
- Limit to 6-8 gadgets
- Key metrics at top
- Use consistent colors
- Mobile-friendly layout

Create practical dashboards for real use cases."""
        
        response = await self.think(prompt)
        
        state = self.add_artifact(
            state, "dashboard_library",
            f"DashboardLibrary_{client_name}_{datetime.utcnow().strftime('%Y%m%d')}",
            response
        )
        return state
    
    async def _design_forge_app(self, state: A7State) -> A7State:
        """Design a Forge app."""
        self.logger.info("Designing Forge app")
        
        client_name = state.get("client_name", "Client")
        requirements = state.get("requirements", {})
        
        prompt = f"""Design a Forge app for {client_name}.

Requirements:
{requirements}

## Forge App Specification

### APP OVERVIEW
**Name**: [App Name]
**Description**: [What the app does]
**Use Cases**:
1. [Use case 1]
2. [Use case 2]

### MANIFEST.YML

```yaml
app:
  id: ari:cloud:ecosystem::app/[unique-id]
  name: [App Name]
  
permissions:
  scopes:
    - read:jira-work
    - write:jira-work
    - read:jira-user
    - storage:app
    
modules:
  jira:issuePanel:
    - key: main-panel
      title: [Panel Title]
      function: panel-resolver
      icon: https://example.com/icon.svg
      
  jira:issueAction:
    - key: quick-action
      title: [Action Title]
      function: action-handler
      
  trigger:
    - key: issue-created-trigger
      function: on-issue-created
      events:
        - avi:jira:created:issue
        
  scheduledTrigger:
    - key: daily-sync
      function: sync-handler
      interval: hour
      
  function:
    - key: panel-resolver
      handler: index.panelHandler
    - key: action-handler
      handler: index.actionHandler
    - key: on-issue-created
      handler: index.onIssueCreated
    - key: sync-handler
      handler: index.syncHandler
```

### FUNCTION CODE

#### index.tsx (UI Kit)
```typescript
import Resolver from '@forge/resolver';
import ForgeUI, {{
  render,
  Fragment,
  Text,
  Button,
  useState,
  useProductContext
}} from '@forge/ui';
import api, {{ route }} from '@forge/api';

// Panel Component
const Panel = () => {{
  const context = useProductContext();
  const [data, setData] = useState(null);
  
  const fetchData = async () => {{
    const response = await api.asApp().requestJira(
      route`/rest/api/3/issue/${{context.platformContext.issueKey}}`
    );
    const issue = await response.json();
    setData(issue);
  }};
  
  return (
    <Fragment>
      <Text>Issue: {{context.platformContext.issueKey}}</Text>
      <Button text="Refresh" onClick={{fetchData}} />
      {{data && <Text>Summary: {{data.fields.summary}}</Text>}}
    </Fragment>
  );
}};

export const panelHandler = render(<Panel />);

// Action Handler
const resolver = new Resolver();

resolver.define('runAction', async ({{ context, payload }}) => {{
  const issueKey = context.extension.issue.key;
  
  // Perform action
  await api.asApp().requestJira(route`/rest/api/3/issue/${{issueKey}}`, {{
    method: 'PUT',
    headers: {{ 'Content-Type': 'application/json' }},
    body: JSON.stringify({{
      fields: {{
        // Update fields
      }}
    }})
  }});
  
  return {{ success: true }};
}});

export const actionHandler = resolver.getDefinitions();

// Trigger Handler
export const onIssueCreated = async (event, context) => {{
  const {{ issue }} = event;
  console.log(`Issue created: ${{issue.key}}`);
  
  // Process new issue
  // Send notification, create linked items, etc.
}};

// Scheduled Handler
export const syncHandler = async (context) => {{
  console.log('Running scheduled sync');
  
  // Fetch data from external system
  // Update Jira issues
}};
```

### STORAGE SCHEMA

```typescript
// App storage for configuration
interface AppConfig {{
  enabled: boolean;
  webhookUrl: string;
  syncInterval: number;
}}

// Storage operations
import {{ storage }} from '@forge/api';

// Store config
await storage.set('config', {{ enabled: true, webhookUrl: '...' }});

// Retrieve config
const config = await storage.get('config');
```

### DEPLOYMENT

1. Install Forge CLI: `npm install -g @forge/cli`
2. Create app: `forge create`
3. Deploy: `forge deploy`
4. Install: `forge install --site your-site.atlassian.net`
5. Tunnel for dev: `forge tunnel`

### TESTING

```typescript
// Unit test example
import {{ mocks }} from '@forge/testing';

describe('Panel', () => {{
  it('should render issue key', async () => {{
    mocks.mockProductContext({{
      platformContext: {{ issueKey: 'TEST-1' }}
    }});
    
    // Render and assert
  }});
}});
```

### ESTIMATED EFFORT
- Initial setup: 0.5 days
- Core functionality: 3 days
- Testing: 1 day
- Documentation: 0.5 days
- **Total**: 5 days

Create a complete, deployable Forge app specification."""
        
        response = await self.think(prompt, tier=ModelTier.REASONING)
        
        state = self.add_artifact(
            state, "forge_app_spec",
            f"ForgeAppSpec_{client_name}_{datetime.utcnow().strftime('%Y%m%d')}",
            response, {"requires_review": True}
        )
        return state
    
    async def _compile_package(self, state: A7State) -> A7State:
        """Compile implementation package."""
        self.logger.info("Compiling implementation package")
        
        client_name = state.get("client_name", "Client")
        
        artifacts_list = [a["type"] for a in state.get("artifacts", [])]
        
        prompt = f"""Compile the implementation package for {client_name}.

Artifacts created: {artifacts_list}

## Implementation Package

### PACKAGE OVERVIEW
- **Client**: {client_name}
- **Version**: 1.0
- **Created**: {datetime.utcnow().strftime('%Y-%m-%d')}
- **Prepared by**: BlueVektor

### CONTENTS SUMMARY

| Category | Items | Complexity | Est. Days |
|----------|-------|------------|-----------|
| Automation Rules | X | Various | X |
| Scripts | X | Various | X |
| Integrations | X | Various | X |
| Dashboards | X | Low | X |
| Filters | X | Low | X |
| Forge Apps | X | High | X |
| **Total** | **X** | - | **X** |

### IMPLEMENTATION PLAN

#### Phase 1: Foundation (Week 1)
**Prerequisites**:
- [ ] Cloud site access (admin)
- [ ] API tokens created
- [ ] Integration endpoints available
- [ ] Test project created

**Tasks**:
1. Create filters (Day 1)
2. Create dashboards (Day 1-2)
3. Implement low-complexity automations (Day 2-3)
4. Test and validate (Day 4-5)

#### Phase 2: Core Automations (Week 2)
**Tasks**:
1. Implement workflow automations (Day 1-2)
2. Implement notification automations (Day 2-3)
3. Implement governance automations (Day 3-4)
4. Test and validate (Day 4-5)

#### Phase 3: Integrations (Week 3)
**Tasks**:
1. Configure Slack integration (Day 1)
2. Configure GitHub integration (Day 1-2)
3. Configure CI/CD webhooks (Day 2-3)
4. Test all integrations (Day 3-4)
5. Documentation (Day 5)

#### Phase 4: Advanced (Week 4+)
**Tasks**:
1. Deploy scripts (if applicable)
2. Deploy Forge apps (if applicable)
3. Performance tuning
4. User training
5. Handover documentation

### INSTALLATION ORDER

1. **Filters** (no dependencies)
   - My Open Issues
   - Team Backlog
   - [etc.]

2. **Dashboards** (depend on filters)
   - Team Sprint Dashboard
   - Executive Summary
   - [etc.]

3. **Automation Rules** (depend on fields/workflows)
   - Start with low-complexity
   - Enable one at a time
   - Monitor for conflicts

4. **Integrations** (depend on external systems)
   - Configure credentials first
   - Test connectivity
   - Enable production

5. **Scripts/Apps** (last)
   - Require deployment
   - Thorough testing

### DEPENDENCIES

| Item | Depends On |
|------|------------|
| SLA Dashboard | SLA custom fields configured |
| GitHub Integration | GitHub app installed |
| Slack Notifications | Slack webhook URL |
| ServiceNow Sync | SNOW API credentials |

### TESTING CHECKLIST

**For each automation**:
- [ ] Trigger fires correctly
- [ ] Conditions evaluated properly
- [ ] Actions execute as expected
- [ ] Error handling works
- [ ] No performance impact

**For each integration**:
- [ ] Authentication works
- [ ] Data flows correctly
- [ ] Errors handled
- [ ] Retry logic works
- [ ] Logging enabled

### ROLLBACK PROCEDURES

**Automation Rules**:
1. Disable the rule
2. Check audit log for affected issues
3. Manually reverse if needed

**Integrations**:
1. Disable webhook/connection
2. Check for pending data
3. Resync if needed

### DOCUMENTATION DELIVERABLES

1. **Admin Guide**
   - How to manage automations
   - How to update integrations
   - Troubleshooting guide

2. **User Guide**
   - Dashboard usage
   - Filter subscriptions
   - How to request changes

3. **Technical Reference**
   - API documentation
   - Script reference
   - Maintenance procedures

### MAINTENANCE REQUIREMENTS

**Weekly**:
- Review automation audit logs
- Check integration health

**Monthly**:
- Review rule performance
- Update filters if needed
- Check for Atlassian updates

**Quarterly**:
- Full review of all automations
- Cleanup unused items
- Performance optimization

### SUCCESS CRITERIA

- All automations running without errors
- Integrations syncing correctly
- Dashboards providing value
- Users trained and using tools
- Documentation complete

Create a comprehensive, implementable package."""
        
        response = await self.think(prompt, tier=ModelTier.REASONING)
        
        state = self.add_artifact(
            state, "implementation_package",
            f"ImplementationPackage_{client_name}_{datetime.utcnow().strftime('%Y%m%d')}",
            response, {"requires_review": True}
        )
        state["package_compiled"] = True
        
        # Request handoff to A6 for QA
        state = self.request_handoff(
            state, target_agent="a6",
            context={"task": "qa_report", "report_type": "implementation_package", "client_name": client_name},
            priority="high"
        )
        
        return state
    
    async def _execute_full_implementation(self, state: A7State) -> A7State:
        """Execute full implementation design."""
        self.logger.info("Executing full implementation design")
        
        for task in ["analyze_requirements", "design_automations", "create_scripts",
                     "design_integrations", "create_dashboards", "compile_package"]:
            state["current_task"] = task
            state = await self.run(state)
        
        return state


def create_a7_agent() -> A7BuilderAgent:
    """Factory function to create A7 agent."""
    return A7BuilderAgent()
