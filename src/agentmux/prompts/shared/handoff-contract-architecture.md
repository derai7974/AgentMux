## Submitting Your Architecture

Write `02_planning/architecture.yaml` with the fields below, then call `submit_architecture()` to validate your file and signal completion. The orchestrator materializes `architecture.md` automatically if you do not write it.

```yaml
solution_overview: |
  High-level approach description.
components:
  - name: ComponentName
    responsibility: What it does
    interfaces:
      - method_or_endpoint()
interfaces_and_contracts: |
  API boundaries and data formats.
data_models: |
  Key entities and relationships.
cross_cutting_concerns: |
  Error handling, logging, security.
technology_choices: |
  Tools and libraries with rationale.
risks_and_mitigations: |
  Known risks and mitigations.
design_handoff: |  # optional
  Notes for designer.
approved_preferences:  # optional — same shape as approved_preferences.json
  source_role: architect
  approved:
    - target_role: coder
      bullet: "- Prefer typed helpers"
```

After writing the file, call `submit_architecture()` (no arguments needed). The tool validates your YAML and signals the orchestrator to advance the workflow. If validation fails, it returns an error so you can correct the file.
