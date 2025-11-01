# Capybara Model Integration with A2IA ✅

## Overview

A2IA is now integrated with your custom SDLC-trained Capybara models based on Llama 3.1 8B.

## Default Configuration

A2IA defaults to `capybara-sdlc:latest` for full tool calling support.

```bash
a2ia-cli  # Automatically uses capybara-sdlc:latest
```

## Available Capybara Models

| Model | Size | Tool Support | Command |
|-------|------|--------------|---------|
| `capybara-sdlc:latest` | 16 GB | ✅ Full | `a2ia-cli` (default) |
| `capybara-gguf:latest` | 4.9 GB | ✅ Full | `a2ia-cli --model capybara-gguf:latest` |

Both models support all A2IA MCP tools (file operations, git, shell commands, etc.)

## Quick Start

```bash
# Use default (non-quantized)
a2ia-cli

# Use quantized version
a2ia-cli --model capybara-gguf:latest

# Use with debug mode
a2ia-cli --debug

# Show model thinking
a2ia-cli --show-thinking
```

## Model Capabilities

Your Capybara models are trained on:
- Sprint planning
- Architecture review
- Effort estimation
- Rollout planning
- Resource allocation
- Technical decision-making

Plus standard A2IA capabilities:
- File operations (read, write, patch)
- Git version control
- Shell command execution
- Memory management

## Switching Models

```bash
# Back to Qwen if needed
a2ia-cli --model a2ia-qwen

# Use any other Ollama model
a2ia-cli --model llama3.1:8b-instruct-q4_K_M
```

## Configuration Files

- Default model: `a2ia/cli/interface.py` (line 519)
- LLM client default: `a2ia/client/llm.py` (line 14)

## Troubleshooting

### Model Not Found
```bash
cd /home/aaron/dev/nevelis/capybara
bash scripts/create_capybara_sdlc.sh
```

### Need Quantized Version
```bash
cd /home/aaron/dev/nevelis/capybara
bash scripts/convert_to_gguf.sh
bash scripts/create_gguf_model.sh
```

### Tool Calling Issues
Both capybara models now have fixed templates and support full tool calling.
If you encounter issues, verify the model was created with the latest Modelfiles.

## Status

✅ Fully integrated and operational
✅ Tool calling working on both models
✅ SDLC training preserved
✅ Production ready

Your custom SDLC-trained models are now the foundation of A2IA! 🦫

