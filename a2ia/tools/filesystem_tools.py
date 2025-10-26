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
async def head(path: str, lines: int = 10) -> dict:
    ws = get_workspace()
    file_path = ws.resolve_path(path)
    try:
        result = subprocess.run(
            ["head", f"-n{lines}", str(file_path)],
            cwd=ws.path,
            capture_output=True,
            text=True,
            timeout=5,
        )
        return {"success": True, "path": str(file_path), "lines": result.stdout.splitlines()}
    except Exception as e:
        return {"success": False, "error": str(e), "path": str(file_path)}

@mcp.tool()
async def tail(path: str, lines: int = 10) -> dict:
    ws = get_workspace()
    file_path = ws.resolve_path(path)
    try:
        result = subprocess.run(
            ["tail", f"-n{lines}", str(file_path)],
            cwd=ws.path,
            capture_output=True,
            text=True,
            timeout=5,
        )
        return {"success": True, "path": str(file_path), "lines": result.stdout.splitlines()}
    except Exception as e:
        return {"success": False, "error": str(e), "path": str(file_path)}

@mcp.tool()
async def grep(pattern: str, path: str = ".", regex: bool = False, ignore_case: bool = False, before_lines: int = 0, after_lines: int = 0) -> dict:
    """Search for a pattern within files under the given path using system grep, with optional context lines."""
    ws = get_workspace()
    root_path = ws.resolve_path(path)

    flags = ["-n", "-r"]
    if ignore_case:
        flags.append("-i")
    if not regex:
        flags.append("-F")
    if before_lines > 0:
        flags.append(f"-B{before_lines}")
    if after_lines > 0:
        flags.append(f"-A{after_lines}")

    try:
        result = subprocess.run(
            ["grep", *flags, pattern, str(root_path)],
            cwd=ws.path,
            capture_output=True,
            text=True,
            timeout=10,
        )

        matches = []
        if result.stdout.strip():
            for line in result.stdout.strip().splitlines():
                if line.startswith("--"):
                    continue  # skip grep context separators
                parts = line.split(":", 2)
                if len(parts) == 3:
                    matches.append({"path": parts[0], "line": int(parts[1]), "text": parts[2]})

        return {"success": True, "matches": matches, "stderr": result.stderr.strip()}

    except subprocess.CalledProcessError as e:
        return {"success": False, "error": e.stderr.strip()}
    except Exception as e:
        return {"success": False, "error": str(e)}

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