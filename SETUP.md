# 🚀 Настройка GarageMind AI — полный чеклист

Что нужно сделать для полноценной работы всех компонентов.

---

## 📋 Быстрый чеклист

| № | Что | Статус | Команда |
|---|-----|--------|---------|
| 1 | Redis | ❌ Не запущен | `sudo systemctl start redis` |
| 2 | SQLite seed-данные | ⚠️ 57 авто, 120 отзывов | `python3 -m app.services.database.seed_data` |
| 3 | ChromaDB (векторная БД) | ❌ Пустая | `python3 -m app.services.rag.build_index` |
| 4 | DeepSeek API | ✅ Есть ключ | — |
| 5 | Admitad API | ❌ Нет ключа | добавить в `.env` |
| 6 | Wildberries партнёрка | ❌ Нет ID | добавить в `.env` |
| 7 | Telegram Bot | ❌ Нет токена | создать через @BotFather |
| 8 | Rate Limiter | ✅ memory fallback | работают |

---

## 1. 🛑 Redis

```bash
# Запустить
sudo systemctl start redis

# Автозагрузка при старте
sudo systemctl enable redis

# Проверить
redis-cli ping
# → PONG
```

> Без Redis Rate Limiter работает на памяти (memory://), что нормально для разработки.

---

## 2. 🔧 Наполнить SQLite seed-данными

```bash
cd /home/ruslan/GarageMindAI/GarageMind
source .venv/bin/activate

# Наполнить БД: 100+ авто, 500+ отзывов, проблемы, спецификации
python3 -m app.services.database.seed_data
```

**Что будет добавлено:**
- 🚗 100+ популярных моделей авто (Lada, Toyota, BMW, Kia, Hyundai, Chery, Geely...)
- 🔩 Размеры шин, PCD, вылет, резьба для каждой модели
- ⭐ 500+ отзывов владельцев с оценками, плюсами, минусами
- ⚠️ Известные проблемы по моделям
- 📊 Технические характеристики шин

**Проверить результат:**
```python
from app.services.database.schema import DatabaseService
db = DatabaseService()
print(db.stats())
# → {'cars': 120+, 'reviews': 500+, 'db_size_mb': 2.5}
```

---

## 3. 🧠 ChromaDB — векторный индекс товаров

```bash
source .venv/bin/activate

# Установить chromadb если ещё нет
pip install chromadb

# Создать индекс
python3 -m app.services.rag.build_index
```

**Что делает:**
- Берёт все названия шин из SQLite (отзывы, проблемы, спецификации)
- Генерирует эмбеддинги через DeepSeek API
- Сохраняет в ChromaDB (папка `data/chromadb/`)
- Позволяет RAG-ретриверу искать семантически похожие товары

**Проверить:**
```python
from app.services.rag import EmbeddingService, VectorStore, Retriever
store = VectorStore()
print(f'Документов в индексе: {store._collection.count()}')
# → 200+
```

---

## 4. 🌐 Admitad API — партнёрские ссылки (опционально)

Добавить в `.env`:
```env
ADMITAD_CLIENT_ID=твой_client_id
ADMITAD_CLIENT_SECRET=твой_client_secret
```

**Где взять:**
1. Зарегистрироваться: https://www.admitad.com/ru/webmaster/
2. Настройки → API → Создать приложение
3. Получить `client_id` и `client_secret`

> Без Admitad API товары генерируются из базы знаний (реальные названия шин) → ссылки на Wildberries с поисковым запросом.

---

## 5. 💰 Wildberries партнёрская ссылка (опционально)

Добавить в `.env`:
```env
WILDBERRIES_AFFILIATE_ID=твой_id
```

**Где взять:**
1. https://partner.wildberries.ru/
2. Получить affiliate ID

---

## 6. 🤖 Telegram Bot (опционально)

Добавить в `.env`:
```env
BOT_TOKEN=1234567890:ABCdefGHIjklmNOPqrstUVwxyz
```

**Где взять:**
1. Написать @BotFather в Telegram
2. `/newbot` → ввести имя → получить токен
3. Команда `/setdomain` → указать твой домен
4. Команда `/setmenubutton` → указать URL Mini App

**Запустить бота:**
```bash
python3 -m app.bot.dispatcher
```

---

## 7. 🚀 Полный первый запуск

```bash
#!/bin/bash

cd /home/ruslan/GarageMindAI/GarageMind
source .venv/bin/activate

# 1. Redis
sudo systemctl start redis

# 2. Seed-данные
python3 -m app.services.database.seed_data

# 3. Векторный индекс
python3 -m app.services.rag.build_index

# 4. Запустить сервер
python3 -m app.main
```

Открыть в браузере: **http://localhost:8000/miniapp/**

---

## 8. 🐳 Docker (продакшен)

```bash
docker compose up --build -d
```

`docker-compose.yml` поднимет:
- API + Mini App (Flask на порту 8000)
- Redis
- Nginx (прокси + SSL)
- Фоновый AutoCollector

---

## 9. 📊 Проверка что всё работает

```bash
# Healthcheck
curl http://localhost:8000/health
# → {"status":"ok","service":"avto-expert-ai"}

# AI-чат
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Подбери шины для Тойота Камри 2020"}],"user_data":{},"user_id":"test"}'
# → {"reply":"...", "ready":false}

# Рекомендация
curl -X POST http://localhost:8000/api/recommend_tires \
  -H "Content-Type: application/json" \
  -d '{"brand":"Toyota","model":"Camry","year":2020,"driving_style":"comfort","season":"summer"}'
# → {"advice":"...", "products":[...]}
```

---

## 10. 🧪 Запуск тестов

```bash
source .venv/bin/activate
python3 -m pytest tests/ -v
```

Ожидаемый результат: **60 passed**
