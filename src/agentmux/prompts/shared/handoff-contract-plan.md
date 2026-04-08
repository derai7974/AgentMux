## Submitting Your Execution Plan

Write the YAML files below, then call the signal tools. The orchestrator materializes `.md` companions automatically if you do not write them.

### Step 1: Write and submit each sub-plan

Write `02_planning/plan_N.yaml` for each sub-plan:

```yaml
index: 1
title: Short descriptive title
scope: What this sub-plan covers
owned_files:
  - src/auth.py
  - tests/test_auth.py
dependencies: None
implementation_approach: |
  Step-by-step approach.
acceptance_criteria: |
  Testable criteria for completion.
tasks:
  - First task
  - Second task
isolation_rationale: |  # optional
  Why this sub-plan is safe for parallel execution.
```

Then call `submit_subplan(index=N)` for each sub-plan. The tool validates your YAML and signals the orchestrator.

### Step 2: Write and submit the execution plan

Write `02_planning/execution_plan.yaml`:

```yaml
version: 1
review_strategy:
  severity: medium
  focus:
    - security
needs_design: false
needs_docs: true
doc_files:
  - docs/api.md
groups:
  - group_id: core-setup
    mode: serial
    plans:
      - file: plan_1.md
        name: Core setup
plan_overview: |
  # Implementation Plan

  Overview of all planned work.
approved_preferences:  # optional — same shape as approved_preferences.json
  source_role: planner
  approved:
    - target_role: coder
      bullet: "- Validate each task before done"
```

Then call `submit_execution_plan()` (no arguments needed). The tool validates your YAML and signals the orchestrator to advance the workflow. If validation fails, it returns an error so you can correct the file.
