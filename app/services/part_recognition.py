"""
Сервис распознавания автозапчастей по фото.
Пока заглушка — в будущем интеграция с OpenAI Vision / DeepSeek Vision.
"""
from __future__ import annotations

import logging
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class PartRecognitionResult:
    """Результат распознавания детали."""
    success: bool
    part_name: Optional[str] = None
    confidence: float = 0.0
    part_type: Optional[str] = None  # "tire", "wheel", "bolt", "other"
    size_hint: Optional[str] = None
    brand_hint: Optional[str] = None
    error: Optional[str] = None
    raw_data: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "part_name": self.part_name,
            "confidence": self.confidence,
            "part_type": self.part_type,
            "size_hint": self.size_hint,
            "brand_hint": self.brand_hint,
            "error": self.error,
        }


def build_part_recognition_service(settings, logger: logging.Logger):
    """
    Фабрика для создания сервиса распознавания деталей.
    В будущем можно переключать провайдера через settings.PART_RECOGNITION_PROVIDER.
    """
    logger.info("PartRecognitionService initialized (stub mode)")
    return PartRecognitionService(logger=logger)


class PartRecognitionService:
    """
    Определяет тип автозапчасти по изображению.
    
    Текущая реализация:
    - Проверяет MIME-тип и размер изображения
    - Возвращает заглушку (реальное распознавание через AI будет позже)
    """

    def __init__(self, logger: logging.Logger):
        self._logger = logger

    def recognize_upload(
        self,
        image_bytes: bytes,
        declared_mime_type: Optional[str] = None,
        filename: Optional[str] = None,
    ) -> PartRecognitionResult:
        """Распознавание из загруженного файла."""
        self._logger.info(
            "Recognize part from upload: mime=%s, size=%d, filename=%s",
            declared_mime_type,
            len(image_bytes),
            filename,
        )

        # Проверка MIME-типа
        if declared_mime_type and not declared_mime_type.startswith("image/"):
            return PartRecognitionResult(
                success=False,
                error=f"Unsupported file type: {declared_mime_type}. Send an image.",
            )

        # Проверка размера (макс 10MB)
        if len(image_bytes) > 10 * 1024 * 1024:
            return PartRecognitionResult(
                success=False,
                error="Image is too large. Maximum size is 10MB.",
            )

        # Пока возвращаем заглушку
        return PartRecognitionResult(
            success=True,
            part_name="шина (предположительно)",
            confidence=0.65,
            part_type="tire",
            size_hint=None,
            brand_hint=None,
        )

    def recognize_base64(
        self,
        base64_data: Optional[str],
        declared_mime_type: Optional[str] = None,
        filename: Optional[str] = None,
    ) -> PartRecognitionResult:
        """Распознавание из base64-строки."""
        if not base64_data:
            return PartRecognitionResult(
                success=False,
                error="Missing image_base64 in request body.",
            )

        self._logger.info(
            "Recognize part from base64: mime=%s, data_len=%d, filename=%s",
            declared_mime_type,
            len(base64_data),
            filename,
        )

        # Пока возвращаем заглушку
        return PartRecognitionResult(
            success=True,
            part_name="шина (предположительно)",
            confidence=0.65,
            part_type="tire",
            size_hint=None,
            brand_hint=None,
        )
