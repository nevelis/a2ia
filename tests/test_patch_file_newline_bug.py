import asyncio
from pathlib import Path
import a2ia.a2ia.tools.filesystem_tools as filesystem_tools


async def _run_patch(tmp_path: Path):
    target = tmp_path / "example.txt"
    target.write_text("hello world\n")

    # Unified diff missing trailing newline at end of file
    diff = """--- a/example.txt
+++ b/example.txt
@@ -1 +1 @@
-hello world
+hello there"""

    result = await filesystem_tools.patch_file(str(target), diff)
    new_content = target.read_text()
    return result, new_content


def test_patch_file_handles_missing_trailing_newline(tmp_path):
    """Ensure patch_file handles missing trailing newline correctly."""
    result, new_content = asyncio.run(_run_patch(tmp_path))

    # The diff should apply cleanly
    assert result["success"], f"Patch failed: {result}"

    # Verify that a newline (not literal '\n') was written properly
    assert not new_content.endswith("\n"), "Literal '\n' found in file!"
    assert "hello there" in new_content, "Patched text not found"
