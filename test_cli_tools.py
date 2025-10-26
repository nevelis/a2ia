#!/usr/bin/env python3
"""Test CLI tool calling with different models."""

import asyncio
import sys
from a2ia.client.llm import OllamaClient
from a2ia.client.simple_mcp import SimpleMCPClient
from a2ia.client.orchestrator import Orchestrator


async def test_model(model_name: str):
    """Test a model's tool calling capability."""
    print(f"\n{'='*70}")
    print(f"Testing model: {model_name}")
    print(f"{'='*70}\n")
    
    # Initialize clients
    llm = OllamaClient(model=model_name)
    mcp = SimpleMCPClient(server_command=["python3", "-m", "a2ia.mcp_server"])
    orchestrator = Orchestrator(llm, mcp)
    
    # Test 1: Simple greeting (no tools)
    print("Test 1: Simple greeting")
    print("-" * 40)
    orchestrator.add_message("user", "Hello! Just say hi back briefly.")
    response = await orchestrator.process_turn()
    print(f"Response: {response['content']}\n")
    
    # Clear for next test
    orchestrator.clear_history()
    
    # Test 2: List workspace files (should use list_directory tool)
    print("\nTest 2: List files (should use ListDirectory tool)")
    print("-" * 40)
    orchestrator.add_message("user", "List the files in the workspace root directory. Use the ListDirectory tool.")
    response = await orchestrator.process_turn()
    print(f"Response: {response['content']}\n")
    
    # Clear for next test
    orchestrator.clear_history()
    
    # Test 3: Read A2IA.md (should use read_file tool)
    print("\nTest 3: Read file (should use ReadFile tool)")
    print("-" * 40)
    orchestrator.add_message("user", "Read the A2IA.md file using the ReadFile tool and tell me what it's about in one sentence.")
    response = await orchestrator.process_turn()
    print(f"Response: {response['content']}\n")


async def main():
    """Run tests."""
    if len(sys.argv) > 1:
        model = sys.argv[1]
    else:
        model = "a2ia-gpt-oss"
    
    try:
        await test_model(model)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        print(traceback.format_exc())


if __name__ == "__main__":
    asyncio.run(main())

