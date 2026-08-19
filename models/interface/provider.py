from abc import ABC, abstractmethod
from typing import List, Dict, Any, Generator

class ModelProvider(ABC):
    @abstractmethod
    def send(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Send a message to the model and return the full response."""
        pass

    @abstractmethod
    def stream(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]] = None) -> Generator[Dict[str, Any], None, None]:
        """Send a message to the model and return a stream of chunks."""
        pass

    @abstractmethod
    def request_action(self, system_prompt: str, user_prompt: str, tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Convenience method for one-shot action selection with tools."""
        pass

    @abstractmethod
    def vision(self, image_path: str, prompt: str) -> str:
        """Process an image and return the model's understanding."""
        pass
