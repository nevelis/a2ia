"""Terraform wrapper tools for infrastructure management."""

import subprocess
from ..core import get_mcp_app, get_workspace

mcp = get_mcp_app()


def _run_terraform(args: list[str], timeout: int = 300) -> dict:
    """Run terraform command in workspace.

    Args:
        args: Terraform command arguments
        timeout: Command timeout in seconds

    Returns:
        Dictionary with success, stdout, stderr
    """
    ws = get_workspace()

    try:
        result = subprocess.run(
            ["terraform"] + args,
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
            "stderr": f"Terraform command timed out after {timeout}s",
            "returncode": -1
        }
    except FileNotFoundError:
        return {
            "success": False,
            "stdout": "",
            "stderr": "terraform command not found - is it installed?",
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
async def terraform_init(upgrade: bool = False) -> dict:
    """Initialize Terraform working directory.

    Args:
        upgrade: Upgrade modules and providers (default: False)

    Returns:
        Dictionary with command result
    """
    args = ["init"]
    if upgrade:
        args.append("-upgrade")

    return _run_terraform(args)


@mcp.tool()
async def terraform_plan(var_file: str | None = None, out: str | None = None) -> dict:
    """Generate Terraform execution plan.

    Args:
        var_file: Variables file path (optional)
        out: Save plan to file (optional)

    Returns:
        Dictionary with plan output
    """
    args = ["plan"]
    if var_file:
        args.extend(["-var-file", var_file])
    if out:
        args.extend(["-out", out])

    return _run_terraform(args)


@mcp.tool()
async def terraform_apply(auto_approve: bool = True, plan_file: str | None = None) -> dict:
    """Apply Terraform changes.

    Args:
        auto_approve: Auto-approve changes (default: True)
        plan_file: Apply saved plan file (optional)

    Returns:
        Dictionary with apply result
    """
    args = ["apply"]
    if auto_approve:
        args.append("-auto-approve")
    if plan_file:
        args.append(plan_file)

    return _run_terraform(args, timeout=600)


@mcp.tool()
async def terraform_destroy(auto_approve: bool = True) -> dict:
    """Destroy Terraform-managed infrastructure.

    Args:
        auto_approve: Auto-approve destruction (default: True)

    Returns:
        Dictionary with destroy result
    """
    args = ["destroy"]
    if auto_approve:
        args.append("-auto-approve")

    return _run_terraform(args, timeout=600)


@mcp.tool()
async def terraform_validate() -> dict:
    """Validate Terraform configuration.

    Returns:
        Dictionary with validation result
    """
    return _run_terraform(["validate"])


@mcp.tool()
async def terraform_workspace(name: str, action: str = "select") -> dict:
    """Manage Terraform workspaces.

    Args:
        name: Workspace name
        action: Action to perform (select, new, delete, list)

    Returns:
        Dictionary with workspace command result
    """
    args = ["workspace", action]

    if action != "list":
        args.append(name)

    return _run_terraform(args)


@mcp.tool()
async def terraform_import(address: str, id: str) -> dict:
    """Import existing infrastructure into Terraform state.

    Args:
        address: Resource address (e.g., aws_instance.example)
        id: Resource ID to import

    Returns:
        Dictionary with import result
    """
    return _run_terraform(["import", address, id])


@mcp.tool()
async def terraform_state(action: str, args: list[str] = None) -> dict:
    """Manage Terraform state.

    Args:
        action: State action (list, show, rm, mv, pull, push)
        args: Additional arguments for the action

    Returns:
        Dictionary with state command result
    """
    cmd_args = ["state", action]
    if args:
        cmd_args.extend(args)

    return _run_terraform(cmd_args)


@mcp.tool()
async def terraform_taint(address: str) -> dict:
    """Mark resource for recreation.

    Args:
        address: Resource address to taint

    Returns:
        Dictionary with taint result
    """
    return _run_terraform(["taint", address])


@mcp.tool()
async def terraform_untaint(address: str) -> dict:
    """Remove taint from resource.

    Args:
        address: Resource address to untaint

    Returns:
        Dictionary with untaint result
    """
    return _run_terraform(["untaint", address])


@mcp.tool()
async def terraform_output(name: str | None = None) -> dict:
    """Get Terraform outputs.

    Args:
        name: Specific output name (optional, returns all if not specified)

    Returns:
        Dictionary with output values
    """
    args = ["output", "-json"]
    if name:
        args.append(name)

    return _run_terraform(args)
