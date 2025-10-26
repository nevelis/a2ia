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


@mcp.tool()
async def patch_file(path: str, diff: str) -> dict:
    """Apply a unified diff deterministically with context verification and EOF insertion alignment."""
    ws = get_workspace()
    file_path = ws.resolve_path(path)
    log_dir = ws.resolve_path('a2ia/logs')
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, 'patch_attempts.log')

    try:
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
