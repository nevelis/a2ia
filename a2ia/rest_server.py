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
            result = subprocess.run(
                ["patch", str(resolved_path), patch_file_path],
                cwd=ws.path,
                capture_output=True,
                text=True,
                timeout=10,
            )

            logger.info(f"Patch command result: returncode={result.returncode}")
            logger.info(f"Patch stdout: {result.stdout}")
            logger.info(f"Patch stderr: {result.stderr}")

            if result.returncode != 0:
                logger.error(f"Patch failed with returncode {result.returncode}")
                logger.error(f"Full diff being applied:\n{patch_data.diff}")

                # Better hint for truncated diffs
                hint = "Check that the diff is complete and properly formatted"
                if "unexpected end" in result.stderr or "malformed" in result.stderr:
                    hint = "Diff appears truncated or incomplete. For creating new files or large changes, use PUT instead of PATCH"

                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "Patch failed",
                        "returncode": result.returncode,
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                        "diff_length": len(patch_data.diff),
                        "diff_ends_with_newline": patch_data.diff.endswith('\n'),
                        "hint": hint
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


@app.post("/workspace/exec-turk", tags=["Shell"], operation_id="ExecuteTurk")
async def execute_turk(
    exec_data: ExecRequest, authenticated: bool = Depends(verify_token)
):
    """Execute shell command with human operator oversight.

    Similar to ExecuteCommand but with human curation for safety.
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
# Git Operations
# ============================================================================


def _run_git(command: list[str], timeout: int = 30) -> dict:
    """Helper to run git commands."""
    ws = get_workspace()

    try:
        result = subprocess.run(
            ["git"] + command,
            cwd=ws.path,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        return {
            "success": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }

    except subprocess.TimeoutExpired as e:
        raise HTTPException(status_code=408, detail="Git command timed out") from e
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail="Git not installed") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/workspace/git/status", tags=["Git"], operation_id="GitStatus")
async def git_status(authenticated: bool = Depends(verify_token)):
    """Get git status."""
    return _run_git(["status"])


@app.get("/workspace/git/log", tags=["Git"], operation_id="GitLog")
async def git_log(limit: int = 10, authenticated: bool = Depends(verify_token)):
    """Get commit history."""
    return _run_git(["log", f"-{limit}", "--oneline", "--decorate", "--graph"])


@app.get("/workspace/git/diff", tags=["Git"], operation_id="GitDiff")
async def git_diff(
    path: str | None = None,
    staged: bool = False,
    authenticated: bool = Depends(verify_token),
):
    """Show changes."""
    command = ["diff"]
    if staged:
        command.append("--cached")
    if path:
        command.append(path)
    return _run_git(command)


class GitAddRequest(BaseModel):
    path: str = Field(default=".", description="Path to stage")


@app.post("/workspace/git/add", tags=["Git"], operation_id="GitAdd")
async def git_add(add_data: GitAddRequest, authenticated: bool = Depends(verify_token)):
    """Stage files for commit."""
    return _run_git(["add", add_data.path])


class GitCommitRequest(BaseModel):
    message: str = Field(description="Commit message")


@app.post("/workspace/git/commit", tags=["Git"], operation_id="GitCommit")
async def git_commit(
    commit_data: GitCommitRequest, authenticated: bool = Depends(verify_token)
):
    """Commit staged changes."""
    return _run_git(["commit", "-m", commit_data.message])


class GitResetRequest(BaseModel):
    commit: str = Field(default="HEAD", description="Commit to reset to")
    hard: bool = Field(default=False, description="Hard reset (discard changes)")


@app.post("/workspace/git/reset", tags=["Git"], operation_id="GitReset")
async def git_reset(
    reset_data: GitResetRequest, authenticated: bool = Depends(verify_token)
):
    """Reset to commit."""
    command = ["reset"]
    if reset_data.hard:
        command.append("--hard")
    command.append(reset_data.commit)
    return _run_git(command)


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


@app.get("/health", tags=["System"])
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

@app.post("/terraform/init", tags=["Terraform"], operation_id="Terraforminit")
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


@app.post("/terraform/plan", tags=["Terraform"], operation_id="Terraformplan")
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


@app.post("/terraform/apply", tags=["Terraform"], operation_id="Terraformapply")
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


@app.post("/terraform/validate", tags=["Terraform"], operation_id="Terraformvalidate")
async def terraform_validate_endpoint(authenticated: bool = Depends(verify_token)):
    """Validate Terraform configuration."""
    from .tools.terraform_tools import terraform_validate
    try:
        return await terraform_validate()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
