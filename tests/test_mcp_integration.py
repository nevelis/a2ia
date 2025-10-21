"""Integration tests for MCP tools.

Tests MCP tools directly by calling them as functions.
"""

import shutil
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_workspace_root(monkeypatch):
    """Create a temporary workspace root directory and clear workspace state."""
    from a2ia.core import clear_workspace

    # Clear any existing workspace state
    clear_workspace()

    temp_dir = tempfile.mkdtemp(prefix="a2ia_mcp_test_")
    monkeypatch.setenv("A2IA_WORKSPACE_ROOT", temp_dir)
    yield temp_dir

    # Clean up
    clear_workspace()
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.mark.integration
class TestMCPWorkspaceTools:
    """Test MCP workspace management tools."""

    async def test_create_workspace(self, temp_workspace_root):
        """Get persistent workspace info via MCP tool."""
        from a2ia.tools.workspace_tools import create_workspace

        result = await create_workspace()
        assert "workspace_id" in result
        assert "path" in result
        # Persistent workspace has fixed ID
        assert Path(result["path"]).exists()

    async def test_create_workspace_with_description(self, temp_workspace_root):
        """Description parameter ignored with persistent workspace."""
        from a2ia.tools.workspace_tools import create_workspace

        result = await create_workspace(description="Test MCP workspace")
        # Description is fixed for persistent workspace
        assert result["description"] == "A2IA Persistent Workspace"

    async def test_create_workspace_with_id(self, temp_workspace_root):
        """Workspace ID parameter ignored with persistent workspace."""
        from a2ia.tools.workspace_tools import create_workspace

        result = await create_workspace(workspace_id="ws_custom_123")
        # With persistent workspace, the ID is always "workspace"
        assert "workspace_id" in result

    async def test_resume_workspace(self, temp_workspace_root):
        """Persistent workspace doesn't need resuming."""
        from a2ia.tools.workspace_tools import create_workspace

        # All calls return the same persistent workspace
        result1 = await create_workspace(workspace_id="ws_resume_test")
        result2 = await create_workspace(workspace_id="different")

        # Both return the same workspace
        assert result1["workspace_id"] == result2["workspace_id"]

    async def test_get_workspace_info(self, temp_workspace_root):
        """Get persistent workspace information."""
        from a2ia.tools.workspace_tools import get_workspace_info

        # Workspace auto-initializes, no create_workspace needed
        info = await get_workspace_info()

        assert "workspace_id" in info
        assert "path" in info
        assert "created_at" in info
        # Description is fixed for persistent workspace
        assert info["description"] == "A2IA Persistent Workspace"

    async def test_get_workspace_info_no_workspace_fails(self, temp_workspace_root):
        """Workspace auto-initializes, never fails."""
        from a2ia.tools.workspace_tools import get_workspace_info

        # This now works because workspace auto-initializes
        info = await get_workspace_info()
        assert "workspace_id" in info

    async def test_close_workspace(self, temp_workspace_root):
        """Close workspace is a no-op with persistent model."""
        from a2ia.tools.workspace_tools import close_workspace, get_workspace_info

        result = await close_workspace()
        assert result["success"] is True

        # Workspace remains active (not closed)
        info = await get_workspace_info()
        assert "workspace_id" in info


@pytest.mark.integration
class TestMCPFilesystemTools:
    """Test MCP filesystem tools."""

    async def test_list_directory(self, temp_workspace_root):
        """List directory contents."""
        from a2ia.tools.filesystem_tools import list_directory
        from a2ia.tools.workspace_tools import create_workspace

        await create_workspace()
        result = await list_directory()

        assert "files" in result
        assert "directories" in result
        assert isinstance(result["files"], list)
        assert isinstance(result["directories"], list)

    async def test_write_and_read_file(self, temp_workspace_root):
        """Write and read a file."""
        from a2ia.tools.filesystem_tools import read_file, write_file
        from a2ia.tools.workspace_tools import create_workspace

        await create_workspace()

        # Write
        write_result = await write_file("test.txt", "Hello MCP!")
        assert write_result["success"] is True
        assert write_result["path"] == "test.txt"

        # Read
        read_result = await read_file("test.txt")
        assert read_result["content"] == "Hello MCP!"
        assert read_result["path"] == "test.txt"

    async def test_write_file_with_nested_path(self, temp_workspace_root):
        """Write file with nested directories."""
        from a2ia.tools.filesystem_tools import read_file, write_file
        from a2ia.tools.workspace_tools import create_workspace

        await create_workspace()

        # Write to nested path
        await write_file("src/utils/helper.py", "# Helper module")

        # Read back
        result = await read_file("src/utils/helper.py")
        assert result["content"] == "# Helper module"

    async def test_edit_file(self, temp_workspace_root):
        """Edit file content."""
        from a2ia.tools.filesystem_tools import edit_file, read_file, write_file
        from a2ia.tools.workspace_tools import create_workspace

        await create_workspace()

        # Write initial content
        await write_file("code.py", "x = 1\ny = 2\nz = 3\n")

        # Edit
        edit_result = await edit_file("code.py", "y = 2", "y = 42")
        assert edit_result["success"] is True
        assert edit_result["changes"] == 1

        # Verify
        read_result = await read_file("code.py")
        assert "y = 42" in read_result["content"]
        assert "y = 2" not in read_result["content"]

    async def test_edit_file_multiple_occurrences(self, temp_workspace_root):
        """Edit all occurrences by default."""
        from a2ia.tools.filesystem_tools import edit_file, read_file, write_file
        from a2ia.tools.workspace_tools import create_workspace

        await create_workspace()

        # Write with duplicates
        await write_file("dup.txt", "foo\nfoo\nfoo\n")

        # Edit all
        edit_result = await edit_file("dup.txt", "foo", "bar")
        assert edit_result["changes"] == 3

        # Verify
        content = (await read_file("dup.txt"))["content"]
        assert content.count("bar") == 3
        assert "foo" not in content

    async def test_edit_file_specific_occurrence(self, temp_workspace_root):
        """Edit specific occurrence."""
        from a2ia.tools.filesystem_tools import edit_file, read_file, write_file
        from a2ia.tools.workspace_tools import create_workspace

        await create_workspace()

        # Write with duplicates
        await write_file("dup.txt", "foo\nfoo\nfoo\n")

        # Edit only second occurrence
        edit_result = await edit_file("dup.txt", "foo", "bar", occurrence=2)
        assert edit_result["changes"] == 1

        # Verify
        content = (await read_file("dup.txt"))["content"]
        lines = content.strip().split("\n")
        assert lines[0] == "foo"
        assert lines[1] == "bar"
        assert lines[2] == "foo"

    async def test_delete_file(self, temp_workspace_root):
        """Delete a file."""
        from a2ia.tools.filesystem_tools import delete_file, read_file, write_file
        from a2ia.tools.workspace_tools import create_workspace

        await create_workspace()

        # Create and delete
        await write_file("temp.txt", "temporary")
        delete_result = await delete_file("temp.txt")
        assert delete_result["success"] is True

        # Should fail to read
        with pytest.raises(FileNotFoundError):
            await read_file("temp.txt")

    async def test_delete_directory_recursive(self, temp_workspace_root):
        """Delete directory recursively."""
        from a2ia.tools.filesystem_tools import delete_file, list_directory, write_file
        from a2ia.tools.workspace_tools import create_workspace

        await create_workspace()

        # Create nested structure
        await write_file("dir/subdir/file.txt", "content")

        # Delete directory
        delete_result = await delete_file("dir", recursive=True)
        assert delete_result["success"] is True

        # Directory should be gone
        files = await list_directory()
        assert "dir" not in files["directories"]

    async def test_move_file(self, temp_workspace_root):
        """Move/rename a file."""
        from a2ia.tools.filesystem_tools import move_file, read_file, write_file
        from a2ia.tools.workspace_tools import create_workspace

        await create_workspace()

        # Create and move
        await write_file("old.txt", "data")
        move_result = await move_file("old.txt", "new.txt")
        assert move_result["success"] is True

        # Old should be gone, new should exist
        with pytest.raises(FileNotFoundError):
            await read_file("old.txt")

        new_content = await read_file("new.txt")
        assert new_content["content"] == "data"

    async def test_list_directory_recursive(self, temp_workspace_root):
        """List directory recursively."""
        from a2ia.tools.filesystem_tools import list_directory, write_file
        from a2ia.tools.workspace_tools import create_workspace

        await create_workspace()

        # Create nested structure
        await write_file("a/b/c/deep.txt", "deep content")
        await write_file("a/b/shallow.txt", "shallow")
        await write_file("top.txt", "top")

        # List recursively
        result = await list_directory(recursive=True)

        # Should include nested directories
        all_dirs = [str(d) for d in result["directories"]]
        assert any("a" in d for d in all_dirs)
        assert any("b" in d for d in all_dirs)


@pytest.mark.integration
class TestMCPShellTools:
    """Test MCP shell execution tools."""

    async def test_execute_command(self, temp_workspace_root):
        """Execute a simple command."""
        from a2ia.tools.shell_tools import execute_command
        from a2ia.tools.workspace_tools import create_workspace

        await create_workspace()

        result = await execute_command("echo 'Hello from MCP'")
        assert result["returncode"] == 0
        assert "Hello from MCP" in result["stdout"]
        assert "duration" in result

    async def test_execute_command_with_error(self, temp_workspace_root):
        """Execute command that fails."""
        from a2ia.tools.shell_tools import execute_command
        from a2ia.tools.workspace_tools import create_workspace

        await create_workspace()

        result = await execute_command("exit 1")
        assert result["returncode"] == 1

    async def test_execute_command_in_subdirectory(self, temp_workspace_root):
        """Execute command in workspace subdirectory."""
        from a2ia.tools.filesystem_tools import write_file
        from a2ia.tools.shell_tools import execute_command
        from a2ia.tools.workspace_tools import create_workspace

        await create_workspace()

        # Create subdirectory with file
        await write_file("subdir/test.txt", "content")

        # Run command in subdirectory
        result = await execute_command("ls", cwd="subdir")
        assert "test.txt" in result["stdout"]

    async def test_execute_command_with_env(self, temp_workspace_root):
        """Execute command with environment variables."""
        from a2ia.tools.shell_tools import execute_command
        from a2ia.tools.workspace_tools import create_workspace

        await create_workspace()

        result = await execute_command(
            "echo $CUSTOM_VAR", env={"CUSTOM_VAR": "test_value"}
        )
        assert "test_value" in result["stdout"]

    async def test_execute_command_captures_stderr(self, temp_workspace_root):
        """Execute command that outputs to stderr."""
        from a2ia.tools.shell_tools import execute_command
        from a2ia.tools.workspace_tools import create_workspace

        await create_workspace()

        result = await execute_command("echo 'error message' >&2")
        assert "error message" in result["stderr"]


@pytest.mark.integration
class TestMCPWorkflows:
    """Test complete MCP workflows."""

    async def test_python_development_workflow(self, temp_workspace_root):
        """Simulate a Python development workflow."""
        from a2ia.tools.filesystem_tools import list_directory, write_file
        from a2ia.tools.shell_tools import execute_command
        from a2ia.tools.workspace_tools import create_workspace

        # Get workspace info (auto-initialized)
        ws = await create_workspace(description="Python dev workflow")
        assert "workspace_id" in ws

        # Write Python files
        await write_file("main.py", "print('Hello, World!')")
        await write_file("test_main.py", "def test_main():\n    assert True")
        await write_file("requirements.txt", "pytest\n")

        # List files
        files = await list_directory()
        assert "main.py" in files["files"]
        assert "test_main.py" in files["files"]

        # Run main.py
        result = await execute_command("python3 main.py")
        assert result["returncode"] == 0
        assert "Hello, World!" in result["stdout"]

    async def test_file_editing_workflow(self, temp_workspace_root):
        """Test iterative file editing."""
        from a2ia.tools.filesystem_tools import edit_file, read_file, write_file
        from a2ia.tools.workspace_tools import create_workspace

        await create_workspace()

        # Write initial version
        await write_file("config.py", "DEBUG = False\nPORT = 8000\n")

        # Edit multiple times
        await edit_file("config.py", "DEBUG = False", "DEBUG = True")
        await edit_file("config.py", "PORT = 8000", "PORT = 3000")

        # Verify final state
        content = (await read_file("config.py"))["content"]
        assert "DEBUG = True" in content
        assert "PORT = 3000" in content

    async def test_project_scaffolding_workflow(self, temp_workspace_root):
        """Create a project structure."""
        from a2ia.tools.filesystem_tools import list_directory, write_file
        from a2ia.tools.workspace_tools import create_workspace

        await create_workspace(description="New project")

        # Create project structure
        await write_file("README.md", "# My Project\n")
        await write_file("src/__init__.py", "")
        await write_file("src/main.py", "def main():\n    pass\n")
        await write_file("tests/__init__.py", "")
        await write_file("tests/test_main.py", "def test_main():\n    pass\n")
        await write_file(".gitignore", "*.pyc\n__pycache__/\n")

        # List everything
        result = await list_directory(recursive=True)

        # Verify structure
        assert "README.md" in result["files"]
        assert ".gitignore" in result["files"]
        assert any("src" in str(d) for d in result["directories"])
        assert any("tests" in str(d) for d in result["directories"])
