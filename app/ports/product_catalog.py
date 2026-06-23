# app/ports/product_catalog.py
from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.models import Product, TireRequest

class ProductCatalog(ABC):
    @abstractmethod
    async def find_tires(self, request: TireRequest) -> List[Product]:
        pass

    @abstractmethod
    async def find_products_by_query(self, query: str, category: Optional[str] = None) -> List[Product]:
        pass