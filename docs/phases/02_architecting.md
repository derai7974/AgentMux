# Phase: Architecting

> Related source files: `src/agentmux/workflow/handlers/architecting.py`, `src/agentmux/workflow/phase_registry.py`, `src/agentmux/workflow/prompts.py`, `src/agentmux/integrations/mcp_server.py`

> Directory: `02_architecting/` | Optional: no
> Research directory: `03_research/` | Optional: on-demand

The architect produces a technical architecture document describing *what* will be built and *with what* tools/libraries. It may also spawn research tasks (code or web) before submitting.

## Artifacts

| File | Writer | Reader | Format |
|------|--------|--------|--------|
| `architect_prompt.md` | orchestrator | architect agent | Markdown prompt |
| `changes_prompt.md` | orchestrator | architect agent (on replanning) | Markdown |
| `architecture.md` | architect agent (via `submit_architecture`) | planner (via prompt injection) | Markdown |

## Research (`03_research/`)

Research tasks are spawned on-demand by the architect during the architecting phase. Each task gets its own subdirectory.

| File | Writer | Reader | Format |
|------|--------|--------|--------|
| `code-<topic>/request.md` | architect agent | code-researcher agent | Markdown |
| `code-<topic>/prompt.md` | orchestrator | code-researcher agent | Markdown prompt |
| `code-<topic>/summary.md` | code-researcher agent | architect, planner, coder (via prompt) | Markdown |
| `code-<topic>/detail.md` | code-researcher agent | architect, planner, coder (via prompt) | Markdown |
| `code-<topic>/done` | code-researcher agent | orchestrator | empty marker |
| `web-<topic>/request.md` | architect agent | web-researcher agent | Markdown |
| `web-<topic>/prompt.md` | orchestrator | web-researcher agent | Markdown prompt |
| `web-<topic>/summary.md` | web-researcher agent | architect, planner, coder (via prompt) | Markdown |
| `web-<topic>/detail.md` | web-researcher agent | architect, planner, coder (via prompt) | Markdown |
| `web-<topic>/done` | web-researcher agent | orchestrator | empty marker |

Research results are injected into the next architect/planner/coder prompt via the `research_handoff` placeholder.

## Transitions

| From | Event | To |
|------|-------|----|
| `product_management` or pipeline start | — | `architecting` |
| `completing` | `changes_requested` | `architecting` (re-planning) |
| `architecting` | `architecture_written` (on `architecture.md` submitted) | `planning` |
