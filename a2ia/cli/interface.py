"""CLI interface with TUI for A2IA."""

import asyncio
import logging
import sys
from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.styles import Style
from typing import Optional

from ..client.llm import OllamaClient
from ..client.simple_mcp import SimpleMCPClient
from ..client.orchestrator import Orchestrator

# Suppress httpx logging noise
logging.getLogger("httpx").setLevel(logging.WARNING)

# Tool emoji mapping
TOOL_EMOJIS = {
    # File operations
    "read_file": "📄",
    "write_file": "✍️",
    "append_file": "➕",
    "patch_file": "🔧",
    "list_directory": "📁",
    "delete_file": "🗑️",
    "copy_file": "📋",
    "move_file": "➡️",
    "create_directory": "📂",
    "prune_directory": "🧹",
    
    # Git operations
    "git_status": "🌿",
    "git_diff": "📊",
    "git_add": "➕",
    "git_commit": "💾",
    "git_push": "☁️",
    "git_pull": "⬇️",
    "git_branch": "🌱",
    "git_checkout": "🔀",
    "git_merge": "🔀",
    "git_log": "📜",
    "git_restore": "⏪",
    "git_reset": "↩️",
    
    # Memory operations
    "store_memory": "🧠",
    "recall_memory": "🔍",
    "list_memories": "📚",
    "delete_memory": "🧹",
    "search_memory": "🔎",
    
    # Execution
    "execute_command": "⚙️",
    "execute_turk": "👷",
    
    # Search/Grep
    "grep": "🔍",
    "find_files": "🔎",
    
    # Terraform
    "terraform_init": "🏗️",
    "terraform_plan": "📋",
    "terraform_apply": "🚀",
    "terraform_destroy": "💥",
    "terraform_validate": "✅",
    
    # Build/CI
    "make": "🔨",
    "run_tests": "🧪",
    
    # Workspace
    "get_workspace_info": "ℹ️",
    "create_workspace": "📦",
}


def get_tool_emoji(tool_name: str) -> str:
    """Get emoji for a tool, with fallback to default."""
    return TOOL_EMOJIS.get(tool_name, "🔧")


def format_tool_result(result: str, max_length: int = 200) -> str:
    """Format tool result to be more concise."""
    if len(result) <= max_length:
        return result
    
    # Truncate and add ellipsis
    return result[:max_length] + "..."


class ThinkingAnimation:
    """Simple pulsating thinking animation."""
    
    def __init__(self):
        self.frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.current_frame = 0
        self.task = None
        self.running = False
    
    async def _animate(self):
        """Animation loop."""
        while self.running:
            frame = self.frames[self.current_frame]
            # Clear line and print thinking animation
            sys.stdout.write(f"\r{frame} Thinking...")
            sys.stdout.flush()
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            await asyncio.sleep(0.1)
    
    def start(self):
        """Start the animation."""
        self.running = True
        self.task = asyncio.create_task(self._animate())
    
    async def stop(self):
        """Stop the animation and clear the line."""
        self.running = False
        if self.task:
            await self.task
            self.task = None
        # Clear the thinking line
        sys.stdout.write("\r" + " " * 20 + "\r")
        sys.stdout.flush()


class CLI:
    """A2IA Command Line Interface."""

    def __init__(
        self,
        model: str = "a2ia-qwen",
        mcp_command: Optional[list] = None,
        debug: bool = False,
        show_thinking: bool = False,
        use_react: bool = False
    ):
        """Initialize CLI.

        Args:
            model: Ollama model to use
            mcp_command: MCP server command (default: local A2IA server)
            debug: Enable debug output showing message history
            show_thinking: Show LLM thinking/reasoning before actions
            use_react: Use ReAct (Reasoning + Acting) mode (experimental)
        """
        self.model = model
        self.mcp_command = mcp_command or ["python3", "-m", "a2ia.server", "--mode", "mcp"]
        self.debug = debug
        self.show_thinking = show_thinking

        self.llm_client = OllamaClient(model=model)
        self.mcp_client = SimpleMCPClient(server_command=self.mcp_command)
        self.orchestrator = Orchestrator(self.llm_client, self.mcp_client, use_react=use_react)

        self.session = PromptSession()
        self.style = Style.from_dict({
            'prompt': '#00aa00 bold',
            'user': '#ffffff',
            'assistant': '#00aaff',
            'system': '#ffaa00',
            'error': '#ff0000',
        })

    async def start(self):
        """Start the CLI session."""
        print("\n" + "=" * 70)
        print("  A2IA - Aaron's AI Assistant")
        print("  Model:", self.model)
        print("=" * 70)
        print("\nConnecting to MCP server...")
        print(f"Command: {' '.join(self.mcp_command)}")

        try:
            await self.mcp_client.connect()
            tools = self.mcp_client.list_tools()
            print(f"✅ Connected! {len(tools)} tools available")
            print("\nType 'exit' or '/quit' to exit")
            print("Type '/clear' to clear conversation history")
            print("Type '/tools' to list available tools")
            print("=" * 70 + "\n")

            await self.repl_loop()

        except Exception as e:
            print(f"❌ Error connecting to MCP server: {e}")
            print(f"Error type: {type(e).__name__}")
            import traceback
            print(f"\nFull traceback:\n{traceback.format_exc()}")
            print("\nMake sure A2IA is installed and the server can start")
            print("Try: python3 -m a2ia.server --mode mcp")
        finally:
            await self.mcp_client.disconnect()

    async def repl_loop(self):
        """Main REPL loop."""
        while True:
            try:
                # Get user input
                user_input = await self.session.prompt_async(
                    HTML('<prompt>You:</prompt> '),
                    style=self.style
                )

                # Handle commands
                if user_input.strip().lower() in ['exit', 'quit', '/quit', '/exit']:
                    print("\n👋 Goodbye!")
                    break

                if user_input.strip() == '/clear':
                    self.orchestrator.clear_history()
                    print("✅ Conversation history cleared\n")
                    continue

                if user_input.strip() == '/tools':
                    tools = self.mcp_client.list_tools()
                    print(f"\n📦 Available tools ({len(tools)}):")
                    for tool in tools:
                        name = tool["function"]["name"]
                        desc = tool["function"]["description"]
                        print(f"  • {name}: {desc}")
                    print()
                    continue

                if not user_input.strip():
                    continue

                # Add user message
                self.orchestrator.add_message("user", user_input)

                # Start thinking animation
                thinking = ThinkingAnimation()
                thinking.start()
                
                # Track state
                has_printed_label = False
                has_content = False
                after_tool = False
                in_thought = False
                
                try:
                    # Use ReAct streaming if enabled
                    if self.orchestrator.use_react:
                        stream = self.orchestrator.process_turn_react_streaming()
                    else:
                        stream = self.orchestrator.process_turn_streaming()
                    
                    async for chunk in stream:
                        chunk_type = chunk.get('type')
                        
                        if chunk_type == 'content':
                            # Stop thinking animation and print A2IA label on first content
                            if not has_printed_label:
                                await thinking.stop()
                                print(f"\n\033[36mA2IA:\033[0m ", end='', flush=True)
                                has_printed_label = True
                            elif after_tool:
                                # Re-print A2IA label after tool output (only once)
                                print(f"\n\033[36mA2IA:\033[0m ", end='', flush=True)
                                after_tool = False  # Clear flag immediately so we don't print again
                            
                            # Print content as it arrives
                            print(chunk['text'], end='', flush=True)
                            has_content = True
                        
                        elif chunk_type == 'tool_call':
                            # Stop thinking if still running
                            if not has_printed_label:
                                await thinking.stop()
                                print()  # Newline after thinking
                            elif has_content:
                                print()  # End the content line
                            
                            # Show tool call with tool-specific emoji
                            tool_name = chunk['name']
                            emoji = get_tool_emoji(tool_name)
                            args = chunk['args']
                            
                            # Format args more concisely
                            if args:
                                # Truncate long string values
                                formatted_args = {}
                                for k, v in args.items():
                                    if isinstance(v, str) and len(v) > 50:
                                        formatted_args[k] = v[:50] + "..."
                                    else:
                                        formatted_args[k] = v
                                args_str = ", ".join(f"{k}={repr(v)}" for k, v in formatted_args.items())
                                print(f"{emoji} {tool_name}({args_str})")
                            else:
                                print(f"{emoji} {tool_name}()")
                            
                            has_content = False  # Reset for next iteration
                        
                        elif chunk_type == 'tool_result':
                            # Show concise tool result
                            result = format_tool_result(chunk['result'], max_length=150)
                            print(f"   ↳ {result}")
                            after_tool = True
                        
                        elif chunk_type == 'tool_error':
                            # Show tool error
                            error = chunk['error']
                            if len(error) > 150:
                                error = error[:150] + "..."
                            print(f"   ✗ {error}")
                            after_tool = True
                        
                        elif chunk_type == 'warning':
                            # Show validation warning
                            print(f"   ⚠️  {chunk['message']}")
                        
                        elif chunk_type == 'thought':
                            # ReAct: Show thinking
                            if not in_thought:
                                await thinking.stop()
                                print(f"\n\033[90m💭 {chunk['text']}\033[0m", end='', flush=True)
                                in_thought = True
                            else:
                                print(chunk['text'], end='', flush=True)
                        
                        elif chunk_type == 'action_start':
                            # ReAct: Tool call starting
                            if in_thought:
                                print()  # End thought line
                                in_thought = False
                            
                            tool_name = chunk['action']
                            emoji = get_tool_emoji(tool_name)
                            args = chunk['args']
                            
                            # Format args concisely
                            if args:
                                formatted_args = {}
                                for k, v in args.items():
                                    if isinstance(v, str) and len(v) > 50:
                                        formatted_args[k] = v[:50] + "..."
                                    else:
                                        formatted_args[k] = v
                                args_str = ", ".join(f"{k}={repr(v)}" for k, v in formatted_args.items())
                                print(f"\n{emoji} {tool_name}({args_str})")
                            else:
                                print(f"\n{emoji} {tool_name}()")
                        
                        elif chunk_type == 'final_answer':
                            # ReAct: Final answer
                            if in_thought:
                                print()  # End thought line
                                in_thought = False
                            
                            await thinking.stop()
                            print(f"\n\033[36mA2IA:\033[0m {chunk['content']}")
                            has_printed_label = True
                            break
                        
                        elif chunk_type == 'done':
                            # Final message received
                            if not has_printed_label:
                                await thinking.stop()
                                print(f"\n\033[36mA2IA:\033[0m {chunk['message'].get('content', '')}")
                            elif has_content:
                                print()  # Add newline at end
                            break
                    
                    # Debug: Show message history
                    if self.debug:
                        print("\n" + "="*70)
                        print("DEBUG: Message History")
                        print("="*70)
                        messages = self.orchestrator.get_messages()
                        for i, msg in enumerate(messages[-5:]):  # Show last 5 messages
                            role = msg.get('role', 'unknown')
                            content = msg.get('content', '')
                            # Truncate long content for display
                            if len(content) > 200:
                                content = content[:200] + "..."
                            print(f"{i+1}. [{role}]: {content}")
                        print("="*70 + "\n")
                    
                finally:
                    # Ensure thinking animation is stopped
                    if thinking.running:
                        await thinking.stop()

                print()  # Extra newline after response

            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except EOFError:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}\n")


async def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="A2IA CLI")
    parser.add_argument("--model", default="a2ia-qwen", help="Ollama model to use")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    parser.add_argument("--show-thinking", action="store_true", help="Show LLM reasoning before actions")
    parser.add_argument("--react", action="store_true", help="Use ReAct mode (experimental, requires model fine-tuning)")
    args = parser.parse_args()

    cli = CLI(model=args.model, debug=args.debug, show_thinking=args.show_thinking, use_react=args.react)
    await cli.start()


def run_cli():
    """Synchronous entry point."""
    asyncio.run(main())


if __name__ == "__main__":
    run_cli()
