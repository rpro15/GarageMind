from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ImagePayload:
    content: bytes
    mime_type: str
    filename: str | None = None
    size: int = 0


@dataclass(frozen=True)
class RecognitionMatch:
    part_name: str
    category: str
    confidence: float

    def to_dict(self) -> dict[str, object]:
        return {
            "part_name": self.part_name,
            "category": self.category,
            "confidence": self.confidence,
        }


@dataclass(frozen=True)
class RecognitionResult:
    part_name: str
    category: str
    confidence: float
    possible_matches: list[RecognitionMatch]
    source: str

    def to_dict(self) -> dict[str, object]:
        return {
            "part_name": self.part_name,
            "category": self.category,
            "confidence": self.confidence,
            "possible_matches": [match.to_dict() for match in self.possible_matches],
            "source": self.source,
        }


@dataclass(frozen=True)
class VinDecoded:
    wmi: str | None
    region: str | None
    manufacturer: str | None
    model_year: int | None
    plant_code: str | None
    serial: str | None

    def to_dict(self) -> dict[str, object]:
        return {
            "wmi": self.wmi,
            "region": self.region,
            "manufacturer": self.manufacturer,
            "model_year": self.model_year,
            "plant_code": self.plant_code,
            "serial": self.serial,
        }


@dataclass(frozen=True)
class Partner:
    id: str
    name: str
    affiliate_enabled: bool
    priority_weight: float  # 0.0–1.0; higher = more preferred in ranking
    base_url: str
    affiliate_tag: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "name": self.name,
            "affiliate_enabled": self.affiliate_enabled,
        }


@dataclass(frozen=True)
class Product:
    id: str
    partner_id: str
    name: str
    category: str  # "tires" | "wheels"
    price: float
    image_url: str | None = None
    description: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "partner_id": self.partner_id,
            "name": self.name,
            "category": self.category,
            "price": self.price,
            "image_url": self.image_url,
            "description": self.description,
        }


@dataclass(frozen=True)
class RecommendationCard:
    product: Product
    partner: Partner
    affiliate_url: str
    score: float
    reason: str

    def to_dict(self) -> dict[str, object]:
        return {
            "product_id": self.product.id,
            "name": self.product.name,
            "category": self.product.category,
            "price": self.product.price,
            "image_url": self.product.image_url,
            "description": self.product.description,
            "partner": self.partner.to_dict(),
            "affiliate_url": self.affiliate_url,
            "score": round(self.score, 4),
            "reason": self.reason,
        }


@dataclass
class ClickEvent:
    product_id: str
    partner_id: str
    affiliate_url: str
    timestamp: str

    def to_dict(self) -> dict[str, object]:
        return {
            "product_id": self.product_id,
            "partner_id": self.partner_id,
            "affiliate_url": self.affiliate_url,
            "timestamp": self.timestamp,
        }


@dataclass(frozen=True)
class VinDecodeResult:
    vin: str
    is_valid: bool
    validation_errors: list[str]
    decoded: VinDecoded

    def to_dict(self) -> dict[str, object]:
        return {
            "vin": self.vin,
            "is_valid": self.is_valid,
            "validation_errors": self.validation_errors,
            "decoded": self.decoded.to_dict(),
        }
