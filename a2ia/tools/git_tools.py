"""Git tools for version control in the workspace."""

import subprocess

from ..core import get_mcp_app, get_workspace

mcp = get_mcp_app()


def _run_git_command(command: list[str], input_text: str | None = None) -> dict:
    """Run a git command in the workspace."""
    workspace = get_workspace()

    try:
        result = subprocess.run(
            ["git"] + command,
            cwd=workspace.path,
            capture_output=True,
            text=True,
            input=input_text,
            timeout=30,
        )

        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "stdout": "",
            "stderr": "Command timed out after 30 seconds",
            "returncode": -1,
        }
    except FileNotFoundError:
        return {
            "success": False,
            "stdout": "",
            "stderr": "Git is not installed or not available in PATH",
            "returncode": -1,
        }
    except Exception as e:
        return {"success": False, "stdout": "", "stderr": str(e), "returncode": -1}


@mcp.tool()
async def git_status() -> dict:
    """Get the git status of the workspace.

    Shows modified, staged, and untracked files.

    Returns:
        Dictionary with git status output
    """
    result = _run_git_command(["status"])
    return result


@mcp.tool()
async def git_diff(path: str | None = None, staged: bool = False) -> dict:
    """Show changes to files in the workspace.

    Args:
        path: Optional path to specific file (relative to workspace)
        staged: If True, show staged changes (git diff --cached)

    Returns:
        Dictionary with diff output
    """
    command = ["diff"]
    if staged:
        command.append("--cached")
    if path:
        command.append(path)

    result = _run_git_command(command)
    return result


@mcp.tool()
async def git_add(path: str = ".") -> dict:
    """Stage files for commit.

    Args:
        path: Path to add (default: "." for all files)

    Returns:
        Dictionary with operation result
    """
    result = _run_git_command(["add", path])
    return result


@mcp.tool()
async def git_commit(message: str) -> dict:
    """Commit staged changes with a message.

    Args:
        message: Commit message

    Returns:
        Dictionary with commit result
    """
    result = _run_git_command(["commit", "-m", message])
    return result


@mcp.tool()
async def git_log(limit: int = 10) -> dict:
    """Show commit history.

    Args:
        limit: Number of commits to show (default: 10)

    Returns:
        Dictionary with log output
    """
    result = _run_git_command(
        ["log", f"-{limit}", "--oneline", "--decorate", "--graph"]
    )
    return result


@mcp.tool()
async def git_reset(commit: str = "HEAD", hard: bool = False) -> dict:
    """Reset workspace to a specific commit.

    WARNING: --hard will discard all uncommitted changes!

    Args:
        commit: Commit hash or reference (default: "HEAD")
        hard: If True, perform hard reset (discard changes)

    Returns:
        Dictionary with reset result
    """
    command = ["reset"]
    if hard:
        command.append("--hard")
    command.append(commit)

    result = _run_git_command(command)
    return result


@mcp.tool()
async def git_restore(path: str) -> dict:
    """Restore a file to its committed state.

    Discards uncommitted changes to the specified file.

    Args:
        path: Path to file to restore

    Returns:
        Dictionary with restore result
    """
    result = _run_git_command(["restore", path])
    return result


@mcp.tool()
async def git_show(commit: str = "HEAD") -> dict:
    """Show the changes in a specific commit.

    Args:
        commit: Commit hash or reference (default: "HEAD")

    Returns:
        Dictionary with commit details
    """
    result = _run_git_command(["show", commit])
    return result


@mcp.tool()
async def git_branch(list_all: bool = True) -> dict:
    """List git branches.

    Args:
        list_all: If True, list all branches including remote

    Returns:
        Dictionary with branch list
    """
    command = ["branch"]
    if list_all:
        command.append("-a")

    result = _run_git_command(command)
    return result


@mcp.tool()
async def git_checkout(branch_or_commit: str, create_new: bool = False) -> dict:
    """Switch to a different branch or commit.

    Args:
        branch_or_commit: Branch name or commit hash
        create_new: If True, create a new branch

    Returns:
        Dictionary with checkout result
    """
    command = ["checkout"]
    if create_new:
        command.append("-b")
    command.append(branch_or_commit)

    result = _run_git_command(command)
    return result
