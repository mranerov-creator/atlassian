"""
Tests for A7 Builder Agent
"""
import pytest

from agents.a7_builder import (
    A7BuilderAgent,
    A7State,
    create_a7_agent,
    # Enums
    AutomationType,
    TriggerType,
    ActionType,
    ForgeModuleType,
    IntegrationPattern,
    ComplexityLevel,
    ScriptType,
    # Models
    AutomationCondition,
    AutomationAction,
    AutomationRule,
    AutomationLibrary,
    GroovyScript,
    ScriptLibrary,
    ForgeModule,
    ForgeFunction,
    ForgeApp,
    APIEndpoint,
    WebhookConfig,
    Integration,
    IntegrationCatalog,
    WorkflowValidator,
    WorkflowPostFunction,
    WorkflowEnhancement,
    GadgetConfig,
    DashboardSpec,
    JQLFilter,
    ImplementationPackage,
)
from core.orchestrator import AgentStatus


class TestA7BuilderAgent:
    """Test suite for A7 Builder agent."""
    
    def test_agent_creation(self):
        """Test agent can be created."""
        agent = create_a7_agent()
        
        assert agent.config.id == "a7"
        assert agent.config.name == "Builder"
        assert "a2" in agent.config.allowed_handoffs
        assert "a4" in agent.config.allowed_handoffs
        assert "a6" in agent.config.allowed_handoffs
    
    def test_system_prompt_contains_rules(self):
        """Test system prompt contains required elements."""
        agent = create_a7_agent()
        prompt = agent.system_prompt()
        
        assert "automation" in prompt.lower()
        assert "forge" in prompt.lower()
        assert "integration" in prompt.lower()
        assert "smart values" in prompt.lower() or "smartvalues" in prompt.lower()


class TestA7Enums:
    """Test A7 enums."""
    
    def test_automation_type(self):
        assert AutomationType.JIRA_AUTOMATION == "jira_automation"
        assert AutomationType.FORGE == "forge"
    
    def test_trigger_type(self):
        assert TriggerType.ISSUE_CREATED == "issue_created"
        assert TriggerType.SCHEDULED == "scheduled"
    
    def test_action_type(self):
        assert ActionType.UPDATE_FIELD == "update_field"
        assert ActionType.SEND_SLACK == "send_slack"
    
    def test_forge_module_type(self):
        assert ForgeModuleType.UI_KIT == "ui_kit"
        assert ForgeModuleType.TRIGGER == "trigger"
    
    def test_script_type(self):
        assert ScriptType.LISTENER == "listener"
        assert ScriptType.VALIDATOR == "validator"


class TestA7Models:
    """Test A7 Pydantic models."""
    
    def test_automation_condition(self):
        condition = AutomationCondition(
            type="field_condition",
            field="priority",
            operator="equals",
            value="Critical",
        )
        assert condition.operator == "equals"
    
    def test_automation_action(self):
        action = AutomationAction(
            type=ActionType.SEND_SLACK,
            target="#alerts",
            template="Issue {{issue.key}} created",
        )
        assert action.type == ActionType.SEND_SLACK
    
    def test_automation_rule(self):
        rule = AutomationRule(
            id="rule-001",
            name="Auto-assign to component lead",
            description="Assign based on component",
            trigger=TriggerType.ISSUE_CREATED,
            conditions=[
                AutomationCondition(type="field_condition", field="component", operator="not_empty")
            ],
            actions=[
                AutomationAction(type=ActionType.ASSIGN_USER, value="{{component.lead}}")
            ],
            complexity=ComplexityLevel.LOW,
        )
        assert rule.trigger == TriggerType.ISSUE_CREATED
        assert len(rule.conditions) == 1
    
    def test_automation_library(self):
        library = AutomationLibrary(
            name="Acme Automations",
            client_name="Acme Corp",
            rules=[
                AutomationRule(
                    id="r1", name="Rule 1", description="Test",
                    trigger=TriggerType.ISSUE_CREATED, actions=[]
                )
            ],
        )
        assert len(library.rules) == 1
    
    def test_groovy_script(self):
        script = GroovyScript(
            id="script-001",
            name="Custom Validator",
            description="Validate estimate",
            script_type=ScriptType.VALIDATOR,
            code="return issue.estimate > 0",
            complexity=ComplexityLevel.LOW,
        )
        assert script.script_type == ScriptType.VALIDATOR
    
    def test_forge_module(self):
        module = ForgeModule(
            key="main-panel",
            name="Issue Panel",
            module_type=ForgeModuleType.UI_KIT,
            description="Shows related info",
            function="panelHandler",
            title="Related Issues",
        )
        assert module.module_type == ForgeModuleType.UI_KIT
    
    def test_forge_function(self):
        func = ForgeFunction(
            key="panel-resolver",
            name="Panel Resolver",
            handler="index.panelHandler",
            code="export const panelHandler = () => {};",
        )
        assert func.handler == "index.panelHandler"
    
    def test_forge_app(self):
        app = ForgeApp(
            id="app-001",
            name="Custom Panel App",
            description="Displays custom data",
            permissions=["read:jira-work", "write:jira-work"],
            modules=[
                ForgeModule(
                    key="panel", name="Panel",
                    module_type=ForgeModuleType.UI_KIT,
                    description="Panel"
                )
            ],
            complexity=ComplexityLevel.HIGH,
        )
        assert len(app.permissions) == 2
    
    def test_api_endpoint(self):
        endpoint = APIEndpoint(
            method="POST",
            path="/api/incidents",
            description="Create incident",
            auth_type="bearer",
        )
        assert endpoint.method == "POST"
    
    def test_webhook_config(self):
        webhook = WebhookConfig(
            id="wh-001",
            name="Slack Notification",
            url="https://hooks.slack.com/xxx",
            events=["issue_created", "issue_updated"],
            enabled=True,
        )
        assert len(webhook.events) == 2
    
    def test_integration(self):
        integration = Integration(
            id="int-001",
            name="Jira-Slack",
            description="Send notifications",
            source="Jira",
            target="Slack",
            pattern=IntegrationPattern.WEBHOOK,
            complexity=ComplexityLevel.LOW,
        )
        assert integration.pattern == IntegrationPattern.WEBHOOK
    
    def test_workflow_validator(self):
        validator = WorkflowValidator(
            id="val-001",
            name="Require Description",
            description="Ensure description filled",
            validation_type="field_required",
            field="description",
            error_message="Description is required",
        )
        assert validator.validation_type == "field_required"
    
    def test_gadget_config(self):
        gadget = GadgetConfig(
            gadget_type="pie_chart",
            title="Issues by Status",
            jql="project = PROJ",
            chart_type="pie",
        )
        assert gadget.gadget_type == "pie_chart"
    
    def test_dashboard_spec(self):
        dashboard = DashboardSpec(
            id="dash-001",
            name="Team Dashboard",
            description="Sprint overview",
            columns=2,
            gadgets=[
                GadgetConfig(gadget_type="filter_results", title="Open Issues")
            ],
        )
        assert dashboard.columns == 2
    
    def test_jql_filter(self):
        filter_spec = JQLFilter(
            id="filter-001",
            name="My Open Issues",
            description="Current user's open issues",
            jql="assignee = currentUser() AND resolution = Unresolved",
        )
        assert "currentUser()" in filter_spec.jql
    
    def test_implementation_package(self):
        package = ImplementationPackage(
            name="Acme Implementation",
            client_name="Acme Corp",
            automation_rules=[],
            scripts=[],
            integrations=[],
            dashboards=[],
            total_items=10,
            estimated_implementation_days=5,
        )
        assert package.estimated_implementation_days == 5


class TestA7State:
    """Test A7 state management."""
    
    def test_state_initialization(self):
        state: A7State = {
            "agent_id": "a7",
            "workflow_id": "test",
            "client_name": "Acme Corp",
            "status": AgentStatus.IDLE,
            "messages": [],
            "artifacts": [],
            "decisions": [],
            "requirements_analyzed": False,
            "automations_designed": False,
            "scripts_created": False,
            "integrations_designed": False,
            "package_compiled": False,
        }
        
        assert state["agent_id"] == "a7"
        assert state["automations_designed"] is False


class TestA7Integration:
    """Integration tests for A7 (require API key)."""
    
    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Requires API key")
    async def test_design_automations(self):
        agent = create_a7_agent()
        
        state: A7State = {
            "agent_id": "a7",
            "workflow_id": "test_auto",
            "client_name": "Test Corp",
            "requirements": {"use_cases": ["auto-assign", "notifications"]},
            "current_task": "design_automations",
            "messages": [],
            "artifacts": [],
            "decisions": [],
            "status": AgentStatus.RUNNING,
            "requirements_analyzed": True,
        }
        
        result = await agent.run(state)
        
        assert result.get("automations_designed") is True
        assert len(result.get("artifacts", [])) > 0
    
    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Requires API key")
    async def test_full_implementation(self):
        agent = create_a7_agent()
        
        state: A7State = {
            "agent_id": "a7",
            "workflow_id": "test_impl",
            "client_name": "Test Corp",
            "engagement_id": "IMPL-TEST-001",
            "current_task": "full_implementation",
            "messages": [],
            "artifacts": [],
            "decisions": [],
            "status": AgentStatus.RUNNING,
        }
        
        result = await agent.run(state)
        
        assert result.get("package_compiled") is True
        assert len(result.get("artifacts", [])) >= 4
