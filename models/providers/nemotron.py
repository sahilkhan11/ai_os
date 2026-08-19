import os
from openai import OpenAI
from typing import List, Dict, Any, Generator
from models.interface.provider import ModelProvider

class NemotronProvider(ModelProvider):
    def __init__(self, model_name: str = "meta/llama-3.1-8b-instruct"):
        self.api_key = os.environ.get("NVIDIA_API_KEY")
        if not self.api_key:
            raise ValueError("NVIDIA_API_KEY environment variable is not set")
        
        # NVIDIA's OpenAI-compatible endpoint
        self.client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=self.api_key
        )
        self.model_name = model_name

    def send(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        kwargs = {
            "model": self.model_name,
            "messages": messages,
            "temperature": 0.2,
            "top_p": 0.7,
            "max_tokens": 1024,
        }
        if tools:
            kwargs["tools"] = tools
            
        response = self.client.chat.completions.create(**kwargs)
        
        # Convert OpenAI response to dict for generic interface
        message = response.choices[0].message
        result = {
            "role": message.role,
            "content": message.content
        }
        
        if hasattr(message, "tool_calls") and message.tool_calls:
            result["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": tc.type,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                } for tc in message.tool_calls
            ]
            
        return result

    def stream(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]] = None) -> Generator[Dict[str, Any], None, None]:
        kwargs = {
            "model": self.model_name,
            "messages": messages,
            "temperature": 0.2,
            "top_p": 0.7,
            "max_tokens": 1024,
            "stream": True
        }
        if tools:
            kwargs["tools"] = tools
            
        response = self.client.chat.completions.create(**kwargs)
        for chunk in response:
            delta = chunk.choices[0].delta
            yield {
                "role": delta.role if hasattr(delta, 'role') else None,
                "content": delta.content if hasattr(delta, 'content') else None,
            }

    def request_action(self, system_prompt: str, user_prompt: str, tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        return self.send(messages, tools=tools)

    def vision(self, image_path: str, prompt: str) -> str:
        """Process an image using OmniParser and return the model's understanding."""
        # Initialize OmniParser wrapper here to avoid loading models until needed
        from computer.vision.omniparser import OmniParserBridge
        import json
        
        parser = OmniParserBridge()
        parsed_content_list, latency = parser.parse(image_path)
        
        # Format the structured list into text for the LLM
        formatted_elements = json.dumps(parsed_content_list, indent=2)
        
        augmented_prompt = (
            f"{prompt}\n\n"
            f"Here are the visual elements detected on the screen by OmniParser:\n"
            f"{formatted_elements}\n\n"
            f"Please use these coordinates and labels to answer the request."
        )
        
        messages = [
            {"role": "user", "content": augmented_prompt}
        ]
        
        response = self.send(messages)
        
        # Inject latency into the response for benchmarking purposes
        response["omniparser_latency"] = latency
        return response
