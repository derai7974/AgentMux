"""Event-driven handler for product_management phase."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from agentmux.workflow.event_catalog import EVENT_PM_COMPLETED
from agentmux.workflow.event_router import (
    EventSpec,
    ToolSpec,
    WorkflowEvent,
)
from agentmux.workflow.phase_helpers import (
    handle_research_request,
    notify_research_complete,
    research_role_from_payload,
    send_to_role,
)
from agentmux.workflow.prompts import (
    build_product_manager_prompt,
    write_prompt_file,
)

if TYPE_CHECKING:
    from ..transitions import PipelineContext


class ProductManagementHandler:
    """Event-driven handler for product_management phase."""

    def enter(self, state: dict, ctx: PipelineContext) -> dict:
        """Called when entering product_management phase.

        Sends product-manager prompt.
        """
        prompt_file = write_prompt_file(
            ctx.files.feature_dir,
            ctx.files.relative_path(
                ctx.files.product_management_dir / "product_manager_prompt.md"
            ),
            build_product_manager_prompt(ctx.files, ctx.agents.get("product-manager")),
        )
        send_to_role(ctx, "product-manager", prompt_file)
        return {}  # No state updates

    def get_event_specs(self) -> Sequence[EventSpec]:
        return ()

    def get_tool_specs(self) -> Sequence[ToolSpec]:
        return (
            ToolSpec(name="pm_done", tool_names=("submit_pm_done",)),
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

    def handle_event(
        self,
        event: WorkflowEvent,
        state: dict,
        ctx: PipelineContext,
    ) -> tuple[dict, str | None]:
        """Handle events for product_management phase."""
        match event.kind:
            case "pm_done":
                return self._handle_pm_done(state, ctx)
            case "research_code_req":
                return self._handle_research_code_req(event, state, ctx)
            case "research_web_req":
                return self._handle_research_web_req(event, state, ctx)
            case "research_done":
                return self._handle_research_done(event, state, ctx)
            case _:
                return {}, None

    def _handle_pm_done(
        self,
        state: dict,
        ctx: PipelineContext,
    ) -> tuple[dict, str | None]:
        """Handle product management completion via tool event."""
        # Kill product-manager pane
        ctx.runtime.kill_primary("product-manager")

        # Transition to architecting
        return {"last_event": EVENT_PM_COMPLETED}, "architecting"

    def _handle_research_code_req(
        self,
        event: WorkflowEvent,
        state: dict,
        ctx: PipelineContext,
    ) -> tuple[dict, str | None]:
        """Handle code research request via tool event."""
        return handle_research_request("code-researcher", event, state, ctx)

    def _handle_research_web_req(
        self,
        event: WorkflowEvent,
        state: dict,
        ctx: PipelineContext,
    ) -> tuple[dict, str | None]:
        """Handle web research request via tool event."""
        return handle_research_request("web-researcher", event, state, ctx)

    def _handle_research_done(
        self,
        event: WorkflowEvent,
        state: dict,
        ctx: PipelineContext,
    ) -> tuple[dict, str | None]:
        """Handle research completion via tool event."""
        payload = event.payload.get("payload", {})
        topic = payload.get("topic", "")
        role = research_role_from_payload(payload)
        if not topic or role is None:
            return {}, None

        return notify_research_complete(role, topic, state, ctx, "product-manager")
