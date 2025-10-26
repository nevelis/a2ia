"""Filesystem operation tools with test-mode-aware cwd handling and full workspace utilities."""

from ..core import get_mcp_app, get_workspace
import os
import subprocess
import tempfile
import time

mcp = get_mcp_app()


def _resolve_cwd(file_path: str) -> str:
    if os.getenv("A2IA_TEST_MODE") == "1":
        return os.path.dirname(file_path)
    return get_workspace().path


@mcp.tool()
async def head(path: str, lines: int = 10):
    ws = get_workspace()
    file_path = ws.resolve_path(path)
    result = subprocess.run(
        ["head", f"-n{lines}", str(file_path)],
        cwd=_resolve_cwd(str(file_path)),
        capture_output=True,
        text=True,
        timeout=5,
    )
    output_lines = result.stdout.splitlines()
    return {"success": True, "path": str(file_path), "lines": output_lines, "count": len(output_lines)}


@mcp.tool()
async def tail(path: str, lines: int = 10):
    ws = get_workspace()
    file_path = ws.resolve_path(path)
    result = subprocess.run(
        ["tail", f"-n{lines}", str(file_path)],
        cwd=_resolve_cwd(str(file_path)),
        capture_output=True,
        text=True,
        timeout=5,
    )
    output_lines = result.stdout.splitlines()
    return {"success": True, "path": str(file_path), "lines": output_lines, "count": len(output_lines)}


@mcp.tool()
async def grep(pattern: str, path: str = ".", regex: bool = False, ignore_case: bool = False, recursive: bool = True, before_lines: int = 0, after_lines: int = 0):
    ws = get_workspace()
    root_path = ws.resolve_path(path)

    flags = ["-n"]
    if recursive:
        flags.append("-r")
    if ignore_case:
        flags.append("-i")
    if regex:
        flags.append("-E")
    else:
        flags.append("-F")
    if before_lines > 0:
        flags.append(f"-B{before_lines}")
    if after_lines > 0:
        flags.append(f"-A{after_lines}")

    result = subprocess.run(
        ["grep", *flags, pattern, str(root_path)],
        cwd=_resolve_cwd(str(root_path)),
        capture_output=True,
        text=True,
        timeout=10,
    )

    output = result.stdout.strip()
    match_count = sum(1 for line in output.splitlines() if ":" in line)

    return {"success": True, "path": str(root_path), "content": output, "count": match_count}


@mcp.tool()
async def append_file(path: str, content: str, encoding: str = "utf-8") -> dict:
    ws = get_workspace()
    return ws.append_file(path, content, encoding)


@mcp.tool()
async def truncate_file(path: str, length: int = 0) -> dict:
    ws = get_workspace()
    return ws.truncate_file(path, length)


@mcp.tool()
async def find_replace(path: str, find_text: str, replace_text: str, encoding: str = "utf-8") -> dict:
    ws = get_workspace()
    return ws.find_replace(path, find_text, replace_text, encoding)


@mcp.tool()
async def find_replace_regex(path: str, pattern: str, replace_text: str, encoding: str = "utf-8") -> dict:
    ws = get_workspace()
    return ws.find_replace_regex(path, pattern, replace_text, encoding)


@mcp.tool()
async def prune_directory(path: str, keep_patterns=None, dry_run: bool = False) -> dict:
    ws = get_workspace()
    return ws.prune_directory(path, keep_patterns, dry_run)


@mcp.tool()
async def patch_file(path: str, diff: str) -> dict:
    from .filesystem_tools import _infer_patch_level

    ws = get_workspace()
    log_dir = ws.resolve_path('a2ia/logs')
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, 'patch_attempts.log')

    try:
        try:
            patch_level = _infer_patch_level(diff)
        except ValueError as e:
            return {"success": False, "error": str(e), "path": path}

        with tempfile.NamedTemporaryFile(mode='w', suffix='.patch', delete=False, encoding='utf-8') as f:
            if not diff.endswith('\n'):
                diff += '\n'
            f.write(diff)
            f.flush()
            os.fsync(f.fileno())
            patch_file_path = f.name

        result = subprocess.run(
            ["patch", f"-p{patch_level}", "-i", patch_file_path],
            cwd=ws.path,
            capture_output=True,
            text=True,
            timeout=10,
        )

        os.unlink(patch_file_path)
        success = result.returncode == 0
        with open(log_path, 'a') as log:
            log.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {path} diff_len={len(diff)} success={success} p={patch_level}\n")

        if success:
            return {"success": True, "path": path, "message": f"Patch applied with -p{patch_level}"}
        else:
            return {"success": False, "path": path, "stderr": result.stderr.strip(), "stdout": result.stdout.strip()}

    except Exception as e:
        with open(log_path, 'a') as log:
            log.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {path} diff_len={len(diff)} error={e}\n")
        return {"success": False, "error": str(e), "path": path}


def _infer_patch_level(diff: str) -> int:
    header_lines = [line for line in diff.splitlines() if line.startswith(("---", "+++"))]
    if len(header_lines) < 2:
        raise ValueError(
            "Invalid diff format: missing --- and +++ headers. Expected:\n--- a/file.txt\n+++ b/file.txt"
        )
    old_path = header_lines[0][3:].strip()
    new_path = header_lines[1][3:].strip()
    if old_path == new_path:
        return 0
    old_parts = old_path.split("/", 1)
    new_parts = new_path.split("/", 1)
    if len(old_parts) == 2 and len(new_parts) == 2 and old_parts[0] != new_parts[0] and old_parts[1] == new_parts[1]:
        return 1
    raise ValueError(
        f"Invalid diff format: expected matching file paths with distinct prefixes, e.g.\n--- a/file.txt\n+++ b/file.txt\nGot: {old_path!r} and {new_path!r}"
    )