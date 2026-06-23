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

DEFAULT_PARTNER_MARKETPLACES = ("ozon", "wildberries", "admitad", "yandex_market")


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
    product_search_provider: str = "stub"
    partner_marketplaces: tuple[str, ...] = DEFAULT_PARTNER_MARKETPLACES
    log_level: str = "INFO"
    db_path: str = "garagemind.db"
    redis_url: str | None = None
    deepseek_api_key: str | None = None
    deepseek_partner_id: str = "GARAGEMIND"

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

        raw_partners = os.getenv(
            "PARTNER_MARKETPLACES",
            ",".join(DEFAULT_PARTNER_MARKETPLACES),
        )
        partner_marketplaces = tuple(
            p.strip().lower()
            for p in raw_partners.split(",")
            if p.strip()
        )

        return cls(
            max_image_bytes=_read_int("MAX_IMAGE_BYTES", 5 * 1024 * 1024),
            allowed_image_mime_types=mime_types or DEFAULT_ALLOWED_IMAGE_MIME_TYPES,
            recognition_provider=os.getenv("PART_RECOGNITION_PROVIDER", "stub").strip().lower() or "stub",
            product_search_provider=os.getenv("PRODUCT_SEARCH_PROVIDER", "stub").strip().lower() or "stub",
            partner_marketplaces=partner_marketplaces or DEFAULT_PARTNER_MARKETPLACES,
            log_level=os.getenv("LOG_LEVEL", "INFO").strip().upper() or "INFO",
            db_path=os.getenv("DB_PATH", "garagemind.db"),
            redis_url=os.getenv("REDIS_URL") or None,
            deepseek_api_key=os.getenv("DEEPSEEK_API_KEY") or None,
            deepseek_partner_id=os.getenv("DEEPSEEK_PARTNER_ID", "GARAGEMIND"),
        )
