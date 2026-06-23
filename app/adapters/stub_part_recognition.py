from __future__ import annotations

import hashlib

from app.domain.models import CatalogItem, ImagePayload, RecognitionMatch, RecognitionResult
from app.ports.part_catalog import PartCatalogRepository
from app.ports.part_recognition import PartRecognitionProvider


DEFAULT_PART_CATALOG = (
    CatalogItem(part_name="Brake Pad Set", category="braking"),
    CatalogItem(part_name="Oil Filter", category="engine"),
    CatalogItem(part_name="Shock Absorber", category="suspension"),
    CatalogItem(part_name="Headlight Assembly", category="lighting"),
    CatalogItem(part_name="Radiator Hose", category="cooling"),
    CatalogItem(part_name="Air Filter Housing", category="intake"),
    CatalogItem(part_name="Alternator", category="electrical"),
    CatalogItem(part_name="Wheel Bearing Hub", category="drivetrain"),
)


class StubPartRecognitionProvider(PartRecognitionProvider):
    def __init__(self, catalog_repository: PartCatalogRepository) -> None:
        self._catalog_repository = catalog_repository

    def recognize(self, image: ImagePayload) -> RecognitionResult:
        catalog_items = self._catalog_repository.list_items() or list(DEFAULT_PART_CATALOG)
        digest = hashlib.sha256(image.content).digest()
        base_index = digest[0] % len(catalog_items)

        matches: list[RecognitionMatch] = []
        for offset in range(3):
            catalog_item = catalog_items[(base_index + offset) % len(catalog_items)]
            if offset == 0:
                confidence = round(0.62 + (digest[1] / 255) * 0.33, 2)
            else:
                confidence = round(0.58 - (offset * 0.12) - ((digest[offset + 1] % 6) / 100), 2)
            matches.append(
                RecognitionMatch(
                    part_name=catalog_item.part_name,
                    category=catalog_item.category,
                    confidence=max(confidence, 0.22),
                )
            )

        primary = matches[0]
        return RecognitionResult(
            part_name=primary.part_name,
            category=primary.category,
            confidence=primary.confidence,
            possible_matches=matches,
            source="stub",
        )
