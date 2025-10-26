import pytest
from a2ia.tools import filesystem_tools as fs

@pytest.mark.unit
class TestFileUtils:

    async def test_head_default(self, tmp_path):
        file_path = tmp_path / "sample.txt"
        file_path.write_text("\n".join([f"line {i}" for i in range(1, 21)]))

        result = await fs.head(str(file_path))
        assert result["success"]
        assert len(result["lines"]) == 10
        assert result["lines"][0] == "line 1"

    async def test_head_custom_count(self, tmp_path):
        file_path = tmp_path / "sample.txt"
        file_path.write_text("\n".join([f"line {i}" for i in range(1, 21)]))

        result = await fs.head(str(file_path), lines=5)
        assert result["success"]
        assert len(result["lines"]) == 5
        assert result["lines"][-1] == "line 5"

    async def test_tail_default(self, tmp_path):
        file_path = tmp_path / "sample.txt"
        file_path.write_text("\n".join([f"line {i}" for i in range(1, 21)]))

        result = await fs.tail(str(file_path))
        assert result["success"]
        assert len(result["lines"]) == 10
        assert result["lines"][-1] == "line 20"

    async def test_grep_simple(self, tmp_path):
        file_path = tmp_path / "grep.txt"
        file_path.write_text("apple\nbanana\napple pie\ncarrot\n")

        result = await fs.grep("apple", str(file_path))
        assert result["success"]
        assert result["count"] == 2
        assert "apple" in result["content"]

    async def test_grep_regex(self, tmp_path):
        file_path = tmp_path / "grep_regex.txt"
        file_path.write_text("foo123\nbar456\nfoo789\n")

        result = await fs.grep("foo[0-9]+", str(file_path), regex=True)
        assert result["success"]
        assert result["count"] == 2
        assert "foo123" in result["content"]

    async def test_grep_directory(self, tmp_path):
        (tmp_path / "dir").mkdir()
        (tmp_path / "dir" / "a.txt").write_text("apple\n")
        (tmp_path / "dir" / "b.txt").write_text("banana\n")

        result = await fs.grep("a", str(tmp_path), recursive=True)
        assert result["success"]
        assert result["count"] >= 2