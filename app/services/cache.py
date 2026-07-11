"""
Сервис кэширования на Redis.

Используется для:
1. Кэширования частых API-запросов (список брендов, моделей)
2. Кэширования результатов DeepSeek API (экономия токенов)
3. Rate limiting
4. Очереди фоновых задач

Подключение:
    cache = get_cache()
    await cache.get("key")
    await cache.set("key", "value", ttl=3600)
"""
from __future__ import annotations

import json
import logging
import threading
from typing import Any, Optional, Callable
from functools import wraps

from app.config.settings import settings

logger = logging.getLogger(__name__)

# Глобальный экземпляр кэша (thread-safe singleton)
_cache_instance = None
_cache_lock = threading.Lock()


class RedisCache:
    """Обёртка над Redis с поддержкой JSON и fallback'ом."""

    def __init__(self, redis_url: str):
        self._redis_url = redis_url
        self._client = None
        self._available = False
        self._connect()

    def _connect(self):
        """Подключение к Redis."""
        try:
            import redis.asyncio as aioredis
            self._client = aioredis.from_url(
                self._redis_url,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2,
            )
            self._available = True
            logger.info("✅ Redis connected: %s", self._redis_url)
        except Exception as e:
            logger.warning("⚠️ Redis not available (using no-cache mode): %s", e)
            self._available = False

    async def get(self, key: str) -> Optional[str]:
        """Получить значение по ключу."""
        if not self._available or not self._client:
            return None
        try:
            return await self._client.get(key)
        except Exception as e:
            logger.warning("Redis get error: %s", e)
            return None

    async def get_json(self, key: str) -> Optional[Any]:
        """Получить и десериализовать JSON."""
        val = await self.get(key)
        if val:
            try:
                return json.loads(val)
            except json.JSONDecodeError:
                return None
        return None

    async def set(self, key: str, value: str, ttl: int = 300) -> bool:
        """Установить значение с TTL (в секундах)."""
        if not self._available or not self._client:
            return False
        try:
            await self._client.set(key, value, ex=ttl)
            return True
        except Exception as e:
            logger.warning("Redis set error: %s", e)
            return False

    async def set_json(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Сериализовать в JSON и сохранить."""
        return await self.set(key, json.dumps(value, ensure_ascii=False, default=str), ttl)

    async def delete(self, key: str) -> bool:
        """Удалить ключ."""
        if not self._available or not self._client:
            return False
        try:
            await self._client.delete(key)
            return True
        except Exception:
            return False

    async def exists(self, key: str) -> bool:
        """Проверить существование ключа."""
        if not self._available or not self._client:
            return False
        try:
            return await self._client.exists(key) > 0
        except Exception:
            return False

    async def incr(self, key: str) -> int:
        """Инкремент счётчика."""
        if not self._available or not self._client:
            return 0
        try:
            return await self._client.incr(key)
        except Exception:
            return 0

    async def expire(self, key: str, ttl: int) -> bool:
        """Установить TTL на существующий ключ."""
        if not self._available or not self._client:
            return False
        try:
            return await self._client.expire(key, ttl)
        except Exception:
            return False

    async def close(self):
        """Закрыть соединение."""
        if self._client:
            await self._client.close()
            self._available = False


def get_cache() -> RedisCache:
    """Получить глобальный экземпляр кэша (thread-safe singleton)."""
    global _cache_instance
    if _cache_instance is None:
        with _cache_lock:
            if _cache_instance is None:
                _cache_instance = RedisCache(settings.REDIS_URL)
    return _cache_instance


# ============================================================
# Декоратор для кэширования результатов функций
# ============================================================

def cached(ttl: int = 300, key_prefix: str = "cache"):
    """
    Декоратор для кэширования результатов асинхронных функций.
    
    Пример:
        @cached(ttl=3600, key_prefix="brands")
        async def get_brands():
            return ["Toyota", "BMW", ...]
    
    Ключ формируется как: {key_prefix}:{args_kwargs_hash}
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache = get_cache()
            
            # Формируем ключ кэша
            key_parts = [key_prefix]
            for arg in args:
                key_parts.append(str(arg))
            for k, v in kwargs.items():
                key_parts.append(f"{k}={v}")
            cache_key = ":".join(key_parts)
            
            # Пробуем достать из кэша
            cached_value = await cache.get_json(cache_key)
            if cached_value is not None:
                logger.debug("Cache HIT: %s", cache_key)
                return cached_value
            
            # Если нет — вызываем функцию
            logger.debug("Cache MISS: %s", cache_key)
            result = await func(*args, **kwargs)
            
            # Сохраняем в кэш
            if result is not None:
                await cache.set_json(cache_key, result, ttl=ttl)
            
            return result
        return wrapper
    return decorator
