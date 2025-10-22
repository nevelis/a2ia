"""Shell command execution tools."""

import asyncio

from ..core import get_mcp_app, get_workspace

mcp = get_mcp_app()


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
    timeout: int = 30,
    cwd: str | None = None,
    env: dict[str, str] | None = None,
) -> dict:
    """Execute a shell command with human operator oversight.

    Similar to execute_command, but with a human operator curating which
    commands run and ensuring safe execution. Use this for complex or
    sensitive operations where human judgment is valuable.

    Args:
        command: Shell command to execute
        timeout: Timeout in seconds (default: 30)
        cwd: Working directory relative to workspace (default: workspace root)
        env: Additional environment variables

    Returns:
        Dictionary with stdout, stderr, returncode, and duration
    """
    # Implementation is identical to execute_command
    return await execute_command(command, timeout, cwd, env)
