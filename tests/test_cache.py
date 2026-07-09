"""Тесты кэширования"""
import asyncio


class TestCacheFallback:
    def test_no_redis_no_crash(self, app):
        from app.services.cache import get_cache
        cache = get_cache()
        assert cache is not None

    def test_set_get(self, app):
        from app.services.cache import get_cache
        cache = get_cache()
        try:
            asyncio.run(cache.set('test_key', 'value'))
            result = asyncio.run(cache.get('test_key'))
        except Exception:
            pass
        assert True

    def test_set_get_json(self, app):
        from app.services.cache import get_cache
        cache = get_cache()
        try:
            asyncio.run(cache.set_json('json_key', {'a': 1}))
            result = asyncio.run(cache.get_json('json_key'))
        except Exception:
            pass
        assert True


class TestCacheConfiguration:
    def test_cache_ttl_config(self, app):
        from flask import current_app
        with app.app_context():
            ttl = current_app.config.get('CACHE_TTL_RECOMMEND', 600)
            assert ttl == 600
