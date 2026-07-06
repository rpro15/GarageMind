# 🤝 Интеграция партнёрских API

> ⏳ **Текущий статус**: партнёрские API пока НЕ подключены.  
> Все товары возвращаются из `MockPartnerCatalog` — заглушки с тестовыми данными.  
> Эта инструкция — **что и куда добавлять**, когда получите API-ключи.

---

## 📋 Что нужно сделать

| Шаг | Что | Статус |
|-----|-----|--------|
| 1 | Получить API-ключи от партнёров | ⏳ Ожидание |
| 2 | Добавить ключи в `.env` | 📝 Инструкция ниже |
| 3 | Создать адаптер для каждого партнёра | 📝 Инструкция ниже |
| 4 | Зарегистрировать адаптер в `MultiSourceProductService` | 📝 Инструкция ниже |
| 5 | **ОТКЛЮЧИТЬ** моковый каталог | 📝 Инструкция ниже |

---

## 🔌 1. Какие партнёры подключать

### 🥇 Приоритет (дают партнёрские ссылки + комиссию)

| Партнёр | API | Комиссия | Что даёт |
|---------|-----|----------|----------|
| **Admitad** | [admitad.com](https://www.admitad.com/ru/webmaster/) | до 6% | Wildberries, Ozon, AliExpress, 1500+ магазинов |
| **CityAds** | [cityads.com](https://cityads.com/) | до 8% | Exist, шинные магазины |
| **ActionPay** | [actionpay.net](https://www.actionpay.net/) | до 5% | Автозапчасти |

### 🥈 Дополнительно (парсинг без API)

| Источник | Метод | Описание |
|----------|-------|----------|
| Wildberries | Парсинг (playwright) | `/app/services/sources/wildberries_source.py` — уже есть код |
| Ozon | Парсинг | Нужно написать аналогично WB |
| Exist.ua | Парсинг | API открыто, нужен ключ |

---

## 📝 2. Добавление ключей в `.env`

Когда получите API-ключи, добавьте их в `.env`:

```ini
# === Admitad (партнёрская сеть) ===
ADMITAD_CLIENT_ID=ваш_client_id
ADMITAD_CLIENT_SECRET=ваш_client_secret
ADMITAD_COUPON=ваш_купон_код

# === Wildberries API (если ключ продавца) ===
WB_API_KEY=ваш_ключ_wildberries

# === Другие партнёры (по мере подключения) ===
# OZON_API_KEY=...
# EXIST_API_KEY=...
```

---

## 🧩 3. Где лежат адаптеры

### Текущая структура:

```
app/
├── adapters/
│   ├── deepseek_client.py        # ✅ DeepSeek AI (работает)
│   ├── partner_api.py            # ⚠️ MockPartnerCatalog (заглушка!)
│   └── marketplace_scraper.py    # ⚠️ Парсинг маркетплейсов (отключён)
│
└── services/
    └── sources/
        ├── multi_source.py       # ✅ MultiSourceProductService (оркестратор)
        ├── partner_source.py     # ⚠️ Admitad (ждёт API-ключ)
        └── wildberries_source.py # ⚠️ WB парсинг (ждёт доработки)
```

### Что менять, когда появятся ключи:

#### А) Подключить Admitad

В `app/services/sources/partner_source.py`:

1. Убедитесь, что `ADMITAD_CLIENT_ID` и `ADMITAD_SECRET` есть в `.env`
2. Раскомментируйте реальный API вызов в `fetch()` — сейчас там fallback

#### Б) Включить Wildberries

В `app/services/sources/wildberries_source.py`:

1. Если есть API-ключ продавца WB — он будет использоваться автоматически
2. Если нет — будет парсинг (нужно протестировать селекторы)

#### В) Подключить MultiSourceProductService к API

Сейчас API (endpoint `/api/recommend_tires`) использует `MockPartnerCatalog`.  
Нужно заменить его на `MultiSourceProductService`.

Файл: `app/main.py` (строка с `catalog = MockPartnerCatalog()`)

Заменить:
```python
# Было:
catalog = MockPartnerCatalog()

# Стало:
from app.services.sources import MultiSourceProductService
from app.services.sources.wildberries_source import WildberriesSource
from app.services.sources.partner_source import PartnerSource

catalog = MultiSourceProductService()
catalog.register_source(WildberriesSource(api_key=os.getenv("WB_API_KEY")))
catalog.register_source(PartnerSource(
    client_id=os.getenv("ADMITAD_CLIENT_ID"),
    client_secret=os.getenv("ADMITAD_CLIENT_SECRET"),
))
```

---

## 🔄 4. Полный цикл товара (как это работает)

```
Пользователь → Mini App → POST /api/recommend_tires
                              │
                              ▼
                     TireRecommendationService
                              │
                    ┌─────────┴──────────┐
                    ▼                     ▼
           1. DeepSeek AI          2. ProductCatalog
              (совет)                 (товары)
                                        │
                              ┌─────────┴──────────┐
                              ▼                     ▼
                     MockPartnerCatalog   MultiSourceProductService
                     (сейчас)              (когда ключи будут)
                                             │
                                   ┌─────────┼──────────┐
                                   ▼         ▼          ▼
                              Wildberries  Admitad   Ozon...
```

---

## 🧪 5. Как тестировать партнёрку

После подключения ключа:

```bash
# 1. Проверить, что ключи загружаются
docker compose exec api python -c "
import os
print('ADMITAD_ID:', os.getenv('ADMITAD_CLIENT_ID', '❌'))
print('WB_API_KEY:', os.getenv('WB_API_KEY', '❌'))
"

# 2. Протестировать поиск через MultiSourceProductService
docker compose exec api python -c "
import asyncio
from app.domain.models import TireRequest, DrivingStyle, Season
from app.services.sources import MultiSourceProductService
from app.services.sources.wildberries_source import WildberriesSource

async def test():
    svc = MultiSourceProductService()
    svc.register_source(WildberriesSource())
    req = TireRequest(brand='Toyota', model='Camry', year=2020, driving_style=DrivingStyle.comfort)
    products = await svc.find_tires(req)
    print(f'Найдено товаров: {len(products)}')
    for p in products[:3]:
        print(f'  - {p.name}: {p.price} ₽')

asyncio.run(test())
"

# 3. Проверить через API
curl -X POST https://rpro.su/api/recommend_tires \
  -H 'Content-Type: application/json' \
  -d '{"brand":"Toyota","model":"Camry","year":2024,"driving_style":"comfort","season":"summer"}'
```

---

## 🚫 6. Как отключить мок (когда всё готово)

1. В `app/main.py`:
   - Заменить `MockPartnerCatalog()` на `MultiSourceProductService()`
   - Зарегистрировать реальные источники

2. Удалить `app/adapters/partner_api.py` (или закомментировать импорт)

3. Пересобрать контейнер:
```bash
docker compose up -d --build api
```

---

## 📊 7. Ожидаемые результаты после подключения

| Метрика | Сейчас (мок) | После API |
|---------|-------------|-----------|
| Товаров в ответе | 1-3 шт (рандом) | 5-15 шт (реальные) |
| Цены | 7 900 - 9 200 ₽ | Реальные цены маркетплейсов |
| Ссылки | example.com | Реальные партнёрские ссылки |
| Доставка | Нет данных | Есть (если API даёт) |
| Комиссия | 0 ₽ | до 6% с продажи |

---

## 💡 Полезные ссылки

- [Admitad API документация](https://www.admitad.com/ru/webmaster/api/)
- [Wildberries API для продавцов](https://suppliers-api.wildberries.ru/)
- [Партнёрская программа Exist.ua](https://exist.ua/partners/)

---

*Документация обновляется по мере подключения партнёров.*
