# ============================================================
# GarageMind AI — Production Dockerfile
# Запуск через Gunicorn с несколькими воркерами
# ============================================================

FROM python:3.11-slim

WORKDIR /app

# Системные зависимости
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Python-зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Код приложения
COPY . .

ENV PYTHONPATH=/app
ENV PORT=8000

EXPOSE 8000

# Gunicorn — production сервер
# Workers = CPU × 2 + 1 (авто)
# Timeout = 30 сек
# Макс 1000 запросов на воркер (защита от утечек)
CMD ["gunicorn", "wsgi:app", \
     "-c", "gunicorn.conf.py", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "4", \
     "--worker-class", "sync", \
     "--timeout", "30", \
     "--graceful-timeout", "30", \
     "--max-requests", "1000", \
     "--max-requests-jitter", "100", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--log-level", "info"]

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1
