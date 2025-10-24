"""Tests for CI/Testing automation tools."""

import pytest
from unittest.mock import patch, Mock


@pytest.mark.unit
class TestCITools:
    """Test CI and testing automation tools."""

    @patch('subprocess.run')
    async def test_make_default_target(self, mock_run):
        """Run make with default target."""
        from a2ia.tools.ci_tools import make

        mock_run.return_value = Mock(returncode=0, stdout="Build successful", stderr="")

        result = await make()

        assert result["success"] is True
        assert "make" in str(mock_run.call_args)

    @patch('subprocess.run')
    async def test_make_specific_target(self, mock_run):
        """Run make with specific target."""
        from a2ia.tools.ci_tools import make

        mock_run.return_value = Mock(returncode=0, stdout="Test passed", stderr="")

        result = await make(target="test")

        assert result["success"] is True
        assert "test" in str(mock_run.call_args)

    @patch('subprocess.run')
    async def test_ruff_check_all(self, mock_run):
        """Run ruff on all files."""
        from a2ia.tools.ci_tools import ruff

        mock_run.return_value = Mock(returncode=0, stdout="All checks passed", stderr="")

        result = await ruff(action="check")

        assert result["success"] is True
        assert "ruff" in str(mock_run.call_args)
        assert "check" in str(mock_run.call_args)

    @patch('subprocess.run')
    async def test_ruff_fix(self, mock_run):
        """Run ruff with auto-fix."""
        from a2ia.tools.ci_tools import ruff

        mock_run.return_value = Mock(returncode=0, stdout="Fixed 3 issues", stderr="")

        result = await ruff(action="check", fix=True)

        assert result["success"] is True
        assert "--fix" in str(mock_run.call_args)

    @patch('subprocess.run')
    async def test_black_format(self, mock_run):
        """Run black formatter."""
        from a2ia.tools.ci_tools import black

        mock_run.return_value = Mock(returncode=0, stdout="All done!", stderr="")

        result = await black()

        assert result["success"] is True
        assert "black" in str(mock_run.call_args)

    @patch('subprocess.run')
    async def test_pytest_all(self, mock_run):
        """Run all pytest tests."""
        from a2ia.tools.ci_tools import pytest_run

        mock_run.return_value = Mock(
            returncode=0,
            stdout="136 passed",
            stderr=""
        )

        result = await pytest_run()

        assert result["success"] is True
        assert "pytest" in str(mock_run.call_args)

    @patch('subprocess.run')
    async def test_pytest_specific_file(self, mock_run):
        """Run pytest on specific file."""
        from a2ia.tools.ci_tools import pytest_run

        mock_run.return_value = Mock(returncode=0, stdout="5 passed", stderr="")

        result = await pytest_run(path="tests/test_workspace.py")

        assert result["success"] is True
        assert "test_workspace.py" in str(mock_run.call_args)

    @patch('subprocess.run')
    async def test_pytest_with_markers(self, mock_run):
        """Run pytest with markers filter."""
        from a2ia.tools.ci_tools import pytest_run

        mock_run.return_value = Mock(returncode=0, stdout="10 passed", stderr="")

        result = await pytest_run(markers="unit")

        assert result["success"] is True
        assert "-m" in str(mock_run.call_args)
        assert "unit" in str(mock_run.call_args)
