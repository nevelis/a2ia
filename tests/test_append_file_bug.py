import pytest
from pathlib import Path

@pytest.mark.asyncio
async def test_append_file_does_not_truncate(tmp_path):
    """Ensure append_file truly appends rather than overwriting."""
    from a2ia.workspace import Workspace
    from a2ia.tools.filesystem_tools import append_file
    from a2ia.core import set_workspace

    ws = Workspace.attach(tmp_path)
    set_workspace(ws)

    file_path = tmp_path / "append.txt"
    file_path.write_text("original")

    # Call append_file — expected to append, not overwrite
    await append_file("append.txt", "_added")

    result = file_path.read_text()

    # This should fail if append_file truncates
    assert result == "original_added", (
        f"AppendFile incorrectly overwrote file; got: {result!r}"
    )