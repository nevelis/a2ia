# A2IA Scripts

## generate_tool_schema.py

### Purpose

Generates documentation of the exact tool schema that A2IA passes to Ollama templates.

### What It Does

1. Connects to the A2IA MCP server
2. Retrieves all available tool definitions  
3. Converts them to Ollama's tool calling format
4. Generates three output files:
   - `tools.json` - Complete tool schema (Ollama format)
   - `tools_markdown.md` - Human-readable documentation
   - `template_example.txt` - Shows what templates receive

### Usage

```bash
cd /home/aaron/dev/nevelis/a2ia
python3 scripts/generate_tool_schema.py
```

### Output Files

#### tools.json

Complete JSON schema in the exact format that Ollama templates receive via `$.Tools`.

Example structure:
```json
[
  {
    "type": "function",
    "function": {
      "name": "read_file",
      "description": "Read a file from the filesystem",
      "parameters": {
        "type": "object",
        "properties": {
          "path": {
            "type": "string",
            "description": "Path to file"
          }
        },
        "required": ["path"]
      }
    }
  }
]
```

#### tools_markdown.md

Formatted documentation with:
- Tool name and description
- Parameter tables (name, type, required, description)
- Expandable JSON schema sections

#### template_example.txt

Shows:
- What the template receives
- How to iterate over tools in Go templates
- Available fields (`.Function.Name`, `.Function.Description`, etc.)
- **Important**: Documents that `.Required` doesn't exist on properties!

### Template Integration

The generated `tools.json` shows exactly what your Modelfile template receives.

In your template, iterate like this:

```
{{- range $.Tools }}
### {{ .Function.Name }}
{{ .Function.Description }}

Parameters:
{{- range $key, $value := .Function.Parameters.Properties }}
- **{{ $key }}** ({{ $value.Type }}): {{ $value.Description }}
{{- end }}
{{- end }}
```

### Key Insight: The $value.Required Bug

The script documents why `$value.Required` doesn't work:

**Properties** is a map where each property has:
- `.Type`
- `.Description`

But NOT `.Required` - that's a separate array!

**Correct way** to check if required:
```
{{- $required := .Function.Parameters.Required }}
{{- range $key, $value := .Function.Parameters.Properties }}
  {{- if has $required $key }}(required){{- end }}
{{- end }}
```

But Ollama's Go template doesn't have a `has` function, so we just omit the required flag.

### Use Cases

1. **Documentation**: Generate up-to-date tool documentation
2. **Template Development**: See exact structure templates receive
3. **Debugging**: Verify tool schemas match expectations
4. **Integration**: Share tool schema with other systems

### Regenerating

Run the script whenever:
- New tools are added to A2IA
- Tool parameters change
- You need updated documentation

### Example Output

```
======================================================================
A2IA Tool Schema Generator
======================================================================

1. Connecting to MCP server...
   ✓ Connected

2. Retrieving tool definitions...
   ✓ Found 42 tools

3. Converting to Ollama format...
   ✓ Converted 42 tools

4. Saving to tools.json...
   ✓ Saved (24567 bytes)

5. Generating tools_markdown.md...
   ✓ Saved (45123 bytes)

6. Generating template_example.txt...
   ✓ Saved (3456 bytes)

======================================================================
✅ Generation Complete!
======================================================================

Generated files:
  - tools.json
  - tools_markdown.md
  - template_example.txt

Tool Categories:
  - read: 5 tools
  - write: 4 tools
  - git: 8 tools
  - memory: 6 tools
  - execute: 3 tools
  - patch: 2 tools
  - other: 14 tools
```

