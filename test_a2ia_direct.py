#!/usr/bin/env python3
"""Test A2IA directly with capybara-gguf model."""

import asyncio
import sys
sys.path.insert(0, '/home/aaron/dev/nevelis/a2ia')

from a2ia.client.llm import OllamaClient
from a2ia.client.mcp_client import SimpleMCPClient
from a2ia.client.orchestrator import Orchestrator


async def test_a2ia_with_model(model_name):
    """Test A2IA components with specified model."""
    print(f"\n{'='*70}")
    print(f"Testing A2IA with: {model_name}")
    print('='*70)
    
    try:
        # Initialize LLM client
        print(f"1. Initializing OllamaClient with {model_name}...")
        llm_client = OllamaClient(model=model_name)
        print("   ✓ OllamaClient created")
        
        # Test basic chat (non-streaming)
        print("\n2. Testing basic chat (non-streaming)...")
        messages = [{"role": "user", "content": "Say 'Hello from A2IA' and nothing else"}]
        response = await llm_client.chat(messages)
        print(f"   ✓ Response: {response}")
        
        # Test streaming
        print("\n3. Testing streaming chat...")
        accumulated = ""
        async for chunk in llm_client.stream_chat(messages):
            if 'message' in chunk and 'content' in chunk['message']:
                accumulated += chunk['message']['content']
            if chunk.get('done'):
                print(f"   ✓ Streaming response: {accumulated}")
                break
        
        # Test with MCP tools
        print("\n4. Initializing MCP client and Orchestrator...")
        mcp_client = SimpleMCPClient(
            server_command=["python3", "-m", "a2ia.server", "--mode", "mcp"]
        )
        await mcp_client.connect()
        print("   ✓ MCP client connected")
        
        orchestrator = Orchestrator(llm_client, mcp_client, use_react=False)
        print("   ✓ Orchestrator created")
        
        # Add a test message
        print("\n5. Testing orchestrator with simple message...")
        orchestrator.add_message("user", "What is 2 + 2? Just give me the number.")
        
        # Process turn with streaming
        print("   Processing with streaming...")
        response_parts = []
        async for chunk in orchestrator.process_turn_streaming(max_iterations=1, enable_tools=False):
            if chunk.get('type') == 'content':
                response_parts.append(chunk['text'])
                print(f"   Chunk: {chunk['text'][:50]}")
        
        print(f"   ✓ Full response: {''.join(response_parts)}")
        
        # Cleanup
        await mcp_client.disconnect()
        print("\n✅ All tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run tests."""
    print("\nA2IA Direct Integration Test")
    print("="*70)
    
    # Test with capybara-gguf
    success = await test_a2ia_with_model("capybara-gguf:latest")
    
    print("\n" + "="*70)
    if success:
        print("✅ A2IA works with capybara-gguf:latest")
    else:
        print("❌ A2IA failed with capybara-gguf:latest")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(main())

