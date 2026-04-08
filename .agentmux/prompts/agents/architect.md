- Prefer extracting repeated prompt instructions into shared fragments/helpers instead of duplicating them across multiple prompt templates.
- Avoid centralized if/else or switch chains for role/phase-specific behavior. Use declarative registries, dispatch tables, or per-role modules so each role/phase owns its own logic.

- The `agentmux-research` MCP server is a pure signal channel: all tools (dispatch AND submission) validate inputs, append to `tool_events.jsonl`, and return confirmation — no file I/O. Side-effects (artifact writes, task dispatch) belong in the orchestrator handler layer, not in MCP tools.
