# A2IA vLLM Integration

**Status:** ✅ Complete and Tested  
**Date:** 2025-10-27  
**Test Coverage:** 7/7 tests passing

## Overview

A2IA now supports **vLLM** as an alternative backend to Ollama, allowing you to run powerful models like Mixtral 8x7B with optimized inference performance. The implementation follows A2IA's unified `LLMClient` interface, making backends interchangeable.

## Architecture

```
┌─────────────────────────────────────────────┐
│         A2IA CLI Interface                  │
│  (Single unified CLI with --backend flag)  │
└─────────────────┬───────────────────────────┘
                  │
        ┌─────────┴──────────┐
        │                    │
┌───────▼────────┐   ┌───────▼────────┐
│ OllamaClient   │   │  VLLMClient    │
│  (localhost    │   │  (OpenAI-      │
│   :11434)      │   │   compatible   │
└────────────────┘   │   API)         │
                     └────────────────┘
         │                    │
         └────────┬───────────┘
                  │
        ┌─────────▼──────────┐
        │   LLMClient Base   │
        │   (Abstract)       │
        └────────────────────┘
                  │
        ┌─────────▼──────────┐
        │   Orchestrator     │
        │   (LLM + MCP       │
        │    integration)    │
        └────────────────────┘
```

## Hardware Requirements

**For Mixtral 8x7B on your machine:**
- ✅ 12GB VRAM (with AWQ quantization)
- ✅ 64GB RAM (CPU offloading)
- ⚠️ CUDA-compatible GPU

## Installation

### 1. Install vLLM

```bash
# Run the setup script
./vllm_setup.sh

# Or manually:
pip install vllm
```

### 2. Verify CUDA

```bash
python3 -c "import torch; print(f'CUDA: {torch.cuda.is_available()}')"
```

### 3. Start vLLM Server

**Option A: Quick Start (Recommended)**
```bash
./vllm_start.sh
```

**Option B: Manual Start with AWQ Quantization**
```bash
vllm serve TheBloke/Mixtral-8x7B-Instruct-v0.1-AWQ \
  --quantization awq \
  --dtype half \
  --max-model-len 4096 \
  --gpu-memory-utilization 0.90 \
  --enable-chunked-prefill \
  --port 8000
```

**Option C: GPTQ Quantization (Alternative)**
```bash
vllm serve TheBloke/Mixtral-8x7B-Instruct-v0.1-GPTQ \
  --quantization gptq \
  --dtype half \
  --max-model-len 4096 \
  --gpu-memory-utilization 0.90 \
  --port 8000
```

### 4. Start A2IA CLI

```bash
# In a new terminal
a2ia-cli --backend vllm --model mistralai/Mixtral-8x7B-Instruct-v0.1
```

## Usage Examples

### Basic Usage with vLLM Backend

```bash
# Use vLLM with default settings
a2ia-cli --backend vllm

# Use vLLM with custom model
a2ia-cli --backend vllm --model mistralai/Mistral-7B-Instruct-v0.2

# Use vLLM with custom URL
a2ia-cli --backend vllm --vllm-url http://remote-server:8000/v1

# Use vLLM with debug mode
a2ia-cli --backend vllm --debug
```

### Switch Between Backends

```bash
# Use Ollama (default)
a2ia-cli --backend ollama --model a2ia-qwen

# Use vLLM
a2ia-cli --backend vllm --model mistralai/Mixtral-8x7B-Instruct-v0.1
```

### ReAct Mode (Experimental)

```bash
# Use vLLM with ReAct prompting
a2ia-cli --backend vllm --react
```

## Performance Tuning

### For 12GB VRAM

**Best Quality/Performance:**
- Use AWQ quantization: `TheBloke/Mixtral-8x7B-Instruct-v0.1-AWQ`
- Set `--gpu-memory-utilization 0.90`
- Reduce `--max-model-len` if OOM: try 2048 or 3072

**If Still OOM:**
```bash
vllm serve TheBloke/Mixtral-8x7B-Instruct-v0.1-AWQ \
  --quantization awq \
  --dtype half \
  --max-model-len 2048 \
  --gpu-memory-utilization 0.85 \
  --port 8000
```

### Alternative Models

If Mixtral is too heavy:

**Mistral 7B (Fits easily in 12GB):**
```bash
vllm serve mistralai/Mistral-7B-Instruct-v0.2 \
  --dtype half \
  --max-model-len 8192 \
  --port 8000
```

**Mixtral 8x22B (Too large, skip):**
- Requires 80GB+ VRAM
- Not suitable for consumer hardware

## Implementation Details

### LLMClient Interface

Both `OllamaClient` and `VLLMClient` implement the abstract `LLMClient` base class:

```python
from a2ia.client.llm_base import LLMClient

class CustomClient(LLMClient):
    async def chat(self, messages, tools=None, temperature=0.7):
        """Non-streaming completion"""
        pass
    
    async def stream_chat(self, messages, tools=None, temperature=0.7):
        """Streaming completion"""
        pass
```

### Key Components

| File | Purpose |
|------|---------|
| `a2ia/client/llm_base.py` | Abstract base class defining LLM interface |
| `a2ia/client/llm.py` | OllamaClient implementation |
| `a2ia/client/vllm_client.py` | VLLMClient implementation (OpenAI-compatible) |
| `a2ia/client/orchestrator.py` | Uses `LLMClient` interface (backend-agnostic) |
| `a2ia/cli/interface.py` | Unified CLI with `--backend` flag |
| `tests/test_vllm_client.py` | Test suite (7 tests, all passing) |

### Response Format Compatibility

`VLLMClient` translates OpenAI SSE format to Ollama-compatible format for orchestrator compatibility:

**OpenAI Format (vLLM native):**
```json
{
  "choices": [{
    "delta": {"content": "text"},
    "finish_reason": null
  }]
}
```

**Ollama Format (A2IA orchestrator):**
```json
{
  "message": {"content": "text"},
  "done": false
}
```

## Troubleshooting

### vLLM Won't Start

**Problem:** `OutOfMemoryError` or CUDA initialization fails

**Solutions:**
1. Check GPU memory: `nvidia-smi`
2. Reduce `--max-model-len` to 2048
3. Lower `--gpu-memory-utilization` to 0.80
4. Use AWQ quantized model
5. Kill other GPU processes

### Tool Calling Not Working

**Problem:** Mixtral doesn't use tools properly

**Context:**
- Mixtral 8x7B wasn't trained with native function calling
- It can work with ReAct-style prompting instead

**Solutions:**
1. Use `--react` flag for ReAct prompting
2. Try models with native function calling:
   - `mistralai/Mistral-7B-Instruct-v0.2` (limited)
   - Consider fine-tuning for tool use
3. Use Ollama with tool-trained models (e.g., `a2ia-qwen`)

### CLI Shows Wrong Backend

**Problem:** `a2ia-cli-vllm` uses Ollama

**Solution:**
The `a2ia-cli-vllm` script is just a convenience alias. You must still pass `--backend vllm`:

```bash
a2ia-cli-vllm --backend vllm  # NOT just a2ia-cli-vllm
```

Or use the main CLI:
```bash
a2ia-cli --backend vllm
```

## Testing

Run the test suite:

```bash
# Test vLLM client
pytest tests/test_vllm_client.py -v

# Test full suite
pytest tests/ -v

# Test with coverage
pytest tests/test_vllm_client.py --cov=a2ia.client.vllm_client
```

**Current Coverage:** 7/7 tests passing ✅

## Monitoring

**GPU Memory:**
```bash
watch -n 1 nvidia-smi
```

**vLLM Metrics:**
```bash
curl http://localhost:8000/metrics
```

**Health Check:**
```bash
curl http://localhost:8000/health
```

## Known Limitations

1. **Native Tool Calling:** Mixtral 8x7B doesn't have robust native function calling. Use `--react` mode or fine-tune.
2. **Memory Constraints:** 12GB VRAM limits context length to ~4096 tokens with quantization.
3. **CPU Offloading:** While possible, CPU offloading is significantly slower than pure GPU inference.

## Future Enhancements

- [ ] Add vLLM-specific optimization flags to CLI
- [ ] Support tensor parallelism for multi-GPU setups
- [ ] Add model auto-detection for optimal settings
- [ ] Integration with vLLM's continuous batching
- [ ] Support for adapters and LoRA fine-tunes

## References

- [vLLM Documentation](https://docs.vllm.ai/)
- [Mixtral Model Card](https://huggingface.co/mistralai/Mixtral-8x7B-Instruct-v0.1)
- [TheBloke's Quantized Models](https://huggingface.co/TheBloke)
- [A2IA Architecture Docs](./A2IA-Codex.md)

---

**Maintained by:** A2IA  
**Epoch:** 4, Phase 2  
**Version:** 2025.10.27

