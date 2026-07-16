"""Схема и инициализация SQLite базы знаний GarageMind."""
import sqlite3
import os
import logging
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# Путь к БД: сначала переменная окружения, потом стандартный путь
_DEFAULT_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "data", "garage_mind.db")
DB_PATH = os.environ.get("GARAGE_MIND_DB_PATH", _DEFAULT_DB)


# ============================================================
# Domain models
# ============================================================

@dataclass
class CarModel:
    """Модель автомобиля с характеристиками."""
    id: int = 0
    brand: str = ""
    model: str = ""
    year_start: int = 2000
    year_end: int = 2026
    tire_sizes: str = ""          # "205/55R16,215/60R17"
    wheel_pcd: str = ""           # "5x114.3"
    wheel_et: str = ""            # "45"
    wheel_dia: str = ""           # "60.1"
    bolt_thread: str = ""         # "M12x1.5"
    bolt_type: str = ""           # "bolt" | "nut"
    popular_tires: str = ""       # "Michelin Pilot Sport 4, Continental..."

    @property
    def tire_sizes_list(self) -> List[str]:
        return [s.strip() for s in self.tire_sizes.split(",") if s.strip()]


@dataclass
class TireReview:
    """Отзыв владельца о шинах."""
    id: int = 0
    car_id: int = 0
    tire_name: str = ""
    tire_size: str = ""
    rating: float = 0.0
    pros: str = ""                # "тихие, износостойкие"
    cons: str = ""                # "дорогие"
    text: str = ""
    source: str = ""              # "drive2.ru"
    date_added: str = ""
    helpful_count: int = 0


@dataclass
class TireProblem:
    """Известные проблемы с шинами."""
    id: int = 0
    car_id: int = 0
    tire_name: str = ""
    problem: str = ""
    severity: str = "warning"     # "info" | "warning" | "critical"
    source: str = ""


@dataclass
class TireSpec:
    """Технические характеристики шины."""
    id: int = 0
    name: str = ""
    category: str = ""            # "sport", "comfort", "winter"...
    size: str = ""
    load_index: str = ""
    speed_index: str = ""
    noise_db: float = 0.0
    fuel_class: str = ""
    wet_grip: str = ""
    tread_depth: float = 0.0
    runflat: bool = False
    ev_compatible: bool = False


# ============================================================
# DatabaseService
# ============================================================

class DatabaseService:
    """
    Единый сервис для работы с SQLite базой знаний.
    Все методы синхронные (SQLite не требует async).
    Использует WAL-журнал + кэш страниц для производительности.
    """

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = ':memory:' if db_path == ':memory:' else db_path
        if db_path != ':memory:':
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()

    @contextmanager
    def _conn(self):
        """Контекстный менеджер подключения к БД (внутренний)."""
        with self.get_conn() as conn:
            yield conn

    @contextmanager
    def get_conn(self):
        """Публичный контекстный менеджер подключения к БД с оптимизациями."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA cache_size=-8000")  # 8MB cache
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA temp_store=MEMORY")
        conn.execute("PRAGMA mmap_size=268435456")  # 256MB mmap
        conn.execute("PRAGMA page_size=4096")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    # ============================================================
    # INIT
    # ============================================================

    def _init_db(self):
        """Создаёт таблицы, если их нет."""
        with self._conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS car_models (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    brand TEXT NOT NULL,
                    model TEXT NOT NULL,
                    year_start INTEGER DEFAULT 2000,
                    year_end INTEGER DEFAULT 2026,
                    tire_sizes TEXT DEFAULT '',
                    wheel_pcd TEXT DEFAULT '',
                    wheel_et TEXT DEFAULT '',
                    wheel_dia TEXT DEFAULT '',
                    bolt_thread TEXT DEFAULT '',
                    bolt_type TEXT DEFAULT 'bolt',
                    popular_tires TEXT DEFAULT '',
                    UNIQUE(brand, model, year_start, year_end)
                );

                CREATE TABLE IF NOT EXISTS tire_reviews (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    car_id INTEGER NOT NULL,
                    tire_name TEXT NOT NULL,
                    tire_size TEXT DEFAULT '',
                    rating REAL DEFAULT 0.0,
                    pros TEXT DEFAULT '',
                    cons TEXT DEFAULT '',
                    text TEXT DEFAULT '',
                    source TEXT DEFAULT '',
                    date_added TEXT DEFAULT (datetime('now')),
                    helpful_count INTEGER DEFAULT 0,
                    FOREIGN KEY (car_id) REFERENCES car_models(id)
                );

                CREATE TABLE IF NOT EXISTS tire_problems (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    car_id INTEGER NOT NULL,
                    tire_name TEXT NOT NULL,
                    problem TEXT NOT NULL,
                    severity TEXT DEFAULT 'warning',
                    source TEXT DEFAULT '',
                    FOREIGN KEY (car_id) REFERENCES car_models(id)
                );

                CREATE TABLE IF NOT EXISTS tire_specs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    category TEXT DEFAULT '',
                    size TEXT DEFAULT '',
                    load_index TEXT DEFAULT '',
                    speed_index TEXT DEFAULT '',
                    noise_db REAL DEFAULT 0.0,
                    fuel_class TEXT DEFAULT '',
                    wet_grip TEXT DEFAULT '',
                    tread_depth REAL DEFAULT 0.0,
                    runflat INTEGER DEFAULT 0,
                    ev_compatible INTEGER DEFAULT 0
                );

                -- Индексы для быстрого поиска
                CREATE INDEX IF NOT EXISTS idx_car_models_brand ON car_models(brand);
                CREATE INDEX IF NOT EXISTS idx_car_models_model ON car_models(model);
                CREATE INDEX IF NOT EXISTS idx_tire_reviews_car_id ON tire_reviews(car_id);
                CREATE INDEX IF NOT EXISTS idx_tire_reviews_tire_name ON tire_reviews(tire_name);
                CREATE INDEX IF NOT EXISTS idx_tire_problems_car_id ON tire_problems(car_id);
                CREATE INDEX IF NOT EXISTS idx_tire_specs_category ON tire_specs(category);
            """)
        logger.info("Database initialized: %s", self.db_path)

    # ============================================================
    # CAR MODELS
    # ============================================================

    def add_car(self, car: CarModel) -> int:
        """Добавить модель авто. Возвращает ID."""
        with self._conn() as conn:
            cur = conn.execute(
                """INSERT OR IGNORE INTO car_models
                   (brand, model, year_start, year_end, tire_sizes, wheel_pcd,
                    wheel_et, wheel_dia, bolt_thread, bolt_type, popular_tires)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (car.brand, car.model, car.year_start, car.year_end,
                 car.tire_sizes, car.wheel_pcd, car.wheel_et, car.wheel_dia,
                 car.bolt_thread, car.bolt_type, car.popular_tires)
            )
            return cur.lastrowid or 0

    def find_car(self, brand: str, model: str, year: int) -> Optional[CarModel]:
        """Найти авто по марке, модели и году."""
        with self._conn() as conn:
            row = conn.execute(
                """SELECT * FROM car_models
                   WHERE LOWER(brand) = LOWER(?)
                     AND LOWER(model) = LOWER(?)
                     AND year_start <= ?
                     AND year_end >= ?
                   LIMIT 1""",
                (brand, model, year, year)
            ).fetchone()
            return CarModel(**dict(row)) if row else None

    def get_brands(self) -> List[str]:
        """Список всех брендов."""
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT DISTINCT brand FROM car_models ORDER BY brand"
            ).fetchall()
            return [r["brand"] for r in rows]

    def get_models(self, brand: str) -> List[str]:
        """Список моделей для бренда."""
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT DISTINCT model FROM car_models WHERE LOWER(brand) = LOWER(?) ORDER BY model",
                (brand,)
            ).fetchall()
            return [r["model"] for r in rows]

    def car_count(self) -> int:
        with self._conn() as conn:
            return conn.execute("SELECT COUNT(*) FROM car_models").fetchone()[0]

    # ============================================================
    # REVIEWS
    # ============================================================

    def add_review(self, review: TireReview) -> int:
        """Добавить отзыв."""
        with self._conn() as conn:
            cur = conn.execute(
                """INSERT INTO tire_reviews
                   (car_id, tire_name, tire_size, rating, pros, cons, text, source, date_added, helpful_count)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), ?)""",
                (review.car_id, review.tire_name, review.tire_size,
                 review.rating, review.pros, review.cons, review.text,
                 review.source, review.helpful_count)
            )
            return cur.lastrowid or 0

    def get_reviews(self, car_id: int, tire_name: Optional[str] = None, limit: int = 10) -> List[TireReview]:
        """Получить отзывы для авто."""
        with self._conn() as conn:
            if tire_name:
                rows = conn.execute(
                    """SELECT * FROM tire_reviews
                       WHERE car_id = ? AND LOWER(tire_name) LIKE ?
                       ORDER BY helpful_count DESC LIMIT ?""",
                    (car_id, f"%{tire_name.lower()}%", limit)
                ).fetchall()
            else:
                rows = conn.execute(
                    """SELECT * FROM tire_reviews
                       WHERE car_id = ?
                       ORDER BY helpful_count DESC LIMIT ?""",
                    (car_id, limit)
                ).fetchall()
            return [TireReview(**dict(r)) for r in rows]

    def search_reviews(self, query: str, limit: int = 20) -> List[TireReview]:
        """Полнотекстовый поиск по отзывам (LIKE)."""
        with self._conn() as conn:
            rows = conn.execute(
                """SELECT * FROM tire_reviews
                   WHERE text LIKE ? OR tire_name LIKE ? OR pros LIKE ? OR cons LIKE ?
                   ORDER BY helpful_count DESC LIMIT ?""",
                (f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%", limit)
            ).fetchall()
            return [TireReview(**dict(r)) for r in rows]

    def review_count(self) -> int:
        with self._conn() as conn:
            return conn.execute("SELECT COUNT(*) FROM tire_reviews").fetchone()[0]

    # ============================================================
    # PROBLEMS
    # ============================================================

    def add_problem(self, problem: TireProblem) -> int:
        with self._conn() as conn:
            cur = conn.execute(
                """INSERT INTO tire_problems (car_id, tire_name, problem, severity, source)
                   VALUES (?, ?, ?, ?, ?)""",
                (problem.car_id, problem.tire_name, problem.problem, problem.severity, problem.source)
            )
            return cur.lastrowid or 0

    def get_problems(self, car_id: int, tire_name: Optional[str] = None) -> List[TireProblem]:
        with self._conn() as conn:
            if tire_name:
                rows = conn.execute(
                    "SELECT * FROM tire_problems WHERE car_id = ? AND LOWER(tire_name) LIKE ?",
                    (car_id, f"%{tire_name.lower()}%")
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM tire_problems WHERE car_id = ? ORDER BY severity DESC",
                    (car_id,)
                ).fetchall()
            return [TireProblem(**dict(r)) for r in rows]

    # ============================================================
    # SPECS
    # ============================================================

    def add_spec(self, spec: TireSpec) -> int:
        with self._conn() as conn:
            cur = conn.execute(
                """INSERT OR IGNORE INTO tire_specs
                   (name, category, size, load_index, speed_index, noise_db,
                    fuel_class, wet_grip, tread_depth, runflat, ev_compatible)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (spec.name, spec.category, spec.size, spec.load_index,
                 spec.speed_index, spec.noise_db, spec.fuel_class, spec.wet_grip,
                 spec.tread_depth, int(spec.runflat), int(spec.ev_compatible))
            )
            return cur.lastrowid or 0

    def get_spec(self, name: str) -> Optional[TireSpec]:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM tire_specs WHERE LOWER(name) = LOWER(?)",
                (name,)
            ).fetchone()
            return TireSpec(**dict(row)) if row else None

    def search_specs(self, query: str, category: Optional[str] = None) -> List[TireSpec]:
        with self._conn() as conn:
            if category:
                rows = conn.execute(
                    "SELECT * FROM tire_specs WHERE LOWER(name) LIKE ? AND category = ? LIMIT 20",
                    (f"%{query}%", category)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM tire_specs WHERE LOWER(name) LIKE ? LIMIT 20",
                    (f"%{query}%",)
                ).fetchall()
            return [TireSpec(**dict(r)) for r in rows]

    # ============================================================
    # ENHANCE (главный метод для AI)
    # ============================================================

    def enhance_prompt(self, brand: str, model: str, year: int) -> str:
        """
        Обогащает промпт данными из БД.
        Возвращает строку, которую можно добавить к запросу AI.
        """
        parts = []

        car = self.find_car(brand, model, year)
        if not car:
            return ""

        # Размеры шин
        if car.tire_sizes_list:
            parts.append(f"Проверенные размеры шин: {', '.join(car.tire_sizes_list)}.")

        # Параметры дисков и крепежа
        wheel_info = []
        if car.wheel_pcd: wheel_info.append(f"PCD: {car.wheel_pcd}")
        if car.wheel_et: wheel_info.append(f"ET: {car.wheel_et}")
        if car.wheel_dia: wheel_info.append(f"ЦО: {car.wheel_dia}")
        if car.bolt_thread: wheel_info.append(f"Резьба: {car.bolt_thread}")
        if wheel_info:
            parts.append(f"Диски и крепёж: {', '.join(wheel_info)}.")

        # Популярные шины
        if car.popular_tires:
            popular = [t.strip() for t in car.popular_tires.split(",") if t.strip()]
            parts.append(f"Владельцы чаще всего ставят: {', '.join(popular[:5])}.")

        # Отзывы
        reviews = self.get_reviews(car.id)
        if reviews:
            parts.append("Отзывы владельцев:")
            for r in reviews[:3]:
                parts.append(f"- {r.tire_name}: ⭐{r.rating}/5. Плюсы: {r.pros}. Минусы: {r.cons}.")

        # Проблемы
        problems = self.get_problems(car.id)
        if problems:
            parts.append("Известные проблемы:")
            for p in problems[:3]:
                icon = "🔴" if p.severity == "critical" else "⚠️" if p.severity == "warning" else "ℹ️"
                parts.append(f"{icon} {p.tire_name}: {p.problem}.")

        return "\n".join(parts)

    # ============================================================
    # STATS
    # ============================================================

    def stats(self) -> Dict[str, Any]:
        return {
            "cars": self.car_count(),
            "reviews": self.review_count(),
            "db_path": self.db_path,
            "db_size_mb": round(os.path.getsize(self.db_path) / 1024 / 1024, 2) if os.path.exists(self.db_path) else 0,
        }
