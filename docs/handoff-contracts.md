# Handoff Contracts

> Related source files: `agentmux/workflow/handoff_contracts.py`, `agentmux/workflow/handoff_artifacts.py`, `agentmux/integrations/mcp_research_server.py`, `agentmux/prompts/shared/handoff-contract-architecture.md`, `agentmux/prompts/shared/handoff-contract-plan.md`, `agentmux/prompts/shared/handoff-contract-review.md`

Handoff contracts define the structured interface between workflow phases. Each contract specifies the fields an agent must produce, validates submissions, and writes dual output files (YAML canonical + MD human-readable).

## Overview

Agents submit phase outputs by writing the canonical `.yaml` file, then calling the MCP submission tool as a completion signal:

1. **Write the YAML file** — agent writes the canonical `.yaml` artifact (e.g., `02_planning/architecture.yaml`) directly. Shared prompt fragments (`[[shared:handoff-contract-*]]`) embedded in agent prompts provide the schema and examples.
2. **Call the MCP signal tool** — the `agentmux-research` MCP server exposes `submit_*` tools that read the agent-written file, validate it against the contract, append a minimal signal entry to `tool_events.jsonl`, and return a confirmation string (or a validation error the agent can act on). The tools write no files themselves.

The orchestrator observes the signal event, materializes `.md` companions from the YAML if not already present, and drives the state transition.

Completion semantics are phase-specific:

- **Architecture** — `architecture.yaml` is the canonical structured artifact, but the planner prompt still consumes `architecture.md`, so the companion Markdown file remains required in practice.
- **Execution plan + subplans** — `execution_plan.yaml` / `plan_N.yaml` are canonical structured artifacts, but `plan.md`, `plan_N.md`, and `tasks_N.md` remain required human-readable companions for downstream prompts and coder handoffs.
- **Review** — `review.yaml` is the canonical structured review artifact. If `review.md` is missing, AgentMux materializes it from `review.yaml` before summary/completion steps so downstream prompts can continue to read the Markdown companion.

## Contracts

### Architecture

- **MCP tool:** `submit_architecture`
- **Canonical file:** `02_planning/architecture.yaml`
- **Companion file:** `02_planning/architecture.md`
- **Required fields:** `solution_overview`, `components` (list of `{name, responsibility, interfaces}`), `interfaces_and_contracts`, `data_models`, `cross_cutting_concerns`, `technology_choices`, `risks_and_mitigations`
- **Optional fields:** `design_handoff`, `approved_preferences` (same shape as `approved_preferences.json`; materialized to `02_planning/approved_preferences.json`)

### Execution plan

- **MCP tool:** `submit_execution_plan`
- **Canonical file:** `02_planning/execution_plan.yaml`
- **Companion file:** `02_planning/plan.md`
- **Required fields:** `groups` (list of `{group_id, mode, plans: [{file, name}]}`), `review_strategy` (`{severity, focus}`), `needs_design`, `needs_docs`, `doc_files`, `plan_overview`
- **Optional fields:** `approved_preferences` (same shape as `approved_preferences.json`; materialized to `02_planning/approved_preferences.json`)

The YAML file merges the former `execution_plan.json` scheduling data and `plan_meta.json` workflow-intent metadata into a single file with a `version: 1` header.

### Subplan

- **MCP tool:** `submit_subplan`
- **Canonical file:** `02_planning/plan_N.yaml`
- **Companion files:** `02_planning/plan_N.md`, `02_planning/tasks_N.md`
- **Required fields:** `index`, `title`, `scope`, `owned_files`, `dependencies`, `implementation_approach`, `acceptance_criteria`, `tasks`
- **Optional fields:** `isolation_rationale`

Subplans are submitted individually before the execution plan. The `index` value determines the `N` in file names.

### Review

- **MCP tool:** `submit_review`
- **Canonical file:** `06_review/review.yaml`
- **Companion file:** `06_review/review.md`
- **Required fields:** `verdict` (`"pass"` or `"fail"`), `summary`
- **Conditional fields:** `findings` (required on `fail` — list of `{location, issue, severity, recommendation}`), `commit_message` (optional on `pass`)
- **Optional fields:** `approved_preferences` (same shape as `approved_preferences.json`; materialized to `08_completion/approved_preferences.json`)

## Validation

`validate_submission(contract_name, data)` in `handoff_contracts.py` performs:

1. **Required-field presence** — all required fields must be present
2. **Type checking** — loose type validation against field specs (`str`, `bool`, `int`, `list[str]`, `list[dict]`, `dict`)
3. **Allowed-value enforcement** — fields with constrained values (e.g., verdict: `pass`/`fail`) are validated
4. **Contract-specific rules:**
   - Architecture: each component must have `name` and `responsibility`
   - Execution plan: groups must be non-empty, unique `group_id`, valid `mode`, plans must have `file` and `name`
   - Subplan: `index` >= 1, non-empty `tasks` and `owned_files`
   - Review: `fail` verdict requires non-empty `findings` with `issue` and `recommendation`

MCP tools raise a validation error with all issues listed; agents receive the error message and can correct their submission.

## Dual-file output

Each handoff produces two files:

- **`.yaml`** — the machine-readable canonical artifact; written by the agent.
- **`.md`** — a human-readable companion; materialized automatically by the orchestrator from the YAML if the agent does not write it.

The `.md` companions are consumed by downstream prompts (plan.md by coder, architecture.md by planner, review.md by fix/summary prompts).

When the agent includes an optional `approved_preferences` mapping in the YAML, the orchestrator writes it to the phase-appropriate `approved_preferences.json` artifact so the existing preference-memory application flow can consume it unchanged.

## Shared prompt fragments

Three shared fragments provide agents with file-writing instructions and YAML schema examples:

| Fragment | Included by | Purpose |
|---|---|---|
| `handoff-contract-architecture.md` | `architect.md` | Architecture submission instructions |
| `handoff-contract-plan.md` | `planner.md`, `change.md` | Execution plan + subplan submission instructions |
| `handoff-contract-review.md` | `review_logic.md`, `review_quality.md`, `review_expert.md` | Review submission instructions |

These are inlined at template-load time via the `[[shared:fragment-name]]` syntax.
