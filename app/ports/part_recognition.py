from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.models import ImagePayload, RecognitionResult


class PartRecognitionProvider(ABC):
    @abstractmethod
    def recognize(self, image: ImagePayload) -> RecognitionResult:
        raise NotImplementedError
