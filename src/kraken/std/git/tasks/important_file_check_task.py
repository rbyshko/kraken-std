from __future__ import annotations

import subprocess as sp
from pathlib import Path

from kraken.core.api import Property, Task, TaskStatus


class ImportantFileCheckTask(Task):
    file_to_check: Property[Path]

    def file_committed(self) -> str:
        command = f"git ls-files -- {self.file_to_check.get()}"
        return sp.getoutput(command)

    def execute(self) -> TaskStatus:
        if not self.file_to_check.get().exists():
            return TaskStatus.failed(f"{self.file_to_check.get()} does not exist, but it should")

        if not self.file_committed():
            return TaskStatus.failed(f"{self.file_to_check.get()} exists but is not committed")

        return TaskStatus.succeeded()

    def get_description(self) -> str | None:
        return f"Check {self.file_to_check.get()} exists and is not gitignored"
