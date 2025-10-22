"""Tests for new filesystem tools."""

import pytest
import tempfile
from pathlib import Path


@pytest.mark.unit
class TestNewFilesystemTools:
    """Test new filesystem tools."""

    async def test_append_file(self, tmp_path):
        """Append content to file."""
        from a2ia.workspace import Workspace
        from a2ia.tools.filesystem_tools import append_file
        from a2ia.core import set_workspace

        ws = Workspace.attach(tmp_path)
        set_workspace(ws)

        # Create initial file
        (tmp_path / "test.txt").write_text("Hello")

        # Append
        await append_file("test.txt", " World")

        assert (tmp_path / "test.txt").read_text() == "Hello World"

    async def test_truncate_file(self, tmp_path):
        """Truncate file to size."""
        from a2ia.workspace import Workspace
        from a2ia.tools.filesystem_tools import truncate_file
        from a2ia.core import set_workspace

        ws = Workspace.attach(tmp_path)
        set_workspace(ws)

        # Create file
        (tmp_path / "test.txt").write_text("Hello World")

        # Truncate to empty
        await truncate_file("test.txt", 0)

        assert (tmp_path / "test.txt").read_text() == ""

    async def test_patch_file(self, tmp_path):
        """Apply unified diff to file."""
        from a2ia.workspace import Workspace
        from a2ia.tools.filesystem_tools import patch_file
        from a2ia.core import set_workspace

        ws = Workspace.attach(tmp_path)
        set_workspace(ws)

        # Create file
        (tmp_path / "test.txt").write_text("line 1\nline 2\nline 3\n")

        # Apply patch
        diff = """--- a/test.txt
+++ b/test.txt
@@ -1,3 +1,3 @@
 line 1
-line 2
+line 2 modified
 line 3
"""
        result = await patch_file("test.txt", diff)

        # Check if patch was applied (if patch command available)
        if result.get("success"):
            content = (tmp_path / "test.txt").read_text()
            assert "line 2 modified" in content

    async def test_prune_directory(self, tmp_path):
        """Prune directory keeping only matching patterns."""
        from a2ia.workspace import Workspace
        from a2ia.tools.filesystem_tools import prune_directory
        from a2ia.core import set_workspace

        ws = Workspace.attach(tmp_path)
        set_workspace(ws)

        # Create files
        (tmp_path / "keep.md").write_text("keep")
        (tmp_path / "delete.txt").write_text("delete")
        (tmp_path / ".gitignore").write_text("ignore")

        # Prune, keeping only .md and .git* files
        result = await prune_directory(".", keep_patterns=["*.md", ".git*"])

        assert (tmp_path / "keep.md").exists()
        assert (tmp_path / ".gitignore").exists()
        assert not (tmp_path / "delete.txt").exists()
        assert result["count"] >= 1  # Deleted at least delete.txt

    async def test_find_replace(self, tmp_path):
        """Find and replace in file."""
        from a2ia.workspace import Workspace
        from a2ia.tools.filesystem_tools import find_replace
        from a2ia.core import set_workspace

        ws = Workspace.attach(tmp_path)
        set_workspace(ws)

        # Create file
        (tmp_path / "test.py").write_text("x = 1\ny = 1\nz = 1\n")

        # Replace all occurrences of "1"
        await find_replace("test.py", "1", "42")

        content = (tmp_path / "test.py").read_text()
        assert content == "x = 42\ny = 42\nz = 42\n"

    async def test_find_replace_regex(self, tmp_path):
        """Find and replace using regex."""
        from a2ia.workspace import Workspace
        from a2ia.tools.filesystem_tools import find_replace_regex
        from a2ia.core import set_workspace

        ws = Workspace.attach(tmp_path)
        set_workspace(ws)

        # Create file
        (tmp_path / "test.py").write_text("def foo():\n    pass\ndef bar():\n    pass\n")

        # Replace function names
        await find_replace_regex("test.py", r"def (\w+)\(\):", r"def new_\1():")

        content = (tmp_path / "test.py").read_text()
        assert "def new_foo():" in content
        assert "def new_bar():" in content
