from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.models import CatalogItem


class PartCatalogRepository(ABC):
    @abstractmethod
    def ensure_schema(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def list_items(self) -> list[CatalogItem]:
        raise NotImplementedError

    @abstractmethod
    def seed_if_empty(self, items: tuple[CatalogItem, ...]) -> None:
        raise NotImplementedError
