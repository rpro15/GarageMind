"""Тесты DeepSeek клиента"""
import asyncio
import pytest


class TestDeepSeekClient:
    def test_init(self):
        from app.adapters.deepseek_client import DeepSeekClient
        client = DeepSeekClient()
        assert client is not None
        assert hasattr(client, 'generate_text')
        assert hasattr(client, 'generate_structured')
        assert client.model is not None

    @pytest.mark.asyncio
    async def test_generate_text_stub_without_key(self, monkeypatch):
        """Без API-ключа generate_text возвращает заглушку (русский текст)."""
        monkeypatch.setenv('DEEPSEEK_API_KEY', '')
        from app.adapters.deepseek_client import DeepSeekClient
        client = DeepSeekClient()
        client.api_key = ""

        result = await client.generate_text("Тестовый промпт", "system prompt")
        assert result is not None
        assert len(result) > 50
        assert "Michelin" in result or "рекомендуемые" in result or "шин" in result

    @pytest.mark.asyncio
    async def test_generate_text_with_mocked_http(self, monkeypatch):
        """С мокнутым httpx.AsyncClient.post."""
        from app.adapters.deepseek_client import DeepSeekClient

        monkeypatch.setenv('DEEPSEEK_API_KEY', 'test-key-123')
        client = DeepSeekClient()
        client.api_key = "test-key-123"

        called = False

        class MockResponse:
            def __init__(self):
                self.status_code = 200
            def json(self):
                return {
                    'choices': [{
                        'message': {'content': 'Рекомендую шины Michelin.'}
                    }]
                }
            def raise_for_status(self):
                pass

        async def mock_post(*args, **kwargs):
            nonlocal called
            called = True
            return MockResponse()

        import httpx
        monkeypatch.setattr(httpx.AsyncClient, 'post', mock_post)

        result = await client.generate_text("Подбери шины", "Ты эксперт")
        assert called
        assert result == 'Рекомендую шины Michelin.'

    def test_generate_text_async(self):
        """Проверяем что async generate_text возвращает корутину."""
        from app.adapters.deepseek_client import DeepSeekClient
        client = DeepSeekClient()
        coro = client.generate_text("Тестовый промпт", "system prompt")
        assert asyncio.iscoroutine(coro)
        coro.close()

    def test_generate_structured_valid(self):
        """Проверяем что generate_structured принимает JSON схему."""
        from app.adapters.deepseek_client import DeepSeekClient
        client = DeepSeekClient()
        import inspect
        sig = inspect.signature(client.generate_structured)
        params = list(sig.parameters.keys())
        assert 'prompt' in params
        assert 'schema' in params
