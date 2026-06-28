"""
Тесты для сервиса рекомендаций шин.
"""
import pytest
from app.domain.models import TireRequest, DrivingStyle, Season, RecommendationResult, Product


class TestTireRequest:
    """Тесты модели TireRequest."""

    def test_create_full_request(self):
        req = TireRequest(
            brand='Toyota',
            model='Camry',
            year=2020,
            driving_style=DrivingStyle.COMFORT,
            budget=50000,
            season=Season.SUMMER,
        )
        assert req.brand == 'Toyota'
        assert req.model == 'Camry'
        assert req.year == 2020
        assert req.driving_style == DrivingStyle.COMFORT
        assert req.budget == 50000
        assert req.season == Season.SUMMER

    def test_create_minimal_request(self):
        req = TireRequest(
            brand='Lada',
            model='Vesta',
            year=2022,
            driving_style=DrivingStyle.ECONOMY,
        )
        assert req.budget is None
        assert req.season is None

    def test_different_driving_styles(self):
        for style in DrivingStyle:
            req = TireRequest(
                brand='Test', model='Test', year=2020,
                driving_style=style
            )
            assert req.driving_style == style

    def test_different_seasons(self):
        for season in Season:
            req = TireRequest(
                brand='Test', model='Test', year=2020,
                driving_style=DrivingStyle.COMFORT,
                season=season
            )
            assert req.season == season


class TestProduct:
    """Тесты модели Product."""

    def test_create_product(self):
        p = Product(
            id='test-1',
            name='Michelin X-Ice',
            price=15000,
            currency='RUB',
            image_url='https://example.com/1.jpg',
            partner_link='https://example.com/buy',
            source='Ozon',
        )
        assert p.id == 'test-1'
        assert p.price == 15000

    def test_product_minimal(self):
        p = Product(
            id='test-2',
            name='Nokian Hakka',
            price=12000,
        )
        assert p.currency == 'RUB'
        assert p.source == 'partner'  # значение по умолчанию
        assert p.image_url is None
        assert p.partner_link is None


class TestRecommendationResult:
    """Тесты модели RecommendationResult."""

    def test_create_recommendation(self):
        request = TireRequest(
            brand='Toyota', model='Camry', year=2020,
            driving_style=DrivingStyle.COMFORT,
        )
        products = [
            Product(id='p1', name='Tire A', price=10000),
            Product(id='p2', name='Tire B', price=15000),
        ]
        rec = RecommendationResult(
            request=request,
            advice='Рекомендуем шины A',
            products=products,
        )
        assert rec.request.brand == 'Toyota'
        assert len(rec.products) == 2
        assert 'Рекомендуем' in rec.advice

    def test_recommendation_empty_products(self):
        rec = RecommendationResult(
            request=TireRequest(
                brand='Test', model='Test', year=2020,
                driving_style=DrivingStyle.SPORT,
            ),
            advice='Нет подходящих шин',
            products=[],
        )
        assert len(rec.products) == 0
