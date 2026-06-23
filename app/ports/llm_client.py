# app/ports/llm_client.py
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

class LLMClient(ABC):
    @abstractmethod
    async def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        pass

    @abstractmethod
    async def generate_structured(self, prompt: str, schema: Dict) -> Dict[str, Any]:
        pass