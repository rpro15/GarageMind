# Авто Эксперт AI 🚗🤖

Умный AI-консультант по подбору шин. Telegram Mini App + Flask API + DeepSeek AI.

## Возможности

- 🎙️ **Голосовой ввод** — просто говорите параметры авто
- 💬 **Чат-интерфейс** — общайтесь с AI как с консультантом
- 🔍 **Умный подбор** — нейросеть DeepSeek анализирует и рекомендует шины
- 🏪 **Каталог партнёров** — цены и ссылки на покупку
- 📱 **Telegram Mini App** — работает внутри Telegram
- 🖼️ **Распознавание деталей по фото**
- 🔢 **Декодинг VIN-номера**

## Стек

- Python 3.11 / Flask 3.1
- Aiogram 3 (Telegram Bot)
- DeepSeek AI API
- HTML/CSS/JS (Mini App)
- Docker / Nginx / Redis

## Быстрый старт

```bash
# Клонировать
git clone https://github.com/yourusername/GarageMind.git
cd GarageMind

# Установить зависимости
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Настройки
cp .env.dev .env
# Отредактируйте .env под себя

# Запустить
python -m app.main
```

Открой в браузере: **http://localhost:8000/miniapp/index.html**

## Docker

```bash
docker compose up --build
```

## Конфигурация (.env)

| Переменная | По умолчанию | Описание |
|-----------|-------------|----------|
| `SECRET_KEY` | `dev-secret` | Ключ Flask |
| `BOT_TOKEN` | — | Токен Telegram бота |
| `DEEPSEEK_API_KEY` | — | Ключ DeepSeek API |
| `DEEPSEEK_MODEL` | `deepseek-chat` | Модель DeepSeek |
| `MINIAPP_URL` | `http://localhost:8000/miniapp/` | URL Mini App |
| `LOG_LEVEL` | `INFO` | Уровень логирования |

## Структура проекта

```text
app/
├── api/             # HTTP эндпоинты (Flask Blueprint)
├── bot/             # Telegram бот (aiogram)
├── config/          # Настройки
├── domain/          # Модели данных
├── ports/           # Интерфейсы (порты)
├── adapters/        # Адаптеры (DeepSeek, партнёры)
├── services/        # Бизнес-логика
├── miniapp/static/  # Frontend Mini App
└── main.py          # Точка входа
```

## API Endpoints

| Метод | Путь | Описание |
|------|------|---------|
| `POST` | `/api/recommend_tires` | Подбор шин |
| `GET` | `/api/brands` | Список марок |
| `GET` | `/api/models` | Модели для марки |
| `POST` | `/api/recognize-part` | Распознать деталь |
| `GET/POST` | `/api/decode-vin` | Декодировать VIN |

## Деплой на сервер

1. Установите Docker и docker-compose на сервере
2. Скопируйте `.env` с реальными ключами
3. Настройте nginx.conf под ваш домен
4. Получите SSL сертификаты (Let's Encrypt)
5. Запустите: `docker compose up -d --build`
