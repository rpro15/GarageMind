# AGENTS.md — GarageMind AI

## Project Overview

**GarageMind AI** ("Авто Эксперт AI") is a production Flask application that recommends tires via an AI chat consultant. Users interact through a **Telegram Mini App** (static SPA served by Flask) or directly via **REST API**. The backend integrates with partner APIs (Admitad, Wildberries), uses DeepSeek LLM for advice generation, and has Redis caching, ChromaDB vector search, and a Telegram bot.

**Domain:** Automotive tire selection for CIS market (Russian-language UI, brands common in Russia/CIS).

---

## Quick Start

```bash
cd GarageMind
cp .env.example .env     # fill in at least SECRET_KEY and DEEPSEEK_API_KEY
pip install -r requirements.txt
pip install bs4 lxml     # needed for forum scraping (not in requirements.txt!)
python -m app.main       # dev server on :8000
# OR
gunicorn wsgi:app -c gunicorn.conf.py
```

**Tests:**
```bash
python -m pytest tests/ -v --tb=short --cov=app
```

---

## Architecture

### Layer diagram (Hexagonal / Ports & Adapters)

```
Mini App (static SPA) ─┐
Telegram Bot ───────────┤
External API calls ─────┤
                        ▼
              ┌─────────────────────┐
              │  Flask (routes.py)  │  ← API layer
              │  admitad.py         │  ← OAuth flow
              │  errors.py          │  ← error handling
              └──────┬──────────────┘
                     │
              ┌──────▼──────────────┐
              │   Services          │  ← business logic
              │   (tire_recommend,  │
              │    vin_decoder,     │
              │    part_recognition,│
              │    user_history,    │
              │    product_compare) │
              └──────┬──────────────┘
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
  ┌──────────┐ ┌──────────┐ ┌──────────┐
  │ Ports    │ │ Adapters │ │ RAG      │
  │ (ABC)    │ │ (impl)   │ │ (Chroma) │
  │ llm_cli… │ │ deepseek │ │ embed.   │
  │ product… │ │ partner  │ │ store    │
  └──────────┘ │ wildbrbs │ │ retriev. │
               │ scraper  │ └──────────┘
               └──────────┘
```

### Core data flow (tire recommendation)

1. Client POSTs `{brand, model, year, driving_style}` to `/api/recommend_tires`
2. `routes.py` builds a `TireRequest` domain model
3. Check Redis cache (key: `recommend:{brand}:{model}:{year}:{driving_style}`)
4. Load user history from SQLite/Redis (if `user_id` provided)
5. `TireRecommendationService.get_recommendation()`:
   - Builds a prompt and calls `DeepSeekClient.generate_text()` for AI advice
   - Calls `MultiSourceProductService.find_tires()` which iterates over registered sources (PartnerSource → WildberriesSource) until reaching `min_products` (default 5)
   - If a `Retriever` is wired, enriches results with semantic search from ChromaDB
6. Returns `{advice, products}` as JSON

### Key directories

| Path | Purpose |
|------|---------|
| `app/domain/models.py` | All domain dataclasses (TireRequest, Product, etc.) |
| `app/api/routes.py` | REST endpoints (recognize-part, decode-vin, recommend_tires, compare_tires, brands/models, lang, user history) |
| `app/api/admitad.py` | OAuth flow for Admitad partner API |
| `app/api/errors.py` | Consistent error response format via `ApiError` exception |
| `app/ports/` | Abstract interfaces (`LLMClient`, `ProductCatalog`) |
| `app/adapters/` | Real implementations (DeepSeek, partner API, marketplace scraper) |
| `app/services/` | Business logic (tire recommendation, VIN decode, part recognition, product comparison, user history, caching, knowledge base) |
| `app/services/rag/` | RAG pipeline: embedding service → ChromaDB vector store → retriever |
| `app/services/sources/` | Product sources: PartnerSource (Admitad), WildberriesSource, ForumScraper, MultiSource aggregator |
| `app/services/database/` | SQLite schema + migrations + seed data |
| `app/services/knowledge/` | AutoCollector (background daemon that scrapes reviews on schedule) |
| `app/bot/` | Telegram bot via aiogram (dispatcher, handlers, keyboards) |
| `app/monitoring/` | Prometheus metrics, request ID middleware, structured logging |
| `app/miniapp/static/` | Static SPA (HTML, CSS, JS, i18n JSON files for 8 languages) |
| `app/config/settings.py` | All environment config loaded from `.env` |
| `tests/` | pytest test suite |
| `data/knowledge/` | JSON knowledge base files (reviews, compatibility data) |
| `monitoring/` | Prometheus + Grafana configs |

---

## Critical Gotchas & Non-Obvious Patterns

### 1. Flask, not FastAPI, but uses `httpx.AsyncClient` everywhere
The app is **Flask** (synchronous WSGI), but services use `httpx.AsyncClient` and `asyncio.run()` to call async code from sync Flask routes. The helper `_run_async()` in `routes.py` wraps `asyncio.run()`. This means:
- Gunicorn uses **sync** worker class by default (`worker_class = "sync"`)
- `asyncio.run()` blocks the sync thread — fine for single requests per worker
- If switching to FastAPI or Uvicorn workers, remove the `asyncio.run()` wrappers

### 2. Test fixture patches `requests.post`, but DeepSeekClient uses `httpx.AsyncClient`
The `mock_deepseek` fixture in `conftest.py` uses `monkeypatch.setattr('requests.post', mock_post)` — but `DeepSeekClient` uses `httpx.AsyncClient.post()`. This means **the mock fixture does NOT actually mock DeepSeek API calls**. Tests that hit the real recommendation path will either fall through to the stub response (if `DEEPSEEK_API_KEY` is empty) or make real HTTP calls.

### 3. Part recognition is a stub
`PartRecognitionService` always returns `part_name="шина (предположительно)", confidence=0.65`. It validates image MIME type and size only. Real vision-based recognition is not implemented.

### 4. Redis is optional with silent fallback
`RedisCache` falls back to no-op mode if Redis is unreachable. All cache methods (`get`, `set`, etc.) check `self._available` and return default values silently. The rate limiter also falls back from Redis to memory.

### 5. DeepSeekClient has built-in fallback
If `DEEPSEEK_API_KEY` is empty, `generate_text()` returns a hardcoded recommendation stub. This means the app works without any API key.

### 6. All domain models are `@dataclass`, not Pydantic
Domain models in `domain/models.py` use plain `@dataclass` with no validation. Pydantic is listed in requirements but only used for the RAG prompts (`chat_prompts.py`).

### 7. Rate limiter initialization is misleading
The code creates a `Limiter` with `storage_uri="memory://"` AND tries to detect Redis. The `storage_uri` is always `"memory://"` regardless of Redis detection — Redis is only used for actual rate limit counts through `RedisStorage` import path, but the `Limiter` init hardcodes `"memory://"`.

### 8. User history data is dual-stored
`UserHistoryService` writes to both Redis (fast cache) and SQLite (persistent). On read, it checks Redis first, falls back to SQLite, then caches back to Redis.

### 9. Naming inconsistency
`tire_recomendation.py` (misspelled filename — missing "m" in "recommendation"). The class inside is `TireRecommendationService` (correctly spelled). The route `/api/recommend_tires` also uses correct spelling. Be consistent with the class name, not the filename.

### 10. MultiSource has a `find_tires` method but `ProductCatalog` port also defines `find_products_by_query`
`MultiSourceProductService` only implements `find_tires()` (called by `TireRecommendationService`). The `find_products_by_query` abstract method on `ProductCatalog` is **not implemented** anywhere.

### 11. Admitad OAuth uses synchronous `httpx.post` while the rest uses async
The callback handler in `admitad.py` uses synchronous `httpx.post()` (no async) because it's a Flask route. This is fine for a one-off OAuth exchange.

### 12. ChromaDB collection created with default settings
`VectorStore` creates collection with `hnsw:space: cosine` and no explicit `hnsw:ef_construction` or `hnsw:M` parameters. For production with many products, tune these.

### 13. AutoCollector is a daemon thread in `main()`
The collector thread is a Python `threading.Thread(daemon=True)` that runs `asyncio.run()`. If the main Flask process restarts, the thread dies without cleanup. The collector only writes to SQLite, so no data loss.

---

## Language & i18n

- All of the following are in **Russian**: API error messages, system prompts for the LLM, code comments, README, inline documentation, domain model attribute names, and i18n JSON files (en, ru, hy, ka, kk, ky, tg, uz).
- **Code identifiers** (class names, function names, variable names) are in English.
- Responses to the user from the AI assistant should be in **Russian** by default, but follow the user's language.

---

## API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/recognize-part` | Upload image (multipart) or base64 JSON → stub recognition |
| GET/POST | `/api/decode-vin` | Validate/decode VIN → vehicle info |
| POST | `/api/recommend_tires` | Main recommendation endpoint (brand, model, year, driving_style required) |
| POST | `/api/compare_tires` | Compare 2-4 products (LLM-generated comparison) |
| GET | `/api/brands` | List supported car brands |
| GET | `/api/models?brand=...` | List models for a brand |
| GET | `/api/lang/{code}` | Get i18n strings for a locale |
| POST | `/api/user/history` | Save user profile/query history |
| GET | `/api/admitad/auth` | Start Admitad OAuth flow |
| GET | `/api/admitad/callback` | Admitad OAuth callback |
| GET | `/api/admitad/status` | Check Admitad connection status |
| GET | `/health` | Health check (returns 200) |

Error responses follow a consistent format: `{"error": {"code": "...", "message": "...", "request_id": "..."}}`.

---

## Environment Variables (key ones)

| Variable | Required | Default | Notes |
|----------|----------|---------|-------|
| `SECRET_KEY` | Yes | `dev-secret` | Flask secret |
| `DEEPSEEK_API_KEY` | No | empty | App works without it (stub responses) |
| `BOT_TOKEN` | No | empty | Telegram bot token |
| `REDIS_URL` | No | `redis://localhost:6379/0` | Falls back gracefully |
| `GARAGE_MIND_DB_PATH` | No | `data/garage_mind.db` | Use `:memory:` for tests |
| `ADMITAD_CLIENT_ID` | No | empty | Partner API |
| `ADMITAD_CLIENT_SECRET` | No | empty | Partner API |
| `WILDBERRIES_API_KEY` | No | empty | Falls back to Playwright parsing |
| `CACHE_TTL_RECOMMEND` | No | `600` | 10 min cache for recommendations |

---

## Tests

- Located in `tests/` — `test_api.py`, `test_routes.py`, `test_services.py`, `test_cache.py`, `test_db_schema.py`, `test_deepseek.py`, `test_monitoring.py`, `test_rag.py`
- Uses `pytest` with `pytest-cov` and `pytest-asyncio` (but `asyncio_mode` not set — tests use `asyncio.run()` manually)
- Coverage target: all `app/` modules
- `conftest.py` sets test env vars and creates a fresh Flask app for each test
- Tests are lenient — many assert `status_code in [200, 400, ...]` rather than exact codes
- To run a single test file: `python -m pytest tests/test_routes.py -v`

---

## Deployment

- **Docker**: `Dockerfile` + `docker-compose.yml` (api, redis, nginx)
- **Gunicorn**: 4 sync workers, 30s timeout, 1000 max requests per worker (memory leak protection)
- **CI/CD**: GitHub Actions — tests → Docker build/push → SSH deploy via `appleboy/ssh-action`
- **Monitoring**: Prometheus (`/metrics` endpoint) + Grafana dashboards
- **Backup**: `scripts/backup.sh` / `scripts/restore.sh` for SQLite DB
