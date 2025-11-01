#!/usr/bin/env python3
"""
Generate tool schema documentation for A2IA.

This script connects to the A2IA MCP server, extracts all tool definitions,
and generates the exact schema that gets passed to Ollama templates.

Output:
- tools.json: Complete tool schema in Ollama format
- tools_markdown.md: Human-readable documentation
"""

import asyncio
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from a2ia.client.simple_mcp import SimpleMCPClient


async def generate_tool_schema():
    """Generate tool schema from MCP server."""
    
    print("=" * 70)
    print("A2IA Tool Schema Generator")
    print("=" * 70)
    print()
    
    # Initialize MCP client
    print("1. Connecting to MCP server...")
    mcp_client = SimpleMCPClient(
        server_command=["python3", "-m", "a2ia.server", "--mode", "mcp"]
    )
    
    try:
        await mcp_client.connect()
        print("   ✓ Connected")
        print()
        
        # Get tools
        print("2. Retrieving tool definitions...")
        tools_list = mcp_client.list_tools()
        print(f"   ✓ Found {len(tools_list)} tools")
        print()
        
        # Tools are already in Ollama format from SimpleMCPClient
        print("3. Validating tool format...")
        ollama_tools = tools_list
        
        # Verify format
        for tool in ollama_tools:
            if "type" not in tool or "function" not in tool:
                print(f"   ⚠️  Invalid tool format: {tool}")
        
        print(f"   ✓ Validated {len(ollama_tools)} tools")
        print()
        
        # Save to JSON
        output_dir = Path(__file__).parent.parent
        json_path = output_dir / "tools.json"
        
        print(f"4. Saving to {json_path.name}...")
        with open(json_path, 'w') as f:
            json.dump(ollama_tools, f, indent=2)
        print(f"   ✓ Saved ({json_path.stat().st_size} bytes)")
        print()
        
        # Generate markdown documentation
        md_path = output_dir / "tools_markdown.md"
        print(f"5. Generating {md_path.name}...")
        
        with open(md_path, 'w') as f:
            f.write("# A2IA Tool Schema Documentation\n\n")
            f.write(f"Generated automatically from MCP server.\n\n")
            f.write(f"**Total Tools:** {len(ollama_tools)}\n\n")
            f.write("---\n\n")
            
            for i, tool in enumerate(ollama_tools, 1):
                func = tool["function"]
                f.write(f"## {i}. {func['name']}\n\n")
                f.write(f"**Description:** {func['description']}\n\n")
                
                params = func.get("parameters", {})
                properties = params.get("properties", {})
                required = params.get("required", [])
                
                if properties:
                    f.write("**Parameters:**\n\n")
                    f.write("| Name | Type | Required | Description |\n")
                    f.write("|------|------|----------|-------------|\n")
                    
                    for param_name, param_info in properties.items():
                        is_required = "✓" if param_name in required else ""
                        param_type = param_info.get("type", "unknown")
                        param_desc = param_info.get("description", "")
                        f.write(f"| `{param_name}` | {param_type} | {is_required} | {param_desc} |\n")
                    f.write("\n")
                else:
                    f.write("**Parameters:** None\n\n")
                
                # Show example JSON schema
                f.write("<details>\n")
                f.write("<summary>JSON Schema</summary>\n\n")
                f.write("```json\n")
                f.write(json.dumps(tool, indent=2))
                f.write("\n```\n\n")
                f.write("</details>\n\n")
                f.write("---\n\n")
        
        print(f"   ✓ Saved ({md_path.stat().st_size} bytes)")
        print()
        
        # Generate template example
        example_path = output_dir / "template_example.txt"
        print(f"6. Generating {example_path.name}...")
        
        with open(example_path, 'w') as f:
            f.write("# Example: What the Ollama Template Receives\n\n")
            f.write("When A2IA sends a request to Ollama with tools, the template\n")
            f.write("receives the $.Tools array populated with tool definitions.\n\n")
            f.write("Here's what the first 3 tools look like:\n\n")
            f.write("```json\n")
            f.write(json.dumps(ollama_tools[:3], indent=2))
            f.write("\n```\n\n")
            f.write("# Template Iteration\n\n")
            f.write("The template iterates over these with:\n\n")
            f.write("```\n")
            f.write("{{- range $.Tools }}\n")
            f.write("  Tool Name: {{ .Function.Name }}\n")
            f.write("  Description: {{ .Function.Description }}\n")
            f.write("  \n")
            f.write("  Parameters:\n")
            f.write("  {{- range $key, $value := .Function.Parameters.Properties }}\n")
            f.write("    - {{ $key }} ({{ $value.Type }}): {{ $value.Description }}\n")
            f.write("  {{- end }}\n")
            f.write("{{- end }}\n")
            f.write("```\n\n")
            f.write("# Available Fields\n\n")
            f.write("For each tool in $.Tools:\n")
            f.write("- .type (always 'function')\n")
            f.write("- .Function.Name (string)\n")
            f.write("- .Function.Description (string)\n")
            f.write("- .Function.Parameters.Properties (map)\n")
            f.write("  - Each property has:\n")
            f.write("    - .Type (string: 'string', 'number', 'boolean', 'object', 'array')\n")
            f.write("    - .Description (string)\n")
            f.write("    - NOTE: .Required does NOT exist! Use Parameters.Required array instead\n")
            f.write("- .Function.Parameters.Required (array of strings)\n")
        
        print(f"   ✓ Saved ({example_path.stat().st_size} bytes)")
        print()
        
        # Summary
        print("=" * 70)
        print("✅ Generation Complete!")
        print("=" * 70)
        print()
        print("Generated files:")
        print(f"  - {json_path.relative_to(Path.cwd())}")
        print(f"  - {md_path.relative_to(Path.cwd())}")
        print(f"  - {example_path.relative_to(Path.cwd())}")
        print()
        print("Tool Categories:")
        
        # Categorize tools by prefix
        categories = {}
        for tool in ollama_tools:
            name = tool["function"]["name"]
            prefix = name.split('_')[0] if '_' in name else 'other'
            categories.setdefault(prefix, []).append(name)
        
        for category, names in sorted(categories.items()):
            print(f"  - {category}: {len(names)} tools")
        
        print()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        # Cleanup
        await mcp_client.disconnect()
    
    return 0


def main():
    """Entry point."""
    return asyncio.run(generate_tool_schema())


if __name__ == "__main__":
    sys.exit(main())

