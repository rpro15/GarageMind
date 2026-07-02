# app/services/tire_recommendation.py
import logging
from typing import List
from app.domain.models import (
    TireRequest, RecommendationResult, Product, 
    DeliverySpeed, OrderType,
)
from app.ports.llm_client import LLMClient
from app.ports.product_catalog import ProductCatalog
from app.services.rag import Retriever
from app.services.sources import MultiSourceProductService
from app.services.sources.wildberries_source import WildberriesSource
from app.services.sources.partner_source import PartnerSource

logger = logging.getLogger(__name__)


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
        self._multi_source = self._setup_sources()

    def _setup_sources(self) -> MultiSourceProductService:
        ms = MultiSourceProductService()
        ms.register_source(WildberriesSource())
        ms.register_source(PartnerSource())
        return ms

    async def get_recommendation(self, request: TireRequest) -> RecommendationResult:
        """Полная рекомендация с учётом региона, доставки, наличия."""
        prompt = self._build_prompt(request)

        # 1. Совет AI
        advice = await self.llm.generate_text(prompt, system_prompt=self._system_prompt())

        # 2. Ищем товары из множественных источников
        products = await self._multi_source.find_tires(request, min_products=5)
        if not products:
            products = await self.catalog.find_tires(request)

        # 3. Фильтруем по предпочтениям пользователя
        products, warnings = self._filter_products(products, request)

        # 4. Обогащаем RAG (семантический поиск)
        if self.retriever and request.preferences.size_str():
            rag_products = await self.retriever.search_products(
                query=f"шины {request.brand} {request.model} {request.preferences.size_str()}",
                brand=request.brand,
                top_k=3,
            )
            existing_ids = {p.id for p in products}
            for rp in rag_products:
                if rp.id not in existing_ids:
                    products.append(rp)

        # 5. Определяем популярный выбор
        popular_pick = None
        if products:
            popular_pick = max(products, key=lambda p: p.rating or 0)

        return RecommendationResult(
            advice=advice,
            products=products,
            request=request,
            popular_pick=popular_pick,
            warnings=warnings,
        )

    def _filter_products(
        self, products: List[Product], request: TireRequest
    ) -> tuple[List[Product], List[str]]:
        """Фильтрует товары по предпочтениям, возвращает предупреждения."""
        filtered = []
        warnings = []
        pref = request.preferences
        loc = request.location

        for p in products:
            # 1. Наличие
            if pref.only_in_stock and not p.in_stock:
                continue

            # 2. Бюджет
            if request.budget and p.price > request.budget:
                warnings.append(f"⚠️ {p.name}: {p.price:.0f}₽ дороже бюджета")
                continue

            # 3. Минимальный рейтинг
            if pref.min_rating and (p.rating is None or p.rating < pref.min_rating):
                continue

            # 4. Доставка
            if pref.delivery_speed == DeliverySpeed.urgent:
                if p.delivery_days is not None and p.delivery_days > 2:
                    continue
                if not p.pickup_available and not p.in_stock:
                    continue
            elif pref.delivery_speed == DeliverySpeed.within_3_days:
                if p.delivery_days is not None and p.delivery_days > 3:
                    continue

            # 5. Способ получения
            if pref.order_type == OrderType.pickup and not p.pickup_available:
                continue

            # 6. Регион — предупреждаем, если цена указана для другого региона
            if loc.search_scope == "region":
                if p.source and "moskva" in p.source.lower() and "москва" not in loc.region.lower():
                    warnings.append(f"📦 {p.name}: цена может отличаться в вашем регионе")

            # 7. Гарантия
            if pref.min_warranty_months and p.warranty_months is not None:
                if p.warranty_months < pref.min_warranty_months:
                    continue

            filtered.append(p)

        return filtered, warnings

    def _system_prompt(self) -> str:
        return (
            "Ты — эксперт по подбору автомобильных шин. "
            "Учитывай регион пользователя, сроки доставки, сезон, стиль вождения и бюджет. "
            "Если размер шин указан — рекомендуй именно этот типоразмер. "
            "Давай конкретные модели, указывай примерные цены с учётом региона. "
            "Не пиши общие фразы."
        )

    def _build_prompt(self, request: TireRequest) -> str:
        pref = request.preferences
        loc = request.location

        parts = [
            f"Автомобиль: {request.brand} {request.model} {request.year} года.",
            f"Стиль вождения: {request.driving_style.value}.",
            f"Регион: {loc.region}, город: {loc.city}.",
        ]

        if request.budget:
            parts.append(f"Бюджет: до {request.budget} рублей.")
        if request.season:
            parts.append(f"Сезон: {request.season.value}.")
        
        size = pref.size_str()
        if size:
            parts.append(f"Размер шин: {size}.")
        
        parts.append(f"Доставка: {pref.delivery_speed.value}.")
        parts.append(f"Способ получения: {pref.order_type.value}.")
        
        if pref.preferred_brands:
            parts.append(f"Предпочтительные бренды: {', '.join(pref.preferred_brands)}.")
        if pref.exclude_brands:
            parts.append(f"Исключить бренды: {', '.join(pref.exclude_brands)}.")
        
        parts.append(
            "Какие шины порекомендуешь? "
            "Укажи размеры, бренды, примерные цены с учётом региона и доступность."
        )
        return "\n".join(parts)
