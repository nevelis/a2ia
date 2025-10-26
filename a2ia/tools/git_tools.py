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


@mcp.tool()
async def git_blame(path: str) -> dict:
    """Show git blame for a file (who changed each line).

    Args:
        path: File path relative to workspace

    Returns:
        Dictionary with blame output
    """
    result = _run_git_command(["blame", path])
    return result



# Enhanced Git actions for meta-command

@mcp.tool()
async def git_branch_create(name: str, from_branch: str | None = None) -> dict:
    """Create new branch.

    Args:
        name: Branch name
        from_branch: Create from this branch (default: current)

    Returns:
        Dictionary with result
    """
    args = ["checkout", "-b", name]
    if from_branch:
        args.append(from_branch)

    result = _run_git_command(args)
    result["branch"] = name
    return result


@mcp.tool()
async def git_list_branches(all_branches: bool = False) -> dict:
    """List branches.

    Args:
        all_branches: Include remote branches (default: False)

    Returns:
        Dictionary with branches list
    """
    args = ["branch"]
    if all_branches:
        args.append("-a")

    result = _run_git_command(args)

    # Parse branch list
    branches = []
    current = None
    if result["success"]:
        for line in result["stdout"].split('\n'):
            if line.strip():
                if line.startswith('*'):
                    current = line[2:].strip()
                    branches.append(current)
                else:
                    branches.append(line.strip())

    result["branches"] = branches
    result["current"] = current
    return result


@mcp.tool()
async def git_push(remote: str = "origin", branch: str | None = None, force_with_lease: bool = False) -> dict:
    """Push to remote safely.

    Args:
        remote: Remote name (default: origin)
        branch: Branch to push (default: current)
        force_with_lease: Safe force push (default: False)

    Returns:
        Dictionary with push result
    """
    import subprocess
    import os

    ws = get_workspace()

    # Get current branch if not specified
    if not branch:
        branch_result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=ws.path,
            capture_output=True,
            text=True,
            env={**os.environ, 'GIT_TERMINAL_PROMPT': '0'}
        )
        branch = branch_result.stdout.strip()

    args = ["push", remote, branch]

    if force_with_lease:
        args.append("--force-with-lease")

    result = _run_git_command(args)
    result["remote"] = remote
    result["branch"] = branch
    return result


@mcp.tool()
async def git_pull(remote: str = "origin", branch: str = "main") -> dict:
    """Pull from remote with rebase (no merge).

    Args:
        remote: Remote name (default: origin)
        branch: Branch to pull (default: main)

    Returns:
        Dictionary with pull result
    """
    result = _run_git_command(["pull", "--rebase", remote, branch])
    result["remote"] = remote
    result["branch"] = branch
    return result


@mcp.tool()
async def git_show(commit: str = "HEAD", summarize: bool = False) -> dict:
    """Show commit details.

    Args:
        commit: Commit hash or ref (default: HEAD)
        summarize: Show summary only (no full diff)

    Returns:
        Dictionary with commit info
    """
    if summarize:
        # Get structured summary
        args = ["show", "--stat", "--format=%H%n%an%n%ae%n%at%n%s", commit]
    else:
        args = ["show", commit]

    result = _run_git_command(args)

    if summarize and result["success"]:
        # Parse structured output
        lines = result["stdout"].split('\n')
        if len(lines) >= 5:
            result["summary"] = {
                "commit_hash": lines[0],
                "author": lines[1],
                "author_email": lines[2],
                "timestamp": lines[3],
                "message": lines[4],
                "stats": '\n'.join(lines[5:])
            }

    return result


@mcp.tool()
async def git_stash(subaction: str, name: str | None = None, message: str | None = None) -> dict:
    """Stash operations.

    Args:
        subaction: Action (push, pop, list, apply, drop)
        name: Stash name for push (optional)
        message: Stash message (optional)

    Returns:
        Dictionary with stash result
    """
    args = ["stash", subaction]

    if subaction == "push":
        if message:
            args.extend(["-m", message])
        elif name:
            args.extend(["-m", name])

    elif subaction in ["pop", "apply", "drop"]:
        if name:
            args.append(name)

    result = _run_git_command(args)

    # Parse stash list
    if subaction == "list" and result["success"]:
        stashes = [line.strip() for line in result["stdout"].split('\n') if line.strip()]
        result["stashes"] = stashes

    return result
