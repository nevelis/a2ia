"""Core A2IA application setup.

Provides the MCP server instance and workspace management.
"""

import os
import subprocess
from pathlib import Path

from mcp.server import FastMCP

from .workspace import Workspace

# Global MCP application instance
mcp_app = FastMCP("a2ia")

# Single persistent workspace directory (configurable via environment)
WORKSPACE_PATH = Path(os.getenv("A2IA_WORKSPACE_PATH", "./workspace"))
WORKSPACE_PATH.mkdir(parents=True, exist_ok=True)

# Single global workspace (auto-initialized)
_workspace: Workspace | None = None


def get_mcp_app() -> FastMCP:
    """Get the MCP application instance."""
    return mcp_app


def initialize_workspace() -> Workspace:
    """Initialize the single persistent workspace with Git."""
    global _workspace

    if _workspace is None:
        # Attach to the persistent workspace directory
        _workspace = Workspace.attach(
            WORKSPACE_PATH, description="A2IA Persistent Workspace"
        )

        # Initialize as Git repository if not already
        git_dir = WORKSPACE_PATH / ".git"
        if not git_dir.exists():
            try:
                subprocess.run(
                    ["git", "init"], cwd=WORKSPACE_PATH, check=True, capture_output=True
                )
                subprocess.run(
                    ["git", "config", "user.name", "A2IA"],
                    cwd=WORKSPACE_PATH,
                    check=True,
                    capture_output=True,
                )
                subprocess.run(
                    ["git", "config", "user.email", "a2ia@localhost"],
                    cwd=WORKSPACE_PATH,
                    check=True,
                    capture_output=True,
                )
                # Initial commit
                subprocess.run(
                    ["git", "commit", "--allow-empty", "-m", "Initial commit by A2IA"],
                    cwd=WORKSPACE_PATH,
                    check=True,
                    capture_output=True,
                )
            except (subprocess.CalledProcessError, FileNotFoundError):
                # Git not available or failed, continue without it
                pass

    return _workspace


def get_workspace() -> Workspace:
    """Get the persistent workspace, initializing if needed."""
    if _workspace is None:
        initialize_workspace()
    return _workspace


def set_workspace(workspace: Workspace) -> None:
    """Set the workspace (for testing compatibility)."""
    global _workspace
    _workspace = workspace


def clear_workspace() -> None:
    """Clear the workspace (for testing compatibility)."""
    global _workspace
    _workspace = None
