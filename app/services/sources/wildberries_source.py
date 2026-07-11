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

        # 4. Кэшируем (даже пустой — чтобы не долбить заблокированный источник)
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
        # Парсим ответ
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
        # Случайный User-Agent
        user_agent = random.choice(_USER_AGENTS)
        headers = {
            "User-Agent": user_agent,
            "Accept": "application/json",
            "Accept-Language": "ru-RU,ru;q=0.9",
            "Referer": "https://www.wildberries.ru/",
        }

        try:
            # Небольшая случайная задержка (0.5-2 сек)
            await asyncio.sleep(random.uniform(0.5, 2.0))

            resp = await self._client.get(
                "https://search.wb.ru/exactmatch/ru/common/v4/search",
                params=params,
                headers=headers,
            )
            if resp.status_code == 403:
                logger.warning("Wildberries blocked (403). Trying alternative endpoint...")
                # Fallback: другой endpoint
                resp = await self._client.get(
                    "https://search.wb.ru/common/v5/search",
                    params={**params, "appType": "1", "curr": "rub", "dest": "-1257786"},
                    headers=headers,
                )

            if resp.status_code == 403:
                logger.warning("Wildberries blocked on both endpoints. Need proxy.")
                return []

            resp.raise_for_status()
            data = resp.json()
            return self._parse_products(data)

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

    async def close(self):
        await self._client.aclose()
