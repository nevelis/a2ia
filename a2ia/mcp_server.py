"""MCP server entry point for A2IA.

Runs the MCP server via stdio for local Claude desktop integration.
"""

import asyncio

from .core import get_mcp_app

# Import all tools to register them with FastMCP
from .tools import workspace_tools, filesystem_tools, shell_tools, memory_tools, git_tools, businessmap_tools  # noqa: F401


def run():
    """Entry point for running the MCP server."""
    mcp = get_mcp_app()

    # Run stdio server (synchronous)
    mcp.run(transport="stdio")


if __name__ == "__main__":
    run()
