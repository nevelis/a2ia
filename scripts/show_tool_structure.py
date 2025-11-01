#!/usr/bin/env python3
"""
Show example tool structure without connecting to MCP server.

This demonstrates what the Ollama template receives.
"""

import json

# Example tool in Ollama format
EXAMPLE_TOOLS = [
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
                        "description": "Path to the file to read"
                    },
                    "encoding": {
                        "type": "string",
                        "description": "File encoding (default: utf-8)"
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write content to a file",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file to write"
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to write to the file"
                    },
                    "create_dirs": {
                        "type": "boolean",
                        "description": "Create parent directories if they don't exist"
                    }
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "execute_command",
            "description": "Execute a shell command",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Shell command to execute"
                    },
                    "working_dir": {
                        "type": "string",
                        "description": "Working directory for command execution"
                    },
                    "timeout": {
                        "type": "number",
                        "description": "Timeout in seconds"
                    }
                },
                "required": ["command"]
            }
        }
    }
]

def main():
    print("=" * 70)
    print("Tool Structure Example")
    print("=" * 70)
    print()
    print("This is what the Ollama template receives via $.Tools")
    print()
    print(json.dumps(EXAMPLE_TOOLS, indent=2))
    print()
    print("=" * 70)
    print("Template Iteration Example")
    print("=" * 70)
    print()
    print("In your Modelfile TEMPLATE:")
    print()
    print("```")
    print("{{- range $.Tools }}")
    print("  Tool: {{ .Function.Name }}")
    print("  Description: {{ .Function.Description }}")
    print("  ")
    print("  Parameters:")
    print("  {{- range $key, $value := .Function.Parameters.Properties }}")
    print("    - {{ $key }} ({{ $value.Type }}): {{ $value.Description }}")
    print("  {{- end }}")
    print("{{- end }}")
    print("```")
    print()
    print("=" * 70)
    print("Available Fields")
    print("=" * 70)
    print()
    print("For each tool in $.Tools:")
    print("  .type                     - Always 'function'")
    print("  .Function.Name            - Tool name (string)")
    print("  .Function.Description     - What the tool does (string)")
    print("  .Function.Parameters      - Parameter schema (object)")
    print()
    print("For each property in .Function.Parameters.Properties:")
    print("  $key                      - Parameter name")
    print("  $value.Type               - Type (string, number, boolean, etc.)")
    print("  $value.Description        - What the parameter does")
    print("  $value.Required           - ❌ DOES NOT EXIST!")
    print()
    print("Required fields are in:")
    print("  .Function.Parameters.Required  - Array of required param names")
    print()
    print("=" * 70)
    print()
    print("To see ALL A2IA tools, run:")
    print("  python3 scripts/generate_tool_schema.py")
    print()

if __name__ == "__main__":
    main()

