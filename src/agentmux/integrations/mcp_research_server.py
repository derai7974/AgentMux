from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import yaml

from ..shared.models import SESSION_DIR_NAMES
from ..workflow.handoff_contracts import validate_submission

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


def _research_dir(
    topic: str, research_type: str, feature_dir: str | None = None
) -> Path:
    return (
        _feature_dir(feature_dir)
        / SESSION_DIR_NAMES["research"]
        / f"{research_type}-{topic}"
    )


def _request_content(
    context: str, questions: list[str], scope_hints: list[str] | None
) -> str:
    lines = [
        "## Context",
        context.strip(),
        "",
        "## Questions",
    ]
    for index, question in enumerate(questions, start=1):
        lines.append(f"{index}. {question}")

    lines.extend(["", "## Scope hints"])
    if scope_hints:
        lines.extend(f"- {hint}" for hint in scope_hints)
    else:
        lines.append("- (none provided)")

    return "\n".join(lines).rstrip() + "\n"


def _dispatch(
    research_type: str,
    topic: str,
    context: str,
    questions: list[str],
    scope_hints: str | list[str] | None,
    feature_dir: str | None = None,
) -> str:
    normalized_topic = _validate_topic(topic)
    normalized_questions = _validate_questions(questions)
    normalized_scope_hints = _normalize_scope_hints(scope_hints)
    directory = _research_dir(normalized_topic, research_type, feature_dir)
    directory.mkdir(parents=True, exist_ok=True)

    request_path = directory / "request.md"
    request_path.write_text(
        _request_content(context, normalized_questions, normalized_scope_hints),
        encoding="utf-8",
    )

    label = "Code research" if research_type == "code" else "Web research"
    return f"{label} on '{normalized_topic}' dispatched."


def _result_content(topic: str, directory: Path, detail: bool) -> str:
    filename = "detail.md" if detail else "summary.md"
    target = directory / filename
    if not target.exists():
        return f"Research on '{topic}' completed but {filename} is missing."
    return target.read_text(encoding="utf-8")


@_tool()
def agentmux_research_dispatch_code(
    topic: str,
    context: str,
    questions: list[str],
    feature_dir: str | None = None,
    scope_hints: str | list[str] | None = None,
) -> str:
    return _dispatch("code", topic, context, questions, scope_hints, feature_dir)


@_tool()
def agentmux_research_dispatch_web(
    topic: str,
    context: str,
    questions: list[str],
    feature_dir: str | None = None,
    scope_hints: str | list[str] | None = None,
) -> str:
    return _dispatch("web", topic, context, questions, scope_hints, feature_dir)


# ---------------------------------------------------------------------------
# Handoff submission helpers
# ---------------------------------------------------------------------------


def _write_yaml(path: Path, data: dict[str, Any]) -> None:
    """Write data as YAML, creating parent directories."""
    path.parent.mkdir(parents=True, exist_ok=True)
    content = yaml.dump(data, default_flow_style=False, sort_keys=False)
    path.write_text(content, encoding="utf-8")


def _write_md(path: Path, content: str) -> None:
    """Write markdown content, creating parent directories."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _validate_or_raise(contract_name: str, data: dict[str, Any]) -> None:
    """Validate data against contract; raise on failure."""
    errors = validate_submission(contract_name, data)
    if errors:
        raise ValueError(
            f"Validation failed for '{contract_name}': " + "; ".join(errors)
        )


def _generate_architecture_md(data: dict[str, Any]) -> str:
    """Generate human-readable markdown from architecture data."""
    lines = ["# Architecture", ""]
    lines.extend(["## Solution Overview", "", data["solution_overview"].strip(), ""])

    lines.append("## Components")
    lines.append("")
    for comp in data["components"]:
        lines.append(f"### {comp['name']}")
        lines.append("")
        lines.append(f"**Responsibility:** {comp['responsibility']}")
        interfaces = comp.get("interfaces")
        if interfaces:
            lines.append("")
            lines.append("**Interfaces:**")
            for iface in interfaces:
                lines.append(f"- {iface}")
        lines.append("")

    for section, key in [
        ("Interfaces and Contracts", "interfaces_and_contracts"),
        ("Data Models", "data_models"),
        ("Cross-Cutting Concerns", "cross_cutting_concerns"),
        ("Technology Choices", "technology_choices"),
        ("Risks and Mitigations", "risks_and_mitigations"),
    ]:
        lines.extend([f"## {section}", "", data[key].strip(), ""])

    if data.get("design_handoff"):
        lines.extend(["## Design Handoff", "", data["design_handoff"].strip(), ""])

    return "\n".join(lines)


def _generate_plan_md(data: dict[str, Any]) -> str:
    """Generate plan.md from plan_overview content."""
    return data["plan_overview"].strip() + "\n"


def _generate_subplan_md(data: dict[str, Any]) -> str:
    """Generate plan_N.md from subplan data."""
    lines = [f"# {data['title']}", ""]
    lines.extend(["## Scope", "", data["scope"].strip(), ""])
    lines.extend(["## Owned Files", ""])
    for f in data["owned_files"]:
        lines.append(f"- `{f}`")
    lines.append("")
    lines.extend(["## Dependencies", "", data["dependencies"].strip(), ""])
    lines.extend(
        ["## Implementation Approach", "", data["implementation_approach"].strip(), ""]
    )
    lines.extend(
        ["## Acceptance Criteria", "", data["acceptance_criteria"].strip(), ""]
    )
    if data.get("isolation_rationale"):
        lines.extend(
            ["## Isolation Rationale", "", data["isolation_rationale"].strip(), ""]
        )
    return "\n".join(lines)


def _generate_tasks_md(data: dict[str, Any]) -> str:
    """Generate tasks_N.md checklist from subplan tasks."""
    lines = [f"# Tasks: {data['title']}", ""]
    for task in data["tasks"]:
        lines.append(f"- [ ] {task}")
    lines.append("")
    return "\n".join(lines)


def _generate_review_md(data: dict[str, Any]) -> str:
    """Generate review.md with verdict on first line for handler compat."""
    verdict = data["verdict"]
    lines = [f"verdict: {verdict}", ""]
    lines.extend(["## Summary", "", data["summary"].strip(), ""])

    if verdict == "fail" and data.get("findings"):
        lines.append("## Findings")
        lines.append("")
        for i, finding in enumerate(data["findings"], 1):
            lines.append(f"### Finding {i}")
            lines.append("")
            if finding.get("location"):
                lines.append(f"**Location:** `{finding['location']}`")
            lines.append(f"**Issue:** {finding['issue']}")
            if finding.get("severity"):
                lines.append(f"**Severity:** {finding['severity']}")
            lines.append(f"**Recommendation:** {finding['recommendation']}")
            lines.append("")

    if verdict == "pass" and data.get("commit_message"):
        lines.extend(
            ["## Suggested Commit Message", "", data["commit_message"].strip(), ""]
        )

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# MCP submission tools
# ---------------------------------------------------------------------------


@_tool()
def agentmux_submit_architecture(
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

    Validates input, writes architecture.yaml + architecture.md.
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

    fdir = _feature_dir(feature_dir)
    planning_dir = fdir / SESSION_DIR_NAMES["planning"]
    planning_dir.mkdir(parents=True, exist_ok=True)

    _write_yaml(planning_dir / "architecture.yaml", data)
    _write_md(planning_dir / "architecture.md", _generate_architecture_md(data))

    return "Architecture submitted. Files: architecture.yaml, architecture.md"


@_tool()
def agentmux_submit_execution_plan(
    groups: list[dict[str, Any]],
    review_strategy: dict[str, Any],
    needs_design: bool,
    needs_docs: bool,
    doc_files: list[str],
    plan_overview: str,
    feature_dir: str | None = None,
) -> str:
    """Submit the execution plan. Validates and writes execution_plan.yaml + plan.md."""
    data: dict[str, Any] = {
        "groups": groups,
        "review_strategy": review_strategy,
        "needs_design": needs_design,
        "needs_docs": needs_docs,
        "doc_files": doc_files,
        "plan_overview": plan_overview,
    }

    _validate_or_raise("execution_plan", data)

    fdir = _feature_dir(feature_dir)
    planning_dir = fdir / SESSION_DIR_NAMES["planning"]
    planning_dir.mkdir(parents=True, exist_ok=True)

    yaml_data = {
        "version": 1,
        "review_strategy": review_strategy,
        "needs_design": needs_design,
        "needs_docs": needs_docs,
        "doc_files": doc_files,
        "groups": groups,
    }
    _write_yaml(planning_dir / "execution_plan.yaml", yaml_data)
    _write_md(planning_dir / "plan.md", _generate_plan_md(data))

    return "Execution plan submitted. Files: execution_plan.yaml, plan.md"


@_tool()
def agentmux_submit_subplan(
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
    """Submit a sub-plan.

    Validates and writes plan_N.yaml, plan_N.md, tasks_N.md.
    """
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

    fdir = _feature_dir(feature_dir)
    planning_dir = fdir / SESSION_DIR_NAMES["planning"]
    planning_dir.mkdir(parents=True, exist_ok=True)

    _write_yaml(planning_dir / f"plan_{index}.yaml", data)
    _write_md(planning_dir / f"plan_{index}.md", _generate_subplan_md(data))
    _write_md(planning_dir / f"tasks_{index}.md", _generate_tasks_md(data))

    return (
        f"Sub-plan {index} submitted. "
        f"Files: plan_{index}.yaml, plan_{index}.md, tasks_{index}.md"
    )


@_tool()
def agentmux_submit_review(
    verdict: str,
    summary: str,
    feature_dir: str | None = None,
    findings: list[dict[str, Any]] | None = None,
    commit_message: str | None = None,
) -> str:
    """Submit a code review. Validates and writes review.yaml + review.md."""
    data: dict[str, Any] = {
        "verdict": verdict,
        "summary": summary,
    }
    if findings is not None:
        data["findings"] = findings
    if commit_message is not None:
        data["commit_message"] = commit_message

    _validate_or_raise("review", data)

    fdir = _feature_dir(feature_dir)
    review_dir = fdir / SESSION_DIR_NAMES["review"]
    review_dir.mkdir(parents=True, exist_ok=True)

    _write_yaml(review_dir / "review.yaml", data)
    _write_md(review_dir / "review.md", _generate_review_md(data))

    return f"Review submitted (verdict: {verdict}). Files: review.yaml, review.md"


if __name__ == "__main__":
    if mcp is None:
        raise SystemExit(
            "Missing dependency: mcp. "
            "Install with `python3 -m pip install -r requirements.txt`."
        )
    mcp.run()
