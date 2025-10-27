#!/usr/bin/env python3
"""Test if capybara-gguf works with tools."""

import asyncio
import httpx
import json


async def test_with_tools():
    """Test capybara-gguf with tool definitions."""
    print("\n" + "="*70)
    print("Testing capybara-gguf:latest WITH TOOLS")
    print("="*70)
    
    # Simple tool definition (like A2IA sends)
    tools = [
        {
            "type": "function",
            "function": {
                "name": "read_file",
                "description": "Read a file from the filesystem",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Path to the file"
                        }
                    },
                    "required": ["path"]
                }
            }
        }
    ]
    
    payload = {
        "model": "capybara-gguf:latest",
        "messages": [
            {"role": "user", "content": "Hello, just say hi"}
        ],
        "stream": True,
        "tools": tools  # This might be causing the 500 error
    }
    
    print("\nTest 1: WITH tools (streaming)")
    print("-" * 70)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            async with client.stream(
                "POST",
                "http://localhost:11434/api/chat",
                json=payload
            ) as response:
                print(f"Status: {response.status_code}")
                
                if response.status_code != 200:
                    error_body = await response.aread()
                    print(f"❌ FAILED - Status {response.status_code}")
                    print(f"Error: {error_body.decode()[:500]}")
                    return False
                
                chunk_count = 0
                async for line in response.aiter_lines():
                    if line.strip():
                        chunk = json.loads(line)
                        chunk_count += 1
                        if chunk.get('done'):
                            print(f"✅ SUCCESS - Received {chunk_count} chunks")
                            return True
                            
        except Exception as e:
            print(f"❌ EXCEPTION: {type(e).__name__}: {e}")
            return False


async def test_without_tools():
    """Test capybara-gguf WITHOUT tool definitions."""
    print("\n" + "="*70)
    print("Testing capybara-gguf:latest WITHOUT TOOLS")
    print("="*70)
    
    payload = {
        "model": "capybara-gguf:latest",
        "messages": [
            {"role": "user", "content": "Hello, just say hi"}
        ],
        "stream": True
        # No tools key
    }
    
    print("\nTest 2: WITHOUT tools (streaming)")
    print("-" * 70)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            async with client.stream(
                "POST",
                "http://localhost:11434/api/chat",
                json=payload
            ) as response:
                print(f"Status: {response.status_code}")
                
                if response.status_code != 200:
                    error_body = await response.aread()
                    print(f"❌ FAILED - Status {response.status_code}")
                    print(f"Error: {error_body.decode()[:500]}")
                    return False
                
                chunk_count = 0
                async for line in response.aiter_lines():
                    if line.strip():
                        chunk = json.loads(line)
                        chunk_count += 1
                        if chunk.get('done'):
                            print(f"✅ SUCCESS - Received {chunk_count} chunks")
                            return True
                            
        except Exception as e:
            print(f"❌ EXCEPTION: {type(e).__name__}: {e}")
            return False


async def main():
    """Run tests."""
    print("\n" + "="*70)
    print("DIAGNOSING CAPYBARA-GGUF TOOLS SUPPORT")
    print("="*70)
    
    # Test without tools first
    without_tools = await test_without_tools()
    
    # Test with tools
    with_tools = await test_with_tools()
    
    print("\n" + "="*70)
    print("RESULTS")
    print("="*70)
    print(f"WITHOUT tools: {'✅ WORKS' if without_tools else '❌ FAILS'}")
    print(f"WITH tools:    {'✅ WORKS' if with_tools else '❌ FAILS'}")
    print("="*70)
    
    if without_tools and not with_tools:
        print("\n🔍 DIAGNOSIS: Model doesn't support tool calling!")
        print("   Solution: Disable tools when using this model")
        print("   Run: a2ia-cli --model capybara-gguf:latest (with tools disabled)")
    elif with_tools and without_tools:
        print("\n✅ Model fully supports tool calling!")
    elif not without_tools:
        print("\n❌ Model has fundamental issues (fails even without tools)")


if __name__ == "__main__":
    asyncio.run(main())

