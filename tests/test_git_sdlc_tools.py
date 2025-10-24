"""Tests for Git SDLC workflow tools."""

import pytest
from unittest.mock import patch, Mock
import tempfile
from pathlib import Path


@pytest.mark.unit
class TestGitSDLCTools:
    """Test Git SDLC workflow automation tools."""

    @patch('subprocess.run')
    async def test_git_create_epoch_branch(self, mock_run):
        """Create epoch branch from main."""
        from a2ia.tools.git_sdlc_tools import git_create_epoch_branch

        mock_run.return_value = Mock(returncode=0, stdout="Switched to a new branch", stderr="")

        result = await git_create_epoch_branch(number=3, descriptor="test-feature")

        assert result["success"] is True
        assert "epoch/3-test-feature" in str(mock_run.call_args)

    @patch('subprocess.run')
    async def test_git_rebase_main(self, mock_run):
        """Rebase current branch onto main."""
        from a2ia.tools.git_sdlc_tools import git_rebase_main

        mock_run.return_value = Mock(returncode=0, stdout="Successfully rebased", stderr="")

        result = await git_rebase_main()

        assert result["success"] is True
        assert "rebase" in str(mock_run.call_args)
        assert "main" in str(mock_run.call_args)

    @patch('subprocess.run')
    async def test_git_push_branch(self, mock_run):
        """Push current branch to remote."""
        from a2ia.tools.git_sdlc_tools import git_push_branch

        mock_run.return_value = Mock(returncode=0, stdout="Branch pushed", stderr="")

        result = await git_push_branch(remote="origin")

        assert result["success"] is True
        assert "push" in str(mock_run.call_args)

    @patch('subprocess.run')
    async def test_git_squash_epoch(self, mock_run):
        """Squash epoch commits."""
        from a2ia.tools.git_sdlc_tools import git_squash_epoch

        # Mock git log to show commits
        # Mock reset --soft
        mock_run.side_effect = [
            Mock(returncode=0, stdout="commit1\ncommit2\ncommit3", stderr=""),  # log
            Mock(returncode=0, stdout="", stderr=""),  # reset --soft
            Mock(returncode=0, stdout="", stderr="")  # commit
        ]

        result = await git_squash_epoch(message="E3: Test epoch changes")

        assert result["success"] is True

    @patch('subprocess.run')
    async def test_git_fast_forward_merge(self, mock_run):
        """Fast-forward merge to main."""
        from a2ia.tools.git_sdlc_tools import git_fast_forward_merge

        mock_run.side_effect = [
            Mock(returncode=0, stdout="", stderr=""),  # checkout main
            Mock(returncode=0, stdout="Fast-forward", stderr="")  # merge --ff-only
        ]

        result = await git_fast_forward_merge(branch="epoch/3-test")

        assert result["success"] is True
        assert "--ff-only" in str(mock_run.call_args_list)

    @patch('subprocess.run')
    async def test_git_tag_epoch_final(self, mock_run):
        """Tag epoch as final."""
        from a2ia.tools.git_sdlc_tools import git_tag_epoch_final

        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        result = await git_tag_epoch_final(epoch_number=3)

        assert result["success"] is True
        assert "epoch-3-final" in str(mock_run.call_args)

    @patch('subprocess.run')
    async def test_workspace_sync(self, mock_run):
        """Sync workspace with remote."""
        from a2ia.tools.git_sdlc_tools import workspace_sync

        mock_run.side_effect = [
            Mock(returncode=0, stdout="", stderr=""),  # fetch --prune
            Mock(returncode=0, stdout="", stderr="")   # rebase
        ]

        result = await workspace_sync()

        assert result["success"] is True
        assert len(mock_run.call_args_list) == 2  # fetch and rebase
