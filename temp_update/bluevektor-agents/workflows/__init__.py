"""
BlueVektor Agents - Workflows Module
"""
from workflows.lead_qualification import (
    LeadQualificationState,
    create_lead_qualification_workflow,
    run_lead_qualification,
)
from workflows.wp1_diagnostic import (
    WP1WorkflowState,
    create_wp1_workflow,
    run_wp1_diagnostic,
    resume_wp1_diagnostic,
)
from workflows.wp4_governance import (
    WP4WorkflowState,
    create_wp4_workflow,
    run_wp4_governance,
    resume_wp4_workflow,
)
from workflows.proposal_generation import (
    ProposalWorkflowState,
    create_proposal_workflow,
    run_proposal_generation,
    resume_proposal_workflow,
)
from workflows.architecture_design import (
    ArchitectureWorkflowState,
    create_architecture_workflow,
    run_architecture_design,
    resume_architecture_workflow,
)
from workflows.migration_execution import (
    MigrationWorkflowState,
    create_migration_workflow,
    run_migration_planning,
    resume_migration_workflow,
)
from workflows.implementation import (
    ImplementationWorkflowState,
    create_implementation_workflow,
    run_implementation,
    resume_implementation_workflow,
)

__all__ = [
    # Lead Qualification
    "LeadQualificationState",
    "create_lead_qualification_workflow",
    "run_lead_qualification",
    # WP1 Diagnostic
    "WP1WorkflowState",
    "create_wp1_workflow",
    "run_wp1_diagnostic",
    "resume_wp1_diagnostic",
    # WP4 Governance
    "WP4WorkflowState",
    "create_wp4_workflow",
    "run_wp4_governance",
    "resume_wp4_workflow",
    # Proposal Generation
    "ProposalWorkflowState",
    "create_proposal_workflow",
    "run_proposal_generation",
    "resume_proposal_workflow",
    # Architecture Design
    "ArchitectureWorkflowState",
    "create_architecture_workflow",
    "run_architecture_design",
    "resume_architecture_workflow",
    # Migration Execution
    "MigrationWorkflowState",
    "create_migration_workflow",
    "run_migration_planning",
    "resume_migration_workflow",
    # Implementation
    "ImplementationWorkflowState",
    "create_implementation_workflow",
    "run_implementation",
    "resume_implementation_workflow",
]
