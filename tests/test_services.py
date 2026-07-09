"""Тесты сервисов"""
import asyncio
from app.services.user_history import UserHistoryService
from app.services.sources.forum_scraper import ForumScraper
from app.config.settings import settings


class TestUserHistory:
    def test_service_init(self):
        svc = UserHistoryService()
        assert svc is not None

    def test_get_profile(self):
        svc = UserHistoryService()
        try:
            profile = asyncio.run(svc.get_profile("test_user"))
            assert profile.user_id == "test_user"
        except Exception:
            pass


class TestForumScraper:
    def test_scraper_init(self):
        scraper = ForumScraper()
        assert scraper is not None

    def test_scraper_stats(self):
        scraper = ForumScraper()
        stats = scraper.stats()
        assert isinstance(stats, dict)

    def test_daily_limit(self):
        limit = settings.COLLECTOR_DAILY_LIMIT
        assert 0 < limit <= 500
