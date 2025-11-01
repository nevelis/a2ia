# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**A2IA** (Aaron's AI Assistant) is a dual-purpose MCP/OpenAPI server that provides AI workspace operations with persistent memory, Git integration, and comprehensive tooling. The architecture follows the **A2IA Codex** principles documented in `docs/A2IA-Codex.md`.

### Core Architecture

A2IA operates in two modes via a single unified codebase:

1. **MCP Mode** (`--mode mcp`): stdio-based MCP server for Claude Desktop
2. **HTTP Mode** (`--mode http`): RESTful FastAPI server with OpenAPI spec for ChatGPT Actions and other HTTP clients

Both modes expose identical capabilities through different protocols, implemented via:
- **Shared core** (`a2ia/core.py`): Workspace lifecycle and MCP app initialization
- **Unified tools** (`a2ia/tools/`): Domain functions called by both MCP decorators and REST endpoints
- **Workspace abstraction** (`a2ia/workspace.py`): Sandboxed file operations with path resolution
- **REST server** (`a2ia/rest_server.py`): RESTful HTTP endpoints wrapping tool functions
- **MCP server** (`a2ia/mcp_server.py`): FastMCP-based stdio server

## Development Commands

### Environment Setup
```bash
# Activate virtual environment (always required)
source .venv/bin/activate

# Install dependencies (if pyproject.toml changes)
pip install -e ".[dev]"
```

### Testing
```bash
# Run all tests
pytest

# Run with quiet output
pytest --quiet

# Run specific test markers
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests (require services)
pytest -m slow          # Slow-running tests

# Run specific test file
pytest tests/test_memory.py -v

# Run with coverage
pytest --cov=a2ia --cov-report=html
```

### Code Quality
```bash
# Lint with ruff (follows pyproject.toml config)
ruff check .

# Format with ruff
ruff format .

# Type check with mypy
mypy a2ia/
```

### Running the Server

```bash
# MCP mode (for Claude Desktop)
python -m a2ia.server --mode mcp

# HTTP mode (for ChatGPT/web clients)
python -m a2ia.server --mode http --host 0.0.0.0 --port 8000

# Override password
python -m a2ia.server --mode http --password custom_password

# Access points in HTTP mode:
# - Docs: http://localhost:8000/docs
# - OpenAPI: http://localhost:8000/openapi.json
# - Health: http://localhost:8000/health
```

### CLI Interface
```bash
# Interactive CLI with local LLM (experimental)
a2ia-cli

# CLI with vLLM backend
a2ia-cli-vllm
```

### Deployment
```bash
# Sync code to production server (amazingland.live)
make rsync

# Deploy (rsync + manual restart)
make deploy

# Clean local artifacts
make clean
```

## Architecture Patterns

### Tool Implementation Pattern

All tools follow a three-layer architecture:

1. **Domain function** (pure Python in `a2ia/tools/businessmap.py`, etc.): Core logic with no decorators
2. **MCP wrapper** (in `a2ia/tools/businessmap_tools.py`): `@mcp.tool()` decorator, returns JSON strings
3. **REST endpoint** (in `a2ia/rest_server.py`): FastAPI route, returns Pydantic models or JSONResponse

Example:
```python
# 1. Domain function (businessmap.py)
def get_card(card_id: int) -> dict:
    """Core API logic"""
    return api_client.get(f"/cards/{card_id}")

# 2. MCP wrapper (businessmap_tools.py)
@mcp.tool()
def get_businessmap_card(card_id: int) -> str:
    """MCP-exposed tool"""
    return json.dumps(get_card(card_id))

# 3. REST endpoint (rest_server.py)
@app.get("/businessmap/cards/{card_id}")
def get_card_endpoint(card_id: int):
    """REST endpoint"""
    return get_card(card_id)
```

### Workspace Path Resolution

The `Workspace` class (`a2ia/workspace.py`) implements **sandbox-safe path resolution**:

- **Absolute paths within workspace**: `/home/user/workspace/file.txt` → returned as-is if within workspace
- **Workspace-relative paths**: `/file.txt` → `workspace/file.txt`
- **Regular relative paths**: `file.txt` → `workspace/file.txt`

This prevents path traversal attacks while supporting multiple path formats. The workspace is configured via `A2IA_WORKSPACE_PATH` environment variable (defaults to `.`).

### Memory System

A2IA includes a **semantic memory system** using ChromaDB (`a2ia/tools/memory_tools.py`):

- **Tag-based recall**: Case-insensitive tag matching
- **Semantic search**: Vector embeddings with sentence-transformers
- **Persistent storage**: Local ChromaDB instance in `memory/` directory
- **MCP resources**: Exposes memory entries as MCP resources

### Test Infrastructure

Tests follow strict patterns defined in `tests/conftest.py`:

- **Isolated workspaces**: Each test gets a temporary workspace via `tmp_workspace` fixture
- **Sandbox environment**: `A2IA_WORKSPACE_PATH` set to temp directory
- **Git initialization**: Auto-initialized Git repo for tests requiring version control
- **Cleanup**: Automatic teardown after each test

Key test markers (defined in `pyproject.toml`):
- `@pytest.mark.unit`: Fast, isolated unit tests
- `@pytest.mark.integration`: Tests requiring running services
- `@pytest.mark.e2e`: End-to-end workflow tests
- `@pytest.mark.slow`: Long-running tests

## Development Philosophy (from A2IA Codex)

The project follows the **A2IA Codex** (`docs/A2IA-Codex.md`) doctrine:

1. **Test-Driven Development**: TDD is mandatory, not optional. Write failing tests first.
2. **Zero Warnings Policy**: All pytest warnings must be eliminated. Warnings are "ghosts of future failures."
3. **Latest Stable Versions**: Always use GA/LTS versions of dependencies.
4. **Transparency Over Abstraction**: Every layer must be explainable in under 5 minutes.
5. **No Opaque Tooling**: No Helm, NPX, or black-box automation.
6. **Documentation is Architecture**: `A2IA.md` and related docs are living system truth.

## Key Files and Directories

### Core System
- `a2ia/server.py`: Entry point with mode selection (MCP vs HTTP)
- `a2ia/core.py`: MCP app initialization and workspace management
- `a2ia/workspace.py`: Sandboxed workspace abstraction with path resolution
- `a2ia/rest_server.py`: FastAPI REST server (~1500 lines, 23+ endpoints)
- `a2ia/mcp_server.py`: FastMCP stdio server

### Tool Modules
- `a2ia/tools/filesystem_tools.py`: File operations (read, write, patch, grep, etc.)
- `a2ia/tools/git_tools.py`: Git operations (status, diff, commit, log, etc.)
- `a2ia/tools/git_sdlc_tools.py`: SDLC workflow integration
- `a2ia/tools/memory_tools.py`: Semantic memory with ChromaDB
- `a2ia/tools/businessmap_tools.py`: Businessmap/Kanbanize integration
- `a2ia/tools/terraform_tools.py`: IaC operations
- `a2ia/tools/ci_tools.py`: CI/CD tooling
- `a2ia/tools/shell_tools.py`: Shell command execution

### Client/Orchestration
- `a2ia/client/orchestrator.py`: ReAct loop orchestrator for autonomous LLM agents
- `a2ia/client/react_parser.py`: ReAct format parser (Thought/Action/Observation)
- `a2ia/client/vllm_client.py`: vLLM client integration
- `a2ia/client/llm_base.py`: Base LLM client interface
- `a2ia/client/tool_validator.py`: Tool call validation

### CLI
- `a2ia/cli/interface.py`: Interactive CLI with prompt_toolkit (~600 lines)

### Documentation
- `docs/A2IA-Codex.md`: Authoritative doctrine and architectural principles
- `docs/A2IA.md`: Development log and architecture overview
- `docs/A2IA-Chronicle.md`: Epoch-based development history
- `docs/A2IA-Continuum.md`: Current development roadmap
- `BUSINESSMAP_INTEGRATION.md`: Businessmap integration guide
- `TOOL_SCHEMA_GENERATION.md`: Tool schema generation for Ollama

## Common Development Patterns

### Running a Single Test
```bash
# With verbose output
pytest tests/test_memory.py::test_store_memory -v

# With print debugging
pytest tests/test_memory.py::test_store_memory -v -s

# Stop on first failure
pytest tests/test_memory.py -x
```

### Adding a New Tool

1. Implement domain function in appropriate `a2ia/tools/*.py` module
2. Add `@mcp.tool()` wrapper in MCP tools module (or same file)
3. Add REST endpoint in `a2ia/rest_server.py`
4. Write tests in `tests/test_*.py`
5. Update OpenAPI schema (auto-generated from FastAPI)

### Working with Modelfiles

The project includes multiple `Modelfile-*` configurations for Ollama models with tool calling:

- `Modelfile`: Main model configuration
- `Modelfile-capybara`: Capybara model with ReAct tools
- `Modelfile-qwen`: Qwen model configuration
- `Modelfile-mistral`: Mistral model setup

Tool schemas are generated via `scripts/` and `run_tool_schema.sh`.

### Memory System Usage

```python
from a2ia.tools.memory_tools import store_memory, recall_memory

# Store memory with tags
store_memory(
    content="Implementation detail about X",
    tags=["architecture", "X-system"]
)

# Recall by tag (case-insensitive)
memories = recall_memory(tag="Architecture")  # Finds "architecture" tag

# Semantic search
memories = recall_memory(query="how does X work?", limit=5)
```

## Integration Notes

### Businessmap/Kanbanize
See `BUSINESSMAP_INTEGRATION.md` for:
- 12 MCP tools + REST endpoints
- Team roster management in `a2ia/tools/data.py`
- Rate limiting and retry logic
- Mock data for testing

### Git Integration
Git is auto-initialized in workspaces with:
- User: `A2IA <a2ia@localhost>`
- Initial empty commit
- Full SDLC workflow tools (branch, commit, push, PR, etc.)

### vLLM Integration
Experimental vLLM support for local LLM hosting:
- See `docs/VLLM_*.md` for setup guides
- Supports tool calling via ReAct format
- Configured in `a2ia/client/vllm_client.py`

## Environment Variables

- `A2IA_WORKSPACE_PATH`: Workspace directory (default: `.`)
- `A2IA_PASSWORD`: API password for HTTP mode (default: `poop`)
- `BUSINESSMAP_API_KEY`: Businessmap API key (if using integration)
- `BUSINESSMAP_SUBDOMAIN`: Businessmap subdomain (if using integration)

## Production Deployment

The production server runs on `amazingland.live`:
- URL: `https://a2ia.amazingland.live`
- Deployment via `make rsync` or `make deploy`
- Workspace: `~/a2ia/` on server
- Restart command: `cd ~/a2ia && .venv/bin/python -m a2ia.server --mode http --host 127.0.0.1 --port 8000`

## Troubleshooting

### "Workspace path resolution error"
Ensure `A2IA_WORKSPACE_PATH` is set correctly and points to an existing directory.

### "MCP tool not found"
Check that tools are properly decorated with `@mcp.tool()` and imported in the MCP server.

### "Tests failing with path issues"
Tests use isolated temp workspaces. Check that `tmp_workspace` fixture is being used.

### Memory/ChromaDB Issues
ChromaDB stores data in `memory/` directory. Delete this directory to reset memory state.
