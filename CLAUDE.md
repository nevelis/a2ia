# A2IA - Aaron's AI Assistant

A dual-purpose server that provides both MCP (Model Context Protocol) tools for Claude and OpenAPI endpoints for ChatGPT Actions. Designed to give AI assistants secure access to a persistent workspace with filesystem operations, shell execution, Git version control, and semantic memory.

## Overview

A2IA enables AI assistants to:
- Work in a **single persistent workspace** with automatic Git version control
- Perform secure filesystem operations (read, write, edit, list, traverse)
- Execute shell commands within the workspace
- Use Git for version control (commit, diff, reset, log, etc.)
- Store and retrieve knowledge using a vector-based memory system
- Everything persists across sessions - no setup required!

The server exposes tools through two interfaces:
1. **MCP Protocol** - For Claude Code and other MCP-compatible clients
2. **OpenAPI/REST** - For ChatGPT Actions and HTTP-based integrations

## Key Features

✅ **Zero Configuration** - Workspace auto-initializes on first use
✅ **Git Integration** - Automatic version control with 11 git tools
✅ **Persistent Storage** - All files survive server restarts
✅ **Semantic Memory** - ChromaDB vector storage for knowledge
✅ **Secure Sandbox** - Path validation prevents directory escape
✅ **26 Total Tools** - Everything you need in one place

## Quick Start

```bash
# Install dependencies
pip install -e ".[dev]"

# Start HTTP server (for ChatGPT Actions)
python -m a2ia.server --mode http --port 8000

# OR start MCP server (for Claude Desktop)
python -m a2ia.server --mode mcp

# Workspace auto-initializes at ./workspace with Git enabled!
```

### Typical Workflow

```python
# 1. Write code (no workspace creation needed!)
write_file("main.py", "print('Hello World')")

# 2. Run it
execute_command("python main.py")

# 3. Commit your progress
git_add(".")
git_commit("Add main.py")

# 4. View history
git_log(limit=5)

# 5. Store knowledge
store_memory("This project uses Python 3.13", tags=["project-info"])

# 6. Rollback if needed
git_reset("HEAD~1", hard=True)
```

## Architecture

### Dual-Purpose Design

```
┌─────────────────────────────────────────────┐
│         Decorator-Based Tool Framework      │
│  @tool("name", "description", schema)       │
└─────────────────┬───────────────────────────┘
                  │
         ┌────────┴────────┐
         │                 │
         ▼                 ▼
┌─────────────────┐  ┌──────────────────┐
│   MCP Server    │  │  HTTP/REST API   │
│   (FastMCP)     │  │  (FastAPI)       │
│                 │  │  + OpenAPI spec  │
│  • stdio        │  │  • Password auth │
│  • native       │  │  • Public endpoint│
└─────────────────┘  └──────────────────┘
```

### Core Components

1. **Persistent Workspace**
   - Single workspace at `./workspace` (configurable via `A2IA_WORKSPACE_PATH`)
   - Auto-initialized on server startup
   - Automatic Git repository initialization
   - All operations scoped to workspace directory
   - Path validation prevents directory escape

2. **Filesystem Tools** (6 tools)
   - `list_directory` - List contents (with optional recursion)
   - `read_file` - Read file contents
   - `write_file` - Create/overwrite files
   - `edit_file` - Surgical edits using search & replace
   - `delete_file` - Remove files/directories
   - `move_file` - Rename/move files

3. **Git Version Control** (11 tools) 🆕
   - `git_status` - Show workspace status
   - `git_diff` - View changes
   - `git_add` - Stage files
   - `git_commit` - Commit changes
   - `git_log` - View history
   - `git_reset` - Rollback to previous state
   - `git_restore` - Discard changes to file
   - `git_show` - Show commit details
   - `git_branch` - List branches
   - `git_checkout` - Switch branches/commits

4. **Shell Execution** (1 tool)
   - `execute_command` - Run shell commands in workspace
   - Captures stdout/stderr
   - Timeout support
   - Environment variable support

5. **Memory System** (5 tools)
   - `store_memory` - Save knowledge with embeddings
   - `recall_memory` - Semantic search over memories
   - `list_memories` - Browse stored knowledge
   - `delete_memory` - Remove specific memory
   - `clear_all_memories` - Clear all memories
   - Uses ChromaDB for vector storage
   - Stored in `workspace/memory/`

6. **Workspace Info** (3 tools - backward compatible)
   - `create_workspace` - Returns info about persistent workspace
   - `get_workspace_info` - Get workspace details
   - `close_workspace` - No-op (workspace is always active)

## Security Model

### Workspace Isolation

All filesystem operations are restricted to the workspace directory:

```python
# Allowed
read_file("/workspace_abc123/src/main.py")
read_file("src/main.py")  # relative to workspace

# Blocked
read_file("/etc/passwd")
read_file("../../../etc/passwd")
read_file("/workspace_abc123/symlink_to_root")
```

Security measures:
- Path canonicalization using `os.path.realpath()`
- Verify resolved path starts with workspace root
- Reject symlinks that escape workspace
- Reject absolute paths outside workspace

### Authentication

**MCP Mode**: No authentication (local stdio/pipe)
**HTTP Mode**: Bearer token authentication with configurable password

```http
Authorization: Bearer poop
```

### Deployment

HTTP server is designed for public endpoints:
- HTTPS recommended (use reverse proxy)
- Rate limiting recommended (nginx/Cloudflare)
- Workspace isolation prevents cross-contamination

## Tool Specifications

### Workspace Management

#### `create_workspace`
```python
{
    "workspace_id": str (optional),  # Resume existing or create new
    "base_path": str (optional),     # Use existing directory
    "description": str (optional)     # Session description
}
→ {"workspace_id": "ws_abc123", "path": "/workspaces/ws_abc123"}
```

#### `get_workspace_info`
```python
{}
→ {
    "workspace_id": "ws_abc123",
    "path": "/workspaces/ws_abc123",
    "created_at": "2025-10-20T14:30:00Z",
    "description": "Feature X implementation"
}
```

### Filesystem Operations

#### `list_directory`
```python
{
    "path": str (optional, default ""),  # Relative to workspace
    "recursive": bool (optional, default False)
}
→ {
    "files": ["main.py", "utils.py"],
    "directories": ["src", "tests"],
    "path": "/workspace/src"
}
```

#### `read_file`
```python
{
    "path": str,                    # Relative to workspace
    "encoding": str (optional)      # Default: utf-8
}
→ {"content": "...", "size": 1234, "path": "src/main.py"}
```

#### `write_file`
```python
{
    "path": str,                    # Relative to workspace
    "content": str,
    "encoding": str (optional)
}
→ {"success": true, "path": "src/main.py", "size": 1234}
```

#### `edit_file`
```python
{
    "path": str,                    # Relative to workspace
    "old_text": str,                # Text to replace
    "new_text": str,                # Replacement text
    "occurrence": int (optional)    # Which match (default: all)
}
→ {"success": true, "changes": 1, "path": "src/main.py"}
```

#### `delete_file`
```python
{
    "path": str,                    # Relative to workspace
    "recursive": bool (optional)    # For directories
}
→ {"success": true, "path": "old_code.py"}
```

#### `move_file`
```python
{
    "source": str,                  # Relative to workspace
    "destination": str              # Relative to workspace
}
→ {"success": true, "source": "old.py", "destination": "new.py"}
```

### Shell Execution

#### `execute_command`
```python
{
    "command": str,                     # Shell command
    "timeout": int (optional),          # Seconds (default: 30)
    "cwd": str (optional),             # Working dir in workspace
    "env": dict (optional)              # Additional env vars
}
→ {
    "stdout": "...",
    "stderr": "...",
    "returncode": 0,
    "duration": 1.23
}
```

### Memory System

#### `store_memory`
```python
{
    "content": str,                     # Knowledge to store
    "tags": list[str] (optional),      # Categorical tags
    "metadata": dict (optional)         # Additional context
}
→ {
    "memory_id": "mem_xyz789",
    "stored_at": "2025-10-20T14:35:00Z"
}
```

#### `recall_memory`
```python
{
    "query": str,                       # Semantic search query
    "limit": int (optional),           # Max results (default: 5)
    "tags": list[str] (optional)       # Filter by tags
}
→ {
    "memories": [
        {
            "memory_id": "mem_xyz789",
            "content": "...",
            "similarity": 0.87,
            "tags": ["architecture", "decision"],
            "stored_at": "2025-10-20T14:35:00Z"
        }
    ]
}
```

#### `list_memories`
```python
{
    "limit": int (optional),           # Max results (default: 20)
    "tags": list[str] (optional),      # Filter by tags
    "since": str (optional)            # ISO timestamp filter
}
→ {"memories": [...], "total": 42}
```

## Usage Examples

### ChatGPT Action Configuration

1. Get the OpenAPI spec:
```bash
curl https://your-server.com/openapi.json > a2ia-spec.json
```

2. In ChatGPT:
   - Go to "Configure" → "Create new action"
   - Paste the OpenAPI spec
   - Set authentication to "Bearer" with token "poop"
   - Save action

3. Use in conversation:
```
User: Create a workspace and implement a Python calculator
GPT: [Calls create_workspace]
     [Calls write_file with calculator code]
     [Calls execute_command to run tests]
     Done! I've implemented a calculator in calculator.py
```

### Claude MCP Configuration

Add to `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "a2ia": {
      "command": "python",
      "args": ["-m", "a2ia.server", "--mode=mcp"],
      "cwd": "/path/to/a2ia"
    }
  }
}
```

### HTTP Server Deployment

```bash
# Development
python -m a2ia.server --mode=http --port=8000 --password=poop

# Production (behind nginx/caddy with HTTPS)
gunicorn a2ia.server:app \
  --bind 0.0.0.0:8000 \
  --workers 4 \
  --timeout 120 \
  -e A2IA_PASSWORD=poop \
  -e A2IA_WORKSPACE_ROOT=/var/workspaces
```

## Implementation Details

### Technology Stack

- **FastMCP**: MCP protocol server (follows bender reference)
- **FastAPI**: HTTP/REST API with OpenAPI generation
- **ChromaDB**: Vector database for memory system
- **Pydantic**: Schema validation and type safety
- **sentence-transformers**: Embedding generation

### Project Structure

```
a2ia/
├── server.py              # Main entry point, dual-mode server
├── decorators.py          # @tool decorator and registration
├── workspace.py           # Workspace management and security
├── tools/
│   ├── __init__.py
│   ├── filesystem.py      # File operation tools
│   ├── shell.py           # Command execution
│   └── memory.py          # Vector memory system
├── http_server.py         # FastAPI HTTP server
├── mcp_server.py          # FastMCP MCP server
├── auth.py                # Authentication middleware
├── openapi_gen.py         # OpenAPI spec generation
├── tests/
│   ├── test_workspace.py  # Security and path validation
│   ├── test_tools.py      # Tool functionality
│   └── test_integration.py
└── requirements.txt
```

### Decorator Framework

Tools are defined once and work for both protocols:

```python
from a2ia.decorators import tool

@tool(
    name="read_file",
    description="Read contents of a file in the workspace",
    schema={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "File path"},
        },
        "required": ["path"]
    }
)
async def read_file(path: str, workspace: Workspace) -> dict:
    """Implementation..."""
    content = workspace.read_file(path)
    return {"content": content, "path": path}
```

The decorator automatically:
- Registers for MCP server
- Creates REST endpoint
- Generates OpenAPI schema
- Handles workspace injection
- Validates inputs

## Development Workflow

### TDD Process

Following the A2IA system prompt philosophy:

1. **Specification** - Document requirements clearly
2. **Test Design** - Write failing tests first
3. **Implementation** - Make tests pass
4. **Validation** - Run full test suite
5. **Self-Review** - Refactor and improve
6. **Documentation** - Update as needed

### Running Tests

```bash
# All tests
pytest

# Security tests
pytest tests/test_workspace.py -v

# Integration tests
pytest tests/test_integration.py -v

# With coverage
pytest --cov=a2ia --cov-report=html
```

### Code Quality

```bash
# Format
ruff format .

# Lint
ruff check .

# Type check
mypy a2ia/
```

## Roadmap

### Phase 1: Core Infrastructure ✓
- Decorator framework
- Workspace management with security
- Basic filesystem tools
- HTTP + MCP servers

### Phase 2: Essential Tools ✓
- All filesystem operations
- Shell execution
- OpenAPI generation
- Authentication

### Phase 3: Memory System ✓
- Vector store integration
- Embedding generation
- Semantic search
- Tag-based filtering

### Phase 4: Production Ready
- Rate limiting
- Usage metrics
- Workspace cleanup/archival
- Multi-user support
- Webhook notifications

### Phase 5: Advanced Features
- File watching/hot reload
- Collaborative workspaces
- Git integration
- Docker container support
- Code analysis tools

## Design Decisions

### Why Dual-Purpose?

Testing and development workflow:
1. Develop with Claude using MCP (native, fast)
2. Deploy for ChatGPT using HTTP (portable, standard)
3. Share same codebase, ensure consistency

### Why ChromaDB?

- Embedded (no separate server needed)
- Fast semantic search
- Simple Python API
- Automatic embedding generation
- Production-ready with persistence

### Why Workspace Isolation?

AI assistants need freedom to operate but must be contained:
- Prevents accidental system damage
- Enables safe multi-tenancy
- Simplifies cleanup and archival
- Allows experimentation without risk

### Why Memory System?

AI context windows are limited:
- Store discoveries and insights
- Avoid redundant analysis
- Build cumulative knowledge
- Enable long-running projects

## Contributing

This is Aaron's personal project but follows professional standards:
- Write tests for all features
- Follow TDD workflow
- Document decisions in commit messages
- Keep code clean and maintainable

## License

Private project - All rights reserved.
