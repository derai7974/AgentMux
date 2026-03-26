from __future__ import annotations

from dataclasses import dataclass

from ..sessions.state_store import (
    cleanup_feature_dir,
    commit_changes,
    feature_slug_from_dir,
)
from ..shared.models import GitHubConfig, RuntimeFiles
from .github import create_branch_and_pr


@dataclass(frozen=True)
class CompletionResult:
    commit_hash: str | None
    pr_url: str | None
    cleaned_up: bool


class CompletionService:
    def finalize_approval(
        self,
        *,
        files: RuntimeFiles,
        github_config: GitHubConfig,
        gh_available: bool,
        issue_number: str | None,
        commit_message: str,
        changed_paths: list[str],
    ) -> CompletionResult:
        commit_hash = commit_changes(files.project_dir, commit_message, changed_paths)
        if commit_hash is None:
            return CompletionResult(commit_hash=None, pr_url=None, cleaned_up=False)

        pr_url: str | None = None
        if gh_available:
            result = create_branch_and_pr(
                project_dir=files.project_dir,
                feature_slug=feature_slug_from_dir(files.feature_dir),
                github_config=github_config,
                issue_number=issue_number,
                feature_dir=files.feature_dir,
            )
            if result:
                pr_url = result["pr_url"]

        cleanup_feature_dir(files.feature_dir)
        return CompletionResult(commit_hash=commit_hash, pr_url=pr_url, cleaned_up=True)
