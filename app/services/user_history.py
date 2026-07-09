"""Сервис персонализации на основе истории запросов пользователя.

Хранит и анализирует историю запросов пользователя, чтобы:
1. При повторном обращении AI помнил предыдущие предпочтения
2. Учитывал предыдущие покупки (через партнёрские ссылки)
3. Не спрашивал одно и то же

Данные хранятся в Redis (быстрый доступ) и дублируются в SQLite (постоянное хранение).
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field, asdict

from app.services.cache import get_cache, RedisCache
from app.services.database.schema import DatabaseService
from app.config.settings import settings

logger = logging.getLogger(__name__)


@dataclass
class UserProfile:
    """Профиль пользователя с историей."""
    user_id: str
    first_seen: str = ""
    last_seen: str = ""
    total_queries: int = 0

    # Предпочтения (последние использованные значения)
    preferred_brand: str = ""
    preferred_model: str = ""
    preferred_driving_style: str = "comfort"
    preferred_season: str = ""
    preferred_budget: Optional[int] = None

    # Что уже покупал (через партнёрские ссылки)
    purchased_tires: List[str] = field(default_factory=list)

    # Последние запросы
    recent_queries: List[dict] = field(default_factory=list, maxlen=10)


class UserHistoryService:
    """
    Сервис персонализации.

    Хранит данные в:
    - Redis (быстрый кэш для текущей сессии)
    - SQLite (постоянное хранение)
    """

    REDIS_PREFIX = "user:"

    def __init__(self):
        self.cache = get_cache()
        self.db = DatabaseService()

    # ================================================================
    # Получение / сохранение профиля
    # ================================================================

    async def get_profile(self, user_id: str) -> UserProfile:
        """Получить профиль пользователя (из Redis или SQLite)."""
        # Пробуем из Redis (быстрый путь)
        cached = await self.cache.get_json(f"{self.REDIS_PREFIX}{user_id}")
        if cached:
            return UserProfile(**cached)

        # Ищем в SQLite
        profile = self._load_from_db(user_id)
        if not profile:
            profile = UserProfile(user_id=user_id, first_seen=date.today().isoformat())

        # Кэшируем в Redis
        await self.cache.set_json(
            f"{self.REDIS_PREFIX}{user_id}",
            asdict(profile),
            ttl=86400,  # на сутки
        )
        return profile

    async def save_profile(self, profile: UserProfile):
        """Сохранить профиль пользователя."""
        # В Redis (быстрый доступ)
        await self.cache.set_json(
            f"{self.REDIS_PREFIX}{profile.user_id}",
            asdict(profile),
            ttl=86400,
        )
        # В SQLite (постоянное хранение)
        self._save_to_db(profile)

    async def update_query(
        self,
        user_id: str,
        brand: str,
        model: str,
        driving_style: str,
        season: Optional[str] = None,
        budget: Optional[int] = None,
    ):
        """Обновить историю пользователя после запроса."""
        profile = await self.get_profile(user_id)

        # Обновляем счётчики и даты
        profile.last_seen = date.today().isoformat()
        profile.total_queries += 1

        # Сохраняем последние предпочтения
        if brand:
            profile.preferred_brand = brand
        if model:
            profile.preferred_model = model
        if driving_style:
            profile.preferred_driving_style = driving_style
        if season:
            profile.preferred_season = season
        if budget:
            profile.preferred_budget = budget

        # Добавляем в историю запросов
        query_entry = {
            "timestamp": datetime.now().isoformat(),
            "brand": brand,
            "model": model,
            "driving_style": driving_style,
            "season": season,
            "budget": budget,
        }
        profile.recent_queries.append(query_entry)
        if len(profile.recent_queries) > 10:
            profile.recent_queries = profile.recent_queries[-10:]

        await self.save_profile(profile)
        logger.debug("История обновлена для user=%s: %s %s", user_id, brand, model)

    async def add_purchase(self, user_id: str, tire_name: str):
        """Записать покупку пользователя."""
        profile = await self.get_profile(user_id)
        if tire_name not in profile.purchased_tires:
            profile.purchased_tires.append(tire_name)
        await self.save_profile(profile)
        logger.info("💳 Покупка сохранена: user=%s купил %s", user_id, tire_name)

    # ================================================================
    # Обогащение промпта для DeepSeek
    # ================================================================

    async def build_history_prompt(self, user_id: str) -> str:
        """
        Сформировать строку с историей пользователя для подстановки в промпт AI.

        Пример результата:
            "Ранее пользователь искал: Toyota Camry (комфорт, лето). Покупал: Michelin Pilot Sport 4."
        """
        profile = await self.get_profile(user_id)

        parts = []

        if profile.total_queries > 0:
            # Последние 3 запроса
            recent = profile.recent_queries[-3:]
            if recent:
                queries_str = []
                for q in recent:
                    q_str = f"{q['brand']} {q['model']}"
                    if q.get("season"):
                        q_str += f" ({q['season']})"
                    queries_str.append(q_str)
                parts.append(f"Ранее пользователь искал: {', '.join(queries_str)}.")

        if profile.purchased_tires:
            parts.append(f"Ранее покупал: {', '.join(profile.purchased_tires)}.")

        if profile.preferred_driving_style:
            style_map = {
                "comfort": "предпочитает комфорт",
                "sport": "предпочитает спортивный стиль",
                "economy": "предпочитает экономию",
            }
            style_str = style_map.get(profile.preferred_driving_style, "")
            if style_str:
                parts.append(f"Пользователь {style_str}.")

        if profile.preferred_budget:
            parts.append(f"Бюджет до {profile.preferred_budget} ₽.")

        return "\n".join(parts)

    # ================================================================
    # SQLite (персистентность)
    # ================================================================

    def _load_from_db(self, user_id: str) -> Optional[UserProfile]:
        """Загрузить профиль из SQLite."""
        try:
            with self.db._conn() as conn:
                row = conn.execute(
                    "SELECT * FROM user_profiles WHERE user_id = ?",
                    (user_id,)
                ).fetchone()
                if row:
                    profile = UserProfile(
                        user_id=row["user_id"],
                        first_seen=row["first_seen"] or "",
                        last_seen=row["last_seen"] or "",
                        total_queries=row["total_queries"] or 0,
                        preferred_brand=row["preferred_brand"] or "",
                        preferred_model=row["preferred_model"] or "",
                        preferred_driving_style=row["preferred_driving_style"] or "comfort",
                        preferred_season=row["preferred_season"] or "",
                        preferred_budget=row["preferred_budget"],
                    )
                    # Загружаем покупки
                    purchases = conn.execute(
                        "SELECT tire_name FROM user_purchases WHERE user_id = ? ORDER BY purchased_at DESC",
                        (user_id,)
                    ).fetchall()
                    profile.purchased_tires = [p["tire_name"] for p in purchases]

                    # Загружаем историю запросов
                    queries = conn.execute(
                        "SELECT * FROM user_queries WHERE user_id = ? ORDER BY queried_at DESC LIMIT 10",
                        (user_id,)
                    ).fetchall()
                    for q in reversed(queries):
                        profile.recent_queries.append({
                            "timestamp": q["queried_at"],
                            "brand": q["brand"],
                            "model": q["model"],
                            "driving_style": q["driving_style"],
                            "season": q["season"],
                            "budget": q["budget"],
                        })

                    return profile
        except Exception as e:
            logger.warning("Ошибка загрузки профиля %s: %s", user_id, e)
        return None

    def _save_to_db(self, profile: UserProfile):
        """Сохранить профиль в SQLite."""
        try:
            with self.db._conn() as conn:
                conn.execute(
                    """INSERT OR REPLACE INTO user_profiles
                       (user_id, first_seen, last_seen, total_queries,
                        preferred_brand, preferred_model, preferred_driving_style,
                        preferred_season, preferred_budget)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (profile.user_id, profile.first_seen, profile.last_seen,
                     profile.total_queries,
                     profile.preferred_brand, profile.preferred_model,
                     profile.preferred_driving_style,
                     profile.preferred_season, profile.preferred_budget)
                )

                # Сохраняем последние запросы
                for q in profile.recent_queries[-3:]:
                    conn.execute(
                        """INSERT INTO user_queries
                           (user_id, brand, model, driving_style, season, budget, queried_at)
                           VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (profile.user_id, q.get("brand"), q.get("model"),
                         q.get("driving_style"), q.get("season"),
                         q.get("budget"), q.get("timestamp"))
                    )

        except Exception as e:
            logger.warning("Ошибка сохранения профиля %s: %s", profile.user_id, e)


# ================================================================
# ДОБАВЛЕНИЕ ТАБЛИЦ В БАЗУ (миграция)
# ================================================================

MIGRATION_SQL = """
CREATE TABLE IF NOT EXISTS user_profiles (
    user_id TEXT PRIMARY KEY,
    first_seen TEXT,
    last_seen TEXT,
    total_queries INTEGER DEFAULT 0,
    preferred_brand TEXT DEFAULT '',
    preferred_model TEXT DEFAULT '',
    preferred_driving_style TEXT DEFAULT 'comfort',
    preferred_season TEXT DEFAULT '',
    preferred_budget INTEGER
);

CREATE TABLE IF NOT EXISTS user_queries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    brand TEXT,
    model TEXT,
    driving_style TEXT,
    season TEXT,
    budget INTEGER,
    queried_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES user_profiles(user_id)
);

CREATE TABLE IF NOT EXISTS user_purchases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    tire_name TEXT NOT NULL,
    purchased_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES user_profiles(user_id)
);

CREATE INDEX IF NOT EXISTS idx_user_queries_user_id ON user_queries(user_id);
CREATE INDEX IF NOT EXISTS idx_user_purchases_user_id ON user_purchases(user_id);
"""


def run_migration():
    """Запустить миграцию для добавления таблиц персонализации."""
    db = DatabaseService()
    with db._conn() as conn:
        conn.executescript(MIGRATION_SQL)
    logger.info("✅ Миграция персонализации выполнена")
