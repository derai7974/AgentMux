from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src import monitor


class MonitorTests(unittest.TestCase):
    def test_render_footer_shows_elapsed_duration(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            feature_dir = Path(td)
            state_path = feature_dir / "state.json"
            panes_path = feature_dir / "panes.json"
            state_path.write_text('{"status": "coder_requested", "active_role": "coder"}', encoding="utf-8")
            panes_path.write_text("{}", encoding="utf-8")

            agents = {"coder": {"cli": "codex", "model": "gpt-5"}}

            with patch("src.monitor.get_active_roles", return_value=set()), patch(
                "src.monitor.time.time", return_value=10000.0
            ):
                output = monitor.render(
                    session_name="session-x",
                    state_path=state_path,
                    panes_path=panes_path,
                    agents=agents,
                    width=40,
                    height=18,
                    start_time=6339.0,
                )

            self.assertIn("1:01:01", output)

    def test_render_shows_recent_status_log_lines(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            feature_dir = Path(td)
            state_path = feature_dir / "state.json"
            panes_path = feature_dir / "panes.json"
            log_path = feature_dir / "status_log.txt"

            state_path.write_text('{"status": "review_ready"}', encoding="utf-8")
            panes_path.write_text("{}", encoding="utf-8")
            log_path.write_text(
                "2026-03-21 11:20:00 plan_ready\n"
                "2026-03-21 11:20:05 designer_requested\n"
                "2026-03-21 11:20:15 design_ready\n",
                encoding="utf-8",
            )

            agents = {"architect": {"cli": "codex", "model": "gpt-5"}}

            with patch("src.monitor.get_active_roles", return_value=set()), patch(
                "src.monitor.time.time", return_value=12000.0
            ):
                output = monitor.render(
                    session_name="session-x",
                    state_path=state_path,
                    panes_path=panes_path,
                    agents=agents,
                    width=40,
                    height=20,
                    start_time=11900.0,
                )

            self.assertIn("11:20 design_ready", output)
            self.assertIn("11:20 designer_reque", output)

    def test_append_status_change_logs_only_when_changed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            feature_dir = Path(td)
            log_path = feature_dir / "status_log.txt"

            with patch("src.monitor.time.strftime", side_effect=["2026-03-21 11:20:05", "2026-03-21 11:20:08"]):
                prev = monitor.append_status_change(log_path, prev_status=None, status="plan_ready")
                prev = monitor.append_status_change(log_path, prev_status=prev, status="plan_ready")
                prev = monitor.append_status_change(log_path, prev_status=prev, status="coder_requested")

            self.assertEqual("coder_requested", prev)
            lines = log_path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(
                [
                    "2026-03-21 11:20:05  plan_ready",
                    "2026-03-21 11:20:08  coder_requested",
                ],
                lines,
            )

    def test_trim_model_strips_cli_prefix_and_limits_to_eight_chars(self) -> None:
        self.assertEqual("opus-4-6", monitor._trim_model("claude-opus-4-6", "claude"))
        self.assertEqual("gpt-5.1-", monitor._trim_model("gpt-5.1-codex-mini", "codex"))
        self.assertEqual("sonnet-4", monitor._trim_model("claude-sonnet-4-6", "claude"))

    def test_format_log_entry_compacts_timestamp_and_status(self) -> None:
        self.assertEqual(
            "14:35 architect_requ",
            monitor._format_log_entry("2026-03-21 14:35:01  architect_requested"),
        )
        self.assertEqual(
            "broken line",
            monitor._format_log_entry("broken line"),
        )

    def test_render_matches_20_column_design_layout(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            feature_dir = Path(td)
            state_path = feature_dir / "state.json"
            panes_path = feature_dir / "panes.json"
            log_path = feature_dir / "status_log.txt"

            state_path.write_text(
                '{"status": "architect_requested", "active_role": "architect", "review_iteration": 2, "subplan_count": 3}',
                encoding="utf-8",
            )
            panes_path.write_text("{}", encoding="utf-8")
            log_path.write_text(
                "2026-03-21 14:35:01  architect_requested\n"
                "2026-03-21 14:37:10  plan_ready\n",
                encoding="utf-8",
            )

            agents = {
                "architect": {"cli": "claude", "model": "claude-opus-4-6"},
                "coder": {"cli": "codex", "model": "gpt-5.1-codex-mini"},
                "designer": {"cli": "claude", "model": "claude-sonnet-4-6"},
            }

            with patch("src.monitor.get_active_roles", return_value={"architect"}), patch(
                "src.monitor.time.time", return_value=10000.0
            ):
                output = monitor.render(
                    session_name="session-x",
                    state_path=state_path,
                    panes_path=panes_path,
                    agents=agents,
                    width=20,
                    height=40,
                    start_time=9738.0,
                )

            self.assertIn("architect_reques", output)
            self.assertIn("review iter 2", output)
            self.assertIn("3 subplans", output)
            self.assertIn("ACTV", output)
            self.assertIn("IDLE", output)
            self.assertIn("claude/opus-4-6", output)
            self.assertIn("codex/gpt-5.1-", output)
            self.assertIn("claude/sonnet-4", output)
            self.assertIn("\n\x1b[1mLog\x1b[0m\n", output)
            self.assertIn("14:35 architect_requ", output)
            self.assertIn("14:37 plan_ready", output)
            self.assertIn("↑ 0:04:22", output)


if __name__ == "__main__":
    unittest.main()
