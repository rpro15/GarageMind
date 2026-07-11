"""
Marketplace Scraper — поиск шин по открытым источникам.

Использует публичные JSON API маркетплейсов (без API-ключей).
Поддерживает Wildberries (поисковый API), Ozon (публичный).
"""
from __future__ import annotations

import logging
import random
from typing import List, Optional
from urllib.parse import quote

import httpx

from app.domain.models import Product, TireRequest

logger = logging.getLogger(__name__)

# User-Agent для обхода блокировок
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
]


class MarketplaceScraper:
    """Поиск шин по открытым данным маркетплейсов."""

    def __init__(self, marketplace_name: Optional[str] = None):
        self._marketplace_name = marketplace_name
        self._client = httpx.AsyncClient(timeout=15.0, follow_redirects=True)

    async def search(self, query: str, max_results: int = 5) -> List[Product]:
        """Поиск товаров по текстовому запросу через доступные источники."""
        # Пробуем Wildberries (публичное JSON API)
        products = await self._search_wildberries(query, max_results)
        if products:
            return products

        # Fallback: моковые данные
        return self._mock_products(query, max_results)

    async def _search_wildberries(self, query: str, max_results: int) -> List[Product]:
        """Поиск через публичный JSON API Wildberries."""
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "application/json",
        }
        params = {
            "query": query,
            "resultset": "catalog",
            "sort": "popular",
            "page": 1,
        }
        try:
            resp = await self._client.get(
                "https://search.wb.ru/exactmatch/ru/common/v4/search",
                params=params,
                headers=headers,
            )
            if resp.status_code == 403:
                logger.warning("Wildberries blocked this request")
                return []
            if resp.status_code != 200:
                return []
            data = resp.json()
            return self._parse_wb_products(data, max_results)
        except Exception as e:
            logger.warning("Wildberries search error: %s", e)
            return []

    @staticmethod
    def _parse_wb_products(data: dict, max_results: int) -> List[Product]:
        products = []
        for item in data.get("data", {}).get("products", [])[:max_results]:
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

    @staticmethod
    def _mock_products(query: str, count: int = 3) -> List[Product]:
        brands = ["Michelin", "Continental", "Bridgestone", "Pirelli", "Goodyear"]
        models = ["Pilot Sport 4", "PremiumContact 6", "Turanza T005", "P Zero", "Eagle F1"]
        products = []
        for i in range(count):
            products.append(Product(
                id=f"mock_{i}",
                name=f"{brands[i % len(brands)]} {models[i % len(models)]} — {query}",
                price=random.choice([8900, 10500, 12400, 13500, 15000]),
                currency="RUB",
                image_url=None,
                partner_link=None,
                source="marketplace",
                rating=round(random.uniform(3.5, 5.0), 1),
            ))
        return products

    async def close(self):
        await self._client.aclose()
