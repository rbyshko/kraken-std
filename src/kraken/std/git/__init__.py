""" Tools for Git versioned projects. """

from __future__ import annotations

from pathlib import Path
from typing import Optional, Sequence, cast

from kraken.core.api import Project

from .tasks.gitignore_sync_task import GitignoreSyncTask
from .tasks.important_file_check_task import ImportantFileCheckTask
from .version import GitVersion, git_describe

__all__ = ["git_describe", "GitVersion", "GitignoreSyncTask", "gitignore", "validate_exists_and_committed"]

GITIGNORE_TASK_NAME = "gitignore"


def gitignore(
    header: str | None,
    paths: Sequence[str] | str,
    *,
    project: Project | None = None,
) -> GitignoreSyncTask:
    project = project or Project.current()
    task = cast(Optional[GitignoreSyncTask], project.tasks().get(GITIGNORE_TASK_NAME))
    if task is None:
        task = project.do(GITIGNORE_TASK_NAME, GitignoreSyncTask, group="apply")
        task.create_check()
    task.add_paths(header, [paths] if isinstance(paths, str) else paths)
    return task


def validate_exists_and_committed(path: Path, project: Project | None = None) -> ImportantFileCheckTask:
    project = project or Project.current()
    return project.do(f"check:{path}", ImportantFileCheckTask, group="check", file_to_check=path)
