from __future__ import annotations

import csv
import sqlite3
from pathlib import Path

_CSV_PATH = Path(__file__).parent / "car_tires.csv"

_DDL = """
CREATE TABLE IF NOT EXISTS car_tires (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    make          TEXT NOT NULL,
    model         TEXT NOT NULL,
    year_from     INTEGER NOT NULL,
    year_to       INTEGER NOT NULL,
    tire_width    INTEGER NOT NULL,
    tire_profile  INTEGER NOT NULL,
    rim_diameter  INTEGER NOT NULL,
    rim_width     REAL NOT NULL,
    bolt_pattern  TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_car_tires_make_model ON car_tires(make, model);
"""


def _load_csv(conn: sqlite3.Connection) -> None:
    with open(_CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = [
            (
                r["make"],
                r["model"],
                int(r["year_from"]),
                int(r["year_to"]),
                int(r["tire_width"]),
                int(r["tire_profile"]),
                int(r["rim_diameter"]),
                float(r["rim_width"]),
                r["bolt_pattern"],
            )
            for r in reader
        ]
    conn.executemany(
        """
        INSERT INTO car_tires
            (make, model, year_from, year_to, tire_width, tire_profile,
             rim_diameter, rim_width, bolt_pattern)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    conn.commit()


def init_car_tires_db(db_path: str = "garagemind.db") -> sqlite3.Connection:
    """Return a connection to the car-tires DB, creating and seeding if needed."""
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.executescript(_DDL)
    conn.commit()

    count = conn.execute("SELECT COUNT(*) FROM car_tires").fetchone()[0]
    if count == 0:
        _load_csv(conn)

    return conn


def lookup_tire_size(
    conn: sqlite3.Connection,
    make: str,
    model: str,
    year: int,
) -> dict | None:
    """Return the first matching tire-size spec for a given car, or None."""
    row = conn.execute(
        """
        SELECT * FROM car_tires
        WHERE lower(make) = lower(?)
          AND lower(model) = lower(?)
          AND year_from <= ?
          AND year_to   >= ?
        ORDER BY year_from DESC
        LIMIT 1
        """,
        (make, model, year, year),
    ).fetchone()
    return dict(row) if row else None


def list_makes(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute(
        "SELECT DISTINCT make FROM car_tires ORDER BY make"
    ).fetchall()
    return [r[0] for r in rows]


def list_models(conn: sqlite3.Connection, make: str) -> list[str]:
    rows = conn.execute(
        "SELECT DISTINCT model FROM car_tires WHERE lower(make) = lower(?) ORDER BY model",
        (make,),
    ).fetchall()
    return [r[0] for r in rows]
