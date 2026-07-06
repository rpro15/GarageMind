import os
from dotenv import load_dotenv

load_dotenv()

DEFAULT_ALLOWED_IMAGE_MIME_TYPES = [
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif",
    "image/bmp",
]


class Settings:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
    MAX_IMAGE_BYTES = int(os.getenv("MAX_IMAGE_BYTES", 5242880))
    ALLOWED_IMAGE_MIME_TYPES = os.getenv("ALLOWED_IMAGE_MIME_TYPES",
                                          ",".join(DEFAULT_ALLOWED_IMAGE_MIME_TYPES)).split(",")
    PART_RECOGNITION_PROVIDER = os.getenv("PART_RECOGNITION_PROVIDER", "stub")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Кэш
    CACHE_TTL_BRANDS = int(os.getenv("CACHE_TTL_BRANDS", "3600"))           # 1 час
    CACHE_TTL_MODELS = int(os.getenv("CACHE_TTL_MODELS", "3600"))           # 1 час
    CACHE_TTL_RECOMMEND = int(os.getenv("CACHE_TTL_RECOMMEND", "600"))      # 10 минут
    CACHE_TTL_API_RESPONSE = int(os.getenv("CACHE_TTL_API_RESPONSE", "300"))  # 5 минут

    # Автосборщик знаний
    AUTO_COLLECTOR_INTERVAL_MINUTES = int(os.getenv("AUTO_COLLECTOR_INTERVAL_MINUTES", "60"))
    AUTO_COLLECTOR_REVIEWS_PER_CYCLE = int(os.getenv("AUTO_COLLECTOR_REVIEWS_PER_CYCLE", "10"))
    COLLECTOR_DAILY_LIMIT = int(os.getenv("COLLECTOR_DAILY_LIMIT", "100"))

    MINIAPP_URL = os.getenv("MINIAPP_URL", "http://localhost:8000/miniapp/")


settings = Settings()
