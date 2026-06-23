# app/adapters/partner_api.py
from typing import List, Optional
from app.domain.models import Product, TireRequest
from app.ports.product_catalog import ProductCatalog
import random

class MockPartnerCatalog(ProductCatalog):
    """Заглушка, возвращающая моковые товары."""
    async def find_tires(self, request: TireRequest) -> List[Product]:
        mock_products = [
            Product(
                id="1",
                name="Michelin Pilot Alpin 5",
                price=8500.0,
                image_url="https://via.placeholder.com/100?text=Tire1",
                partner_link="https://example.com/partner/1",
                source="mock"
            ),
            Product(
                id="2",
                name="Continental WinterContact TS 860",
                price=7900.0,
                image_url="https://via.placeholder.com/100?text=Tire2",
                partner_link="https://example.com/partner/2",
                source="mock"
            ),
            Product(
                id="3",
                name="Nokian Hakkapeliitta R5",
                price=9200.0,
                image_url="https://via.placeholder.com/100?text=Tire3",
                partner_link="https://example.com/partner/3",
                source="mock"
            ),
        ]
        return random.sample(mock_products, k=random.randint(1, 3))

    async def find_products_by_query(self, query: str, category: Optional[str] = None) -> List[Product]:
        return []