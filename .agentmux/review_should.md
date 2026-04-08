
# Refactoring - Should be

Diese Aspekte sollten von der Implementierung umgesetzt worden sein

- Toolcall als eigenes event (statt file events), auf das der Orchestrator hört
- Orchestrator schreibt md Dateien (wie vorher) in das session verzeichnis
- Die Dateien die vom entsprechenden Agent zwingend benötigt werden, werden (wie vorher) direkt in das Prompt eingebettet
- MCP Tools haben eine saubere Abstraktion (MCP Tool), die von konkretem provider implementiert wird (copilot mcp aktivierung sieht anders aus als bei gemini zb)
- Wir müssen eine hybride Lösung wählen: Agents schreiben die Dateien, Tool Call gibt signal dass der agent fertig ist und welche Dateien er geschrieben hat + Metadaten (z.b. ausführungsplan)
- wenn wir schon einen agentmux namespace für die tools haben brauchen wir keinen 'agentmux_'
- Alle "done-signale" müssen über ein entsprechendes Tool laufen

Outlined Plan: 

│ Refactoring Plan: Handoff Contracts — Should-Be Architecture                                                                        │
│                                                                                                                                     │
│ Approach: Implement the hybrid model where agents write files themselves AND call MCP tools to signal completion. Tool calls become │
│ first-class tool.* events — not file events.                                                                                        │
│                                                                                                                                     │
│ 4 Steps (largely sequential, Step 4 independent):                                                                                   │
│                                                                                                                                     │
│ Step 1 — Tool Call Event Channel (infrastructure only)                                                                              │
│                                                                                                                                     │
│  - Add tool_events.jsonl append-only log to session dir                                                                             │
│  - New ToolCallEventSource (watchdog-backed) emitting tool.<name> events                                                            │
│  - Wire into EventBus + WorkflowEventRouter                                                                                         │
│  - MCP tools append to this log instead of relying on file detection                                                                │
│                                                                                                                                     │
│ Step 2 — Migrate Handlers to Tool Events + Move File Writing                                                                        │
│                                                                                                                                     │
│  - ArchitectingHandler, PlanningHandler, ReviewingHandler: replace file EventSpecs with tool call events (tool.submit_architecture  │
│ etc.)                                                                                                                               │
│  - Move file-writing (architecture.md, plan.md, review.md) from MCP tools → orchestrator handlers                                   │
│  - MCP tools become pure: validate → append to event log → return confirmation                                                      │
│                                                                                                                                     │
│ Step 3 — Coder/Researcher Done Tools + Rename                                                                                       │
│                                                                                                                                     │
│  - New submit_done(subplan_index) tool for coders                                                                                   │
│  - New submit_research_done(topic, type) tool for researchers                                                                       │
│  - Add coder/researcher roles to MCP access (DEFAULT_RESEARCH_ROLES)                                                                │
│  - Remove redundant agentmux_ prefix from all tool names                                                                            │
│  - Update all prompt templates                                                                                                      │
│                                                                                                                                     │
│ Step 4 — Copilot MCP Configurator (independent, can run parallel with 2-3)                                                          │
│                                                                                                                                     │
│  - Add CopilotConfigurator to integrations/mcp/configurators.py                                                                     │
│  - Wire into CONFIGURATORS dict so init + ensure_mcp_config auto-covers Copilot
