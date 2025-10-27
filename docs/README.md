# A2IA - Aaron's AI Assistant

Dual-purpose MCP/HTTP server providing secure workspace operations for AI assistants.

## Quick Start

### Activate Virtual Environment
```bash
source .venv/bin/activate
```

### Run Tests
```bash
# All tests
pytest

# Unit tests only (26 passing)
pytest -m unit

# Integration tests (TODO)
pytest -m integration
```

### Run MCP Server (for Claude Desktop)
```bash
python -m a2ia.server --mode mcp
```

### Run HTTP Server (for ChatGPT Actions)
```bash
python -m a2ia.server --mode http --port 8000 --password poop
```

Access at:
- **Health**: http://localhost:8000/health
- **Docs**: http://localhost:8000/docs
- **OpenAPI**: http://localhost:8000/openapi.json

## Current Status

See [STATUS.md](STATUS.md) for detailed progress.

**Summary:**
- ✅ Secure workspace with 26 passing unit tests
- ✅ MCP server with FastMCP
- ✅ HTTP server with FastAPI + OpenAPI
- ✅ Bearer token auth for HTTP
- ✅ Workspace, filesystem, and shell tools
- 🚧 Integration tests (in progress)
- 🚧 Memory system with ChromaDB (TODO)

## Project Structure

```
a2ia/
├── a2ia/              # Main package
│   ├── core.py        # MCP app setup
│   ├── workspace.py   # Secure workspace
│   ├── server.py      # Dual-mode entry
│   ├── mcp_server.py  # MCP stdio server
│   ├── http_server.py # FastAPI HTTP server
│   └── tools/         # Tool implementations
├── tests/             # Test suite
├── STATUS.md          # Detailed status
└── CLAUDE.md          # Design docs
```

## Next Steps

1. Write integration tests for HTTP endpoints
2. Debug write_file JSON parsing issue
3. Implement memory system with ChromaDB
4. Test with Claude desktop & ChatGPT

See [STATUS.md](STATUS.md) and the TODO list for full details.
