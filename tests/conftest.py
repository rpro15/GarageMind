"""Фикстуры для тестов"""

import os
import sys
import tempfile
import pytest

# Добавляем корень проекта в путь
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.main import create_app


@pytest.fixture
def app():
    """Создаём Flask-приложение для тестов"""
    os.environ['SECRET_KEY'] = 'test-secret-key'
    os.environ['DEEPSEEK_API_KEY'] = ''  # Пустой = заглушка, без HTTP вызовов
    os.environ['DEEPSEEK_MODEL'] = 'deepseek-chat'
    os.environ['LOG_LEVEL'] = 'CRITICAL'
    os.environ['CACHE_TTL_RECOMMEND'] = '600'
    os.environ['CACHE_TTL_BRANDS'] = '3600'
    os.environ['CACHE_TTL_MODELS'] = '3600'
    os.environ['GARAGE_MIND_DB_PATH'] = ':memory:'
    os.environ['REDIS_URL'] = ''  # Не используем Redis в тестах

    app = create_app()
    app.config['TESTING'] = True
    return app


@pytest.fixture
def client(app):
    """Тестовый HTTP-клиент"""
    return app.test_client()


@pytest.fixture
def mock_deepseek(monkeypatch):
    """
    Мокаем DeepSeek API на уровне DeepSeekClient.generate_text.
    Патчим сам метод, а не httpx.AsyncClient.
    """
    from app.adapters.deepseek_client import DeepSeekClient

    async def mock_generate_text(self, prompt="", system_prompt=None, messages=None):
        return (
            'Рекомендую шины Michelin Pilot Sport 4. '
            'Отличное сцепление на мокрой дороге, '
            'низкий уровень шума. Цена: 12 400 ₽.'
        )

    async def mock_generate_structured(self, prompt="", schema=None):
        return {"error": "mock"}

    monkeypatch.setattr(DeepSeekClient, 'generate_text', mock_generate_text)
    monkeypatch.setattr(DeepSeekClient, 'generate_structured', mock_generate_structured)


@pytest.fixture
def mock_deepseek_embedding(monkeypatch):
    """Мокаем EmbeddingService.get_embedding для RAG."""
    from app.services.rag.embedding_service import EmbeddingService

    async def mock_get_embedding(self, text: str) -> list:
        return [0.1] * 384  # MiniLM-L6-v2 размер

    monkeypatch.setattr(EmbeddingService, 'get_embedding', mock_get_embedding)


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

