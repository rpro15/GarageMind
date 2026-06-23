from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Partner:
    """A partner in the affiliate network."""

    id: str
    name: str
    affiliate_weight: float  # 0.0–1.0; higher = preferred in ranking
    url_template: str | None = None  # e.g. "https://example.com/p/{product_id}?ref=garagemind"
    has_agreement: bool = False

    def build_url(self, product_id: str) -> str | None:
        if self.url_template is None:
            return None
        return self.url_template.format(product_id=product_id)


@dataclass(frozen=True)
class Product:
    """A tire or wheel product offered by a partner."""

    id: str
    name: str
    category: str  # "tire" | "wheel"
    price: float
    rating: float  # 0.0–5.0
    delivery_days: int
    partner_id: str
    image_url: str | None = None
    description: str | None = None


@dataclass(frozen=True)
class Recommendation:
    """A ranked product recommendation with an affiliate link."""

    product: Product
    partner: Partner
    score: float
    affiliate_url: str | None
    reason: str

    def to_dict(self) -> dict[str, object]:
        return {
            "product_id": self.product.id,
            "name": self.product.name,
            "category": self.product.category,
            "price": self.product.price,
            "rating": self.product.rating,
            "delivery_days": self.product.delivery_days,
            "image_url": self.product.image_url,
            "description": self.product.description,
            "partner": self.partner.name,
            "partner_id": self.partner.id,
            "score": round(self.score, 4),
            "affiliate_url": self.affiliate_url,
            "reason": self.reason,
        }


@dataclass
class ClickEvent:
    """Records a user click on an affiliate recommendation."""

    product_id: str
    partner_id: str
    timestamp: str
    session_id: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "product_id": self.product_id,
            "partner_id": self.partner_id,
            "timestamp": self.timestamp,
            "session_id": self.session_id,
        }
