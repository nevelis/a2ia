"""Test workspace path resolution - ensure '/' paths are relative to workspace root."""

import pytest
import tempfile
import os
from pathlib import Path
from a2ia.workspace import Workspace


class TestWorkspacePathResolution:
    """Test that paths starting with '/' are resolved relative to workspace root."""
    
    def test_absolute_path_resolves_to_workspace_root(self):
        """Test that /file.txt resolves to workspace_root/file.txt, not /file.txt."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ws = Workspace(tmpdir)
            
            # Test with leading slash
            resolved = ws.resolve_path("/get_weather.py")
            expected = Path(tmpdir) / "get_weather.py"
            
            assert resolved == expected
            assert str(resolved).startswith(tmpdir)
            # Should NOT resolve to filesystem root
            assert resolved != Path("/get_weather.py")
    
    def test_nested_absolute_path_resolves_correctly(self):
        """Test that /subdir/file.txt resolves to workspace_root/subdir/file.txt."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ws = Workspace(tmpdir)
            
            # Test with nested path
            resolved = ws.resolve_path("/workspace/code.py")
            expected = Path(tmpdir) / "workspace" / "code.py"
            
            assert resolved == expected
            assert str(resolved).startswith(tmpdir)
    
    def test_relative_path_still_works(self):
        """Test that relative paths (without leading /) still work."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ws = Workspace(tmpdir)
            
            # Test without leading slash
            resolved = ws.resolve_path("get_weather.py")
            expected = Path(tmpdir) / "get_weather.py"
            
            assert resolved == expected
    
    def test_dot_relative_path_works(self):
        """Test that './file.txt' works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ws = Workspace(tmpdir)
            
            resolved = ws.resolve_path("./get_weather.py")
            expected = Path(tmpdir) / "get_weather.py"
            
            assert resolved == expected
    
    def test_read_file_with_absolute_path(self):
        """Test that read_file works with paths starting with /."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ws = Workspace(tmpdir)
            
            # Create a test file
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("Hello, World!")
            
            # Read using absolute-style path
            content = ws.read_file("/test.txt")
            assert content == "Hello, World!"
    
    def test_write_file_with_absolute_path(self):
        """Test that write_file works with paths starting with /."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ws = Workspace(tmpdir)
            
            # Write using absolute-style path
            ws.write_file("/new_file.txt", "Test content")
            
            # Verify file was created in workspace root
            expected_path = Path(tmpdir) / "new_file.txt"
            assert expected_path.exists()
            assert expected_path.read_text() == "Test content"
    
    def test_list_directory_with_absolute_path(self):
        """Test that list_directory works with paths starting with /."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ws = Workspace(tmpdir)
            
            # Create test files
            (Path(tmpdir) / "file1.txt").write_text("content1")
            (Path(tmpdir) / "file2.txt").write_text("content2")
            
            # List using absolute-style path
            result = ws.list_directory("/")
            
            assert result["success"]
            assert len(result["files"]) >= 2
            # Files should be workspace-relative, not absolute paths
            for file_path in result["files"]:
                assert not file_path.startswith('/'), f"Path should be relative: {file_path}"
                assert file_path in ["file1.txt", "file2.txt"]
    
    def test_list_directory_returns_relative_paths(self):
        """Test that list_directory always returns workspace-relative paths."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ws = Workspace(tmpdir)
            
            # Create nested structure
            (Path(tmpdir) / "root.txt").write_text("root")
            (Path(tmpdir) / "subdir").mkdir()
            (Path(tmpdir) / "subdir" / "nested.txt").write_text("nested")
            
            # List non-recursive
            result = ws.list_directory(".")
            assert result["success"]
            for file_path in result["files"]:
                assert not file_path.startswith('/'), f"Should be relative: {file_path}"
                assert not file_path.startswith(tmpdir), f"Should not contain tmpdir: {file_path}"
            
            # List recursive
            result = ws.list_directory(".", recursive=True)
            assert result["success"]
            assert len(result["files"]) == 2
            for file_path in result["files"]:
                assert not file_path.startswith('/'), f"Should be relative: {file_path}"
                assert not file_path.startswith(tmpdir), f"Should not contain tmpdir: {file_path}"
            
            # Verify specific paths
            file_paths = result["files"]
            assert "root.txt" in file_paths
            assert "subdir/nested.txt" in file_paths

