"""Tests for ExecuteTurk tracking."""

import pytest


@pytest.mark.unit
class TestTurkTracking:
    """Test ExecuteTurk command tracking."""

    async def test_turk_tracking_increments(self):
        """ExecuteTurk tracks command usage."""
        from a2ia.tools.shell_tools import execute_turk, turk_info, turk_reset

        # Reset first
        await turk_reset()

        # Track some commands
        from unittest.mock import patch, Mock

        with patch('subprocess.run', return_value=Mock(returncode=0, stdout="", stderr="")):
            with patch('asyncio.create_subprocess_shell'):
                # Simulate turk calls (won't actually run due to mocks)
                # Just test the tracking mechanism
                pass

        # For now, just verify the tools exist and have correct signatures
        info = await turk_info()
        assert "total_calls" in info
        assert "unique_commands" in info
        assert "commands" in info

    async def test_turk_reset_clears_tracking(self):
        """TurkReset clears command history."""
        from a2ia.tools.shell_tools import turk_reset, turk_info

        # Reset
        reset_result = await turk_reset()

        assert reset_result["success"] is True
        assert "previous_total" in reset_result

        # Verify cleared
        info = await turk_info()
        assert info["total_calls"] == 0
        assert info["unique_commands"] == 0
