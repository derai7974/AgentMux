"""Tests for refactored MCP research server tools (Sub-plan 2).

All tools are now pure: they validate inputs, append to tool_events.jsonl,
and return a confirmation string. They write NO files other than the log.
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

import agentmux.integrations.mcp_research_server as mrs


class _FeatureDirMixin:
    """Mixin providing a temporary feature directory with FEATURE_DIR env."""

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


class TestResearchDispatchCode(_FeatureDirMixin, unittest.TestCase):
    """Tests for renamed research_dispatch_code tool."""

    def test_validates_topic_and_appends_to_log(self):
        result = mrs.research_dispatch_code(
            topic="auth-module",
            context="Planning auth changes",
            questions=["Where is auth middleware?"],
            feature_dir=str(self.feature_dir),
            scope_hints=["src/"],
        )
        self.assertEqual("Code research on 'auth-module' dispatched.", result)
        entries = self._read_log_entries()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["tool"], "research_dispatch_code")
        self.assertEqual(entries[0]["payload"]["topic"], "auth-module")
        self.assertEqual(entries[0]["payload"]["research_type"], "code")
        self.assertEqual(entries[0]["payload"]["context"], "Planning auth changes")

    def test_does_not_write_request_md(self):
        mrs.research_dispatch_code(
            topic="test-topic",
            context="x",
            questions=["q"],
            feature_dir=str(self.feature_dir),
        )
        # No request.md should be created anywhere
        for p in self.feature_dir.rglob("request.md"):
            self.fail(f"request.md should not exist: {p}")

    def test_rejects_invalid_topic(self):
        with self.assertRaises(ValueError):
            mrs.research_dispatch_code(
                topic="Bad_Topic",
                context="x",
                questions=["q"],
                feature_dir=str(self.feature_dir),
            )

    def test_rejects_empty_questions(self):
        with self.assertRaises(ValueError):
            mrs.research_dispatch_code(
                topic="valid-topic",
                context="x",
                questions=["", "  "],
                feature_dir=str(self.feature_dir),
            )


class TestResearchDispatchWeb(_FeatureDirMixin, unittest.TestCase):
    """Tests for renamed research_dispatch_web tool."""

    def test_validates_and_appends_with_web_type(self):
        result = mrs.research_dispatch_web(
            topic="sdk-compat",
            context="SDK matrix needed",
            questions=["Which SDKs support MCP?"],
            feature_dir=str(self.feature_dir),
        )
        self.assertEqual("Web research on 'sdk-compat' dispatched.", result)
        entries = self._read_log_entries()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["tool"], "research_dispatch_web")
        self.assertEqual(entries[0]["payload"]["research_type"], "web")

    def test_does_not_write_request_md(self):
        mrs.research_dispatch_web(
            topic="test-topic",
            context="x",
            questions=["q"],
            feature_dir=str(self.feature_dir),
        )
        for p in self.feature_dir.rglob("request.md"):
            self.fail(f"request.md should not exist: {p}")


class TestSubmitArchitecture(_FeatureDirMixin, unittest.TestCase):
    """Tests for renamed submit_architecture tool."""

    def _defaults(self, **overrides):
        defaults = {
            "solution_overview": "Plugin architecture",
            "components": [{"name": "Core", "responsibility": "Main loop"}],
            "interfaces_and_contracts": "REST API",
            "data_models": "User, Session",
            "cross_cutting_concerns": "Logging",
            "technology_choices": "Python",
            "risks_and_mitigations": "None",
            "feature_dir": str(self.feature_dir),
        }
        defaults.update(overrides)
        return defaults

    def test_validates_and_appends(self):
        result = mrs.submit_architecture(**self._defaults())
        self.assertIn("Architecture submitted", result)
        entries = self._read_log_entries()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["tool"], "submit_architecture")
        self.assertEqual(
            entries[0]["payload"]["solution_overview"], "Plugin architecture"
        )

    def test_does_not_write_files(self):
        mrs.submit_architecture(**self._defaults())
        self.assertFalse(
            (self.feature_dir / "02_planning" / "architecture.yaml").exists()
        )
        self.assertFalse(
            (self.feature_dir / "02_planning" / "architecture.md").exists()
        )

    def test_validation_error_on_empty_field(self):
        with self.assertRaises(ValueError) as ctx:
            mrs.submit_architecture(
                solution_overview="",
                components=[],
                interfaces_and_contracts="x",
                data_models="x",
                cross_cutting_concerns="x",
                technology_choices="x",
                risks_and_mitigations="x",
                feature_dir=str(self.feature_dir),
            )
        self.assertIn("solution_overview", str(ctx.exception))

    def test_optional_design_handoff_in_payload(self):
        mrs.submit_architecture(**self._defaults(design_handoff="UI mockups needed"))
        entries = self._read_log_entries()
        self.assertEqual(entries[0]["payload"]["design_handoff"], "UI mockups needed")


class TestSubmitExecutionPlan(_FeatureDirMixin, unittest.TestCase):
    """Tests for renamed submit_execution_plan tool."""

    def _defaults(self, **overrides):
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
        return defaults

    def test_validates_and_appends(self):
        result = mrs.submit_execution_plan(**self._defaults())
        self.assertIn("Execution plan submitted", result)
        entries = self._read_log_entries()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["tool"], "submit_execution_plan")
        self.assertEqual(entries[0]["payload"]["needs_design"], False)

    def test_does_not_write_files(self):
        mrs.submit_execution_plan(**self._defaults())
        self.assertFalse(
            (self.feature_dir / "02_planning" / "execution_plan.yaml").exists()
        )
        self.assertFalse((self.feature_dir / "02_planning" / "plan.md").exists())

    def test_validation_error_on_bad_mode(self):
        with self.assertRaises(ValueError) as ctx:
            mrs.submit_execution_plan(
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


class TestSubmitSubplan(_FeatureDirMixin, unittest.TestCase):
    """Tests for renamed submit_subplan tool."""

    def _defaults(self, **overrides):
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
        return defaults

    def test_validates_and_appends(self):
        result = mrs.submit_subplan(**self._defaults())
        self.assertIn("Sub-plan 1 submitted", result)
        entries = self._read_log_entries()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["tool"], "submit_subplan")
        self.assertEqual(entries[0]["payload"]["index"], 1)

    def test_does_not_write_files(self):
        mrs.submit_subplan(**self._defaults())
        self.assertFalse((self.feature_dir / "02_planning" / "plan_1.yaml").exists())
        self.assertFalse((self.feature_dir / "02_planning" / "plan_1.md").exists())
        self.assertFalse((self.feature_dir / "02_planning" / "tasks_1.md").exists())

    def test_validation_error_on_index_zero(self):
        with self.assertRaises(ValueError):
            mrs.submit_subplan(
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

    def test_optional_isolation_rationale_in_payload(self):
        mrs.submit_subplan(**self._defaults(isolation_rationale="No shared state"))
        entries = self._read_log_entries()
        self.assertEqual(
            entries[0]["payload"]["isolation_rationale"], "No shared state"
        )


class TestSubmitReview(_FeatureDirMixin, unittest.TestCase):
    """Tests for renamed submit_review tool."""

    def test_pass_validates_and_appends(self):
        result = mrs.submit_review(
            verdict="pass",
            summary="All checks passed",
            feature_dir=str(self.feature_dir),
        )
        self.assertIn("verdict: pass", result)
        entries = self._read_log_entries()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["tool"], "submit_review")
        self.assertEqual(entries[0]["payload"]["verdict"], "pass")

    def test_fail_with_findings_appends(self):
        result = mrs.submit_review(
            verdict="fail",
            summary="Issues found",
            feature_dir=str(self.feature_dir),
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
        mrs.submit_review(
            verdict="pass",
            summary="OK",
            feature_dir=str(self.feature_dir),
        )
        self.assertFalse((self.feature_dir / "06_review" / "review.yaml").exists())
        self.assertFalse((self.feature_dir / "06_review" / "review.md").exists())

    def test_fail_without_findings_raises(self):
        with self.assertRaises(ValueError) as ctx:
            mrs.submit_review(
                verdict="fail",
                summary="Bad",
                feature_dir=str(self.feature_dir),
            )
        self.assertIn("findings", str(ctx.exception))

    def test_invalid_verdict_raises(self):
        with self.assertRaises(ValueError):
            mrs.submit_review(
                verdict="maybe",
                summary="Unsure",
                feature_dir=str(self.feature_dir),
            )

    def test_commit_message_in_payload(self):
        mrs.submit_review(
            verdict="pass",
            summary="OK",
            feature_dir=str(self.feature_dir),
            commit_message="feat: add auth",
        )
        entries = self._read_log_entries()
        self.assertEqual(entries[0]["payload"]["commit_message"], "feat: add auth")


class TestSubmitDone(_FeatureDirMixin, unittest.TestCase):
    """Tests for new submit_done tool."""

    def test_valid_index_appends_and_returns_confirmation(self):
        result = mrs.submit_done(subplan_index=1, feature_dir=str(self.feature_dir))
        self.assertEqual("Sub-plan 1 marked done.", result)
        entries = self._read_log_entries()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["tool"], "submit_done")
        self.assertEqual(entries[0]["payload"]["subplan_index"], 1)

    def test_rejects_index_zero(self):
        with self.assertRaises(ValueError):
            mrs.submit_done(subplan_index=0, feature_dir=str(self.feature_dir))

    def test_rejects_negative_index(self):
        with self.assertRaises(ValueError):
            mrs.submit_done(subplan_index=-1, feature_dir=str(self.feature_dir))

    def test_rejects_non_integer(self):
        with self.assertRaises(ValueError):
            mrs.submit_done(subplan_index="1", feature_dir=str(self.feature_dir))

    def test_accepts_higher_index(self):
        result = mrs.submit_done(subplan_index=5, feature_dir=str(self.feature_dir))
        self.assertEqual("Sub-plan 5 marked done.", result)
        entries = self._read_log_entries()
        self.assertEqual(entries[0]["payload"]["subplan_index"], 5)


class TestSubmitResearchDone(_FeatureDirMixin, unittest.TestCase):
    """Tests for new submit_research_done tool."""

    def test_valid_code_type_appends(self):
        result = mrs.submit_research_done(
            topic="auth-module", type="code", feature_dir=str(self.feature_dir)
        )
        self.assertEqual("Research on 'auth-module' (code) marked done.", result)
        entries = self._read_log_entries()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["tool"], "submit_research_done")
        self.assertEqual(entries[0]["payload"]["topic"], "auth-module")
        self.assertEqual(entries[0]["payload"]["type"], "code")

    def test_valid_web_type_appends(self):
        result = mrs.submit_research_done(
            topic="sdk-compat", type="web", feature_dir=str(self.feature_dir)
        )
        self.assertEqual("Research on 'sdk-compat' (web) marked done.", result)
        entries = self._read_log_entries()
        self.assertEqual(entries[0]["payload"]["type"], "web")

    def test_rejects_invalid_topic_slug(self):
        with self.assertRaises(ValueError):
            mrs.submit_research_done(
                topic="Bad_Topic", type="code", feature_dir=str(self.feature_dir)
            )

    def test_rejects_invalid_type(self):
        with self.assertRaises(ValueError):
            mrs.submit_research_done(
                topic="valid-topic", type="invalid", feature_dir=str(self.feature_dir)
            )

    def test_rejects_empty_topic(self):
        with self.assertRaises(ValueError):
            mrs.submit_research_done(
                topic="", type="code", feature_dir=str(self.feature_dir)
            )


class TestSubmitPmDone(_FeatureDirMixin, unittest.TestCase):
    """Tests for new submit_pm_done tool."""

    def test_appends_and_returns_confirmation(self):
        result = mrs.submit_pm_done(feature_dir=str(self.feature_dir))
        self.assertEqual("Product management phase done.", result)
        entries = self._read_log_entries()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["tool"], "submit_pm_done")
        self.assertEqual(entries[0]["payload"], {})


class TestNoHandoffArtifactsImport(unittest.TestCase):
    """Verify handoff_artifacts is no longer imported in mcp_research_server."""

    def test_no_handoff_artifacts_import(self):
        import inspect

        source = inspect.getsource(mrs)
        self.assertNotIn("handoff_artifacts", source)


class TestNoAgentmuxPrefix(unittest.TestCase):
    """Verify no tool name has agentmux_ prefix."""

    def test_no_agentmux_prefix_on_tools(self):
        tool_funcs = [
            name
            for name in dir(mrs)
            if name.startswith(("research_dispatch_", "submit_"))
            and not name.startswith("_")
        ]
        for name in tool_funcs:
            self.assertFalse(
                name.startswith("agentmux_"),
                f"Tool {name} still has agentmux_ prefix",
            )


if __name__ == "__main__":
    unittest.main()
