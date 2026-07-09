# 🚗 GarageMind AI — Умный AI-консультант по подбору шин

**Premium AI-консультант** | Telegram Mini App + Flask API + DeepSeek AI + RAG

---

## ✨ Возможности

### 🤖 AI-консультант (DeepSeek)
- **Умный подбор шин** — нейросеть анализирует авто, стиль вождения, сезон, бюджет
- **Пошаговый диалог** — общается как живой консультант (6 шагов опроса)
- **История запросов** — AI помнит, что вы искали ранее (персонализация)
- **Сравнение товаров** — выберите 2–3 шины и получите таблицу сравнения

### 🧠 RAG-база знаний (Retrieval Augmented Generation)
- **ChromaDB** — векторный поиск по каталогу шин
- **Парсинг форумов** — сбор реальных отзывов с drive2.ru, drom.ru, pnevo.ru, автоклубов
- **SQLite база знаний** — проверенные размеры шин, популярные модели, известные проблемы
- **Автосборщик отзывов** — ежечасно пополняет базу (до 100 отзывов в день)

### ⚡ Кэширование и скорость
- **Redis** — кэш ответов DeepSeek (10 мин), списка брендов/моделей (1 час)
- **Декоратор `@cached`** — автоматическое кэширование любых функций
- **Fallback-режим** — работает без Redis (no-cache режим)

### 🌍 Мультиязычность (8 языков)
🇷🇺 Русский · 🇬🇧 English · 🇰🇿 Қазақша · 🇺🇿 O'zbekcha · 🇰🇬 Кыргызча · 🇹🇯 Тоҷикӣ · 🇦🇲 Հայերեն · 🇬🇪 ქართული

### 📱 Telegram Mini App
- Два режима: **Чат** (пошаговый диалог) и **Форма** (быстрый подбор)
- **Голосовой ввод** — SpeechRecognition API
- **Carbon Design** — тёмная тема, glassmorphism, анимации
- **Адаптивность** — идеально под Telegram и мобильные

### 🔧 Дополнительно
- 🔢 **VIN-декодинг** — расшифровка VIN-номера
- 🖼️ **Распознавание деталей по фото**
- 🏪 **Партнёрские ссылки** — Wildberries, Ozon, AliExpress через Admitad
- 📊 **Prometheus + Grafana** мониторинг

---

## 🆕 Что добавлено в 2026

- ✅ **Redis-кэширование** всех частых запросов
- ✅ **Парсинг реальных отзывов** с 8 автомобильных форумов
- ✅ **Персонализация** — AI помнит историю каждого пользователя
- ✅ **Сравнение товаров** — выберите 2–3 шины, получите таблицу + рекомендацию AI
- ✅ **RAG (Retrieval Augmented Generation)** — семантический поиск по ChromaDB
- ✅ **Автосборщик знаний** — фоновый сбор отзывов с соблюдением дневного лимита
- ✅ **Полные настройки в `.env`** — все параметры вынесены в конфигурацию

---

## 📊 Архитектура

```
┌─────────────────────────────────────────────────────────────┐
│                    Telegram Mini App                        │
│    (HTML/CSS/JS — Carbon Design, 8 языков, голосовой ввод) │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                    Flask API (Python 3.11)                   │
│  ┌──────────┐ ┌───────────┐ ┌──────────┐ ┌──────────────┐ │
│  │ DeepSeek │ │  RAG      │ │ User     │ │ Product      │ │
│  │ AI       │ │ Retriever │ │ History  │ │ Comparison   │ │
│  └──────────┘ └───────────┘ └──────────┘ └──────────────┘ │
│  ┌──────────┐ ┌───────────┐ ┌──────────────────────────┐ │
│  │ Forum    │ │ Auto-     │ │ VIN Decoder / Part       │ │
│  │ Scraper  │ │ Collector │ │ Recognition              │ │
│  └──────────┘ └───────────┘ └──────────────────────────┘ │
└──────────┬──────────────┬──────────────┬───────────────────┘
           │              │              │
┌──────────▼──┐ ┌─────────▼──────┐ ┌────▼────────────────┐
│   Redis     │ │   ChromaDB    │ │   SQLite             │
│   (кэш)     │ │   (векторы)   │ │   (отзывы, шины)    │
└─────────────┘ └────────────────┘ └─────────────────────┘
```

---

## 🚀 Быстрый старт

```bash
# 1. Клонировать
git clone https://github.com/rpro15/GarageMind.git
cd GarageMind

# 2. Установить зависимости
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Настройки
cp .env.example .env
# Отредактируйте .env под себя

# 4. Запустить
python -m app.main
```

Открой в браузере: **http://localhost:8000/miniapp/index.html**

## 🐳 Docker

```bash
docker compose up --build
```

---

## 🔧 Конфигурация (.env)

| Переменная | По умолчанию | Описание |
|-----------|-------------|----------|
| **Основные** |
| `SECRET_KEY` | `dev-secret` | Ключ Flask |
| `LOG_LEVEL` | `INFO` | Уровень логирования |
| **Telegram** |
| `BOT_TOKEN` | — | Токен Telegram бота |
| **DeepSeek / LLM** |
| `DEEPSEEK_API_KEY` | — | Ключ DeepSeek API |
| `DEEPSEEK_MODEL` | `deepseek-chat` | Модель DeepSeek |
| **Redis (кэш)** |
| `REDIS_URL` | `redis://localhost:6379/0` | URL Redis |
| `CACHE_TTL_RECOMMEND` | `600` | TTL кэша рекомендаций (10 мин) |
| `CACHE_TTL_BRANDS` | `3600` | TTL кэша брендов (1 час) |
| `CACHE_TTL_MODELS` | `3600` | TTL кэша моделей (1 час) |
| **AutoCollector (сбор отзывов)** |
| `COLLECTOR_DAILY_LIMIT` | `100` | Макс. отзывов в день |
| `AUTO_COLLECTOR_INTERVAL_MINUTES` | `60` | Проверка каждый час |
| `AUTO_COLLECTOR_REVIEWS_PER_CYCLE` | `10` | За один цикл |
| **Партнёрские API** |
| `ADMITAD_CLIENT_ID` | — | Admitad API ключ |
| `ADMITAD_CLIENT_SECRET` | — | Admitad секрет |
| `WILDBERRIES_API_KEY` | — | Wildberries API |

---

## 📁 Структура проекта

```text
GarageMind/
├── app/
│   ├── api/                    # HTTP эндпоинты
│   ├── bot/                    # Telegram бот
│   ├── config/                 # Настройки (.env → Settings)
│   ├── domain/                 # Модели данных
│   ├── ports/                  # Интерфейсы (LLM, ProductCatalog)
│   ├── adapters/               # DeepSeek, партнёры
│   ├── services/
│   │   ├── cache.py            # Redis кэш + декоратор @cached
│   │   ├── tire_recomendation.py  # AI-подбор шин
│   │   ├── part_recognition.py    # Распознавание по фото
│   │   ├── vin_decoder.py         # VIN-декодинг
│   │   ├── product_comparison.py  # Сравнение товаров 🆕
│   │   ├── user_history.py        # Персонализация 🆕
│   │   ├── database/              # SQLite база знаний
│   │   ├── rag/                   # RAG (ChromaDB)
│   │   ├── knowledge/             # Автосборщик отзывов
│   │   └── sources/               # Парсинг форумов 🆕
│   ├── monitoring/             # Prometheus метрики
│   ├── miniapp/static/         # Frontend
│   └── main.py                 # Точка входа
├── data/                       # SQLite, ChromaDB
├── docs/                       # Документация
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

---

## 🌐 API Endpoints

| Метод | Путь | Описание |
|------|------|---------|
| `GET` | `/health` | Healthcheck |
| `POST` | `/api/recommend_tires` | Подбор шин (с кэшем) |
| `POST` | `/api/compare_tires` | Сравнение 2–3 товаров 🆕 |
| `GET` | `/api/brands` | Список марок (с кэшем) |
| `GET` | `/api/models` | Модели для марки (с кэшем) |
| `POST` | `/api/recognize-part` | Распознать деталь по фото |
| `GET/POST` | `/api/decode-vin` | Декодировать VIN |
| `POST` | `/api/user/history` | История пользователя 🆕 |
| `GET` | `/api/lang/<code>` | Файл локализации |

---

## 🗺️ Roadmap

### ✅ v1.0 (текущее)
- AI-подбор шин через DeepSeek
- Telegram Mini App с Carbon Design
- 8 языков интерфейса
- VIN-декодинг, распознавание по фото

### ✅ v1.1 (2026)
- Redis-кэширование
- RAG-поиск через ChromaDB
- Парсинг реальных отзывов с форумов
- Персонализация (история пользователя)
- Сравнение товаров
- Автосборщик отзывов

### 🔜 v1.2 (планы)
- Push-уведомления о скидках
- A/B-тестирование промптов
- Локальная модель Llama
- Админ-панель

---

## 📄 Лицензия

MIT © 2026 Garage Mind AI
