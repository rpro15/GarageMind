from __future__ import annotations

import datetime
import logging

from app.api.errors import ApiError
from app.domain.models import ProductRecommendation, RecommendRequest, RecommendResult
from app.ports.product_search import ProductSearchProvider
from app.services.cache import RecommendationCache

VALID_CATEGORIES = {"tires", "wheels"}
VALID_SEASONS = {"winter", "summer", "all_season"}
VALID_DRIVING_STYLES = {"comfort", "sport", "offroad"}

_MAX_RESULTS = 4


class RecommendationService:
    def __init__(
        self,
        provider: ProductSearchProvider,
        partner_marketplaces: list[str],
        logger: logging.Logger,
        cache: RecommendationCache | None = None,
    ) -> None:
        self._provider = provider
        self._partner_marketplaces = partner_marketplaces
        self._logger = logger
        self._cache = cache

    def recommend(self, request: RecommendRequest) -> RecommendResult:
        self._validate(request)

        cache_key = {
            "make": request.car_make,
            "model": request.car_model,
            "year": request.car_year,
            "category": request.category,
            "season": request.season,
            "style": request.driving_style,
            "budget": request.budget_rub,
        }

        if self._cache:
            cached = self._cache.get(cache_key)
            if cached is not None:
                self._logger.debug("Cache hit for recommendation request")
                from app.domain.models import ProductRecommendation as PR
                raw_results = [
                    PR(
                        rank=c["rank"],
                        product_name=c["product_name"],
                        category=c["category"],
                        season=c["season"],
                        price_rub=c["price_rub"],
                        marketplace=c["marketplace"],
                        affiliate_url=c["affiliate_url"],
                        image_url=c.get("image_url"),
                        is_partner=c["is_partner"],
                        source=c["source"],
                    )
                    for c in cached
                ]
                return RecommendResult(
                    recommendations=raw_results,
                    car_make=request.car_make,
                    car_model=request.car_model,
                    car_year=request.car_year,
                    partner_priority=self._partner_marketplaces,
                )

        raw_results = self._provider.search(request)

        ranked = self._apply_partner_priority(raw_results)

        if self._cache and ranked:
            self._cache.set(cache_key, [r.to_dict() for r in ranked])

        self._logger.debug(
            "Recommendation results car=%s %s/%s category=%s count=%s",
            request.car_make,
            request.car_model,
            request.car_year,
            request.category,
            len(ranked),
        )

        return RecommendResult(
            recommendations=ranked,
            car_make=request.car_make,
            car_model=request.car_model,
            car_year=request.car_year,
            partner_priority=self._partner_marketplaces,
        )

    def _validate(self, request: RecommendRequest) -> None:
        errors: list[str] = []

        if not request.car_make or not request.car_make.strip():
            errors.append("car_make is required.")
        if not request.car_model or not request.car_model.strip():
            errors.append("car_model is required.")

        current_year = datetime.datetime.now().year
        if not (1900 <= request.car_year <= current_year + 1):
            errors.append(
                f"car_year must be between 1900 and {current_year + 1}."
            )

        if request.category not in VALID_CATEGORIES:
            errors.append(
                f"category must be one of: {', '.join(sorted(VALID_CATEGORIES))}."
            )
        if request.season not in VALID_SEASONS:
            errors.append(
                f"season must be one of: {', '.join(sorted(VALID_SEASONS))}."
            )
        if request.driving_style not in VALID_DRIVING_STYLES:
            errors.append(
                f"driving_style must be one of: {', '.join(sorted(VALID_DRIVING_STYLES))}."
            )
        if request.budget_rub <= 0:
            errors.append("budget_rub must be a positive integer.")

        if errors:
            raise ApiError(
                code="invalid_recommend_request",
                message="Recommendation request contains invalid fields.",
                status_code=400,
                details={"errors": errors},
            )

    def _apply_partner_priority(
        self, items: list[ProductRecommendation]
    ) -> list[ProductRecommendation]:
        """Sort items so partner marketplaces appear first, then re-rank."""
        partner_set = set(self._partner_marketplaces)

        partner_items = [r for r in items if r.marketplace in partner_set]
        non_partner_items = [r for r in items if r.marketplace not in partner_set]

        combined = partner_items + non_partner_items
        combined = combined[:_MAX_RESULTS]

        result: list[ProductRecommendation] = []
        for rank, item in enumerate(combined, start=1):
            result.append(
                ProductRecommendation(
                    rank=rank,
                    product_name=item.product_name,
                    category=item.category,
                    season=item.season,
                    price_rub=item.price_rub,
                    marketplace=item.marketplace,
                    affiliate_url=item.affiliate_url,
                    image_url=item.image_url,
                    is_partner=item.marketplace in partner_set,
                    source=item.source,
                )
            )
        return result


def build_recommendation_service(
    provider_name: str,
    partner_marketplaces: list[str],
    logger: logging.Logger,
    redis_url: str | None = None,
    deepseek_api_key: str | None = None,
    deepseek_partner_id: str = "GARAGEMIND",
) -> RecommendationService:
    provider: ProductSearchProvider

    if provider_name == "deepseek" and deepseek_api_key:
        from app.adapters.deepseek_recommendation import DeepSeekProductSearchProvider

        provider = DeepSeekProductSearchProvider(
            api_key=deepseek_api_key,
            partner_id=deepseek_partner_id,
            logger=logger,
        )
    elif provider_name == "stub":
        from app.adapters.stub_product_search import StubProductSearchProvider

        provider = StubProductSearchProvider()
    else:
        logger.warning(
            "Unsupported product search provider '%s'; falling back to stub.",
            provider_name,
        )
        from app.adapters.stub_product_search import StubProductSearchProvider

        provider = StubProductSearchProvider()

    cache: RecommendationCache | None = None
    if redis_url:
        cache = RecommendationCache(redis_url=redis_url, logger=logger)

    return RecommendationService(
        provider=provider,
        partner_marketplaces=partner_marketplaces,
        logger=logger,
        cache=cache,
    )
