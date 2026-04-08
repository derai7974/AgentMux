"""Tests for MCP submission tools (architecture, execution_plan, subplan, review).

Submit tools are pure completion signals: they read and validate the agent-written
YAML file, append a minimal signal event to tool_events.jsonl, and return a
confirmation string. They write NO files other than the log.
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

import yaml


class SubmitToolTestBase(unittest.TestCase):
    """Base class providing a temporary feature directory."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.feature_dir = Path(self._tmpdir.name)
        os.environ["FEATURE_DIR"] = str(self.feature_dir)

    def tearDown(self):
        os.environ.pop("FEATURE_DIR", None)
        self._tmpdir.cleanup()

    def _read_log_entries(self):
        log_path = self.feature_dir / "tool_events.jsonl"
        if not log_path.exists():
            return []
        return [json.loads(line) for line in log_path.read_text().strip().splitlines()]

    def _write_yaml(self, rel_path: str, data: dict) -> Path:
        """Write a YAML file into the feature dir."""
        path = self.feature_dir / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            yaml.safe_dump(data, default_flow_style=False), encoding="utf-8"
        )
        return path


_VALID_ARCHITECTURE = {
    "solution_overview": "Plugin architecture",
    "components": [
        {
            "name": "Core",
            "responsibility": "Main loop",
            "interfaces": ["run()"],
        }
    ],
    "interfaces_and_contracts": "REST API",
    "data_models": "User, Session",
    "cross_cutting_concerns": "Logging, auth",
    "technology_choices": "Python",
    "risks_and_mitigations": "None",
}

_VALID_EXECUTION_PLAN = {
    "version": 1,
    "groups": [
        {
            "group_id": "core",
            "mode": "serial",
            "plans": [{"file": "plan_1.md", "name": "Setup"}],
        }
    ],
    "review_strategy": {"severity": "medium", "focus": ["security"]},
    "needs_design": False,
    "needs_docs": True,
    "doc_files": ["docs/api.md"],
    "plan_overview": "# Plan\n\nSetup core modules.",
}

_VALID_SUBPLAN = {
    "index": 1,
    "title": "Auth module",
    "scope": "User authentication",
    "owned_files": ["src/auth.py"],
    "dependencies": "None",
    "implementation_approach": "Step by step",
    "acceptance_criteria": "Tests pass",
    "tasks": ["Create module", "Write tests"],
}

_VALID_REVIEW_PASS = {
    "verdict": "pass",
    "summary": "All checks passed",
}


class TestSubmitArchitecture(SubmitToolTestBase):
    def _submit(self, feature_dir=None):
        from agentmux.integrations.mcp_research_server import submit_architecture

        return submit_architecture(
            feature_dir=feature_dir or str(self.feature_dir),
        )

    def test_appends_minimal_signal_to_log(self):
        self._write_yaml("02_planning/architecture.yaml", _VALID_ARCHITECTURE)
        result = self._submit()
        self.assertIn("Architecture submitted", result)
        entries = self._read_log_entries()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["tool"], "submit_architecture")
        # Payload should be empty — no data carried
        self.assertEqual(entries[0]["payload"], {})

    def test_does_not_write_files(self):
        self._write_yaml("02_planning/architecture.yaml", _VALID_ARCHITECTURE)
        self._submit()
        # Only architecture.yaml (which WE wrote) should exist
        self.assertFalse(
            (self.feature_dir / "02_planning" / "architecture.md").exists()
        )

    def test_raises_when_yaml_missing(self):
        from agentmux.integrations.mcp_research_server import submit_architecture

        with self.assertRaises(ValueError) as ctx:
            submit_architecture(feature_dir=str(self.feature_dir))
        self.assertIn("architecture.yaml", str(ctx.exception))

    def test_raises_on_invalid_yaml_content(self):
        from agentmux.integrations.mcp_research_server import submit_architecture

        bad = {**_VALID_ARCHITECTURE, "solution_overview": ""}  # empty = invalid
        self._write_yaml("02_planning/architecture.yaml", bad)
        with self.assertRaises(ValueError) as ctx:
            submit_architecture(feature_dir=str(self.feature_dir))
        self.assertIn("solution_overview", str(ctx.exception))

    def test_accepts_optional_design_handoff(self):
        data = {**_VALID_ARCHITECTURE, "design_handoff": "UI mockups needed"}
        self._write_yaml("02_planning/architecture.yaml", data)
        result = self._submit()
        self.assertIn("Architecture submitted", result)

    def test_accepts_optional_approved_preferences(self):
        data = {
            **_VALID_ARCHITECTURE,
            "approved_preferences": {
                "source_role": "architect",
                "approved": [
                    {"target_role": "coder", "bullet": "- Prefer typed helpers"}
                ],
            },
        }
        self._write_yaml("02_planning/architecture.yaml", data)
        result = self._submit()
        self.assertIn("Architecture submitted", result)

    def test_rejects_invalid_approved_preferences(self):
        from agentmux.integrations.mcp_research_server import submit_architecture

        data = {
            **_VALID_ARCHITECTURE,
            "approved_preferences": {
                "source_role": "planner",  # wrong role for architecture
                "approved": [{"target_role": "coder", "bullet": "- x"}],
            },
        }
        self._write_yaml("02_planning/architecture.yaml", data)
        with self.assertRaises(ValueError) as ctx:
            submit_architecture(feature_dir=str(self.feature_dir))
        self.assertIn("approved_preferences", str(ctx.exception))


class TestSubmitExecutionPlan(SubmitToolTestBase):
    def _submit(self, feature_dir=None):
        from agentmux.integrations.mcp_research_server import submit_execution_plan

        return submit_execution_plan(
            feature_dir=feature_dir or str(self.feature_dir),
        )

    def test_appends_minimal_signal_to_log(self):
        self._write_yaml("02_planning/execution_plan.yaml", _VALID_EXECUTION_PLAN)
        result = self._submit()
        self.assertIn("Execution plan submitted", result)
        entries = self._read_log_entries()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["tool"], "submit_execution_plan")
        self.assertEqual(entries[0]["payload"], {})

    def test_does_not_write_files(self):
        self._write_yaml("02_planning/execution_plan.yaml", _VALID_EXECUTION_PLAN)
        self._submit()
        self.assertFalse((self.feature_dir / "02_planning" / "plan.md").exists())

    def test_raises_when_yaml_missing(self):
        from agentmux.integrations.mcp_research_server import submit_execution_plan

        with self.assertRaises(ValueError) as ctx:
            submit_execution_plan(feature_dir=str(self.feature_dir))
        self.assertIn("execution_plan.yaml", str(ctx.exception))

    def test_raises_on_invalid_mode(self):
        from agentmux.integrations.mcp_research_server import submit_execution_plan

        bad = {
            **_VALID_EXECUTION_PLAN,
            "groups": [
                {
                    "group_id": "g1",
                    "mode": "bad",
                    "plans": [{"file": "p.md", "name": "x"}],
                }
            ],
        }
        self._write_yaml("02_planning/execution_plan.yaml", bad)
        with self.assertRaises(ValueError) as ctx:
            submit_execution_plan(feature_dir=str(self.feature_dir))
        self.assertIn("mode", str(ctx.exception))

    def test_accepts_optional_approved_preferences(self):
        data = {
            **_VALID_EXECUTION_PLAN,
            "approved_preferences": {
                "source_role": "planner",
                "approved": [
                    {
                        "target_role": "coder",
                        "bullet": "- Validate each task before done",
                    }
                ],
            },
        }
        self._write_yaml("02_planning/execution_plan.yaml", data)
        result = self._submit()
        self.assertIn("Execution plan submitted", result)


class TestSubmitSubplan(SubmitToolTestBase):
    def _submit(self, index=1, feature_dir=None):
        from agentmux.integrations.mcp_research_server import submit_subplan

        return submit_subplan(
            index=index,
            feature_dir=feature_dir or str(self.feature_dir),
        )

    def test_appends_signal_with_index_to_log(self):
        self._write_yaml("02_planning/plan_1.yaml", _VALID_SUBPLAN)
        result = self._submit(index=1)
        self.assertIn("Sub-plan 1 submitted", result)
        entries = self._read_log_entries()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["tool"], "submit_subplan")
        # Index is the only payload data (needed by handler)
        self.assertEqual(entries[0]["payload"], {"index": 1})

    def test_does_not_write_files(self):
        self._write_yaml("02_planning/plan_1.yaml", _VALID_SUBPLAN)
        self._submit(index=1)
        self.assertFalse((self.feature_dir / "02_planning" / "plan_1.md").exists())
        self.assertFalse((self.feature_dir / "02_planning" / "tasks_1.md").exists())

    def test_raises_when_yaml_missing(self):
        from agentmux.integrations.mcp_research_server import submit_subplan

        with self.assertRaises(ValueError) as ctx:
            submit_subplan(index=1, feature_dir=str(self.feature_dir))
        self.assertIn("plan_1.yaml", str(ctx.exception))

    def test_raises_on_invalid_index(self):
        from agentmux.integrations.mcp_research_server import submit_subplan

        with self.assertRaises(ValueError):
            submit_subplan(index=0, feature_dir=str(self.feature_dir))

    def test_different_index(self):
        data = {**_VALID_SUBPLAN, "index": 3}
        self._write_yaml("02_planning/plan_3.yaml", data)
        result = self._submit(index=3)
        self.assertIn("Sub-plan 3 submitted", result)
        entries = self._read_log_entries()
        self.assertEqual(entries[0]["payload"]["index"], 3)

    def test_accepts_optional_isolation_rationale(self):
        data = {**_VALID_SUBPLAN, "isolation_rationale": "No shared state"}
        self._write_yaml("02_planning/plan_1.yaml", data)
        result = self._submit(index=1)
        self.assertIn("Sub-plan 1 submitted", result)

    def test_raises_on_zero_tasks(self):
        from agentmux.integrations.mcp_research_server import submit_subplan

        bad = {**_VALID_SUBPLAN, "tasks": []}
        self._write_yaml("02_planning/plan_1.yaml", bad)
        with self.assertRaises(ValueError):
            submit_subplan(index=1, feature_dir=str(self.feature_dir))


class TestSubmitReview(SubmitToolTestBase):
    def _submit(self, feature_dir=None):
        from agentmux.integrations.mcp_research_server import submit_review

        return submit_review(
            feature_dir=feature_dir or str(self.feature_dir),
        )

    def test_pass_appends_minimal_signal_to_log(self):
        self._write_yaml("06_review/review.yaml", _VALID_REVIEW_PASS)
        result = self._submit()
        self.assertIn("verdict: pass", result)
        entries = self._read_log_entries()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["tool"], "submit_review")
        self.assertEqual(entries[0]["payload"], {})

    def test_does_not_write_files(self):
        self._write_yaml("06_review/review.yaml", _VALID_REVIEW_PASS)
        self._submit()
        self.assertFalse((self.feature_dir / "06_review" / "review.md").exists())

    def test_raises_when_yaml_missing(self):
        from agentmux.integrations.mcp_research_server import submit_review

        with self.assertRaises(ValueError) as ctx:
            submit_review(feature_dir=str(self.feature_dir))
        self.assertIn("review.yaml", str(ctx.exception))

    def test_fail_with_findings(self):
        data = {
            "verdict": "fail",
            "summary": "Issues found",
            "findings": [
                {
                    "location": "src/x.py:10",
                    "issue": "Missing validation",
                    "severity": "high",
                    "recommendation": "Add check",
                }
            ],
        }
        self._write_yaml("06_review/review.yaml", data)
        result = self._submit()
        self.assertIn("verdict: fail", result)
        entries = self._read_log_entries()
        self.assertEqual(entries[0]["payload"], {})

    def test_fail_without_findings_raises(self):
        from agentmux.integrations.mcp_research_server import submit_review

        self._write_yaml("06_review/review.yaml", {"verdict": "fail", "summary": "Bad"})
        with self.assertRaises(ValueError) as ctx:
            submit_review(feature_dir=str(self.feature_dir))
        self.assertIn("findings", str(ctx.exception))

    def test_invalid_verdict_raises(self):
        from agentmux.integrations.mcp_research_server import submit_review

        self._write_yaml(
            "06_review/review.yaml", {"verdict": "maybe", "summary": "Unsure"}
        )
        with self.assertRaises(ValueError):
            submit_review(feature_dir=str(self.feature_dir))

    def test_accepts_optional_commit_message(self):
        data = {**_VALID_REVIEW_PASS, "commit_message": "feat: add auth"}
        self._write_yaml("06_review/review.yaml", data)
        result = self._submit()
        self.assertIn("verdict: pass", result)

    def test_accepts_optional_approved_preferences(self):
        data = {
            **_VALID_REVIEW_PASS,
            "approved_preferences": {
                "source_role": "reviewer",
                "approved": [
                    {"target_role": "coder", "bullet": "- Keep regression tests"}
                ],
            },
        }
        self._write_yaml("06_review/review.yaml", data)
        result = self._submit()
        self.assertIn("verdict: pass", result)


if __name__ == "__main__":
    unittest.main()
