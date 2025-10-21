# Quick Restart Guide

## Immediately After Restart

```bash
# 1. Verify tests pass (venv already activated)
pytest --quiet

# 2. Start HTTP server (for ChatGPT Actions)
python -m a2ia.server --mode http --port 8000

# 3. Start MCP server (for Claude Desktop)
python -m a2ia.server --mode mcp
```

## What's Working - Single Workspace Model ✅

✅ **26 Tools** - All operational via MCP and HTTP
  - 6 Filesystem tools (read, write, edit, list, delete, move)
  - 11 Git tools (status, diff, add, commit, log, reset, restore, show, branch, checkout)
  - 1 Shell tool (execute_command)
  - 5 Memory tools (store, recall, list, delete, clear)
  - 3 Workspace info tools (backward compatible)

✅ **91 Tests Passing** - Full test coverage
  - 26 unit tests - Workspace security
  - 22 HTTP integration tests - All endpoints
  - 25 MCP integration tests - All tools
  - 18 memory system tests - ChromaDB vector storage

✅ **Auto-Initialized Workspace** - Zero configuration
  - Persistent workspace at `./workspace`
  - Automatic Git repository initialization
  - Memory stored in `workspace/memory/`
  - Everything persists across restarts

✅ **Git Integration** - Built-in version control
  - Every operation can be committed
  - Easy rollback with git_reset
  - View history with git_log
  - Branch and experiment safely

✅ **Dual-Mode Server** - Works everywhere
  - MCP mode for Claude Desktop
  - HTTP mode for ChatGPT Actions
  - OpenAPI spec at `/openapi.json`
  - Interactive docs at `/docs`

## Architecture Highlights

**Simplified Model:**
- Single persistent workspace (no multi-workspace complexity)
- Auto-initialization (no workspace creation needed)
- Git repository by default (automatic version control)
- No session management (perfect for personal/team use)
- No OAuth complexity (simple bearer token for HTTP)

**Workspace Location:**
```bash
# Default
./workspace

# Custom (set before starting server)
export A2IA_WORKSPACE_PATH=/custom/path
```

## Quick Workflow Examples

### Filesystem + Git Workflow
```python
# 1. Write code (no setup needed!)
write_file("app.py", "print('Hello')")

# 2. Check what changed
git_status()

# 3. Commit when stable
git_add(".")
git_commit("Add hello world app")

# 4. View history
git_log(limit=5)

# 5. Rollback if needed
git_reset("HEAD~1", hard=True)
```

### Memory System Workflow
```python
# Store knowledge
store_memory(
    "Project uses Python 3.13 with FastAPI",
    tags=["tech-stack", "backend"]
)

# Recall later
recall_memory("what tech stack?", limit=3)

# List all memories
list_memories(tags=["tech-stack"])
```

### Shell Execution
```python
# Run tests
execute_command("pytest -v")

# Install package
execute_command("pip install requests")

# Run app
execute_command("python app.py")
```

## Key Files

- **`STATUS.md`** - Detailed system status and features
- **`CLAUDE.md`** - Full architecture and design documentation
- **`./workspace/`** - Your persistent workspace with Git
- **`./workspace/memory/`** - ChromaDB vector storage
- **`pyproject.toml`** - Project configuration

## Configuration Options

```bash
# Workspace location
export A2IA_WORKSPACE_PATH=/path/to/workspace

# Memory storage location
export A2IA_MEMORY_PATH=/path/to/memory

# HTTP server password
export A2IA_PASSWORD=your-secret-token
```

## Testing

```bash
# All tests
pytest

# Unit tests only (fast)
pytest -m unit

# Integration tests
pytest -m integration

# Specific test suite
pytest tests/test_workspace.py -v

# With coverage
pytest --cov=a2ia
```

## Troubleshooting

**Workspace not initializing?**
- Check `A2IA_WORKSPACE_PATH` is writable
- Ensure Git is installed for version control

**Memory system errors?**
- Check `workspace/memory/` directory exists
- ChromaDB needs write permissions

**HTTP auth failing?**
- Use header: `Authorization: Bearer poop`
- Or set custom password with `A2IA_PASSWORD`

## System is Production-Ready

All core features implemented and tested:
- ✅ Persistent workspace with Git
- ✅ 26 tools working (filesystem, git, shell, memory)
- ✅ MCP server operational
- ✅ HTTP server with OpenAPI
- ✅ 91 tests passing
- ✅ Documentation complete

**Ready for immediate use in:**
- Personal development workflows
- AI-assisted coding sessions
- Team collaboration
- ChatGPT Actions integration
- Claude Desktop integration

---

Last Updated: 2025-10-20
Version: 0.2.0 (Simplified Single Workspace)
