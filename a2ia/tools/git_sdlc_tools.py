"""Git SDLC workflow automation tools."""

import subprocess
from ..core import get_mcp_app, get_workspace

mcp = get_mcp_app()


def _run_git(args: list[str], timeout: int = 60) -> dict:
    """Run git command in workspace.

    Args:
        args: Git command arguments
        timeout: Command timeout

    Returns:
        Dictionary with success, stdout, stderr
    """
    import os
    ws = get_workspace()

    # Set environment to prevent interactive prompts
    env = os.environ.copy()
    env['GIT_TERMINAL_PROMPT'] = '0'
    env['GIT_EDITOR'] = 'true'  # No-op editor

    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=ws.path,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env  # Non-interactive environment
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
            "stderr": f"Git command timed out after {timeout}s",
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
async def git_create_epoch_branch(number: int, descriptor: str) -> dict:
    """Create new epoch branch from main.

    Args:
        number: Epoch number
        descriptor: Branch descriptor (e.g., "cicd-pipeline")

    Returns:
        Dictionary with branch creation result
    """
    branch_name = f"epoch/{number}-{descriptor}"

    # Ensure we're on main
    checkout_result = _run_git(["checkout", "main"])
    if not checkout_result["success"]:
        return checkout_result

    # Create and switch to new epoch branch
    result = _run_git(["checkout", "-b", branch_name])
    result["branch"] = branch_name
    return result


@mcp.tool()
async def git_rebase_main() -> dict:
    """Rebase current branch onto main.

    Returns:
        Dictionary with rebase result
    """
    # Fetch latest main
    fetch_result = _run_git(["fetch", "origin", "main"])
    if not fetch_result["success"]:
        return fetch_result

    # Rebase onto main
    return _run_git(["rebase", "origin/main"])


@mcp.tool()
async def git_push_branch(remote: str = "origin", force: bool = False, set_upstream: bool = True) -> dict:
    """Push current branch to remote.

    Args:
        remote: Remote name (default: origin)
        force: Force push (default: False)
        set_upstream: Set upstream tracking (default: True)

    Returns:
        Dictionary with push result
    """
    # Get current branch name
    branch_result = _run_git(["branch", "--show-current"])
    if not branch_result["success"]:
        return branch_result

    branch_name = branch_result["stdout"].strip()

    # Build push command
    args = ["push"]
    if set_upstream:
        args.extend(["-u", remote, branch_name])
    else:
        args.extend([remote, branch_name])

    if force:
        args.append("--force")

    result = _run_git(args)
    result["branch"] = branch_name
    result["remote"] = remote
    return result


@mcp.tool()
async def git_squash_epoch(message: str) -> dict:
    """Squash all commits in current epoch into one.

    Args:
        message: Squashed commit message (markdown format with epoch changes)

    Returns:
        Dictionary with squash result
    """
    # Get commits since main
    log_result = _run_git(["log", "main..HEAD", "--oneline"])
    if not log_result["success"]:
        return log_result

    commit_count = len([l for l in log_result["stdout"].split('\n') if l.strip()])

    if commit_count == 0:
        return {"success": False, "error": "No commits to squash"}

    if commit_count == 1:
        return {"success": True, "message": "Only one commit, no squash needed"}

    # Soft reset to main
    reset_result = _run_git(["reset", "--soft", "main"])
    if not reset_result["success"]:
        return reset_result

    # Create new squashed commit
    result = _run_git(["commit", "-m", message])
    result["commits_squashed"] = commit_count
    return result


@mcp.tool()
async def git_fast_forward_merge(branch: str | None = None) -> dict:
    """Merge epoch branch into main using fast-forward only.

    Args:
        branch: Branch to merge (default: current branch)

    Returns:
        Dictionary with merge result
    """
    # Get current branch if not specified
    if not branch:
        branch_result = _run_git(["branch", "--show-current"])
        if not branch_result["success"]:
            return branch_result
        branch = branch_result["stdout"].strip()

    # Checkout main
    checkout_result = _run_git(["checkout", "main"])
    if not checkout_result["success"]:
        return checkout_result

    # Fast-forward merge
    result = _run_git(["merge", "--ff-only", branch])
    result["merged_branch"] = branch
    return result


@mcp.tool()
async def git_tag_epoch_final(epoch_number: int, message: str | None = None) -> dict:
    """Tag current commit as epoch-n-final.

    Args:
        epoch_number: Epoch number
        message: Optional tag message

    Returns:
        Dictionary with tag result
    """
    tag_name = f"epoch-{epoch_number}-final"

    args = ["tag"]
    if message:
        args.extend(["-a", tag_name, "-m", message])
    else:
        args.append(tag_name)

    result = _run_git(args)
    result["tag"] = tag_name
    return result


@mcp.tool()
async def git_cherry_pick_phase(commit_hash: str) -> dict:
    """Cherry-pick a phase commit.

    Args:
        commit_hash: Commit hash to cherry-pick

    Returns:
        Dictionary with cherry-pick result
    """
    return _run_git(["cherry-pick", commit_hash])


@mcp.tool()
async def workspace_sync(remote: str = "origin") -> dict:
    """Sync workspace: fetch, prune, and rebase.

    Args:
        remote: Remote name (default: origin)

    Returns:
        Dictionary with sync result
    """
    results = []

    # Fetch
    fetch_result = _run_git(["fetch", remote, "--prune"])
    results.append(("fetch", fetch_result["success"]))

    if not fetch_result["success"]:
        return fetch_result

    # Rebase current branch
    rebase_result = _run_git(["rebase", f"{remote}/main"])
    results.append(("rebase", rebase_result["success"]))

    return {
        "success": all(r[1] for r in results),
        "steps": results,
        "stdout": rebase_result["stdout"],
        "stderr": rebase_result["stderr"]
    }
