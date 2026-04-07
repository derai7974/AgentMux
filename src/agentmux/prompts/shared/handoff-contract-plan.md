## Submitting Your Execution Plan

Use the MCP tools to submit your execution plan. This ensures structured, validated output.

### Step 1: Submit sub-plans

For each sub-plan, call `agentmux_submit_subplan` with:
- `index` (required) — Sub-plan number (1, 2, 3, ...)
- `title` (required) — Short descriptive title
- `scope` (required) — What this sub-plan covers
- `owned_files` (required) — Files created or modified (for parallel isolation)
- `dependencies` (required) — What this sub-plan depends on
- `implementation_approach` (required) — Step-by-step approach
- `acceptance_criteria` (required) — Testable criteria for completion
- `tasks` (required) — Task checklist items
- `isolation_rationale` (optional) — Why this sub-plan is safe for parallel execution

### Step 2: Submit the execution plan

Call `agentmux_submit_execution_plan` with:
- `groups` (required) — Execution groups: `[{group_id, mode: "serial"|"parallel", plans: [{file, name}]}]`
- `review_strategy` (required) — `{severity: "low"|"medium"|"high", focus: [...]}`
- `needs_design` (required) — Whether a design phase is required
- `needs_docs` (required) — Whether documentation updates are needed
- `doc_files` (required) — Documentation files to create or update
- `plan_overview` (required) — Human-readable plan summary

The tools validate input and write the corresponding `.yaml` and `.md` files.

**If MCP tools are unavailable**, write `02_planning/execution_plan.yaml` directly:

```yaml
version: 1
review_strategy:
  severity: medium
  focus: [security, performance]
needs_design: false
needs_docs: true
doc_files: [docs/api.md]
groups:
  - group_id: core-setup
    mode: serial
    plans:
      - file: plan_1.md
        name: Setup core module
```

And write each `02_planning/plan_N.yaml`:

```yaml
index: 1
title: Plan title
scope: What it covers
owned_files: [src/file.py]
dependencies: None
implementation_approach: |
  Step-by-step approach.
acceptance_criteria: |
  Testable criteria.
tasks:
  - First task
  - Second task
```

Then write the corresponding `.md` and `tasks_N.md` files as human-readable versions.
