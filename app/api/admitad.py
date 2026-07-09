"""
Admitad OAuth — получение API ключа через редирект.

Как зарегистрировать приложение в Admitad:
1. Зайти: https://www.admitad.com/ru/webmaster/
2. Настройки → API → Создать приложение
3. Указать Redirect URI: https://rpro.su/api/admitad/callback
4. Получить client_id и client_secret
5. Вписать в .env: ADMITAD_CLIENT_ID, ADMITAD_CLIENT_SECRET

Поток:
   Пользователь → /api/admitad/auth → Admitad OAuth → редирект на callback
   → получаем токен → сохраняем в кэш → готово
"""
import logging
import os
from urllib.parse import urlencode

import httpx
from flask import Blueprint, jsonify, redirect, request, current_app

from app.config.settings import settings

logger = logging.getLogger(__name__)

admitad_blueprint = Blueprint("admitad", __name__, url_prefix="/api/admitad")

# === Конфигурация OAuth ===
ADMITAD_AUTH_URL = "https://www.admitad.com/ru/webmaster/oauth/"
ADMITAD_TOKEN_URL = "https://api.admitad.com/token/"
REDIRECT_URI = "https://rpro.su/api/admitad/callback"


@admitad_blueprint.route("/auth")
def auth():
    """
    Шаг 1: Редирект на страницу авторизации Admitad.
    Нажать эту ссылку → попасть на Admitad → подтвердить → вернуться на callback.
    """
    client_id = settings.ADMITAD_CLIENT_ID or os.getenv("ADMITAD_CLIENT_ID", "")
    if not client_id:
        return jsonify({
            "error": "Admitad не настроен",
            "message": "Добавь ADMITAD_CLIENT_ID и ADMITAD_CLIENT_SECRET в .env",
            "docs": "https://github.com/rpro15/GarageMind#admitad",
        }), 400

    params = {
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": "advcampaigns banners coupons websites",
    }
    url = f"{ADMITAD_AUTH_URL}?{urlencode(params)}"
    logger.info("Redirecting to Admitad OAuth: %s", url)
    return redirect(url)


@admitad_blueprint.route("/callback")
def callback():
    """
    Шаг 2: Обработка редиректа от Admitad после авторизации.
    Admitad присылает ?code=... — мы обмениваем его на access_token.
    """
    code = request.args.get("code")
    error = request.args.get("error")

    if error:
        logger.warning("Admitad OAuth error: %s", error)
        return jsonify({"error": f"Admitad отказал: {error}"}), 400

    if not code:
        return jsonify({"error": "Missing code parameter"}), 400

    client_id = settings.ADMITAD_CLIENT_ID or os.getenv("ADMITAD_CLIENT_ID", "")
    client_secret = settings.ADMITAD_CLIENT_SECRET or os.getenv("ADMITAD_CLIENT_SECRET", "")

    if not client_id or not client_secret:
        return jsonify({"error": "Admitad не настроен — нет ADMITAD_CLIENT_ID/SECRET в .env"}), 400

    # Обмениваем code на токен
    try:
        resp = httpx.post(
            ADMITAD_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "client_id": client_id,
                "client_secret": client_secret,
                "code": code,
                "redirect_uri": REDIRECT_URI,
            },
            timeout=15,
        )
        data = resp.json()
    except Exception as e:
        logger.error("Admitad token exchange failed: %s", e)
        return jsonify({"error": "Не удалось получить токен"}), 502

    if resp.status_code != 200:
        logger.warning("Admitad token error: %s", data)
        return jsonify({"error": data.get("error_description", "Unknown error")}), 400

    access_token = data.get("access_token")
    refresh_token = data.get("refresh_token")

    if not access_token:
        return jsonify({"error": "No access_token in response"}), 400

    # Сохраняем токен в кэш (на час, как живёт токен)
    try:
        cache = current_app.extensions.get("services", {}).get("cache")
        if cache and hasattr(cache, 'set'):
            import asyncio
            asyncio.run(cache.set("admitad:access_token", access_token, ttl=3600))
            if refresh_token:
                asyncio.run(cache.set("admitad:refresh_token", refresh_token, ttl=86400))
    except Exception as e:
        logger.warning("Failed to save token to cache: %s", e)

    logger.info("✅ Admitad OAuth успешен! Токен получен.")

    # Перенаправляем на страницу успеха
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>✅ Admitad подключён</title>
        <meta http-equiv="refresh" content="5;url=/">
        <style>
            body {{ font-family: sans-serif; text-align: center; padding: 50px; background: #1a1a2e; color: #fff; }}
            .card {{ background: #16213e; border-radius: 12px; padding: 30px; max-width: 500px; margin: 0 auto; }}
            h1 {{ color: #4ade80; }}
            .success {{ font-size: 48px; }}
            .hint {{ color: #94a3b8; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="card">
            <div class="success">✅</div>
            <h1>Admitad подключён!</h1>
            <p>API токен получен и сохранён в кэш.</p>
            <p class="hint">Через 5 секунд вы будете перенаправлены на главную.</p>
        </div>
    </body>
    </html>
    """


@admitad_blueprint.route("/status")
def status():
    """
    Проверка статуса подключения Admitad.
    """
    client_id = settings.ADMITAD_CLIENT_ID or os.getenv("ADMITAD_CLIENT_ID", "")
    client_secret = settings.ADMITAD_CLIENT_SECRET or os.getenv("ADMITAD_CLIENT_SECRET", "")

    has_credentials = bool(client_id and client_secret)

    # Проверяем, есть ли токен в кэше
    has_token = False
    try:
        cache = current_app.extensions.get("services", {}).get("cache")
        if cache and hasattr(cache, 'get'):
            import asyncio
            token = asyncio.run(cache.get("admitad:access_token"))
            has_token = bool(token)
    except Exception:
        pass

    return jsonify({
        "configured": has_credentials,
        "authorized": has_token,
        "message": (
            "✅ Admitad готов к работе" if has_token else
            "🔑 Есть ключи, но нет токена. Нажми /api/admitad/auth" if has_credentials else
            "❌ Admitad не настроен. Добавь ADMITAD_CLIENT_ID и ADMITAD_CLIENT_SECRET в .env"
        ),
        "auth_url": "/api/admitad/auth" if has_credentials else None,
    })


@admitad_blueprint.route("/verify")
def verify():
    """
    Страница верификации для Admitad.
    Admitad может запросить подтверждение, что сайт принадлежит нам.
    """
    return jsonify({
        "status": "ok",
        "service": "GarageMind AI",
        "owner": "rpro15",
        "admitad_integration": "active",
    }), 200
