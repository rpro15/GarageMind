from __future__ import annotations

from app.domain.catalog import Partner, Product, Recommendation

_MAX_PRICE = 20_000.0
_MAX_DELIVERY_DAYS = 14


def _price_score(price: float) -> float:
    return max(0.0, 1.0 - price / _MAX_PRICE)


def _delivery_score(delivery_days: int) -> float:
    return max(0.0, 1.0 - delivery_days / _MAX_DELIVERY_DAYS)


def _rating_score(rating: float) -> float:
    return max(0.0, min(1.0, rating / 5.0))


def rank_score(product: Product, partner: Partner) -> float:
    """Deterministic ranking score.

    Formula::

        score = match_score * 0.40
              + price_score * 0.20
              + delivery_score * 0.10
              + rating_score * 0.10
              + affiliate_weight * 0.20

    ``match_score`` is always 1.0 here because products are pre-filtered by
    category before scoring.
    """
    return (
        1.0 * 0.40
        + _price_score(product.price) * 0.20
        + _delivery_score(product.delivery_days) * 0.10
        + _rating_score(product.rating) * 0.10
        + partner.affiliate_weight * 0.20
    )


def _build_reason(product: Product, partner: Partner) -> str:
    parts: list[str] = []
    if partner.has_agreement:
        parts.append("affiliate partner")
    if product.rating >= 4.5:
        parts.append("highly rated")
    if product.delivery_days <= 2:
        parts.append("fast delivery")
    if product.price < 3_000:
        parts.append("competitive price")
    return ", ".join(parts) if parts else "good overall match"


class PartnerRegistry:
    """In-memory registry of affiliate partners."""

    def __init__(self, partners: list[Partner] | None = None) -> None:
        self._partners: dict[str, Partner] = {}
        for p in (partners or _DEFAULT_PARTNERS):
            self._partners[p.id] = p

    def get(self, partner_id: str) -> Partner | None:
        return self._partners.get(partner_id)

    def all(self) -> list[Partner]:
        return list(self._partners.values())


class ProductCatalog:
    """In-memory stub product catalog for tires and wheels."""

    def __init__(self, products: list[Product] | None = None) -> None:
        self._products: dict[str, Product] = {}
        for p in (products or _DEFAULT_PRODUCTS):
            self._products[p.id] = p

    def get(self, product_id: str) -> Product | None:
        return self._products.get(product_id)

    def by_category(self, category: str) -> list[Product]:
        return [p for p in self._products.values() if p.category == category]

    def all(self) -> list[Product]:
        return list(self._products.values())


class RecommendationRanker:
    """Ranks products for a given category, preferring affiliate partners."""

    def __init__(
        self,
        catalog: ProductCatalog,
        registry: PartnerRegistry,
    ) -> None:
        self._catalog = catalog
        self._registry = registry

    def recommend(
        self, category: str, top_n: int = 4
    ) -> list[Recommendation]:
        products = self._catalog.by_category(category)
        scored: list[tuple[float, Product, Partner]] = []
        for product in products:
            partner = self._registry.get(product.partner_id)
            if partner is None:
                continue
            score = rank_score(product, partner)
            scored.append((score, product, partner))

        scored.sort(key=lambda t: t[0], reverse=True)

        results: list[Recommendation] = []
        for score, product, partner in scored[:top_n]:
            affiliate_url = partner.build_url(product.id)
            reason = _build_reason(product, partner)
            results.append(
                Recommendation(
                    product=product,
                    partner=partner,
                    score=score,
                    affiliate_url=affiliate_url,
                    reason=reason,
                )
            )
        return results


# ---------------------------------------------------------------------------
# Default stub data – replaced by real catalog/partner data in production
# ---------------------------------------------------------------------------

_DEFAULT_PARTNERS: list[Partner] = [
    Partner(
        id="ozon",
        name="Ozon",
        affiliate_weight=0.9,
        url_template="https://ozon.ru/product/{product_id}?ref=garagemind",
        has_agreement=True,
    ),
    Partner(
        id="wildberries",
        name="Wildberries",
        affiliate_weight=0.7,
        url_template="https://wildberries.ru/catalog/{product_id}/detail.aspx?ref=garagemind",
        has_agreement=True,
    ),
    Partner(
        id="avito",
        name="Avito",
        affiliate_weight=0.3,
        url_template=None,
        has_agreement=False,
    ),
]

_DEFAULT_PRODUCTS: list[Product] = [
    # Tires
    Product(
        id="tire-001",
        name="Michelin Pilot Sport 4 205/55 R16",
        category="tire",
        price=6_500.0,
        rating=4.8,
        delivery_days=3,
        partner_id="ozon",
        image_url=None,
        description="High-performance summer tyre",
    ),
    Product(
        id="tire-002",
        name="Nokian Hakkapeliitta 9 205/55 R16",
        category="tire",
        price=7_200.0,
        rating=4.9,
        delivery_days=5,
        partner_id="wildberries",
        image_url=None,
        description="Premium studded winter tyre",
    ),
    Product(
        id="tire-003",
        name="Cordiant Sport 3 195/65 R15",
        category="tire",
        price=2_800.0,
        rating=4.1,
        delivery_days=2,
        partner_id="ozon",
        image_url=None,
        description="Budget summer tyre",
    ),
    Product(
        id="tire-004",
        name="Yokohama Geolandar A/T 265/70 R17",
        category="tire",
        price=9_000.0,
        rating=4.6,
        delivery_days=7,
        partner_id="avito",
        image_url=None,
        description="All-terrain tyre for SUV",
    ),
    Product(
        id="tire-005",
        name="Pirelli Cinturato P7 225/50 R17",
        category="tire",
        price=5_400.0,
        rating=4.5,
        delivery_days=4,
        partner_id="wildberries",
        image_url=None,
        description="Eco-friendly touring tyre",
    ),
    # Wheels
    Product(
        id="wheel-001",
        name="K&K Fujiyama 6.5x16 5x114.3",
        category="wheel",
        price=4_200.0,
        rating=4.4,
        delivery_days=3,
        partner_id="ozon",
        image_url=None,
        description="Cast alloy wheel, anthracite",
    ),
    Product(
        id="wheel-002",
        name="Replay TY96 7x17 5x114.3",
        category="wheel",
        price=5_800.0,
        rating=4.7,
        delivery_days=5,
        partner_id="wildberries",
        image_url=None,
        description="OEM-style alloy wheel for Toyota",
    ),
    Product(
        id="wheel-003",
        name="SKAD Sakura 6x15 4x100",
        category="wheel",
        price=2_600.0,
        rating=4.0,
        delivery_days=2,
        partner_id="ozon",
        image_url=None,
        description="Economy steel wheel",
    ),
    Product(
        id="wheel-004",
        name="NZ Wheels SH673 7x17 5x120",
        category="wheel",
        price=7_100.0,
        rating=4.6,
        delivery_days=6,
        partner_id="avito",
        image_url=None,
        description="Sport alloy wheel for BMW",
    ),
]
