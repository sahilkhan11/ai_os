import os
import sys
import json

# Add root to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from computer.screen.screen import capture_screenshot
from models.providers.nemotron import NemotronProvider

def test_vision():
    print("Capturing screenshot of current desktop...")
    image_path = "/workspace/vision_test_screenshot.png"
    capture_screenshot(image_path)
    
    print("\nInitializing Nemotron Provider (this will load OmniParser on CPU)...")
    try:
        # Defaulting to a model that is available on NVIDIA API
        provider = NemotronProvider(model_name="meta/llama-3.1-8b-instruct")
    except ValueError as e:
        print(f"Error: {e}")
        return

    prompt = "What elements are on this page and where are they located?"
    print(f"\nSending image and prompt to vision(): '{prompt}'")
    
    try:
        response = provider.vision(image_path, prompt)
        
        print("\n=== OmniParser CPU Latency ===")
        print(f"Latency: {response.get('omniparser_latency', 0):.2f} seconds")
        
        print("\n=== LLM Response ===")
        print(response.get("content", "No content in response."))
    except Exception as e:
        print(f"\nError during vision execution: {e}")

if __name__ == "__main__":
    test_vision()
