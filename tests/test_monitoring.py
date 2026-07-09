"""Тесты мониторинга и метрик"""


class TestHealthMetrics:
    def test_health_has_tracking(self, client):
        """Проверяем что health endpoint работает и логируется"""
        resp = client.get('/health')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['status'] == 'ok'

    def test_health_after_requests(self, client):
        """Несколько запросов не ломают health"""
        for _ in range(5):
            resp = client.get('/health')
            assert resp.status_code == 200


class TestAPIMetrics:
    def test_brands_api_works(self, client):
        """API brands работает и логируется"""
        resp = client.get('/api/brands')
        assert resp.status_code == 200

    def test_models_api_works(self, client):
        """API models работает"""
        resp = client.get('/api/models?brand=Toyota')
        assert resp.status_code == 200

    def test_error_returns_proper_status(self, client):
        """Некорректный запрос возвращает 4xx"""
        resp = client.get('/api/models')  # без brand
        assert resp.status_code == 400
        data = resp.get_json()
        assert data is not None
