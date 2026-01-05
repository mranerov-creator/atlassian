# BlueVektor Agents

AI-native workforce for BlueVektor - Atlassian Cloud Enterprise Consulting.

## Overview

BlueVektor Agents is a multi-agent system designed to accelerate the creation, sale, and delivery of consulting workpackages (WP1 Diagnostic, WP4 Governance, etc.) while maintaining quality and traceability.

### Agent Roster

| ID | Name | Purpose | Status |
|----|------|---------|--------|
| A0 | CEO / Strategist | Strategy, positioning, pricing | Planned |
| **A1** | **GTM & Partnerships** | **Pipeline generation, qualification, outreach** | ✅ Implemented |
| A2 | Solution Architect | TO-BE design, technical decisions | Planned |
| **A3** | **Assessment Analyst** | **WP1 execution, evidence, hotspots, 30/60/90** | ✅ Implemented |
| **A4** | **Governance Lead** | **WP4 execution, policies, standards, runbooks** | ✅ Implemented |
| A5 | Migration Factory | WP2/WP5 execution, wave planning | Planned |
| **A6** | **Delivery PM/QA** | **QA, proposals, SoW, project management** | ✅ Implemented |
| A7 | Builder | Automation, tools, integrations | Planned |

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Anthropic API key

### Setup

```bash
# Clone the repo
git clone https://github.com/bluevektor/bluevektor-agents.git
cd bluevektor-agents

# Copy environment file
cp .env.example .env

# Edit .env and add your ANTHROPIC_API_KEY
nano .env

# Start infrastructure (PostgreSQL + Redis)
docker-compose up -d postgres redis

# Install Python dependencies
pip install -e ".[dev]"

# Initialize database
bv init

# Verify agents are registered
bv agents
```

### Usage Examples

#### Qualify a Lead

```bash
bv a1 qualify \
  --company "Acme Corp" \
  --email "john@acme.com" \
  --notes "Interested in Cloud migration, currently on Server"
```

#### Generate Outreach Sequence

```bash
bv a1 outreach \
  --company "TechPartner Inc" \
  --type "partner" \
  --lang "en" \
  --output outreach_techpartner.md
```

#### Prepare Discovery Call

```bash
bv a1 discovery \
  --company "Enterprise Co" \
  --context "They mentioned pain with multiple Jira instances" \
  --output discovery_agenda.md
```

#### Create Opportunity Brief

```bash
# From discovery call notes
bv a1 brief discovery_notes.txt --output opportunity_brief.md
```

### A3 Assessment Analyst - WP1 Diagnostic

#### Execute Full WP1 Diagnostic

```bash
bv a3 wp1 \
  --client "Acme Corp" \
  --engagement "WP1-ACME-001" \
  --url "https://acme.atlassian.net" \
  --output ./wp1_output/
```

#### Collect Evidence

```bash
bv a3 evidence \
  --client "Acme Corp" \
  --output evidence_plan.md
```

#### Identify Hotspots

```bash
bv a3 hotspots \
  --client "Acme Corp" \
  --evidence evidence_data.md \
  --output hotspot_map.md
```

#### Generate 30/60/90 Plan

```bash
bv a3 plan \
  --client "Acme Corp" \
  --evidence analysis.md \
  --output plan_30_60_90.md
```

#### Resume WP1 After Review

```bash
bv a3 resume \
  --engagement "WP1-ACME-001" \
  --response approve
```

### A6 Delivery PM/QA

#### QA Review a Deliverable

```bash
bv a6 qa report.md \
  --type wp1_report \
  --output qa_feedback.md
```

#### Generate Complete Proposal Package

```bash
bv a6 proposal \
  --client "Acme Corp" \
  --brief opportunity_brief.json \
  --output ./proposal/
```

#### Generate Statement of Work

```bash
bv a6 sow \
  --client "Acme Corp" \
  --brief brief.json \
  --output sow_acme.md
```

#### Estimate Effort

```bash
bv a6 estimate \
  --client "Acme Corp" \
  --wp wp1 \
  --users 500 \
  --output estimate.md
```

#### Create Project Plan

```bash
bv a6 plan \
  --client "Acme Corp" \
  --engagement "ENG-ACME-001" \
  --wp wp1 \
  --output project_plan.md
```

#### Resume Proposal After Pricing Review

```bash
bv a6 resume \
  --engagement "PROP-ACME-001" \
  --response approve
```

### A4 Governance Lead - WP4 Governance

#### Execute Full WP4 Governance Office-in-a-Box

```bash
bv a4 wp4 \
  --client "Acme Corp" \
  --engagement "WP4-ACME-001" \
  --wp1 wp1_findings.json \
  --output ./wp4_output/
```

#### Define Operating Model

```bash
bv a4 operating-model \
  --client "Acme Corp" \
  --output operating_model.md
```

#### Create Governance Policies

```bash
bv a4 policies \
  --client "Acme Corp" \
  --output policies.md
```

#### Build Standards Library

```bash
bv a4 standards \
  --client "Acme Corp" \
  --output standards.md
```

#### Create Admin Runbooks

```bash
bv a4 runbooks \
  --client "Acme Corp" \
  --output runbooks.md
```

#### Define KPIs and Metrics

```bash
bv a4 kpis \
  --client "Acme Corp" \
  --output kpis.md
```

#### Resume WP4 After Review

```bash
bv a4 resume \
  --engagement "WP4-ACME-001" \
  --response approve
```

#### Interactive Chat

```bash
bv chat --agent a1
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        ORCHESTRATOR                              │
│                    LangGraph + Python                           │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
   ┌─────────┐          ┌─────────┐          ┌─────────┐
   │ Claude  │          │ Claude  │          │  Local  │
   │  Opus   │          │ Sonnet  │          │ (Ollama)│
   └─────────┘          └─────────┘          └─────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         MEMORY                                   │
│              PostgreSQL + pgvector + Redis                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     TOOLS (MCP)                                  │
│      Atlassian │ Google │ LinkedIn │ FileSystem                  │
└─────────────────────────────────────────────────────────────────┘
```

## Project Structure

```
bluevektor-agents/
├── core/                    # Core infrastructure
│   ├── config.py           # Configuration management
│   ├── llm.py              # LLM routing (Claude, Ollama)
│   ├── memory.py           # PostgreSQL + Redis memory
│   └── orchestrator.py     # LangGraph orchestration
│
├── agents/                  # Agent implementations
│   ├── base.py             # Base agent class
│   ├── a1_gtm.py           # GTM & Partnerships
│   └── ...                 # Other agents
│
├── workflows/               # LangGraph workflows
│   └── lead_qualification.py
│
├── knowledge/               # RAG knowledge base
│   ├── templates/
│   ├── playbooks/
│   └── checklists/
│
├── api/                     # FastAPI endpoints
├── cli/                     # Typer CLI
└── tests/                   # Test suite
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `ANTHROPIC_API_KEY` | Anthropic API key | Yes |
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `REDIS_URL` | Redis connection string | Yes |
| `DEFAULT_MODEL` | Default Claude model | No |
| `REASONING_MODEL` | Model for complex tasks | No |
| `FAST_MODEL` | Model for simple tasks | No |

### Model Tiers

| Tier | Model | Use Case |
|------|-------|----------|
| `reasoning` | claude-opus-4-20250514 | Strategy, complex analysis |
| `standard` | claude-sonnet-4-20250514 | General tasks |
| `fast` | claude-haiku-3-20240307 | High-volume, simple tasks |
| `local` | llama3.2 (Ollama) | Cost-sensitive tasks |

## Development

### Running Tests

```bash
pytest tests/ -v
```

### Code Quality

```bash
# Linting
ruff check .

# Type checking
mypy .

# Format
ruff format .
```

### Adding a New Agent

1. Create `agents/a{N}_{name}.py`
2. Extend `BaseAgent`
3. Implement `system_prompt()` and `run()`
4. Define state schema if needed
5. Register in `agents/__init__.py`

## Workflows

### Lead Qualification (A1)

```
intake → enrich → analyze_triggers → qualify →
[qualified?] → determine_action →
[high score] → human_review → prepare_outreach → END
[medium] → prepare_outreach → END
[low] → archive → END
```

### WP1 Diagnostic (A3)

```
initialize → collect_evidence → analyze_volumetrics → analyze_apps →
identify_hotspots → generate_plan → draft_report →
internal_review → [approved] → finalize_deliverables → complete → END
              → [revise] → draft_report (loop)
              → [reject] → END
```

**WP1 Deliverables:**
- Evidence collection plan
- Volumetrics analysis
- App inventory (CSK 4R)
- Hotspot heatmap
- 30/60/90 transformation plan
- Executive report
- Presentation outline

### WP4 Governance (A4)

```
initialize → define_operating_model → create_policies → build_standards →
design_app_governance → define_kpis → create_runbooks → compile_handbook →
internal_review → [approved] → finalize_deliverables → complete → END
              → [revise] → compile_handbook (loop)
```

**WP4 Deliverables:**
- Operating model (roles, RACI, committees)
- Governance policies (7 core policies)
- Standards library (workflows, fields, SLAs)
- App governance framework
- KPI dashboard
- Admin runbooks (10+ runbooks)
- Implementation roadmap
- WP4 Handbook (complete deliverable)

### Proposal Generation (A6)

```
validate → estimate_effort → generate_one_pager → generate_sow →
qa_review → [passed] → human_pricing_review →
[approved] → finalize → END
[adjust] → estimate_effort (loop)
```

**Proposal Deliverables:**
- Effort estimate
- One-pager (executive summary)
- Statement of Work (SoW)
- Cover letter
- QA report

### Human-in-the-Loop

Certain artifacts require human approval:
- Opportunity briefs
- Proposals
- Client deliverables

The system pauses and can notify via webhook (Slack, email, etc.).

## API Endpoints

When running with `docker-compose --profile app up`:

- `GET /health` - Health check
- `GET /agents` - List agents
- `POST /agents/{id}/run` - Run agent task
- `POST /workflows/{id}/run` - Execute workflow
- `POST /workflows/{id}/resume` - Resume paused workflow

## Roadmap

- [x] Core infrastructure (LLM, Memory, Orchestrator)
- [x] A1 GTM Agent
- [x] Lead Qualification Workflow
- [x] A3 Assessment Analyst Agent
- [x] WP1 Diagnostic Workflow
- [x] A4 Governance Lead Agent
- [x] WP4 Governance Workflow
- [x] A6 Delivery PM/QA Agent
- [x] Proposal Generation Workflow
- [x] CLI Interface
- [ ] MCP Tool Integration (Atlassian, Google)
- [ ] Web Dashboard
- [ ] A2, A5, A7 Agents
- [ ] A0 Strategic Agent

## License

Proprietary - BlueVektor © 2025

## Support

- Email: hello@bluevektor.com
- Web: https://bluevektor.com
