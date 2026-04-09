# Phase: Completion

> Directory: `08_completion/` | Optional: no

The reviewer writes a human-readable summary of the implementation. The pipeline then awaits user approval or a change request via the native completion UI.

## Artifacts

| File | Writer | Reader | Format |
|------|--------|--------|--------|
| `summary_prompt.md` | orchestrator | reviewer agent | Markdown prompt |
| `summary.md` | reviewer agent | PR description, humans | Markdown |
| `approval.json` | completion UI (user approves) | orchestrator | JSON |
| `changes.md` | completion UI (user requests changes) | orchestrator | Markdown |
| `approved_preferences.json` | reviewer agent (optional, via `approved_preferences` in `review.yaml`) | subsequent planner/coder prompts | JSON |

## Transitions

| From | Event | To |
|------|-------|----|
| `reviewing` (pass or loop cap) | `review_passed` / `review_failed` | `completing` |
| `completing` | `approval_received` (on `approval.json`) | `done` (pipeline ends) |
| `completing` | `changes_requested` (on `changes.md`) | `architecting` (re-planning) |

## Notes

- When the user approves, the pipeline commits changes locally and optionally opens a PR if `gh` is available and configured.
- When the user requests changes, the architect receives a re-planning prompt with the change description from `changes.md`.
- `approved_preferences.json` written here is injected into future planner and coder prompts for preference continuity across re-planning loops.
