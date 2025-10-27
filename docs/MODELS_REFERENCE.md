# A2IA Models Reference

**Status:** ✅ Both models fixed and working  
**Date:** 2025-10-27

---

## Available Models

### 1. `a2ia-qwen` (Recommended)

**Base:** `qwen2.5:7b`  
**Tool Support:** ✅ Native tool calling  
**Template:** ChatML (`<|im_start|>`, `<|im_end|>`)  
**VRAM:** ~4-5GB  
**Best For:** General development with tool calling

**Create:**
```bash
./create_qwen_model.sh
```

**Use:**
```bash
# Default - works great with tools
a2ia-cli --model a2ia-qwen

# With debug
a2ia-cli --model a2ia-qwen --debug
```

**Why use this:**
- ✅ Native tool calling support (no --react needed)
- ✅ Fast and efficient
- ✅ Great quality responses
- ✅ Works perfectly with MCP tools

---

### 2. `a2ia-mistral`

**Base:** `mistral:7b-instruct-q4_K_M`  
**Tool Support:** ❌ No native tool calling (use --react)  
**Template:** Mistral Instruct (`[INST]...[/INST]`)  
**VRAM:** ~4-5GB  
**Best For:** General chat, --react mode

**Create:**
```bash
./create_mistral_model.sh
```

**Use:**
```bash
# Basic chat (no tool calling)
a2ia-cli --model a2ia-mistral

# With ReAct for tools
a2ia-cli --model a2ia-mistral --react
```

**Why use this:**
- ✅ Good general responses
- ✅ Works with --react mode
- ⚠️ Needs --react flag for tools
- ⚠️ Slower than Qwen for tool-heavy tasks

---

## Quick Comparison

| Feature | a2ia-qwen | a2ia-mistral |
|---------|-----------|--------------|
| Tool Calling | ✅ Native | ⚠️ --react only |
| Speed | ⚡ Fast | ⚡ Fast |
| Quality | 🌟 Excellent | 🌟 Excellent |
| VRAM | 4-5GB | 4-5GB |
| Best For | Development | Chat/ReAct |
| Recommended | ✅ Yes | ⚠️ Backup |

---

## Template Details

### Qwen Template (ChatML)

```
<|im_start|>system
{{ .System }}
<|im_end|>
<|im_start|>user
{{ .Prompt }}
<|im_end|>
<|im_start|>assistant
```

**Supports:**
- System prompts ✅
- Tool calling ✅
- Multi-turn conversations ✅

### Mistral Template (Instruct)

```
[INST] {{ .System }} {{ .Prompt }} [/INST]
```

**Supports:**
- System prompts ✅
- Tool calling ❌
- Multi-turn conversations ✅

---

## Testing

### Test a2ia-qwen:

```bash
# Basic test
ollama run a2ia-qwen "What is 2+2?"

# With A2IA CLI
a2ia-cli --model a2ia-qwen
> List files in the workspace
```

### Test a2ia-mistral:

```bash
# Basic test
ollama run a2ia-mistral "What is 2+2?"

# With A2IA CLI (ReAct mode for tools)
a2ia-cli --model a2ia-mistral --react
> List files in the workspace
```

---

## Troubleshooting

### "model not found"

**Solution:** Create the model first:
```bash
./create_qwen_model.sh
# or
./create_mistral_model.sh
```

### "does not support tools" (Mistral)

**Solution:** Use --react flag:
```bash
a2ia-cli --model a2ia-mistral --react
```

### Qwen giving weird responses

**Problem:** Wrong template (Llama format instead of ChatML)  
**Solution:** Recreate with correct template:
```bash
./create_qwen_model.sh
```

### Mistral not responding properly

**Problem:** Wrong template format  
**Solution:** Recreate with correct template:
```bash
./create_mistral_model.sh
```

---

## Recommendation

**For A2IA Development:** Use `a2ia-qwen`

```bash
a2ia-cli --model a2ia-qwen
```

**Why:**
- Native tool calling (no --react workaround)
- Excellent quality
- Fast performance
- Works perfectly with MCP tools
- Less complexity

**For vLLM Comparison:**
- Both models use ~4-5GB VRAM (vs vLLM's 11.5GB failure)
- Both work reliably on 12GB GPU
- Native Ollama quantization and memory management

---

## Files

```
Modelfile-qwen              # Qwen with ChatML template
Modelfile-mistral           # Mistral with Instruct template
create_qwen_model.sh        # Create a2ia-qwen
create_mistral_model.sh     # Create a2ia-mistral
MODELS_REFERENCE.md         # This file
```

---

**Status:** All models working correctly ✅  
**Tested:** 2025-10-27  
**Hardware:** RTX 3500 (12GB VRAM)

