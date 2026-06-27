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
    MINIAPP_URL = os.getenv("MINIAPP_URL", "http://localhost:8000/miniapp/")


settings = Settings()