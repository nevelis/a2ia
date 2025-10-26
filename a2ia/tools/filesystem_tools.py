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
async def truncate_file(path: str) -> dict:
    """
    Truncates the given file to length 0.
    Creates the file if it does not exist.
    Operates safely within the workspace boundary.
    """
    ws = get_workspace()
    file_path = ws.resolve_path(path)

    try:
        os.makedirs(file_path.parent, exist_ok=True)
        with open(file_path, "w", encoding="utf-8"):
            pass
        return {"success": True, "path": str(file_path)}
    except Exception as e:
        return {"success": False, "error": str(e), "path": str(file_path)}

@mcp.tool()
async def patch_file(path: str, diff: str) -> dict:
    ws = get_workspace()
    log_dir = ws.resolve_path('a2ia/logs')
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, 'patch_attempts.log')

    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.patch', delete=False) as f:
            if not diff.endswith('\n'):
                diff += '\n'
            f.write(diff)
            f.flush()
            patch_file_path = f.name

        result = subprocess.run(
            ["patch", "-p0", path, "-i", patch_file_path],
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
