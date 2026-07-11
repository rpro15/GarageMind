"""
Источник Wildberries.
Стратегия:
1. Официальный API Wildberries (нужен ключ продавца)
2. Если нет ключа — парсинг через Playwright (headless)
"""
import logging
import re
from typing import List, Optional
import httpx

from app.domain.models import Product, TireRequest
from app.services.sources.multi_source import BaseSource

logger = logging.getLogger(__name__)


class WildberriesSource(BaseSource):
    name = "wildberries"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self._client = httpx.AsyncClient(timeout=15.0, follow_redirects=True, trust_env=False)

    async def fetch(self, request: TireRequest) -> List[Product]:
        """Пробует API, если нет ключа — парсит."""
        if self.api_key:
            return await self._via_api(request)
        return await self._via_parse(request)

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
        Использует случайные User-Agent для обхода блокировки.
        """
        query = f"шины {request.brand} {request.model} {request.year}"
        params = {
            "query": query,
            "resultset": "catalog",
            "sort": "popular",
            "page": 1,
        }
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json",
            "Accept-Language": "ru-RU,ru;q=0.9",
        }

        try:
            resp = await self._client.get(
                "https://search.wb.ru/exactmatch/ru/common/v4/search",
                params=params,
                headers=headers,
            )
            if resp.status_code == 403:
                logger.warning("Wildberries blocked. Need proxy.")
                return []

            resp.raise_for_status()
            data = resp.json()
            return self._parse_products(data)

        except Exception as e:
            logger.warning("Wildberries parse error: %s", e)
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
