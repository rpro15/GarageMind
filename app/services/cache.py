from __future__ import annotations

"""Optional Redis cache for recommendation results.

When Redis is not available (e.g. during development without docker-compose),
the cache silently degrades to a no-op so the service still works.
"""

import json
import logging
from typing import Any

_DEFAULT_TTL = 3600  # 1 hour


class RecommendationCache:
    """Wraps a Redis connection.  Falls back to no-op if Redis is unavailable."""

    def __init__(self, redis_url: str, logger: logging.Logger) -> None:
        self._logger = logger
        self._client: Any = None
        try:
            import redis  # type: ignore[import]

            client = redis.from_url(redis_url, decode_responses=True, socket_connect_timeout=2)
            client.ping()
            self._client = client
            self._logger.info("Redis cache connected: %s", redis_url)
        except Exception as exc:  # noqa: BLE001
            self._logger.warning(
                "Redis unavailable (%s) — running without cache.", exc
            )

    @property
    def available(self) -> bool:
        return self._client is not None

    def _key(self, request_dict: dict) -> str:
        parts = "|".join(
            f"{k}={request_dict[k]}"
            for k in sorted(request_dict)
        )
        return f"garagemind:rec:{parts}"

    def get(self, request_dict: dict) -> list[dict] | None:
        if not self._client:
            return None
        try:
            raw = self._client.get(self._key(request_dict))
            return json.loads(raw) if raw else None
        except Exception as exc:  # noqa: BLE001
            self._logger.debug("Cache get error: %s", exc)
            return None

    def set(self, request_dict: dict, recommendations: list[dict], ttl: int = _DEFAULT_TTL) -> None:
        if not self._client:
            return
        try:
            self._client.setex(self._key(request_dict), ttl, json.dumps(recommendations))
        except Exception as exc:  # noqa: BLE001
            self._logger.debug("Cache set error: %s", exc)
