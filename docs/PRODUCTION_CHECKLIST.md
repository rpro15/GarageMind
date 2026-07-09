# 🚀 Production Checklist — GarageMind AI

> Что нужно для 10 000+ пользователей без тормозов

---

## 1️⃣ Критично — сделать СЕЙЧАС

### 🏎️ Производительность

- [ ] **Rate Limiting**: `pip install flask-limiter` + ограничить `/api/recommend_tires` до 10/min
- [ ] **Timeout для DeepSeek**: `requests.post(timeout=10)` — чтобы не висли
- [ ] **Connection Pooling**: заменить `requests` на `requests.Session()`
- [ ] **Асинхронность**: перевести Flask → Quart (async) или FastAPI
- [ ] **Очередь**: Celery + Redis для тяжёлых задач (парсинг, генерация)

### 🧪 Тесты

```bash
pip install pytest pytest-cov pytest-mock
```

- [ ] `tests/test_api.py` — тест эндпоинтов с моком DeepSeek
- [ ] `tests/test_cache.py` — тест Redis-кэша
- [ ] `tests/test_rag.py` — тест ChromaDB
- [ ] `tests/conftest.py` — фикстуры + моки

### 🔒 Безопасность

- [ ] **CORS**: `pip install flask-cors` + настроить для домена
- [ ] **Защита .env**: `.env` в `.gitignore` — ✅ есть
- [ ] **Валидация**: Pydantic модели на входящие запросы
- [ ] **HTTPS форсинг**: Nginx → редирект HTTP→HTTPS

---

## 2️⃣ Мониторинг

- [ ] **Prometheus**: добавить `flask_prometheus_metrics`
- [ ] **Grafana дашборд**: CPU, RAM, RPS, latency, cache hit ratio
- [ ] **Sentry**: `pip install sentry-sdk` — отлавливать ошибки
- [ ] **Uptime Kuma** / **Betterstack** — мониторинг здоровья
- [ ] **Логи в файл**: настроить `logging.handlers.RotatingFileHandler`

---

## 3️⃣ CI/CD

Создать `.github/workflows/deploy.yml`:

```yaml
name: CI/CD
on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: pip install -r requirements.txt
      - run: pytest tests/ --cov=app

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to server
        uses: appleboy/ssh-action@v1
        with:
          host: ${{ secrets.HOST }}
          username: ${{ secrets.USER }}
          key: ${{ secrets.SSH_KEY }}
          script: |
            cd /opt/garage-mind
            git pull origin main
            docker compose down
            docker compose up --build -d
            docker system prune -f
```

---

## 4️⃣ База данных

- [ ] **Alembic** миграции: `pip install alembic`
- [ ] **Бекап SQLite**: cron-задача на копирование data/*.sqlite
- [ ] **Репликация Redis**: Redis Sentinel для отказоустойчивости
- [ ] **Индексы SQLite**: `CREATE INDEX idx_products_category ON products(category)`

---

## 5️⃣ Деплой-инфраструктура

```text
┌─────────────────────────────────────────────────┐
│                  Cloudflare DNS                  │
│              (rpro.su → IP сервера)              │
└─────────────────────┬───────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────┐
│               Nginx (reverse proxy)               │
│    - HTTP → HTTPS redirect                       │
│    - Rate limiting: limit_req_zone               │
│    - Compression: gzip                           │
│    - Static cache: /miniapp/static/              │
└─────────────────────┬───────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────┐
│              Docker Compose                       │
│                                                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │
│  │  Flask   │  │  Redis   │  │ ChromaDB      │   │
│  │  (×2-4)  │  │  (cache) │  │ (векторная БД) │   │
│  └──────────┘  └──────────┘  └──────────────┘   │
│                                                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │
│  │ Celery   │  │ SQLite   │  │ Prometheus    │   │
│  │ (фоновые)│  │ (знания)  │  │ + Grafana    │   │
│  └──────────┘  └──────────┘  └──────────────┘   │
└─────────────────────────────────────────────────┘
```

### Скрипт быстрого развёртывания

```bash
#!/bin/bash
# deploy.sh — полный деплой одной командой

echo "🚀 Деплой GarageMind..."

# 1. Обновить код
git pull origin main

# 2. Создать бекап
mkdir -p backups/$(date +%Y-%m-%d)
cp data/*.sqlite backups/$(date +%Y-%m-%d)/ 2>/dev/null || true

# 3. Собрать и запустить
docker compose down
docker compose up --build -d

# 4. Применить миграции
docker compose exec api python -m alembic upgrade head

# 5. Прогреть кэш
curl -s https://rpro.su/api/brands > /dev/null
curl -s https://rpro.su/health > /dev/null

# 6. Очистить старые образы
docker system prune -f

echo "✅ Деплой завершён"
```

---

## 📊 Метрики для Grafana (основные)

| Метрика | Описание | Алерт если |
|:--------|:---------|:-----------|
| `http_requests_total` | Всего запросов | > 1000/мин |
| `http_request_duration_seconds` | Время ответа | > 5 сек |
| `deepseek_api_latency` | Задержка DeepSeek | > 3 сек |
| `redis_cache_hit_ratio` | % попаданий в кэш | < 60% |
| `celery_queue_size` | Размер очереди | > 100 |
| `memory_usage_percent` | Использование RAM | > 80% |

---

## 📝 Пример .env для продакшна

```ini
# GarageMind — Production
SECRET_KEY=$(openssl rand -hex 32)
LOG_LEVEL=WARNING

BOT_TOKEN=your_bot_token

DEEPSEEK_API_KEY=sk-your-key
DEEPSEEK_MODEL=deepseek-chat

REDIS_URL=redis://redis:6379/0

CACHE_TTL_RECOMMEND=600
CACHE_TTL_BRANDS=3600
CACHE_TTL_MODELS=3600

COLLECTOR_DAILY_LIMIT=100
AUTO_COLLECTOR_INTERVAL_MINUTES=60
AUTO_COLLECTOR_REVIEWS_PER_CYCLE=10

ADMITAD_CLIENT_ID=your_id
ADMITAD_CLIENT_SECRET=your_secret
WILDBERRIES_API_KEY=your_key

GARAGE_MIND_DB_PATH=/app/data/garage_mind.sqlite
MINIAPP_URL=https://rpro.su/miniapp/

# Мониторинг
SENTRY_DSN=https://xxx@sentry.io/xxx
PROMETHEUS_ENABLED=true
```

---

## ⚡ Сколько выдержит текущая архитектура?

| Компонент | Текущий лимит | Узкое место |
|:----------|:-------------:|:------------|
| **Flask** (1 воркер) | ~100 RPS | Gunicorn workers = 1 |
| **Flask** (gunicorn ×4) | ~400 RPS | ✅ Легко фиксится |
| **Redis** | ~100 000 RPS | ✅ OK |
| **SQLite** | ~50 000 RPS | ✅ OK для 10k |
| **DeepSeek API** | ~60 RPS (лимит API) | ⚠️ Кэш спасает |
| **ChromaDB** | ~1 000 RPS | ⚠️ Для 10k норм |
| **Nginx** | ~10 000+ RPS | ✅ OK |

**Вывод:** текущая архитектура выдержит **2 000–5 000 DAU** без проблем.  
Для **10 000+** нужно: gunicorn ×4, rate limit, async, Celery.
