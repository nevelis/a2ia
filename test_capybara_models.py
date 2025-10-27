#!/usr/bin/env python3
"""Test both capybara models to compare behavior."""

import asyncio
import httpx
import json


async def test_model(model_name: str):
    """Test a model with a simple query."""
    print(f"\n{'='*70}")
    print(f"Testing: {model_name}")
    print('='*70)
    
    payload = {
        "model": model_name,
        "messages": [
            {"role": "user", "content": "Hello, how are you?"}
        ],
        "stream": True
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            async with client.stream(
                "POST",
                "http://localhost:11434/api/chat",
                json=payload
            ) as response:
                print(f"Status: {response.status_code}")
                print(f"Headers: {dict(response.headers)}")
                
                if response.status_code != 200:
                    error_body = await response.aread()
                    print(f"Error body: {error_body.decode()}")
                    return False
                
                # Read streaming response
                chunk_count = 0
                async for line in response.aiter_lines():
                    if line.strip():
                        try:
                            chunk = json.loads(line)
                            chunk_count += 1
                            if chunk_count == 1:
                                print(f"First chunk: {json.dumps(chunk, indent=2)[:200]}")
                            if chunk.get('done'):
                                print(f"✅ Success! Received {chunk_count} chunks")
                                return True
                        except json.JSONDecodeError as e:
                            print(f"❌ JSON decode error: {e}")
                            print(f"   Line: {line}")
                            return False
                            
        except httpx.HTTPStatusError as e:
            print(f"❌ HTTP Status Error: {e.response.status_code}")
            try:
                error_text = await e.response.aread()
                print(f"   Response: {error_text.decode()[:500]}")
            except:
                print(f"   (Unable to read response body)")
            return False
        except Exception as e:
            print(f"❌ Error: {type(e).__name__}: {e}")
            return False
    
    return False


async def main():
    """Test both models."""
    print("Testing Capybara Models")
    print("=" * 70)
    
    # Test non-quantized model
    sdlc_ok = await test_model("capybara-sdlc:latest")
    
    # Test quantized GGUF model
    gguf_ok = await test_model("capybara-gguf:latest")
    
    print(f"\n{'='*70}")
    print("SUMMARY")
    print('='*70)
    print(f"capybara-sdlc:latest  - {'✅ WORKS' if sdlc_ok else '❌ FAILED'}")
    print(f"capybara-gguf:latest  - {'✅ WORKS' if gguf_ok else '❌ FAILED'}")
    print('='*70)


if __name__ == "__main__":
    asyncio.run(main())

