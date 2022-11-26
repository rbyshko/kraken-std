""" Implements Maturin as a build system for kraken-std. """

from __future__ import annotations

import logging
import subprocess as sp
from pathlib import Path
from typing import List

from kraken.std.python.settings import PythonSettings

from . import ManagedEnvironment
from .poetry import PoetryManagedEnvironment, PoetryPythonBuildSystem

logger = logging.getLogger(__name__)


class MaturinPythonBuildSystem(PoetryPythonBuildSystem):
    """A maturin-backed version of the Poetry build system, that invokes the maturin build-backend.
    Can be enabled by adding the following to the local pyproject.yaml:
    ```toml
    [tool.poetry.dev-dependencies]
    maturin = "0.13.7"

    [build-system]
    requires = ["maturin>=0.13,<0.14"]
    build-backend = "maturin"
    ```
    """

    name = "Maturin"

    def get_managed_environment(self) -> ManagedEnvironment:
        return MaturinManagedEnvironment(self.project_directory)

    def build_command(self) -> List[str]:
        return ["poetry", "run", "maturin", "build", "--release"]

    def dist_dir(self) -> Path:
        return self.project_directory / "target" / "wheels"


class MaturinManagedEnvironment(PoetryManagedEnvironment):
    def install(self, settings: PythonSettings) -> None:
        super(MaturinManagedEnvironment, self).install(settings)
        command = ["poetry", "run", "maturin", "develop"]
        logger.info("%s", command)
        sp.check_call(command, cwd=self.project_directory)
