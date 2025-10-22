"""FastAPI HTTP server for A2IA.

Exposes MCP tools as HTTP endpoints with OpenAPI documentation.
"""

import os
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

# Import all tools to register them

# Configuration
API_PASSWORD = os.getenv("A2IA_PASSWORD", "poop")

# FastAPI app
app = FastAPI(
    title="A2IA - Aaron's AI Assistant",
    description="Secure workspace operations for AI assistants. Provides filesystem access, shell execution, and memory management within isolated workspaces.",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Add servers to OpenAPI schema
app.servers = [
    {
        "url": "https://a2ia.amazingland.live",
        "description": "Production server"
    }
]

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


# Pydantic models for requests/responses


class ToolCallRequest(BaseModel):
    """Request to call a tool."""

    arguments: dict[str, Any] = Field(
        default_factory=dict, description="Tool arguments"
    )


class ToolCallResponse(BaseModel):
    """Response from calling a tool."""

    result: Any = Field(description="Tool execution result")
    error: str | None = Field(None, description="Error message if execution failed")


# Workspace tools


@app.post(
    "/tools/create_workspace", response_model=ToolCallResponse, tags=["Workspace"]
)
async def create_workspace_endpoint(
    workspace_id: str | None = None,
    base_path: str | None = None,
    description: str | None = None,
    authenticated: bool = Depends(verify_token),
):
    """Create or resume a workspace for the current session."""
    from .tools.workspace_tools import create_workspace

    try:
        result = await create_workspace(workspace_id, base_path, description)
        return ToolCallResponse(result=result)
    except Exception as e:
        return ToolCallResponse(result=None, error=str(e))


@app.get(
    "/tools/get_workspace_info", response_model=ToolCallResponse, tags=["Workspace"]
)
async def get_workspace_info_endpoint(authenticated: bool = Depends(verify_token)):
    """Get information about the current workspace."""
    from .tools.workspace_tools import get_workspace_info

    try:
        result = await get_workspace_info()
        return ToolCallResponse(result=result)
    except Exception as e:
        return ToolCallResponse(result=None, error=str(e))


@app.post("/tools/close_workspace", response_model=ToolCallResponse, tags=["Workspace"])
async def close_workspace_endpoint(authenticated: bool = Depends(verify_token)):
    """Close the current workspace."""
    from .tools.workspace_tools import close_workspace

    try:
        result = await close_workspace()
        return ToolCallResponse(result=result)
    except Exception as e:
        return ToolCallResponse(result=None, error=str(e))


# Filesystem tools


@app.get("/tools/list_directory", response_model=ToolCallResponse, tags=["Filesystem"])
async def list_directory_endpoint(
    path: str = "", recursive: bool = False, authenticated: bool = Depends(verify_token)
):
    """List contents of a directory in the workspace."""
    from .tools.filesystem_tools import list_directory

    try:
        result = await list_directory(path, recursive)
        return ToolCallResponse(result=result)
    except Exception as e:
        return ToolCallResponse(result=None, error=str(e))


@app.get("/tools/read_file", response_model=ToolCallResponse, tags=["Filesystem"])
async def read_file_endpoint(
    path: str, encoding: str = "utf-8", authenticated: bool = Depends(verify_token)
):
    """Read contents of a file in the workspace."""
    from .tools.filesystem_tools import read_file

    try:
        result = await read_file(path, encoding)
        return ToolCallResponse(result=result)
    except Exception as e:
        return ToolCallResponse(result=None, error=str(e))


class WriteFileRequest(BaseModel):
    path: str = Field(description="File path relative to workspace root")
    content: str = Field(description="Content to write")
    encoding: str = Field(default="utf-8", description="Text encoding")


@app.post("/tools/write_file", response_model=ToolCallResponse, tags=["Filesystem"])
async def write_file_endpoint(
    request: WriteFileRequest, authenticated: bool = Depends(verify_token)
):
    """Write content to a file in the workspace."""
    from .tools.filesystem_tools import write_file

    try:
        result = await write_file(request.path, request.content, request.encoding)
        return ToolCallResponse(result=result)
    except Exception as e:
        return ToolCallResponse(result=None, error=str(e))


class EditFileRequest(BaseModel):
    path: str = Field(description="File path relative to workspace root")
    old_text: str = Field(description="Text to find and replace")
    new_text: str = Field(description="Replacement text")
    occurrence: int | None = Field(
        None, description="Which occurrence to replace (1-indexed), None for all"
    )


@app.post("/tools/edit_file", response_model=ToolCallResponse, tags=["Filesystem"])
async def edit_file_endpoint(
    request: EditFileRequest, authenticated: bool = Depends(verify_token)
):
    """Edit a file by replacing text."""
    from .tools.filesystem_tools import edit_file

    try:
        result = await edit_file(
            request.path, request.old_text, request.new_text, request.occurrence
        )
        return ToolCallResponse(result=result)
    except Exception as e:
        return ToolCallResponse(result=None, error=str(e))


@app.delete("/tools/delete_file", response_model=ToolCallResponse, tags=["Filesystem"])
async def delete_file_endpoint(
    path: str, recursive: bool = False, authenticated: bool = Depends(verify_token)
):
    """Delete a file or directory in the workspace."""
    from .tools.filesystem_tools import delete_file

    try:
        result = await delete_file(path, recursive)
        return ToolCallResponse(result=result)
    except Exception as e:
        return ToolCallResponse(result=None, error=str(e))


class MoveFileRequest(BaseModel):
    source: str = Field(description="Source path relative to workspace root")
    destination: str = Field(description="Destination path relative to workspace root")


@app.post("/tools/move_file", response_model=ToolCallResponse, tags=["Filesystem"])
async def move_file_endpoint(
    request: MoveFileRequest, authenticated: bool = Depends(verify_token)
):
    """Move or rename a file/directory in the workspace."""
    from .tools.filesystem_tools import move_file

    try:
        result = await move_file(request.source, request.destination)
        return ToolCallResponse(result=result)
    except Exception as e:
        return ToolCallResponse(result=None, error=str(e))


# Shell tools


class ExecuteCommandRequest(BaseModel):
    command: str = Field(description="Shell command to execute")
    timeout: int = Field(default=30, description="Timeout in seconds")
    cwd: str | None = Field(None, description="Working directory relative to workspace")
    env: dict[str, str] | None = Field(
        None, description="Additional environment variables"
    )


@app.post("/tools/execute_command", response_model=ToolCallResponse, tags=["Shell"])
async def execute_command_endpoint(
    request: ExecuteCommandRequest, authenticated: bool = Depends(verify_token)
):
    """Execute a shell command in the workspace."""
    from .tools.shell_tools import execute_command

    try:
        result = await execute_command(
            request.command, request.timeout, request.cwd, request.env
        )
        return ToolCallResponse(result=result)
    except Exception as e:
        return ToolCallResponse(result=None, error=str(e))


# Memory tools


class StoreMemoryRequest(BaseModel):
    content: str = Field(description="Knowledge content to store")
    tags: list[str] | None = Field(None, description="Categorical tags")
    metadata: dict[str, Any] | None = Field(None, description="Additional metadata")


@app.post("/tools/store_memory", response_model=ToolCallResponse, tags=["Memory"])
async def store_memory_endpoint(
    request: StoreMemoryRequest, authenticated: bool = Depends(verify_token)
):
    """Store knowledge in semantic memory."""
    from .tools.memory_tools import store_memory

    try:
        result = await store_memory(request.content, request.tags, request.metadata)
        return ToolCallResponse(result=result)
    except Exception as e:
        return ToolCallResponse(result=None, error=str(e))


@app.get("/tools/recall_memory", response_model=ToolCallResponse, tags=["Memory"])
async def recall_memory_endpoint(
    query: str,
    limit: int = 5,
    tags: str | None = None,  # Comma-separated tags
    authenticated: bool = Depends(verify_token),
):
    """Recall memories using semantic search."""
    from .tools.memory_tools import recall_memory

    try:
        tag_list = tags.split(",") if tags else None
        result = await recall_memory(query, limit, tag_list)
        return ToolCallResponse(result=result)
    except Exception as e:
        return ToolCallResponse(result=None, error=str(e))


@app.get("/tools/list_memories", response_model=ToolCallResponse, tags=["Memory"])
async def list_memories_endpoint(
    limit: int = 20,
    tags: str | None = None,  # Comma-separated tags
    since: str | None = None,
    authenticated: bool = Depends(verify_token),
):
    """List stored memories with optional filtering."""
    from .tools.memory_tools import list_memories

    try:
        tag_list = tags.split(",") if tags else None
        result = await list_memories(limit, tag_list, since)
        return ToolCallResponse(result=result)
    except Exception as e:
        return ToolCallResponse(result=None, error=str(e))


@app.delete("/tools/delete_memory", response_model=ToolCallResponse, tags=["Memory"])
async def delete_memory_endpoint(
    memory_id: str, authenticated: bool = Depends(verify_token)
):
    """Delete a memory by ID."""
    from .tools.memory_tools import delete_memory

    try:
        result = await delete_memory(memory_id)
        return ToolCallResponse(result=result)
    except Exception as e:
        return ToolCallResponse(result=None, error=str(e))


@app.post("/tools/clear_all_memories", response_model=ToolCallResponse, tags=["Memory"])
async def clear_all_memories_endpoint(authenticated: bool = Depends(verify_token)):
    """Clear all memories (WARNING: irreversible!)."""
    from .tools.memory_tools import clear_all_memories

    try:
        result = await clear_all_memories()
        return ToolCallResponse(result=result)
    except Exception as e:
        return ToolCallResponse(result=None, error=str(e))


# Git tools


@app.get("/tools/git_status", response_model=ToolCallResponse, tags=["Git"])
async def git_status_endpoint(authenticated: bool = Depends(verify_token)):
    """Get git status of workspace."""
    from .tools.git_tools import git_status

    try:
        result = await git_status()
        return ToolCallResponse(result=result)
    except Exception as e:
        return ToolCallResponse(result=None, error=str(e))


@app.get("/tools/git_diff", response_model=ToolCallResponse, tags=["Git"])
async def git_diff_endpoint(
    path: str | None = None,
    staged: bool = False,
    authenticated: bool = Depends(verify_token),
):
    """Show git diff."""
    from .tools.git_tools import git_diff

    try:
        result = await git_diff(path, staged)
        return ToolCallResponse(result=result)
    except Exception as e:
        return ToolCallResponse(result=None, error=str(e))


class GitAddRequest(BaseModel):
    path: str = Field(default=".", description="Path to add")


@app.post("/tools/git_add", response_model=ToolCallResponse, tags=["Git"])
async def git_add_endpoint(
    request: GitAddRequest, authenticated: bool = Depends(verify_token)
):
    """Stage files for commit."""
    from .tools.git_tools import git_add

    try:
        result = await git_add(request.path)
        return ToolCallResponse(result=result)
    except Exception as e:
        return ToolCallResponse(result=None, error=str(e))


class GitCommitRequest(BaseModel):
    message: str = Field(description="Commit message")


@app.post("/tools/git_commit", response_model=ToolCallResponse, tags=["Git"])
async def git_commit_endpoint(
    request: GitCommitRequest, authenticated: bool = Depends(verify_token)
):
    """Commit staged changes."""
    from .tools.git_tools import git_commit

    try:
        result = await git_commit(request.message)
        return ToolCallResponse(result=result)
    except Exception as e:
        return ToolCallResponse(result=None, error=str(e))


@app.get("/tools/git_log", response_model=ToolCallResponse, tags=["Git"])
async def git_log_endpoint(
    limit: int = 10, authenticated: bool = Depends(verify_token)
):
    """Show commit history."""
    from .tools.git_tools import git_log

    try:
        result = await git_log(limit)
        return ToolCallResponse(result=result)
    except Exception as e:
        return ToolCallResponse(result=None, error=str(e))


class GitResetRequest(BaseModel):
    commit: str = Field(default="HEAD", description="Commit to reset to")
    hard: bool = Field(
        default=False, description="Perform hard reset (WARNING: discards changes)"
    )


@app.post("/tools/git_reset", response_model=ToolCallResponse, tags=["Git"])
async def git_reset_endpoint(
    request: GitResetRequest, authenticated: bool = Depends(verify_token)
):
    """Reset to a commit."""
    from .tools.git_tools import git_reset

    try:
        result = await git_reset(request.commit, request.hard)
        return ToolCallResponse(result=result)
    except Exception as e:
        return ToolCallResponse(result=None, error=str(e))


class GitRestoreRequest(BaseModel):
    path: str = Field(description="Path to restore")


@app.post("/tools/git_restore", response_model=ToolCallResponse, tags=["Git"])
async def git_restore_endpoint(
    request: GitRestoreRequest, authenticated: bool = Depends(verify_token)
):
    """Restore file to committed state."""
    from .tools.git_tools import git_restore

    try:
        result = await git_restore(request.path)
        return ToolCallResponse(result=result)
    except Exception as e:
        return ToolCallResponse(result=None, error=str(e))


@app.get("/tools/git_show", response_model=ToolCallResponse, tags=["Git"])
async def git_show_endpoint(
    commit: str = "HEAD", authenticated: bool = Depends(verify_token)
):
    """Show commit details."""
    from .tools.git_tools import git_show

    try:
        result = await git_show(commit)
        return ToolCallResponse(result=result)
    except Exception as e:
        return ToolCallResponse(result=None, error=str(e))


# Health check (no auth required)


@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "0.1.0"}


# OpenAPI spec endpoint (for ChatGPT Actions)


@app.get("/openapi.json", include_in_schema=False)
async def get_openapi_spec():
    """Get the OpenAPI specification."""
    return app.openapi()


def run_http_server(host: str = "0.0.0.0", port: int = 8000):
    """Run the HTTP server."""
    import uvicorn

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_http_server()
