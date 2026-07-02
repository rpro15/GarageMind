"""
Скрипт для первичной индексации каталога товаров в векторную базу.
Запускать после того, как каталог наполнен данными.
"""
import asyncio
import logging

from app.services.rag import EmbeddingService, VectorStore, Retriever
from app.adapters.partner_api import MockPartnerCatalog
from app.domain.models import TireRequest, DrivingStyle, Season

logger = logging.getLogger(__name__)


async def index_all():
    embedding = EmbeddingService()
    store = VectorStore()
    retriever = Retriever(embedding, store)
    catalog = MockPartnerCatalog()

    # Получаем все товары из каталога (для примера — 3 запроса)
    all_products = []
    for brand in ["Toyota", "Kia", "Volkswagen"]:
        req = TireRequest(
            brand=brand,
            model="",
            year=2024,
            driving_style=DrivingStyle.comfort,
            season=Season.summer,
        )
        products = await catalog.find_tires(req)
        all_products.extend(products)

    if all_products:
        indexed = await retriever.index_products(all_products)
        logger.info("✅ Индексировано %d товаров в векторную базу", indexed)
        logger.info("   Всего в базе: %d", store.count())
    else:
        logger.warning("Нет товаров для индексации")

    await embedding.close()
    return store.count()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(index_all())
