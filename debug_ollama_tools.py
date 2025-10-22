"""Debug script to see what Ollama returns for tool calls."""

import asyncio
import httpx
import json


async def test_ollama_tool_calling():
    """Test what format Ollama returns for function calls."""

    # Define a simple tool
    tools = [
        {
            "type": "function",
            "function": {
                "name": "WriteFile",
                "description": "Write content to a file",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "File path"},
                        "content": {"type": "string", "description": "File content"}
                    },
                    "required": ["path", "content"]
                }
            }
        }
    ]

    messages = [
        {"role": "user", "content": "Create a file called test.txt with content 'Hello World'"}
    ]

    payload = {
        "model": "a2ia-llama3",
        "messages": messages,
        "stream": False,
        "tools": tools
    }

    print("Sending request to Ollama...")
    print(f"Tools: {len(tools)}")
    print(f"Messages: {messages}\n")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:11434/api/chat",
            json=payload,
            timeout=60.0
        )

        print(f"Status: {response.status_code}\n")

        if response.status_code == 200:
            data = response.json()
            message = data.get("message", {})

            print("=" * 70)
            print("RESPONSE MESSAGE:")
            print("=" * 70)
            print(json.dumps(message, indent=2))
            print("=" * 70)

            print("\nChecking for tool_calls...")
            if "tool_calls" in message:
                print(f"✅ Found tool_calls: {len(message['tool_calls'])}")
                for tc in message['tool_calls']:
                    print(f"   • {tc}")
            else:
                print("❌ No tool_calls in response")

            print("\nChecking content...")
            if message.get("content"):
                print(f"Content: {message['content'][:200]}")
            else:
                print("No content")

        else:
            print(f"Error: {response.text}")


if __name__ == "__main__":
    asyncio.run(test_ollama_tool_calling())
