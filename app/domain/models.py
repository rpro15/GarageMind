from __future__ import annotations

from dataclasses import dataclass

from typing import List, Optional
from enum import Enum


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

class DrivingStyle(str, Enum):
    COMFORT = "comfort"
    SPORT = "sport"
    ECONOMY = "economy"

class Season(str, Enum):
    SUMMER = "summer"
    WINTER = "winter"
    ALL_SEASON = "all_season"

@dataclass
class TireRequest:
    brand: str
    model: str
    year: int
    driving_style: DrivingStyle
    budget: Optional[int] = None
    season: Optional[Season] = None

@dataclass
class Product:
    id: str
    name: str
    price: float
    currency: str = "RUB"
    image_url: Optional[str] = None
    partner_link: Optional[str] = None
    source: str  # 'ozon', 'wb', 'yandex', etc.

@dataclass
class RecommendationResult:
    advice: str  # текст от DeepSeek
    products: List[Product]
    request: TireRequest