"""
Источник Wildberries.
Стратегия:
1. Кэш (in-memory, 5 мин)
2. Официальный API Wildberries (нужен ключ продавца)
3. Парсинг через поисковый запрос (с ротацией User-Agent + кэшем ошибок)
"""
import logging
import random
import asyncio
import time
from typing import List, Optional
import httpx

from app.domain.models import Product, TireRequest
from app.services.sources.multi_source import BaseSource

logger = logging.getLogger(__name__)

# Ротация User-Agent для обхода блокировки
_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:133.0) Gecko/20100101 Firefox/133.0",
]

# Простой in-memory кэш
_wb_cache: dict = {}
_WB_CACHE_TTL = 300  # 5 минут


def _cache_key(request: TireRequest) -> str:
    return f"wb:{request.brand}:{request.model}:{request.year}:{request.season.value if request.season else ''}"


def _get_cached(key: str) -> Optional[List[Product]]:
    entry = _wb_cache.get(key)
    if entry:
        ts, products = entry
        if time.time() - ts < _WB_CACHE_TTL:
            return products
        del _wb_cache[key]
    return None


def _set_cached(key: str, products: List[Product]):
    _wb_cache[key] = (time.time(), products)
    # Очистка старых записей
    if len(_wb_cache) > 100:
        now = time.time()
        for k in list(_wb_cache.keys()):
            ts, _ = _wb_cache[k]
            if now - ts > _WB_CACHE_TTL:
                del _wb_cache[k]


class WildberriesSource(BaseSource):
    name = "wildberries"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self._client = httpx.AsyncClient(timeout=15.0, follow_redirects=True, trust_env=False)

    async def fetch(self, request: TireRequest) -> List[Product]:
        """Пробует кэш, API, потом парсинг с ротацией UA."""
        key = _cache_key(request)

        # 1. Кэш
        cached = _get_cached(key)
        if cached is not None:
            logger.debug("Wildberries cache HIT: %s", key)
            return cached

        # 2. API (если есть ключ)
        products = []
        if self.api_key:
            try:
                products = await self._via_api(request)
            except Exception as e:
                logger.warning("Wildberries API error: %s", e)

        # 3. Парсинг
        if not products:
            try:
                products = await self._via_parse(request)
            except Exception as e:
                logger.warning("Wildberries parse error: %s", e)

        # 4. Кэшируем (даже пустой)
        _set_cached(key, products)
        return products

    async def _via_api(self, request: TireRequest) -> List[Product]:
        """Официальный API Wildberries (для продавцов)."""
        query = f"шины {request.brand} {request.model} {request.year}"
        params = {
            "query": query,
            "sort": "popular",
            "limit": 10,
        }
        headers = {"Authorization": self.api_key}
        resp = await self._client.get(
            "https://suppliers-api.wildberries.ru/api/v3/catalog/search",
            params=params,
            headers=headers,
        )
        resp.raise_for_status()
        data = resp.json()
        products = []
        for item in data.get("data", {}).get("products", []):
            products.append(Product(
                id=f"wb_{item['id']}",
                name=item.get("name", ""),
                price=float(item.get("salePriceU", 0)) / 100,
                currency="RUB",
                image_url=f"https://basket-{item.get('basket', '01')}.wb.ru/vol{item['id']}/part{item['id']}/images/big/1.jpg",
                partner_link=f"https://www.wildberries.ru/catalog/{item['id']}/detail.aspx",
                source="wildberries",
                rating=float(item.get("rating", 0)),
            ))
        return products

    async def _via_parse(self, request: TireRequest) -> List[Product]:
        """
        Парсинг Wildberries через поисковый запрос.
        Ротация User-Agent + случайная задержка для обхода блокировки.
        """
        query = f"шины {request.brand} {request.model} {request.year}"
        params = {
            "query": query,
            "resultset": "catalog",
            "sort": "popular",
            "page": 1,
        }
        user_agent = random.choice(_USER_AGENTS)
        headers = {
            "User-Agent": user_agent,
            "Accept": "application/json",
            "Accept-Language": "ru-RU,ru;q=0.9",
            "Referer": "https://www.wildberries.ru/",
        }

        try:
            # Случайная задержка (0.5-2 сек) для обхода блокировки
            await asyncio.sleep(random.uniform(0.5, 2.0))

            # Попытка 1: основной endpoint
            resp = await self._client.get(
                "https://search.wb.ru/exactmatch/ru/common/v4/search",
                params=params,
                headers=headers,
            )

            # Если 403 -- fallback на альтернативный endpoint
            if resp.status_code == 403:
                logger.warning("Wildberries blocked (403). Trying alternative endpoint...")
                resp = await self._client.get(
                    "https://search.wb.ru/common/v5/search",
                    params={**params, "appType": "1", "curr": "rub", "dest": "-1257786"},
                    headers=headers,
                )
                if resp.status_code == 403:
                    logger.warning("Wildberries blocked on both endpoints. Need proxy.")
                    return []

            # Если 429 -- rate limited, ждём
            if resp.status_code == 429:
                retry_after = int(resp.headers.get("Retry-After", "5"))
                logger.warning("Wildberries rate limited (429). Waiting %ds...", retry_after)
                await asyncio.sleep(min(retry_after, 30))
                return []

            resp.raise_for_status()
            data = resp.json()
            return self._parse_products(data)

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                logger.warning("Wildberries 429 caught in exception handler")
                return []
            logger.warning("Wildberries HTTP error (%s): %s", type(e).__name__, e)
            return []
        except Exception as e:
            logger.warning("Wildberries parse error (%s): %s", type(e).__name__, e)
            return []

    def _parse_products(self, data: dict) -> List[Product]:
        products = []
        for item in data.get("data", {}).get("products", [])[:10]:
            product_id = item.get("id", 0)
            products.append(Product(
                id=f"wb_{product_id}",
                name=item.get("name", ""),
                price=float(item.get("salePriceU", 0)) / 100,
                currency="RUB",
                image_url=f"https://basket-{item.get('basket', '01')}.wb.ru/vol{product_id}/part{product_id}/images/big/1.jpg",
                partner_link=f"https://www.wildberries.ru/catalog/{product_id}/detail.aspx",
                source="wildberries",
                rating=float(item.get("rating", 0)),
            ))
        return products

    async def search(self, query: str, max_results: int = 5) -> List[Product]:
        """Поиск по текстовому запросу (реализация ProductCatalog)."""
        params = {
            "query": query,
            "resultset": "catalog",
            "sort": "popular",
            "page": 1,
        }
        user_agent = random.choice(_USER_AGENTS)
        headers = {
            "User-Agent": user_agent,
            "Accept": "application/json",
            "Accept-Language": "ru-RU,ru;q=0.9",
            "Referer": "https://www.wildberries.ru/",
        }
        try:
            await asyncio.sleep(random.uniform(0.3, 1.0))
            resp = await self._client.get(
                "https://search.wb.ru/exactmatch/ru/common/v4/search",
                params=params,
                headers=headers,
            )
            if resp.status_code == 200:
                data = resp.json()
                return self._parse_products(data)[:max_results]
        except Exception as e:
            logger.warning("Wildberries search error: %s", e)
        return []

    async def close(self):
        await self._client.aclose()
