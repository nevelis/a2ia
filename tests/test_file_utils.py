"""Tests for file utility tools (Head, Tail, Grep)."""

import pytest
from pathlib import Path


@pytest.mark.unit
class TestFileUtils:
    """Test file utility tools."""

    async def test_head_default(self, tmp_path):
        """Head returns first 10 lines by default."""
        from a2ia.workspace import Workspace
        from a2ia.tools.filesystem_tools import head
        from a2ia.core import set_workspace

        ws = Workspace.attach(tmp_path)
        set_workspace(ws)

        # Create file with 20 lines
        lines = "\n".join(f"line {i}" for i in range(1, 21))
        (tmp_path / "test.txt").write_text(lines)

        result = await head("test.txt")

        assert "line 1" in result["content"]
        assert "line 10" in result["content"]
        assert "line 11" not in result["content"]
        assert result["lines"] == 10

    async def test_head_custom_count(self, tmp_path):
        """Head with custom line count."""
        from a2ia.workspace import Workspace
        from a2ia.tools.filesystem_tools import head
        from a2ia.core import set_workspace

        ws = Workspace.attach(tmp_path)
        set_workspace(ws)

        lines = "\n".join(f"line {i}" for i in range(1, 21))
        (tmp_path / "test.txt").write_text(lines)

        result = await head("test.txt", lines=5)

        assert result["lines"] == 5
        assert "line 5" in result["content"]
        assert "line 6" not in result["content"]

    async def test_tail_default(self, tmp_path):
        """Tail returns last 10 lines by default."""
        from a2ia.workspace import Workspace
        from a2ia.tools.filesystem_tools import tail
        from a2ia.core import set_workspace

        ws = Workspace.attach(tmp_path)
        set_workspace(ws)

        lines = "\n".join(f"line {i}" for i in range(1, 21))
        (tmp_path / "test.txt").write_text(lines)

        result = await tail("test.txt")

        assert "line 11" in result["content"]
        assert "line 20" in result["content"]
        assert "line 10" not in result["content"]
        assert result["lines"] == 10

    async def test_grep_simple(self, tmp_path):
        """Grep finds matching lines."""
        from a2ia.workspace import Workspace
        from a2ia.tools.filesystem_tools import grep
        from a2ia.core import set_workspace

        ws = Workspace.attach(tmp_path)
        set_workspace(ws)

        content = "hello world\nfoo bar\nhello again\nbaz"
        (tmp_path / "test.txt").write_text(content)

        result = await grep("hello", "test.txt")

        assert result["matches"] == 2
        assert "hello world" in result["lines"][0]
        assert "hello again" in result["lines"][1]

    async def test_grep_regex(self, tmp_path):
        """Grep with regex pattern."""
        from a2ia.workspace import Workspace
        from a2ia.tools.filesystem_tools import grep
        from a2ia.core import set_workspace

        ws = Workspace.attach(tmp_path)
        set_workspace(ws)

        content = "test123\ntest456\nfoo789\ntest"
        (tmp_path / "test.txt").write_text(content)

        result = await grep(r"test\d+", "test.txt", regex=True)

        assert result["matches"] == 2
        assert "test123" in result["lines"][0]
        assert "test456" in result["lines"][1]

    async def test_grep_directory(self, tmp_path):
        """Grep across multiple files in directory."""
        from a2ia.workspace import Workspace
        from a2ia.tools.filesystem_tools import grep
        from a2ia.core import set_workspace

        ws = Workspace.attach(tmp_path)
        set_workspace(ws)

        (tmp_path / "file1.txt").write_text("hello world")
        (tmp_path / "file2.txt").write_text("foo bar")
        (tmp_path / "file3.txt").write_text("hello again")

        result = await grep("hello", ".", recursive=True)

        assert result["matches"] >= 2
        assert len(result["files"]) >= 2
