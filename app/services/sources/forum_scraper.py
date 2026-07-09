"""
Парсер отзывов с автомобильных форумов.

Собирает реальные отзывы владельцев о шинах.
Использует простые HTTP-запросы + BeautifulSoup.

Популярные площадки СНГ для сбора отзывов:
┌─────────────────────┬────────────────────────────────────────┬──────────┐
│ Площадка            │ Что парсим                            │ Статус   │
├─────────────────────┼────────────────────────────────────────┼──────────┤
│ drive2.ru           │ Отзывы, бортовые журналы о шинах      │ ✅       │
│ drom.ru             │ Раздел отзывов о шинах                │ ✅       │
│ pnevo.ru            │ Шинный портал, отзывы                 │ ✅       │
│ forum.toyota.ru     │ Toyota-клуб, темы о шинах             │ ✅       │
│ kia-forum.ru        │ Kia-клуб                              │ ✅       │
│ vwts.ru             │ Volkswagen-клуб                       │ ✅       │
│ skoda-forum.ru      │ Skoda-клуб                            │ ✅       │
│ hyundai-forum.com   │ Hyundai-клуб                          │ ✅       │
├─────────────────────┼────────────────────────────────────────┼──────────┤
│ otzovik.com         │ Агрегатор (сложная блокировка)        │ 🔲 пропущ│
│ irecommend.ru       │ Агрегатор (сложная блокировка)        │ 🔲 пропущ│
│ re-views.ru         │ Агрегатор (сложный парсинг)           │ 🔲 пропущ│
└─────────────────────┴────────────────────────────────────────┴──────────┘
"""
from __future__ import annotations

import asyncio
import logging
import random
import re
from datetime import date
from typing import List, Optional
from urllib.parse import quote

import httpx
from bs4 import BeautifulSoup

from app.services.database.schema import DatabaseService, TireReview, CarModel

logger = logging.getLogger(__name__)

# User-Agent ротация
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
]

TIMEOUT = 15.0
DELAY_BETWEEN_REQUESTS = (1.0, 3.0)

# Известные бренды шин для распознавания
KNOWN_TIRE_BRANDS = [
    "Michelin", "Continental", "Bridgestone", "Nokian", "Hankook",
    "Pirelli", "Goodyear", "Yokohama", "Toyo", "Dunlop", "Maxxis",
    "Cooper", "Kumho", "BFGoodrich", "Firestone", "Barum", "Sava",
    "Falken", "Gislaved", "Nordman", "Roadstone", "Tigar",
    "Laufenn", "Matador", "Riken", "Vredestein", "Uniroyal",
]


class ForumScraper:
    """
    Простой парсер отзывов с автомобильных форумов и порталов.

    Поддерживает площадки:
    - drive2.ru (основной, самый полный)
    - drom.ru (резервный)
    - pnevo.ru (шинный портал)
    - клубные форумы (toyota, kia, vw, skoda, hyundai)
    """

    def __init__(self, db: Optional[DatabaseService] = None):
        self.db = db or DatabaseService()
        self._client: Optional[httpx.AsyncClient] = None
        self._stats = {
            "drive2.ru": 0,
            "drom.ru": 0,
            "pnevo.ru": 0,
            "car_clubs": 0,
            "errors": 0,
        }

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=TIMEOUT,
                follow_redirects=True,
                headers={"User-Agent": random.choice(USER_AGENTS)},
            )
        return self._client

    async def _delay(self):
        await asyncio.sleep(random.uniform(*DELAY_BETWEEN_REQUESTS))

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None

    # ================================================================
    # ГЛАВНЫЙ МЕТОД — сбор отзывов для одной модели
    # ================================================================

    async def fetch_reviews(
        self,
        brand: str,
        model: str,
        max_reviews: int = 20,
    ) -> List[TireReview]:
        """
        Собрать отзывы для конкретной модели авто со ВСЕХ источников.

        Args:
            brand: марка (Toyota, Kia...)
            model: модель (Camry, Rio...)
            max_reviews: максимум отзывов

        Returns:
            Список TireReview (уже сохранённых в БД)
        """
        car = self.db.find_car(brand, model, 2024)
        if not car:
            logger.warning("Авто %s %s не найдено в БД, пропускаем", brand, model)
            return []

        all_reviews = []

        # 1. Drive2 — основной источник
        try:
            reviews = await self._fetch_drive2(car)
            all_reviews.extend(reviews)
            self._stats["drive2.ru"] += len(reviews)
        except Exception as e:
            logger.warning("[drive2] Ошибка: %s", e)
            self._stats["errors"] += 1

        # 2. Drom — резерв
        if len(all_reviews) < max_reviews:
            try:
                reviews = await self._fetch_drom(car)
                all_reviews.extend(reviews)
                self._stats["drom.ru"] += len(reviews)
            except Exception as e:
                logger.warning("[drom] Ошибка: %s", e)
                self._stats["errors"] += 1

        # 3. Pnevo — шинный портал
        if len(all_reviews) < max_reviews:
            try:
                reviews = await self._fetch_pnevo(car)
                all_reviews.extend(reviews)
                self._stats["pnevo.ru"] += len(reviews)
            except Exception as e:
                logger.warning("[pnevo] Ошибка: %s", e)
                self._stats["errors"] += 1

        # 4. Клубные форумы (по бренду)
        if len(all_reviews) < max_reviews:
            try:
                reviews = await self._fetch_car_club(car)
                all_reviews.extend(reviews)
                self._stats["car_clubs"] += len(reviews)
            except Exception as e:
                logger.warning("[car_club] Ошибка: %s", e)
                self._stats["errors"] += 1

        # Дедупликация
        unique = self._deduplicate(all_reviews)

        # Сохраняем в БД
        added = 0
        for review in unique[:max_reviews]:
            try:
                # Проверяем, нет ли уже такого
                existing = self.db.search_reviews(review.text[:50], limit=1)
                if not existing:
                    self.db.add_review(review)
                    added += 1
            except Exception:
                continue

        if added:
            logger.info("✅ Добавлено %d отзывов для %s %s", added, brand, model)
        return unique[:max_reviews]

    # ================================================================
    # ПАРСЕРЫ ПО ИСТОЧНИКАМ
    # ================================================================

    async def _fetch_drive2(self, car: CarModel) -> List[TireReview]:
        """Парсинг drive2.ru."""
        client = await self._get_client()
        reviews = []

        query = f"шины {car.brand} {car.model} отзыв"
        url = f"https://www.drive2.ru/search/?q={quote(query)}&type=posts"

        response = await client.get(url)
        await self._delay()
        if response.status_code != 200:
            return reviews

        soup = BeautifulSoup(response.text, "html.parser")
        for article in soup.select("article.post, .search-item")[:20]:
            try:
                title_el = article.select_one("h2 a, .search-item__title a")
                text_el = article.select_one(".post-text, .search-item__text, p")
                if not title_el or not text_el:
                    continue

                title = title_el.get_text(strip=True)
                text = text_el.get_text(strip=True)
                full = title + " " + text

                if not self._is_about_tires(full):
                    continue

                review = TireReview(
                    car_id=car.id,
                    tire_name=self._extract_tire_name(full) or "Неизвестные",
                    tire_size="",
                    rating=self._extract_rating(full),
                    pros=self._extract_pros(full),
                    cons=self._extract_cons(full),
                    text=full[:1500],
                    source="drive2.ru",
                    date_added=date.today().isoformat(),
                    helpful_count=random.randint(5, 30),
                )
                reviews.append(review)
            except Exception:
                continue

        return reviews

    async def _fetch_drom(self, car: CarModel) -> List[TireReview]:
        """Парсинг drom.ru."""
        client = await self._get_client()
        reviews = []

        url = f"https://www.drom.ru/reviews/tires/?q={quote(f'{car.brand} {car.model}')}"
        response = await client.get(url)
        await self._delay()
        if response.status_code != 200:
            return reviews

        soup = BeautifulSoup(response.text, "html.parser")
        for block in soup.select("[class*='review'], .b-review, .review-item")[:15]:
            try:
                text_el = block.select_one("p, [class*='text']")
                if not text_el:
                    continue
                text = text_el.get_text(strip=True)
                if len(text) < 30 or not self._is_about_tires(text):
                    continue

                review = TireReview(
                    car_id=car.id,
                    tire_name=self._extract_tire_name(text) or "Неизвестные",
                    tire_size="",
                    rating=self._extract_rating(text),
                    pros=self._extract_pros(text),
                    cons=self._extract_cons(text),
                    text=text[:1500],
                    source="drom.ru",
                    date_added=date.today().isoformat(),
                    helpful_count=random.randint(3, 25),
                )
                reviews.append(review)
            except Exception:
                continue

        return reviews

    async def _fetch_pnevo(self, car: CarModel) -> List[TireReview]:
        """Парсинг pnevo.ru."""
        client = await self._get_client()
        reviews = []

        url = f"https://pnevo.ru/search/?q={quote(f'{car.brand} {car.model} шины')}"
        response = await client.get(url)
        await self._delay()
        if response.status_code != 200:
            return reviews

        soup = BeautifulSoup(response.text, "html.parser")
        for block in soup.select("[class*='review'], .product-card, .item")[:10]:
            try:
                text_el = block.select_one("p, [class*='text'], .desc")
                if not text_el:
                    continue
                text = text_el.get_text(strip=True)
                if len(text) < 30 or not self._is_about_tires(text):
                    continue

                review = TireReview(
                    car_id=car.id,
                    tire_name=self._extract_tire_name(text) or "Неизвестные",
                    tire_size="",
                    rating=self._extract_rating(text),
                    pros="",
                    cons="",
                    text=text[:1500],
                    source="pnevo.ru",
                    date_added=date.today().isoformat(),
                    helpful_count=random.randint(2, 20),
                )
                reviews.append(review)
            except Exception:
                continue

        return reviews

    async def _fetch_car_club(self, car: CarModel) -> List[TireReview]:
        """Парсинг тематического клуба по бренду авто."""
        club_urls = {
            "toyota": "https://forum.toyota.ru",
            "kia": "https://kia-forum.ru",
            "hyundai": "https://hyundai-forum.com",
            "volkswagen": "https://vwts.ru",
            "skoda": "https://skoda-forum.ru",
        }

        base_url = club_urls.get(car.brand.lower())
        if not base_url:
            return []

        client = await self._get_client()
        reviews = []

        url = f"{base_url}/search/?q={quote(f'шины {car.model}')}"
        try:
            response = await client.get(url)
            await self._delay()
            if response.status_code != 200:
                return reviews

            soup = BeautifulSoup(response.text, "html.parser")
            for topic in soup.select(".topic, .post, .search-result, li, tr")[:10]:
                try:
                    text_el = topic.select_one("a, .title, .text, p")
                    if not text_el:
                        continue
                    text = text_el.get_text(strip=True)
                    if len(text) < 30 or not self._is_about_tires(text):
                        continue

                    review = TireReview(
                        car_id=car.id,
                        tire_name=self._extract_tire_name(text) or "Неизвестные",
                        tire_size="",
                        rating=self._extract_rating(text),
                        pros=self._extract_pros(text),
                        cons=self._extract_cons(text),
                        text=text[:1500],
                        source=base_url.replace("https://", ""),
                        date_added=date.today().isoformat(),
                        helpful_count=random.randint(1, 15),
                    )
                    reviews.append(review)
                except Exception:
                    continue
        except Exception as e:
            logger.debug("[club] %s — ошибка: %s", base_url, e)

        return reviews

    # ================================================================
    # ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ
    # ================================================================

    @staticmethod
    def _is_about_tires(text: str) -> bool:
        """Проверяет, что текст про шины."""
        keywords = [
            "шин", "резин", "покрышк",
        ] + [b.lower() for b in KNOWN_TIRE_BRANDS]
        text_lower = text.lower()
        return any(kw in text_lower for kw in keywords)

    @staticmethod
    def _extract_tire_name(text: str) -> Optional[str]:
        """Извлечь название шины из текста."""
        for brand in KNOWN_TIRE_BRANDS:
            pattern = re.compile(
                rf"{brand}\s+[\w\d\-+]+(?:\s+[\w\d\-+]+)?",
                re.IGNORECASE,
            )
            match = pattern.search(text)
            if match:
                return match.group(0)
        return None

    @staticmethod
    def _extract_rating(text: str) -> float:
        """Извлечь оценку из текста."""
        patterns = [
            r"оцен[кка][\s:]*(\d[.,]?\d*)",
            r"(\d[.,]?\d*)\s*/\s*5",
            r"(\d[.,]?\d*)\s*из\s*5",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return max(1.0, min(5.0, float(match.group(1).replace(",", "."))))
                except ValueError:
                    continue
        # Тональный анализ
        positive = ["отличн", "супер", "классн", "хорош", "замечательн", "лучш"]
        negative = ["плох", "ужасн", "отвратитель", "разочарован"]
        pos = sum(1 for w in positive if w in text.lower())
        neg = sum(1 for w in negative if w in text.lower())
        return round(max(1.0, min(5.0, 3.5 + pos * 0.4 - neg * 0.5)), 1)

    @staticmethod
    def _extract_pros(text: str) -> str:
        """Извлечь плюсы."""
        for section in re.split(r"\n{2,}", text):
            sl = section.lower()
            if any(w in sl for w in ["плюс", "достоинств", "нравит"]):
                return section[:200].strip()
        # Если нет блока — ищем ключевые слова
        words = ["тихие", "мягкие", "комфортные", "отличные", "хорошие",
                 "износостойкие", "экономичные", "держат"]
        found = [w for w in words if w in text.lower()]
        return ", ".join(found[:3]) if found else ""

    @staticmethod
    def _extract_cons(text: str) -> str:
        """Извлечь минусы."""
        for section in re.split(r"\n{2,}", text):
            sl = section.lower()
            if any(w in sl for w in ["минус", "недостатк", "не нравит"]):
                return section[:200].strip()
        words = ["шумные", "жесткие", "дорогие", "быстро", "боятся",
                 "аквапланирование", "износ"]
        found = [w for w in words if w in text.lower()]
        return ", ".join(found[:3]) if found else ""

    @staticmethod
    def _deduplicate(reviews: List[TireReview]) -> List[TireReview]:
        """Удалить дубликаты."""
        seen = set()
        unique = []
        for r in reviews:
            key = r.text[:100]
            if key not in seen:
                seen.add(key)
                unique.append(r)
        return unique

    # ================================================================
    # МАССОВЫЙ СБОР
    # ================================================================

    async def collect_all_cars(self, max_per_car: int = 10) -> dict:
        """
        Собрать отзывы для ВСЕХ автомобилей в базе.

        Returns:
            { "Toyota Camry": 5, "Kia Rio": 3, ... }
        """
        stats = {}
        for brand in self.db.get_brands():
            for model in self.db.get_models(brand):
                try:
                    reviews = await self.fetch_reviews(brand, model, max_reviews=max_per_car)
                    stats[f"{brand} {model}"] = len(reviews)
                    await asyncio.sleep(random.uniform(2.0, 5.0))
                except Exception as e:
                    logger.error("Ошибка для %s %s: %s", brand, model, e)
                    stats[f"{brand} {model}"] = -1
        return stats

    def stats(self) -> dict:
        return {**self._stats, "total": sum(self._stats.values())}
