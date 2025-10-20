"""FastAPI HTTP server for A2IA.

Exposes MCP tools as HTTP endpoints with OpenAPI documentation.
"""

import os
from typing import Any, Dict, Optional
from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .core import get_mcp_app

# Import all tools to register them
from .tools import workspace_tools, filesystem_tools, shell_tools

# Configuration
API_PASSWORD = os.getenv("A2IA_PASSWORD", "poop")

# FastAPI app
app = FastAPI(
    title="A2IA - Aaron's AI Assistant",
    description="Secure workspace operations for AI assistants. Provides filesystem access, shell execution, and memory management within isolated workspaces.",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Security
security = HTTPBearer()


def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> bool:
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
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Tool arguments")


class ToolCallResponse(BaseModel):
    """Response from calling a tool."""
    result: Any = Field(description="Tool execution result")
    error: Optional[str] = Field(None, description="Error message if execution failed")


# Workspace tools

@app.post("/tools/create_workspace", response_model=ToolCallResponse, tags=["Workspace"])
async def create_workspace_endpoint(
    workspace_id: Optional[str] = None,
    base_path: Optional[str] = None,
    description: Optional[str] = None,
    authenticated: bool = Depends(verify_token)
):
    """Create or resume a workspace for the current session."""
    from .tools.workspace_tools import create_workspace
    try:
        result = await create_workspace(workspace_id, base_path, description)
        return ToolCallResponse(result=result)
    except Exception as e:
        return ToolCallResponse(result=None, error=str(e))


@app.get("/tools/get_workspace_info", response_model=ToolCallResponse, tags=["Workspace"])
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
    path: str = "",
    recursive: bool = False,
    authenticated: bool = Depends(verify_token)
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
    path: str,
    encoding: str = "utf-8",
    authenticated: bool = Depends(verify_token)
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
    request: WriteFileRequest,
    authenticated: bool = Depends(verify_token)
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
    occurrence: Optional[int] = Field(None, description="Which occurrence to replace (1-indexed), None for all")


@app.post("/tools/edit_file", response_model=ToolCallResponse, tags=["Filesystem"])
async def edit_file_endpoint(
    request: EditFileRequest,
    authenticated: bool = Depends(verify_token)
):
    """Edit a file by replacing text."""
    from .tools.filesystem_tools import edit_file
    try:
        result = await edit_file(request.path, request.old_text, request.new_text, request.occurrence)
        return ToolCallResponse(result=result)
    except Exception as e:
        return ToolCallResponse(result=None, error=str(e))


@app.delete("/tools/delete_file", response_model=ToolCallResponse, tags=["Filesystem"])
async def delete_file_endpoint(
    path: str,
    recursive: bool = False,
    authenticated: bool = Depends(verify_token)
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
    request: MoveFileRequest,
    authenticated: bool = Depends(verify_token)
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
    cwd: Optional[str] = Field(None, description="Working directory relative to workspace")
    env: Optional[Dict[str, str]] = Field(None, description="Additional environment variables")


@app.post("/tools/execute_command", response_model=ToolCallResponse, tags=["Shell"])
async def execute_command_endpoint(
    request: ExecuteCommandRequest,
    authenticated: bool = Depends(verify_token)
):
    """Execute a shell command in the workspace."""
    from .tools.shell_tools import execute_command
    try:
        result = await execute_command(request.command, request.timeout, request.cwd, request.env)
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
