# app/services/tire_recommendation.py
from typing import List, Dict, Any
from app.domain.models import TireRequest, RecommendationResult, Product
from app.ports.llm_client import LLMClient
from app.ports.product_catalog import ProductCatalog
from app.services.rag import Retriever


class TireRecommendationService:
    def __init__(
        self,
        llm_client: LLMClient,
        catalog: ProductCatalog,
        retriever: Retriever | None = None,
    ):
        self.llm = llm_client
        self.catalog = catalog
        self.retriever = retriever

    async def get_recommendation(self, request: TireRequest) -> RecommendationResult:
        prompt = self._build_prompt(request)

        # 1. Генерируем совет AI
        advice = await self.llm.generate_text(prompt, system_prompt=self._system_prompt())

        # 2. Получаем товары из каталога
        products = await self.catalog.find_tires(request)

        # 3. Если есть RAG — обогащаем результат семантическим поиском
        if self.retriever and products:
            rag_query = f"{request.brand} {request.model} шины {request.season.value if request.season else ''}"
            rag_products = await self.retriever.search_products(
                query=rag_query,
                brand=request.brand,
                top_k=5,
            )
            # Добавляем RAG-товары, которых нет в products
            existing_ids = {p.id for p in products}
            for rp in rag_products:
                if rp.id not in existing_ids:
                    products.append(rp)

        return RecommendationResult(
            advice=advice,
            products=products,
            request=request,
        )

    def _system_prompt(self) -> str:
        return (
            "Ты — эксперт по подбору автомобильных шин. "
            "Давай рекомендации по размеру, сезону, бренду, учитывая стиль вождения и бюджет. "
            "Будь конкретен, не пиши общие фразы. "
            "Если бюджет не указан, предложи несколько вариантов в разных ценовых категориях."
        )

    def _build_prompt(self, request: TireRequest) -> str:
        parts = [
            f"Автомобиль: {request.brand} {request.model} {request.year} года выпуска.",
            f"Стиль вождения: {request.driving_style.value}.",
        ]
        if request.budget:
            parts.append(f"Бюджет: до {request.budget} рублей за комплект (4 шт.).")
        if request.season:
            parts.append(f"Сезон: {request.season.value}.")
        parts.append("Какие шины порекомендуешь? Укажи размеры, рекомендуемые бренды и примерные цены.")
        return "\n".join(parts)