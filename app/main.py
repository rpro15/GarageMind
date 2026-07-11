import os
import asyncio
import logging
import threading

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from limits.storage import MemoryStorage, RedisStorage

from app.api.errors import register_error_handlers
from app.api.routes import api_blueprint
from app.config.settings import settings
from app.services.part_recognition import build_part_recognition_service
from app.services.vin_decoder import VinDecoderService
from app.adapters.deepseek_client import DeepSeekClient
from app.adapters.partner_api import MockPartnerCatalog
from app.services.tire_recomendation import TireRecommendationService
from app.services.knowledge.auto_collector import AutoCollector
from app.services.cache import get_cache
from app.services.user_history import run_migration as run_user_history_migration
from app.monitoring.metrics import setup_monitoring
from app.api.admitad import admitad_blueprint
from app.services.sources import MultiSourceProductService
from app.services.sources.wildberries_source import WildberriesSource
from app.services.sources.partner_source import PartnerSource
from app.services.rag import EmbeddingService, VectorStore, Retriever

# Структурированное логирование
try:
    import structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer()
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
except ImportError:
    pass

logging.basicConfig(
    level=settings.LOG_LEVEL,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


def create_app() -> Flask:
    # Flask со статикой для Mini App
    app = Flask(__name__)
    app.config['SECRET_KEY'] = settings.SECRET_KEY
    CORS(app)

    MINIAPP_STATIC = os.path.join(app.root_path, 'miniapp', 'static')

    # Rate Limiting (memory by default, Redis если доступен)
    limiter_storage = "memory://"
    try:
        if settings.REDIS_URL and 'redis' in settings.REDIS_URL:
            import redis as redis_lib
            r = redis_lib.from_url(settings.REDIS_URL)
            r.ping()
            limiter_storage = settings.REDIS_URL
            logger.info("🚦 Rate limiter: Redis storage")
        else:
            logger.info("🚦 Rate limiter: memory storage")
    except Exception:
        logger.info("🚦 Rate limiter: memory storage (fallback)")

    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"],
        storage_uri=limiter_storage,
    )
    limiter.init_app(app)

    # Настройка мониторинга (Prometheus метрики + request ID + structured logs)
    metrics = setup_monitoring(app)

    # Healthcheck на корню (для Docker)
    @app.route('/health', methods=['GET'])
    def health():
        return jsonify({"status": "ok", "service": "avto-expert-ai"}), 200

    # Mini App: отдаём index.html по /miniapp/
    @app.route('/miniapp/')
    @app.route('/miniapp/<path:filename>')
    def miniapp_static(filename='index.html'):
        return send_from_directory(
            os.path.join(app.root_path, 'miniapp', 'static'),
            filename
        )

    # Регистрация blueprint'ов
    app.register_blueprint(api_blueprint)
    app.register_blueprint(admitad_blueprint)
    register_error_handlers(app)

    # Инициализация сервисов
    part_service = build_part_recognition_service(settings, logger)
    vin_service = VinDecoderService(logger)
    llm_client = DeepSeekClient()

    # MultiSourceProductService — реальный поиск по всем источникам
    catalog = MultiSourceProductService()
    catalog.register_source(PartnerSource(
        client_id=settings.ADMITAD_CLIENT_ID or None,
        client_secret=settings.ADMITAD_CLIENT_SECRET or None,
    ))
    catalog.register_source(WildberriesSource(
        api_key=settings.WILDBERRIES_API_KEY or None,
    ))
    logger.info("🏪 MultiSourceProductService: Admitad + Wildberries + fallback")

    # RAG: векторный поиск по каталогу шин
    embedding_service = EmbeddingService()
    vector_store = VectorStore()
    retriever = Retriever(embedding_service, vector_store)
    logger.info("🧠 RAG retriever initialized")

    tire_service = TireRecommendationService(llm_client, catalog, retriever=retriever)

    # Инициализация кэша (Redis)
    cache = get_cache()
    logger.info("🧠 Cache service initialized (Redis: %s)", "available" if cache._available else "not available (fallback to no-cache)")

    # Миграция таблиц персонализации
    try:
        run_user_history_migration()
        logger.info("✅ User history migration completed")
    except Exception as e:
        logger.warning("User history migration failed: %s", e)

    app.extensions["services"] = {
        "part_recognition": part_service,
        "vin_decoder": vin_service,
        "tire_recommendation": tire_service,
        "cache": cache,
        "llm_client": llm_client,
    }

    return app


def main():
    app = create_app()

    # Бота запускаем только если есть токен
    if settings.BOT_TOKEN:
        logger.info("BOT_TOKEN is set — bot can be started separately")
        logger.info("Run: python -m app.bot.dispatcher")
    else:
        logger.info("BOT_TOKEN not set — bot disabled (ok for local dev)")

    # Фоновый сборщик знаний (каждый час, лимит 100 отзывов в день)
    collector = AutoCollector()
    collector_thread = threading.Thread(
        target=lambda: asyncio.run(
            collector.run_daemon(interval_minutes=settings.AUTO_COLLECTOR_INTERVAL_MINUTES)
        ),
        daemon=True,
        name="auto_collector",
    )
    collector_thread.start()
    logger.info(
        "🧠 AutoCollector started (interval=%d min, daily_limit=%d)",
        settings.AUTO_COLLECTOR_INTERVAL_MINUTES,
        settings.COLLECTOR_DAILY_LIMIT,
    )

    port = int(os.environ.get("PORT", 8000))
    logger.info("🚀 Starting Flask server on 0.0.0.0:%s", port)
    app.run(host='0.0.0.0', port=port, debug=False)


if __name__ == "__main__":
    main()
