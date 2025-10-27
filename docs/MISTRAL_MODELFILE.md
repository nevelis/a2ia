# A2IA Mistral Modelfile

**Base Model:** `mistral:7b-instruct-q4_K_M`  
**Custom Model:** `a2ia-mistral`  
**Purpose:** Optimized Mistral 7B with A2IA system prompt and tool calling

---

## Quick Setup

### 1. Pull Base Model (if not already present)

```bash
ollama pull mistral:7b-instruct-q4_K_M
```

### 2. Create Custom Model

```bash
./create_mistral_model.sh
```

Or manually:

```bash
ollama create a2ia-mistral -f Modelfile-mistral
```

### 3. Use with A2IA

```bash
a2ia-cli --model a2ia-mistral
```

---

## What's Included

### System Prompt

The Modelfile includes A2IA's complete system prompt with:
- TDD workflow (Specification → Test → Implement → Validate → Commit)
- Tool usage guidelines (MCP tools, patching, relative paths)
- Session initialization (read A2IA.md, Codex, memory)
- Core principles (Ghost Doctrine, transparency, test-first)
- Behavioral guidelines (autonomy, decisiveness, conciseness)

### Optimized Parameters

```
temperature: 0.3       # Focused, deterministic responses
top_p: 0.9            # Good balance of creativity and consistency
top_k: 40             # Reasonable token selection
num_ctx: 8192         # Full 8K context (Mistral supports up to 32K)
repeat_penalty: 1.1   # Prevent repetition
```

### Stop Tokens

```
</s>        # Mistral end-of-sequence
[/INST]     # End of instruction block
```

---

## Mistral vs Other Models

| Feature | a2ia-mistral | a2ia-qwen | Llama 3.1 |
|---------|--------------|-----------|-----------|
| Base Model | Mistral 7B | Qwen 2.5 | Llama 3.1 8B |
| VRAM Usage | 4-5GB | 4-5GB | 5-6GB |
| Context | 8K (32K max) | 32K | 128K |
| Tool Calling | ✅ Good | ✅ Excellent | ✅ Good |
| Speed | Fast | Very Fast | Medium |
| Quality | High | High | Very High |
| Best For | General dev | Tool-heavy | Long context |

---

## Usage Examples

### Basic Usage

```bash
# Interactive chat
ollama run a2ia-mistral

# With A2IA CLI
a2ia-cli --model a2ia-mistral
```

### With Options

```bash
# Show thinking/reasoning
a2ia-cli --model a2ia-mistral --show-thinking

# Debug mode
a2ia-cli --model a2ia-mistral --debug

# Clear history
a2ia-cli --model a2ia-mistral
> /clear
```

### Test Model

```bash
# Quick test
ollama run a2ia-mistral "List files in the workspace"

# Tool calling test
a2ia-cli --model a2ia-mistral
> What files are in the current directory?
```

---

## Customization

### Modify System Prompt

Edit `Modelfile-mistral` and update the `SYSTEM` block, then recreate:

```bash
ollama create a2ia-mistral -f Modelfile-mistral
```

### Adjust Temperature

```bash
# Add to Modelfile-mistral
PARAMETER temperature 0.5  # More creative
# or
PARAMETER temperature 0.1  # More deterministic

# Recreate model
ollama create a2ia-mistral -f Modelfile-mistral
```

### Increase Context Window

```bash
# Edit Modelfile-mistral
PARAMETER num_ctx 16384  # 16K context

# Recreate model
ollama create a2ia-mistral -f Modelfile-mistral
```

---

## Performance Tuning

### For Speed

```bash
# Reduce context for faster responses
PARAMETER num_ctx 4096
PARAMETER temperature 0.2
```

### For Quality

```bash
# Increase context and sampling
PARAMETER num_ctx 16384
PARAMETER temperature 0.4
PARAMETER top_p 0.95
```

### For Tool Calling

```bash
# Deterministic, focused
PARAMETER temperature 0.2
PARAMETER top_p 0.85
PARAMETER repeat_penalty 1.2  # Prevent tool name repetition
```

---

## Troubleshooting

### "model 'a2ia-mistral' not found"

**Solution:** Create the model first:
```bash
./create_mistral_model.sh
```

### "base model 'mistral:7b-instruct-q4_K_M' not found"

**Solution:** Pull the base model:
```bash
ollama pull mistral:7b-instruct-q4_K_M
```

### Tool calling not working well

**Solution:** Lower temperature for more deterministic tool use:
```bash
# Edit Modelfile-mistral
PARAMETER temperature 0.2

# Recreate
ollama create a2ia-mistral -f Modelfile-mistral
```

### Responses too verbose

**Solution:** The system prompt emphasizes conciseness, but you can add:
```bash
# In SYSTEM prompt, add emphasis:
**BE EXTREMELY CONCISE:** One or two sentences maximum unless explaining complex code.
```

---

## Comparison with vLLM

Since vLLM didn't work on your 12GB VRAM, here's why Ollama is better:

| Aspect | Ollama (a2ia-mistral) | vLLM |
|--------|----------------------|------|
| Setup | ✅ 2 commands | ❌ Complex |
| Memory | ✅ 4-5GB VRAM | ❌ 11.5GB (OOM) |
| Quantization | ✅ Built-in (4-bit) | ⚠️ Requires special models |
| Tool Calling | ✅ Works great | ⚠️ Model dependent |
| Customization | ✅ Modelfile system | ⚠️ API parameters only |
| Speed | ✅ 40-60 tok/s | N/A (doesn't run) |

---

## File Reference

```
Modelfile-mistral           # The Modelfile definition
create_mistral_model.sh     # Quick setup script
MISTRAL_MODELFILE.md       # This documentation
```

---

## Next Steps

1. **Create the model:**
   ```bash
   ./create_mistral_model.sh
   ```

2. **Test it:**
   ```bash
   a2ia-cli --model a2ia-mistral
   ```

3. **Start building:**
   ```bash
   You: What files are in the workspace?
   A2IA: [Uses list_directory tool and responds]
   ```

4. **Iterate as needed:**
   - Adjust temperature in Modelfile-mistral
   - Modify system prompt for your workflow
   - Recreate model with `ollama create`

---

**Status:** Ready to use! 🚀  
**Hardware:** Perfect for 12GB VRAM (uses ~4-5GB)  
**Quality:** Production ready with A2IA workflow

