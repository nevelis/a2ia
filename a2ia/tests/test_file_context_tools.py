import pytest
import os
from a2ia.tools import filesystem_tools as fs

@pytest.mark.asyncio
async def test_grep_before_after_lines(tmp_path):
    test_file = tmp_path / "example.txt"
    content = """line1
context-before
pattern-line
context-after
line5
"""
    test_file.write_text(content)

    result = await fs.grep("pattern-line", str(test_file), before_lines=1, after_lines=1)
    assert result["success"]
    matched_lines = [m["text"] for m in result["matches"]]
    assert any("pattern-line" in t for t in matched_lines)

@pytest.mark.asyncio
async def test_head_n_lines(tmp_path):
    test_file = tmp_path / "headtest.txt"
    content = "\n".join([f"line {i}" for i in range(1, 21)])
    test_file.write_text(content)

    result = await fs.head(str(test_file), lines=5)
    assert result["success"]
    assert len(result["lines"]) == 5
    assert result["lines"][0] == "line 1"

@pytest.mark.asyncio
async def test_tail_n_lines(tmp_path):
    test_file = tmp_path / "tailtest.txt"
    content = "\n".join([f"line {i}" for i in range(1, 21)])
    test_file.write_text(content)

    result = await fs.tail(str(test_file), lines=5)
    assert result["success"]
    assert len(result["lines"]) == 5
    assert result["lines"][-1] == "line 20"