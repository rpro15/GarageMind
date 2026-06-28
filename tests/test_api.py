"""
Тесты API для Авто Эксперт AI.
"""
import json
import pytest
from app.main import create_app


@pytest.fixture
def app():
    """Фикстура Flask приложения."""
    application = create_app()
    application.config['TESTING'] = True
    return application


@pytest.fixture
def client(app):
    """Фикстура тестового клиента."""
    return app.test_client()


# =============================================
# Healthcheck
# =============================================

class TestHealth:
    def test_health_endpoint(self, client):
        """GET /health должен возвращать 200."""
        resp = client.get('/health')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['status'] == 'ok'
        assert data['service'] == 'avto-expert-ai'

    def test_api_health_endpoint(self, client):
        """GET /api/health должен возвращать 200."""
        resp = client.get('/api/health')
        assert resp.status_code == 200


# =============================================
# Mini App Frontend
# =============================================

class TestMiniApp:
    def test_index_html(self, client):
        """GET /miniapp/index.html должен отдавать HTML."""
        resp = client.get('/miniapp/index.html')
        assert resp.status_code == 200
        assert b'<!DOCTYPE html>' in resp.data
        assert b'\xd0\x90\xd0\xb2\xd1\x82\xd0\xbe \xd0\xad\xd0\xba\xd1\x81\xd0\xbf\xd0\xb5\xd1\x80\xd1\x82' in resp.data

    def test_style_css(self, client):
        """GET /miniapp/style.css должен отдавать CSS."""
        resp = client.get('/miniapp/style.css')
        assert resp.status_code == 200
        assert b'Carbon Theme' in resp.data or b':root' in resp.data

    def test_scripts_js(self, client):
        """GET /miniapp/scripts.js должен отдавать JS."""
        resp = client.get('/miniapp/scripts.js')
        assert resp.status_code == 200
        assert b'API_BASE' in resp.data

    def test_not_found(self, client):
        """GET /miniapp/not_exists.html -> 404."""
        resp = client.get('/miniapp/not_exists.html')
        assert resp.status_code == 404


# =============================================
# Brands API
# =============================================

class TestBrands:
    def test_get_brands(self, client):
        """GET /api/brands возвращает список марок."""
        resp = client.get('/api/brands')
        assert resp.status_code == 200
        brands = resp.get_json()
        assert isinstance(brands, list)
        assert len(brands) > 0
        assert 'Toyota' in brands
        assert 'Lada' in brands

    def test_brands_are_sorted(self, client):
        """Марки должны быть отсортированы."""
        resp = client.get('/api/brands')
        brands = resp.get_json()
        assert brands == sorted(brands)


# =============================================
# Models API
# =============================================

class TestModels:
    def test_get_models_with_brand(self, client):
        """GET /api/models?brand=Toyota возвращает модели."""
        resp = client.get('/api/models?brand=Toyota')
        assert resp.status_code == 200
        models = resp.get_json()
        assert isinstance(models, list)
        assert len(models) > 0
        assert 'Camry' in models or 'Corolla' in models

    def test_get_models_without_brand(self, client):
        """GET /api/models без brand -> 400."""
        resp = client.get('/api/models')
        assert resp.status_code == 400
        data = resp.get_json()
        assert 'error' in data

    def test_get_models_unknown_brand(self, client):
        """GET /api/models?brand=Unknown -> пустой список."""
        resp = client.get('/api/models?brand=Unknown')
        assert resp.status_code == 200
        models = resp.get_json()
        assert models == []


# =============================================
# Tire Recommendation
# =============================================

class TestTireRecommendation:
    def test_recommend_success(self, client):
        """POST /api/recommend_tires с валидными данными -> 200."""
        payload = {
            'brand': 'Toyota',
            'model': 'Camry',
            'year': 2020,
            'driving_style': 'comfort',
            'season': 'summer',
            'budget': 50000
        }
        resp = client.post(
            '/api/recommend_tires',
            data=json.dumps(payload),
            content_type='application/json'
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'advice' in data
        assert 'products' in data
        assert isinstance(data['products'], list)
        assert 'request' in data

    def test_recommend_missing_fields(self, client):
        """POST /api/recommend_tires без полей -> 400."""
        resp = client.post(
            '/api/recommend_tires',
            data=json.dumps({}),
            content_type='application/json'
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert 'error' in data

    def test_recommend_no_body(self, client):
        """POST /api/recommend_tires без тела -> 400."""
        resp = client.post(
            '/api/recommend_tires',
            content_type='application/json'
        )
        assert resp.status_code == 400

    def test_recommend_invalid_driving_style(self, client):
        """POST с невалидным driving_style -> 400."""
        payload = {
            'brand': 'Toyota',
            'model': 'Camry',
            'year': 2020,
            'driving_style': 'invalid_style',
        }
        resp = client.post(
            '/api/recommend_tires',
            data=json.dumps(payload),
            content_type='application/json'
        )
        assert resp.status_code == 400

    def test_recommend_without_budget(self, client):
        """POST без бюджета -> 200 (бюджет опционален)."""
        payload = {
            'brand': 'Lada',
            'model': 'Vesta',
            'year': 2022,
            'driving_style': 'economy',
            'season': 'winter',
        }
        resp = client.post(
            '/api/recommend_tires',
            data=json.dumps(payload),
            content_type='application/json'
        )
        assert resp.status_code == 200


# =============================================
# VIN Decoding
# =============================================

class TestVinDecoder:
    def test_decode_valid_vin_get(self, client):
        """GET /api/decode-vin?vin=... с валидным VIN."""
        resp = client.get('/api/decode-vin?vin=1HGCM82633A004352')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['is_valid'] is True
        assert data['decoded']['manufacturer'] == 'Honda'

    def test_decode_valid_vin_post(self, client):
        """POST /api/decode-vin с валидным VIN."""
        resp = client.post(
            '/api/decode-vin',
            data=json.dumps({'vin': '1HGCM82633A004352'}),
            content_type='application/json'
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['is_valid'] is True

    def test_decode_invalid_vin(self, client):
        """GET /api/decode-vin с невалидным VIN -> 422."""
        resp = client.get('/api/decode-vin?vin=1HGCM82633A004353')
        assert resp.status_code == 422
        data = resp.get_json()
        assert data['is_valid'] is False
        assert len(data['validation_errors']) > 0

    def test_decode_missing_vin(self, client):
        """GET /api/decode-vin без VIN -> 400."""
        resp = client.get('/api/decode-vin')
        assert resp.status_code == 400


# =============================================
# Request IDs
# =============================================

class TestRequestId:
    def test_request_id_in_response(self, client):
        """Ответы должны содержать X-Request-Id."""
        resp = client.get('/health')
        assert 'X-Request-Id' in resp.headers
        assert len(resp.headers['X-Request-Id']) > 0

    def test_request_id_passthrough(self, client):
        """X-Request-Id из запроса передаётся в ответ."""
        resp = client.get('/health', headers={'X-Request-Id': 'my-test-id'})
        assert resp.headers.get('X-Request-Id') == 'my-test-id'


# =============================================
# Part Recognition
# =============================================

class TestPartRecognition:
    def test_recognize_part_no_file(self, client):
        """POST /api/recognize-part без файла -> 400."""
        resp = client.post('/api/recognize-part', content_type='multipart/form-data')
        assert resp.status_code == 400

    def test_recognize_part_unsupported_media(self, client):
        """POST /api/recognize-part с text/plain -> 415."""
        resp = client.post(
            '/api/recognize-part',
            data='test',
            content_type='text/plain'
        )
        assert resp.status_code == 415

    def test_recognize_part_empty_json(self, client):
        """POST /api/recognize-part с пустым JSON -> 400."""
        resp = client.post(
            '/api/recognize-part',
            data=json.dumps({}),
            content_type='application/json'
        )
        assert resp.status_code == 400
