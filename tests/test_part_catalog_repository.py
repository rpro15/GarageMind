from __future__ import annotations

import tempfile
import unittest

from app.adapters.sqlite_part_catalog import SqlitePartCatalogRepository
from app.adapters.stub_part_recognition import DEFAULT_PART_CATALOG
from app.domain.models import CatalogItem


class SqlitePartCatalogRepositoryTestCase(unittest.TestCase):
    def test_seeded_catalog_persists_between_instances(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            database_path = f"{tmp_dir}/catalog.db"
            repository = SqlitePartCatalogRepository(database_path)
            repository.ensure_schema()
            repository.seed_if_empty(DEFAULT_PART_CATALOG)

            first_read = repository.list_items()
            second_repository = SqlitePartCatalogRepository(database_path)
            second_repository.ensure_schema()
            second_read = second_repository.list_items()

            self.assertEqual(first_read, second_read)
            self.assertEqual(first_read[0].part_name, "Brake Pad Set")
            self.assertGreaterEqual(len(first_read), 8)

    def test_seed_if_empty_does_not_replace_existing_catalog(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            database_path = f"{tmp_dir}/catalog.db"
            repository = SqlitePartCatalogRepository(database_path)
            repository.ensure_schema()
            repository.seed_if_empty((CatalogItem(part_name="Custom Rotor", category="braking"),))
            repository.seed_if_empty(DEFAULT_PART_CATALOG)

            items = repository.list_items()
            self.assertEqual(len(items), 1)
            self.assertEqual(items[0].part_name, "Custom Rotor")


if __name__ == "__main__":
    unittest.main()
