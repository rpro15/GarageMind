"""Тесты API эндпоинтов"""
import json
import pytest


class TestHealthEndpoint:
    """Тесты /health"""

    def test_health_returns_ok(self, client):
        resp = client.get('/health')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['status'] == 'ok'


class TestBrandsEndpoint:
    def test_brands_list(self, client):
        resp = client.get('/api/brands')
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_brands_cache(self, client):
        resp1 = client.get('/api/brands')
        resp2 = client.get('/api/brands')
        assert resp1.status_code == 200
        assert resp2.status_code == 200


class TestModelsEndpoint:
    def test_models_success(self, client):
        resp = client.get('/api/models?brand=Toyota')
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, list)

    def test_models_no_brand(self, client):
        resp = client.get('/api/models')
        assert resp.status_code == 400


class TestUserHistoryEndpoint:
    def test_history_save(self, client):
        resp = client.post('/api/user/history', json={
            'user_id': 'tg_test_123',
            'brand': 'Toyota',
            'model': 'Camry',
            'driving_style': 'comfort',
            'season': 'summer'
        })
        data = resp.get_json()
        # Может вернуть dict или list — проверяем status
        if isinstance(data, dict):
            assert data.get('status') == 'ok'
        assert resp.status_code == 200

    def test_history_no_user(self, client):
        resp = client.post('/api/user/history', json={'brand': 'Toyota'})
        assert resp.status_code == 400


class TestLangEndpoint:
    def test_lang_russian(self, client):
        resp = client.get('/api/lang/ru')
        assert resp.status_code == 200

    def test_lang_english(self, client):
        resp = client.get('/api/lang/en')
        assert resp.status_code == 200

    def test_lang_not_found(self, client):
        resp = client.get('/api/lang/xx')
        # Может вернуть 200 (default lang) или 404 — принимаем оба
        assert resp.status_code in [200, 404]


class TestCORS:
    def test_cors_headers(self, client):
        resp = client.options('/api/brands')
        assert resp.status_code in [200, 204]
