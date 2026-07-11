# app/adapters/deepseek_client.py
import httpx
import json
from typing import Optional, Dict, Any
from app.config.settings import settings
from app.ports.llm_client import LLMClient

class DeepSeekClient(LLMClient):
    def __init__(self):
        self.api_key = settings.DEEPSEEK_API_KEY
        self.base_url = "https://api.deepseek.com/v1"
        self.model = settings.DEEPSEEK_MODEL or "deepseek-chat"
        self.timeout = 30.0

    async def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        # Если нет API-ключа — возвращаем заглушку
        if not self.api_key:
            return (
                "Рекомендуемые шины для вашего автомобиля:\n"
                "- Michelin Pilot Sport 4 (лето) — отличное сцепление, ~12 000₽/шт\n"
                "- Continental PremiumContact 6 (лето) — комфорт и тишина, ~10 500₽/шт\n"
                "- Nokian Tyres Hakka Blue 3 (лето) — безопасность, ~11 000₽/шт\n"
                "Рекомендуем размеры: 225/55 R17 или 215/55 R17."
            )

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        async with httpx.AsyncClient(timeout=self.timeout, trust_env=False) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 1000
                }
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()

    async def generate_structured(self, prompt: str, schema: Dict) -> Dict[str, Any]:
        system = "Ты — ассистент по подбору автозапчастей. Отвечай только в формате JSON."
        full_prompt = f"{prompt}\n\nСхема ответа: {json.dumps(schema, ensure_ascii=False)}"
        text = await self.generate_text(full_prompt, system_prompt=system)
        try:
            if "```json" in text:
                start = text.find("```json") + 7
                end = text.find("```", start)
                text = text[start:end].strip()
            return json.loads(text)
        except json.JSONDecodeError:
            return {"error": "Invalid JSON", "raw": text}