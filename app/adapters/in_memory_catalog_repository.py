from __future__ import annotations

from datetime import datetime, timezone

from app.domain.models import CatalogPart
from app.ports.catalog_repository import CatalogRepository


class InMemoryCatalogRepository(CatalogRepository):
    """Volatile in-memory catalog repository intended for unit tests.

    All data lives in a plain Python list and is discarded when the object is
    garbage-collected.  It is **not** thread-safe; use
    :class:`SqliteCatalogRepository` in production.
    """

    def __init__(self) -> None:
        self._parts: list[CatalogPart] = []
        self._next_id: int = 1

    def list_parts(self) -> list[CatalogPart]:
        return list(self._parts)

    def get_part(self, part_id: int) -> CatalogPart | None:
        return next((p for p in self._parts if p.id == part_id), None)

    def count(self) -> int:
        return len(self._parts)

    def add_part(self, part_name: str, category: str) -> CatalogPart:
        now = datetime.now(tz=timezone.utc).isoformat()
        part = CatalogPart(
            id=self._next_id,
            part_name=part_name,
            category=category,
            created_at=now,
        )
        self._parts.append(part)
        self._next_id += 1
        return part
