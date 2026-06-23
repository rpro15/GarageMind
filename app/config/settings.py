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


@dataclass(frozen=True)
class Settings:
    max_image_bytes: int = 5 * 1024 * 1024
    allowed_image_mime_types: tuple[str, ...] = DEFAULT_ALLOWED_IMAGE_MIME_TYPES
    recognition_provider: str = "stub"
    log_level: str = "INFO"

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
        )

load_dotenv()

class Settings:
    # Существующие переменные (оставляем как есть)
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
    MAX_IMAGE_BYTES = int(os.getenv("MAX_IMAGE_BYTES", 5242880))
    ALLOWED_IMAGE_MIME_TYPES = os.getenv("ALLOWED_IMAGE_MIME_TYPES", 
                                          "image/jpeg,image/png,image/webp,image/gif,image/bmp").split(',')
    PART_RECOGNITION_PROVIDER = os.getenv("PART_RECOGNITION_PROVIDER", "stub")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # НОВЫЕ ПЕРЕМЕННЫЕ (добавить)
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    MINIAPP_URL = os.getenv("MINIAPP_URL", "https://localhost/miniapp/")

settings = Settings()