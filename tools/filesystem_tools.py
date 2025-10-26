"""Filesystem operation tools."""

from ..core import get_mcp_app, get_workspace
import os
import subprocess
import tempfile
import time

mcp = get_mcp_app()

@mcp.tool()
async def list_directory(path: str = "", recursive: bool = False) -> dict:
    ws = get_workspace()
    return ws.list_directory(path, recursive)

@mcp.tool()
async def read_file(path: str, encoding: str = "utf-8") -> dict:
    ws = get_workspace()
    content = ws.read_file(path, encoding)
    return {"content": content, "path": path, "size": len(content.encode(encoding))}

@mcp.tool()
async def write_file(path: str, content: str, encoding: str = "utf-8") -> dict:
    ws = get_workspace()
    return ws.write_file(path, content, encoding)

@mcp.tool()
async def delete_file(path: str, recursive: bool = False) -> dict:
    ws = get_workspace()
    return ws.delete_file(path, recursive)

@mcp.tool()
async def move_file(source: str, destination: str) -> dict:
    ws = get_workspace()
    return ws.move_file(source, destination)

@mcp.tool()
async def append_file(path: str, content: str, encoding: str = "utf-8") -> dict:
    """Append content to a file within the workspace (creates if missing)."""
    ws = get_workspace()
    file_path = ws.resolve_path(path)

    try:
        os.makedirs(file_path.parent, exist_ok=True)
        with open(file_path, "a", encoding=encoding) as f:
            f.write(content)
        return {"success": True, "path": str(file_path)}
    except Exception as e:
        return {"success": False, "error": str(e), "path": str(file_path)}

@mcp.tool()
async def truncate_file(path: str, length: int = 0) -> dict:
    """Truncates the given file to a specific length (0 clears it)."""
    ws = get_workspace()
    file_path = ws.resolve_path(path)

    try:
        os.makedirs(file_path.parent, exist_ok=True)
        with open(file_path, "r+b" if file_path.exists() else "wb") as f:
            f.truncate(length)
        return {"success": True, "path": str(file_path), "length": length}
    except Exception as e:
        return {"success": False, "error": str(e), "path": str(file_path)}

@mcp.tool()
async def patch_file(path: str, diff: str) -> dict:
    """Apply a unified diff patch to a file in the workspace."""
    ws = get_workspace()
    log_dir = ws.resolve_path('a2ia/logs')
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, 'patch_attempts.log')

    try:
        # Write diff to temp file and ensure it's completely flushed to disk
        with tempfile.NamedTemporaryFile(mode='w', suffix='.patch', delete=False, encoding='utf-8') as f:
            if not diff.endswith('\n'):
                diff += '\n'
            f.write(diff)
            f.flush()
            os.fsync(f.fileno())
            patch_file_path = f.name

        # Explicitly close before subprocess starts reading it
        f.close()

        # Correct argument order: -i before target file, workspace-relative cwd
        result = subprocess.run(
            ["patch", "-p0", "-i", patch_file_path],
            cwd=ws.path,
            capture_output=True,
            text=True,
            timeout=10,
        )

        os.unlink(patch_file_path)
        success = result.returncode == 0
        with open(log_path, 'a') as log:
            log.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {path} diff_len={len(diff)} success={success}\n")

        if success:
            return {"success": True, "path": path, "message": "Patch applied"}
        else:
            return {
                "success": False,
                "path": path,
                "stderr": result.stderr.strip(),
                "stdout": result.stdout.strip(),
            }

    except Exception as e:
        with open(log_path, 'a') as log:
            log.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {path} diff_len={len(diff)} error={e}\n")
        return {"success": False, "error": str(e), "path": path}