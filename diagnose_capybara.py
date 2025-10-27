#!/usr/bin/env python3
"""Diagnose capybara model issues by interrogating Ollama API."""

import requests
import json
import sys


def test_model_info(model_name):
    """Get model information from Ollama."""
    print(f"\n{'='*70}")
    print(f"Model Information: {model_name}")
    print('='*70)
    
    try:
        response = requests.post(
            "http://localhost:11434/api/show",
            json={"name": model_name},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Status: {response.status_code}")
            print(f"\nModelfile:")
            print(data.get('modelfile', 'N/A'))
            print(f"\nParameters:")
            print(json.dumps(data.get('parameters', {}), indent=2))
            print(f"\nTemplate:")
            template = data.get('template', 'N/A')
            print(template[:500] + ('...' if len(template) > 500 else ''))
            return True
        else:
            print(f"❌ Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_model_chat(model_name):
    """Test chat with the model (non-streaming)."""
    print(f"\n{'='*70}")
    print(f"Testing Chat: {model_name}")
    print('='*70)
    
    payload = {
        "model": model_name,
        "messages": [
            {"role": "user", "content": "Hello, respond with just 'Hi'"}
        ],
        "stream": False
    }
    
    try:
        response = requests.post(
            "http://localhost:11434/api/chat",
            json=payload,
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Response received")
            print(f"Message: {json.dumps(data.get('message', {}), indent=2)}")
            return True
        else:
            print(f"❌ Failed")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_model_stream(model_name):
    """Test streaming chat with the model."""
    print(f"\n{'='*70}")
    print(f"Testing Streaming: {model_name}")
    print('='*70)
    
    payload = {
        "model": model_name,
        "messages": [
            {"role": "user", "content": "Hello"}
        ],
        "stream": True
    }
    
    try:
        response = requests.post(
            "http://localhost:11434/api/chat",
            json=payload,
            stream=True,
            timeout=30
        )
        
        print(f"Initial Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Failed - Status {response.status_code}")
            # Try to read error body
            try:
                error_text = response.text
                print(f"Error response: {error_text}")
            except:
                print("Could not read error response")
            return False
        
        # Try to read streaming response
        chunk_count = 0
        for line in response.iter_lines():
            if line:
                try:
                    chunk = json.loads(line)
                    chunk_count += 1
                    if chunk_count == 1:
                        print(f"First chunk: {json.dumps(chunk, indent=2)[:300]}")
                    if chunk.get('done'):
                        print(f"✓ Streaming works! Received {chunk_count} chunks")
                        return True
                except json.JSONDecodeError as e:
                    print(f"❌ JSON decode error: {e}")
                    print(f"Line: {line[:200]}")
                    return False
                    
    except requests.exceptions.RequestException as e:
        print(f"❌ Request Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")
        return False
    
    return False


def main():
    """Run diagnostics on both models."""
    print("\n" + "="*70)
    print("CAPYBARA MODEL DIAGNOSTICS")
    print("="*70)
    
    # Check if Ollama is running
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code != 200:
            print("❌ Ollama is not responding properly")
            sys.exit(1)
    except:
        print("❌ Cannot connect to Ollama at http://localhost:11434")
        sys.exit(1)
    
    print("✓ Ollama is running")
    
    # Test working model (capybara-sdlc)
    print("\n" + "="*70)
    print("TESTING: capybara-sdlc:latest (Working Model)")
    print("="*70)
    
    sdlc_info = test_model_info("capybara-sdlc:latest")
    sdlc_chat = test_model_chat("capybara-sdlc:latest") if sdlc_info else False
    sdlc_stream = test_model_stream("capybara-sdlc:latest") if sdlc_chat else False
    
    # Test failing model (capybara-gguf)
    print("\n" + "="*70)
    print("TESTING: capybara-gguf:latest (GGUF Model)")
    print("="*70)
    
    gguf_info = test_model_info("capybara-gguf:latest")
    gguf_chat = test_model_chat("capybara-gguf:latest") if gguf_info else False
    gguf_stream = test_model_stream("capybara-gguf:latest") if gguf_chat else False
    
    # Summary
    print("\n" + "="*70)
    print("DIAGNOSTIC SUMMARY")
    print("="*70)
    print(f"\ncapybara-sdlc:latest (Full Model):")
    print(f"  Model Info:   {'✓ PASS' if sdlc_info else '✗ FAIL'}")
    print(f"  Chat:         {'✓ PASS' if sdlc_chat else '✗ FAIL'}")
    print(f"  Streaming:    {'✓ PASS' if sdlc_stream else '✗ FAIL'}")
    
    print(f"\ncapybara-gguf:latest (Quantized):")
    print(f"  Model Info:   {'✓ PASS' if gguf_info else '✗ FAIL'}")
    print(f"  Chat:         {'✓ PASS' if gguf_chat else '✗ FAIL'}")
    print(f"  Streaming:    {'✓ PASS' if gguf_stream else '✗ FAIL'}")
    
    print("\n" + "="*70)
    
    if not gguf_stream and sdlc_stream:
        print("\n⚠️  GGUF model has issues. Try recreating:")
        print("    cd /home/aaron/dev/nevelis/capybara")
        print("    ollama rm capybara-gguf")
        print("    ollama create capybara-gguf -f Modelfile-gguf")
    

if __name__ == "__main__":
    main()

