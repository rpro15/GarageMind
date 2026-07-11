# ============================================================
# GarageMind AI — Production Dockerfile
# Запуск через Gunicorn с несколькими воркерами
# ============================================================

FROM python:3.11-slim AS builder

WORKDIR /app

# Системные зависимости для сборки
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ============================================================
# Финальный образ
# ============================================================
FROM python:3.11-slim

WORKDIR /app

# Копируем только установленные пакеты из builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Системные зависимости
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates && \
    rm -rf /var/lib/apt/lists/* && \
    addgroup --system app && \
    adduser --system --ingroup app app

# Код приложения
COPY --chown=app:app . .

ENV PYTHONPATH=/app
ENV PORT=8000

EXPOSE 8000

USER app

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

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
