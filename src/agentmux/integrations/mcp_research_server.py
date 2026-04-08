from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

from ..runtime.tool_events import append_tool_event

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:  # pragma: no cover - runtime dependency check
    FastMCP = None  # type: ignore[assignment]

TOPIC_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

mcp = FastMCP("agentmux-research") if FastMCP is not None else None


def _tool():
    if mcp is None:

        def decorate(func):
            return func

        return decorate
    return mcp.tool()


def _feature_dir(feature_dir: str | None = None) -> Path:
    raw = (feature_dir or os.environ.get("FEATURE_DIR", "")).strip()
    if not raw:
        raise RuntimeError("feature_dir is required.")
    path = Path(raw).expanduser()
    path = (Path.cwd() / path).resolve() if not path.is_absolute() else path.resolve()
    if not path.exists():
        raise RuntimeError(f"feature_dir does not exist: {path}")
    return path


def _log_path(feature_dir: str | None = None) -> Path:
    return _feature_dir(feature_dir) / "tool_events.jsonl"


def _validate_topic(topic: str) -> str:
    normalized = topic.strip()
    if not normalized or not TOPIC_PATTERN.fullmatch(normalized):
        raise ValueError(
            "topic must be a non-empty slug (lowercase alphanumeric and hyphens)."
        )
    return normalized


def _validate_questions(questions: list[str]) -> list[str]:
    cleaned = [
        question.strip() for question in questions if question and question.strip()
    ]
    if not cleaned:
        raise ValueError("questions must contain at least one non-empty question.")
    return cleaned


def _normalize_scope_hints(scope_hints: str | list[str] | None) -> list[str] | None:
    if scope_hints is None:
        return None
    if isinstance(scope_hints, str):
        cleaned = scope_hints.strip()
        return [cleaned] if cleaned else None
    cleaned = [hint.strip() for hint in scope_hints if hint and hint.strip()]
    return cleaned or None


def _validate_or_raise(contract_name: str, data: dict[str, Any]) -> None:
    """Validate data against the contract for the given name.

    Raises ValueError with details if validation fails.
    """
    from ..workflow.handoff_contracts import ValidationError, validate_submission

    try:
        errors = validate_submission(contract_name, data)
    except ValidationError as exc:
        raise ValueError(str(exc)) from exc
    if errors:
        raise ValueError("; ".join(errors))


# ---------------------------------------------------------------------------
# Research dispatch tools
# ---------------------------------------------------------------------------


@_tool()
def research_dispatch_code(
    topic: str,
    context: str,
    questions: list[str],
    feature_dir: str | None = None,
    scope_hints: str | list[str] | None = None,
) -> str:
    """Dispatch a code-research task."""
    normalized_topic = _validate_topic(topic)
    normalized_questions = _validate_questions(questions)
    normalized_scope_hints = _normalize_scope_hints(scope_hints)
    payload = {
        "topic": normalized_topic,
        "context": context.strip(),
        "questions": normalized_questions,
        "scope_hints": normalized_scope_hints,
        "research_type": "code",
    }
    append_tool_event(_log_path(feature_dir), "research_dispatch_code", payload)
    return f"Code research on '{normalized_topic}' dispatched."


@_tool()
def research_dispatch_web(
    topic: str,
    context: str,
    questions: list[str],
    feature_dir: str | None = None,
    scope_hints: str | list[str] | None = None,
) -> str:
    """Dispatch a web-research task."""
    normalized_topic = _validate_topic(topic)
    normalized_questions = _validate_questions(questions)
    normalized_scope_hints = _normalize_scope_hints(scope_hints)
    payload = {
        "topic": normalized_topic,
        "context": context.strip(),
        "questions": normalized_questions,
        "scope_hints": normalized_scope_hints,
        "research_type": "web",
    }
    append_tool_event(_log_path(feature_dir), "research_dispatch_web", payload)
    return f"Web research on '{normalized_topic}' dispatched."


# ---------------------------------------------------------------------------
# Submission tools
# ---------------------------------------------------------------------------


@_tool()
def submit_architecture(
    solution_overview: str,
    components: list[dict[str, Any]],
    interfaces_and_contracts: str,
    data_models: str,
    cross_cutting_concerns: str,
    technology_choices: str,
    risks_and_mitigations: str,
    feature_dir: str | None = None,
    design_handoff: str | None = None,
) -> str:
    """Submit architecture document.

    Validates input and appends to tool_events.jsonl.
    """
    data: dict[str, Any] = {
        "solution_overview": solution_overview,
        "components": components,
        "interfaces_and_contracts": interfaces_and_contracts,
        "data_models": data_models,
        "cross_cutting_concerns": cross_cutting_concerns,
        "technology_choices": technology_choices,
        "risks_and_mitigations": risks_and_mitigations,
    }
    if design_handoff is not None:
        data["design_handoff"] = design_handoff

    _validate_or_raise("architecture", data)
    append_tool_event(_log_path(feature_dir), "submit_architecture", data)
    return "Architecture submitted."


@_tool()
def submit_execution_plan(
    groups: list[dict[str, Any]],
    review_strategy: dict[str, Any],
    needs_design: bool,
    needs_docs: bool,
    doc_files: list[str],
    plan_overview: str,
    feature_dir: str | None = None,
) -> str:
    """Submit the execution plan. Validates and appends to tool_events.jsonl."""
    data: dict[str, Any] = {
        "groups": groups,
        "review_strategy": review_strategy,
        "needs_design": needs_design,
        "needs_docs": needs_docs,
        "doc_files": doc_files,
        "plan_overview": plan_overview,
    }

    _validate_or_raise("execution_plan", data)
    append_tool_event(_log_path(feature_dir), "submit_execution_plan", data)
    return "Execution plan submitted."


@_tool()
def submit_subplan(
    index: int,
    title: str,
    scope: str,
    owned_files: list[str],
    dependencies: str,
    implementation_approach: str,
    acceptance_criteria: str,
    tasks: list[str],
    feature_dir: str | None = None,
    isolation_rationale: str | None = None,
) -> str:
    """Submit a sub-plan. Validates and appends to tool_events.jsonl."""
    data: dict[str, Any] = {
        "index": index,
        "title": title,
        "scope": scope,
        "owned_files": owned_files,
        "dependencies": dependencies,
        "implementation_approach": implementation_approach,
        "acceptance_criteria": acceptance_criteria,
        "tasks": tasks,
    }
    if isolation_rationale is not None:
        data["isolation_rationale"] = isolation_rationale

    _validate_or_raise("subplan", data)
    append_tool_event(_log_path(feature_dir), "submit_subplan", data)
    return f"Sub-plan {index} submitted."


@_tool()
def submit_review(
    verdict: str,
    summary: str,
    feature_dir: str | None = None,
    findings: list[dict[str, Any]] | None = None,
    commit_message: str | None = None,
) -> str:
    """Submit a code review. Validates and appends to tool_events.jsonl."""
    data: dict[str, Any] = {
        "verdict": verdict,
        "summary": summary,
    }
    if findings is not None:
        data["findings"] = findings
    if commit_message is not None:
        data["commit_message"] = commit_message

    _validate_or_raise("review", data)
    append_tool_event(_log_path(feature_dir), "submit_review", data)
    return f"Review submitted (verdict: {verdict})."


# ---------------------------------------------------------------------------
# Completion-signal tools
# ---------------------------------------------------------------------------


@_tool()
def submit_done(
    subplan_index: int,
    feature_dir: str | None = None,
) -> str:
    """Mark a sub-plan as done."""
    if not isinstance(subplan_index, int) or subplan_index < 1:
        raise ValueError("subplan_index must be an integer >= 1.")
    append_tool_event(
        _log_path(feature_dir), "submit_done", {"subplan_index": subplan_index}
    )
    return f"Sub-plan {subplan_index} marked done."


@_tool()
def submit_research_done(
    topic: str,
    type: str,
    feature_dir: str | None = None,
) -> str:
    """Mark a research task as done."""
    normalized = _validate_topic(topic)
    if type not in ("code", "web"):
        raise ValueError("type must be 'code' or 'web'.")
    append_tool_event(
        _log_path(feature_dir),
        "submit_research_done",
        {"topic": normalized, "type": type, "role_type": type},
    )
    return f"Research on '{normalized}' ({type}) marked done."


@_tool()
def submit_pm_done(
    feature_dir: str | None = None,
) -> str:
    """Mark the product management phase as done."""
    append_tool_event(_log_path(feature_dir), "submit_pm_done", {})
    return "Product management phase done."


if __name__ == "__main__":
    if mcp is None:
        raise SystemExit(
            "Missing dependency: mcp. "
            "Install with `python3 -m pip install -r requirements.txt`."
        )
    mcp.run()
