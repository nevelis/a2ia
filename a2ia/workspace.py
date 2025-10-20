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
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


class WorkspaceSecurityError(Exception):
    """Raised when a path operation violates workspace security."""
    pass


@dataclass
class Workspace:
    """A secure, isolated workspace for filesystem operations."""

    workspace_id: str
    path: Path
    description: Optional[str] = None
    created_at: Optional[str] = None

    def __post_init__(self):
        """Ensure path is absolute and resolved."""
        self.path = self.path.resolve()

        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc).isoformat()

    @classmethod
    def create(
        cls,
        workspace_root: Path,
        workspace_id: Optional[str] = None,
        description: Optional[str] = None
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
            workspace_id=workspace_id,
            path=workspace_path,
            description=description
        )
        ws.save_metadata()

        return ws

    @classmethod
    def attach(
        cls,
        path: Path,
        description: Optional[str] = None
    ) -> "Workspace":
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
                created_at=metadata.get("created_at")
            )

        # Create new workspace from existing directory
        ws = cls(
            workspace_id=path.name,
            path=path,
            description=description
        )
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
        # Convert to Path object
        target = Path(path)

        # If relative, make it relative to workspace
        if not target.is_absolute():
            target = self.path / target

        # Resolve symlinks and normalize path
        try:
            resolved = target.resolve(strict=False)
        except (OSError, RuntimeError) as e:
            raise WorkspaceSecurityError(f"Cannot resolve path {path}: {e}")

        # Verify the resolved path is within workspace
        try:
            resolved.relative_to(self.path)
        except ValueError:
            raise WorkspaceSecurityError(
                f"Path {path} resolves to {resolved}, which is outside workspace {self.path}"
            )

        return resolved

    def read_file(self, path: str, encoding: str = "utf-8") -> str:
        """Read file contents.

        Args:
            path: File path relative to workspace
            encoding: Text encoding (default: utf-8)

        Returns:
            File contents as string

        Raises:
            WorkspaceSecurityError: If path is outside workspace
            FileNotFoundError: If file doesn't exist
        """
        resolved = self.resolve_path(path)

        if not resolved.exists():
            raise FileNotFoundError(f"File not found: {path}")

        if not resolved.is_file():
            raise ValueError(f"Not a file: {path}")

        return resolved.read_text(encoding=encoding)

    def write_file(self, path: str, content: str, encoding: str = "utf-8") -> dict:
        """Write file contents, creating parent directories if needed.

        Args:
            path: File path relative to workspace
            content: Content to write
            encoding: Text encoding (default: utf-8)

        Returns:
            Dict with success status, path, and size

        Raises:
            WorkspaceSecurityError: If path is outside workspace
        """
        resolved = self.resolve_path(path)

        # Create parent directories
        resolved.parent.mkdir(parents=True, exist_ok=True)

        # Write file
        resolved.write_text(content, encoding=encoding)

        return {
            "success": True,
            "path": str(resolved.relative_to(self.path)),
            "size": resolved.stat().st_size
        }

    def list_directory(self, path: str = "", recursive: bool = False) -> dict:
        """List directory contents.

        Args:
            path: Directory path relative to workspace (default: root)
            recursive: If True, list recursively

        Returns:
            Dict with 'files' and 'directories' lists

        Raises:
            WorkspaceSecurityError: If path is outside workspace
            FileNotFoundError: If directory doesn't exist
        """
        if path == "":
            resolved = self.path
        else:
            resolved = self.resolve_path(path)

        if not resolved.exists():
            raise FileNotFoundError(f"Directory not found: {path}")

        if not resolved.is_dir():
            raise ValueError(f"Not a directory: {path}")

        files = []
        directories = []

        # Metadata file to exclude from listings
        metadata_filename = ".a2ia_workspace.json"

        if recursive:
            for root, dirs, filenames in os.walk(resolved):
                root_path = Path(root)
                rel_root = root_path.relative_to(resolved)

                for filename in filenames:
                    # Skip metadata file
                    if filename == metadata_filename:
                        continue

                    if rel_root == Path("."):
                        files.append(filename)
                    else:
                        files.append(str(rel_root / filename))

                for dirname in dirs:
                    if rel_root == Path("."):
                        directories.append(dirname)
                    else:
                        directories.append(str(rel_root / dirname))
        else:
            for item in resolved.iterdir():
                # Skip metadata file
                if item.name == metadata_filename:
                    continue

                rel_path = item.relative_to(resolved)
                if item.is_file():
                    files.append(str(rel_path))
                elif item.is_dir():
                    directories.append(str(rel_path))

        return {
            "files": sorted(files),
            "directories": sorted(directories),
            "path": str(resolved)
        }

    def delete_file(self, path: str, recursive: bool = False) -> dict:
        """Delete a file or directory.

        Args:
            path: Path relative to workspace
            recursive: If True, delete directories recursively

        Returns:
            Dict with success status and path

        Raises:
            WorkspaceSecurityError: If path is outside workspace
            FileNotFoundError: If file doesn't exist
        """
        resolved = self.resolve_path(path)

        if not resolved.exists():
            raise FileNotFoundError(f"Path not found: {path}")

        if resolved.is_dir():
            if not recursive:
                raise ValueError(f"Path is a directory, use recursive=True: {path}")
            shutil.rmtree(resolved)
        else:
            resolved.unlink()

        return {
            "success": True,
            "path": str(Path(path))
        }

    def move_file(self, source: str, destination: str) -> dict:
        """Move or rename a file/directory.

        Args:
            source: Source path relative to workspace
            destination: Destination path relative to workspace

        Returns:
            Dict with success status and paths

        Raises:
            WorkspaceSecurityError: If paths are outside workspace
            FileNotFoundError: If source doesn't exist
        """
        src_resolved = self.resolve_path(source)
        dst_resolved = self.resolve_path(destination)

        if not src_resolved.exists():
            raise FileNotFoundError(f"Source not found: {source}")

        # Create destination parent directories
        dst_resolved.parent.mkdir(parents=True, exist_ok=True)

        # Move/rename
        shutil.move(str(src_resolved), str(dst_resolved))

        return {
            "success": True,
            "source": source,
            "destination": destination
        }

    def edit_file(
        self,
        path: str,
        old_text: str,
        new_text: str,
        occurrence: Optional[int] = None
    ) -> dict:
        """Edit a file by replacing text.

        Args:
            path: File path relative to workspace
            old_text: Text to find and replace
            new_text: Replacement text
            occurrence: Which occurrence to replace (1-indexed), or None for all

        Returns:
            Dict with success status, path, and number of changes

        Raises:
            WorkspaceSecurityError: If path is outside workspace
            FileNotFoundError: If file doesn't exist
            ValueError: If old_text not found
        """
        resolved = self.resolve_path(path)

        if not resolved.exists():
            raise FileNotFoundError(f"File not found: {path}")

        content = resolved.read_text()

        if old_text not in content:
            raise ValueError(f"Text not found in file: {old_text}")

        if occurrence is None:
            # Replace all occurrences
            new_content = content.replace(old_text, new_text)
            changes = content.count(old_text)
        else:
            # Replace specific occurrence
            parts = content.split(old_text)
            if occurrence < 1 or occurrence > len(parts) - 1:
                raise ValueError(f"Occurrence {occurrence} out of range (1-{len(parts) - 1})")

            # Rebuild with replacement at specific position
            new_content = old_text.join(parts[:occurrence]) + new_text + old_text.join(parts[occurrence:])
            changes = 1

        resolved.write_text(new_content)

        return {
            "success": True,
            "path": str(Path(path)),
            "changes": changes
        }

    def save_metadata(self):
        """Save workspace metadata to .a2ia_workspace.json."""
        metadata = {
            "workspace_id": self.workspace_id,
            "description": self.description,
            "created_at": self.created_at
        }

        metadata_file = self.path / ".a2ia_workspace.json"
        metadata_file.write_text(json.dumps(metadata, indent=2))

    def to_dict(self) -> dict:
        """Convert workspace to dictionary representation."""
        return {
            "workspace_id": self.workspace_id,
            "path": str(self.path),
            "description": self.description,
            "created_at": self.created_at
        }
