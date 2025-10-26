import asyncio
from pathlib import Path
import pytest
import a2ia.tools.filesystem_tools as filesystem_tools

def _mock_workspace(tmp_path: Path):
    class MockWorkspace:
        def resolve_path(self, rel_path: str) -> str:
            return str(tmp_path / rel_path)
    return MockWorkspace()

@pytest.fixture(autouse=True)
def mock_workspace(tmp_path, monkeypatch):
    # Automatically override get_workspace for all tests
    monkeypatch.setattr(filesystem_tools, "get_workspace", lambda: _mock_workspace(tmp_path))

def _make_workspace(tmp_path: Path, rel_path: str, initial: str = "") -> Path:
    target = tmp_path / rel_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(initial)
    return tmp_path

async def invoke_patch(rel_path: str, diff: str):
    return await filesystem_tools.patch_file(rel_path, diff)

# --- Existing tests ---

def test_patch_file_api_sandboxed_empty_file(tmp_path):
    rel_path = "a2ia/test_empty.txt"
    diff = """--- a/test_empty.txt
+++ b/test_empty.txt
@@ -0,0 +1,2 @@
+hello
+world"""

    _make_workspace(tmp_path, rel_path)
    result = asyncio.run(invoke_patch(rel_path, diff))
    abs_path = tmp_path / rel_path
    assert result["success"]
    assert abs_path.read_text().strip().endswith("world")

def test_patch_file_api_sandboxed_middle(tmp_path):
    rel_path = "a2ia/test_middle.txt"
    initial = "one\ntwo\nthree\n"
    diff = """--- a/test_middle.txt
+++ b/test_middle.txt
@@ -2 +2 @@
-two
+TWO"""

    _make_workspace(tmp_path, rel_path, initial)
    result = asyncio.run(invoke_patch(rel_path, diff))
    abs_path = tmp_path / rel_path
    content = abs_path.read_text()
    assert result["success"]
    assert "TWO" in content
    assert "one" in content and "three" in content

def test_patch_file_api_sandboxed_end(tmp_path):
    rel_path = "a2ia/test_end.txt"
    initial = "a\nb\n"
    diff = """--- a/test_end.txt
+++ b/test_end.txt
@@ -2,0 +3 @@
+c"""

    _make_workspace(tmp_path, rel_path, initial)
    result = asyncio.run(invoke_patch(rel_path, diff))
    abs_path = tmp_path / rel_path
    assert result["success"]
    assert abs_path.read_text().strip().endswith("c")

def test_patch_file_api_sandboxed_two_hunks(tmp_path):
    rel_path = "a2ia/test_twohunks.txt"
    initial = "a\nb\nc\nd\n"
    diff = """--- a/test_twohunks.txt
+++ b/test_twohunks.txt
@@ -1 +1 @@
-a
+A
@@ -4 +4 @@
-d
+D"""

    _make_workspace(tmp_path, rel_path, initial)
    result = asyncio.run(invoke_patch(rel_path, diff))
    abs_path = tmp_path / rel_path
    content = abs_path.read_text().strip().splitlines()
    assert result["success"]
    assert content[0] == "A"
    assert content[-1] == "D"

# --- Context-aware tests ---

def test_patch_file_with_context_lines(tmp_path):
    rel_path = "a2ia/test_context.txt"
    initial = "alpha\nbravo\ncharlie\n"
    diff = """--- a/test_context.txt
+++ b/test_context.txt
@@ -1,3 +1,3 @@
 alpha
-bravo
+BRAVO
 charlie"""

    _make_workspace(tmp_path, rel_path, initial)
    result = asyncio.run(invoke_patch(rel_path, diff))
    abs_path = tmp_path / rel_path
    content = abs_path.read_text().splitlines()
    assert result["success"]
    assert "BRAVO" in content
    assert "bravo" not in content

def test_patch_file_without_context_lines(tmp_path):
    rel_path = "a2ia/test_nocontext.txt"
    initial = "one\ntwo\nthree\n"
    diff = """--- a/test_nocontext.txt
+++ b/test_nocontext.txt
@@ -2 +2 @@
-two
+TWO"""

    _make_workspace(tmp_path, rel_path, initial)
    result = asyncio.run(invoke_patch(rel_path, diff))
    abs_path = tmp_path / rel_path
    assert result["success"]
    assert "TWO" in abs_path.read_text()

def test_patch_file_context_mismatch(tmp_path):
    rel_path = "a2ia/test_mismatch.txt"
    initial = "apple\nbanana\ncarrot\n"
    diff = """--- a/test_mismatch.txt
+++ b/test_mismatch.txt
@@ -1,3 +1,3 @@
 apple
-banana
+BANANA
 pear"""

    _make_workspace(tmp_path, rel_path, initial)
    result = asyncio.run(invoke_patch(rel_path, diff))
    assert not result["success"]
    assert "context mismatch" in result["stderr"]

def test_patch_file_missing_final_newline(tmp_path):
    rel_path = "a2ia/test_nonewline.txt"
    initial = "red\ngreen\nblue"  # no trailing newline
    diff = """--- a/test_nonewline.txt
+++ b/test_nonewline.txt
@@ -3 +3 @@
-blue
+BLUE"""

    _make_workspace(tmp_path, rel_path, initial)
    result = asyncio.run(invoke_patch(rel_path, diff))
    abs_path = tmp_path / rel_path
    text = abs_path.read_text()
    assert result["success"]
    assert text.endswith("\n")
    assert "BLUE" in text