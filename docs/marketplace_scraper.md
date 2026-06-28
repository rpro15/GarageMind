# Marketplace Scraper — поиск шин по открытым источникам

## Зачем

Пока нет API от Ozon / Wildberries / Яндекс.Маркета, модуль `MarketplaceScraper`
пытается получить данные через **парсинг HTML** публичных страниц поиска.

Когда появятся официальные API — достаточно отключить скрапер и включить API-адаптер.

---

## Как работает

1. Формируется поисковый URL для маркетплейса (шаблон в `MARKETPLACES`)
2. GET-запрос с заголовками реального браузера (User-Agent)
3. Парсинг HTML через JSON-LD / микроразметку (без lxml/bs4)
4. Если парсинг упал или маркетплейс отключён — возвращается **заглушка**

---

## Подключение скрапера

### 1. Включить нужный маркетплейс в конфиге

Файл: `app/adapters/marketplace_scraper.py`

```python
MARKETPLACES = [
    {
        "name": "Ozon",
        "search_url": "https://www.ozon.ru/search/?text={query}",
        "enabled": True,        # <-- поменять на True
        "selectors": { ... },
    },
]
```

### 2. Создать адаптер для ProductCatalog

```python
# app/adapters/scraper_catalog.py
from app.adapters.marketplace_scraper import MarketplaceScraper
from app.domain.models import Product, TireRequest
from app.ports.product_catalog import ProductCatalog

class ScraperCatalog(ProductCatalog):
    def __init__(self):
        self.scraper = MarketplaceScraper()

    async def find_tires(self, request: TireRequest) -> list[Product]:
        query = f"{request.brand} {request.model} {request.year} шины"
        return await self.scraper.search(query)
```

### 3. Подключить в create_app() вместо MockPartnerCatalog

В `app/main.py`:

```python
from app.adapters.scraper_catalog import ScraperCatalog

# Было:
catalog = MockPartnerCatalog()

# Стало:
catalog = ScraperCatalog()
```

---

## Отключение скрапера (переход на API)

Когда появится официальный API (например, Ozon Seller API / WB API):

### 1. Создать API-адаптер

```python
# app/adapters/ozon_api.py
class OzonApiCatalog(ProductCatalog):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.ozon.ru/..."

    async def find_tires(self, request: TireRequest) -> list[Product]:
        # ... запрос к Ozon API ...
        pass
```

### 2. Переключить в main.py

```python
catalog = OzonApiCatalog(settings.OZON_API_KEY)
```

### 3. Отключить скрапер

```python
MARKETPLACES[0]["enabled"] = False  # или просто не импортировать ScraperCatalog
```

---

## Конфигурация маркетплейсов

| Поле | Описание |
|------|----------|
| `name` | Название (Ozon, Wildberries, ...) |
| `search_url` | URL поиска с `{query}` внутри |
| `enabled` | `True` — реальный парсинг, `False` — заглушка |
| `selectors` | CSS-селекторы для карточки, названия и цены |
| `partner_link` | Шаблон ссылки на товар (если есть) |

### Текущий статус

| Маркетплейс | Статус | Комментарий |
|-------------|--------|-------------|
| Ozon | ❌ отключён | Селекторы не протестированы |
| Wildberries | ❌ отключён | Селекторы не протестированы |
| Яндекс.Маркет | ❌ отключён | Селекторы не протестированы |
| Drom.ru | ❌ отключён | Требует отдельной реализации |

---

## Важно

- Маркетплейсы могут блокировать частые запросы без API-ключа
- При `enabled=False` всегда возвращается **заглушка** из 3-х случайных шин
- Для продакшена **рекомендуется** получать API-доступ к маркетплейсам
- При включении скрапера добавьте `random` задержку между запросами, чтобы не получить блокировку

## Пример: быстрый тест скрапера

```bash
cd /project
python -c "
import asyncio
from app.adapters.marketplace_scraper import MarketplaceScraper

async def test():
    s = MarketplaceScraper()
    products = await s.search('Toyota Camry шины')
    for p in products:
        print(f'{p.name} — {p.price} ₽ [{p.source}]')
    await s.close()

asyncio.run(test())
```
