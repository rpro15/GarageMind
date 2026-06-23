from __future__ import annotations

import unittest

from app.config.settings import Settings
from app.domain.models import Partner, Product
from app.main import create_app
from app.services.affiliate_link_builder import AffiliateLinkBuilder
from app.services.click_tracker import ClickTrackingService
from app.services.partner_registry import PartnerRegistry
from app.services.recommendation import RecommendationService
from app.services.recommendation_ranker import RecommendationRanker


# ---------------------------------------------------------------------------
# Test fixtures
# ---------------------------------------------------------------------------

PARTNER_A = Partner(
    id="pa",
    name="ShopA",
    affiliate_enabled=True,
    priority_weight=0.9,
    base_url="https://shop-a.example.com",
    affiliate_tag="tag_a",
)
PARTNER_B = Partner(
    id="pb",
    name="ShopB",
    affiliate_enabled=True,
    priority_weight=0.5,
    base_url="https://shop-b.example.com",
    affiliate_tag="tag_b",
)
PARTNER_C = Partner(
    id="pc",
    name="ShopC",
    affiliate_enabled=False,
    priority_weight=0.3,
    base_url="https://shop-c.example.com",
    affiliate_tag=None,
)

TIRE_A = Product(id="t_a", partner_id="pa", name="Tire A", category="tires", price=5000.0)
TIRE_B = Product(id="t_b", partner_id="pb", name="Tire B", category="tires", price=8000.0)
TIRE_C = Product(id="t_c", partner_id="pc", name="Tire C", category="tires", price=3000.0)

WHEEL_A = Product(id="w_a", partner_id="pa", name="Wheel A", category="wheels", price=4000.0)


# ---------------------------------------------------------------------------
# AffiliateLinkBuilder tests
# ---------------------------------------------------------------------------


class AffiliateLinkBuilderTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.builder = AffiliateLinkBuilder()

    def test_affiliate_link_includes_ref_tag(self) -> None:
        url = self.builder.build(TIRE_A, PARTNER_A)
        self.assertIn("ref=tag_a", url)
        self.assertIn("/catalog/t_a", url)
        self.assertIn("shop-a.example.com", url)

    def test_non_affiliate_link_has_no_ref_tag(self) -> None:
        url = self.builder.build(TIRE_C, PARTNER_C)
        self.assertNotIn("ref=", url)
        self.assertIn("/catalog/t_c", url)

    def test_link_uses_partner_base_url(self) -> None:
        url_b = self.builder.build(TIRE_B, PARTNER_B)
        self.assertIn("shop-b.example.com", url_b)
        self.assertIn("ref=tag_b", url_b)


# ---------------------------------------------------------------------------
# PartnerRegistry tests
# ---------------------------------------------------------------------------


class PartnerRegistryTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = PartnerRegistry(
            partners=[PARTNER_A, PARTNER_B, PARTNER_C],
            products=[TIRE_A, TIRE_B, TIRE_C, WHEEL_A],
        )

    def test_list_products_returns_all(self) -> None:
        products = self.registry.list_products()
        self.assertEqual(len(products), 4)

    def test_list_products_filters_by_category(self) -> None:
        tires = self.registry.list_products(category="tires")
        self.assertEqual(len(tires), 3)
        for p in tires:
            self.assertEqual(p.category, "tires")

    def test_list_products_category_wheels(self) -> None:
        wheels = self.registry.list_products(category="wheels")
        self.assertEqual(len(wheels), 1)
        self.assertEqual(wheels[0].id, "w_a")

    def test_get_partner_by_id(self) -> None:
        partner = self.registry.get_partner("pa")
        self.assertIsNotNone(partner)
        self.assertEqual(partner.name, "ShopA")  # type: ignore[union-attr]

    def test_get_partner_unknown_returns_none(self) -> None:
        self.assertIsNone(self.registry.get_partner("unknown"))

    def test_default_registry_has_tires_and_wheels(self) -> None:
        default_registry = PartnerRegistry()
        tires = default_registry.list_products(category="tires")
        wheels = default_registry.list_products(category="wheels")
        self.assertGreater(len(tires), 0)
        self.assertGreater(len(wheels), 0)


# ---------------------------------------------------------------------------
# RecommendationRanker tests
# ---------------------------------------------------------------------------


class RecommendationRankerTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.ranker = RecommendationRanker()
        self.partners = {
            PARTNER_A.id: PARTNER_A,
            PARTNER_B.id: PARTNER_B,
            PARTNER_C.id: PARTNER_C,
        }

    def test_returns_ranked_cards(self) -> None:
        cards = self.ranker.rank([TIRE_A, TIRE_B, TIRE_C], self.partners)
        self.assertEqual(len(cards), 3)

    def test_affiliate_partner_ranks_higher_than_non_affiliate(self) -> None:
        cards = self.ranker.rank([TIRE_A, TIRE_C], self.partners)
        # TIRE_A → affiliate partner (pa, weight=0.9), TIRE_C → non-affiliate (pc)
        self.assertEqual(cards[0].product.id, "t_a")

    def test_higher_priority_weight_wins_when_both_affiliate(self) -> None:
        # TIRE_A: affiliate_component=0.9, price=5000
        # TIRE_B: affiliate_component=0.5, price=8000 (max), price_component=0
        # TIRE_A score = 0.9*0.4 + (1 - 5000/8000)*0.6 = 0.36 + 0.225 = 0.585
        # TIRE_B score = 0.5*0.4 + 0*0.6 = 0.2
        cards = self.ranker.rank([TIRE_A, TIRE_B], self.partners)
        self.assertEqual(cards[0].product.id, "t_a")

    def test_top_n_limits_results(self) -> None:
        cards = self.ranker.rank([TIRE_A, TIRE_B, TIRE_C], self.partners, top_n=2)
        self.assertEqual(len(cards), 2)

    def test_scores_are_between_0_and_1(self) -> None:
        cards = self.ranker.rank([TIRE_A, TIRE_B, TIRE_C], self.partners)
        for card in cards:
            self.assertGreaterEqual(card.score, 0.0)
            self.assertLessEqual(card.score, 1.0)

    def test_empty_product_list_returns_empty(self) -> None:
        cards = self.ranker.rank([], self.partners)
        self.assertEqual(cards, [])

    def test_affiliate_url_is_present(self) -> None:
        cards = self.ranker.rank([TIRE_A], self.partners)
        self.assertTrue(cards[0].affiliate_url.startswith("https://"))

    def test_non_affiliate_card_has_reason(self) -> None:
        cards = self.ranker.rank([TIRE_C], self.partners)
        self.assertIsInstance(cards[0].reason, str)
        self.assertGreater(len(cards[0].reason), 0)

    def test_to_dict_contains_required_fields(self) -> None:
        cards = self.ranker.rank([TIRE_A], self.partners)
        d = cards[0].to_dict()
        for key in ("product_id", "name", "category", "price", "partner", "affiliate_url", "score", "reason"):
            self.assertIn(key, d)


# ---------------------------------------------------------------------------
# ClickTrackingService tests
# ---------------------------------------------------------------------------


class ClickTrackingServiceTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tracker = ClickTrackingService()

    def test_record_returns_event(self) -> None:
        event = self.tracker.record("t_a", "pa", "https://example.com/catalog/t_a?ref=x")
        self.assertEqual(event.product_id, "t_a")
        self.assertEqual(event.partner_id, "pa")
        self.assertIn("t_a?ref=x", event.affiliate_url)
        self.assertIsInstance(event.timestamp, str)

    def test_list_events_empty_initially(self) -> None:
        self.assertEqual(self.tracker.list_events(), [])

    def test_list_events_returns_all_recorded(self) -> None:
        self.tracker.record("t_a", "pa", "https://example.com/1")
        self.tracker.record("t_b", "pb", "https://example.com/2")
        events = self.tracker.list_events()
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0].product_id, "t_a")
        self.assertEqual(events[1].product_id, "t_b")

    def test_event_to_dict_contains_required_fields(self) -> None:
        event = self.tracker.record("t_a", "pa", "https://example.com/catalog/t_a")
        d = event.to_dict()
        for key in ("product_id", "partner_id", "affiliate_url", "timestamp"):
            self.assertIn(key, d)


# ---------------------------------------------------------------------------
# RecommendationService integration
# ---------------------------------------------------------------------------


class RecommendationServiceTestCase(unittest.TestCase):
    def setUp(self) -> None:
        registry = PartnerRegistry(
            partners=[PARTNER_A, PARTNER_B, PARTNER_C],
            products=[TIRE_A, TIRE_B, TIRE_C, WHEEL_A],
        )
        ranker = RecommendationRanker()
        self.service = RecommendationService(registry=registry, ranker=ranker)

    def test_recommend_all_categories(self) -> None:
        cards = self.service.recommend()
        self.assertGreater(len(cards), 0)
        categories = {c.product.category for c in cards}
        self.assertIn("tires", categories)
        self.assertIn("wheels", categories)

    def test_recommend_tires_only(self) -> None:
        cards = self.service.recommend(category="tires")
        for card in cards:
            self.assertEqual(card.product.category, "tires")

    def test_recommend_wheels_only(self) -> None:
        cards = self.service.recommend(category="wheels")
        for card in cards:
            self.assertEqual(card.product.category, "wheels")

    def test_recommend_respects_top_n(self) -> None:
        cards = self.service.recommend(top_n=2)
        self.assertLessEqual(len(cards), 2)


# ---------------------------------------------------------------------------
# API endpoint tests
# ---------------------------------------------------------------------------


class RecommendationApiTestCase(unittest.TestCase):
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

    def test_get_recommendations_returns_list(self) -> None:
        response = self.client.get("/api/recommendations")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertIn("recommendations", payload)
        self.assertIsInstance(payload["recommendations"], list)
        self.assertGreater(len(payload["recommendations"]), 0)

    def test_get_recommendations_filtered_by_tires(self) -> None:
        response = self.client.get("/api/recommendations?category=tires")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        for card in payload["recommendations"]:
            self.assertEqual(card["category"], "tires")

    def test_get_recommendations_filtered_by_wheels(self) -> None:
        response = self.client.get("/api/recommendations?category=wheels")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        for card in payload["recommendations"]:
            self.assertEqual(card["category"], "wheels")

    def test_get_recommendations_invalid_category_returns_400(self) -> None:
        response = self.client.get("/api/recommendations?category=brakes")
        self.assertEqual(response.status_code, 400)
        payload = response.get_json()
        self.assertEqual(payload["error"]["code"], "invalid_category")

    def test_recommendation_cards_have_affiliate_url(self) -> None:
        response = self.client.get("/api/recommendations")
        payload = response.get_json()
        for card in payload["recommendations"]:
            self.assertIn("affiliate_url", card)
            self.assertTrue(card["affiliate_url"].startswith("https://"))

    def test_recommendation_cards_have_partner_info(self) -> None:
        response = self.client.get("/api/recommendations")
        payload = response.get_json()
        for card in payload["recommendations"]:
            self.assertIn("partner", card)
            self.assertIn("name", card["partner"])

    def test_post_click_records_event(self) -> None:
        response = self.client.post(
            "/api/clicks",
            json={
                "product_id": "tire_001",
                "partner_id": "partner_ozon",
                "affiliate_url": "https://ozon.ru/catalog/tire_001?ref=garagemind_ozon",
            },
        )
        self.assertEqual(response.status_code, 201)
        payload = response.get_json()
        self.assertTrue(payload["recorded"])
        event = payload["event"]
        self.assertEqual(event["product_id"], "tire_001")
        self.assertEqual(event["partner_id"], "partner_ozon")
        self.assertIn("timestamp", event)

    def test_post_click_missing_fields_returns_400(self) -> None:
        response = self.client.post(
            "/api/clicks",
            json={"product_id": "tire_001"},
        )
        self.assertEqual(response.status_code, 400)
        payload = response.get_json()
        self.assertEqual(payload["error"]["code"], "missing_click_fields")

    def test_post_click_non_json_returns_415(self) -> None:
        response = self.client.post(
            "/api/clicks",
            data="product_id=tire_001",
            content_type="application/x-www-form-urlencoded",
        )
        self.assertEqual(response.status_code, 415)

    def test_x_request_id_present_on_recommendations(self) -> None:
        response = self.client.get("/api/recommendations")
        self.assertIsNotNone(response.headers.get("X-Request-Id"))


if __name__ == "__main__":
    unittest.main()
