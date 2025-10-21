"""Workspace management tools."""

from ..core import get_mcp_app, get_workspace

mcp = get_mcp_app()


@mcp.tool()
async def create_workspace(
    workspace_id: str | None = None,
    base_path: str | None = None,
    description: str | None = None,
) -> dict:
    """Get information about the persistent workspace.

    NOTE: This tool is kept for backward compatibility. A2IA now uses a single
    persistent workspace that is automatically initialized. Arguments are ignored.

    Args:
        workspace_id: Ignored (kept for compatibility)
        base_path: Ignored (kept for compatibility)
        description: Ignored (kept for compatibility)

    Returns:
        Dictionary with workspace information
    """
    ws = get_workspace()  # Auto-initializes if needed

    return {
        "workspace_id": ws.workspace_id,
        "path": str(ws.path),
        "description": ws.description,
        "created_at": ws.created_at,
        "note": "A2IA uses a single persistent workspace",
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
        "created_at": ws.created_at,
    }


@mcp.tool()
async def close_workspace() -> dict:
    """No-op: Workspace is persistent and cannot be closed.

    NOTE: This tool is kept for backward compatibility. The workspace
    remains active and persistent.

    Returns:
        Dictionary with status message
    """
    return {
        "success": True,
        "message": "Workspace is persistent and remains active",
        "note": "A2IA uses a single persistent workspace that is always available",
    }
