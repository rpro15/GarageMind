from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

from app.domain.models import CatalogPart
from app.ports.catalog_repository import CatalogRepository


class SqliteCatalogRepository(CatalogRepository):
    """SQLite-backed catalog repository.

    For file-backed databases each public method opens and closes its own
    connection, so the repository is safe to use across threads and request
    contexts without a connection pool.

    When ``db_path`` is ``":memory:"`` a single shared connection is reused
    for the lifetime of the object, because SQLite in-memory databases are
    private to the connection that created them.
    """

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        self._shared_conn: sqlite3.Connection | None = None
        if db_path == ":memory:":
            self._shared_conn = self._open()
        self._init_schema()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _open(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _connect(self) -> sqlite3.Connection:
        if self._shared_conn is not None:
            return self._shared_conn
        return self._open()

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS catalog_parts (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    part_name   TEXT    NOT NULL,
                    category    TEXT    NOT NULL,
                    created_at  TEXT    NOT NULL
                )
                """
            )

    # ------------------------------------------------------------------
    # CatalogRepository interface
    # ------------------------------------------------------------------

    def list_parts(self) -> list[CatalogPart]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, part_name, category, created_at FROM catalog_parts ORDER BY id"
            ).fetchall()
        return [
            CatalogPart(
                id=row["id"],
                part_name=row["part_name"],
                category=row["category"],
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def get_part(self, part_id: int) -> CatalogPart | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT id, part_name, category, created_at FROM catalog_parts WHERE id = ?",
                (part_id,),
            ).fetchone()
        if row is None:
            return None
        return CatalogPart(
            id=row["id"],
            part_name=row["part_name"],
            category=row["category"],
            created_at=row["created_at"],
        )

    def count(self) -> int:
        with self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) FROM catalog_parts").fetchone()
        return row[0]

    def add_part(self, part_name: str, category: str) -> CatalogPart:
        now = datetime.now(tz=timezone.utc).isoformat()
        with self._connect() as conn:
            cursor = conn.execute(
                "INSERT INTO catalog_parts (part_name, category, created_at) VALUES (?, ?, ?)",
                (part_name, category, now),
            )
            new_id = cursor.lastrowid
        return CatalogPart(id=new_id, part_name=part_name, category=category, created_at=now)
