from __future__ import annotations

import os
import sqlite3

from app.domain.models import CatalogItem
from app.ports.part_catalog import PartCatalogRepository


class SqlitePartCatalogRepository(PartCatalogRepository):
    def __init__(self, database_path: str) -> None:
        self._database_path = database_path

    def ensure_schema(self) -> None:
        self._ensure_parent_dir()
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS part_catalog (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    part_name TEXT NOT NULL UNIQUE,
                    category TEXT NOT NULL
                )
                """
            )
            connection.commit()

    def list_items(self) -> list[CatalogItem]:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                SELECT part_name, category
                FROM part_catalog
                ORDER BY id ASC
                """
            )
            rows = cursor.fetchall()
        return [CatalogItem(part_name=row[0], category=row[1]) for row in rows]

    def seed_if_empty(self, items: tuple[CatalogItem, ...]) -> None:
        with self._connect() as connection:
            existing_count = connection.execute("SELECT COUNT(*) FROM part_catalog").fetchone()[0]
            if existing_count > 0:
                return

            connection.executemany(
                "INSERT INTO part_catalog (part_name, category) VALUES (?, ?)",
                [(item.part_name, item.category) for item in items],
            )
            connection.commit()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._database_path)

    def _ensure_parent_dir(self) -> None:
        if self._database_path == ":memory:":
            return
        parent_dir = os.path.dirname(self._database_path)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)
