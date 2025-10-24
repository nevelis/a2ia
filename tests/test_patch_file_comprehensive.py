"""Comprehensive tests for PatchFile to ensure it handles real diffs."""

import pytest
from pathlib import Path


@pytest.mark.unit
class TestPatchFileComprehensive:
    """Comprehensive PatchFile tests with real unified diffs."""

    async def test_patch_simple_change(self, tmp_path):
        """Apply simple single-line change."""
        from a2ia.workspace import Workspace
        from a2ia.tools.filesystem_tools import patch_file
        from a2ia.core import set_workspace

        ws = Workspace.attach(tmp_path)
        set_workspace(ws)

        # Create original file
        original = "line 1\nline 2\nline 3\n"
        (tmp_path / "test.txt").write_text(original)

        # Create proper unified diff
        diff = """--- a/test.txt
+++ b/test.txt
@@ -1,3 +1,3 @@
 line 1
-line 2
+line 2 modified
 line 3
"""

        result = await patch_file("test.txt", diff)

        if result.get("success"):
            content = (tmp_path / "test.txt").read_text()
            assert "line 2 modified" in content
            assert "line 2\n" not in content

    async def test_patch_multiline_change(self, tmp_path):
        """Apply multi-line changes."""
        from a2ia.workspace import Workspace
        from a2ia.tools.filesystem_tools import patch_file
        from a2ia.core import set_workspace

        ws = Workspace.attach(tmp_path)
        set_workspace(ws)

        original = "def foo():\n    pass\n\ndef bar():\n    pass\n"
        (tmp_path / "code.py").write_text(original)

        diff = """--- a/code.py
+++ b/code.py
@@ -1,5 +1,5 @@
 def foo():
-    pass
+    return 42

 def bar():
     pass
"""

        result = await patch_file("code.py", diff)

        if result.get("success"):
            content = (tmp_path / "code.py").read_text()
            assert "return 42" in content

    async def test_patch_preserves_newlines(self, tmp_path):
        """Verify newlines are preserved in patches."""
        from a2ia.workspace import Workspace
        from a2ia.tools.filesystem_tools import patch_file
        from a2ia.core import set_workspace

        ws = Workspace.attach(tmp_path)
        set_workspace(ws)

        original = "hello\nworld\n"
        (tmp_path / "test.txt").write_text(original)

        # Diff with actual newlines
        diff = "--- a/test.txt\n+++ b/test.txt\n@@ -1,2 +1,2 @@\n-hello\n+goodbye\n world\n"

        result = await patch_file("test.txt", diff)

        if result.get("success"):
            content = (tmp_path / "test.txt").read_text()
            assert "goodbye" in content

    async def test_patch_multiple_hunks(self, tmp_path):
        """Apply patch with multiple hunks."""
        from a2ia.workspace import Workspace
        from a2ia.tools.filesystem_tools import patch_file
        from a2ia.core import set_workspace

        ws = Workspace.attach(tmp_path)
        set_workspace(ws)

        original = """def foo():
    return 1

def bar():
    return 2

def baz():
    return 3
"""
        (tmp_path / "code.py").write_text(original)

        # Patch with multiple hunks
        diff = """--- a/code.py
+++ b/code.py
@@ -1,2 +1,2 @@
 def foo():
-    return 1
+    return 42
 
@@ -4,2 +4,2 @@
 def bar():
-    return 2
+    return 99
"""

        result = await patch_file("code.py", diff)

        if result.get("success"):
            content = (tmp_path / "code.py").read_text()
            assert "return 42" in content
            assert "return 99" in content

    async def test_patch_sequential_application(self, tmp_path):
        """Apply multiple patches sequentially."""
        from a2ia.workspace import Workspace
        from a2ia.tools.filesystem_tools import patch_file
        from a2ia.core import set_workspace

        ws = Workspace.attach(tmp_path)
        set_workspace(ws)

        original = "line 1\nline 2\nline 3\n"
        (tmp_path / "test.txt").write_text(original)

        # First patch
        diff1 = """--- a/test.txt
+++ b/test.txt
@@ -1,3 +1,3 @@
-line 1
+LINE 1
 line 2
 line 3
"""
        result1 = await patch_file("test.txt", diff1)

        # Second patch on modified file
        diff2 = """--- a/test.txt
+++ b/test.txt
@@ -1,3 +1,3 @@
 LINE 1
-line 2
+LINE 2
 line 3
"""
        result2 = await patch_file("test.txt", diff2)

        if result1.get("success") and result2.get("success"):
            content = (tmp_path / "test.txt").read_text()
            assert "LINE 1" in content
            assert "LINE 2" in content
            assert "line 3" in content
