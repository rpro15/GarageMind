from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.models import CatalogPart


class CatalogRepository(ABC):
    @abstractmethod
    def list_parts(self) -> list[CatalogPart]:
        raise NotImplementedError

    @abstractmethod
    def get_part(self, part_id: int) -> CatalogPart | None:
        raise NotImplementedError

    @abstractmethod
    def count(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def add_part(self, part_name: str, category: str) -> CatalogPart:
        raise NotImplementedError
