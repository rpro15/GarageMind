import logging
from typing import List, Optional
import httpx
from app.config.settings import settings

logger = logging.getLogger(__name__)

# Глобальный fallback-эмбеддинг (нулевой вектор) для режима без API key
_FALLBACK_EMBEDDING: List[float] | None = None


def _get_fallback_embedding() -> List[float]:
    """Возвращает нулевой эмбеддинг при отсутствии API key."""
    global _FALLBACK_EMBEDDING
    if _FALLBACK_EMBEDDING is None:
        _FALLBACK_EMBEDDING = [0.0] * 768
    return _FALLBACK_EMBEDDING


class EmbeddingService:
    """Генерация эмбеддингов через DeepSeek API."""

    DIMS = 768

    def __init__(self, api_key: Optional[str] = None, model: str = "text-embedding-v2"):
        self.api_key = api_key or settings.DEEPSEEK_API_KEY
        self.model = model
        self._available = bool(self.api_key)
        self._client = httpx.AsyncClient(timeout=30.0) if self._available else None

    async def embed(self, text: str) -> List[float]:
        """Получить эмбеддинг для одного текста."""
        if not self._available or not self._client:
            logger.warning("EmbeddingService: no API key, returning fallback")
            return _get_fallback_embedding()
        try:
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
        except Exception as e:
            logger.error("Embedding error: %s", e)
            return _get_fallback_embedding()

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Получить эмбеддинги для нескольких текстов."""
        if not self._available or not self._client:
            logger.warning("EmbeddingService: no API key, returning fallback batch")
            return [_get_fallback_embedding() for _ in texts]
        try:
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
        except Exception as e:
            logger.error("Embedding batch error: %s", e)
            return [_get_fallback_embedding() for _ in texts]

    async def close(self):
        if self._client:
            await self._client.aclose()
