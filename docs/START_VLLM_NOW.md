# Start vLLM Right Now

You got the "All connection attempts failed" error because vLLM server isn't running yet.

## Step-by-Step Setup (5 minutes)

### Step 1: Install vLLM

```bash
cd /home/aaron/dev/nevelis/a2ia

# Activate your venv if you have one
source .venv/bin/activate  # or wherever your venv is

# Install vLLM
pip install vllm
```

**Expected:** This will take 2-3 minutes to download and install.

### Step 2: Verify CUDA

```bash
python3 -c "import torch; print(f'CUDA Available: {torch.cuda.is_available()}')"
```

**Expected output:** `CUDA Available: True`

If False, vLLM won't work with GPU acceleration. You'll need to check your CUDA installation.

### Step 3: Start vLLM Server

**Open a NEW terminal** (keep this one for later) and run:

```bash
cd /home/aaron/dev/nevelis/a2ia

# Option A: Use the quick start script
./vllm_start.sh

# Option B: Start manually with AWQ quantized Mixtral (recommended for 12GB VRAM)
vllm serve TheBloke/Mixtral-8x7B-Instruct-v0.1-AWQ \
  --quantization awq \
  --dtype half \
  --max-model-len 4096 \
  --gpu-memory-utilization 0.90 \
  --port 8000

# Option C: Use smaller Mistral 7B if Mixtral is too heavy
vllm serve mistralai/Mistral-7B-Instruct-v0.2 \
  --dtype half \
  --max-model-len 8192 \
  --port 8000
```

**Expected:** 
- First run will download the model (10-20GB, takes 5-10 minutes)
- Server will start and show: `INFO: Uvicorn running on http://0.0.0.0:8000`
- You'll see model loading messages

**Keep this terminal running!** The server needs to stay active.

### Step 4: Verify Server is Running

**In your ORIGINAL terminal** (not the one running vLLM):

```bash
cd /home/aaron/dev/nevelis/a2ia
./check_vllm.sh
```

**Expected:** ✅ Messages showing vLLM is installed and running.

### Step 5: Try A2IA Again

```bash
a2ia-cli --backend vllm --model mistralai/Mixtral-8x7B-Instruct-v0.1
```

Now it should work!

## Troubleshooting

### "ModuleNotFoundError: No module named 'vllm'"

**Problem:** vLLM not installed in the current Python environment

**Solution:** 
```bash
# Make sure you're in the right venv
which python3

# Install vLLM
pip install vllm
```

### "CUDA Available: False"

**Problem:** PyTorch can't find your GPU

**Solutions:**
1. Check CUDA is installed: `nvidia-smi`
2. Reinstall PyTorch with CUDA support:
   ```bash
   pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
   ```

### "OutOfMemoryError" when starting vLLM

**Problem:** Model is too big for 12GB VRAM

**Solutions:**
1. Use AWQ quantized version (4-bit):
   ```bash
   vllm serve TheBloke/Mixtral-8x7B-Instruct-v0.1-AWQ \
     --quantization awq --dtype half --port 8000
   ```

2. Reduce max context:
   ```bash
   vllm serve TheBloke/Mixtral-8x7B-Instruct-v0.1-AWQ \
     --quantization awq --max-model-len 2048 --port 8000
   ```

3. Use smaller model:
   ```bash
   vllm serve mistralai/Mistral-7B-Instruct-v0.2 --port 8000
   ```

### Server won't start / Port already in use

**Problem:** Something is already using port 8000

**Solution:**
```bash
# Check what's using port 8000
lsof -i :8000

# Kill it if needed
kill <PID>

# Or use a different port
vllm serve <model> --port 8001

# Then connect with:
a2ia-cli --backend vllm --vllm-url http://localhost:8001/v1
```

## Quick Reference

**Check status:**
```bash
./check_vllm.sh
```

**Monitor GPU:**
```bash
watch -n 1 nvidia-smi
```

**Test vLLM API:**
```bash
curl http://localhost:8000/health
curl http://localhost:8000/v1/models
```

**Stop vLLM:**
- Go to the terminal running vLLM
- Press `Ctrl+C`

---

**Need help?** Check [VLLM_README.md](./VLLM_README.md) for full documentation.

