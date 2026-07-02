import logging
from typing import List
import httpx
from app.config.settings import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Генерация эмбеддингов через DeepSeek API."""

    DIMS = 1024

    def __init__(self, api_key: str | None = None, model: str = "text-embedding-v2"):
        self.api_key = api_key or settings.DEEPSEEK_API_KEY
        self.model = model
        self._client = httpx.AsyncClient(timeout=30.0)

    async def embed(self, text: str) -> List[float]:
        """Получить эмбеддинг для одного текста."""
        resp = await self._client.post(
            "https://api.deepseek.com/v1/embeddings",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={"model": self.model, "input": text},
        )
        resp.raise_for_status()
        return resp.json()["data"][0]["embedding"]

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Получить эмбеддинги для нескольких текстов."""
        resp = await self._client.post(
            "https://api.deepseek.com/v1/embeddings",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={"model": self.model, "input": texts},
        )
        resp.raise_for_status()
        data = resp.json()["data"]
        return [item["embedding"] for item in sorted(data, key=lambda x: x["index"])]

    async def close(self):
        await self._client.aclose()
