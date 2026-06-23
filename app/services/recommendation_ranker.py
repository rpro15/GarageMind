from __future__ import annotations

from app.domain.models import Partner, Product, RecommendationCard
from app.services.affiliate_link_builder import AffiliateLinkBuilder


class RecommendationRanker:
    """Ranks products using a deterministic, partner-aware scoring formula.

    Score formula
    -------------
    affiliate_component = partner.priority_weight  if affiliate_enabled  else 0.0
    price_component     = 1.0 - (price / max_price)   # lower price → higher score
    score               = affiliate_component * 0.40 + price_component * 0.60

    Partners with an active affiliate agreement receive a significant boost,
    ensuring they appear at the top when price is otherwise comparable.
    """

    AFFILIATE_WEIGHT: float = 0.40
    PRICE_WEIGHT: float = 0.60

    def __init__(self, link_builder: AffiliateLinkBuilder | None = None) -> None:
        self._link_builder = link_builder or AffiliateLinkBuilder()

    def rank(
        self,
        products: list[Product],
        partners: dict[str, Partner],
        *,
        top_n: int = 4,
    ) -> list[RecommendationCard]:
        if not products:
            return []

        max_price = max(p.price for p in products) or 1.0

        cards: list[RecommendationCard] = []
        for product in products:
            partner = partners.get(product.partner_id)
            if partner is None:
                continue

            affiliate_component = (
                partner.priority_weight if partner.affiliate_enabled else 0.0
            )
            price_component = 1.0 - (product.price / max_price)
            score = (
                affiliate_component * self.AFFILIATE_WEIGHT
                + price_component * self.PRICE_WEIGHT
            )

            affiliate_url = self._link_builder.build(product, partner)
            reason = self._build_reason(partner, price_component)

            cards.append(
                RecommendationCard(
                    product=product,
                    partner=partner,
                    affiliate_url=affiliate_url,
                    score=score,
                    reason=reason,
                )
            )

        cards.sort(key=lambda c: c.score, reverse=True)
        return cards[:top_n]

    @staticmethod
    def _build_reason(partner: Partner, price_component: float) -> str:
        parts: list[str] = []
        if partner.affiliate_enabled:
            parts.append(f"partner offer from {partner.name}")
        if price_component > 0.5:
            parts.append("competitive price")
        return ", ".join(parts) if parts else f"available at {partner.name}"
