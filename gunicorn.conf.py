"""
Gunicorn configuration for production.

Запуск:
    gunicorn wsgi:app -c gunicorn.conf.py

Для 10 000+ пользователей увеличьте workers до 8-12.
"""
import multiprocessing
import os

# === Основные настройки ===

# Количество воркеров = CPU × 2 + 1
# На типичном сервере (2-4 ядра) это 4-9 воркеров
workers = int(os.environ.get("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2 + 1))

# Тип воркеров — sync (для Flask) или uvicorn (для async)
worker_class = os.environ.get("GUNICORN_WORKER_CLASS", "sync")

# Таймауты
timeout = int(os.environ.get("GUNICORN_TIMEOUT", 30))          # максимум 30 сек на запрос
graceful_timeout = int(os.environ.get("GUNICORN_GRACEFUL_TIMEOUT", 30))

# Количество соединений (для sync воркеров не используется,
# но для gevent/uvicorn важно)
worker_connections = 1000

# === Сеть ===

bind = os.environ.get("GUNICORN_BIND", "0.0.0.0:8000")

# === Логирование ===

accesslog = os.environ.get("GUNICORN_ACCESS_LOG", "-")  # stdout
errorlog = os.environ.get("GUNICORN_ERROR_LOG", "-")    # stderr
loglevel = os.environ.get("GUNICORN_LOG_LEVEL", "info")

# === Перезагрузка (только для разработки) ===

reload = os.environ.get("GUNICORN_RELOAD", "false").lower() == "true"

# === Максимальное количество запросов до перезапуска воркера ===
# Защита от утечки памяти
max_requests = int(os.environ.get("GUNICORN_MAX_REQUESTS", 1000))
max_requests_jitter = int(os.environ.get("GUNICORN_MAX_REQUESTS_JITTER", 100))

# === Надёжность ===

# Перезапускать воркеры, если они упали
preload_app = True

# Daemon (запуск в фоне — обычно не нужно в Docker)
daemon = False

# PID файл
pidfile = os.environ.get("GUNICORN_PIDFILE", "/tmp/gunicorn.pid")

# === Метрики ===

# Статистика в логах
statsd_host = os.environ.get("GUNICORN_STATSD_HOST", None)

# === Обработчики ===

def on_starting(server):
    """Логируем запуск с количеством воркеров."""
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("gunicorn")
    logger.info(
        "🚀 Gunicorn starting: %d workers, bind=%s, worker_class=%s",
        server.cfg.workers,
        server.cfg.bind,
        server.cfg.worker_class,
    )


def on_exit(server):
    """Логируем остановку."""
    import logging
    logger = logging.getLogger("gunicorn")
    logger.info("🛑 Gunicorn shutting down")
