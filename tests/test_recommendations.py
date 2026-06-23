from __future__ import annotations

import unittest

from app.config.settings import Settings
from app.domain.catalog import Partner, Product
from app.main import create_app
from app.services.affiliate import AffiliateLinkBuilder, ClickTrackingService
from app.services.recommendation import (
    PartnerRegistry,
    ProductCatalog,
    RecommendationRanker,
    rank_score,
)


# ---------------------------------------------------------------------------
# Unit tests for ranking logic
# ---------------------------------------------------------------------------


class RankScoreTestCase(unittest.TestCase):
    def _partner(self, affiliate_weight: float, has_agreement: bool = True) -> Partner:
        return Partner(
            id="p1",
            name="Test Partner",
            affiliate_weight=affiliate_weight,
            url_template="https://example.com/{product_id}",
            has_agreement=has_agreement,
        )

    def _product(self, price: float, rating: float, delivery_days: int) -> Product:
        return Product(
            id="prod1",
            name="Test Tire",
            category="tire",
            price=price,
            rating=rating,
            delivery_days=delivery_days,
            partner_id="p1",
        )

    def test_affiliate_weight_increases_score(self) -> None:
        product = self._product(price=5000, rating=4.0, delivery_days=5)
        low_partner = self._partner(affiliate_weight=0.1)
        high_partner = self._partner(affiliate_weight=0.9)

        low_score = rank_score(product, low_partner)
        high_score = rank_score(product, high_partner)

        self.assertGreater(high_score, low_score)

    def test_lower_price_increases_score(self) -> None:
        partner = self._partner(affiliate_weight=0.5)
        cheap = self._product(price=1000, rating=4.0, delivery_days=5)
        expensive = self._product(price=15000, rating=4.0, delivery_days=5)

        self.assertGreater(rank_score(cheap, partner), rank_score(expensive, partner))

    def test_faster_delivery_increases_score(self) -> None:
        partner = self._partner(affiliate_weight=0.5)
        fast = self._product(price=5000, rating=4.0, delivery_days=1)
        slow = self._product(price=5000, rating=4.0, delivery_days=14)

        self.assertGreater(rank_score(fast, partner), rank_score(slow, partner))

    def test_higher_rating_increases_score(self) -> None:
        partner = self._partner(affiliate_weight=0.5)
        top_rated = self._product(price=5000, rating=5.0, delivery_days=5)
        low_rated = self._product(price=5000, rating=1.0, delivery_days=5)

        self.assertGreater(rank_score(top_rated, partner), rank_score(low_rated, partner))

    def test_score_clamped_between_zero_and_one(self) -> None:
        partner = self._partner(affiliate_weight=1.0)
        product = self._product(price=0.0, rating=5.0, delivery_days=0)
        score = rank_score(product, partner)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)


class RecommendationRankerTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.affiliate_partner = Partner(
            id="aff",
            name="Affiliate Partner",
            affiliate_weight=0.9,
            url_template="https://aff.example.com/{product_id}?ref=garagemind",
            has_agreement=True,
        )
        self.non_affiliate_partner = Partner(
            id="noaff",
            name="No Agreement Partner",
            affiliate_weight=0.1,
            url_template=None,
            has_agreement=False,
        )
        self.registry = PartnerRegistry([self.affiliate_partner, self.non_affiliate_partner])

        self.tire_aff = Product(
            id="t1",
            name="Premium Tire (affiliate)",
            category="tire",
            price=5000,
            rating=4.5,
            delivery_days=3,
            partner_id="aff",
        )
        self.tire_noaff = Product(
            id="t2",
            name="Budget Tire (no affiliate)",
            category="tire",
            price=5000,
            rating=4.5,
            delivery_days=3,
            partner_id="noaff",
        )
        self.wheel = Product(
            id="w1",
            name="Alloy Wheel",
            category="wheel",
            price=4000,
            rating=4.3,
            delivery_days=4,
            partner_id="aff",
        )
        self.catalog = ProductCatalog([self.tire_aff, self.tire_noaff, self.wheel])
        self.ranker = RecommendationRanker(self.catalog, self.registry)

    def test_recommend_returns_only_requested_category(self) -> None:
        results = self.ranker.recommend("tire")
        categories = {r.product.category for r in results}
        self.assertEqual(categories, {"tire"})

    def test_recommend_wheel_category_works(self) -> None:
        results = self.ranker.recommend("wheel")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].product.id, "w1")

    def test_affiliate_partner_ranked_first(self) -> None:
        results = self.ranker.recommend("tire", top_n=2)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].partner.id, "aff")

    def test_top_n_limits_results(self) -> None:
        results = self.ranker.recommend("tire", top_n=1)
        self.assertEqual(len(results), 1)

    def test_affiliate_url_included_for_partner_with_template(self) -> None:
        results = self.ranker.recommend("tire", top_n=1)
        self.assertIsNotNone(results[0].affiliate_url)
        self.assertIn("t1", results[0].affiliate_url)

    def test_no_affiliate_url_when_partner_has_no_template(self) -> None:
        results = self.ranker.recommend("tire", top_n=2)
        noaff_result = next(r for r in results if r.partner.id == "noaff")
        self.assertIsNone(noaff_result.affiliate_url)

    def test_recommendation_to_dict_has_expected_keys(self) -> None:
        results = self.ranker.recommend("tire", top_n=1)
        d = results[0].to_dict()
        for key in ("product_id", "name", "category", "price", "rating",
                    "delivery_days", "partner", "score", "affiliate_url", "reason"):
            self.assertIn(key, d)

    def test_empty_category_returns_empty_list(self) -> None:
        results = self.ranker.recommend("brake", top_n=4)
        self.assertEqual(results, [])


# ---------------------------------------------------------------------------
# Unit tests for AffiliateLinkBuilder
# ---------------------------------------------------------------------------


class AffiliateLinkBuilderTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.builder = AffiliateLinkBuilder()

    def test_builds_url_with_product_id(self) -> None:
        url = self.builder.build("https://example.com/{product_id}?ref=gm", "tire-001")
        self.assertEqual(url, "https://example.com/tire-001?ref=gm")

    def test_returns_none_when_template_is_none(self) -> None:
        self.assertIsNone(self.builder.build(None, "tire-001"))


# ---------------------------------------------------------------------------
# Unit tests for ClickTrackingService
# ---------------------------------------------------------------------------


class ClickTrackingServiceTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tracker = ClickTrackingService()

    def test_record_stores_event(self) -> None:
        event = self.tracker.record("tire-001", "ozon")
        self.assertEqual(len(self.tracker.all_events()), 1)
        self.assertEqual(event.product_id, "tire-001")
        self.assertEqual(event.partner_id, "ozon")

    def test_record_captures_session_id(self) -> None:
        event = self.tracker.record("tire-001", "ozon", session_id="abc123")
        self.assertEqual(event.session_id, "abc123")

    def test_record_sets_timestamp(self) -> None:
        event = self.tracker.record("tire-001", "ozon")
        self.assertIsNotNone(event.timestamp)
        self.assertIn("T", event.timestamp)  # ISO 8601

    def test_events_for_product_filters_correctly(self) -> None:
        self.tracker.record("tire-001", "ozon")
        self.tracker.record("wheel-001", "ozon")
        results = self.tracker.events_for_product("tire-001")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].product_id, "tire-001")

    def test_events_for_partner_filters_correctly(self) -> None:
        self.tracker.record("tire-001", "ozon")
        self.tracker.record("tire-001", "wildberries")
        results = self.tracker.events_for_partner("ozon")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].partner_id, "ozon")

    def test_multiple_events_accumulate(self) -> None:
        for i in range(5):
            self.tracker.record(f"product-{i}", "ozon")
        self.assertEqual(len(self.tracker.all_events()), 5)


# ---------------------------------------------------------------------------
# API integration tests for new endpoints
# ---------------------------------------------------------------------------


class RecommendApiTestCase(unittest.TestCase):
    def setUp(self) -> None:
        app = create_app(
            Settings(
                max_image_bytes=1024 * 1024,
                allowed_image_mime_types=("image/png",),
                recognition_provider="stub",
                log_level="DEBUG",
            )
        )
        app.testing = True
        self.client = app.test_client()

    def test_recommend_tire_returns_200(self) -> None:
        response = self.client.get("/api/recommend?category=tire")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["category"], "tire")
        self.assertGreater(payload["count"], 0)

    def test_recommend_wheel_returns_200(self) -> None:
        response = self.client.get("/api/recommend?category=wheel")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["category"], "wheel")
        self.assertGreater(payload["count"], 0)

    def test_recommend_limits_results_with_n(self) -> None:
        response = self.client.get("/api/recommend?category=tire&n=2")
        payload = response.get_json()
        self.assertLessEqual(payload["count"], 2)

    def test_recommend_returns_affiliate_partner_first(self) -> None:
        response = self.client.get("/api/recommend?category=tire&n=4")
        payload = response.get_json()
        recs = payload["recommendations"]
        self.assertGreater(len(recs), 1)
        # The first result must be from an affiliate-enabled partner
        self.assertIn(recs[0]["partner_id"], {"ozon", "wildberries"})

    def test_recommend_without_category_returns_400(self) -> None:
        response = self.client.get("/api/recommend")
        self.assertEqual(response.status_code, 400)
        payload = response.get_json()
        self.assertEqual(payload["error"]["code"], "missing_category")

    def test_recommend_with_invalid_category_returns_400(self) -> None:
        response = self.client.get("/api/recommend?category=engine")
        self.assertEqual(response.status_code, 400)
        payload = response.get_json()
        self.assertEqual(payload["error"]["code"], "invalid_category")

    def test_track_click_records_event(self) -> None:
        response = self.client.post(
            "/api/track-click",
            json={"product_id": "tire-001", "partner_id": "ozon"},
        )
        self.assertEqual(response.status_code, 201)
        payload = response.get_json()
        self.assertEqual(payload["status"], "recorded")
        self.assertEqual(payload["event"]["product_id"], "tire-001")
        self.assertEqual(payload["event"]["partner_id"], "ozon")

    def test_track_click_with_session_id(self) -> None:
        response = self.client.post(
            "/api/track-click",
            json={"product_id": "tire-001", "partner_id": "ozon", "session_id": "sess42"},
        )
        self.assertEqual(response.status_code, 201)
        payload = response.get_json()
        self.assertEqual(payload["event"]["session_id"], "sess42")

    def test_track_click_missing_fields_returns_400(self) -> None:
        response = self.client.post(
            "/api/track-click",
            json={"product_id": "tire-001"},
        )
        self.assertEqual(response.status_code, 400)
        payload = response.get_json()
        self.assertEqual(payload["error"]["code"], "missing_fields")

    def test_track_click_invalid_json_returns_400(self) -> None:
        response = self.client.post(
            "/api/track-click",
            data="not-json",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
