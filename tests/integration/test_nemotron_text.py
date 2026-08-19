import os
import sys
import json

# Add root to python path so we can import models package
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from models.providers.nemotron import NemotronProvider

def test_nemotron():
    print("Initializing Nemotron Provider...")
    try:
        # Defaulting to a model that is available and supports tool calling on NVIDIA API
        provider = NemotronProvider(model_name="meta/llama-3.1-8b-instruct") 
    except ValueError as e:
        print(f"Error: {e}")
        print("Please ensure NVIDIA_API_KEY is set in your environment (e.g. export NVIDIA_API_KEY='nvapi-...')")
        return

    print("\n--- Test 1: Basic Text Completion ---")
    messages = [
        {"role": "user", "content": "What is 2 + 2? Answer in one word."}
    ]
    print(f"Sending: {messages}")
    try:
        response = provider.send(messages)
        print(f"Response: {response}")
    except Exception as e:
        print(f"API Error: {e}")
        return

    print("\n--- Test 2: Tool Calling ---")
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get the current weather in a given location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The city and state, e.g. San Francisco, CA"
                        }
                    },
                    "required": ["location"]
                }
            }
        }
    ]
    system_prompt = "You are a helpful assistant. Use tools if necessary."
    user_prompt = "What's the weather like in Tokyo right now?"
    
    print(f"Sending prompt: '{user_prompt}'")
    print(f"With tools: {[t['function']['name'] for t in tools]}")
    
    try:
        action_response = provider.request_action(system_prompt, user_prompt, tools=tools)
        print(f"Response:")
        print(json.dumps(action_response, indent=2))
    except Exception as e:
        print(f"API Error: {e}")

if __name__ == "__main__":
    test_nemotron()
