from __future__ import annotations

from dataclasses import dataclass


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
class CatalogPart:
    id: int
    part_name: str
    category: str
    created_at: str

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "part_name": self.part_name,
            "category": self.category,
            "created_at": self.created_at,
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
