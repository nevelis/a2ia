"""Tests for Terraform wrapper tools."""

import pytest
from unittest.mock import patch, Mock


@pytest.mark.unit
class TestTerraformTools:
    """Test Terraform wrapper tools."""

    @patch('subprocess.run')
    async def test_terraform_init(self, mock_run):
        """Test terraform init."""
        from a2ia.tools.terraform_tools import terraform_init

        mock_run.return_value = Mock(
            returncode=0,
            stdout="Terraform initialized",
            stderr=""
        )

        result = await terraform_init()

        assert result["success"] is True
        assert "init" in mock_run.call_args[0][0]

    @patch('subprocess.run')
    async def test_terraform_plan(self, mock_run):
        """Test terraform plan."""
        from a2ia.tools.terraform_tools import terraform_plan

        mock_run.return_value = Mock(
            returncode=0,
            stdout="Plan: 3 to add, 0 to change, 0 to destroy",
            stderr=""
        )

        result = await terraform_plan()

        assert result["success"] is True
        assert "plan" in mock_run.call_args[0][0]

    @patch('subprocess.run')
    async def test_terraform_apply_auto_approve(self, mock_run):
        """Test terraform apply with auto-approve."""
        from a2ia.tools.terraform_tools import terraform_apply

        mock_run.return_value = Mock(
            returncode=0,
            stdout="Apply complete",
            stderr=""
        )

        result = await terraform_apply()

        assert result["success"] is True
        # Should include -auto-approve flag
        assert "-auto-approve" in ' '.join(mock_run.call_args[0][0])

    @patch('subprocess.run')
    async def test_terraform_workspace_select(self, mock_run):
        """Test terraform workspace select."""
        from a2ia.tools.terraform_tools import terraform_workspace

        mock_run.return_value = Mock(
            returncode=0,
            stdout="Switched to workspace dev",
            stderr=""
        )

        result = await terraform_workspace(name="dev", action="select")

        assert result["success"] is True
        assert "workspace" in mock_run.call_args[0][0]

    @patch('subprocess.run')
    async def test_terraform_import(self, mock_run):
        """Test terraform import."""
        from a2ia.tools.terraform_tools import terraform_import

        mock_run.return_value = Mock(
            returncode=0,
            stdout="Import successful",
            stderr=""
        )

        result = await terraform_import(address="aws_instance.example", id="i-12345")

        assert result["success"] is True
        assert "import" in mock_run.call_args[0][0]
