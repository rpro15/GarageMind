from __future__ import annotations

import os
from dataclasses import dataclass


DEFAULT_ALLOWED_IMAGE_MIME_TYPES = (
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif",
    "image/bmp",
)


def _read_int(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default

    try:
        value = int(raw_value)
    except ValueError:
        return default

    return value if value > 0 else default


DEFAULT_DATABASE_PATH = "garagemind.db"


@dataclass(frozen=True)
class Settings:
    max_image_bytes: int = 5 * 1024 * 1024
    allowed_image_mime_types: tuple[str, ...] = DEFAULT_ALLOWED_IMAGE_MIME_TYPES
    recognition_provider: str = "stub"
    log_level: str = "INFO"
    database_path: str = DEFAULT_DATABASE_PATH

    @classmethod
    def from_env(cls) -> "Settings":
        raw_mime_types = os.getenv(
            "ALLOWED_IMAGE_MIME_TYPES",
            ",".join(DEFAULT_ALLOWED_IMAGE_MIME_TYPES),
        )
        mime_types = tuple(
            mime_type.strip().lower()
            for mime_type in raw_mime_types.split(",")
            if mime_type.strip()
        )

        return cls(
            max_image_bytes=_read_int("MAX_IMAGE_BYTES", 5 * 1024 * 1024),
            allowed_image_mime_types=mime_types or DEFAULT_ALLOWED_IMAGE_MIME_TYPES,
            recognition_provider=os.getenv("PART_RECOGNITION_PROVIDER", "stub").strip().lower() or "stub",
            log_level=os.getenv("LOG_LEVEL", "INFO").strip().upper() or "INFO",
            database_path=os.getenv("DATABASE_PATH", DEFAULT_DATABASE_PATH).strip() or DEFAULT_DATABASE_PATH,
        )
