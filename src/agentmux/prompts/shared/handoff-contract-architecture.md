## Submitting Your Architecture

Write `02_planning/architecture.md` as a Markdown document describing your technical design, then call `submit_architecture()` to signal completion.

The document is free-form Markdown — include whatever sections are appropriate (Solution Overview, Components, Interfaces, Data Models, Technology Choices, Risks, etc.). The orchestrator reads it directly and advances the workflow.

After writing the file, call `submit_architecture()` (no arguments needed). The tool verifies the file is non-empty and signals the orchestrator that the architecture event has occurred. If the file is missing or empty, it returns an error so you can correct it.
