"""MCP server entry point for A2IA.

Runs the MCP server via stdio for local Claude desktop integration.
"""

import asyncio
from .core import get_mcp_app

# Import all tools to register them
from .tools import workspace_tools, filesystem_tools, shell_tools


async def main():
    """Run the MCP server."""
    mcp = get_mcp_app()

    # Run stdio server (for Claude desktop)
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await mcp.run(
            read_stream,
            write_stream,
            mcp.create_initialization_options()
        )


def run():
    """Entry point for running the MCP server."""
    asyncio.run(main())


if __name__ == "__main__":
    run()
