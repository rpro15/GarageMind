import logging
from typing import List
from app.domain.models import Product, TireRequest

logger = logging.getLogger(__name__)


class BaseSource:
    name: str = "base"

    async def fetch(self, request: TireRequest) -> List[Product]:
        raise NotImplementedError


class MultiSourceProductService:
    def __init__(self):
        self._sources: List[BaseSource] = []

    def register_source(self, source: BaseSource):
        self._sources.append(source)

    async def find_tires(self, request: TireRequest, min_products: int = 5) -> List[Product]:
        all_products = []
        seen_ids = set()

        for source in self._sources:
            try:
                products = await source.fetch(request)
                for p in products:
                    if p.id not in seen_ids:
                        all_products.append(p)
                        seen_ids.add(p.id)
                logger.info("Source %s: %d товаров (всего %d)", source.name, len(products), len(all_products))
            except Exception as e:
                logger.warning("Source %s error: %s", source.name, e)
                continue

            if len(all_products) >= min_products:
                break

        return all_products
