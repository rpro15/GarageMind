from __future__ import annotations

import hashlib

from app.domain.models import ImagePayload, RecognitionMatch, RecognitionResult
from app.ports.part_recognition import PartRecognitionProvider


PART_CATALOG = (
    {"part_name": "Brake Pad Set", "category": "braking"},
    {"part_name": "Oil Filter", "category": "engine"},
    {"part_name": "Shock Absorber", "category": "suspension"},
    {"part_name": "Headlight Assembly", "category": "lighting"},
    {"part_name": "Radiator Hose", "category": "cooling"},
    {"part_name": "Air Filter Housing", "category": "intake"},
    {"part_name": "Alternator", "category": "electrical"},
    {"part_name": "Wheel Bearing Hub", "category": "drivetrain"},
)


class StubPartRecognitionProvider(PartRecognitionProvider):
    def recognize(self, image: ImagePayload) -> RecognitionResult:
        digest = hashlib.sha256(image.content).digest()
        base_index = digest[0] % len(PART_CATALOG)

        matches: list[RecognitionMatch] = []
        for offset in range(3):
            catalog_item = PART_CATALOG[(base_index + offset) % len(PART_CATALOG)]
            if offset == 0:
                confidence = round(0.62 + (digest[1] / 255) * 0.33, 2)
            else:
                confidence = round(0.58 - (offset * 0.12) - ((digest[offset + 1] % 6) / 100), 2)
            matches.append(
                RecognitionMatch(
                    part_name=catalog_item["part_name"],
                    category=catalog_item["category"],
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
