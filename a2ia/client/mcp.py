"""MCP client for connecting to A2IA MCP server."""

import asyncio
import json
from typing import List, Dict, Any, Optional
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp import ClientSession


class MCPClient:
    """Client for connecting to MCP servers via stdio."""

    def __init__(self, server_command: List[str]):
        """Initialize MCP client.

        Args:
            server_command: Command to start MCP server (e.g., ["python", "-m", "a2ia.server", "--mode", "mcp"])
        """
        self.server_command = server_command
        self.process = None
        self.connected = False
        self._session: Optional[ClientSession] = None
        self._tools: List[Dict[str, Any]] = []
        self._context_manager = None

    async def connect(self, timeout: int = 30):
        """Connect to MCP server via stdio.

        Args:
            timeout: Connection timeout in seconds
        """
        import sys

        try:
            print("  [1/4] Creating server parameters...")
            # Create server parameters - also capture stderr for debugging
            server_params = StdioServerParameters(
                command=self.server_command[0],
                args=self.server_command[1:] if len(self.server_command) > 1 else [],
                env=None
            )

            print("  [2/4] Starting MCP server process...")
            # Connect using stdio_client with timeout
            self._context_manager = stdio_client(server_params)

            # This starts the subprocess
            read_stream, write_stream = await asyncio.wait_for(
                self._context_manager.__aenter__(),
                timeout=timeout
            )
            print("      Server process started")

            print("  [3/4] Initializing MCP session...")
            print("      Creating ClientSession...")
            # Create session
            self._session = ClientSession(read_stream, write_stream)
            print("      ClientSession created")

            print("      Calling session.initialize()...")
            # Initialize with timeout
            await asyncio.wait_for(self._session.initialize(), timeout=timeout)
            print("      Session initialized!")

            print("  [4/4] Loading tools...")
            # List tools with timeout
            tools_result = await asyncio.wait_for(
                self._session.list_tools(),
                timeout=timeout
            )

            # Convert to OpenAI function format
            self._tools = []
            for tool in tools_result.tools:
                self._tools.append({
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description or "",
                        "parameters": tool.inputSchema
                    }
                })

            self.connected = True

        except asyncio.TimeoutError as e:
            raise TimeoutError(f"MCP server connection timed out after {timeout}s") from e
        except Exception as e:
            import traceback
            print(f"\nDEBUG: Connection failed at some step")
            print(f"Error: {e}")
            print(f"Traceback:\n{traceback.format_exc()}")
            raise RuntimeError(f"Failed to connect to MCP server: {e}") from e

    async def disconnect(self):
        """Disconnect from MCP server."""
        if self._context_manager:
            await self._context_manager.__aexit__(None, None, None)
            self._context_manager = None

        self._session = None
        self.connected = False

    def list_tools(self) -> List[Dict[str, Any]]:
        """Get list of available tools in OpenAI format.

        Returns:
            List of tool definitions
        """
        return self._tools

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Call an MCP tool.

        Args:
            name: Tool name
            arguments: Tool arguments

        Returns:
            Tool result
        """
        if not self._session:
            raise RuntimeError("Not connected to MCP server")

        result = await self._session.call_tool(name, arguments)

        # Extract text content from result
        if result.content:
            for content in result.content:
                if hasattr(content, 'text'):
                    # Try to parse as JSON if possible
                    try:
                        return json.loads(content.text)
                    except:
                        return content.text

        return None

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
