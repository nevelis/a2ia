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
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request, Security
from fastapi.responses import PlainTextResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from .core import get_workspace, initialize_workspace

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

# Security
security = HTTPBearer()


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


@app.get("/workspace", tags=["Workspace"])
async def get_workspace_info(authenticated: bool = Depends(verify_token)):
    """Get information about the persistent workspace."""
    ws = get_workspace()
    return {
        "workspace_id": ws.workspace_id,
        "path": str(ws.path),
        "description": ws.description,
        "created_at": ws.created_at,
    }


# ============================================================================
# File Operations - RESTful
# ============================================================================


@app.get("/workspace/files/{path:path}", tags=["Files"])
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


@app.put("/workspace/files/{path:path}", tags=["Files"])
async def write_file(
    path: str, request: Request, authenticated: bool = Depends(verify_token)
):
    """Write or overwrite entire file with request body."""
    try:
        ws = get_workspace()

        content = await request.body()
        content_str = content.decode("utf-8")

        ws.write_file(path, content_str)

        resolved_path = ws.resolve_path(path)
        return {"success": True, "path": path, "size": resolved_path.stat().st_size}

    except Exception as e:
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {str(e)}") from e


class PatchRequest(BaseModel):
    diff: str = Field(description="Unified diff to apply")


@app.patch("/workspace/files/{path:path}", tags=["Files"])
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
    ws = get_workspace()

    try:
        resolved_path = ws.resolve_path(path)

        if not resolved_path.exists():
            raise HTTPException(status_code=404, detail=f"File not found: {path}")

        # Write diff to temp file
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".patch", delete=False) as f:
            f.write(patch_data.diff)
            patch_file_path = f.name

        try:
            # Apply patch
            result = subprocess.run(
                ["patch", str(resolved_path), patch_file_path],
                cwd=ws.path,
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode != 0:
                raise HTTPException(
                    status_code=400, detail=f"Patch failed: {result.stderr}"
                )

            return {
                "success": True,
                "path": path,
                "message": "Patch applied successfully",
            }

        finally:
            # Clean up temp file
            os.unlink(patch_file_path)

    except subprocess.TimeoutExpired as e:
        raise HTTPException(status_code=408, detail="Patch operation timed out") from e
    except FileNotFoundError as e:
        if "patch" in str(e):
            raise HTTPException(
                status_code=500,
                detail="'patch' command not found. Please install GNU patch.",
            ) from e
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.delete("/workspace/files/{path:path}", tags=["Files"])
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


@app.post("/workspace/files/{path:path}/move", tags=["Files"])
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


@app.post("/workspace/exec", tags=["Shell"])
async def execute_command(
    exec_data: ExecRequest, authenticated: bool = Depends(verify_token)
):
    """Execute shell command in workspace."""
    ws = get_workspace()

    try:
        # Determine working directory
        if exec_data.cwd:
            cwd = ws._resolve_path(exec_data.cwd)
        else:
            cwd = ws.path

        # Prepare environment
        env = os.environ.copy()
        if exec_data.env:
            env.update(exec_data.env)

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
        )

        duration = time.time() - start

        return {
            "command": exec_data.command,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "duration": round(duration, 2),
        }

    except subprocess.TimeoutExpired as e:
        raise HTTPException(
            status_code=408,
            detail=f"Command timed out after {exec_data.timeout} seconds",
        ) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


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


@app.get("/workspace/git/status", tags=["Git"])
async def git_status(authenticated: bool = Depends(verify_token)):
    """Get git status."""
    return _run_git(["status"])


@app.get("/workspace/git/log", tags=["Git"])
async def git_log(limit: int = 10, authenticated: bool = Depends(verify_token)):
    """Get commit history."""
    return _run_git(["log", f"-{limit}", "--oneline", "--decorate", "--graph"])


@app.get("/workspace/git/diff", tags=["Git"])
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


@app.post("/workspace/git/add", tags=["Git"])
async def git_add(add_data: GitAddRequest, authenticated: bool = Depends(verify_token)):
    """Stage files for commit."""
    return _run_git(["add", add_data.path])


class GitCommitRequest(BaseModel):
    message: str = Field(description="Commit message")


@app.post("/workspace/git/commit", tags=["Git"])
async def git_commit(
    commit_data: GitCommitRequest, authenticated: bool = Depends(verify_token)
):
    """Commit staged changes."""
    return _run_git(["commit", "-m", commit_data.message])


class GitResetRequest(BaseModel):
    commit: str = Field(default="HEAD", description="Commit to reset to")
    hard: bool = Field(default=False, description="Hard reset (discard changes)")


@app.post("/workspace/git/reset", tags=["Git"])
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


@app.get("/memory", tags=["Memory"])
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


@app.post("/memory", tags=["Memory"])
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


@app.get("/memory/search", tags=["Memory"])
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


@app.delete("/memory/{memory_id}", tags=["Memory"])
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
