"""Shell command execution tools."""

import asyncio
from collections import Counter

from ..core import get_mcp_app, get_workspace

mcp = get_mcp_app()

# Global tracker for ExecuteTurk command usage
_turk_commands = Counter()


@mcp.tool()
async def execute_command(
    command: str,
    timeout: int = 30,
    cwd: str | None = None,
    env: dict[str, str] | None = None,
) -> dict:
    """Execute a shell command in the workspace.

    Args:
        command: Shell command to execute
        timeout: Timeout in seconds (default: 30)
        cwd: Working directory relative to workspace (default: workspace root)
        env: Additional environment variables

    Returns:
        Dictionary with stdout, stderr, returncode, and duration
    """
    ws = get_workspace()

    # Resolve working directory
    if cwd:
        work_dir = ws.resolve_path(cwd)
    else:
        work_dir = ws.path

    # Prepare environment
    command_env = None
    if env:
        import os

        command_env = os.environ.copy()
        command_env.update(env)

    # Execute command
    import time

    start_time = time.time()

    try:
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.DEVNULL,  # Close stdin to prevent interactive hangs
            cwd=str(work_dir),
            env=command_env,
        )

        stdout_bytes, stderr_bytes = await asyncio.wait_for(
            process.communicate(), timeout=timeout
        )

        duration = time.time() - start_time

        return {
            "stdout": stdout_bytes.decode("utf-8", errors="replace"),
            "stderr": stderr_bytes.decode("utf-8", errors="replace"),
            "returncode": process.returncode,
            "duration": round(duration, 2),
        }

    except TimeoutError:
        duration = time.time() - start_time
        return {
            "stdout": "",
            "stderr": f"Command timed out after {timeout} seconds",
            "returncode": -1,
            "duration": round(duration, 2),
            "error": "timeout",
        }
    except Exception as e:
        duration = time.time() - start_time
        return {
            "stdout": "",
            "stderr": str(e),
            "returncode": -1,
            "duration": round(duration, 2),
            "error": "execution_failed",
        }


@mcp.tool()
async def execute_turk(
    command: str,
    timeout: int = 300,  # 5 minutes default for manual commands
    cwd: str | None = None,
    env: dict[str, str] | None = None,
) -> dict:
    """Execute a shell command with human operator oversight.

    Similar to execute_command, but with a human operator curating which
    commands run and ensuring safe execution. Use this for complex or
    sensitive operations where human judgment is valuable.

    Tracks command usage for tooling gap analysis.

    Args:
        command: Shell command to execute
        timeout: Timeout in seconds (default: 30)
        cwd: Working directory relative to workspace (default: workspace root)
        env: Additional environment variables

    Returns:
        Dictionary with stdout, stderr, returncode, and duration
    """
    # Track this command for tooling analysis
    global _turk_commands
    _turk_commands[command] += 1

    # Execute the command
    return await execute_command(command, timeout, cwd, env)


@mcp.tool()
async def turk_info() -> dict:
    """Get ExecuteTurk command usage statistics.

    Shows which commands have been executed via ExecuteTurk and their frequency.
    Used to identify tooling gaps that should be automated.

    Returns:
        Dictionary with command usage statistics
    """
    global _turk_commands

    # Sort by frequency
    sorted_commands = sorted(_turk_commands.items(), key=lambda x: x[1], reverse=True)

    return {
        "total_calls": sum(_turk_commands.values()),
        "unique_commands": len(_turk_commands),
        "commands": [
            {"command": cmd, "count": count}
            for cmd, count in sorted_commands
        ],
        "top_5": sorted_commands[:5] if sorted_commands else []
    }


@mcp.tool()
async def turk_reset() -> dict:
    """Reset ExecuteTurk command tracking.

    Call this after reviewing turk_info and updating A2IA-Tooldev.md.

    Returns:
        Dictionary with reset confirmation
    """
    global _turk_commands
    old_count = sum(_turk_commands.values())
    _turk_commands.clear()

    return {
        "success": True,
        "message": "ExecuteTurk tracking reset",
        "previous_total": old_count
    }
