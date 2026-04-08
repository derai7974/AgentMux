"""Event-driven handler for planning phase.

The planning phase is where the planner creates execution plans based on
the architecture document produced by the architect in the architecting phase.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from agentmux.workflow.event_catalog import EVENT_CHANGES_REQUESTED, EVENT_PLAN_WRITTEN
from agentmux.workflow.event_router import (
    EventSpec,
    ToolSpec,
    WorkflowEvent,
)
from agentmux.workflow.execution_plan import load_execution_plan
from agentmux.workflow.handoff_artifacts import (
    submit_execution_plan,
    submit_subplan,
)
from agentmux.workflow.phase_helpers import (
    apply_role_preferences,
    dispatch_research_task,
    load_plan_meta,
    notify_research_complete,
    send_to_role,
)
from agentmux.workflow.prompts import (
    build_change_prompt,
    build_planner_prompt,
    write_prompt_file,
)

if TYPE_CHECKING:
    from agentmux.workflow.transitions import PipelineContext


class PlanningHandler:
    """Event-driven handler for planning phase.

    The planner receives the architecture document and creates execution plans.
    """

    def get_event_specs(self) -> Sequence[EventSpec]:
        return ()

    def get_tool_specs(self) -> Sequence[ToolSpec]:
        return (
            ToolSpec(name="execution_plan", tool_names=("submit_execution_plan",)),
            ToolSpec(name="subplan", tool_names=("submit_subplan",)),
            ToolSpec(
                name="research_code_req",
                tool_names=("research_dispatch_code",),
            ),
            ToolSpec(
                name="research_web_req",
                tool_names=("research_dispatch_web",),
            ),
            ToolSpec(
                name="research_done",
                tool_names=("submit_research_done",),
            ),
        )

    def enter(self, state: dict, ctx: PipelineContext) -> dict:
        """Called when entering planning phase.

        Sends planner prompt (initial or changes).
        """
        is_replan = (
            state.get("last_event") == EVENT_CHANGES_REQUESTED
            and ctx.files.changes.exists()
        )
        prompt_file = write_prompt_file(
            ctx.files.feature_dir,
            ctx.files.relative_path(
                ctx.files.planning_dir
                / ("changes_prompt.txt" if is_replan else "planner_prompt.md")
            ),
            build_change_prompt(ctx.files, ctx.agents.get("planner"))
            if is_replan
            else build_planner_prompt(ctx.files, ctx.agents.get("planner")),
        )
        send_to_role(ctx, "planner", prompt_file)
        return {}

    def handle_event(
        self,
        event: WorkflowEvent,
        state: dict,
        ctx: PipelineContext,
    ) -> tuple[dict, str | None]:
        """Handle events for planning phase."""
        match event.kind:
            case "execution_plan":
                return self._handle_execution_plan(event, state, ctx)
            case "subplan":
                return self._handle_subplan(event, state, ctx)
            case "research_code_req":
                return self._handle_research_code_req(event, state, ctx)
            case "research_web_req":
                return self._handle_research_web_req(event, state, ctx)
            case "research_done":
                return self._handle_research_done(event, state, ctx)
            case _:
                return {}, None

    def _handle_execution_plan(
        self,
        event: WorkflowEvent,
        state: dict,
        ctx: PipelineContext,
    ) -> tuple[dict, str | None]:
        """Handle execution plan submission via tool event."""
        payload = event.payload.get("payload", {})

        # Write execution plan artifacts (idempotent — guard by existence)
        yaml_path = ctx.files.planning_dir / "execution_plan.yaml"
        wrote_plan = not yaml_path.exists()
        if wrote_plan:
            submit_execution_plan(ctx.files.feature_dir, payload)

        # Apply approved preferences from planner
        apply_role_preferences(ctx, "planner")

        # Validate only what we just wrote — skip on replay (existing file may differ)
        if wrote_plan and yaml_path.exists():
            load_execution_plan(ctx.files.planning_dir)
        meta = load_plan_meta(ctx.files.planning_dir)
        needs_design = bool(meta.get("needs_design")) and "designer" in ctx.agents

        # Delete changes.md if exists
        if ctx.files.changes.exists():
            ctx.files.changes.unlink()

        # Deactivate and kill planner - their work is done
        ctx.runtime.deactivate("planner")
        ctx.runtime.kill_primary("planner")

        # Determine next phase
        next_phase = "designing" if needs_design else "implementing"
        return {"last_event": EVENT_PLAN_WRITTEN}, next_phase

    def _handle_subplan(
        self,
        event: WorkflowEvent,
        state: dict,
        ctx: PipelineContext,
    ) -> tuple[dict, str | None]:
        """Handle subplan submission via tool event."""
        payload = event.payload.get("payload", {})
        index = payload.get("index")
        if index is None:
            return {"error": "missing subplan index"}, None

        # Write subplan artifacts (idempotent — guard by existence)
        yaml_path = ctx.files.planning_dir / f"plan_{index}.yaml"
        if not yaml_path.exists():
            submit_subplan(ctx.files.feature_dir, payload)

        return {}, None

    def _handle_research_code_req(
        self,
        event: WorkflowEvent,
        state: dict,
        ctx: PipelineContext,
    ) -> tuple[dict, str | None]:
        """Handle code research request via tool event."""
        payload = event.payload.get("payload", {})
        topic = payload.get("topic", "")
        if not topic:
            return {}, None

        # Write request.md before dispatching (side-effect ordering requirement)
        req_dir = ctx.files.research_dir / f"code-{topic}"
        req_dir.mkdir(parents=True, exist_ok=True)
        req_path = req_dir / "request.md"
        if not req_path.exists():
            questions = payload.get("questions", [])
            scope_hints = payload.get("scope_hints", [])
            content = (
                f"# Research Request: {topic}\n\n"
                f"## Context\n{payload.get('context', '')}\n\n"
                f"## Questions\n"
                + "\n".join(f"- {q}" for q in questions)
                + (
                    "\n\n## Scope Hints\n" + "\n".join(f"- {h}" for h in scope_hints)
                    if scope_hints
                    else ""
                )
            )
            req_path.write_text(content, encoding="utf-8")

        return dispatch_research_task("code-researcher", topic, state, ctx)

    def _handle_research_web_req(
        self,
        event: WorkflowEvent,
        state: dict,
        ctx: PipelineContext,
    ) -> tuple[dict, str | None]:
        """Handle web research request via tool event."""
        payload = event.payload.get("payload", {})
        topic = payload.get("topic", "")
        if not topic:
            return {}, None

        # Write request.md before dispatching (side-effect ordering requirement)
        req_dir = ctx.files.research_dir / f"web-{topic}"
        req_dir.mkdir(parents=True, exist_ok=True)
        req_path = req_dir / "request.md"
        if not req_path.exists():
            questions = payload.get("questions", [])
            scope_hints = payload.get("scope_hints", [])
            content = (
                f"# Research Request: {topic}\n\n"
                f"## Context\n{payload.get('context', '')}\n\n"
                f"## Questions\n"
                + "\n".join(f"- {q}" for q in questions)
                + (
                    "\n\n## Scope Hints\n" + "\n".join(f"- {h}" for h in scope_hints)
                    if scope_hints
                    else ""
                )
            )
            req_path.write_text(content, encoding="utf-8")

        return dispatch_research_task("web-researcher", topic, state, ctx)

    def _handle_research_done(
        self,
        event: WorkflowEvent,
        state: dict,
        ctx: PipelineContext,
    ) -> tuple[dict, str | None]:
        """Handle research completion via tool event."""
        payload = event.payload.get("payload", {})
        topic = payload.get("topic", "")
        role_type = payload.get("role_type", "")  # "code" or "web"
        if not topic or not role_type:
            return {}, None

        role = "code-researcher" if role_type == "code" else "web-researcher"
        return notify_research_complete(role, topic, state, ctx, "planner")
