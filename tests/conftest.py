"""Фикстуры для тестов"""

import os
import sys
import tempfile
import pytest

# Добавляем корень проекта в путь
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.main import create_app
from app.config.settings import Settings


@pytest.fixture
def app():
    """Создаём Flask-приложение для тестов"""
    # Настройки для тестов
    os.environ['SECRET_KEY'] = 'test-secret-key'
    os.environ['DEEPSEEK_API_KEY'] = 'test-key'
    os.environ['DEEPSEEK_MODEL'] = 'deepseek-chat'
    os.environ['LOG_LEVEL'] = 'CRITICAL'
    os.environ['CACHE_TTL_RECOMMEND'] = '600'
    os.environ['CACHE_TTL_BRANDS'] = '3600'
    os.environ['CACHE_TTL_MODELS'] = '3600'
    os.environ['GARAGE_MIND_DB_PATH'] = ':memory:'

    app = create_app()
    app.config['TESTING'] = True
    return app


@pytest.fixture
def client(app):
    """Тестовый HTTP-клиент"""
    return app.test_client()


@pytest.fixture
def mock_deepseek(monkeypatch):
    """Мокаем DeepSeek API, чтобы не делать реальные запросы"""
    
    class MockDeepSeekResponse:
        def __init__(self, status_code=200):
            self.status_code = status_code
        
        def json(self):
            return {
                'choices': [{
                    'message': {
                        'content': 'Рекомендую шины Michelin Pilot Sport 4. '
                                  'Отличное сцепление на мокрой дороге, '
                                  'низкий уровень шума. Цена: 12 400 ₽.'
                    }
                }]
            }
        
        def raise_for_status(self):
            pass

    def mock_post(*args, **kwargs):
        return MockDeepSeekResponse()

    monkeypatch.setattr('requests.post', mock_post)


@pytest.fixture
def mock_deepseek_embedding(monkeypatch):
    """Мокаем эмбеддинги DeepSeek (для RAG)"""
    
    class MockEmbedResponse:
        def __init__(self):
            self.status_code = 200
        
        def json(self):
            return {
                'data': [{
                    'embedding': [0.1] * 1024  # 1024-мерный вектор
                }]
            }
        
        def raise_for_status(self):
            pass

    def mock_post(*args, **kwargs):
        return MockEmbedResponse()

    monkeypatch.setattr('requests.post', mock_post)


@pytest.fixture
def sample_tire_request():
    """Типовой запрос на подбор шин"""
    return {
        'brand': 'Toyota',
        'model': 'Camry',
        'year': 2020,
        'season': 'summer',
        'driving_style': 'comfort',
        'budget': 15000
    }


@pytest.fixture
def sample_compare_request():
    """Типовой запрос на сравнение"""
    return {
        'products': [
            {'id': '1', 'name': 'Michelin Pilot Sport 4', 'price': 12400, 'rating': 4.5},
            {'id': '2', 'name': 'Continental PremiumContact 6', 'price': 10800, 'rating': 4.3},
            {'id': '3', 'name': 'Pirelli Cinturato P7', 'price': 11500, 'rating': 4.4}
        ]
    }
