"""Secure workspace management for A2IA.

Provides isolated filesystem operations with security guarantees:
- All paths validated to be within workspace
- Symlink escape prevention
- Directory traversal attack prevention
"""

import json
import os
import shutil
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path


class WorkspaceSecurityError(Exception):
    """Raised when a path operation violates workspace security."""

    pass


@dataclass
class Workspace:
    """A secure, isolated workspace for filesystem operations."""

    workspace_id: str
    path: Path
    description: str | None = None
    created_at: str | None = None

    def __post_init__(self):
        """Ensure path is absolute and resolved."""
        self.path = self.path.resolve()

        if self.created_at is None:
            self.created_at = datetime.now(UTC).isoformat()

    @classmethod
    def create(
        cls,
        workspace_root: Path,
        workspace_id: str | None = None,
        description: str | None = None,
    ) -> "Workspace":
        """Create a new workspace directory.

        Args:
            workspace_root: Root directory for all workspaces
            workspace_id: Specific workspace ID (generated if not provided)
            description: Human-readable description

        Returns:
            Workspace instance
        """
        if workspace_id is None:
            workspace_id = f"ws_{uuid.uuid4().hex[:12]}"

        workspace_path = workspace_root / workspace_id
        workspace_path.mkdir(parents=True, exist_ok=True)

        ws = cls(
            workspace_id=workspace_id, path=workspace_path, description=description
        )
        ws.save_metadata()

        return ws

    @classmethod
    def attach(cls, path: Path, description: str | None = None) -> "Workspace":
        """Attach to an existing directory as workspace.

        Args:
            path: Existing directory to use as workspace
            description: Human-readable description

        Returns:
            Workspace instance
        """
        path = path.resolve()

        if not path.exists():
            raise FileNotFoundError(f"Directory not found: {path}")

        if not path.is_dir():
            raise ValueError(f"Not a directory: {path}")

        # Try to load existing metadata
        metadata_file = path / ".a2ia_workspace.json"
        if metadata_file.exists():
            metadata = json.loads(metadata_file.read_text())
            return cls(
                workspace_id=metadata.get("workspace_id", path.name),
                path=path,
                description=metadata.get("description", description),
                created_at=metadata.get("created_at"),
            )

        # Create new workspace from existing directory
        ws = cls(workspace_id=path.name, path=path, description=description)
        ws.save_metadata()

        return ws

    @classmethod
    def resume(cls, workspace_root: Path, workspace_id: str) -> "Workspace":
        """Resume an existing workspace by ID.

        Args:
            workspace_root: Root directory for all workspaces
            workspace_id: Workspace ID to resume

        Returns:
            Workspace instance

        Raises:
            FileNotFoundError: If workspace doesn't exist
        """
        workspace_path = workspace_root / workspace_id

        if not workspace_path.exists():
            raise FileNotFoundError(f"Workspace not found: {workspace_id}")

        return cls.attach(workspace_path)

    def resolve_path(self, path: str) -> Path:
        """Resolve and validate a path within the workspace.

        This is the core security function that prevents:
        - Directory traversal attacks (../..)
        - Symlink escape attacks
        - Absolute path access outside workspace

        Args:
            path: Relative or absolute path

        Returns:
            Resolved absolute path within workspace

        Raises:
            WorkspaceSecurityError: If path is outside workspace
        """
        target = Path(path)

        if target.is_absolute():
            path_str = str(target).lstrip('/')
            target = self.path / path_str
        else:
            target = self.path / target

        try:
            resolved = target.resolve(strict=False)
        except (OSError, RuntimeError) as e:
            raise WorkspaceSecurityError(f"Cannot resolve path {path}: {e}") from e

        try:
            resolved.relative_to(self.path)
        except ValueError as e:
            raise WorkspaceSecurityError(
                f"Path {path} resolves to {resolved}, which is outside workspace {self.path}"
            ) from e

        return resolved

    def read_file(self, path: str, encoding: str = "utf-8") -> str:
        resolved = self.resolve_path(path)
        return resolved.read_text(encoding=encoding)

    def write_file(self, path: str, content: str, encoding: str = "utf-8") -> None:
        resolved = self.resolve_path(path)
        resolved.parent.mkdir(parents=True, exist_ok=True)
        resolved.write_text(content, encoding=encoding)

    def delete_file(self, path: str) -> None:
        resolved = self.resolve_path(path)
        if resolved.exists():
            resolved.unlink()

    def list_files(self, subdir: str | None = None) -> list[str]:
        target_dir = self.resolve_path(subdir or ".")
        return [str(p.relative_to(self.path)) for p in target_dir.rglob("*") if p.is_file()]

    def prune(self) -> None:
        for item in self.path.iterdir():
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()

    def save_metadata(self) -> None:
        metadata = {
            "workspace_id": self.workspace_id,
            "description": self.description,
            "created_at": self.created_at,
        }
        metadata_file = self.path / ".a2ia_workspace.json"
        metadata_file.write_text(json.dumps(metadata, indent=2))

    def load_metadata(self) -> dict:
        metadata_file = self.path / ".a2ia_workspace.json"
        if not metadata_file.exists():
            raise FileNotFoundError(f"No metadata found in {self.path}")
        return json.loads(metadata_file.read_text())