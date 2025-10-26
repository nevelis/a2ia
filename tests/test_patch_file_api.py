import asyncio
import subprocess
from pathlib import Path
from unittest.mock import patch
from a2ia.tools import filesystem_tools

def _make_workspace(tmp_path: Path, rel_path: str, initial: str = "") -> Path:
    ws_root = tmp_path / "workspace"
    ws_root.mkdir(exist_ok=True)
    target = ws_root / rel_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(initial)
    return ws_root

async def invoke_patch(rel_path: str, diff: str):
    return await filesystem_tools.patch_file(rel_path, diff)

def _sandboxed_patch_factory(ws_root, captured):
    real_run = subprocess.run  # keep a reference to the real one
    def sandboxed_run(args, **kwargs):
        kwargs["cwd"] = ws_root  # force safe workspace directory
        captured.append((args, kwargs))
        return real_run(args, **kwargs)  # use real subprocess.run to avoid recursion
    return sandboxed_run

def test_patch_file_api_sandboxed_empty_file(tmp_path):
    rel_path = "a2ia/test_empty.txt"
    diff = """--- a/test_empty.txt
+++ b/test_empty.txt
@@ -0,0 +1,2 @@
+hello
+world"""

    ws_root = _make_workspace(tmp_path, rel_path)
    captured = []

    with patch("a2ia.tools.filesystem_tools.subprocess.run", side_effect=_sandboxed_patch_factory(ws_root, captured)):
        result = asyncio.run(invoke_patch(rel_path, diff))

    assert result["success"], result
    assert any("patch" in call[0][0] for call in captured)
    abs_path = ws_root / rel_path
    assert abs_path.read_text().strip().endswith("world")

def test_patch_file_api_sandboxed_middle(tmp_path):
    rel_path = "a2ia/test_middle.txt"
    initial = """one
two
three
"""
    diff = """--- a/test_middle.txt
+++ b/test_middle.txt
@@ -2 +2 @@
-two
+TWO"""

    ws_root = _make_workspace(tmp_path, rel_path, initial)
    captured = []

    with patch("a2ia.tools.filesystem_tools.subprocess.run", side_effect=_sandboxed_patch_factory(ws_root, captured)):
        result = asyncio.run(invoke_patch(rel_path, diff))

    assert result["success"], result
    assert any("patch" in call[0][0] for call in captured)
    abs_path = ws_root / rel_path
    content = abs_path.read_text()
    assert "TWO" in content
    assert "one" in content and "three" in content

def test_patch_file_api_sandboxed_end(tmp_path):
    rel_path = "a2ia/test_end.txt"
    initial = """a
b
"""
    diff = """--- a/test_end.txt
+++ b/test_end.txt
@@ -2,0 +3 @@
+c"""

    ws_root = _make_workspace(tmp_path, rel_path, initial)
    captured = []

    with patch("a2ia.tools.filesystem_tools.subprocess.run", side_effect=_sandboxed_patch_factory(ws_root, captured)):
        result = asyncio.run(invoke_patch(rel_path, diff))

    assert result["success"], result
    abs_path = ws_root / rel_path
    assert abs_path.read_text().strip().endswith("c")

def test_patch_file_api_sandboxed_two_hunks(tmp_path):
    rel_path = "a2ia/test_twohunks.txt"
    initial = """a
b
c
d
"""
    diff = """--- a/test_twohunks.txt
+++ b/test_twohunks.txt
@@ -1 +1 @@
-a
+A
@@ -4 +4 @@
-d
+D"""

    ws_root = _make_workspace(tmp_path, rel_path, initial)
    captured = []

    with patch("a2ia.tools.filesystem_tools.subprocess.run", side_effect=_sandboxed_patch_factory(ws_root, captured)):
        result = asyncio.run(invoke_patch(rel_path, diff))

    assert result["success"], result
    abs_path = ws_root / rel_path
    content = abs_path.read_text().strip().splitlines()
    assert content[0] == "A"
    assert content[-1] == "D"