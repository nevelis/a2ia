"""Manual CLI test script."""

import asyncio
from a2ia.client.llm import OllamaClient
from a2ia.client.mcp import MCPClient
from a2ia.client.orchestrator import Orchestrator


async def main():
    """Test the CLI components."""
    print("Testing A2IA CLI components...\n")

    # Test 1: LLM client
    print("1. Testing Ollama client with qwen2.5...")
    llm = OllamaClient(model="a2ia-qwen")
    response = await llm.chat([{"role": "user", "content": "Say hi in 5 words"}])
    print(f"   Response: {response['content']}")
    print(f"   ✅ LLM works!\n")

    # Test 2: MCP client
    print("2. Testing MCP client...")
    mcp = MCPClient(server_command=["python3", "-m", "a2ia.server", "--mode", "mcp"])

    try:
        await mcp.connect()
        tools = mcp.list_tools()
        print(f"   Connected! {len(tools)} tools available")

        # List some tools
        tool_names = [t["function"]["name"] for t in tools[:5]]
        print(f"   Sample tools: {', '.join(tool_names)}")
        print(f"   ✅ MCP client works!\n")

        # Test 3: Call a tool
        print("3. Testing tool call (get_workspace_info)...")
        result = await mcp.call_tool("get_workspace_info", {})
        print(f"   Result: {result}")
        print(f"   ✅ Tool calling works!\n")

    finally:
        await mcp.disconnect()

    # Test 4: Orchestrator
    print("4. Testing orchestrator...")
    llm2 = OllamaClient(model="a2ia-qwen")
    mcp2 = MCPClient(server_command=["python3", "-m", "a2ia.server", "--mode", "mcp"])

    try:
        await mcp2.connect()
        orch = Orchestrator(llm_client=llm2, mcp_client=mcp2)

        orch.add_message("user", "What is in the workspace? List files.")
        response = await orch.process_turn()

        print(f"   Response: {response['content'][:200]}")
        print(f"   ✅ Orchestrator works!\n")

    finally:
        await mcp2.disconnect()

    print("=" * 70)
    print("All components working! CLI is ready!")
    print("Run: a2ia-cli")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
