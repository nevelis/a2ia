"""Filesystem operation tools with deterministic, streaming unified diff patching (final EOF alignment fix)."""

from ..core import get_mcp_app, get_workspace
import os
import re
import tempfile
import time

mcp = get_mcp_app()


def _normalize_newlines(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if not text.endswith("\n"):
        text += "\n"
    return text


def _parse_hunk_header(line: str):
    match = re.match(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", line)
    if not match:
        raise ValueError(f"Invalid hunk header: {line}")
    old_start = int(match.group(1))
    old_count = int(match.group(2) or 1)
    new_start = int(match.group(3))
    new_count = int(match.group(4) or 1)
    return old_start, old_count, new_start, new_count


def _validate_diff_format(diff: str) -> tuple[bool, str]:
    """Validate diff format and return (is_valid, error_message)."""
    lines = diff.splitlines()
    
    # Find the first --- and +++ lines
    from_line = None
    to_line = None
    
    for i, line in enumerate(lines):
        if line.startswith('---'):
            from_line = line
            if i + 1 < len(lines) and lines[i + 1].startswith('+++'):
                to_line = lines[i + 1]
                break
    
    # Check if headers are present - they are required
    if from_line is None or to_line is None:
        return False, "Invalid diff format: missing --- and +++ headers"
    
    # Check that prefixes match convention
    from_path = from_line[4:].strip()
    to_path = to_line[4:].strip()
    
    # Extract prefix type (a/, b/, c/, etc.)
    from_prefix = ""
    to_prefix = ""
    
    if '/' in from_path:
        from_prefix = from_path.split('/')[0]
    if '/' in to_path:
        to_prefix = to_path.split('/')[0]
    
    # Both should have the same prefix style
    if (from_prefix and not to_prefix) or (not from_prefix and to_prefix):
        return False, f"Invalid diff format: mismatched prefix style (from: '{from_prefix}', to: '{to_prefix}')"
    
    # If both have prefixes, check they follow a/b convention
    if from_prefix and to_prefix:
        if from_prefix == to_prefix:
            return False, f"Invalid diff format: same prefixes ('--- {from_prefix}/' and '+++ {to_prefix}/' should be different)"
        # Require standard a/b convention
        if not ((from_prefix == 'a' and to_prefix == 'b') or (from_prefix == 'b' and to_prefix == 'a')):
            return False, f"Invalid diff format: non-standard prefixes ('--- {from_prefix}/' and '+++ {to_prefix}/' should be 'a' and 'b')"
    
    return True, ""


@mcp.tool()
async def patch_file(path: str, diff: str) -> dict:
    """Apply a unified diff deterministically with context verification and EOF insertion alignment."""
    ws = get_workspace()
    file_path = ws.resolve_path(path)
    log_dir = ws.resolve_path('a2ia/logs')
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, 'patch_attempts.log')

    try:
        # Validate diff format first
        is_valid, error_msg = _validate_diff_format(diff)
        if not is_valid:
            return {"success": False, "path": path, "error": error_msg, "stdout": "", "stderr": error_msg}
        
        diff = _normalize_newlines(diff)
        if not os.path.exists(file_path):
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('')

        with open(file_path, 'r', encoding='utf-8') as f:
            original_lines = f.readlines()

        diff_lines = diff.splitlines()
        output_lines = []
        orig_index = 0
        i = 0
        applied_cleanly = True
        mismatches = 0
        hunks_applied = 0
        lines_added = 0
        lines_removed = 0

        while i < len(diff_lines):
            line = diff_lines[i]
            if not line.startswith('@@'):
                i += 1
                continue

            hunks_applied += 1
            old_start, old_count, new_start, new_count = _parse_hunk_header(line)

            target_index = max(0, old_start - 1)
            while orig_index < target_index and orig_index < len(original_lines):
                output_lines.append(original_lines[orig_index])
                orig_index += 1

            i += 1

            insert_buffer = []

            while i < len(diff_lines) and not diff_lines[i].startswith('@@'):
                dl = diff_lines[i]

                if dl.startswith('+'):
                    insert_buffer.append(dl[1:] + '\n')
                    lines_added += 1

                elif dl.startswith('-'):
                    if insert_buffer:
                        output_lines.extend(insert_buffer)
                        insert_buffer = []
                    if orig_index < len(original_lines):
                        orig_index += 1
                        lines_removed += 1

                elif dl.startswith(' '):
                    if insert_buffer:
                        output_lines.extend(insert_buffer)
                        insert_buffer = []
                    context_text = dl[1:].rstrip('\r\n')
                    if orig_index < len(original_lines):
                        src_line = original_lines[orig_index].rstrip('\r\n')
                        if src_line != context_text:
                            applied_cleanly = False
                            mismatches += 1
                        output_lines.append(original_lines[orig_index])
                        orig_index += 1
                    else:
                        applied_cleanly = False
                else:
                    pass
                i += 1

            # Flush any remaining insertions at end of hunk
            if insert_buffer:
                if old_count == 0:
                    # Pure insertion (e.g., EOF) — place after the last copied context line
                    while orig_index < target_index + 1 and orig_index < len(original_lines):
                        output_lines.append(original_lines[orig_index])
                        orig_index += 1
                output_lines.extend(insert_buffer)
                insert_buffer = []

        while orig_index < len(original_lines):
            output_lines.append(original_lines[orig_index])
            orig_index += 1

        new_content = _normalize_newlines(''.join(output_lines))

        with tempfile.NamedTemporaryFile('w', delete=False, encoding='utf-8') as tmp:
            tmp.write(new_content)
            tmp_path = tmp.name

        os.replace(tmp_path, file_path)

        with open(log_path, 'a', encoding='utf-8') as log:
            log.write(
                f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {path} hunks={hunks_applied} added={lines_added} removed={lines_removed} mismatches={mismatches} clean={applied_cleanly}\n"
            )

        return {
            "success": applied_cleanly,
            "path": path,
            "stdout": f"Applied {hunks_applied} hunks (+{lines_added}/-{lines_removed}) with {mismatches} mismatches",
            "stderr": "" if applied_cleanly else "context mismatch or alignment error"
        }

    except Exception as e:
        with open(log_path, 'a', encoding='utf-8') as log:
            log.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {path} error={e}\n")
        return {"success": False, "path": path, "stderr": str(e), "stdout": diff}


@mcp.tool()
async def append_file(path: str, content: str, encoding: str = 'utf-8') -> dict:
    ws = get_workspace()
    return ws.append_file(path, content, encoding)


@mcp.tool()
async def truncate_file(path: str, length: int = 0) -> dict:
    ws = get_workspace()
    return ws.truncate_file(path, length)


@mcp.tool()
async def prune_directory(path: str, keep_patterns=None, dry_run: bool = False) -> dict:
    ws = get_workspace()
    return ws.prune_directory(path, keep_patterns, dry_run)


@mcp.tool()
async def list_directory(path: str = "", recursive: bool = False) -> dict:
    """List files in a directory."""
    ws = get_workspace()
    return ws.list_directory(path, recursive)


@mcp.tool()
async def read_file(path: str, encoding: str = "utf-8") -> dict:
    """Read file content."""
    ws = get_workspace()
    content = ws.read_file(path, encoding)
    return {"content": content, "path": path, "size": len(content.encode(encoding))}


@mcp.tool()
async def write_file(path: str, content: str, encoding: str = "utf-8") -> dict:
    """Write content to a file."""
    ws = get_workspace()
    ws.write_file(path, content, encoding)
    return {"success": True, "path": path}


@mcp.tool()
async def delete_file(path: str, recursive: bool = False) -> dict:
    """Delete a file or directory."""
    ws = get_workspace()
    return ws.delete_file(path, recursive)


@mcp.tool()
async def move_file(source: str, destination: str) -> dict:
    """Move or rename a file."""
    ws = get_workspace()
    return ws.move_file(source, destination)


@mcp.tool()
async def find_replace(path: str, find_text: str, replace_text: str, encoding: str = "utf-8") -> dict:
    """Find and replace text in a file."""
    ws = get_workspace()
    return ws.find_replace(path, find_text, replace_text, encoding)


@mcp.tool()
async def find_replace_regex(path: str, pattern: str, replace_text: str, encoding: str = "utf-8") -> dict:
    """Find and replace using regex in a file."""
    ws = get_workspace()
    return ws.find_replace_regex(path, pattern, replace_text, encoding)


@mcp.tool()
async def head(path: str, lines: int = 10) -> dict:
    """Get the first N lines of a file."""
    ws = get_workspace()
    file_path = ws.resolve_path(path)
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            file_lines = [line.rstrip('\n') for line in f.readlines()[:lines]]
        return {"success": True, "path": path, "lines": file_lines, "count": len(file_lines)}
    except Exception as e:
        return {"success": False, "path": path, "error": str(e)}


@mcp.tool()
async def tail(path: str, lines: int = 10) -> dict:
    """Get the last N lines of a file."""
    ws = get_workspace()
    file_path = ws.resolve_path(path)
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            file_lines = [line.rstrip('\n') for line in f.readlines()]
        tail_lines = file_lines[-lines:] if len(file_lines) >= lines else file_lines
        return {"success": True, "path": path, "lines": tail_lines, "count": len(tail_lines)}
    except Exception as e:
        return {"success": False, "path": path, "error": str(e)}


@mcp.tool()
async def grep(pattern: str, path: str, regex: bool = False, recursive: bool = False, ignore_case: bool = False) -> dict:
    """Search for pattern in file(s).
    
    Args:
        pattern: Search pattern
        path: File or directory path
        regex: Use regex pattern matching (default: False)
        recursive: Search recursively in directories (default: False)
        ignore_case: Case-insensitive search (default: False)
    
    Returns:
        Dictionary with search results
    """
    ws = get_workspace()
    file_path = ws.resolve_path(path)
    
    try:
        import fnmatch
        from pathlib import Path
        
        matches = []
        count = 0
        
        # Prepare pattern for case-insensitive matching
        if ignore_case and not regex:
            pattern_lower = pattern.lower()
        elif ignore_case and regex:
            # Add case-insensitive flag to regex
            import re as regex_module
            regex_flags = regex_module.IGNORECASE
        else:
            regex_flags = 0
        
        if os.path.isfile(file_path):
            files_to_search = [file_path]
        elif os.path.isdir(file_path):
            if recursive:
                files_to_search = [f for f in Path(file_path).rglob("*") if f.is_file()]
            else:
                files_to_search = [f for f in Path(file_path).glob("*") if f.is_file()]
        else:
            return {"success": False, "path": path, "error": "Path not found"}
        
        for fpath in files_to_search:
            with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    if regex:
                        if re.search(pattern, line, regex_flags if ignore_case else 0):
                            matches.append(f"{fpath}:{line_num}:{line.rstrip()}")
                            count += 1
                    else:
                        # Simple string matching
                        search_line = line.lower() if ignore_case else line
                        search_pattern = pattern_lower if ignore_case else pattern
                        if search_pattern in search_line:
                            matches.append(f"{fpath}:{line_num}:{line.rstrip()}")
                            count += 1
        
        return {
            "success": True,
            "path": path,
            "pattern": pattern,
            "count": count,
            "matches": matches,
            "content": "\n".join(matches)
        }
    except Exception as e:
        return {"success": False, "path": path, "error": str(e)}
