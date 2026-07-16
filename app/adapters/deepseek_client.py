# app/adapters/deepseek_client.py
import httpx
import json
import logging
from typing import Optional, Dict, Any
from app.config.settings import settings
from app.ports.llm_client import LLMClient

logger = logging.getLogger(__name__)

class DeepSeekClient(LLMClient):
    def __init__(self):
        self.api_key = settings.DEEPSEEK_API_KEY
        self.base_url = "https://api.deepseek.com/v1"
        self.model = settings.DEEPSEEK_MODEL or "deepseek-chat"
        self.timeout = 60.0

    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        messages: Optional[list] = None,
    ) -> str:
        """
        Генерация текста с поддержкой русского языка.
        """
        # Если нет API-ключа — возвращаем заглушку на русском
        if not self.api_key:
            return (
                "Рекомендуемые шины для вашего автомобиля:\n\n"
                "🏆 **Лучший выбор**: Michelin Primacy 4+ 215/55 R17 — отличное сцепление на мокрой дороге, "
                "низкий уровень шума, долговечность. Цена: ~42 000₽ за комплект.\n\n"
                "💰 **Бюджетный вариант**: Hankook Kinergy Eco 215/55 R17 — хороший баланс цены и качества, "
                "экономия топлива. Цена: ~24 000₽ за комплект.\n\n"
                "❄️ **Если зима**: Nokian Tyres Hakkapeliitta R5 215/55 R17 — лучшие показатели "
                "безопасности на льду и снегу. Цена: ~36 000₽ за комплект.\n\n"
                "Рекомендуемые размеры: 215/55 R17 (стандарт) или 225/50 R17 (улучшенная управляемость)."
            )

        if messages:
            deepseek_messages = messages
        else:
            deepseek_messages = []
            if system_prompt:
                deepseek_messages.append({"role": "system", "content": system_prompt})
            deepseek_messages.append({"role": "user", "content": prompt})

        try:
            async with httpx.AsyncClient(timeout=self.timeout, trust_env=False) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": deepseek_messages,
                        "temperature": 0.7,
                        "max_tokens": 1500
                    }
                )
                response.raise_for_status()
                data = response.json()
                reply = data["choices"][0]["message"]["content"].strip()
                return reply
        except httpx.TimeoutException:
            logger.error("DeepSeek API timeout after %ss", self.timeout)
            return "Извините, сервис временно недоступен. Попробуйте ещё раз через минуту."
        except Exception as e:
            logger.error("DeepSeek API error: %s", e)
            return (
                "К сожалению, не удалось получить рекомендацию от AI. "
                "Вот базовые рекомендации:\n"
                "- Для вашего авто подойдут шины 215/55 R17 или 225/50 R17\n"
                "- Летние: Michelin, Continental, Nokian\n"
                "- Зимние: Nokian Hakkapeliitta, Continental VikingContact\n"
                "- Бюджетные: Hankook, Nordman, Cordiant"
            )

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