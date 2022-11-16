""" Implements Maturin as a build system for kraken-std. """

from __future__ import annotations

import logging
from pathlib import Path
from typing import List

from .poetry import PoetryPythonBuildSystem

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

    def build_command(self) -> List[str]:
        return ["poetry", "run", "maturin", "build"]

    def dist_dir(self) -> Path:
        return self.project_directory / "target" / "wheels"
