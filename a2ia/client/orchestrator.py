"""Conversation orchestrator combining LLM and MCP tools."""

import json
from typing import List, Dict, Any, Optional
from .llm import OllamaClient
from .mcp import MCPClient


def sanitize_path(path_str: str) -> str:
    """Remove workspace path prefix to avoid leaking filesystem location.

    Args:
        path_str: Path string that might contain workspace prefix

    Returns:
        Sanitized path (workspace root → /)
    """
    from pathlib import Path
    from ..core import get_workspace

    try:
        ws = get_workspace()
        workspace_path = str(ws.path)

        # Replace workspace path with /
        if workspace_path in path_str:
            return path_str.replace(workspace_path, "/")

        return path_str
    except:
        return path_str


def format_tool_result(result: Any) -> str:
    """Format tool result as nice ASCII output instead of raw JSON.

    Args:
        result: Tool result (dict, list, or string)

    Returns:
        Formatted string (with workspace paths sanitized)
    """
    if isinstance(result, dict):
        # Format dict as key-value list
        lines = []
        for key, value in result.items():
            if isinstance(value, list) and len(value) > 3:
                # Show first few items
                preview = ', '.join(str(v) for v in value[:3])
                lines.append(f"  {key}: [{preview}, ... {len(value)} total]")
            elif isinstance(value, str) and len(value) > 100:
                # Truncate long strings
                sanitized = sanitize_path(value)
                lines.append(f"  {key}: {sanitized[:100]}...")
            else:
                # Sanitize path if it's a string
                sanitized = sanitize_path(str(value)) if isinstance(value, str) else value
                lines.append(f"  {key}: {sanitized}")
        return "\n".join(lines)
    elif isinstance(result, list):
        # Format list items
        if len(result) <= 10:
            return "\n".join(f"  • {item}" for item in result)
        else:
            preview = "\n".join(f"  • {item}" for item in result[:10])
            return f"{preview}\n  ... {len(result) - 10} more items"
    else:
        sanitized = sanitize_path(str(result))
        return sanitized


class Orchestrator:
    """Orchestrates conversation between user, LLM, and MCP tools."""

    def __init__(self, llm_client: OllamaClient, mcp_client: MCPClient):
        """Initialize orchestrator.

        Args:
            llm_client: Ollama LLM client
            mcp_client: MCP client for tools
        """
        self.llm_client = llm_client
        self.mcp_client = mcp_client
        self.messages: List[Dict[str, Any]] = []

    def add_message(self, role: str, content: str):
        """Add a message to the conversation.

        Args:
            role: Message role (user, assistant, system)
            content: Message content
        """
        self.messages.append({
            "role": role,
            "content": content
        })

    async def process_turn(self, max_iterations: int = 300, enable_tools: bool = True) -> Dict[str, Any]:
        """Process one conversation turn with potential tool calls.

        Args:
            max_iterations: Maximum tool call iterations to prevent infinite loops
            enable_tools: Enable automatic tool calling (default: True)

        Returns:
            Final assistant message
        """
        # Re-enable tools
        tools = self.mcp_client.list_tools() if (self.mcp_client.connected and enable_tools) else None

        for iteration in range(max_iterations):
            # Get LLM response (quietly)
            response = await self.llm_client.chat(self.messages, tools=tools)

            # Debug: check if model output JSON as text instead of tool_calls
            if not response.get('tool_calls') and response.get('content'):
                # Try to parse JSON from content
                import re
                content = response['content']
                # Look for {"name": "ToolName", "parameters": {...}} patterns
                json_pattern = r'\{"name":\s*"(\w+)",\s*"parameters":\s*(\{[^}]+\})\}'
                matches = re.findall(json_pattern, content)

                if matches:
                    # Convert text JSON to proper tool_calls
                    response['tool_calls'] = []
                    for tool_name, params_str in matches:
                        try:
                            response['tool_calls'].append({
                                'id': f'call_{iteration}',
                                'function': {
                                    'name': tool_name,
                                    'arguments': params_str
                                }
                            })
                        except:
                            pass

            # Show tool calls if any
            if response.get('tool_calls'):
                for tc in response['tool_calls']:
                    tool_name = tc['function']['name']
                    # Parse arguments
                    try:
                        if isinstance(tc['function']['arguments'], str):
                            args = json.loads(tc['function']['arguments'])
                        else:
                            args = tc['function']['arguments']

                        # Format args nicely
                        if args:
                            args_str = ", ".join(f"{k}={repr(v)}" for k, v in args.items())
                            print(f"🔧 {tool_name}({args_str})")
                        else:
                            print(f"🔧 {tool_name}()")
                    except:
                        print(f"🔧 {tool_name}()")

            # Check if there are tool calls
            if "tool_calls" not in response or not response.get("tool_calls"):
                # No tool calls - this is the final response
                self.messages.append(response)
                return response

            # Add assistant message with tool calls
            self.messages.append(response)

            # Execute each tool call
            for tool_call in response["tool_calls"]:
                function = tool_call["function"]
                tool_name = function["name"]

                # Parse arguments
                try:
                    if isinstance(function["arguments"], str):
                        arguments = json.loads(function["arguments"])
                    else:
                        arguments = function["arguments"]

                    # Fix double-escaped strings (model sends \\n instead of \n)
                    for key, value in arguments.items():
                        if isinstance(value, str):
                            # Decode escape sequences
                            arguments[key] = value.encode().decode('unicode_escape')

                except json.JSONDecodeError:
                    arguments = {}

                # Call the tool
                try:
                    result = await self.mcp_client.call_tool(tool_name, arguments)

                    # Format result nicely
                    formatted_result = format_tool_result(result)

                    # Show result to user
                    print(f"   ↳ {formatted_result}\n")

                    # Add tool result as "user" message (Ollama doesn't properly support "tool" role)
                    result_json = json.dumps(result) if isinstance(result, dict) else str(result)
                    self.messages.append({
                        "role": "user",
                        "content": f"[Tool result from {tool_name}]: {result_json}"
                    })

                except Exception as e:
                    # Show error to user
                    print(f"   ✗ Error: {e}\n")

                    # Add error as user message (consistent with tool results)
                    self.messages.append({
                        "role": "user",
                        "content": f"[Tool error from {tool_name}]: {str(e)}"
                    })

        # Max iterations reached
        final_response = {
            "role": "assistant",
            "content": "Max tool call iterations reached. Please try a simpler request."
        }
        self.messages.append(final_response)
        return final_response

    def clear_history(self):
        """Clear conversation history."""
        self.messages = []

    def get_messages(self) -> List[Dict[str, Any]]:
        """Get all conversation messages.

        Returns:
            List of messages
        """
        return self.messages.copy()
