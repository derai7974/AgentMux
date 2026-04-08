"""Tests for MCP submission tools (architecture, execution_plan, subplan, review).

After Sub-plan 2 refactoring, all tools are pure: they validate inputs,
append to tool_events.jsonl, and return a confirmation string. They write
NO files other than the log.
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path


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


class TestSubmitArchitecture(SubmitToolTestBase):
    def _submit(self, **overrides):
        from agentmux.integrations.mcp_research_server import submit_architecture

        defaults = {
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
            "feature_dir": str(self.feature_dir),
        }
        defaults.update(overrides)
        return submit_architecture(**defaults)

    def test_appends_to_log(self):
        result = self._submit()
        self.assertIn("Architecture submitted", result)
        entries = self._read_log_entries()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["tool"], "submit_architecture")
        self.assertEqual(
            entries[0]["payload"]["solution_overview"], "Plugin architecture"
        )
        self.assertEqual(len(entries[0]["payload"]["components"]), 1)
        self.assertEqual(entries[0]["payload"]["components"][0]["name"], "Core")

    def test_does_not_write_files(self):
        self._submit()
        self.assertFalse(
            (self.feature_dir / "02_planning" / "architecture.yaml").exists()
        )
        self.assertFalse(
            (self.feature_dir / "02_planning" / "architecture.md").exists()
        )

    def test_optional_design_handoff_in_payload(self):
        self._submit(design_handoff="UI mockups needed")
        entries = self._read_log_entries()
        self.assertEqual(entries[0]["payload"]["design_handoff"], "UI mockups needed")

    def test_validation_error_missing_field(self):
        from agentmux.integrations.mcp_research_server import submit_architecture

        with self.assertRaises(ValueError) as ctx:
            submit_architecture(
                solution_overview="",  # empty = invalid
                components=[],
                interfaces_and_contracts="x",
                data_models="x",
                cross_cutting_concerns="x",
                technology_choices="x",
                risks_and_mitigations="x",
                feature_dir=str(self.feature_dir),
            )
        self.assertIn("solution_overview", str(ctx.exception))


class TestSubmitExecutionPlan(SubmitToolTestBase):
    def _submit(self, **overrides):
        from agentmux.integrations.mcp_research_server import submit_execution_plan

        defaults = {
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
            "feature_dir": str(self.feature_dir),
        }
        defaults.update(overrides)
        return submit_execution_plan(**defaults)

    def test_appends_to_log(self):
        result = self._submit()
        self.assertIn("Execution plan submitted", result)
        entries = self._read_log_entries()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["tool"], "submit_execution_plan")
        self.assertFalse(entries[0]["payload"]["needs_design"])
        self.assertTrue(entries[0]["payload"]["needs_docs"])
        self.assertEqual(entries[0]["payload"]["review_strategy"]["severity"], "medium")
        self.assertEqual(len(entries[0]["payload"]["groups"]), 1)

    def test_does_not_write_files(self):
        self._submit()
        self.assertFalse(
            (self.feature_dir / "02_planning" / "execution_plan.yaml").exists()
        )
        self.assertFalse((self.feature_dir / "02_planning" / "plan.md").exists())

    def test_validation_error_invalid_mode(self):
        from agentmux.integrations.mcp_research_server import submit_execution_plan

        with self.assertRaises(ValueError) as ctx:
            submit_execution_plan(
                groups=[
                    {
                        "group_id": "g1",
                        "mode": "bad",
                        "plans": [{"file": "p.md", "name": "x"}],
                    }
                ],
                review_strategy={"severity": "medium", "focus": []},
                needs_design=False,
                needs_docs=False,
                doc_files=[],
                plan_overview="Overview",
                feature_dir=str(self.feature_dir),
            )
        self.assertIn("mode", str(ctx.exception))


class TestSubmitSubplan(SubmitToolTestBase):
    def _submit(self, **overrides):
        from agentmux.integrations.mcp_research_server import submit_subplan

        defaults = {
            "index": 1,
            "title": "Auth module",
            "scope": "User authentication",
            "owned_files": ["src/auth.py"],
            "dependencies": "None",
            "implementation_approach": "Step by step",
            "acceptance_criteria": "Tests pass",
            "tasks": ["Create module", "Write tests"],
            "feature_dir": str(self.feature_dir),
        }
        defaults.update(overrides)
        return submit_subplan(**defaults)

    def test_appends_to_log(self):
        result = self._submit()
        self.assertIn("Sub-plan 1 submitted", result)
        entries = self._read_log_entries()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["tool"], "submit_subplan")
        self.assertEqual(entries[0]["payload"]["index"], 1)
        self.assertEqual(entries[0]["payload"]["title"], "Auth module")
        self.assertEqual(
            entries[0]["payload"]["tasks"], ["Create module", "Write tests"]
        )

    def test_does_not_write_files(self):
        self._submit()
        self.assertFalse((self.feature_dir / "02_planning" / "plan_1.yaml").exists())
        self.assertFalse((self.feature_dir / "02_planning" / "plan_1.md").exists())
        self.assertFalse((self.feature_dir / "02_planning" / "tasks_1.md").exists())

    def test_optional_isolation_rationale_in_payload(self):
        self._submit(isolation_rationale="No shared state")
        entries = self._read_log_entries()
        self.assertEqual(
            entries[0]["payload"]["isolation_rationale"], "No shared state"
        )

    def test_validation_error_index_zero(self):
        from agentmux.integrations.mcp_research_server import submit_subplan

        with self.assertRaises(ValueError):
            submit_subplan(
                index=0,
                title="Bad",
                scope="x",
                owned_files=["f.py"],
                dependencies="none",
                implementation_approach="x",
                acceptance_criteria="x",
                tasks=["t"],
                feature_dir=str(self.feature_dir),
            )

    def test_different_index(self):
        self._submit(index=3, title="Third plan")
        entries = self._read_log_entries()
        self.assertEqual(entries[0]["payload"]["index"], 3)


class TestSubmitReview(SubmitToolTestBase):
    def _submit(self, **overrides):
        from agentmux.integrations.mcp_research_server import submit_review

        defaults = {
            "verdict": "pass",
            "summary": "All checks passed",
            "feature_dir": str(self.feature_dir),
        }
        defaults.update(overrides)
        return submit_review(**defaults)

    def test_pass_appends_to_log(self):
        result = self._submit()
        self.assertIn("verdict: pass", result)
        entries = self._read_log_entries()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["tool"], "submit_review")
        self.assertEqual(entries[0]["payload"]["verdict"], "pass")

    def test_pass_with_commit_message(self):
        self._submit(commit_message="feat: add auth")
        entries = self._read_log_entries()
        self.assertEqual(entries[0]["payload"]["commit_message"], "feat: add auth")

    def test_fail_appends_with_findings(self):
        result = self._submit(
            verdict="fail",
            summary="Issues found",
            findings=[
                {
                    "location": "src/x.py:10",
                    "issue": "Missing validation",
                    "severity": "high",
                    "recommendation": "Add check",
                }
            ],
        )
        self.assertIn("verdict: fail", result)
        entries = self._read_log_entries()
        self.assertEqual(entries[0]["payload"]["verdict"], "fail")
        self.assertEqual(len(entries[0]["payload"]["findings"]), 1)

    def test_does_not_write_files(self):
        self._submit()
        self.assertFalse((self.feature_dir / "06_review" / "review.yaml").exists())
        self.assertFalse((self.feature_dir / "06_review" / "review.md").exists())

    def test_fail_without_findings_raises(self):
        from agentmux.integrations.mcp_research_server import submit_review

        with self.assertRaises(ValueError) as ctx:
            submit_review(
                verdict="fail",
                summary="Bad",
                feature_dir=str(self.feature_dir),
            )
        self.assertIn("findings", str(ctx.exception))

    def test_invalid_verdict_raises(self):
        from agentmux.integrations.mcp_research_server import submit_review

        with self.assertRaises(ValueError):
            submit_review(
                verdict="maybe",
                summary="Unsure",
                feature_dir=str(self.feature_dir),
            )


if __name__ == "__main__":
    unittest.main()
