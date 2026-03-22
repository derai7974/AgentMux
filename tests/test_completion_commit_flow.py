from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.models import AgentConfig
from src.phases import CompletingPhase
from src.prompts import build_confirmation_prompt
from src.state import create_feature_files, load_state
from src.transitions import EXIT_SUCCESS, PipelineContext


class _FakeRuntime:
    def send(self, role: str, prompt_file: Path) -> None:
        _ = role, prompt_file

    def deactivate_many(self, roles) -> None:
        _ = roles

    def finish_many(self, role: str) -> None:
        _ = role


def _make_ctx(feature_dir: Path) -> tuple[PipelineContext, dict]:
    project_dir = feature_dir.parent / "project"
    project_dir.mkdir(parents=True, exist_ok=True)
    files = create_feature_files(project_dir, feature_dir, "test", "session-x")
    agents = {
        "architect": AgentConfig(role="architect", cli="claude", model="opus", args=[]),
        "coder": AgentConfig(role="coder", cli="codex", model="gpt-5.3-codex", args=[]),
    }
    ctx = PipelineContext(
        files=files,
        runtime=_FakeRuntime(),
        agents=agents,
        max_review_iterations=3,
        prompts={},
    )
    return ctx, load_state(files.state)


class CompletionCommitFlowTests(unittest.TestCase):
    def test_build_confirmation_prompt_includes_git_status_output(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            feature_dir = Path(td) / "feature"
            ctx, _ = _make_ctx(feature_dir)
            status_output = " M src/phases.py\n?? tests/test_completion_commit_flow.py\n"

            with patch(
                "src.prompts.subprocess.run",
                return_value=subprocess.CompletedProcess(
                    args=["git", "status", "--porcelain"],
                    returncode=0,
                    stdout=status_output,
                    stderr="",
                ),
            ) as run_mock:
                prompt = build_confirmation_prompt(ctx.files)

            self.assertIn(status_output.strip(), prompt)
            run_mock.assert_called_once_with(
                ["git", "status", "--porcelain"],
                cwd=ctx.files.project_dir,
                capture_output=True,
                text=True,
                check=True,
            )

    def test_approval_commits_changed_minus_exclusions_and_cleans_up_on_success(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            feature_dir = Path(td) / "feature"
            ctx, state = _make_ctx(feature_dir)
            approval = {
                "action": "approve",
                "commit_message": "test commit",
                "exclude_files": ["tests/skip.py"],
            }
            (ctx.files.completion_dir / "approval.json").write_text(json.dumps(approval), encoding="utf-8")

            with patch(
                "src.phases.subprocess.run",
                return_value=subprocess.CompletedProcess(
                    args=["git", "status", "--porcelain"],
                    returncode=0,
                    stdout=" M src/phases.py\n?? tests/skip.py\nR  old.py -> renamed.py\n",
                    stderr="",
                ),
            ), patch("src.phases.commit_changes", return_value="abc123") as commit_mock, patch(
                "src.phases.cleanup_feature_dir"
            ) as cleanup_mock:
                result = CompletingPhase().handle_event(state, "approval_received", ctx)

            self.assertEqual(EXIT_SUCCESS, result)
            commit_mock.assert_called_once_with(
                ctx.files.project_dir,
                "test commit",
                ["src/phases.py", "renamed.py"],
            )
            cleanup_mock.assert_called_once_with(ctx.files.feature_dir)

    def test_approval_failure_keeps_feature_directory(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            feature_dir = Path(td) / "feature"
            ctx, state = _make_ctx(feature_dir)
            approval = {
                "action": "approve",
                "commit_message": "test commit",
                "exclude_files": [],
            }
            (ctx.files.completion_dir / "approval.json").write_text(json.dumps(approval), encoding="utf-8")

            with patch(
                "src.phases.subprocess.run",
                return_value=subprocess.CompletedProcess(
                    args=["git", "status", "--porcelain"],
                    returncode=0,
                    stdout=" M src/phases.py\n",
                    stderr="",
                ),
            ), patch("src.phases.commit_changes", return_value=None), patch(
                "src.phases.cleanup_feature_dir"
            ) as cleanup_mock:
                result = CompletingPhase().handle_event(state, "approval_received", ctx)

            self.assertEqual(EXIT_SUCCESS, result)
            cleanup_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
