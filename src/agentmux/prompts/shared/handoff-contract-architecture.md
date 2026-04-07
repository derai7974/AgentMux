## Submitting Your Architecture

Use the `agentmux_submit_architecture` MCP tool to submit your architecture document. This ensures structured, validated output.

**Tool parameters:**
- `solution_overview` (required) — High-level approach and rationale
- `components` (required) — List of components, each with `name`, `responsibility`, and `interfaces`
- `interfaces_and_contracts` (required) — API boundaries, data formats, protocols
- `data_models` (required) — Key entities, relationships, storage
- `cross_cutting_concerns` (required) — Error handling, logging, security, testing strategy
- `technology_choices` (required) — Tools, libraries, frameworks with rationale
- `risks_and_mitigations` (required) — Known risks and mitigation strategies
- `design_handoff` (optional) — Notes for the designer if UI work is needed

The tool validates your input and writes `architecture.yaml` + `architecture.md` to the planning directory.

**If the MCP tool is unavailable**, write `02_planning/architecture.yaml` directly:

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
```

Then write `02_planning/architecture.md` as a human-readable version of the same content.
