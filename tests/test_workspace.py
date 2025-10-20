"""Tests for workspace management and security.

Security requirements:
- All paths must be within workspace directory
- Symlinks cannot escape workspace
- Relative paths with .. cannot escape
- Absolute paths outside workspace are rejected
"""

import os
import tempfile
from pathlib import Path
import pytest

from a2ia.workspace import Workspace, WorkspaceSecurityError

# Mark all tests in this file as unit tests
pytestmark = pytest.mark.unit


class TestWorkspaceCreation:
    """Test workspace initialization."""

    def test_create_new_workspace(self, tmp_path):
        """Should create a new workspace directory."""
        workspace_root = tmp_path / "workspaces"
        workspace_root.mkdir()

        ws = Workspace.create(workspace_root)

        assert ws.workspace_id.startswith("ws_")
        assert ws.path.exists()
        assert ws.path.parent == workspace_root

    def test_create_workspace_with_id(self, tmp_path):
        """Should create workspace with specific ID."""
        workspace_root = tmp_path / "workspaces"
        workspace_root.mkdir()

        ws = Workspace.create(workspace_root, workspace_id="ws_test123")

        assert ws.workspace_id == "ws_test123"
        assert ws.path.name == "ws_test123"

    def test_attach_to_existing_directory(self, tmp_path):
        """Should attach to existing directory as workspace."""
        existing_dir = tmp_path / "my_project"
        existing_dir.mkdir()
        (existing_dir / "README.md").write_text("Hello")

        ws = Workspace.attach(existing_dir)

        assert ws.path == existing_dir.resolve()
        assert ws.workspace_id == "my_project"
        assert (ws.path / "README.md").exists()

    def test_resume_existing_workspace(self, tmp_path):
        """Should resume existing workspace by ID."""
        workspace_root = tmp_path / "workspaces"
        workspace_root.mkdir()

        # Create workspace
        ws1 = Workspace.create(workspace_root, workspace_id="ws_resume_test")
        ws1.write_file("test.txt", "content")

        # Resume it
        ws2 = Workspace.resume(workspace_root, "ws_resume_test")

        assert ws2.workspace_id == ws1.workspace_id
        assert ws2.path == ws1.path
        assert ws2.read_file("test.txt") == "content"


class TestPathSecurity:
    """Test path validation and security."""

    def test_resolve_relative_path(self, tmp_path):
        """Should resolve relative paths within workspace."""
        ws = Workspace.attach(tmp_path)

        resolved = ws.resolve_path("src/main.py")

        assert resolved == tmp_path / "src" / "main.py"

    def test_resolve_absolute_path_in_workspace(self, tmp_path):
        """Should accept absolute paths within workspace."""
        ws = Workspace.attach(tmp_path)
        absolute_path = tmp_path / "file.txt"

        resolved = ws.resolve_path(str(absolute_path))

        assert resolved == absolute_path

    def test_reject_absolute_path_outside_workspace(self, tmp_path):
        """Should reject absolute paths outside workspace."""
        ws = Workspace.attach(tmp_path)

        with pytest.raises(WorkspaceSecurityError, match="outside workspace"):
            ws.resolve_path("/etc/passwd")

    def test_reject_parent_directory_escape(self, tmp_path):
        """Should reject relative paths that escape with .."""
        ws = Workspace.attach(tmp_path)

        with pytest.raises(WorkspaceSecurityError, match="outside workspace"):
            ws.resolve_path("../../etc/passwd")

    def test_reject_symlink_escape(self, tmp_path):
        """Should reject symlinks that point outside workspace."""
        ws = Workspace.attach(tmp_path)

        # Create symlink pointing outside workspace
        outside_file = tmp_path.parent / "outside.txt"
        outside_file.write_text("secret")

        symlink = tmp_path / "link_to_outside"
        symlink.symlink_to(outside_file)

        with pytest.raises(WorkspaceSecurityError, match="outside workspace"):
            ws.resolve_path("link_to_outside")

    def test_allow_symlink_within_workspace(self, tmp_path):
        """Should allow symlinks within workspace."""
        ws = Workspace.attach(tmp_path)

        # Create file and symlink within workspace
        target = tmp_path / "target.txt"
        target.write_text("content")

        symlink = tmp_path / "link.txt"
        symlink.symlink_to(target)

        resolved = ws.resolve_path("link.txt")

        assert resolved == target

    def test_reject_current_dir_escape(self, tmp_path):
        """Should reject ./../../ patterns that try to escape."""
        ws = Workspace.attach(tmp_path)

        with pytest.raises(WorkspaceSecurityError, match="outside workspace"):
            ws.resolve_path("./../../etc/passwd")


class TestFileOperations:
    """Test filesystem operations within workspace."""

    def test_read_file(self, tmp_path):
        """Should read file contents."""
        ws = Workspace.attach(tmp_path)
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!")

        content = ws.read_file("test.txt")

        assert content == "Hello, World!"

    def test_read_nonexistent_file(self, tmp_path):
        """Should raise error for nonexistent file."""
        ws = Workspace.attach(tmp_path)

        with pytest.raises(FileNotFoundError):
            ws.read_file("nonexistent.txt")

    def test_write_file(self, tmp_path):
        """Should write file contents."""
        ws = Workspace.attach(tmp_path)

        ws.write_file("new.txt", "content")

        assert (tmp_path / "new.txt").read_text() == "content"

    def test_write_file_creates_directories(self, tmp_path):
        """Should create parent directories when writing."""
        ws = Workspace.attach(tmp_path)

        ws.write_file("src/utils/helper.py", "def help(): pass")

        assert (tmp_path / "src" / "utils" / "helper.py").exists()

    def test_write_file_outside_workspace_fails(self, tmp_path):
        """Should prevent writing outside workspace."""
        ws = Workspace.attach(tmp_path)

        with pytest.raises(WorkspaceSecurityError):
            ws.write_file("/etc/passwd", "malicious")

    def test_list_directory(self, tmp_path):
        """Should list directory contents."""
        ws = Workspace.attach(tmp_path)

        # Create test structure
        (tmp_path / "file1.txt").write_text("a")
        (tmp_path / "file2.py").write_text("b")
        (tmp_path / "subdir").mkdir()

        result = ws.list_directory()

        assert set(result["files"]) == {"file1.txt", "file2.py"}
        assert set(result["directories"]) == {"subdir"}

    def test_list_directory_recursive(self, tmp_path):
        """Should list directory recursively."""
        ws = Workspace.attach(tmp_path)

        # Create nested structure
        (tmp_path / "root.txt").write_text("a")
        (tmp_path / "dir1").mkdir()
        (tmp_path / "dir1" / "file1.txt").write_text("b")
        (tmp_path / "dir1" / "dir2").mkdir()
        (tmp_path / "dir1" / "dir2" / "file2.txt").write_text("c")

        result = ws.list_directory(recursive=True)

        # Should include all nested files
        assert "root.txt" in result["files"]
        assert "dir1/file1.txt" in result["files"]
        assert "dir1/dir2/file2.txt" in result["files"]

    def test_delete_file(self, tmp_path):
        """Should delete a file."""
        ws = Workspace.attach(tmp_path)
        test_file = tmp_path / "delete_me.txt"
        test_file.write_text("temporary")

        ws.delete_file("delete_me.txt")

        assert not test_file.exists()

    def test_delete_directory(self, tmp_path):
        """Should delete a directory and contents."""
        ws = Workspace.attach(tmp_path)

        # Create directory with files
        (tmp_path / "remove_me").mkdir()
        (tmp_path / "remove_me" / "file.txt").write_text("a")

        ws.delete_file("remove_me", recursive=True)

        assert not (tmp_path / "remove_me").exists()

    def test_move_file(self, tmp_path):
        """Should move/rename a file."""
        ws = Workspace.attach(tmp_path)

        (tmp_path / "old.txt").write_text("content")

        ws.move_file("old.txt", "new.txt")

        assert not (tmp_path / "old.txt").exists()
        assert (tmp_path / "new.txt").read_text() == "content"

    def test_edit_file(self, tmp_path):
        """Should edit file by replacing text."""
        ws = Workspace.attach(tmp_path)

        (tmp_path / "code.py").write_text("def foo():\n    return 'old'\n")

        ws.edit_file("code.py", old_text="'old'", new_text="'new'")

        assert "'new'" in (tmp_path / "code.py").read_text()
        assert "'old'" not in (tmp_path / "code.py").read_text()

    def test_edit_file_specific_occurrence(self, tmp_path):
        """Should edit only specific occurrence."""
        ws = Workspace.attach(tmp_path)

        (tmp_path / "data.txt").write_text("foo\nfoo\nfoo\n")

        ws.edit_file("data.txt", old_text="foo", new_text="bar", occurrence=2)

        content = (tmp_path / "data.txt").read_text()
        lines = content.strip().split("\n")

        assert lines[0] == "foo"
        assert lines[1] == "bar"
        assert lines[2] == "foo"


class TestWorkspaceMetadata:
    """Test workspace metadata and state management."""

    def test_workspace_has_created_at(self, tmp_path):
        """Should track creation time."""
        ws = Workspace.attach(tmp_path)

        assert ws.created_at is not None
        assert isinstance(ws.created_at, str)  # ISO format

    def test_workspace_has_description(self, tmp_path):
        """Should store description."""
        ws = Workspace.attach(tmp_path, description="Test workspace")

        assert ws.description == "Test workspace"

    def test_workspace_saves_metadata(self, tmp_path):
        """Should persist metadata to disk."""
        ws1 = Workspace.attach(tmp_path, description="Original")
        ws1.save_metadata()

        # Load from same directory
        ws2 = Workspace.attach(tmp_path)

        assert ws2.description == "Original"
        assert ws2.created_at == ws1.created_at
