"""CLI interface with TUI for A2IA."""

import asyncio
import logging
from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.styles import Style
from typing import Optional

from ..client.llm import OllamaClient
from ..client.simple_mcp import SimpleMCPClient
from ..client.orchestrator import Orchestrator

# Suppress httpx logging noise
logging.getLogger("httpx").setLevel(logging.WARNING)


class CLI:
    """A2IA Command Line Interface."""

    def __init__(
        self,
        model: str = "a2ia-qwen",
        mcp_command: Optional[list] = None
    ):
        """Initialize CLI.

        Args:
            model: Ollama model to use
            mcp_command: MCP server command (default: local A2IA server)
        """
        self.model = model
        self.mcp_command = mcp_command or ["python3", "-m", "a2ia.server", "--mode", "mcp"]

        self.llm_client = OllamaClient(model=model)
        self.mcp_client = SimpleMCPClient(server_command=self.mcp_command)
        self.orchestrator = Orchestrator(self.llm_client, self.mcp_client)

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

                # Process turn
                print()  # Newline before response
                response = await self.orchestrator.process_turn()

                # Print assistant response
                print(f"\n\033[36mA2IA:\033[0m {response['content']}\n")

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
    args = parser.parse_args()

    cli = CLI(model=args.model)
    await cli.start()


def run_cli():
    """Synchronous entry point."""
    asyncio.run(main())


if __name__ == "__main__":
    run_cli()
