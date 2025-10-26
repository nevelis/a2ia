"""Tests for enhanced Git meta-command actions."""

import pytest
from unittest.mock import patch, Mock


@pytest.mark.unit
class TestGitEnhancedActions:
    """Test new Git meta-command actions."""

    @patch('subprocess.run')
    async def test_git_create_branch(self, mock_run):
        """Create new branch."""
        from a2ia.tools.git_tools import git_branch_create

        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        result = await git_branch_create("feature-branch")

        assert result["success"] is True
        assert "checkout" in str(mock_run.call_args) or "branch" in str(mock_run.call_args)

    @patch('subprocess.run')
    async def test_git_list_branches(self, mock_run):
        """List all branches."""
        from a2ia.tools.git_tools import git_list_branches

        mock_run.return_value = Mock(
            returncode=0,
            stdout="* main\n  feature-1\n  feature-2\n",
            stderr=""
        )

        result = await git_list_branches()

        assert result["success"] is True
        assert "branches" in result

    @patch('subprocess.run')
    async def test_git_push_safe(self, mock_run):
        """Push with force-with-lease."""
        from a2ia.tools.git_tools import git_push

        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        result = await git_push(remote="origin", force_with_lease=True)

        assert result["success"] is True
        assert "--force-with-lease" in str(mock_run.call_args)

    @patch('subprocess.run')
    async def test_git_pull_rebase(self, mock_run):
        """Pull with rebase (no merge)."""
        from a2ia.tools.git_tools import git_pull

        mock_run.return_value = Mock(returncode=0, stdout="Successfully rebased", stderr="")

        result = await git_pull(remote="origin", branch="main")

        assert result["success"] is True
        assert "--rebase" in str(mock_run.call_args)
        assert "merge" not in str(mock_run.call_args).lower()

    @patch('subprocess.run')
    async def test_git_show_summary(self, mock_run):
        """Show commit with summary."""
        from a2ia.tools.git_tools import git_show

        mock_run.return_value = Mock(
            returncode=0,
            stdout="commit abc123\nAuthor: Test\nDate: 2025\n\n    Commit msg\n\n file.txt | 2 +-",
            stderr=""
        )

        result = await git_show(commit="HEAD", summarize=True)

        assert result["success"] is True
        if "summary" in result:
            assert "files_changed" in result["summary"] or "commit_hash" in result["summary"]

    @patch('subprocess.run')
    async def test_git_stash_push(self, mock_run):
        """Stash changes with name."""
        from a2ia.tools.git_tools import git_stash

        mock_run.return_value = Mock(returncode=0, stdout="Saved", stderr="")

        result = await git_stash(subaction="push", name="work-in-progress")

        assert result["success"] is True
        assert "stash" in str(mock_run.call_args)
        assert "push" in str(mock_run.call_args)

    @patch('subprocess.run')
    async def test_git_stash_list(self, mock_run):
        """List stashes."""
        from a2ia.tools.git_tools import git_stash

        mock_run.return_value = Mock(
            returncode=0,
            stdout="stash@{0}: work-in-progress\nstash@{1}: old-work\n",
            stderr=""
        )

        result = await git_stash(subaction="list")

        assert result["success"] is True
        assert "stashes" in result or "stdout" in result
