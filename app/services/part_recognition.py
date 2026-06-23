from __future__ import annotations

import base64
import binascii
import logging
import os

from app.adapters.stub_part_recognition import StubPartRecognitionProvider
from app.api.errors import ApiError
from app.config.settings import Settings
from app.domain.models import ImagePayload, RecognitionResult
from app.ports.part_recognition import PartRecognitionProvider


def sniff_image_mime_type(image_bytes: bytes) -> str | None:
    if image_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if image_bytes.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if image_bytes.startswith((b"GIF87a", b"GIF89a")):
        return "image/gif"
    if image_bytes.startswith(b"BM"):
        return "image/bmp"
    if len(image_bytes) >= 12 and image_bytes.startswith(b"RIFF") and image_bytes[8:12] == b"WEBP":
        return "image/webp"
    return None


class PartRecognitionService:
    def __init__(
        self,
        provider: PartRecognitionProvider,
        settings: Settings,
        logger: logging.Logger,
    ) -> None:
        self._provider = provider
        self._settings = settings
        self._logger = logger

    def recognize_upload(
        self,
        image_bytes: bytes,
        *,
        declared_mime_type: str | None,
        filename: str | None,
    ) -> RecognitionResult:
        return self._recognize(
            image_bytes=image_bytes,
            declared_mime_type=declared_mime_type,
            filename=filename,
        )

    def recognize_base64(
        self,
        encoded_image: str | None,
        *,
        declared_mime_type: str | None = None,
        filename: str | None = None,
    ) -> RecognitionResult:
        if not encoded_image or not isinstance(encoded_image, str):
            raise ApiError(
                code="missing_image_payload",
                message="image_base64 is required.",
                status_code=400,
            )

        payload = encoded_image.strip()
        if payload.startswith("data:"):
            header, separator, raw_data = payload.partition(",")
            if not separator or ";base64" not in header:
                raise ApiError(
                    code="invalid_base64_image",
                    message="Data URI image payload must contain a base64 body.",
                    status_code=400,
                )
            declared_mime_type = declared_mime_type or header[5:].split(";", maxsplit=1)[0]
            payload = raw_data

        try:
            image_bytes = base64.b64decode(payload, validate=True)
        except (ValueError, binascii.Error) as exc:
            raise ApiError(
                code="invalid_base64_image",
                message="image_base64 must be a valid base64-encoded string.",
                status_code=400,
            ) from exc

        return self._recognize(
            image_bytes=image_bytes,
            declared_mime_type=declared_mime_type,
            filename=filename,
        )

    def _recognize(
        self,
        *,
        image_bytes: bytes,
        declared_mime_type: str | None,
        filename: str | None,
    ) -> RecognitionResult:
        if not image_bytes:
            raise ApiError(
                code="empty_image_payload",
                message="Image payload must not be empty.",
                status_code=400,
            )

        payload_size = len(image_bytes)
        if payload_size > self._settings.max_image_bytes:
            raise ApiError(
                code="image_too_large",
                message="Image payload exceeds the configured size limit.",
                status_code=413,
                details={"max_image_bytes": self._settings.max_image_bytes},
            )

        normalized_mime_type = (declared_mime_type or "").split(";", maxsplit=1)[0].strip().lower()
        if normalized_mime_type and normalized_mime_type not in self._settings.allowed_image_mime_types:
            raise ApiError(
                code="unsupported_media_type",
                message="Declared image content type is not allowed.",
                status_code=415,
                details={"allowed_mime_types": list(self._settings.allowed_image_mime_types)},
            )

        sniffed_mime_type = sniff_image_mime_type(image_bytes)
        if sniffed_mime_type is None:
            raise ApiError(
                code="invalid_image_payload",
                message="Unable to identify a supported image format from the payload.",
                status_code=422,
            )

        if sniffed_mime_type not in self._settings.allowed_image_mime_types:
            raise ApiError(
                code="unsupported_media_type",
                message="Detected image format is not allowed.",
                status_code=415,
                details={"allowed_mime_types": list(self._settings.allowed_image_mime_types)},
            )

        if normalized_mime_type and normalized_mime_type != sniffed_mime_type:
            raise ApiError(
                code="image_mime_mismatch",
                message="Declared image content type does not match the uploaded file.",
                status_code=422,
                details={
                    "declared_mime_type": normalized_mime_type,
                    "detected_mime_type": sniffed_mime_type,
                },
            )

        safe_filename = os.path.basename(filename) if filename else None
        self._logger.debug(
            "Recognizing part via provider=%s mime=%s size=%s filename=%s",
            self._settings.recognition_provider,
            sniffed_mime_type,
            payload_size,
            safe_filename,
        )

        return self._provider.recognize(
            ImagePayload(
                content=image_bytes,
                mime_type=sniffed_mime_type,
                filename=safe_filename,
                size=payload_size,
            )
        )


def build_part_recognition_service(settings: Settings, logger: logging.Logger) -> PartRecognitionService:
    provider: PartRecognitionProvider
    if settings.recognition_provider == "stub":
        provider = StubPartRecognitionProvider()
    else:
        logger.warning(
            "Unsupported part recognition provider '%s'; falling back to stub provider.",
            settings.recognition_provider,
        )
        provider = StubPartRecognitionProvider()

    return PartRecognitionService(provider=provider, settings=settings, logger=logger)
