# 👗 AI Fashion Finder — Промт для разработки

> **Концепт:** Приложение находит одежду по фото. Сфоткал лук → AI распознаёт → показывает на Wildberries, Ozon, Lamoda

---

## 🎯 Идея

Пользователь загружает фото (стритстайл, витрина, селебрити). AI определяет:
- Категория (куртка, джинсы, кроссовки)
- Цвет, фасон, материал
- Ищет похожие товары на маркетплейсах
- Возвращает ссылки + сравнение цен

---

## 📁 Структура проекта (аналогично GarageMind)

```
fashion-ai/
├── app/
│   ├── api/               # Flask/Quart эндпоинты
│   │   ├── routes.py      # upload, recognize, search
│   │   ├── schemas.py     # Pydantic модели
│   │   └── middleware.py  # Rate limit, логи
│   │
│   ├── bot/               # Telegram Bot (aiogram)
│   │   ├── handlers.py    # Приём фото, меню
│   │   ├── keyboards.py   # Клавиатуры
│   │   └── messages.py    # Шаблоны ответов
│   │
│   ├── config/
│   │   ├── settings.py    # .env → Settings
│   │   └── prompts.yaml   # Промты для AI
│   │
│   ├── domain/
│   │   ├── clothing.py    # Модель одежды
│   │   ├── look.py        # Полный лук
│   │   └── product.py     # Товар с маркетплейса
│   │
│   ├── ports/
│   │   ├── image_analyzer.py   # Интерфейс AI-анализа
│   │   ├── search_engine.py    # Интерфейс поиска
│   │   └── product_api.py      # Интерфейс маркетплейсов
│   │
│   ├── adapters/
│   │   ├── deepseek_api.py     # DeepSeek Vision
│   │   ├── yandex_vision.py    # Yandex Vision (альтернатива)
│   │   ├── wildberries_api.py  # WB партнёрский API
│   │   ├── ozon_api.py         # Ozon API
│   │   ├── lamoda_api.py       # Lamoda API
│   │   └── admitad_api.py      # Admitad (партнёрки)
│   │
│   ├── services/
│   │   ├── image_analysis.py   # Анализ фото → категории
│   │   ├── visual_search.py    # Поиск похожих товаров
│   │   ├── product_matcher.py  # Сопоставление: фото → товар
│   │   ├── price_comparison.py # Сравнение цен по магазинам
│   │   ├── outfit_builder.py   # Сборка полного лука
│   │   ├── user_history.py     # История поисков
│   │   ├── cache.py            # Redis-кэш (аналогично)
│   │   └── rag/                # RAG для каталога брендов
│   │       ├── chroma_client.py
│   │       └── knowledge_base.py
│   │
│   ├── monitoring/
│   │   ├── metrics.py          # Prometheus
│   │   └── logger.py           # Логирование
│   │
│   ├── miniapp/            # Telegram Mini App + PWA
│   │   └── static/
│   │       ├── index.html      # Камера + результаты
│   │       ├── style.css       # Carbon Design / Fashion-тема
│   │       ├── scripts.js      # Работа с камерой
│   │       ├── manifest.json   # PWA
│   │       ├── sw.js           # Service Worker
│   │       ├── icons/          # Иконки (логотип)
│   │       └── lang/           # RU, EN, KZ, UZ
│   │
│   └── main.py             # Точка входа
│
├── data/
│   ├── chroma_db/          # Векторная БД брендов
│   └── sqlite/             # SQLite (knowledge base)
│
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
├── README.md
└── docs/
    └── PRESENTATION.md
```

---

## 🧠 Как работает

```
[Фото пользователя]
       │
       ▼
┌─────────────────┐
│  AI Vision       │  DeepSeek / Yandex Vision
│  (распознаёт)    │  → определяет: куртка, пуховик, зелёный
└────────┬────────┘
         │
         ▼
┌────────────────────┐
│  Visual Search     │  Поиск по фото на WB/Ozon/Lamoda
│  (ищет похожее)    │  → находит 5-10 похожих товаров
└────────┬───────────┘
         │
         ▼
┌────────────────────┐
│  Price Comparison  │  Сравнение: цена, размер, отзывы
│  (выбирает лучшее) │  → топ-3 с ссылками
└────────┬───────────┘
         │
         ▼
┌────────────────────┐
│  Outfit Builder    │  Если фото полного лука:
│  (собирает лук)    │  → джинсы + кроссовки + сумка
└────────┬───────────┘
         │
         ▼
[Ответ: 3 товара + ссылки + цены + похожие]
```

---

## 🎨 UI / UX

- **Камера**: открыть камеру или выбрать из галереи
- **Обрезка**: авто-кароп фото на объект
- **Результат**: карточка товара → цена → WB/Ozon/Lamoda
- **Поделиться**: можно отправить другу
- **Избранное**: сохранить лук

### Цветовая схема (модная, премиум)

| Роль | Цвет | Код |
|:-----|:-----|:----|
| Фон | Тёмно-серый | `#0d0d0d` |
| Акцент | Розово-пурпурный | `#ff2d78` |
| Акцент 2 | Градиент заката | `#ff6b35 → #ff2d78 → #a83279` |
| Текст | Белый | `#ffffff` |
| Карточки | Glassmorphism | `rgba(255,255,255,0.05)` |

---

## 🔧 Технологии

| Компонент | Технология |
|:----------|:-----------|
| Backend | Python 3.11 / Flask или Quart (async) |
| AI Vision | DeepSeek Vision API / Yandex Vision |
| Поиск | Аггрегатор маркетплейсов (WB API, Ozon API, Lamoda API) |
| Векторная БД | ChromaDB (→ Qdrant для продакшна) |
| Кэш | Redis |
| База знаний | SQLite |
| Фронтенд | HTML/CSS/JS + Camera API |
| Telegram Bot | Aiogram 3 |
| Telegram Mini App | + PWA для установки на iPhone |
| Партнёрские ссылки | Admitad, Everad |
| Мониторинг | Prometheus + Grafana |
| Деплой | Docker + Docker Compose + Nginx |

---

## 🌍 Языки (MVP — 3 языка)

- 🇷🇺 Русский
- 🇬🇧 English
- 🇰🇿 Қазақша

---

## 🗺️ Roadmap

### MVP (v1.0)
- [ ] Загрузка фото
- [ ] AI-распознавание категории одежды
- [ ] Поиск на Wildberries
- [ ] Telegram Mini App
- [ ] Базовый UI

### v1.1
- [ ] Поиск на Ozon + Lamoda
- [ ] Сравнение цен
- [ ] PWA для iPhone
- [ ] Redis-кэш

### v1.2
- [ ] RAG для брендов
- [ ] Распознавание полного лука (outfit)
- [ ] Избранное / история
- [ ] 8 языков

### v1.3
- [ ] Свой каталог (продажа через партнёрку)
- [ ] AI-стилист: «что добавить к этому луку»
- [ ] Chrome Extension «найди это на WB»

---

## 💡 Что добавить (мои идеи)

1. 🔍 **Поиск по селфи**: «иди и купи такое же» — по фото на улице
2. 📏 **Определение размера**: AI + таблицы размеров брендов
3. 💰 **Уведомления о скидках**: на отслеживаемые товары
4. 🎨 **Палитра цветов**: из фото → подборка вещей под цветотип
5. 🌐 **Chrome Extension**: клик по фото на сайте → поиск на WB
6. 📱 **iOS Shortcut**: Siri → «найди такой же пуховик»
7. 🤖 **Тг-бот + Mini App**: дуальный запуск

---

## ⚡ Быстрый старт (как в GarageMind)

```bash
git clone https://github.com/rpro15/FashionFinder.git
cd FashionFinder
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # API ключи
python -m app.main

# Docker
docker compose up --build
```

---

## 🎯 Промт для меня (разработчика)

> Разработай Fashion Finder AI — приложение, которое по фото находит одежду на маркетплейсах (WB, Ozon, Lamoda). 
>
> **Структура** — как в GarageMind: Flask API + Telegram Mini App + PWA + Redis + RAG.
>
> **Ключевые фичи:**
> - AI-распознавание одежды по фото (DeepSeek Vision / Yandex Vision)
> - Поиск похожих товаров на маркетплейсах
> - Сравнение цен по 3+ магазинам
> - Сборка полного лука из нескольких предметов
> - Telegram Mini App с камерой
> - PWA для iPhone (без App Store)
> - Премиальный тёмный дизайн (fashion-стиль)
>
> **Цвета:** #ff2d78 (розовый), #ff6b35 (оранжевый), #0d0d0d (фон)
> **Иконка:** на тёмном фоне — стилизованная вешалка/платье, неоновый розовый
>
> Начни с настройки .env, создания виртуального окружения и запуска базового Flask-сервера.
