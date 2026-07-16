"""Тесты источников товаров (партнёры, Wildberries, MultiSource)."""
import pytest
from app.domain.models import TireRequest, DrivingStyle, Season
from app.services.sources.multi_source import MultiSourceProductService
from app.services.sources.partner_source import PartnerSource
from app.services.sources.wildberries_source import WildberriesSource


class TestPartnerSource:
    """Тесты PartnerSource (фолбек на генерацию из БД)."""

    @pytest.mark.asyncio
    async def test_fetch_without_api_key(self):
        """Без API ключа должен генерировать товары из базы знаний."""
        source = PartnerSource(client_id=None, client_secret=None)
        request = TireRequest(
            brand="Toyota",
            model="Camry",
            year=2020,
            driving_style=DrivingStyle.comfort,
            season=Season.summer,
        )
        products = await source.fetch(request)
        assert len(products) > 0
        assert all(p.price > 0 for p in products)
        assert all(p.currency == "RUB" for p in products)

    @pytest.mark.asyncio
    async def test_search_without_api_key(self):
        """Без API ключа search возвращает пустой список."""
        source = PartnerSource(client_id=None, client_secret=None)
        products = await source.search("Michelin шины", max_results=3)
        assert products == []


class TestMultiSource:
    """Тесты MultiSourceProductService."""

    @pytest.mark.asyncio
    async def test_find_tires_aggregates_sources(self):
        """MultiSource собирает товары из всех источников."""
        catalog = MultiSourceProductService()
        catalog.register_source(PartnerSource(client_id=None, client_secret=None))

        request = TireRequest(
            brand="Toyota",
            model="Camry",
            year=2020,
            driving_style=DrivingStyle.comfort,
            season=Season.summer,
        )
        products = await catalog.find_tires(request, min_products=3)
        assert len(products) >= 3

    @pytest.mark.asyncio
    async def test_find_products_by_query(self):
        """Поиск по текстовому запросу."""
        catalog = MultiSourceProductService()
        catalog.register_source(PartnerSource(client_id=None, client_secret=None))

        products = await catalog.find_products_by_query("Michelin шины 205/55R16")
        assert isinstance(products, list)
        # Может быть пустым, так как PartnerSource.search без API ключа пуст
        # Это нормальное поведение


class TestWildberriesSource:
    """Тесты WildberriesSource (в основном проверка структуры)."""

    def test_wildberries_init(self):
        """Проверка инициализации."""
        source = WildberriesSource(api_key=None)
        assert source.name == "wildberries"
        assert source.api_key is None

    def test_wildberries_cache_functions(self):
        """Проверка функций кэша Wildberries."""
        from app.services.sources.wildberries_source import _cache_key, _get_cached, _set_cached
        request = TireRequest(
            brand="Toyota",
            model="Camry",
            year=2020,
            driving_style=DrivingStyle.comfort,
            season=Season.summer,
        )
        key = _cache_key(request)
        assert "Toyota" in key
        assert "Camry" in key

        # Проверка кэша
        cached = _get_cached(key)
        assert cached is None  # ещё ничего не клали
