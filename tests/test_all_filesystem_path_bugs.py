"""Comprehensive tests for ALL filesystem path resolution edge cases.

Tests should FAIL until we fix resolve_path to handle:
1. Workspace-relative paths: /file.txt → workspace/file.txt
2. Absolute paths within workspace: /full/workspace/path/file.txt → /full/workspace/path/file.txt
3. Absolute paths outside workspace: Should be rejected or handled safely
"""

import pytest
import tempfile
from pathlib import Path
from a2ia.workspace import Workspace


class TestFilesystemPathEdgeCases:
    """Test all edge cases for filesystem path resolution."""
    
    def test_resolve_path_with_workspace_absolute_path(self):
        """Test that absolute paths within workspace are handled correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ws = Workspace(tmpdir)
            
            # Create a test file
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("content")
            
            # When LLM provides absolute filesystem path within workspace
            absolute_path = str(test_file)
            resolved = ws.resolve_path(absolute_path)
            
            # Should resolve to the actual file, not double-path
            assert resolved == test_file
            assert resolved.exists()
            assert not str(resolved).count(tmpdir) > 1, \
                f"Path contains workspace dir multiple times: {resolved}"
    
    def test_resolve_path_workspace_relative_with_slash(self):
        """Test that /file.txt resolves to workspace/file.txt."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ws = Workspace(tmpdir)
            
            resolved = ws.resolve_path("/test.txt")
            expected = Path(tmpdir) / "test.txt"
            
            assert resolved == expected
    
    def test_resolve_path_workspace_relative_without_slash(self):
        """Test that file.txt resolves to workspace/file.txt."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ws = Workspace(tmpdir)
            
            resolved = ws.resolve_path("test.txt")
            expected = Path(tmpdir) / "test.txt"
            
            assert resolved == expected
    
    def test_read_file_with_absolute_workspace_path(self):
        """Test ReadFile with absolute path within workspace."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ws = Workspace(tmpdir)
            
            # Create a test file
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("Hello, World!")
            
            # Read using absolute filesystem path
            content = ws.read_file(str(test_file))
            assert content == "Hello, World!"
    
    def test_write_file_with_absolute_workspace_path(self):
        """Test WriteFile with absolute path within workspace."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ws = Workspace(tmpdir)
            
            # Write using absolute filesystem path
            test_file = Path(tmpdir) / "test.txt"
            ws.write_file(str(test_file), "Test content")
            
            # Verify
            assert test_file.exists()
            assert test_file.read_text() == "Test content"
            
            # Should NOT create double path
            double_path = Path(tmpdir) / tmpdir.lstrip('/') / "test.txt"
            assert not double_path.exists(), \
                f"Double path was created: {double_path}"
    
    def test_append_file_with_absolute_workspace_path(self):
        """Test AppendFile with absolute path within workspace."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ws = Workspace(tmpdir)
            
            # Create initial file
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("Line 1\n")
            
            # Append using absolute filesystem path
            ws.append_file(str(test_file), "Line 2\n")
            
            # Verify
            assert test_file.read_text() == "Line 1\nLine 2\n"
    
    def test_delete_file_with_absolute_workspace_path(self):
        """Test DeleteFile with absolute path within workspace."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ws = Workspace(tmpdir)
            
            # Create a test file
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("Delete me")
            
            # Delete using absolute filesystem path
            result = ws.delete_file(str(test_file))
            
            # Verify
            assert result["success"]
            assert not test_file.exists()
    
    def test_move_file_with_absolute_workspace_paths(self):
        """Test MoveFile with absolute paths within workspace."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ws = Workspace(tmpdir)
            
            # Create source file
            src_file = Path(tmpdir) / "source.txt"
            src_file.write_text("Move me")
            
            # Move using absolute filesystem paths
            dst_file = Path(tmpdir) / "dest.txt"
            result = ws.move_file(str(src_file), str(dst_file))
            
            # Verify
            assert result["success"]
            assert not src_file.exists()
            assert dst_file.exists()
            assert dst_file.read_text() == "Move me"
    
    def test_all_path_types_work_consistently(self):
        """Test that all path types work for read operations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ws = Workspace(tmpdir)
            
            # Create a test file
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("Consistent content")
            
            # Test all path formats
            path_formats = [
                str(test_file),  # Absolute filesystem path
                "/test.txt",     # Workspace-relative with /
                "test.txt",      # Workspace-relative without /
            ]
            
            for path_format in path_formats:
                content = ws.read_file(path_format)
                assert content == "Consistent content", \
                    f"Failed for path format: {path_format}"
    
    def test_nested_paths_with_absolute_workspace_path(self):
        """Test nested paths with absolute filesystem paths."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ws = Workspace(tmpdir)
            
            # Create nested structure
            nested_dir = Path(tmpdir) / "subdir" / "nested"
            nested_dir.mkdir(parents=True)
            test_file = nested_dir / "test.txt"
            test_file.write_text("Nested content")
            
            # Read using absolute filesystem path
            content = ws.read_file(str(test_file))
            assert content == "Nested content"
            
            # Verify no double-pathing
            resolved = ws.resolve_path(str(test_file))
            assert resolved == test_file
            assert str(resolved).count(str(tmpdir)) == 1, \
                f"Workspace dir appears multiple times in: {resolved}"

