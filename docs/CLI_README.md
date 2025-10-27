# A2IA CLI - Command Line Interface

A terminal-based interface for interacting with A2IA using local Ollama models and MCP tools.

## Quick Start

```bash
# Start the CLI
a2ia-cli

# Use a specific model
a2ia-cli --model qwen2.5:7b
a2ia-cli --model gemma3:4b
```

## Features

- **Interactive Chat** - Talk to A2IA using local Ollama models
- **MCP Tool Access** - Full access to all 26 A2IA tools
- **TUI Interface** - Clean terminal UI with scrolling output
- **Conversation History** - Maintains context across turns
- **Command Support** - `/quit`, `/clear`, `/tools`

## Available Models

Models are defined in `Modelfile` and created with `ollama create`:

**Recommended:**
- `a2ia-qwen` - Based on qwen2.5:7b, optimized for tool use (temp=0.2)

**Also Available:**
- `qwen2.5:7b` - Direct qwen2.5 (no custom prompt)
- `gemma3:4b` - Smaller, GPU-friendly
- `gemma3:12b` - Larger, better quality (may not fit in GPU)

## Architecture

```
┌─────────────┐
│  User Input │
└──────┬──────┘
       │
┌──────▼──────────────┐
│  CLI Interface      │  prompt_toolkit
│  (interface.py)     │
└──────┬──────────────┘
       │
┌──────▼──────────────┐
│  Orchestrator       │  Message routing
│  (orchestrator.py)  │  Tool call handling
└───┬──────────────┬──┘
    │              │
┌───▼────┐    ┌────▼────┐
│ Ollama │    │   MCP   │
│ Client │    │ Client  │
└───┬────┘    └────┬────┘
    │              │
┌───▼────┐    ┌────▼────┐
│ Model  │    │   A2IA  │
│(qwen2.5│    │   MCP   │
│  etc)  │    │  Server │
└────────┘    └────┬────┘
                   │
              ┌────▼────┐
              │  Tools  │
              │ (26)    │
              └─────────┘
```

## Commands

**In-Chat Commands:**
- `/quit` or `/exit` - Exit the CLI
- `/clear` - Clear conversation history
- `/tools` - List all available MCP tools

## Example Session

```
======================================================================
  A2IA - Aaron's AI Assistant
  Model: a2ia-qwen
======================================================================

Connecting to MCP server...
✅ Connected! 26 tools available

Type 'exit' or '/quit' to exit
Type '/clear' to clear conversation history
Type '/tools' to list available tools
======================================================================

You: Hello! What files are in the workspace?

A2IA: Let me check the workspace for you.

[calls list_directory tool]

The workspace contains several files including A2IA.md, pyproject.toml,
and directories like a2ia/, tests/, etc.

You: Create a file called hello.txt with "Hello World"

A2IA: I'll create that file for you.

[calls write_file tool]

Done! Created hello.txt with the content "Hello World".

You: /quit

👋 Goodbye!
```

## Development

**Running Tests:**
```bash
# All CLI tests
pytest tests/test_llm_client.py tests/test_mcp_client.py tests/test_orchestrator.py -v

# Just unit tests (fast)
pytest tests/test_llm_client.py::TestOllamaClient -v

# Integration (requires Ollama running)
pytest tests/test_llm_client.py::TestOllamaIntegration -v
```

**Creating Custom Models:**
```bash
# Edit Modelfile
vim Modelfile

# Create model
ollama create my-model -f Modelfile

# Test it
a2ia-cli --model my-model
```

## Troubleshooting

**"Ollama not running"**
- Start Ollama: `ollama serve`
- Check: `curl http://localhost:11434/api/tags`

**"Model not found"**
- List models: `ollama list`
- Pull model: `ollama pull qwen2.5:7b`
- Create custom: `ollama create a2ia-qwen -f Modelfile`

**"MCP server failed to start"**
- Test MCP server: `python3 -m a2ia.server --mode mcp`
- Check A2IA is installed: `pip install -e .`

**Tools not working**
- Ensure MCP server path is correct
- Check workspace permissions
- Try: `python3 -m a2ia.server --mode mcp` manually

## Model Comparison

We tested several models for tool usage:

| Model | Size | Concise? | Tool Calling | Notes |
|-------|------|----------|--------------|-------|
| qwen2.5:7b | 4.7GB | ✅ Yes | ✅ Good | **Recommended** - One sentence response |
| qwen3-coder | 18GB | ❌ No | ❓ Unknown | Wrote 400+ lines for "Hello"! |
| gpt-oss | 13GB | ❌ No | ❓ Unknown | Verbose "thinking" output |
| gemma3:4b | 2.5GB | ❓ TBD | ❓ TBD | Smaller, GPU-friendly |
| gemma3:12b | 8GB | ❓ TBD | ❓ TBD | Better quality |

**Winner (so far): qwen2.5:7b** ✅

## Configuration

The `Modelfile` contains:
- Base model (`FROM qwen2.5:7b`)
- System prompt (from NEWPROMPT.md)
- Temperature 0.2 (for consistent tool calling)
- 32k context window
- Stop tokens

## Next Steps

1. ✅ Test qwen2.5:7b - **Works great!**
2. ⏳ Test gemma3:4b when downloaded
3. ⏳ Test gemma3:12b when downloaded
4. Select final model based on performance
5. Full integration test with real workspace tasks

---

**Status: CLI is functional and ready to use with qwen2.5:7b!** 🚀
