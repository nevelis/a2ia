"""CLI interface with TUI for A2IA."""

import asyncio
import logging
import signal
import sys
from pathlib import Path
from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.styles import Style
from prompt_toolkit.history import FileHistory
from typing import Optional


class DeduplicatingFileHistory(FileHistory):
    """FileHistory that skips blank lines and consecutive duplicates."""
    
    def append_string(self, string: str) -> None:
        """Append string to history, skipping blanks and consecutive duplicates."""
        # Skip blank lines
        if not string or not string.strip():
            return
        
        # Check if this is a duplicate of the last entry
        try:
            # Load history to check last entry
            with open(self.filename, 'r') as f:
                lines = f.readlines()
            
            # Find the last command (lines starting with '+')
            last_command = None
            for line in reversed(lines):
                if line.startswith('+'):
                    last_command = line[1:].rstrip('\n')
                    break
            
            # Skip if same as last command
            if last_command == string:
                return
        except (FileNotFoundError, IOError):
            # File doesn't exist yet or can't be read
            pass
        
        # Append to history
        super().append_string(string)

from ..client.llm import OllamaClient
from ..client.vllm_client import VLLMClient
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
    
    async def _animate_with_interrupt_check(self, interrupt_event):
        """Animation loop with interrupt checking."""
        while self.running and not interrupt_event.is_set():
            frame = self.frames[self.current_frame]
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
        use_react: bool = False,
        backend: str = "ollama",
        vllm_url: str = "http://localhost:8000/v1"
    ):
        """Initialize CLI.

        Args:
            model: Model name (Ollama model or vLLM model path)
            mcp_command: MCP server command (default: local A2IA server)
            debug: Enable debug output showing message history
            show_thinking: Show LLM thinking/reasoning before actions
            use_react: Use ReAct (Reasoning + Acting) mode (experimental)
            backend: LLM backend to use: 'ollama' or 'vllm' (default: ollama)
            vllm_url: vLLM server URL (only used if backend='vllm')
        """
        self.model = model
        self.backend = backend
        self.mcp_command = mcp_command or ["python3", "-m", "a2ia.server", "--mode", "mcp"]
        self.debug = debug
        self.show_thinking = show_thinking

        # Initialize LLM client based on backend
        if backend == "vllm":
            self.llm_client = VLLMClient(model=model, base_url=vllm_url)
        else:  # Default to Ollama
            self.llm_client = OllamaClient(model=model)
        
        self.mcp_client = SimpleMCPClient(server_command=self.mcp_command)
        self.orchestrator = Orchestrator(self.llm_client, self.mcp_client, use_react=use_react)

        # Set up command history with deduplication
        history_file = Path.home() / ".a2ia-history"
        self.session = PromptSession(history=DeduplicatingFileHistory(str(history_file)))
        self.style = Style.from_dict({
            'prompt': '#00aa00 bold',
            'user': '#ffffff',
            'assistant': '#00aaff',
            'system': '#ffaa00',
            'error': '#ff0000',
        })
        
        # Track if we're currently processing inference (for interrupt handling)
        self._processing_inference = False
        self._interrupt_requested = False

    async def start(self):
        """Start the CLI session."""
        print("\n" + "=" * 70)
        print("  A2IA - Aaron's AI Assistant")
        print(f"  Backend: {self.backend.upper()}")
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

    def _handle_sigint(self, signum, frame):
        """Handle SIGINT (Ctrl+C) signal."""
        if self._processing_inference:
            # During inference - set interrupt flag
            self._interrupt_requested = True
        else:
            # During input - raise KeyboardInterrupt to exit
            raise KeyboardInterrupt()
    
    async def repl_loop(self):
        """Main REPL loop."""
        # Set up signal handler for Ctrl+C
        signal.signal(signal.SIGINT, self._handle_sigint)
        
        while True:
            try:
                # Reset interrupt flag
                self._interrupt_requested = False
                
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

                # Process inference
                await self._process_inference(user_input)

            except KeyboardInterrupt:
                # Ctrl+C during input prompt - exit
                print("\n\n👋 Goodbye!")
                break
            except EOFError:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}\n")

    async def _monitor_interrupt(self, stream_task):
        """Monitor for interrupt requests and cancel stream task."""
        while not self._interrupt_requested and not stream_task.done():
            await asyncio.sleep(0.05)  # Check every 50ms
        
        if self._interrupt_requested and not stream_task.done():
            stream_task.cancel()
    
    async def _consume_stream(self, stream, thinking, state_dict):
        """Consume stream and process chunks."""
        async for chunk in stream:
            chunk_type = chunk.get('type')
            
            if chunk_type == 'content':
                # Stop thinking animation and print A2IA label on first content
                if not state_dict['has_printed_label']:
                    await thinking.stop()
                    print(f"\n\033[36mA2IA:\033[0m ", end='', flush=True)
                    state_dict['has_printed_label'] = True
                elif state_dict['after_tool']:
                    # After tool, just add space, don't re-print label
                    # (we're continuing the same response)
                    state_dict['after_tool'] = False
                
                # Print content as it arrives
                print(chunk['text'], end='', flush=True)
                state_dict['has_content'] = True
            
            elif chunk_type == 'tool_call':
                # Stop thinking if still running
                if not state_dict['has_printed_label']:
                    await thinking.stop()
                    print()  # Newline after thinking
                elif state_dict['has_content']:
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
                    print(f"{emoji} \033[33m{tool_name}\033[0m({args_str})")
                else:
                    print(f"{emoji} \033[33m{tool_name}\033[0m()")
                
                state_dict['after_tool'] = False
                state_dict['has_content'] = False
            
            elif chunk_type == 'tool_result':
                result = chunk['result']
                truncated = str(result)[:100] + "..." if len(str(result)) > 100 else str(result)
                print(f"   ↳ {truncated}")
                state_dict['after_tool'] = True
            
            elif chunk_type == 'tool_error':
                error = chunk['error']
                print(f"   ✗ \033[31m{error}\033[0m")
                state_dict['after_tool'] = True
            
            elif chunk_type == 'warning':
                print(f"   ⚠️  {chunk['message']}")
            
            elif chunk_type == 'thought':
                if self.show_thinking:
                    if not state_dict['in_thought']:
                        print("\n💭 \033[90m", end='')
                        state_dict['in_thought'] = True
                    print(chunk['text'], end='', flush=True)
            
            elif chunk_type == 'done':
                if state_dict['in_thought']:
                    print("\033[0m")  # Reset color
                    state_dict['in_thought'] = False
                break
    
    async def _process_inference(self, user_input: str):
        """Process a single inference turn with interrupt handling."""
        # Mark that we're processing inference
        self._processing_inference = True
        
        # Add user message
        self.orchestrator.add_message("user", user_input)

        # Start thinking animation (with newline before)
        print()  # Newline before thinking animation
        thinking = ThinkingAnimation()
        thinking.start()
        
        # Track state
        state_dict = {
            'has_printed_label': False,
            'has_content': False,
            'after_tool': False,
            'in_thought': False
        }
        
        try:
            # Use ReAct streaming if enabled
            if self.orchestrator.use_react:
                stream = self.orchestrator.process_turn_react_streaming()
            else:
                stream = self.orchestrator.process_turn_streaming()
            
            # Create tasks for stream consumption and interrupt monitoring
            stream_task = asyncio.create_task(self._consume_stream(stream, thinking, state_dict))
            monitor_task = asyncio.create_task(self._monitor_interrupt(stream_task))
            
            # Wait for stream to complete or be interrupted
            done, pending = await asyncio.wait(
                [stream_task, monitor_task],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # Cancel any remaining tasks
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            
            # Check if we were interrupted
            if self._interrupt_requested or stream_task.cancelled():
                await thinking.stop()
                print("\n\033[31m⚠️  Interrupted\033[0m\n")
                return
            
            # Check if stream task had an exception
            if stream_task.done() and not stream_task.cancelled():
                try:
                    await stream_task  # Propagate any exceptions
                except Exception:
                    raise
            
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
                
        except asyncio.CancelledError:
            # Task was cancelled - treat as interrupt
            await thinking.stop()
            print("\n\033[31m⚠️  Interrupted\033[0m\n")
            return
        except KeyboardInterrupt:
            # Ctrl+C during inference - interrupt and continue
            await thinking.stop()
            print("\n\033[31m⚠️  Interrupted\033[0m\n")
            return
            
        finally:
            # Ensure thinking animation is stopped
            if thinking.running:
                await thinking.stop()
            
            # Mark that we're done processing inference
            self._processing_inference = False

        print()  # Extra newline after response


async def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="A2IA CLI")
    parser.add_argument("--model", default="a2ia-qwen", help="Model name (Ollama model or vLLM model path)")
    parser.add_argument("--backend", default="ollama", choices=["ollama", "vllm"], help="LLM backend to use (default: ollama)")
    parser.add_argument("--vllm-url", default="http://localhost:8000/v1", help="vLLM server URL (only used with --backend=vllm)")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    parser.add_argument("--show-thinking", action="store_true", help="Show LLM reasoning before actions")
    parser.add_argument("--react", action="store_true", help="Use ReAct mode (experimental, requires model fine-tuning)")
    args = parser.parse_args()

    cli = CLI(
        model=args.model, 
        backend=args.backend,
        vllm_url=args.vllm_url,
        debug=args.debug, 
        show_thinking=args.show_thinking, 
        use_react=args.react
    )
    await cli.start()


def run_cli():
    """Synchronous entry point."""
    asyncio.run(main())


if __name__ == "__main__":
    run_cli()
