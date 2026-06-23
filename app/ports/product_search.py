from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.models import ProductRecommendation, RecommendRequest


class ProductSearchProvider(ABC):
    @abstractmethod
    def search(self, request: RecommendRequest) -> list[ProductRecommendation]:
        raise NotImplementedError
