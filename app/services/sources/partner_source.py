"""
Источник партнёрских ссылок.
Подключается к Admitad / CityAds / партнёрским программам.
"""
import logging
from typing import List, Optional
from app.domain.models import Product, TireRequest
from app.services.sources.multi_source import BaseSource

logger = logging.getLogger(__name__)


class PartnerSource(BaseSource):
    """
    Генерирует партнёрские ссылки для маркетплейсов.
    В реальности здесь будет API Admitad / actionpay / gdeslon.
    """

    name = "partners"

    # Партнёрские ID (заменить на свои)
    PARTNER_IDS = {
        "wildberries": "YOUR_WB_ID",
        "ozon": "YOUR_OZON_ID",
        "exist": "YOUR_EXIST_ID",
    }

    def __init__(self, partner_id: str = "default"):
        self.partner_id = partner_id

    async def fetch(self, request: TireRequest) -> List[Product]:
        """
        Пока возвращает заглушки с партнёрскими ссылками.
        При интеграции с Admitad — будет реальный API.
        """
        return [
            Product(
                id=f"part_ozon_{request.brand.lower()}_1",
                name=f"{request.brand} {request.model} — шины летние (партнёр)",
                price=12500.0,
                currency="RUB",
                partner_link=f"https://www.ozon.ru/product/?partner={self.PARTNER_IDS['ozon']}&text={request.brand}+{request.model}+шины",
                source="ozon_partner",
                rating=4.3,
            ),
            Product(
                id=f"part_wb_{request.brand.lower()}_1",
                name=f"{request.brand} {request.model} — шины зимние (партнёр)",
                price=15800.0,
                currency="RUB",
                partner_link=f"https://ad.wildberries.ru/{self.PARTNER_IDS['wildberries']}?text={request.brand}+{request.model}",
                source="wildberries_partner",
                rating=4.5,
            ),
        ]
