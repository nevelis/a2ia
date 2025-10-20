"""Filesystem operation tools."""

from typing import Optional
from ..core import get_mcp_app, get_workspace

mcp = get_mcp_app()


@mcp.tool()
async def list_directory(path: str = "", recursive: bool = False) -> dict:
    """List contents of a directory in the workspace.

    Args:
        path: Directory path relative to workspace root (empty for root)
        recursive: If True, list recursively

    Returns:
        Dictionary with files and directories lists
    """
    ws = get_workspace()
    return ws.list_directory(path, recursive)


@mcp.tool()
async def read_file(path: str, encoding: str = "utf-8") -> dict:
    """Read contents of a file in the workspace.

    Args:
        path: File path relative to workspace root
        encoding: Text encoding (default: utf-8)

    Returns:
        Dictionary with file content and metadata
    """
    ws = get_workspace()
    content = ws.read_file(path, encoding)

    return {
        "content": content,
        "path": path,
        "size": len(content.encode(encoding))
    }


@mcp.tool()
async def write_file(path: str, content: str, encoding: str = "utf-8") -> dict:
    """Write content to a file in the workspace.

    Creates parent directories if needed. Overwrites existing files.

    Args:
        path: File path relative to workspace root
        content: Content to write
        encoding: Text encoding (default: utf-8)

    Returns:
        Dictionary with success status and file info
    """
    ws = get_workspace()
    return ws.write_file(path, content, encoding)


@mcp.tool()
async def edit_file(
    path: str,
    old_text: str,
    new_text: str,
    occurrence: Optional[int] = None
) -> dict:
    """Edit a file by replacing text.

    Args:
        path: File path relative to workspace root
        old_text: Text to find and replace
        new_text: Replacement text
        occurrence: Which occurrence to replace (1-indexed), None for all

    Returns:
        Dictionary with success status and number of changes
    """
    ws = get_workspace()
    return ws.edit_file(path, old_text, new_text, occurrence)


@mcp.tool()
async def delete_file(path: str, recursive: bool = False) -> dict:
    """Delete a file or directory in the workspace.

    Args:
        path: Path relative to workspace root
        recursive: If True, delete directories recursively

    Returns:
        Dictionary with success status
    """
    ws = get_workspace()
    return ws.delete_file(path, recursive)


@mcp.tool()
async def move_file(source: str, destination: str) -> dict:
    """Move or rename a file/directory in the workspace.

    Args:
        source: Source path relative to workspace root
        destination: Destination path relative to workspace root

    Returns:
        Dictionary with success status
    """
    ws = get_workspace()
    return ws.move_file(source, destination)
