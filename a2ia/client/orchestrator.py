"""Conversation orchestrator combining LLM and MCP tools."""

import json
from typing import List, Dict, Any, Optional, AsyncIterator
from .llm import OllamaClient
from .mcp import MCPClient
from .tool_validator import ToolValidator
from .react_parser import ReActParser, parse_react_response, format_observation
from ..prompts.react_system import format_react_prompt


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

    def __init__(self, llm_client: OllamaClient, mcp_client: MCPClient, use_react: bool = False):
        """Initialize orchestrator.

        Args:
            llm_client: Ollama LLM client
            mcp_client: MCP client for tools
            use_react: Use ReAct (Reasoning + Acting) mode (default: True)
        """
        self.llm_client = llm_client
        self.mcp_client = mcp_client
        self.messages: List[Dict[str, Any]] = []
        self.use_react = use_react
        
        # Initialize tool validator with available tools
        tools = self.mcp_client.list_tools() if mcp_client.connected else []
        self.validator = ToolValidator(tools) if tools else None
        
        # Add ReAct system prompt if enabled
        if self.use_react and tools:
            react_prompt = format_react_prompt(tools)
            self.messages.append({
                'role': 'system',
                'content': react_prompt
            })

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

                # Validate tool call BEFORE executing
                if self.validator:
                    is_valid, error_msg = self.validator.validate_tool_call(tool_name, arguments)
                    if not is_valid:
                        # Validation failed - show error and skip
                        print(f"   ✗ {error_msg}\n")
                        
                        # Add helpful error message to context
                        self.messages.append({
                            "role": "user",
                            "content": f"[Validation error]: {error_msg}\n\nPlease use a valid tool with correct parameters."
                        })
                        continue  # Skip to next tool call

                # Call the tool
                try:
                    result = await self.mcp_client.call_tool(tool_name, arguments)

                    # Validate response
                    if self.validator:
                        is_valid, warnings = self.validator.validate_tool_response(result, tool_name)
                        
                        # Show warnings if any
                        for warning in warnings:
                            print(f"   ⚠️  {warning}")

                    # Format result nicely
                    formatted_result = format_tool_result(result)

                    # Show result to user
                    print(f"   ↳ {formatted_result}\n")

                    # Add tool result as "user" message
                    result_json = json.dumps(result) if isinstance(result, dict) else str(result)
                    content = f"[Tool result from {tool_name}]: {result_json}"
                    
                    self.messages.append({
                        "role": "user",
                        "content": content
                    })

                except Exception as e:
                    # Record failure for throttling
                    if self.validator:
                        self.validator.throttler.record_call(tool_name, success=False)
                    
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

    async def process_turn_streaming(
        self, 
        max_iterations: int = 300, 
        enable_tools: bool = True
    ) -> AsyncIterator[Dict[str, Any]]:
        """Process one conversation turn with streaming and potential tool calls.

        Args:
            max_iterations: Maximum tool call iterations to prevent infinite loops
            enable_tools: Enable automatic tool calling (default: True)

        Yields:
            Stream chunks with type and content:
            - {'type': 'content', 'text': str}: Text content chunk
            - {'type': 'tool_call', 'name': str, 'args': dict}: Tool call info
            - {'type': 'tool_result', 'name': str, 'result': str}: Tool result
            - {'type': 'done', 'message': dict}: Final complete message
        """
        # Re-enable tools
        tools = self.mcp_client.list_tools() if (self.mcp_client.connected and enable_tools) else None

        for iteration in range(max_iterations):
            # Collect streaming response
            accumulated_content = ""
            accumulated_tool_calls = []
            final_message = None
            has_thinking = False

            # Stream from LLM
            async for chunk in self.llm_client.stream_chat(self.messages, tools=tools):
                # Extract message from chunk
                if 'message' in chunk:
                    msg = chunk['message']
                    
                    # Handle content chunks
                    if 'content' in msg and msg['content']:
                        content = msg['content']
                        accumulated_content += content
                        # Yield content chunk for display
                        yield {
                            'type': 'content',
                            'text': content
                        }
                    
                    # Handle tool calls
                    if 'tool_calls' in msg and msg['tool_calls']:
                        # Accumulate tool calls
                        accumulated_tool_calls.extend(msg['tool_calls'])
                
                # Check if done
                if chunk.get('done'):
                    # Build final message
                    final_message = {
                        'role': 'assistant',
                        'content': accumulated_content
                    }
                    if accumulated_tool_calls:
                        final_message['tool_calls'] = accumulated_tool_calls
                    break

            # If no message received, something went wrong
            if final_message is None:
                final_message = {
                    'role': 'assistant',
                    'content': accumulated_content or "Error: No response received"
                }

            # Check if there are tool calls
            if not final_message.get('tool_calls'):
                # No tool calls - this is the final response
                self.messages.append(final_message)
                yield {
                    'type': 'done',
                    'message': final_message
                }
                return

            # Add assistant message with tool calls
            self.messages.append(final_message)

            # Execute each tool call
            for tool_call in final_message['tool_calls']:
                function = tool_call['function']
                tool_name = function['name']

                # Parse arguments
                try:
                    if isinstance(function['arguments'], str):
                        arguments = json.loads(function['arguments'])
                    else:
                        arguments = function['arguments']

                    # Fix double-escaped strings
                    for key, value in arguments.items():
                        if isinstance(value, str):
                            arguments[key] = value.encode().decode('unicode_escape')

                except json.JSONDecodeError:
                    arguments = {}

                # Validate tool call BEFORE executing
                if self.validator:
                    is_valid, error_msg = self.validator.validate_tool_call(tool_name, arguments)
                    if not is_valid:
                        # Validation failed - don't even try to call the tool
                        yield {
                            'type': 'tool_error',
                            'name': tool_name,
                            'error': error_msg
                        }
                        
                        # Add helpful error message to context
                        self.messages.append({
                            'role': 'user',
                            'content': f'[Validation error]: {error_msg}\n\nPlease use a valid tool with correct parameters.'
                        })
                        continue  # Skip to next tool call
                
                # Yield tool call info
                yield {
                    'type': 'tool_call',
                    'name': tool_name,
                    'args': arguments
                }

                # Call the tool
                try:
                    result = await self.mcp_client.call_tool(tool_name, arguments)

                    # Validate response
                    if self.validator:
                        is_valid, warnings = self.validator.validate_tool_response(result, tool_name)
                        
                        # Show warnings if any
                        for warning in warnings:
                            yield {
                                'type': 'warning',
                                'message': warning
                            }
                    
                    # Format result nicely
                    formatted_result = format_tool_result(result)

                    # Yield tool result
                    yield {
                        'type': 'tool_result',
                        'name': tool_name,
                        'result': formatted_result
                    }

                    # Add tool result as "user" message
                    result_json = json.dumps(result) if isinstance(result, dict) else str(result)
                    content = f'[Tool result from {tool_name}]: {result_json}'
                    
                    self.messages.append({
                        'role': 'user',
                        'content': content
                    })

                except Exception as e:
                    # Record failure for throttling
                    if self.validator:
                        self.validator.throttler.record_call(tool_name, success=False)
                    
                    # Yield error
                    yield {
                        'type': 'tool_error',
                        'name': tool_name,
                        'error': str(e)
                    }

                    # Add error as user message
                    self.messages.append({
                        'role': 'user',
                        'content': f'[Tool error from {tool_name}]: {str(e)}'
                    })

        # Max iterations reached
        final_response = {
            'role': 'assistant',
            'content': 'Max tool call iterations reached. Please try a simpler request.'
        }
        self.messages.append(final_response)
        yield {
            'type': 'done',
            'message': final_response
        }

    async def process_turn_react_streaming(
        self,
        max_iterations: int = 300
    ) -> AsyncIterator[Dict[str, Any]]:
        """Process turn using ReAct pattern with streaming.
        
        Yields:
            - {'type': 'thought', 'text': str}: Reasoning text
            - {'type': 'action_start', 'action': str}: Tool call starting
            - {'type': 'tool_result', 'name': str, 'result': str}: Tool result
            - {'type': 'final_answer', 'content': str}: Final answer text
        """
        tools = self.mcp_client.list_tools() if self.mcp_client.connected else None
        
        for iteration in range(max_iterations):
            parser = ReActParser()
            accumulated_response = ""
            
            # Stream from LLM
            async for chunk in self.llm_client.stream_chat(self.messages, tools=None):  # ReAct doesn't use native tool calling
                if 'message' in chunk:
                    msg = chunk['message']
                    
                    if 'content' in msg and msg['content']:
                        content = msg['content']
                        accumulated_response += content
                        
                        # Parse the chunk
                        parsed = parser.add_chunk(content)
                        
                        if parsed['type'] == 'thought':
                            # Yield thought text for display
                            yield {
                                'type': 'thought',
                                'text': parsed['text']
                            }
                        
                        elif parsed['type'] == 'tool_call':
                            # Tool call detected
                            tool_name = parsed['action']
                            arguments = parsed['input']
                            
                            # Validate tool call
                            if self.validator:
                                is_valid, error_msg = self.validator.validate_tool_call(tool_name, arguments)
                                if not is_valid:
                                    yield {
                                        'type': 'tool_error',
                                        'name': tool_name,
                                        'error': error_msg
                                    }
                                    
                                    # Add error observation
                                    self.messages.append({
                                        'role': 'assistant',
                                        'content': accumulated_response
                                    })
                                    self.messages.append({
                                        'role': 'user',
                                        'content': format_observation(tool_name, {'error': error_msg})
                                    })
                                    break  # Go to next iteration
                            
                            # Yield action start
                            yield {
                                'type': 'action_start',
                                'action': tool_name,
                                'args': arguments
                            }
                            
                            # Execute tool
                            try:
                                result = await self.mcp_client.call_tool(tool_name, arguments)
                                
                                # Validate response
                                if self.validator:
                                    is_valid, warnings = self.validator.validate_tool_response(result, tool_name)
                                    for warning in warnings:
                                        yield {'type': 'warning', 'message': warning}
                                
                                # Format result
                                formatted_result = format_tool_result(result)
                                
                                # Yield tool result
                                yield {
                                    'type': 'tool_result',
                                    'name': tool_name,
                                    'result': formatted_result
                                }
                                
                                # Add to message history in ReAct format
                                self.messages.append({
                                    'role': 'assistant',
                                    'content': accumulated_response
                                })
                                self.messages.append({
                                    'role': 'user',
                                    'content': format_observation(tool_name, result)
                                })
                                
                            except Exception as e:
                                # Record failure
                                if self.validator:
                                    self.validator.throttler.record_call(tool_name, success=False)
                                
                                yield {
                                    'type': 'tool_error',
                                    'name': tool_name,
                                    'error': str(e)
                                }
                                
                                # Add error observation
                                self.messages.append({
                                    'role': 'assistant',
                                    'content': accumulated_response
                                })
                                self.messages.append({
                                    'role': 'user',
                                    'content': format_observation(tool_name, {'error': str(e)})
                                })
                            
                            break  # Exit stream loop to get next response
                        
                        elif parsed['type'] == 'final_answer':
                            # Final answer - we're done
                            yield {
                                'type': 'final_answer',
                                'content': parsed['content']
                            }
                            
                            # Add to history
                            self.messages.append({
                                'role': 'assistant',
                                'content': accumulated_response
                            })
                            return  # Done with this turn
                
                if chunk.get('done'):
                    # Stream complete - check if we got a complete response
                    if parsed['type'] == 'accumulating':
                        # Try to parse the complete response
                        thought, action, action_input = parse_react_response(accumulated_response)
                        
                        if action and action.lower() in ['final answer', 'finalanswer']:
                            # Final answer
                            yield {
                                'type': 'final_answer',
                                'content': action_input if isinstance(action_input, str) else json.dumps(action_input)
                            }
                            
                            self.messages.append({
                                'role': 'assistant',
                                'content': accumulated_response
                            })
                            return
                    break
        
        # Max iterations reached
        yield {
            'type': 'error',
            'message': 'Max iterations reached'
        }

    def clear_history(self):
        """Clear conversation history."""
        self.messages = []

    def get_messages(self) -> List[Dict[str, Any]]:
        """Get all conversation messages.

        Returns:
            List of messages
        """
        return self.messages.copy()
