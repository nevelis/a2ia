"""CI/Testing automation tools."""

import subprocess
from ..core import get_mcp_app, get_workspace

mcp = get_mcp_app()


def _run_command(cmd: list[str], timeout: int = 300) -> dict:
    """Run command in workspace.

    Args:
        cmd: Command to run
        timeout: Timeout in seconds

    Returns:
        Dictionary with success, stdout, stderr
    """
    ws = get_workspace()

    try:
        result = subprocess.run(
            cmd,
            cwd=ws.path,
            capture_output=True,
            text=True,
            timeout=timeout
        )

        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "stdout": "",
            "stderr": f"Command timed out after {timeout}s",
            "returncode": -1
        }
    except FileNotFoundError as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": f"Command not found: {e}",
            "returncode": -1
        }
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": str(e),
            "returncode": -1
        }


@mcp.tool()
async def make(target: str | None = None, makefile: str | None = None) -> dict:
    """Run make command.

    Args:
        target: Make target (default: default target)
        makefile: Specific Makefile to use (default: Makefile)

    Returns:
        Dictionary with make result
    """
    cmd = ["make"]

    if makefile:
        cmd.extend(["-f", makefile])

    if target:
        cmd.append(target)

    # Use longer timeout for make (e.g., E2E tests can be slow)
    result = _run_command(cmd, timeout=600)  # 10 minutes for make
    result["target"] = target or "default"
    return result


@mcp.tool()
async def ruff(
    action: str = "check",
    path: str = ".",
    fix: bool = False,
    unsafe_fixes: bool = False
) -> dict:
    """Run Ruff linter/formatter.

    Args:
        action: Action to perform (check, format)
        path: Path to lint (default: all files)
        fix: Auto-fix issues (default: False)
        unsafe_fixes: Apply unsafe fixes (default: False)

    Returns:
        Dictionary with ruff result
    """
    cmd = ["ruff", action, path]

    if fix:
        cmd.append("--fix")

    if unsafe_fixes:
        cmd.append("--unsafe-fixes")

    return _run_command(cmd)


@mcp.tool()
async def black(path: str = ".", check: bool = False) -> dict:
    """Run Black code formatter.

    Args:
        path: Path to format (default: all files)
        check: Check only, don't modify files (default: False)

    Returns:
        Dictionary with black result
    """
    cmd = ["black", path]

    if check:
        cmd.append("--check")

    return _run_command(cmd)


@mcp.tool()
async def pytest_run(
    path: str | None = None,
    markers: str | None = None,
    verbose: bool = True,
    coverage: bool = False
) -> dict:
    """Run pytest tests.

    Args:
        path: Specific test file/directory (default: all tests)
        markers: Test markers to filter (e.g., "unit", "integration")
        verbose: Verbose output (default: True)
        coverage: Generate coverage report (default: False)

    Returns:
        Dictionary with test results
    """
    cmd = ["pytest"]

    if path:
        cmd.append(path)

    if markers:
        cmd.extend(["-m", markers])

    if verbose:
        cmd.append("-v")

    if coverage:
        cmd.extend(["--cov", "--cov-report=html"])

    result = _run_command(cmd, timeout=600)

    # Parse test count from output
    import re
    match = re.search(r'(\d+) passed', result["stdout"])
    if match:
        result["tests_passed"] = int(match.group(1))

    return result
