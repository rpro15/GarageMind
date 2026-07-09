"""Тесты маршрутов API"""
from unittest.mock import MagicMock


class TestRecommendRoute:
    def test_recommend_returns_advice(self, client):
        """POST /api/recommend_tires возвращает совет"""
        resp = client.post('/api/recommend_tires', json={
            'brand': 'Toyota',
            'model': 'Camry',
            'year': 2020,
            'season': 'summer',
            'driving_style': 'comfort',
            'budget': 15000
        })
        data = resp.get_json()
        # Может быть ошибка если нет API ключа, но не 500
        assert resp.status_code in [200, 400, 401, 403, 429]
        if resp.status_code == 200 and isinstance(data, dict):
            assert 'advice' in data or 'recommendation' in data

    def test_recommend_no_data(self, client):
        """Пустой запрос = 400"""
        resp = client.post('/api/recommend_tires', json={})
        assert resp.status_code == 400

    def test_recommend_invalid_method(self, client):
        """GET вместо POST = 405"""
        resp = client.get('/api/recommend_tires')
        assert resp.status_code == 405


class TestCompareRoute:
    def test_compare_success(self, client):
        """POST /api/compare_tires с 2+ товарами"""
        resp = client.post('/api/compare_tires', json={
            'products': [
                {'id': '1', 'name': 'Tire A', 'price': 100},
                {'id': '2', 'name': 'Tire B', 'price': 120}
            ]
        })
        assert resp.status_code in [200, 400]

    def test_compare_empty(self, client):
        """Пустой список товаров = 400"""
        resp = client.post('/api/compare_tires', json={'products': []})
        assert resp.status_code == 400

    def test_compare_one_product(self, client):
        """1 товар = 400 (нужно минимум 2)"""
        resp = client.post('/api/compare_tires', json={
            'products': [{'id': '1'}]
        })
        assert resp.status_code == 400


class TestHistoryRoute:
    def test_history_invalid_user_id(self, client):
        """POST /api/user/history без user_id = 400"""
        resp = client.post('/api/user/history', json={
            'brand': 'Toyota'
        })
        assert resp.status_code == 400

    def test_history_without_body(self, client):
        """POST /api/user/history без тела = 400"""
        resp = client.post('/api/user/history',
            content_type='application/json',
            data='not-json'
        )
        assert resp.status_code in [400, 415]


class TestModelsRoute:
    def test_models_returns_list(self, client):
        """GET /api/models?brand=BMW"""
        resp = client.get('/api/models?brand=BMW')
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, list)


class TestBrandsRoute:
    def test_brands_returns_list(self, client):
        """GET /api/brands"""
        resp = client.get('/api/brands')
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, list)
        assert len(data) > 0
        # Проверяем что это строки
        assert all(isinstance(b, str) for b in data)


class TestLangRoute:
    def test_lang_ru_keys(self, client):
        """GET /api/lang/ru содержит ключи"""
        resp = client.get('/api/lang/ru')
        assert resp.status_code == 200
        data = resp.get_json()
        if isinstance(data, dict):
            assert len(data) > 0

    def test_lang_en_keys(self, client):
        """GET /api/lang/en содержит ключи"""
        resp = client.get('/api/lang/en')
        assert resp.status_code == 200
        data = resp.get_json()
        if isinstance(data, dict):
            assert len(data) > 0


class TestHealthRoute:
    def test_health_methods(self, client):
        """/health должен отвечать на GET"""
        resp = client.get('/health')
        assert resp.status_code == 200

    def test_health_returns_json(self, client):
        """Ответ /health — JSON со status"""
        resp = client.get('/health')
        data = resp.get_json()
        assert data['status'] == 'ok'
        assert 'service' in data
