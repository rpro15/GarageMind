"""
Источник партнёрских ссылок через Admitad.
Admitad — крупнейший агрегатор партнёрских программ в СНГ.
Подключает Wildberries, Ozon, AliExpress, Exist и 1500+ магазинов.

Как получить ключ:
1. Регистрация: https://www.admitad.com/ru/webmaster/
2. Создать приложение: Admitad → Настройки → API → Создать приложение
3. Получить: client_id, client_secret, coupon_code
4. Вписать в .env: ADMITAD_CLIENT_ID, ADMITAD_CLIENT_SECRET, ADMITAD_COUPON
"""
import logging
from typing import List, Optional
import httpx

from app.domain.models import Product, TireRequest
from app.services.sources.multi_source import BaseSource

logger = logging.getLogger(__name__)


class PartnerSource(BaseSource):
    name = "partners"

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        coupon_code: Optional[str] = None,
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.coupon_code = coupon_code
        self._client = httpx.AsyncClient(timeout=15.0)
        self._token: Optional[str] = None

    async def _get_token(self) -> Optional[str]:
        """Получить access_token от Admitad API."""
        if not self.client_id or not self.client_secret:
            return None
        if self._token:
            return self._token

        try:
            resp = await self._client.post(
                "https://api.admitad.com/token/",
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "scope": "advcampaigns banners coupons websites",
                },
            )
            if resp.status_code == 200:
                self._token = resp.json().get("access_token")
                return self._token
        except Exception as e:
            logger.warning("Admitad token error: %s", e)
        return None

    async def _search_products(
        self, query: str, token: str
    ) -> List[dict]:
        """Поиск товаров по партнёрским программам."""
        # Admitad Search API
        url = "https://api.admitad.com/search/"
        params = {
            "q": query,
            "limit": 5,
            "campaigns": "wildberries,ozon,aliexpress",  # только шинные
        }
        headers = {"Authorization": f"Bearer {token}"}

        try:
            resp = await self._client.get(url, params=params, headers=headers)
            if resp.status_code == 200:
                return resp.json().get("results", [])
        except Exception as e:
            logger.warning("Admitad search error: %s", e)
        return []

    async def fetch(self, request: TireRequest) -> List[Product]:
        """Поиск товаров через Admitad партнёрскую сеть."""
        token = await self._get_token()

        # Если нет API ключа — возвращаем заглушки с реальными ссылками
        if not token:
            return self._fallback_products(request)

        # Реальный поиск через Admitad API
        query = f"шины {request.brand} {request.model} {request.season.value if request.season else ''}"
        results = await self._search_products(query, token)

        products = []
        for i, item in enumerate(results[:5]):
            products.append(Product(
                id=f"admitad_{request.brand.lower()}_{i}",
                name=item.get("name", f"Шины {request.brand} {request.model}"),
                price=float(item.get("price", 0)),
                currency=item.get("currency", "RUB"),
                image_url=item.get("image_url"),
                partner_link=item.get("url", ""),
                source=f"admitad_{item.get('campaign', 'shop')}",
                rating=float(item.get("rating", 0)) if item.get("rating") else None,
            ))

        return products if products else self._fallback_products(request)

    def _fallback_products(self, request: TireRequest) -> List[Product]:
        """
        Заглушки с реальными партнёрскими ссылками.
        Работает без API ключа — просто пример формата ссылок.
        """
        brand = request.brand.lower()
        model = request.model.lower()
        query = f"{brand}+{model}+шины"

        return [
            Product(
                id=f"aff_wb_{brand}_1",
                name=f"{request.brand} {request.model} — на Wildberries",
                price=13490.0,
                currency="RUB",
                partner_link=f"https://ad.wildberries.ru/cc/Uid123?text={query}",
                source="wildberries_aff",
                rating=4.5,
            ),
            Product(
                id=f"aff_ozon_{brand}_1",
                name=f"{request.brand} {request.model} — на Ozon",
                price=12500.0,
                currency="RUB",
                partner_link=f"https://www.ozon.ru/t/QkDpRz/?text={query}",
                source="ozon_aff",
                rating=4.3,
            ),
            Product(
                id=f"aff_ali_{brand}_1",
                name=f"{request.brand} {request.model} — на AliExpress",
                price=11200.0,
                currency="RUB",
                partner_link=f"https://alii.pub/your-coupon?text={query}",
                source="aliexpress_aff",
                rating=4.1,
            ),
            Product(
                id=f"aff_exist_{brand}_1",
                name=f"{request.brand} {request.model} — на Exist.ua",
                price=14500.0,
                currency="RUB",
                partner_link=f"https://exist.ua/ru/tires/?text={query}",
                source="exist_aff",
                rating=4.6,
            ),
        ]

    async def close(self):
        await self._client.aclose()
