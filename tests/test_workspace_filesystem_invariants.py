import os
import io
import pytest
from pathlib import Path

@pytest.mark.asyncio
class TestWorkspaceFilesystemInvariants:
    async def test_append_file_does_not_truncate(self, tmp_path):
        from a2ia.workspace import Workspace
        from a2ia.tools.filesystem_tools import append_file
        from a2ia.core import set_workspace

        ws = Workspace.attach(tmp_path)
        set_workspace(ws)

        f = tmp_path / 'file.txt'
        f.write_text('original')
        await append_file('file.txt', '_appended')
        assert f.read_text() == 'original_appended'

    async def test_truncate_file_creates_and_truncates(self, tmp_path):
        from a2ia.workspace import Workspace
        from a2ia.tools.filesystem_tools import truncate_file
        from a2ia.core import set_workspace

        ws = Workspace.attach(tmp_path)
        set_workspace(ws)

        # Nonexistent file should be created and truncated to 0
        result = await truncate_file('newfile.txt', 0)
        f = tmp_path / 'newfile.txt'
        assert f.exists(), 'File should be created'
        assert f.read_text() == '', 'File should be empty'
        assert result['success']

        # Existing file should be truncated to given size
        f.write_text('abcdef')
        await truncate_file('newfile.txt', 3)
        assert f.read_text() == 'abc'

    def test_resolve_path_blocks_escape(self, tmp_path):
        from a2ia.workspace import Workspace, WorkspaceSecurityError

        ws = Workspace.attach(tmp_path)

        # Create outside file
        outside = tmp_path.parent / 'escape.txt'
        outside.write_text('malicious')

        with pytest.raises(WorkspaceSecurityError):
            ws.resolve_path('../escape.txt')

    def test_list_directory_excludes_metadata(self, tmp_path):
        from a2ia.workspace import Workspace

        ws = Workspace.attach(tmp_path)
        (tmp_path / '.a2ia_workspace.json').write_text('{}')
        (tmp_path / 'keep.txt').write_text('ok')

        listing = ws.list_directory()
        files = listing['files']

        assert '.a2ia_workspace.json' not in files, 'Metadata file must be excluded'
        assert 'keep.txt' in files

    def test_edit_file_large_data_preserves_integrity(self, tmp_path):
        from a2ia.workspace import Workspace

        ws = Workspace.attach(tmp_path)
        big_file = tmp_path / 'big.txt'
        big_file.write_text('x' * 10_000 + 'BAD' + 'x' * 10_000)

        result = ws.edit_file('big.txt', 'BAD', 'GOOD')
        assert result['changes'] == 1

        content = big_file.read_text()
        assert 'GOOD' in content
        assert 'BAD' not in content