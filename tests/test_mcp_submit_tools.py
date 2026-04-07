"""Tests for MCP submission tools (architecture, execution_plan, subplan, review)."""

from __future__ import annotations

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
        self.planning_dir = self.feature_dir / "02_planning"
        self.review_dir = self.feature_dir / "06_review"
        # Set FEATURE_DIR so _feature_dir() can resolve it
        os.environ["FEATURE_DIR"] = str(self.feature_dir)

    def tearDown(self):
        os.environ.pop("FEATURE_DIR", None)
        self._tmpdir.cleanup()


class TestSubmitArchitecture(SubmitToolTestBase):
    def _submit(self, **overrides):
        from agentmux.integrations.mcp_research_server import (
            agentmux_submit_architecture,
        )

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
        return agentmux_submit_architecture(**defaults)

    def test_creates_yaml_and_md(self):
        result = self._submit()
        self.assertIn("Architecture submitted", result)
        self.assertTrue((self.planning_dir / "architecture.yaml").exists())
        self.assertTrue((self.planning_dir / "architecture.md").exists())

    def test_yaml_content_valid(self):
        self._submit()
        data = yaml.safe_load((self.planning_dir / "architecture.yaml").read_text())
        self.assertEqual(data["solution_overview"], "Plugin architecture")
        self.assertEqual(len(data["components"]), 1)
        self.assertEqual(data["components"][0]["name"], "Core")

    def test_md_has_sections(self):
        self._submit()
        md = (self.planning_dir / "architecture.md").read_text()
        self.assertIn("# Architecture", md)
        self.assertIn("## Solution Overview", md)
        self.assertIn("## Components", md)
        self.assertIn("### Core", md)

    def test_optional_design_handoff(self):
        self._submit(design_handoff="UI mockups needed")
        md = (self.planning_dir / "architecture.md").read_text()
        self.assertIn("## Design Handoff", md)
        self.assertIn("UI mockups needed", md)

    def test_validation_error_missing_field(self):
        from agentmux.integrations.mcp_research_server import (
            agentmux_submit_architecture,
        )

        with self.assertRaises(ValueError) as ctx:
            agentmux_submit_architecture(
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
        from agentmux.integrations.mcp_research_server import (
            agentmux_submit_execution_plan,
        )

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
        return agentmux_submit_execution_plan(**defaults)

    def test_creates_yaml_and_plan_md(self):
        result = self._submit()
        self.assertIn("Execution plan submitted", result)
        self.assertTrue((self.planning_dir / "execution_plan.yaml").exists())
        self.assertTrue((self.planning_dir / "plan.md").exists())

    def test_yaml_has_version_and_merged_fields(self):
        self._submit()
        data = yaml.safe_load((self.planning_dir / "execution_plan.yaml").read_text())
        self.assertEqual(data["version"], 1)
        self.assertFalse(data["needs_design"])
        self.assertTrue(data["needs_docs"])
        self.assertEqual(data["review_strategy"]["severity"], "medium")
        self.assertEqual(len(data["groups"]), 1)

    def test_plan_md_content(self):
        self._submit()
        md = (self.planning_dir / "plan.md").read_text()
        self.assertIn("Setup core modules", md)

    def test_validation_error_invalid_mode(self):
        from agentmux.integrations.mcp_research_server import (
            agentmux_submit_execution_plan,
        )

        with self.assertRaises(ValueError) as ctx:
            agentmux_submit_execution_plan(
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
        from agentmux.integrations.mcp_research_server import (
            agentmux_submit_subplan,
        )

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
        return agentmux_submit_subplan(**defaults)

    def test_creates_three_files(self):
        result = self._submit()
        self.assertIn("Sub-plan 1 submitted", result)
        self.assertTrue((self.planning_dir / "plan_1.yaml").exists())
        self.assertTrue((self.planning_dir / "plan_1.md").exists())
        self.assertTrue((self.planning_dir / "tasks_1.md").exists())

    def test_yaml_content(self):
        self._submit()
        data = yaml.safe_load((self.planning_dir / "plan_1.yaml").read_text())
        self.assertEqual(data["index"], 1)
        self.assertEqual(data["title"], "Auth module")
        self.assertEqual(data["tasks"], ["Create module", "Write tests"])

    def test_md_has_sections(self):
        self._submit()
        md = (self.planning_dir / "plan_1.md").read_text()
        self.assertIn("# Auth module", md)
        self.assertIn("## Scope", md)
        self.assertIn("## Owned Files", md)
        self.assertIn("`src/auth.py`", md)

    def test_tasks_md_has_checklist(self):
        self._submit()
        tasks = (self.planning_dir / "tasks_1.md").read_text()
        self.assertIn("- [ ] Create module", tasks)
        self.assertIn("- [ ] Write tests", tasks)

    def test_optional_isolation_rationale(self):
        self._submit(isolation_rationale="No shared state")
        md = (self.planning_dir / "plan_1.md").read_text()
        self.assertIn("## Isolation Rationale", md)

    def test_validation_error_index_zero(self):
        from agentmux.integrations.mcp_research_server import (
            agentmux_submit_subplan,
        )

        with self.assertRaises(ValueError):
            agentmux_submit_subplan(
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
        self.assertTrue((self.planning_dir / "plan_3.yaml").exists())
        self.assertTrue((self.planning_dir / "plan_3.md").exists())
        self.assertTrue((self.planning_dir / "tasks_3.md").exists())


class TestSubmitReview(SubmitToolTestBase):
    def _submit(self, **overrides):
        from agentmux.integrations.mcp_research_server import (
            agentmux_submit_review,
        )

        defaults = {
            "verdict": "pass",
            "summary": "All checks passed",
            "feature_dir": str(self.feature_dir),
        }
        defaults.update(overrides)
        return agentmux_submit_review(**defaults)

    def test_pass_creates_files(self):
        result = self._submit()
        self.assertIn("verdict: pass", result)
        self.assertTrue((self.review_dir / "review.yaml").exists())
        self.assertTrue((self.review_dir / "review.md").exists())

    def test_pass_md_first_line_verdict(self):
        self._submit()
        md = (self.review_dir / "review.md").read_text()
        first_line = md.splitlines()[0]
        self.assertEqual(first_line, "verdict: pass")

    def test_pass_with_commit_message(self):
        self._submit(commit_message="feat: add auth")
        md = (self.review_dir / "review.md").read_text()
        self.assertIn("feat: add auth", md)
        data = yaml.safe_load((self.review_dir / "review.yaml").read_text())
        self.assertEqual(data["commit_message"], "feat: add auth")

    def test_fail_creates_files(self):
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

    def test_fail_md_has_findings(self):
        self._submit(
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
        md = (self.review_dir / "review.md").read_text()
        self.assertEqual(md.splitlines()[0], "verdict: fail")
        self.assertIn("## Findings", md)
        self.assertIn("Missing validation", md)
        self.assertIn("`src/x.py:10`", md)

    def test_fail_without_findings_raises(self):
        from agentmux.integrations.mcp_research_server import (
            agentmux_submit_review,
        )

        with self.assertRaises(ValueError) as ctx:
            agentmux_submit_review(
                verdict="fail",
                summary="Bad",
                feature_dir=str(self.feature_dir),
            )
        self.assertIn("findings", str(ctx.exception))

    def test_invalid_verdict_raises(self):
        from agentmux.integrations.mcp_research_server import (
            agentmux_submit_review,
        )

        with self.assertRaises(ValueError):
            agentmux_submit_review(
                verdict="maybe",
                summary="Unsure",
                feature_dir=str(self.feature_dir),
            )


if __name__ == "__main__":
    unittest.main()
