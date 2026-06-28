"""
Мониторинг и метрики для Авто Эксперт AI.

Предоставляет:
- Prometheus метрики (latency, request count, errors)
- Request ID middleware
- Структурированное логирование
"""

import uuid
import time
import logging

from flask import g, request, jsonify
from prometheus_flask_exporter import PrometheusMetrics
from prometheus_client.registry import CollectorRegistry

logger = logging.getLogger(__name__)

# Отдельный реестр Prometheus — чтобы не было Duplicated timeseries
# при повторных create_app() в тестах
_registry = CollectorRegistry()
_metrics_instance: PrometheusMetrics | None = None


def setup_monitoring(app):
    """
    Настраивает мониторинг для Flask приложения.

    Метрики создаются только 1 раз (singleton). При повторных вызовах
    (например, в тестах) просто возвращаем существующий инстанс.
    """
    global _metrics_instance

    if _metrics_instance is None:
        _metrics_instance = PrometheusMetrics(
            app,
            group_by='endpoint',
            path='/metrics',
            registry=_registry,
        )
        _metrics_instance.summary(
            'request_errors_by_type',
            'Request errors grouped by error type',
            labels={'error_type': lambda: g.get('error_type', 'unknown')}
        )

    # Request ID middleware
    _setup_request_id_middleware(app)
    _setup_error_handlers(app)

    return _metrics_instance


def _setup_request_id_middleware(app):
    """Добавляет X-Request-Id и логирование запросов."""

    @app.before_request
    def before_request():
        g.request_id = request.headers.get('X-Request-Id', str(uuid.uuid4())[:8])
        g.start_time = time.time()
        g.error_type = 'none'

    @app.after_request
    def after_request(response):
        response.headers['X-Request-Id'] = g.get('request_id', '')
        duration = time.time() - g.get('start_time', time.time())
        logger.info(
            "request completed",
            extra={
                'request_id': g.get('request_id', ''),
                'method': request.method,
                'path': request.path,
                'status': response.status_code,
                'duration_ms': round(duration * 1000, 2),
            }
        )
        return response


def _setup_error_handlers(app):
    """Кастомные обработчики ошибок."""

    @app.errorhandler(404)
    def not_found(e):
        g.error_type = 'not_found'
        return jsonify({
            "error": {
                "code": "not_found",
                "message": "The requested URL was not found.",
                "request_id": g.get('request_id', ''),
            }
        }), 404

    @app.errorhandler(500)
    def internal_error(e):
        g.error_type = 'internal'
        logger.exception("Internal server error")
        return jsonify({
            "error": {
                "code": "internal_error",
                "message": "An internal error occurred.",
                "request_id": g.get('request_id', ''),
            }
        }), 500


class RequestMetrics:
    """
    Контекстный менеджер для замера времени выполнения операций.
    """

    def __init__(self, operation_name):
        self.operation_name = operation_name
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        status = 'error' if exc_type else 'success'
        logger.info(
            "operation completed",
            extra={
                'operation': self.operation_name,
                'duration_ms': round(duration * 1000, 2),
                'status': status,
                'request_id': g.get('request_id', ''),
            }
        )
