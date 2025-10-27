# vLLM Quick Start Guide

**TL;DR:** Run powerful LLMs with vLLM on your 12GB VRAM machine in 3 steps.

## Quick Setup (Safe Mode - Mistral 7B)

```bash
# 1. Install vLLM
pip install vllm

# 2. Start vLLM server (in one terminal)
./vllm_mistral7b.sh

# 3. Start A2IA CLI (in another terminal)
a2ia-cli --backend vllm --model mistralai/Mistral-7B-Instruct-v0.2
```

## Quick Setup (Advanced - Mixtral 8x7B)

⚠️ **May cause OOM errors on 12GB VRAM**

```bash
# 1. Install vLLM
pip install vllm

# 2. Start vLLM server (in one terminal)
./vllm_mixtral_awq.sh

# 3. Start A2IA CLI (in another terminal)
a2ia-cli --backend vllm --model mistralai/Mixtral-8x7B-Instruct-v0.1
```

## That's It!

Now you can use A2IA with Mixtral 8x7B just like you would with Ollama:

```
You: What files are in the current directory?
A2IA: [Uses list_directory tool and responds]
```

## Switching Between Backends

```bash
# Use Ollama (default)
a2ia-cli

# Use vLLM
a2ia-cli --backend vllm
```

## Common Commands

```bash
# Check GPU memory
nvidia-smi

# Check vLLM health
curl http://localhost:8000/health

# Stop vLLM (in vLLM terminal)
Ctrl+C
```

## If Something Goes Wrong

**Out of Memory?**
```bash
# Use smaller context window
./vllm_start.sh  # Edit max-model-len to 2048
```

**vLLM won't start?**
```bash
# Check CUDA
python3 -c "import torch; print(torch.cuda.is_available())"

# Try smaller model
vllm serve mistralai/Mistral-7B-Instruct-v0.2 --port 8000
```

**Tools not working?**
```bash
# Try ReAct mode instead
a2ia-cli --backend vllm --react
```

## Full Documentation

See [VLLM_README.md](./VLLM_README.md) for complete documentation.

---

**Status:** ✅ Production Ready  
**Tests:** 113/113 passing  
**Date:** 2025-10-27

