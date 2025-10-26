"""Tests for patch path prefix detection and -p level inference (sandboxed)."""

import pytest
from pathlib import Path

@pytest.mark.unit
class TestPatchFilePathDetection:
    async def test_patch_level_p1_detected_for_a_b_prefix(self, sandbox_ws):
        from a2ia.tools.filesystem_tools import patch_file

        target = sandbox_ws.path / "sample.txt"
        target.write_text("old line\n")

        diff = """--- a/sample.txt
+++ b/sample.txt
@@ -1 +1 @@
-old line
+new line
"""

        result = await patch_file("sample.txt", diff)
        assert result.get("success"), f"Expected success, got {result}"
        assert "new line" in target.read_text()

    async def test_patch_level_p0_detected_for_no_prefix(self, sandbox_ws):
        from a2ia.tools.filesystem_tools import patch_file

        target = sandbox_ws.path / "plain.txt"
        target.write_text("hello\n")

        diff = """--- plain.txt
+++ plain.txt
@@ -1 +1 @@
-hello
+world
"""

        result = await patch_file("plain.txt", diff)
        assert result.get("success"), f"Expected success, got {result}"
        assert "world" in target.read_text()

    async def test_patch_mismatched_prefix_raises_error(self, sandbox_ws):
        from a2ia.tools.filesystem_tools import patch_file

        target = sandbox_ws.path / "bad.txt"
        target.write_text("content\n")

        diff = """--- a/foo.txt
+++ c/bar.txt
@@ -1 +1 @@
-content
+broken
"""

        result = await patch_file("bad.txt", diff)
        assert not result.get("success"), "Expected failure for mismatched prefixes"
        assert "Invalid diff format" in result.get("error", ""), result

    async def test_patch_missing_header_lines_raises_error(self, sandbox_ws):
        from a2ia.tools.filesystem_tools import patch_file

        target = sandbox_ws.path / "missing.txt"
        target.write_text("foo\n")

        diff = "@@ -1 +1 @@\n-foo\n+bar\n"

        result = await patch_file("missing.txt", diff)
        assert not result.get("success"), "Expected failure for missing headers"
        assert "Invalid diff format" in result.get("error", ""), result