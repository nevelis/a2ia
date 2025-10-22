"""Filesystem operation tools."""

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

    return {"content": content, "path": path, "size": len(content.encode(encoding))}


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
    path: str, old_text: str, new_text: str, occurrence: int | None = None
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


@mcp.tool()
async def append_file(path: str, content: str, encoding: str = "utf-8") -> dict:
    """Append content to end of existing file.

    Args:
        path: File path relative to workspace root
        content: Content to append
        encoding: Text encoding (default: utf-8)

    Returns:
        Dictionary with success status and file size
    """
    ws = get_workspace()

    # Read existing content
    try:
        existing = ws.read_file(path, encoding)
    except FileNotFoundError:
        existing = ""

    # Append new content
    new_content = existing + content
    return ws.write_file(path, new_content, encoding)


@mcp.tool()
async def truncate_file(path: str, size: int = 0) -> dict:
    """Truncate file to specified size (default: empty file).

    Args:
        path: File path relative to workspace root
        size: New file size in bytes (default: 0 for empty)

    Returns:
        Dictionary with success status
    """
    ws = get_workspace()
    resolved_path = ws.resolve_path(path)

    with open(resolved_path, 'r+') as f:
        f.truncate(size)

    return {"success": True, "path": path, "size": size}


@mcp.tool()
async def patch_file(path: str, diff: str) -> dict:
    """Apply unified diff patch to file.

    Args:
        path: File path relative to workspace root
        diff: Unified diff content

    Returns:
        Dictionary with success status
    """
    import subprocess
    import tempfile

    ws = get_workspace()
    resolved_path = ws.resolve_path(path)

    # Write diff to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.patch', delete=False) as f:
        f.write(diff)
        patch_file_path = f.name

    try:
        # Apply patch
        result = subprocess.run(
            ["patch", str(resolved_path), patch_file_path],
            cwd=ws.path,
            capture_output=True,
            text=True,
            timeout=10
        )

        import os
        os.unlink(patch_file_path)

        if result.returncode != 0:
            return {
                "success": False,
                "error": f"Patch failed: {result.stderr}",
                "path": path
            }

        return {"success": True, "path": path, "message": "Patch applied"}

    except Exception as e:
        return {"success": False, "error": str(e), "path": path}


@mcp.tool()
async def find_replace(path: str, find: str, replace: str, count: int = -1) -> dict:
    """Find and replace text in file (alias for edit_file).

    Args:
        path: File path relative to workspace root
        find: Text to find
        replace: Replacement text
        count: Max replacements (-1 for all, default: all)

    Returns:
        Dictionary with success status and change count
    """
    ws = get_workspace()
    content = ws.read_file(path)

    # Do replacement
    if count == -1:
        new_content = content.replace(find, replace)
        changes = content.count(find)
    else:
        new_content = content.replace(find, replace, count)
        changes = min(content.count(find), count)

    ws.write_file(path, new_content)

    return {
        "success": True,
        "path": path,
        "changes": changes
    }


@mcp.tool()
async def find_replace_regex(path: str, pattern: str, replacement: str, count: int = 0) -> dict:
    """Find and replace using regular expressions.

    Args:
        path: File path relative to workspace root
        pattern: Regex pattern to find
        replacement: Replacement text (can use \\1, \\2 for capture groups)
        count: Max replacements (0 for all, default: all)

    Returns:
        Dictionary with success status and change count
    """
    import re

    ws = get_workspace()
    content = ws.read_file(path)

    # Do regex replacement
    new_content, changes = re.subn(pattern, replacement, content, count=count)

    ws.write_file(path, new_content)

    return {
        "success": True,
        "path": path,
        "changes": changes,
        "pattern": pattern
    }


@mcp.tool()
async def prune_directory(path: str, keep_patterns: list[str] = None) -> dict:
    """Delete all files/folders in directory except those matching keep patterns.

    Args:
        path: Directory path relative to workspace root
        keep_patterns: List of glob patterns to keep (e.g., [".git", "*.md"])

    Returns:
        Dictionary with deleted count
    """
    import fnmatch
    from pathlib import Path

    ws = get_workspace()
    resolved_path = ws.resolve_path(path)

    keep_patterns = keep_patterns or []
    deleted = []

    for item in resolved_path.iterdir():
        # Check if item matches any keep pattern
        should_keep = any(
            fnmatch.fnmatch(item.name, pattern)
            for pattern in keep_patterns
        )

        if not should_keep:
            try:
                ws.delete_file(str(Path(path) / item.name), recursive=True)
                deleted.append(item.name)
            except:
                pass

    return {
        "success": True,
        "path": path,
        "deleted": deleted,
        "count": len(deleted)
    }


@mcp.tool()
async def head(path: str, lines: int = 10) -> dict:
    """Read first N lines of a file.

    Args:
        path: File path relative to workspace root
        lines: Number of lines to read (default: 10)

    Returns:
        Dictionary with content and line count
    """
    ws = get_workspace()
    content = ws.read_file(path)

    file_lines = content.split('\n')
    head_lines = file_lines[:lines]

    return {
        "content": '\n'.join(head_lines),
        "lines": len(head_lines),
        "total_lines": len(file_lines),
        "path": path
    }


@mcp.tool()
async def tail(path: str, lines: int = 10) -> dict:
    """Read last N lines of a file.

    Args:
        path: File path relative to workspace root
        lines: Number of lines to read (default: 10)

    Returns:
        Dictionary with content and line count
    """
    ws = get_workspace()
    content = ws.read_file(path)

    file_lines = content.split('\n')
    tail_lines = file_lines[-lines:] if lines < len(file_lines) else file_lines

    return {
        "content": '\n'.join(tail_lines),
        "lines": len(tail_lines),
        "total_lines": len(file_lines),
        "path": path
    }


@mcp.tool()
async def grep(pattern: str, path: str, regex: bool = False, recursive: bool = False, ignore_case: bool = False) -> dict:
    """Search for pattern in file(s).

    Uses ripgrep (rg) if available, falls back to Python implementation.

    Args:
        pattern: Search pattern (literal or regex)
        path: File or directory path
        regex: Treat pattern as regex (default: False)
        recursive: Search directories recursively (default: False)
        ignore_case: Case-insensitive search (default: False)

    Returns:
        Dictionary with matches, lines, and file info
    """
    import subprocess
    import re as regex_module
    from pathlib import Path

    ws = get_workspace()
    resolved_path = ws.resolve_path(path)

    # Try using ripgrep (ag/rg) for speed
    try:
        cmd = ["rg", "--json"]
        if not regex:
            cmd.append("--fixed-strings")
        if ignore_case:
            cmd.append("--ignore-case")

        cmd.extend([pattern, str(resolved_path)])

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode in [0, 1]:  # 0=found, 1=not found
            # Parse ripgrep JSON output
            import json
            matches = []
            files = set()

            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    if data.get('type') == 'match':
                        match_data = data['data']
                        files.add(match_data['path']['text'])
                        matches.append(match_data['lines']['text'].strip())
                except:
                    pass

            return {
                "matches": len(matches),
                "lines": matches,
                "files": list(files),
                "pattern": pattern,
                "path": path
            }

    except (FileNotFoundError, subprocess.TimeoutExpired):
        # Fallback to Python implementation
        pass

    # Python fallback
    matches = []
    files_matched = []

    if resolved_path.is_file():
        content = resolved_path.read_text()
        for line in content.split('\n'):
            if regex:
                if regex_module.search(pattern, line, regex_module.IGNORECASE if ignore_case else 0):
                    matches.append(line)
            else:
                search_line = line.lower() if ignore_case else line
                search_pattern = pattern.lower() if ignore_case else pattern
                if search_pattern in search_line:
                    matches.append(line)

        if matches:
            files_matched.append(path)

    elif resolved_path.is_dir() and recursive:
        for file_path in resolved_path.rglob("*"):
            if file_path.is_file():
                try:
                    content = file_path.read_text()
                    file_matches = []

                    for line in content.split('\n'):
                        if regex:
                            if regex_module.search(pattern, line, regex_module.IGNORECASE if ignore_case else 0):
                                file_matches.append(line)
                        else:
                            search_line = line.lower() if ignore_case else line
                            search_pattern = pattern.lower() if ignore_case else pattern
                            if search_pattern in search_line:
                                file_matches.append(line)

                    if file_matches:
                        matches.extend(file_matches)
                        rel_path = file_path.relative_to(resolved_path)
                        files_matched.append(str(Path(path) / rel_path))
                except:
                    pass

    return {
        "matches": len(matches),
        "lines": matches[:100],  # Limit to first 100 matches
        "files": files_matched,
        "pattern": pattern,
        "path": path
    }
