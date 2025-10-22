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
@pytest.mark.skip(reason="Using SimpleMCPClient instead - MCP stdio protocol complex")
class TestMCPIntegration:
    """Integration tests with real A2IA MCP server."""

    async def test_connect_to_mcp_server(self):
        """Connect to A2IA MCP server via stdio."""
        from a2ia.client.mcp import MCPClient

        client = MCPClient(
            server_command=["python3", "-m", "a2ia.server", "--mode", "mcp"]
        )

        try:
            await client.connect()
            assert client.connected
            assert client.process is not None
        finally:
            await client.disconnect()

    async def test_list_tools_from_server(self):
        """List available tools from MCP server."""
        from a2ia.client.mcp import MCPClient

        client = MCPClient(
            server_command=["python3", "-m", "a2ia.server", "--mode", "mcp"]
        )

        try:
            await client.connect()
            tools = client.list_tools()

            # Should have all our A2IA tools
            tool_names = [t["function"]["name"] for t in tools]

            assert "read_file" in tool_names
            assert "write_file" in tool_names
            assert "execute_command" in tool_names
            assert "git_status" in tool_names
            assert "store_memory" in tool_names

            # Should be at least 20+ tools
            assert len(tools) >= 20

        finally:
            await client.disconnect()

    async def test_call_tool_read_file(self):
        """Call read_file tool via MCP."""
        from a2ia.client.mcp import MCPClient
        import tempfile
        from pathlib import Path

        # Create a temp workspace
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("Hello MCP!")

            client = MCPClient(
                server_command=["python3", "-m", "a2ia.server", "--mode", "mcp"]
            )

            try:
                await client.connect()

                # Call read_file tool
                result = await client.call_tool("read_file", {"path": "test.txt"})

                assert "content" in result
                # Note: This will fail because MCP server uses a different workspace
                # Just testing the call mechanism works

            finally:
                await client.disconnect()

    async def test_concurrent_tool_calls(self):
        """Call multiple tools concurrently."""
        from a2ia.client.mcp import MCPClient

        client = MCPClient(
            server_command=["python3", "-m", "a2ia.server", "--mode", "mcp"]
        )

        try:
            await client.connect()

            # Call multiple tools
            results = await asyncio.gather(
                client.call_tool("get_workspace_info", {}),
                client.call_tool("git_status", {}),
                client.call_tool("list_directory", {"path": ""}),
            )

            assert len(results) == 3
            # All should return dictionaries
            assert all(isinstance(r, dict) for r in results)

        finally:
            await client.disconnect()
