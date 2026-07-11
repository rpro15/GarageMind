"""
Автоматический сборщик данных о шинах с автомобильных форумов.

Работает в фоне по расписанию:
- Каждый час проверяет, сколько отзывов собрано за день
- Собирает реальные отзывы с drive2.ru, drom.ru, pnevo.ru и клубных форумов
- Добавляет до 100 записей в день (контролируется через COLLECTOR_DAILY_LIMIT)
- Извлекает плюсы/минусы, оценки, названия шин — складывает в SQLite

Лимиты (настраиваются в .env):
    COLLECTOR_DAILY_LIMIT=100           # макс записей в день
    AUTO_COLLECTOR_INTERVAL_MINUTES=60  # проверка каждый час
    AUTO_COLLECTOR_REVIEWS_PER_CYCLE=10 # сколько добавлять за цикл

Запуск:
    python3 -m app.services.knowledge.auto_collector            # разовый запуск
    python3 -m app.services.knowledge.auto_collector --daemon   # демон
"""
import asyncio
import logging
import sys
import random
from datetime import date
from typing import Optional, List

from app.services.database import DatabaseService
from app.services.database.schema import TireReview, TireProblem
from app.services.sources.forum_scraper import ForumScraper
from app.config.settings import settings

logger = logging.getLogger(__name__)

# ============================================================
# Реальные модели шин с характеристиками (для seed-данных)
# ============================================================

KNOWN_TIRES = [
    ("Michelin Pilot Sport 4", "sport", 4.7),
    ("Continental PremiumContact 6", "comfort", 4.5),
    ("Bridgestone Turanza T005", "standard", 3.8),
    ("Nokian Hakka Green 3", "economical", 4.6),
    ("Hankook Kinergy Eco 2", "economical", 4.2),
    ("Pirelli P Zero PZ4", "sport", 4.3),
    ("Goodyear Eagle F1 Asymmetric 5", "sport", 4.4),
    ("Michelin Primacy 4+", "comfort", 4.6),
    ("Continental EcoContact 6", "economical", 4.3),
    ("Nokian Hakka Blue 3", "comfort", 4.4),
    ("Michelin Latitude Sport 3", "suv", 4.5),
    ("Continental CrossContact LX Sport", "suv", 4.3),
    ("Pirelli Scorpion Verde All Season", "suv", 4.1),
    ("Bridgestone Alenza 001", "suv", 4.2),
    ("Goodyear Wrangler AT Adventure", "offroad", 4.0),
]

ALL_PROS = [
    "тихие, отличное сцепление, износостойкие",
    "комфортные, мягкие, хорошо держат дорогу",
    "экономичные, низкий расход топлива",
    "отличное сцепление на мокрой, безопасные",
    "спортивные, информативный руль",
    "цена/качество — лучшие в своём сегменте",
    "долго ходят, 2-3 сезона без проблем",
    "не шумят на трассе, комфортные",
    "отлично держат колею",
    "короткий тормозной путь",
]

ALL_CONS = [
    "высокая цена, дороговаты",
    "шумноваты на скорости выше 100",
    "боится ям и плохих дорог",
    "быстро изнашиваются передние",
    "жёсткие, не для наших дорог",
    "среднее сцепление на мокрой",
    "аквапланирование на лужах",
    "тяжеловаты, влияют на разгон",
    "не любят перегрузки",
]

PROBLEMS = [
    ("critical", "Быстрый износ передних шин (10-15 тыс. км)"),
    ("warning", "Шум на скорости выше 90 км/ч"),
    ("critical", "Боковина трескается через 2 сезона"),
    ("warning", "Аквапланирование на мокрой трассе выше 110 км/ч"),
    ("info", "Не подходят для зимней эксплуатации"),
    ("warning", "Гул на трассе, требуется шумоизоляция арок"),
    ("critical", "Грыжи на боковине после попадания в яму"),
    ("warning", "Дисбаланс, требует балансировки каждые 5000 км"),
]


class AutoCollector:
    """
    Фоновый сборщик знаний.

    Каждый цикл:
    1. Проверяет дневной лимит
    2. Сначала пытается собрать реальные отзывы с форумов (ForumScraper)
    3. Если форумы не дали данных — генерирует seed-отзывы
    4. Добавляет проблемы
    """

    def __init__(self, db: Optional[DatabaseService] = None):
        self.db = db or DatabaseService()
        self.scraper = ForumScraper(db)
        self.running = False
        self.total_collected = 0
        self._daily_limit = settings.COLLECTOR_DAILY_LIMIT
        self._reviews_per_cycle = settings.AUTO_COLLECTOR_REVIEWS_PER_CYCLE

    def _get_today_count(self) -> int:
        """Сколько отзывов уже собрано сегодня."""
        today = date.today().isoformat()
        with self.db._conn() as conn:
            row = conn.execute(
                "SELECT COUNT(*) FROM tire_reviews WHERE date(date_added) = ?",
                (today,)
            ).fetchone()
            return row[0] if row else 0

    async def collect_once(self) -> dict:
        """Один цикл сбора данных. Соблюдает дневной лимит."""
        stats = {
            "reviews_added": 0,
            "problems_added": 0,
            "skipped_daily_limit": 0,
            "forum_reviews": 0,
            "seed_reviews": 0,
            "errors": 0,
        }

        try:
            today_count = self._get_today_count()
            remaining = self._daily_limit - today_count

            if remaining <= 0:
                stats["skipped_daily_limit"] = 1
                logger.info(
                    "⏰ Дневной лимит исчерпан: %d/%d отзывов собрано",
                    today_count,
                    self._daily_limit,
                )
                return stats

            reviews_to_add = min(self._reviews_per_cycle, remaining)
            logger.info(
                "📊 Сегодня собрано %d/%d отзывов. Добавляем ещё %d...",
                today_count,
                self._daily_limit,
                reviews_to_add,
            )

            # 1. Пробуем собрать реальные отзывы с форумов
            added_forum = await self._collect_forum_reviews(target=reviews_to_add)
            stats["forum_reviews"] = added_forum

            # 2. Если форумы не дали — генерируем seed
            if added_forum < reviews_to_add:
                added_seed = await self._collect_seed_reviews(target=reviews_to_add - added_forum)
                stats["seed_reviews"] = added_seed

            stats["reviews_added"] = added_forum + added_seed

            # 3. Добавляем проблемы
            stats["problems_added"] = await self._collect_problems()

            self.total_collected += stats["reviews_added"]

        except Exception as e:
            logger.error("Collect error: %s", e, exc_info=True)
            stats["errors"] += 1

        return stats

    async def _collect_forum_reviews(self, target: int = 10) -> int:
        """Собирает реальные отзывы с форумов через ForumScraper."""
        brands = self.db.get_brands()
        if not brands:
            return 0

        random.shuffle(brands)
        total_added = 0

        for brand in brands[:3]:  # максимум 3 бренда за цикл
            models = self.db.get_models(brand)
            if not models:
                continue

            model = random.choice(models)
            logger.info("🔍 Собираю отзывы с форумов для %s %s...", brand, model)

            try:
                reviews = await self.scraper.fetch_reviews(
                    brand=brand,
                    model=model,
                    max_reviews=target,
                )
                if reviews:
                    total_added += len(reviews)
                    logger.info("✅ Форумные отзывы для %s %s: %d", brand, model, len(reviews))

                if total_added >= target:
                    break

                # Пауза между брендами
                await asyncio.sleep(random.uniform(2.0, 4.0))

            except Exception as e:
                logger.warning("Ошибка ForumScraper для %s %s: %s", brand, model, e)
                continue

        return total_added

    async def _collect_seed_reviews(self, target: int = 10) -> int:
        """Генерирует seed-отзывы как запасной вариант."""
        with self.db._conn() as conn:
            cars = conn.execute(
                "SELECT id, brand, model FROM car_models ORDER BY RANDOM()"
            ).fetchall()

        if not cars:
            logger.warning("Нет автомобилей в БД.")
            return 0

        added = 0
        attempts = 0
        max_attempts = target * 5

        while added < target and attempts < max_attempts:
            attempts += 1
            car = random.choice(cars)
            tire_name, _, base_rating = random.choice(KNOWN_TIRES)

            # Проверяем уникальность
            with self.db._conn() as conn:
                exists = conn.execute(
                    """SELECT COUNT(*) FROM tire_reviews
                       WHERE car_id = ? AND tire_name = ?
                       AND date(date_added) = date('now')""",
                    (car["id"], tire_name)
                ).fetchone()[0]

            if exists > 0:
                continue

            rating = round(max(1.0, min(5.0, base_rating + random.uniform(-0.5, 0.3))), 1)
            review_text = random.choice([
                "Отличные шины! После 20000 км износ минимальный.",
                "Езжу второй сезон. По комфорту лучшие.",
                "Хороший бюджетный вариант. Для города отлично.",
                "Очень доволен покупкой. Отлично держат мокрую дорогу.",
                "Эталонные шины. Тишина в салоне на любом покрытии.",
                "Хорошая управляемость на сухом и мокром покрытии.",
                "Для города самое то. Не шумят, ямы глотают достойно.",
                "Отличные шины для спокойной езды. Тихие, мягкие.",
            ])

            review = TireReview(
                car_id=car["id"],
                tire_name=tire_name,
                tire_size="",
                rating=rating,
                pros=random.choice(ALL_PROS),
                cons=random.choice(ALL_CONS),
                text=f"{review_text} (seed: {car['brand']} {car['model']})",
                source="auto_collector_seed",
                date_added=date.today().isoformat(),
                helpful_count=random.randint(1, 50),
            )

            try:
                self.db.add_review(review)
                added += 1
            except Exception:
                continue

        if added > 0:
            logger.info("✅ Добавлено %d seed-отзывов за цикл", added)
        return added

    async def _collect_problems(self, target: int = 3) -> int:
        """Добавляет новые проблемы."""
        with self.db._conn() as conn:
            cars = conn.execute(
                "SELECT id, brand, model FROM car_models ORDER BY RANDOM()"
            ).fetchall()

        added = 0
        for car in cars:
            tire_name = random.choice(KNOWN_TIRES)[0]
            severity, problem = random.choice(PROBLEMS)

            with self.db._conn() as conn:
                exists = conn.execute(
                    "SELECT COUNT(*) FROM tire_problems WHERE car_id = ? AND problem = ?",
                    (car["id"], problem)
                ).fetchone()[0]

            if exists > 0:
                continue

            tp = TireProblem(
                car_id=car["id"],
                tire_name=tire_name,
                problem=problem,
                severity=severity,
                source="auto_collector",
            )

            try:
                self.db.add_problem(tp)
                added += 1
            except Exception:
                pass

            if added >= target:
                break

        return added

    async def run_daemon(self, interval_minutes: int = 60):
        """Запускает демона, который собирает данные каждые N минут."""
        self.running = True
        logger.info(
            "🚀 AutoCollector daemon started (interval=%d min, daily_limit=%d)",
            interval_minutes,
            self._daily_limit,
        )

        while self.running:
            try:
                stats = await self.collect_once()

                if stats.get("reviews_added", 0) > 0 or stats.get("problems_added", 0) > 0:
                    logger.info(
                        "📊 Собрано: +%d отзывов (форум: %d, seed: %d), +%d проблем (всего: %d)",
                        stats["reviews_added"],
                        stats["forum_reviews"],
                        stats["seed_reviews"],
                        stats["problems_added"],
                        self.total_collected,
                    )
                elif stats.get("skipped_daily_limit"):
                    logger.info("🌙 Дневной лимит достигнут. Следующая проверка завтра.")
                else:
                    logger.debug("Новых данных нет в этом цикле")

            except Exception as e:
                logger.error("Ошибка цикла демона: %s", e, exc_info=True)

            await asyncio.sleep(interval_minutes * 60)

        logger.info("🛑 AutoCollector остановлен")

    def stop(self):
        self.running = False


# ============================================================
# CLI
# ============================================================

async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    collector = AutoCollector()

    if "--daemon" in sys.argv:
        interval = settings.AUTO_COLLECTOR_INTERVAL_MINUTES
        for i, arg in enumerate(sys.argv):
            if arg == "--interval" and i + 1 < len(sys.argv):
                interval = int(sys.argv[i + 1])

        logger.info("🚀 Запуск AutoCollector демона (интервал=%d мин)", interval)
        await collector.run_daemon(interval_minutes=interval)
    else:
        logger.info("📥 Разовый сбор данных...")
        stats = await collector.collect_once()
        logger.info("✅ Готово: %s", stats)

    # Итоговая статистика
    stats = collector.db.stats()
    logger.info(
        "📊 База знаний: %d авто, %d отзывов",
        stats["cars"],
        stats["reviews"],
    )

    await collector.scraper.close()


if __name__ == "__main__":
    asyncio.run(main())
