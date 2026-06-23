from __future__ import annotations

import sqlite3
import threading
from pathlib import Path

_DDL = """
CREATE TABLE IF NOT EXISTS users (
    user_id     TEXT PRIMARY KEY,
    car_make    TEXT,
    car_model   TEXT,
    car_year    INTEGER,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS click_log (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       TEXT,
    product_name  TEXT NOT NULL,
    marketplace   TEXT NOT NULL,
    affiliate_url TEXT NOT NULL,
    clicked_at    TEXT NOT NULL DEFAULT (datetime('now'))
);
"""

_local = threading.local()


def _connect(db_path: str) -> sqlite3.Connection:
    if not hasattr(_local, "conn") or _local.db_path != db_path:
        conn = sqlite3.connect(db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        _local.conn = conn
        _local.db_path = db_path
    return _local.conn


class Database:
    """Thin SQLite wrapper used by the Flask API and the Telegram bot."""

    def __init__(self, db_path: str = "garagemind.db") -> None:
        self._db_path = db_path
        self._lock = threading.Lock()
        self._init_schema()

    def _init_schema(self) -> None:
        with self._lock:
            conn = _connect(self._db_path)
            conn.executescript(_DDL)
            conn.commit()

    # ------------------------------------------------------------------
    # Users
    # ------------------------------------------------------------------

    def upsert_user(
        self,
        user_id: str,
        car_make: str | None = None,
        car_model: str | None = None,
        car_year: int | None = None,
    ) -> None:
        with self._lock:
            conn = _connect(self._db_path)
            conn.execute(
                """
                INSERT INTO users (user_id, car_make, car_model, car_year)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    car_make  = COALESCE(excluded.car_make,  car_make),
                    car_model = COALESCE(excluded.car_model, car_model),
                    car_year  = COALESCE(excluded.car_year,  car_year)
                """,
                (user_id, car_make, car_model, car_year),
            )
            conn.commit()

    def get_user(self, user_id: str) -> dict | None:
        conn = _connect(self._db_path)
        row = conn.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        ).fetchone()
        return dict(row) if row else None

    # ------------------------------------------------------------------
    # Click log
    # ------------------------------------------------------------------

    def log_click(
        self,
        user_id: str | None,
        product_name: str,
        marketplace: str,
        affiliate_url: str,
    ) -> None:
        with self._lock:
            conn = _connect(self._db_path)
            conn.execute(
                """
                INSERT INTO click_log (user_id, product_name, marketplace, affiliate_url)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, product_name, marketplace, affiliate_url),
            )
            conn.commit()

    def get_clicks(self, limit: int = 100) -> list[dict]:
        conn = _connect(self._db_path)
        rows = conn.execute(
            "SELECT * FROM click_log ORDER BY clicked_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]
