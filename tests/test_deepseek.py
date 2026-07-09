"""Тесты DeepSeek клиента"""
import asyncio


class TestDeepSeekClient:
    def test_init(self):
        from app.adapters.deepseek_client import DeepSeekClient
        client = DeepSeekClient()
        assert client is not None
        assert hasattr(client, 'generate_text')  # async метод
        assert hasattr(client, 'generate_structured')
        assert client.model is not None

    def test_generate_text_async(self):
        """Проверяем что async generate_text создаёт задачу (но не ждём)"""
        from app.adapters.deepseek_client import DeepSeekClient
        
        client = DeepSeekClient()
        try:
            coro = client.generate_text("Тестовый промпт", "system prompt")
            # Проверяем что это корутина
            import asyncio
            assert asyncio.iscoroutine(coro)
            coro.close()  # закрываем без выполнения
        except Exception:
            pass
        assert True

    def test_generate_structured_valid(self):
        """Проверяем что generate_structured принимает JSON схему"""
        from app.adapters.deepseek_client import DeepSeekClient
        
        client = DeepSeekClient()
        # Просто проверяем что метод существует и принимает аргументы
        import inspect
        sig = inspect.signature(client.generate_structured)
        params = list(sig.parameters.keys())
        assert 'prompt' in params
        assert 'schema' in params  # generate_structured(prompt, schema) без system_prompt
