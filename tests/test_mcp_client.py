"""Tests for MCP client integration."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import asyncio


@pytest.mark.unit
class TestMCPClient:
    """Test MCP client."""

    async def test_create_mcp_client(self):
        """Create MCP client with server command."""
        from a2ia.client.mcp import MCPClient

        client = MCPClient(
            server_command=["python", "-m", "a2ia.server", "--mode", "mcp"]
        )
        assert client.server_command == ["python", "-m", "a2ia.server", "--mode", "mcp"]
        assert client.process is None
        assert not client.connected

    async def test_list_tools_format(self):
        """Tools should be in OpenAI function calling format."""
        from a2ia.client.mcp import MCPClient

        client = MCPClient(server_command=["echo"])

        # Mock the MCP connection
        client._tools = [
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "Read a file",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "File path"}
                        },
                        "required": ["path"]
                    }
                }
            }
        ]

        tools = client.list_tools()
        assert len(tools) == 1
        assert tools[0]["type"] == "function"
        assert tools[0]["function"]["name"] == "read_file"


@pytest.mark.integration
class TestSimpleMCPIntegration:
    """Integration tests with SimpleMCPClient (direct function calls)."""

    async def test_list_tools(self):
        """List available tools from SimpleMCPClient."""
        from a2ia.client.simple_mcp import SimpleMCPClient

        client = SimpleMCPClient(
            server_command=["python3", "-m", "a2ia.mcp_server"]
        )

        tools = client.list_tools()

        # Should have all our A2IA tools
        tool_names = [t["function"]["name"] for t in tools]

        assert "ReadFile" in tool_names
        assert "WriteFile" in tool_names
        assert "ExecuteCommand" in tool_names
        assert "GitStatus" in tool_names
        assert "StoreMemory" in tool_names

        # Should be at least 30+ tools
        assert len(tools) >= 30

    async def test_call_tool_git_status(self):
        """Call git_status tool via SimpleMCPClient."""
        from a2ia.client.simple_mcp import SimpleMCPClient

        client = SimpleMCPClient(
            server_command=["python3", "-m", "a2ia.mcp_server"]
        )

        # Call git_status tool (bypasses stdio, calls directly)
        result = await client.call_tool("GitStatus", {})

        assert isinstance(result, dict)
        assert "success" in result
        assert "stdout" in result

    async def test_call_tool_workspace_info(self):
        """Call get_workspace_info tool via SimpleMCPClient."""
        from a2ia.client.simple_mcp import SimpleMCPClient

        client = SimpleMCPClient(
            server_command=["python3", "-m", "a2ia.mcp_server"]
        )

        result = await client.call_tool("GetWorkspaceInfo", {})

        assert isinstance(result, dict)
        assert "path" in result

    async def test_concurrent_tool_calls(self):
        """Call multiple tools concurrently via SimpleMCPClient."""
        from a2ia.client.simple_mcp import SimpleMCPClient

        client = SimpleMCPClient(
            server_command=["python3", "-m", "a2ia.mcp_server"]
        )

        # Call multiple tools concurrently
        results = await asyncio.gather(
            client.call_tool("GetWorkspaceInfo", {}),
            client.call_tool("GitStatus", {}),
        )

        assert len(results) == 2
        # All should return dictionaries
        assert all(isinstance(r, dict) for r in results)
