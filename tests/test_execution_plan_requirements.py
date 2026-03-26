from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from agentmux.workflow.execution_plan import load_execution_plan


class ExecutionPlanRequirementsTests(unittest.TestCase):
    def test_missing_execution_plan_returns_none_for_legacy_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            planning_dir = Path(td) / "02_planning"
            planning_dir.mkdir(parents=True, exist_ok=True)

            self.assertIsNone(load_execution_plan(planning_dir))

    def test_load_execution_plan_accepts_valid_structure_and_existing_plan_files(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            planning_dir = Path(td) / "02_planning"
            planning_dir.mkdir(parents=True, exist_ok=True)
            (planning_dir / "plan_1.md").write_text("# Plan 1\n", encoding="utf-8")
            (planning_dir / "plan_2.md").write_text("# Plan 2\n", encoding="utf-8")
            (planning_dir / "execution_plan.json").write_text(
                json.dumps(
                    {
                        "version": 1,
                        "groups": [
                            {
                                "group_id": "foundation",
                                "mode": "serial",
                                "plans": ["plan_1.md"],
                            },
                            {
                                "group_id": "parallel-impl",
                                "mode": "parallel",
                                "plans": ["plan_2.md"],
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )

            execution_plan = load_execution_plan(planning_dir)

            assert execution_plan is not None
            self.assertEqual(1, execution_plan.version)
            self.assertEqual(2, len(execution_plan.groups))
            self.assertEqual("foundation", execution_plan.groups[0].group_id)
            self.assertEqual("serial", execution_plan.groups[0].mode)
            self.assertEqual(["plan_1.md"], execution_plan.groups[0].plans)

    def test_load_execution_plan_fails_for_missing_referenced_plan_file(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            planning_dir = Path(td) / "02_planning"
            planning_dir.mkdir(parents=True, exist_ok=True)
            (planning_dir / "execution_plan.json").write_text(
                json.dumps(
                    {
                        "version": 1,
                        "groups": [
                            {
                                "group_id": "g1",
                                "mode": "serial",
                                "plans": ["plan_1.md"],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(RuntimeError, "plan_1.md"):
                load_execution_plan(planning_dir)

    def test_load_execution_plan_fails_for_malformed_groups(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            planning_dir = Path(td) / "02_planning"
            planning_dir.mkdir(parents=True, exist_ok=True)
            (planning_dir / "execution_plan.json").write_text(
                json.dumps({"version": 1, "groups": {}}),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(RuntimeError, "groups"):
                load_execution_plan(planning_dir)

    def test_load_execution_plan_rejects_duplicate_group_ids(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            planning_dir = Path(td) / "02_planning"
            planning_dir.mkdir(parents=True, exist_ok=True)
            (planning_dir / "plan_1.md").write_text("# Plan 1\n", encoding="utf-8")
            (planning_dir / "plan_2.md").write_text("# Plan 2\n", encoding="utf-8")
            (planning_dir / "execution_plan.json").write_text(
                json.dumps(
                    {
                        "version": 1,
                        "groups": [
                            {
                                "group_id": "g1",
                                "mode": "serial",
                                "plans": ["plan_1.md"],
                            },
                            {
                                "group_id": "g1",
                                "mode": "parallel",
                                "plans": ["plan_2.md"],
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(RuntimeError, "duplicate"):
                load_execution_plan(planning_dir)


if __name__ == "__main__":
    unittest.main()
