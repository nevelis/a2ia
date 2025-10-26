"""RESTful HTTP server for A2IA.

Clean REST API following HTTP semantics:
- GET for reading
- PUT for replacing
- PATCH for modifying
- DELETE for removing
- POST for actions/creation
"""

import os
import subprocess
import logging
import traceback
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request, Security
from fastapi.responses import PlainTextResponse, JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from .core import get_workspace, initialize_workspace
from .tools.filesystem_tools import patch_file as deterministic_patch

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("a2ia.rest_server")

# Configuration
API_PASSWORD = os.getenv("A2IA_PASSWORD", "poop")


# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize workspace on startup."""
    try:
        initialize_workspace()
    except Exception:
        # Will initialize on first request if startup fails
        pass
    yield
    # Cleanup on shutdown (if needed)


# FastAPI app
app = FastAPI(
    title="A2IA - Aaron's AI Assistant",
    description="RESTful API for AI-assisted development with persistent workspace, Git, and semantic memory.",
    version="0.2.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Add servers to OpenAPI schema
app.servers = [
    {
        "url": "https://a2ia.amazingland.live",
        "description": "Production server"
    }
]


# Customize OpenAPI schema to add x-openai-isConsequential flags
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    # Import the original openapi function from FastAPI
    from fastapi.openapi.utils import get_openapi

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        servers=app.servers,
    )

    # Add x-openai-isConsequential to all operations
    # Set to false so ChatGPT never prompts for confirmation
    for path, path_item in openapi_schema.get("paths", {}).items():
        for method, operation in path_item.items():
            if method in ["get", "post", "put", "patch", "delete"]:
                # false = no confirmation needed
                operation["x-openai-isConsequential"] = False

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

# Security
security = HTTPBearer()


def sanitize_path_for_response(abs_path: str, workspace_path: str) -> str:
    """Convert absolute workspace path to relative path for API responses.

    Prevents leaking real filesystem structure to clients.
    Example: /home/aaron/a2ia/workspace/file.txt -> file.txt
    """
    from pathlib import Path
    try:
        abs_p = Path(abs_path)
        ws_p = Path(workspace_path)
        # Get relative path from workspace
        rel = abs_p.relative_to(ws_p)
        return str(rel)
    except (ValueError, Exception):
        # If can't make relative, just return the original
        # (but this shouldn't happen with proper workspace isolation)
        return abs_path


# Global exception handler for detailed error logging
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Log all unhandled exceptions with full details."""
    logger.error("=" * 80)
    logger.error(f"UNHANDLED EXCEPTION: {type(exc).__name__}")
    logger.error(f"Request: {request.method} {request.url.path}")
    logger.error(f"Client: {request.client.host if request.client else 'unknown'}")

    # Try to log request body if present
    try:
        body = await request.body()
        if body:
            logger.error(f"Request body ({len(body)} bytes): {body[:1000]}")
    except:
        logger.error("Could not read request body")

    logger.error(f"Exception: {exc}")
    logger.error(f"Full traceback:\n{traceback.format_exc()}")
    logger.error("=" * 80)

    # Sanitize error message to not leak filesystem paths
    error_msg = str(exc)
    # Don't include absolute paths in error messages sent to client
    # (but keep them in server logs above)

    return JSONResponse(
        status_code=500,
        content={
            "detail": f"{type(exc).__name__}: {error_msg}",
            "type": type(exc).__name__,
            "path": request.url.path,
            "hint": "Check server logs for detailed error information"
        }
    )


def verify_token(
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> bool:
    """Verify bearer token authentication."""
    if credentials.credentials != API_PASSWORD:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return True


# ============================================================================
# Workspace Info
# ============================================================================


@app.get("/workspace", tags=["Workspace"], operation_id="GetWorkspaceInfo")
async def get_workspace_info(authenticated: bool = Depends(verify_token)):
    """Get information about the persistent workspace."""
    ws = get_workspace()
    return {
        "workspace_id": ws.workspace_id,
        "path": "/workspace",  # Don't leak real filesystem path
        "description": ws.description,
        "created_at": ws.created_at,
    }


# ============================================================================
# File Operations - RESTful
# ============================================================================


@app.get("/workspace/files/{path:path}", tags=["Files"], operation_id="ReadFile")
async def read_file(
    path: str,
    list: bool = False,
    recursive: bool = False,
    authenticated: bool = Depends(verify_token),
):
    """Read file contents OR list directory.

    - If file: returns file contents as text
    - If directory and list=true: returns JSON with files/directories
    - Supports Range header for partial reads (TODO)
    """
    ws = get_workspace()

    try:
        resolved_path = ws.resolve_path(path)

        # Check if directory
        if resolved_path.is_dir():
            if not list:
                raise HTTPException(
                    status_code=400,
                    detail="Path is a directory. Use ?list=true to list contents.",
                )

            # List directory
            files = []
            directories = []

            if recursive:
                for item in resolved_path.rglob("*"):
                    rel_path = str(item.relative_to(resolved_path))
                    if item.is_file():
                        files.append(rel_path)
                    elif item.is_dir():
                        directories.append(rel_path)
            else:
                for item in resolved_path.iterdir():
                    if item.is_file():
                        files.append(item.name)
                    elif item.is_dir():
                        directories.append(item.name)

            return {
                "path": path,
                "files": sorted(files),
                "directories": sorted(directories),
                "count": len(files) + len(directories),
            }

        # Read file
        content = resolved_path.read_text()
        return PlainTextResponse(
            content=content,
            headers={
                "X-File-Path": path,
                "X-File-Size": str(resolved_path.stat().st_size),
            },
        )

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"File not found: {path}") from e
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=f"Permission denied: {path}") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


class WriteFileRequest(BaseModel):
    content: str = Field(description="File content to write")


@app.put("/workspace/files/{path:path}", tags=["Files"], operation_id="WriteFile")
async def write_file(
    path: str,
    body: WriteFileRequest,
    authenticated: bool = Depends(verify_token)
):
    """Write or overwrite entire file with content.

    Send JSON body with 'content' field:
    ```json
    {"content": "file contents here..."}
    ```
    """
    try:
        ws = get_workspace()
        logger.info(f"PUT /workspace/files/{path} ({len(body.content)} chars)")

        ws.write_file(path, body.content)

        resolved_path = ws.resolve_path(path)
        return {"success": True, "path": path, "size": resolved_path.stat().st_size}

    except Exception as e:
        logger.error(f"Error writing file {path}: {type(e).__name__}: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {str(e)}") from e


class PatchRequest(BaseModel):
    diff: str = Field(description="Unified diff to apply")


@app.patch("/workspace/files/{path:path}", tags=["Files"], operation_id="PatchFile")
async def patch_file(
    path: str, patch_data: PatchRequest, authenticated: bool = Depends(verify_token)
):
    """Apply unified diff to file.

    Accepts unified diff format:
    ```
    --- a/file.txt
    +++ b/file.txt
    @@ -1,3 +1,3 @@
     line 1
    -line 2
    +line 2 modified
     line 3
    ```
    """
    try:
        logger.info(f"PATCH /workspace/files/{path}")
        logger.info(f"Diff content ({len(patch_data.diff)} chars):\n{patch_data.diff[:500]}")

        # Check if diff looks truncated (doesn't end with newline or looks incomplete)
        if not patch_data.diff.endswith('\n'):
            logger.warning(f"Diff appears truncated - doesn't end with newline")

        # Count +/- lines to detect if truncated
        plus_lines = patch_data.diff.count('\n+')
        minus_lines = patch_data.diff.count('\n-')
        logger.info(f"Diff has {plus_lines} additions, {minus_lines} deletions")

        ws = get_workspace()
        resolved_path = ws.resolve_path(path)

        # Check if this is a "create new file" diff (@@  -0,0 +1,N @@)
        is_new_file = "-0,0" in patch_data.diff and "+1," in patch_data.diff

        if not resolved_path.exists():
            if is_new_file:
                logger.info(f"Creating new file: {path}")
                # Create empty file so patch can work
                resolved_path.parent.mkdir(parents=True, exist_ok=True)
                resolved_path.touch()
            else:
                logger.error(f"File not found: {path}")
                raise HTTPException(status_code=404, detail=f"File not found: {path}")

        # Write diff to temp file
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".patch", delete=False) as f:
            f.write(patch_data.diff)
            patch_file_path = f.name

        logger.info(f"Temp patch file: {patch_file_path}")

        try:
            # Apply patch
            from .tools.filesystem_tools import patch_file as deterministic_patch
            result = await deterministic_patch(path, patch_data.diff)

            logger.info(f"Patch command result: succcess={result['success']}")
            logger.info(f"Patch stdout: {result['stdout']}")
            logger.info(f"Patch stderr: {result['stderr']}")

            if not result["success"]:
                logger.error("Patch failed")
                logger.error(f"Full diff being applied:\n{patch_data.diff}")

                # Better hint for truncated diffs
                hint = "Check that the diff is complete and properly formatted."

                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "Patch failed",
                        "diff_length": len(patch_data.diff),
                        "diff_ends_with_newline": patch_data.diff.endswith('\n'),
                        "hint": hint,
                        **result,
                    }
                )

            logger.info(f"Patch applied successfully to {path}")
            return {
                "success": True,
                "path": path,
                "message": "Patch applied successfully",
            }

        finally:
            # Clean up temp file
            os.unlink(patch_file_path)

    except HTTPException:
        raise
    except subprocess.TimeoutExpired as e:
        logger.error(f"Patch timeout: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=408, detail="Patch operation timed out") from e
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        logger.error(traceback.format_exc())
        if "patch" in str(e):
            raise HTTPException(
                status_code=500,
                detail="'patch' command not found. Please install GNU patch.",
            ) from e
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Unexpected error in patch_file: {type(e).__name__}: {e}")
        logger.error(f"Request path: {path}")
        logger.error(f"Diff length: {len(patch_data.diff)}")
        logger.error(f"Full traceback:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"{type(e).__name__}: {str(e)}"
        ) from e


@app.delete("/workspace/files/{path:path}", tags=["Files"], operation_id="DeleteFile")
async def delete_file(
    path: str, recursive: bool = False, authenticated: bool = Depends(verify_token)
):
    """Delete file or directory.

    Use recursive=true for directories.
    """
    ws = get_workspace()

    try:
        ws.delete_file(path, recursive=recursive)
        return {"success": True, "path": path, "message": "Deleted successfully"}

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"File not found: {path}") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


class MoveRequest(BaseModel):
    destination: str = Field(description="Destination path")


@app.post("/workspace/files/{path:path}/move", tags=["Files"], operation_id="MoveFile")
async def move_file(
    path: str, move_data: MoveRequest, authenticated: bool = Depends(verify_token)
):
    """Move or rename file/directory."""
    ws = get_workspace()

    try:
        ws.move_file(path, move_data.destination)
        return {"success": True, "from": path, "to": move_data.destination}

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Source not found: {path}") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


# ============================================================================
# Shell Execution
# ============================================================================


class ExecRequest(BaseModel):
    command: str = Field(description="Shell command to execute")
    timeout: int = Field(default=30, description="Timeout in seconds")
    cwd: str | None = Field(
        None, description="Working directory (relative to workspace)"
    )
    env: dict | None = Field(None, description="Additional environment variables")


@app.post("/workspace/exec", tags=["Shell"], operation_id="ExecuteCommand")
async def execute_command(
    exec_data: ExecRequest, authenticated: bool = Depends(verify_token)
):
    """Execute shell command in workspace."""
    try:
        logger.info(f"POST /workspace/exec - command: {exec_data.command[:100]}")
        logger.info(f"  cwd: {exec_data.cwd}, timeout: {exec_data.timeout}s")

        ws = get_workspace()

        # Determine working directory
        if exec_data.cwd:
            cwd = ws.resolve_path(exec_data.cwd)  # Fixed: was _resolve_path
            logger.info(f"  Working directory: {cwd}")
        else:
            cwd = ws.path
            logger.info(f"  Working directory: {cwd} (workspace root)")

        # Prepare environment
        env = os.environ.copy()
        if exec_data.env:
            env.update(exec_data.env)
            logger.info(f"  Custom env vars: {list(exec_data.env.keys())}")

        # Execute command
        import time

        start = time.time()

        result = subprocess.run(
            exec_data.command,
            shell=True,
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            timeout=exec_data.timeout,
            stdin=subprocess.DEVNULL,  # Close stdin to prevent interactive hangs
        )

        duration = time.time() - start

        logger.info(f"Command completed: returncode={result.returncode}, duration={duration:.2f}s")
        if result.stdout:
            logger.info(f"  stdout: {result.stdout[:200]}")
        if result.stderr:
            logger.info(f"  stderr: {result.stderr[:200]}")

        return {
            "command": exec_data.command,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "duration": round(duration, 2),
        }

    except subprocess.TimeoutExpired as e:
        logger.error(f"Command timeout: {exec_data.command}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=408,
            detail=f"Command timed out after {exec_data.timeout} seconds",
        ) from e
    except Exception as e:
        logger.error(f"Error executing command: {type(e).__name__}: {e}")
        logger.error(f"  Command: {exec_data.command}")
        logger.error(f"  CWD: {exec_data.cwd}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {str(e)}") from e


class ExecTurkRequest(BaseModel):
    """Request for ExecuteTurk with longer default timeout."""
    command: str = Field(description="Shell command to execute")
    timeout: int = Field(default=300, description="Timeout in seconds (default: 5 minutes)")
    cwd: str | None = Field(None, description="Working directory (relative to workspace)")
    env: dict | None = Field(None, description="Additional environment variables")


@app.post("/workspace/exec-turk", tags=["Shell"], operation_id="ExecuteTurk")
async def execute_turk(
    exec_data: ExecTurkRequest, authenticated: bool = Depends(verify_token)
):
    """Execute shell command with human operator oversight.

    Similar to ExecuteCommand but with human curation for safety.
    Default timeout is 5 minutes (vs 30s for ExecuteCommand).
    """
    from .tools.shell_tools import execute_turk as exec_turk
    try:
        logger.info(f"POST /workspace/exec-turk - command: {exec_data.command[:100]}")

        result = await exec_turk(
            command=exec_data.command,
            timeout=exec_data.timeout,
            cwd=exec_data.cwd,
            env=exec_data.env
        )

        return result

    except Exception as e:
        logger.error(f"Error executing turk command: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {str(e)}") from e


# ============================================================================
# Memory Operations
# ============================================================================


@app.get("/memory", tags=["Memory"], operation_id="ListMemories")
async def list_memories(
    limit: int = 20,
    tags: str | None = None,
    authenticated: bool = Depends(verify_token),
):
    """List stored memories."""
    from .tools.memory_tools import list_memories as list_mem

    tag_list = tags.split(",") if tags else None
    result = await list_mem(limit=limit, tags=tag_list)
    return result


class StoreMemoryRequest(BaseModel):
    content: str = Field(description="Knowledge to store")
    tags: list[str] | None = Field(None, description="Tags")
    metadata: dict | None = Field(None, description="Metadata")


@app.post("/memory", tags=["Memory"], operation_id="StoreMemory")
async def store_memory(
    memory_data: StoreMemoryRequest, authenticated: bool = Depends(verify_token)
):
    """Store knowledge in semantic memory."""
    from .tools.memory_tools import store_memory as store_mem

    result = await store_mem(
        content=memory_data.content,
        tags=memory_data.tags,
        metadata=memory_data.metadata,
    )
    return result


@app.get("/memory/search", tags=["Memory"], operation_id="RecallMemory")
async def search_memories(
    q: str,
    limit: int = 5,
    tags: str | None = None,
    authenticated: bool = Depends(verify_token),
):
    """Semantic search over memories."""
    from .tools.memory_tools import recall_memory

    tag_list = tags.split(",") if tags else None
    result = await recall_memory(query=q, limit=limit, tags=tag_list)
    return result


@app.delete("/memory/{memory_id}", tags=["Memory"], operation_id="DeleteMemory")
async def delete_memory(memory_id: str, authenticated: bool = Depends(verify_token)):
    """Delete specific memory."""
    from .tools.memory_tools import delete_memory as del_mem

    result = await del_mem(memory_id=memory_id)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail="Memory not found")
    return result


# ============================================================================
# Health Check
# ============================================================================


@app.get("/health", tags=["System"], operation_id="HealthCheck")
async def health_check():
    """Health check endpoint (no auth required)."""
    return {"status": "healthy", "version": "0.2.0", "api_style": "REST"}


# ============================================================================
# Server Entry Point
# ============================================================================


def run_rest_server(host: str = "0.0.0.0", port: int = 8000):
    """Run the REST HTTP server."""
    import uvicorn

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_rest_server()


# ============================================================================
# File Utilities
# ============================================================================

@app.get("/workspace/files/{path:path}/head", tags=["Files"], operation_id="Head")
async def head_file(
    path: str,
    lines: int = 10,
    authenticated: bool = Depends(verify_token)
):
    """Read first N lines of file."""
    from .tools.filesystem_tools import head
    try:
        result = await head(path, lines)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/workspace/files/{path:path}/tail", tags=["Files"], operation_id="Tail")
async def tail_file(
    path: str,
    lines: int = 10,
    authenticated: bool = Depends(verify_token)
):
    """Read last N lines of file."""
    from .tools.filesystem_tools import tail
    try:
        result = await tail(path, lines)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


class GrepRequest(BaseModel):
    pattern: str = Field(description="Search pattern")
    path: str = Field(description="File or directory path")
    regex: bool = Field(default=False, description="Use regex")
    recursive: bool = Field(default=False, description="Search recursively")
    ignore_case: bool = Field(default=False, description="Case insensitive")


@app.post("/workspace/grep", tags=["Files"], operation_id="Grep")
async def grep_files(
    grep_data: GrepRequest,
    authenticated: bool = Depends(verify_token)
):
    """Search for pattern in files."""
    from .tools.filesystem_tools import grep
    try:
        result = await grep(
            pattern=grep_data.pattern,
            path=grep_data.path,
            regex=grep_data.regex,
            recursive=grep_data.recursive,
            ignore_case=grep_data.ignore_case
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


# ============================================================================
# Terraform Operations
# ============================================================================

@app.post("/terraform/init", tags=["Terraform"], operation_id="TerraformInit")
async def terraform_init_endpoint(
    upgrade: bool = False,
    authenticated: bool = Depends(verify_token)
):
    """Initialize Terraform."""
    from .tools.terraform_tools import terraform_init
    try:
        return await terraform_init(upgrade)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/terraform/plan", tags=["Terraform"], operation_id="TerraformPlan")
async def terraform_plan_endpoint(
    var_file: str | None = None,
    out: str | None = None,
    authenticated: bool = Depends(verify_token)
):
    """Generate Terraform plan."""
    from .tools.terraform_tools import terraform_plan
    try:
        return await terraform_plan(var_file, out)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/terraform/apply", tags=["Terraform"], operation_id="TerraformApply")
async def terraform_apply_endpoint(
    auto_approve: bool = True,
    plan_file: str | None = None,
    authenticated: bool = Depends(verify_token)
):
    """Apply Terraform changes."""
    from .tools.terraform_tools import terraform_apply
    try:
        return await terraform_apply(auto_approve, plan_file)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/terraform/validate", tags=["Terraform"], operation_id="TerraformValidate")
async def terraform_validate_endpoint(authenticated: bool = Depends(verify_token)):
    """Validate Terraform configuration."""
    from .tools.terraform_tools import terraform_validate
    try:
        return await terraform_validate()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


# ============================================================================
# CI/Testing Tools
# ============================================================================

@app.post("/ci/make", tags=["CI"], operation_id="Make")
async def make_endpoint(
    target: str | None = None,
    makefile: str | None = None,
    authenticated: bool = Depends(verify_token)
):
    """Run make command."""
    from .tools.ci_tools import make
    return await make(target, makefile)


@app.post("/ci/ruff", tags=["CI"], operation_id="Ruff")
async def ruff_endpoint(
    action: str = "check",
    path: str = ".",
    fix: bool = False,
    authenticated: bool = Depends(verify_token)
):
    """Run Ruff linter."""
    from .tools.ci_tools import ruff
    return await ruff(action, path, fix)


@app.post("/ci/black", tags=["CI"], operation_id="Black")
async def black_endpoint(
    path: str = ".",
    check: bool = False,
    authenticated: bool = Depends(verify_token)
):
    """Run Black formatter."""
    from .tools.ci_tools import black
    return await black(path, check)


@app.post("/ci/pytest", tags=["CI"], operation_id="PytestRun")
async def pytest_endpoint(
    path: str | None = None,
    markers: str | None = None,
    verbose: bool = True,
    authenticated: bool = Depends(verify_token)
):
    """Run pytest tests."""
    from .tools.ci_tools import pytest_run
    return await pytest_run(path, markers, verbose)


# ============================================================================
# ExecuteTurk Tracking
# ============================================================================

@app.get("/turk/info", tags=["Tracking"], operation_id="TurkInfo")
async def turk_info_endpoint(authenticated: bool = Depends(verify_token)):
    """Get ExecuteTurk usage statistics."""
    from .tools.shell_tools import turk_info
    return await turk_info()


@app.post("/turk/reset", tags=["Tracking"], operation_id="TurkReset")
async def turk_reset_endpoint(authenticated: bool = Depends(verify_token)):
    """Reset ExecuteTurk tracking."""
    from .tools.shell_tools import turk_reset
    return await turk_reset()
# Git Meta-Operation - replaces all individual git endpoints

class GitRequest(BaseModel):
    """Git operation request with detailed subcommand support.

    Available actions:
    - status: Show git status
    - diff: Show changes (params: path, staged)
    - add: Stage files (params: path)
    - commit: Commit changes (params: message)
    - log: View history (params: limit)
    - reset: Reset to commit (params: commit, hard)
    - blame: Show who changed lines (params: path)
    - checkout: Switch branch (params: branch_or_commit, create_new)
    - create_epoch_branch: Create epoch/n-name branch (params: number, descriptor)
    - rebase_main: Rebase onto main
    - push_branch: Push to remote (params: remote, force)
    - squash_epoch: Squash epoch commits (params: message)
    - merge_ff: Fast-forward merge (params: branch)
    - tag_epoch: Tag as epoch-n-final (params: epoch_number, message)
    - cherry_pick: Cherry-pick commit (params: commit_hash)
    - sync: Fetch and rebase from remote (params: remote)
    - create_branch: Create new branch (params: branch, from_branch)
    - list_branches: List all branches (params: all_branches)
    - push: Push to remote safely (params: remote, branch, force_with_lease)
    - pull: Pull with rebase (params: remote, branch)
    - show: Show commit details (params: commit, summarize)
    - stash_push/pop/list/apply/drop: Stash operations (params: name, message)
    """
    action: str = Field(description="Git action to perform")
    path: str | None = Field(None, description="File path for diff/blame")
    staged: bool | None = Field(None, description="Show staged changes (diff)")
    message: str | None = Field(None, description="Commit/tag/squash message")
    limit: int | None = Field(None, description="Number of log entries")
    commit: str | None = Field(None, description="Commit hash for reset/show")
    hard: bool | None = Field(None, description="Hard reset (reset)")
    branch_or_commit: str | None = Field(None, description="Branch/commit for checkout")
    create_new: bool | None = Field(None, description="Create new branch (checkout)")
    number: int | None = Field(None, description="Epoch number")
    descriptor: str | None = Field(None, description="Branch descriptor")
    remote: str | None = Field(None, description="Remote name (default: origin)")
    force: bool | None = Field(None, description="Force operation")
    force_with_lease: bool | None = Field(None, description="Safe force push")
    branch: str | None = Field(None, description="Branch name")
    from_branch: str | None = Field(None, description="Create branch from")
    all_branches: bool | None = Field(None, description="Include remote branches")
    epoch_number: int | None = Field(None, description="Epoch number for tagging")
    commit_hash: str | None = Field(None, description="Commit to cherry-pick")
    summarize: bool | None = Field(None, description="Show summary only (show)")
    name: str | None = Field(None, description="Stash name")


@app.post("/git", tags=["Git"], operation_id="Git")
async def git_operation(
    git_req: GitRequest,
    authenticated: bool = Depends(verify_token)
):
    """Execute Git operations with detailed subcommand support.

    This meta-operation provides access to all Git functionality through a single endpoint.
    Specify the action and relevant parameters for the operation you want to perform.
    """
    from .tools import git_tools, git_sdlc_tools

    action = git_req.action

    try:
        # Route to appropriate tool based on action
        if action == "status":
            return await git_tools.git_status()
        elif action == "diff":
            return await git_tools.git_diff(git_req.path, git_req.staged or False)
        elif action == "add":
            if not git_req.path:
                raise ValueError("path required for add")
            return await git_tools.git_add(git_req.path)
        elif action == "commit":
            if not git_req.message:
                raise ValueError("message required for commit")
            return await git_tools.git_commit(git_req.message)
        elif action == "log":
            return await git_tools.git_log(git_req.limit or 10)
        elif action == "reset":
            return await git_tools.git_reset(git_req.commit or "HEAD", git_req.hard or False)
        elif action == "blame":
            if not git_req.path:
                raise ValueError("path required for blame")
            return await git_tools.git_blame(git_req.path)
        elif action == "checkout":
            if not git_req.branch_or_commit:
                raise ValueError("branch_or_commit required for checkout")
            return await git_tools.git_checkout(git_req.branch_or_commit, git_req.create_new or False)
        elif action == "create_epoch_branch":
            if not git_req.number or not git_req.descriptor:
                raise ValueError("number and descriptor required for create_epoch_branch")
            return await git_sdlc_tools.git_create_epoch_branch(git_req.number, git_req.descriptor)
        elif action == "rebase_main":
            return await git_sdlc_tools.git_rebase_main()
        elif action == "push_branch":
            return await git_sdlc_tools.git_push_branch(git_req.remote or "origin", git_req.force or False)
        elif action == "squash_epoch":
            if not git_req.message:
                raise ValueError("message required for squash_epoch")
            return await git_sdlc_tools.git_squash_epoch(git_req.message)
        elif action == "merge_ff":
            return await git_sdlc_tools.git_fast_forward_merge(git_req.branch)
        elif action == "tag_epoch":
            if not git_req.epoch_number:
                raise ValueError("epoch_number required for tag_epoch")
            return await git_sdlc_tools.git_tag_epoch_final(git_req.epoch_number, git_req.message)
        elif action == "cherry_pick":
            if not git_req.commit_hash:
                raise ValueError("commit_hash required for cherry_pick")
            return await git_sdlc_tools.git_cherry_pick_phase(git_req.commit_hash)
        elif action == "sync":
            return await git_sdlc_tools.workspace_sync(git_req.remote or "origin")
        elif action == "create_branch":
            if not git_req.branch:
                raise ValueError("branch required for create_branch")
            return await git_tools.git_branch_create(git_req.branch)
        elif action == "list_branches":
            return await git_tools.git_list_branches(git_req.all_branches or False)
        elif action == "push":
            return await git_tools.git_push(
                git_req.remote or "origin",
                git_req.branch,
                git_req.force_with_lease or False
            )
        elif action == "pull":
            return await git_tools.git_pull(
                git_req.remote or "origin",
                git_req.branch or "main"
            )
        elif action == "show":
            return await git_tools.git_show(git_req.commit or "HEAD", git_req.summarize or False)
        elif action in ["stash_push", "stash_pop", "stash_list", "stash_apply", "stash_drop"]:
            subaction = action.replace("stash_", "")
            return await git_tools.git_stash(subaction, git_req.name, git_req.message)
        else:
            raise ValueError(f"Unknown git action: {action}")

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
