# Fixed: CUDA Out of Memory Error

## What Happened

You got `torch.OutOfMemoryError` because the model you tried to load was too large for 12GB VRAM.

**Your GPU:** NVIDIA RTX 3500 Ada (12GB VRAM)  
**Problem:** Trying to load unquantized Mixtral 8x7B (~40GB model into 12GB VRAM)

## The Fix: Use One of These Commands

### ✅ Option 1: Mistral 7B (RECOMMENDED - Easy & Fast)

```bash
# Start vLLM with Mistral 7B
./vllm_mistral7b.sh

# Or manually:
vllm serve mistralai/Mistral-7B-Instruct-v0.2 \
  --dtype half \
  --max-model-len 8192 \
  --gpu-memory-utilization 0.90 \
  --port 8000
```

**Then start A2IA with:**
```bash
a2ia-cli --backend vllm --model mistralai/Mistral-7B-Instruct-v0.2
```

**Why this works:**
- ✅ Mistral 7B uses only ~6-7GB VRAM
- ✅ Leaves 5GB headroom
- ✅ Fast inference (60-80 tokens/sec)
- ✅ Great quality
- ✅ Good tool calling support

---

### ⚠️ Option 2: Mixtral 8x7B (AWQ Quantized - Advanced)

```bash
# Start vLLM with quantized Mixtral
./vllm_mixtral_awq.sh

# Or manually:
vllm serve TheBloke/Mixtral-8x7B-Instruct-v0.1-AWQ \
  --quantization awq \
  --dtype half \
  --max-model-len 2048 \
  --gpu-memory-utilization 0.85 \
  --port 8000
```

**Then start A2IA with:**
```bash
a2ia-cli --backend vllm --model mistralai/Mixtral-8x7B-Instruct-v0.1
```

**Why this might still be tight:**
- ⚠️ Uses ~10-11GB VRAM (very close to limit)
- ⚠️ Smaller context (2K tokens vs 8K)
- ⚠️ May still OOM under load
- ✅ More powerful than Mistral 7B
- ✅ AWQ quantization makes it possible

**If this still fails → Use Option 1 instead**

---

### 🔄 Option 3: Just Use Ollama

vLLM is great but Ollama is easier for local development:

```bash
# Pull Mistral with Ollama
ollama pull mistral:7b-instruct

# Use with A2IA
a2ia-cli --backend ollama --model mistral:7b-instruct
```

**Advantages:**
- ✅ Handles memory automatically
- ✅ No manual configuration needed
- ✅ Works out of the box
- ✅ Great for development

---

## Why The Original Command Failed

You ran:
```bash
vllm serve mistralai/Mixtral-8x7B-Instruct-v0.1  # ← This is ~40GB uncompressed!
```

**Problems:**
1. ❌ No quantization → Full FP16 weights (~40GB)
2. ❌ Model doesn't fit in 12GB VRAM
3. ❌ Immediate OOM error

**What you needed:**
```bash
vllm serve TheBloke/Mixtral-8x7B-Instruct-v0.1-AWQ  # ← AWQ quantized (~10GB)
  --quantization awq  # ← Enable 4-bit compression
```

---

## Quick Reference

### Safe Model (Mistral 7B):
```bash
./vllm_mistral7b.sh
a2ia-cli --backend vllm --model mistralai/Mistral-7B-Instruct-v0.2
```

### Advanced Model (Mixtral 8x7B):
```bash
./vllm_mixtral_awq.sh
a2ia-cli --backend vllm --model mistralai/Mixtral-8x7B-Instruct-v0.1
```

### Monitor GPU:
```bash
watch -n 1 nvidia-smi
```

### Check vLLM Status:
```bash
./check_vllm.sh
```

---

## Memory Usage Comparison

| Model | VRAM Used | Context | Speed | Fits 12GB? |
|-------|-----------|---------|-------|------------|
| Mistral 7B (FP16) | ~6-7GB | 8K | 60-80 tok/s | ✅ Easy |
| Mixtral 8x7B (AWQ) | ~10-11GB | 2-4K | 30-40 tok/s | ⚠️ Tight |
| Mixtral 8x7B (Full) | ~40GB | N/A | N/A | ❌ No |

---

## My Recommendation

**Start with Mistral 7B (`./vllm_mistral7b.sh`)**

It's:
- Reliable and fast
- Great quality
- Easy on your GPU
- Perfect for development

Once you're comfortable, try Mixtral AWQ if you need more power.

---

**Status:** Ready to try again! 🚀

