# 🚗 Авто Эксперт AI

**AI-консультант по подбору шин** — Telegram Mini App с премиум-дизайном и экспертной системой рекомендаций.

---

## 📱 Скриншоты

| Чат-консультант | Форма подбора | Диалог подбора |
|:---:|:---:|:---:|
| ![Чат](screenshots/01_chat.png) | ![Форма](screenshots/02_form.png) | ![Диалог](screenshots/03_chat_dialog.png) |

| Форма с данными |
|:---:|
| ![Форма заполнена](screenshots/04_form_filled.png) |

---

## ✨ Возможности

### 🎯 Два режима подбора
1. **Чат-консультант** — пошаговый диалог с AI (6 шагов: марка → модель → год → стиль вождения → сезон → бюджет)
2. **Форма быстрого подбора** — все поля сразу для тех, кто знает, что ищет

### 🗄️ База данных (92 бренда)

| Регион | Бренды |
|:-------|:-------|
| 🇷🇺 **Россия** | Lada, УАЗ, ГАЗ, КАМАЗ, Москвич, Evolute, Aurus, Daewoo, ЗАЗ |
| 🇪🇺 **Европа** | VW, BMW, Mercedes, Audi, Porsche, Skoda, Opel, Renault, Peugeot, Citroen, Fiat, Volvo, Mini, Smart, Alfa Romeo, Maserati, Ferrari, Lamborghini, Bentley, Rolls-Royce, Aston Martin, Jaguar, Land Rover |
| 🇰🇷 **Корея** | Kia, Hyundai, Genesis, SsangYong + Kyron, KGM (KG Mobility) |
| 🇯🇵 **Япония** | Toyota, Nissan, Honda, Mazda, Mitsubishi, Subaru, Suzuki, Lexus, Infiniti |
| 🇺🇸 **США** | Ford, Chevrolet, Dodge, Jeep, Cadillac, Lincoln, GMC, Tesla |
| 🇨🇳 **Китай (38 брендов)** | Chery, Changan, Geely, Haval, BYD, Zeekr, Li Auto, NIO, Voyah, Exeed, Omoda, Jaecoo, Tank, Great Wall, GAC, Hongqi, BAIC, Dongfeng, FAW, DFSK, Wuling, HiPhi, Xpeng, Lantu, Avatr, AITO, IM Motors, Ora, Wey, Kaiyi, Fengon, Skywell, Soueast, Baojun, Foton, Neta, MVM, SWM |

### 🎨 Премиум-дизайн
- Carbon-тёмная тема с акцентным неоново-голубым (Cyan)
- Анимированный фон с силуэтом автомобиля
- Стеклянные эффекты (glassmorphism) с backdrop-blur
- Навигатор по деталям (`parts-nav`) с SVG-иконками
- Плавные анимации (появление сообщений, карточек, загрузки)
- Анимированная индикация печати (typing dots)
- Индикатор речи (speech wave)

### 🔊 Голосовой ввод
- Распознавание речи (SpeechRecognition API)
- Визуальный индикатор с анимацией волны
- Поддержка русского языка

### 🛠️ Результаты подбора
- **Совет AI** — экспертная рекомендация (advice-box)
- **Народный выбор** — популярная модель с золотым акцентом
- **Список товаров** — карточки с ценами, рейтингом, изображениями
- **Лучшая цена** — автоматический бейдж на самом дешёвом варианте
- **Рейтинг звёздами** — визуальная оценка товара
- **Кнопка "Купить"** — прямая ссылка на магазин
- **Поделиться** — Web Share API для отправки друзьям

### 💻 Технологии
- **Backend:** Python 3 + Flask + CORS
- **Frontend:** Vanilla JS + CSS3 (Custom Properties + SVG)
- **Telegram:** Mini Apps API (expand, ready, sendData)
- **Мониторинг:** Prometheus метрики + structured logging

---

## 🚀 Запуск

```bash
# Установка зависимостей
pip install flask flask-cors httpx python-dotenv prometheus-flask-exporter

# Запуск сервера
cd GarageMind
PYTHONPATH=. python app/main.py
```

Сервер будет доступен на `http://localhost:8000`

Mini App: `http://localhost:8000/miniapp/index.html`

---

## 📐 Архитектура

```
GarageMind/
├── app/
│   ├── main.py              # Точка входа Flask
│   ├── api/                  # REST API
│   │   ├── routes.py         # Эндпоинты (/api/recommend_tires, /api/brands)
│   │   └── errors.py         # Обработка ошибок
│   ├── miniapp/
│   │   └── static/           # Frontend (фронтенд бизнес-логика)
│   │       ├── index.html    # Mini App (Telegram + браузер)
│   │       ├── style.css     # Premium Carbon Design (25KB)
│   │       └── scripts.js    # Полная логика чата и формы (29KB)
│   ├── adapters/             # Внешние API (DeepSeek AI)
│   ├── config/               # Конфигурация (.env)
│   ├── monitoring/           # Prometheus метрики
│   └── bot/                  # Telegram Bot (aiogram)
└── docs/
    └── README.md             # ← Этот файл
```

---

## 🔮 План масштабирования

### 1️⃣ Frontend (Mini App)
- [ ] **Каталог шин** — полноценная база товаров с фильтрацией
- [ ] **Сравнение товаров** — выбор 2–3 моделей для сравнения
- [ ] **Отзывы** — возможность оставить отзыв на шины
- [ ] **История запросов** — сохранение предыдущих подборов
- [ ] **Сохранение авто** — профиль автомобиля (несколько марок)
- [ ] **PWA** — установка на главный экран, оффлайн-режим
- [ ] **Тёмная/светлая тема** — переключение
- [ ] **Локализация** — английский, казахский, узбекский

### 2️⃣ Backend
- [ ] **Авторизация** — вход через Telegram / Google
- [ ] **База данных** — PostgreSQL вместо in-memory
- [ ] **Кеширование** — Redis для быстрых ответов
- [ ] **Рекомендательная система** — ML на основе истории
- [ ] **Партнёрские API** — реальные цены от маркетплейсов
- [ ] **WebSocket** — real-time уведомления о новых ценах

### 3️⃣ Mobile / Telegram
- [ ] **Native Android App** — Kotlin, Material Design 3
- [ ] **iOS App** — SwiftUI
- [ ] **Telegram Bot** — полноценный бот с inline-режимом
- [ ] **Push-уведомления** — скидки, новые поступления

### 4️⃣ Монетизация
- [ ] **Партнёрские ссылки** — комиссия с покупок (агрегаторы)
- [ ] **Premium-подписка** — расширенная аналитика, без рекламы
- [ ] **Сервисный центр** — интеграция с шиномонтажами
- [ ] **B2B** — API для автосалонов и автосервисов

### 5️⃣ AI/ML
- [ ] **Рекомендации на основе модели авто** — анализ совместимости
- [ ] **Прогноз цен** — когда лучше покупать
- [ ] **Чат-бот** — генеративные ответы через LLM
- [ ] **Распознавание авто по фото** — сфотографировал шину → получил рекомендацию

---

## 📊 Статистика кода

| Файл | Размер | Строк |
|:-----|:-------|:-----|
| `style.css` | 25 KB | 1043 |
| `scripts.js` | 29 KB | 640+ |
| `index.html` | 8 KB | ~180 |
| **Всего фронтенд** | **~62 KB** | **~1850** |

---

## 🧑‍💻 Команда

Проект создан для автоматизации подбора шин на рынке РФ.  
**2026 — Garage Mind AI**
