"""Core A2IA application setup.

Provides the MCP server instance and workspace management.
"""

from pathlib import Path
from typing import Optional
from mcp.server import FastMCP

from .workspace import Workspace

# Global MCP application instance
mcp_app = FastMCP("a2ia")

# Workspace root directory (configurable via environment)
import os
WORKSPACE_ROOT = Path(os.getenv("A2IA_WORKSPACE_ROOT", "./workspaces"))
WORKSPACE_ROOT.mkdir(parents=True, exist_ok=True)

# Current workspace (thread-local would be better for production)
_current_workspace: Optional[Workspace] = None


def get_mcp_app() -> FastMCP:
    """Get the MCP application instance."""
    return mcp_app


def get_workspace() -> Workspace:
    """Get the current workspace, raising error if none exists."""
    if _current_workspace is None:
        raise RuntimeError("No workspace initialized. Call create_workspace first.")
    return _current_workspace


def set_workspace(workspace: Workspace) -> None:
    """Set the current workspace."""
    global _current_workspace
    _current_workspace = workspace


def clear_workspace() -> None:
    """Clear the current workspace."""
    global _current_workspace
    _current_workspace = None
