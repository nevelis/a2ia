# vLLM OOM Solutions for 12GB VRAM

**Problem:** Even Mistral 7B is OOMing on your RTX 3500 (12GB VRAM)

**Root Cause:** vLLM is being greedy with memory allocation by default.

---

## Solution 1: CPU Offloading (Recommended)

**Try this first:**

```bash
./vllm_mistral7b_cpu_offload.sh
```

**What it does:**
- Uses only 70% of GPU memory (~8GB)
- Offloads extra layers to RAM
- Slower but should work
- Uses your 64GB RAM advantage

**Configuration:**
```bash
--gpu-memory-utilization 0.70  # Only 70% of VRAM
--swap-space 16                # 16GB RAM for offloading
--max-model-len 4096           # Reasonable context
--max-num-batched-tokens 2048  # Smaller batches
```

---

## Solution 2: Minimal Memory Mode

**If Solution 1 still OOMs:**

```bash
./vllm_mistral7b_minimal.sh
```

**What it does:**
- Uses only 60% of GPU memory (~7GB)
- Single sequence at a time
- Very conservative settings
- Should NOT OOM

**Configuration:**
```bash
--gpu-memory-utilization 0.60  # Only 60% of VRAM
--max-model-len 2048            # Small context
--max-num-batched-tokens 1024   # Tiny batches
--max-num-seqs 1                # One request at a time
```

---

## Solution 3: Tiny Model (Guaranteed to Work)

**For testing if vLLM setup works at all:**

```bash
./vllm_tiny.sh
```

**What it does:**
- Loads Phi-3 Mini (3.8B params)
- Only uses ~3-4GB VRAM
- Fast and efficient
- Proves vLLM works on your system

**Then connect with:**
```bash
a2ia-cli --backend vllm --model microsoft/Phi-3-mini-4k-instruct
```

---

## Solution 4: Just Use Ollama

Honestly, if vLLM keeps fighting you, Ollama handles memory better:

```bash
# Pull a good model
ollama pull mistral:7b-instruct

# Use with A2IA
a2ia-cli --backend ollama --model mistral:7b-instruct
```

**Why Ollama might be better for you:**
- ✅ Automatic memory management
- ✅ Works out of the box
- ✅ No manual tuning needed
- ✅ Handles 12GB VRAM well
- ✅ Quantized models included

---

## Why Is This Happening?

Your error shows:
```
11.47 GiB memory in use
11.26 GiB allocated by PyTorch
```

**The problem:**
1. vLLM allocates memory greedily by default
2. It tries to use ~95% of VRAM (11.4GB)
3. The model + KV cache + overhead = 11.47GB
4. 11.47GB > 11.60GB available = OOM

**The fix:**
- Reduce `--gpu-memory-utilization` to 0.60-0.70
- Enable CPU offloading with `--swap-space`
- Use smaller batch sizes
- Or use a smaller model

---

## Recommended Approach

### Step 1: Try CPU Offloading
```bash
./vllm_mistral7b_cpu_offload.sh
```

### Step 2: If that OOMs, try Minimal
```bash
./vllm_mistral7b_minimal.sh
```

### Step 3: If that OOMs, try Tiny
```bash
./vllm_tiny.sh
```

### Step 4: If vLLM won't cooperate, use Ollama
```bash
ollama pull mistral:7b-instruct
a2ia-cli --backend ollama --model mistral:7b-instruct
```

---

## Memory Configuration Explained

| Flag | What It Does | Default | Recommended |
|------|--------------|---------|-------------|
| `--gpu-memory-utilization` | % of VRAM to use | 0.90 (90%) | 0.60-0.70 |
| `--swap-space` | GB of RAM for offloading | 0 | 8-16 |
| `--max-model-len` | Max context tokens | 8192 | 2048-4096 |
| `--max-num-batched-tokens` | Batch size | Auto | 1024-2048 |
| `--max-num-seqs` | Concurrent sequences | Auto | 1-4 |

---

## Environment Variable Option

You can also try the PyTorch suggestion:

```bash
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

# Then start vLLM
./vllm_mistral7b_cpu_offload.sh
```

This helps with memory fragmentation but may not solve the core issue.

---

## Alternative: Use Quantized Ollama Models

If vLLM is too finicky, Ollama has great quantized models:

```bash
# 4-bit quantized models (fit easily)
ollama pull mistral:7b-instruct-q4_K_M
ollama pull llama3.1:8b-instruct-q4_K_M
ollama pull qwen2.5:7b-instruct-q4_K_M

# Use with A2IA
a2ia-cli --model mistral:7b-instruct-q4_K_M
```

These will use ~4-5GB VRAM and work perfectly on your hardware.

---

## Performance Expectations

### vLLM with CPU Offloading:
- ✅ Will work (probably)
- ⚠️ Slower than pure GPU (~30-50 tok/s)
- ✅ Uses your 64GB RAM

### vLLM Minimal Mode:
- ✅ Should work
- ⚠️ Small context (2K tokens)
- ✅ Still faster than CPU-only

### Ollama:
- ✅ Works reliably
- ✅ Good speed (~40-60 tok/s)
- ✅ No manual tuning needed

---

## My Recommendation

**Try in this order:**

1. `./vllm_mistral7b_cpu_offload.sh` (best quality + offloading)
2. `./vllm_mistral7b_minimal.sh` (if #1 OOMs)
3. `ollama pull mistral:7b-instruct-q4_K_M && a2ia-cli` (if vLLM won't work)

Option 3 is honestly the most pragmatic for development on 12GB VRAM.

---

**Status:** You have options! 🚀

