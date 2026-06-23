from __future__ import annotations

import logging
import unittest

from app.domain.models import ProductRecommendation, RecommendRequest
from app.services.recommendation import RecommendationService
from app.adapters.stub_product_search import StubProductSearchProvider


def _make_service(partners: list[str] | None = None) -> RecommendationService:
    return RecommendationService(
        provider=StubProductSearchProvider(),
        partner_marketplaces=partners if partners is not None else ["ozon", "wildberries"],
        logger=logging.getLogger("tests.recommendation"),
    )


def _valid_request(**overrides) -> RecommendRequest:
    defaults = dict(
        car_make="Toyota",
        car_model="Camry",
        car_year=2020,
        category="tires",
        season="winter",
        driving_style="comfort",
        budget_rub=30000,
    )
    defaults.update(overrides)
    return RecommendRequest(**defaults)


class RecommendationServiceTestCase(unittest.TestCase):
    def test_returns_up_to_four_results(self) -> None:
        service = _make_service()
        result = service.recommend(_valid_request())
        self.assertLessEqual(len(result.recommendations), 4)
        self.assertGreater(len(result.recommendations), 0)

    def test_ranks_are_sequential_starting_at_one(self) -> None:
        service = _make_service()
        result = service.recommend(_valid_request())
        ranks = [r.rank for r in result.recommendations]
        self.assertEqual(ranks, list(range(1, len(ranks) + 1)))

    def test_partner_items_come_first(self) -> None:
        service = _make_service(partners=["ozon"])
        result = service.recommend(_valid_request(season="winter", budget_rub=50000))
        partner_ranks = [r.rank for r in result.recommendations if r.is_partner]
        non_partner_ranks = [r.rank for r in result.recommendations if not r.is_partner]
        if partner_ranks and non_partner_ranks:
            self.assertLess(max(partner_ranks), min(non_partner_ranks))

    def test_is_partner_flag_set_correctly(self) -> None:
        partners = ["ozon"]
        service = _make_service(partners=partners)
        result = service.recommend(_valid_request(budget_rub=50000))
        for rec in result.recommendations:
            if rec.marketplace in partners:
                self.assertTrue(rec.is_partner, msg=f"{rec.marketplace} should be partner")
            else:
                self.assertFalse(rec.is_partner, msg=f"{rec.marketplace} should not be partner")

    def test_results_respect_budget(self) -> None:
        service = _make_service()
        result = service.recommend(_valid_request(budget_rub=7000))
        for rec in result.recommendations:
            self.assertLessEqual(rec.price_rub, 7000)

    def test_results_match_requested_category(self) -> None:
        service = _make_service()
        result = service.recommend(_valid_request(category="wheels", season="winter", budget_rub=50000))
        for rec in result.recommendations:
            self.assertEqual(rec.category, "wheels")

    def test_car_info_reflected_in_result(self) -> None:
        service = _make_service()
        result = service.recommend(_valid_request(car_make="BMW", car_model="3 Series", car_year=2019))
        self.assertEqual(result.car_make, "BMW")
        self.assertEqual(result.car_model, "3 Series")
        self.assertEqual(result.car_year, 2019)

    def test_partner_priority_list_in_result(self) -> None:
        partners = ["ozon", "admitad"]
        service = _make_service(partners=partners)
        result = service.recommend(_valid_request())
        self.assertEqual(result.partner_priority, partners)

    def test_validates_missing_car_make(self) -> None:
        from app.api.errors import ApiError
        service = _make_service()
        with self.assertRaises(ApiError) as ctx:
            service.recommend(_valid_request(car_make=""))
        self.assertEqual(ctx.exception.code, "invalid_recommend_request")

    def test_validates_invalid_category(self) -> None:
        from app.api.errors import ApiError
        service = _make_service()
        with self.assertRaises(ApiError) as ctx:
            service.recommend(_valid_request(category="oil"))
        self.assertEqual(ctx.exception.code, "invalid_recommend_request")

    def test_validates_invalid_season(self) -> None:
        from app.api.errors import ApiError
        service = _make_service()
        with self.assertRaises(ApiError) as ctx:
            service.recommend(_valid_request(season="monsoon"))
        self.assertEqual(ctx.exception.code, "invalid_recommend_request")

    def test_validates_invalid_driving_style(self) -> None:
        from app.api.errors import ApiError
        service = _make_service()
        with self.assertRaises(ApiError) as ctx:
            service.recommend(_valid_request(driving_style="racing"))
        self.assertEqual(ctx.exception.code, "invalid_recommend_request")

    def test_validates_non_positive_budget(self) -> None:
        from app.api.errors import ApiError
        service = _make_service()
        with self.assertRaises(ApiError) as ctx:
            service.recommend(_valid_request(budget_rub=0))
        self.assertEqual(ctx.exception.code, "invalid_recommend_request")

    def test_validates_invalid_car_year(self) -> None:
        from app.api.errors import ApiError
        service = _make_service()
        with self.assertRaises(ApiError) as ctx:
            service.recommend(_valid_request(car_year=1800))
        self.assertEqual(ctx.exception.code, "invalid_recommend_request")

    def test_no_results_when_budget_too_low(self) -> None:
        service = _make_service()
        result = service.recommend(_valid_request(budget_rub=100))
        self.assertEqual(result.recommendations, [])

    def test_to_dict_structure(self) -> None:
        service = _make_service()
        result = service.recommend(_valid_request(budget_rub=50000))
        d = result.to_dict()
        self.assertIn("recommendations", d)
        self.assertIn("car", d)
        self.assertIn("partner_priority", d)
        self.assertIn("make", d["car"])
        self.assertIn("model", d["car"])
        self.assertIn("year", d["car"])
        if d["recommendations"]:
            rec = d["recommendations"][0]
            for key in ("rank", "product_name", "category", "season", "price_rub",
                        "marketplace", "affiliate_url", "image_url", "is_partner", "source"):
                self.assertIn(key, rec)


if __name__ == "__main__":
    unittest.main()
