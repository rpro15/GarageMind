from __future__ import annotations

from app.domain.models import RecommendationCard
from app.services.partner_registry import PartnerRegistry
from app.services.recommendation_ranker import RecommendationRanker

ALLOWED_CATEGORIES: frozenset[str] = frozenset({"tires", "wheels"})


class RecommendationService:
    """Orchestrates partner registry and ranker to produce recommendation cards.

    A VIN is deliberately *not* required for the core flow; it may be passed
    as optional context in a future iteration to narrow the product selection.
    """

    def __init__(
        self,
        registry: PartnerRegistry,
        ranker: RecommendationRanker,
    ) -> None:
        self._registry = registry
        self._ranker = ranker

    def recommend(
        self,
        category: str | None = None,
        top_n: int = 4,
    ) -> list[RecommendationCard]:
        products = self._registry.list_products(category=category)
        partners = {p.id: p for p in self._registry.list_partners()}
        return self._ranker.rank(products, partners, top_n=top_n)
