"""Manifest parser for the relevant bits and pieces."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, fields
from enum import Enum
from pathlib import Path
from typing import Any, List

import tomli
import tomli_w
from pydantic import ClassError


@dataclass
class Bin:
    name: str
    path: str

    def to_json(self) -> dict[str, str]:
        return {"name": self.name, "path": self.path}


# TODO: Differentiate between lib kinds?


@dataclass
class ArtifactKind(Enum):
    BIN = 1
    LIB = 2


@dataclass
class Artifact:
    name: str
    path: str
    kind: ArtifactKind

    def to_json(self) -> dict[str, str]:
        return {"name": self.name, "path": self.path, "kind": str(self.kind)}


@dataclass
class WorkspaceMember:
    id: str
    name: str
    version: str
    edition: str
    manifest_path: Path


@dataclass
class CargoMetadata:
    _path: Path
    _data: dict[str, Any]

    workspaceMembers: list[WorkspaceMember]
    artifacts: list[Artifact]

    @classmethod
    def read(cls, project_dir: Path) -> CargoMetadata:
        result = subprocess.run(
            ["cargo", "metadata", "--no-deps", "--format-version=1", "--manifest-path", project_dir / "Cargo.toml"],
            stdout=subprocess.PIPE,
        )
        return cls.of(project_dir, json.loads(result.stdout.decode("utf-8")))

    @classmethod
    def of(cls, path: Path, data: dict[str, Any]) -> CargoMetadata:
        workspace_members = []
        artifacts = []
        for package in data["packages"]:
            id = package["id"]
            if id in data["workspace_members"]:
                workspace_members.append(
                    WorkspaceMember(
                        id, package["name"], package["version"], package["edition"], Path(package["manifest_path"])
                    )
                )
                for target in package["targets"]:
                    if "bin" in target["kind"]:
                        artifacts.append(Artifact(target["name"], target["src_path"], ArtifactKind.BIN))
                    elif "lib" in target["kind"]:
                        artifacts.append(Artifact(target["name"], target["src_path"], ArtifactKind.LIB))

        return cls(path, data, workspace_members, artifacts)


@dataclass
class Package:
    name: str
    version: str | None
    edition: str | None
    unhandled: dict[str, Any] | None

    @classmethod
    def from_json(cls, json: dict[str, str]) -> Package:
        cloned = dict(json)
        name = cloned.pop("name")
        version = cloned.pop("version", None)
        edition = cloned.pop("edition", None)
        return Package(name, version, edition, cloned)

    def to_json(self) -> dict[str, str]:
        values = {f.name: getattr(self, f.name) for f in fields(self) if f.name != "unhandled"}
        if self.unhandled is not None:
            values.update({k: v for k, v in self.unhandled.items() if v is not None})
        return {k: v for k, v in values.items() if v is not None}


@dataclass
class WorkspacePackage:
    version: str
    unhandled: dict[str, Any] | None

    @classmethod
    def from_json(cls, json: dict[str, str]) -> WorkspacePackage:
        cloned = dict(json)
        version = cloned.pop("version")
        return WorkspacePackage(version, cloned)

    def to_json(self) -> dict[str, str]:
        values = {f.name: getattr(self, f.name) for f in fields(self) if f.name != "unhandled"}
        if self.unhandled is not None:
            values.update({k: v for k, v in self.unhandled.items() if v is not None})
        return {k: v for k, v in values.items() if v is not None}


@dataclass
class Workspace:
    package: WorkspacePackage | None
    members: List[str] | None
    unhandled: dict[str, Any] | None

    @classmethod
    def from_json(cls, json: dict[str, Any]) -> Workspace:
        cloned = dict(json)
        return Workspace(
            WorkspacePackage.from_json(cloned.pop("package")) if "package" in cloned else None,
            cloned.pop("members") if "members" in cloned else None,
            cloned,
        )

    def to_json(self) -> dict[str, Any]:
        values = {
            "package": self.package.to_json() if self.package else None,
            "members": self.members if self.members else None,
        }
        if self.unhandled is not None:
            values.update({k: v for k, v in self.unhandled.items() if v is not None})
        return {k: v for k, v in values.items() if v is not None}


@dataclass
class Dependencies:
    data: dict[str, Any]

    @classmethod
    def from_json(cls, json: dict[str, Any]) -> Dependencies:
        cloned = dict(json)
        return Dependencies(cloned)

    def to_json(self) -> dict[str, Any]:
        return self.data


@dataclass
class CargoManifest:
    _path: Path
    _data: dict[str, Any]

    package: Package | None
    workspace: Workspace | None
    dependencies: Dependencies | None
    bin: list[Bin]

    @classmethod
    def read(cls, path: Path) -> CargoManifest:
        with path.open("rb") as fp:
            ret = cls.of(path, tomli.load(fp))
            if ret.package is None and ret.workspace is None:
                raise ClassError
            return ret

    @classmethod
    def of(cls, path: Path, data: dict[str, Any]) -> CargoManifest:
        return cls(
            path,
            data,
            Package.from_json(data["package"]) if "package" in data else None,
            Workspace.from_json(data["workspace"]) if "workspace" in data else None,
            Dependencies.from_json(data["dependencies"]) if "dependencies" in data else None,
            [Bin(**x) for x in data.get("bin", [])],
        )

    def to_json(self) -> dict[str, Any]:
        result = self._data.copy()
        if self.bin:
            result["bin"] = [x.to_json() for x in self.bin]
        else:
            result.pop("bin", None)
        if self.package:
            result["package"] = self.package.to_json()
        if self.workspace:
            result["workspace"] = self.workspace.to_json()
        if self.dependencies:
            result["dependencies"] = self.dependencies.to_json()
        return result

    def to_toml_string(self) -> str:
        return tomli_w.dumps(self.to_json())

    def save(self, path: Path | None = None) -> None:
        path = path or self._path
        with path.open("wb") as fp:
            tomli_w.dump(self.to_json(), fp)
