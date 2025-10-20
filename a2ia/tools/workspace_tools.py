"""Workspace management tools."""

from typing import Optional
from ..core import get_mcp_app, set_workspace, get_workspace, WORKSPACE_ROOT, clear_workspace
from ..workspace import Workspace

mcp = get_mcp_app()


@mcp.tool()
async def create_workspace(
    workspace_id: Optional[str] = None,
    base_path: Optional[str] = None,
    description: Optional[str] = None
) -> dict:
    """Create or resume a workspace for the current session.

    Args:
        workspace_id: Optional workspace ID to resume existing workspace
        base_path: Optional path to existing directory to use as workspace
        description: Optional description for the workspace

    Returns:
        Dictionary with workspace_id and path
    """
    if base_path:
        # Attach to existing directory
        from pathlib import Path
        ws = Workspace.attach(Path(base_path), description=description)
    elif workspace_id:
        # Try to resume existing workspace
        try:
            ws = Workspace.resume(WORKSPACE_ROOT, workspace_id)
        except FileNotFoundError:
            # Create new with specified ID
            ws = Workspace.create(WORKSPACE_ROOT, workspace_id=workspace_id, description=description)
    else:
        # Create new workspace with generated ID
        ws = Workspace.create(WORKSPACE_ROOT, description=description)

    set_workspace(ws)

    return {
        "workspace_id": ws.workspace_id,
        "path": str(ws.path),
        "description": ws.description,
        "created_at": ws.created_at
    }


@mcp.tool()
async def get_workspace_info() -> dict:
    """Get information about the current workspace.

    Returns:
        Dictionary with workspace details
    """
    ws = get_workspace()
    return {
        "workspace_id": ws.workspace_id,
        "path": str(ws.path),
        "description": ws.description,
        "created_at": ws.created_at
    }


@mcp.tool()
async def close_workspace() -> dict:
    """Close the current workspace.

    Returns:
        Dictionary with success status
    """
    clear_workspace()
    return {"success": True, "message": "Workspace closed"}
