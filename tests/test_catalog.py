from __future__ import annotations

import unittest

from app.adapters.in_memory_catalog_repository import InMemoryCatalogRepository
from app.adapters.sqlite_catalog_repository import SqliteCatalogRepository
from app.adapters.stub_part_recognition import PART_CATALOG
from app.config.settings import Settings
from app.main import create_app, seed_catalog


class InMemoryCatalogRepositoryTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = InMemoryCatalogRepository()

    def test_empty_repository_returns_no_parts(self) -> None:
        self.assertEqual(self.repo.list_parts(), [])

    def test_count_returns_zero_for_empty_repository(self) -> None:
        self.assertEqual(self.repo.count(), 0)

    def test_add_part_increments_count(self) -> None:
        self.repo.add_part("Brake Pad Set", "braking")
        self.assertEqual(self.repo.count(), 1)

    def test_add_part_assigns_sequential_ids(self) -> None:
        first = self.repo.add_part("Oil Filter", "engine")
        second = self.repo.add_part("Shock Absorber", "suspension")
        self.assertEqual(first.id, 1)
        self.assertEqual(second.id, 2)

    def test_add_part_stores_correct_fields(self) -> None:
        part = self.repo.add_part("Alternator", "electrical")
        self.assertEqual(part.part_name, "Alternator")
        self.assertEqual(part.category, "electrical")
        self.assertIsNotNone(part.created_at)

    def test_list_parts_returns_all_added_parts(self) -> None:
        self.repo.add_part("Headlight Assembly", "lighting")
        self.repo.add_part("Radiator Hose", "cooling")
        parts = self.repo.list_parts()
        self.assertEqual(len(parts), 2)
        self.assertEqual(parts[0].part_name, "Headlight Assembly")
        self.assertEqual(parts[1].part_name, "Radiator Hose")

    def test_get_part_returns_matching_part(self) -> None:
        added = self.repo.add_part("Wheel Bearing Hub", "drivetrain")
        fetched = self.repo.get_part(added.id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.part_name, "Wheel Bearing Hub")

    def test_get_part_returns_none_for_missing_id(self) -> None:
        self.assertIsNone(self.repo.get_part(999))

    def test_to_dict_includes_expected_keys(self) -> None:
        part = self.repo.add_part("Air Filter Housing", "intake")
        d = part.to_dict()
        self.assertIn("id", d)
        self.assertIn("part_name", d)
        self.assertIn("category", d)
        self.assertIn("created_at", d)


class SqliteCatalogRepositoryTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = SqliteCatalogRepository(":memory:")

    def test_empty_repository_has_count_zero(self) -> None:
        self.assertEqual(self.repo.count(), 0)

    def test_add_and_list_parts(self) -> None:
        self.repo.add_part("Brake Pad Set", "braking")
        self.repo.add_part("Oil Filter", "engine")
        parts = self.repo.list_parts()
        self.assertEqual(len(parts), 2)

    def test_add_part_assigns_autoincrement_id(self) -> None:
        first = self.repo.add_part("Shock Absorber", "suspension")
        second = self.repo.add_part("Alternator", "electrical")
        self.assertNotEqual(first.id, second.id)

    def test_get_part_returns_correct_part(self) -> None:
        added = self.repo.add_part("Headlight Assembly", "lighting")
        fetched = self.repo.get_part(added.id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.part_name, "Headlight Assembly")
        self.assertEqual(fetched.category, "lighting")

    def test_get_part_returns_none_for_unknown_id(self) -> None:
        self.assertIsNone(self.repo.get_part(9999))

    def test_list_parts_returns_ordered_by_id(self) -> None:
        self.repo.add_part("Wheel Bearing Hub", "drivetrain")
        self.repo.add_part("Air Filter Housing", "intake")
        parts = self.repo.list_parts()
        self.assertEqual(parts[0].id, 1)
        self.assertEqual(parts[1].id, 2)


class SeedCatalogTestCase(unittest.TestCase):
    def test_seed_populates_empty_repository(self) -> None:
        repo = InMemoryCatalogRepository()
        seed_catalog(repo)
        self.assertEqual(repo.count(), len(PART_CATALOG))

    def test_seed_is_idempotent(self) -> None:
        repo = InMemoryCatalogRepository()
        seed_catalog(repo)
        seed_catalog(repo)
        self.assertEqual(repo.count(), len(PART_CATALOG))

    def test_seeded_parts_match_catalog_data(self) -> None:
        repo = InMemoryCatalogRepository()
        seed_catalog(repo)
        parts = repo.list_parts()
        for i, item in enumerate(PART_CATALOG):
            self.assertEqual(parts[i].part_name, item["part_name"])
            self.assertEqual(parts[i].category, item["category"])


class CatalogApiTestCase(unittest.TestCase):
    def setUp(self) -> None:
        app = create_app(
            Settings(
                max_image_bytes=1024 * 1024,
                allowed_image_mime_types=("image/png",),
                recognition_provider="stub",
                log_level="DEBUG",
                database_path=":memory:",
            )
        )
        app.testing = True
        self.client = app.test_client()

    def test_list_catalog_returns_200(self) -> None:
        response = self.client.get("/api/catalog")
        self.assertEqual(response.status_code, 200)

    def test_list_catalog_returns_seeded_parts(self) -> None:
        response = self.client.get("/api/catalog")
        payload = response.get_json()
        self.assertIn("parts", payload)
        self.assertIn("total", payload)
        self.assertEqual(payload["total"], len(PART_CATALOG))

    def test_list_catalog_part_shape(self) -> None:
        response = self.client.get("/api/catalog")
        payload = response.get_json()
        part = payload["parts"][0]
        self.assertIn("id", part)
        self.assertIn("part_name", part)
        self.assertIn("category", part)
        self.assertIn("created_at", part)

    def test_get_catalog_part_returns_200(self) -> None:
        response = self.client.get("/api/catalog/1")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["id"], 1)
        self.assertIn("part_name", payload)
        self.assertIn("category", payload)

    def test_get_catalog_part_returns_404_for_missing_id(self) -> None:
        response = self.client.get("/api/catalog/9999")
        self.assertEqual(response.status_code, 404)
        payload = response.get_json()
        self.assertEqual(payload["error"]["code"], "part_not_found")


if __name__ == "__main__":
    unittest.main()
