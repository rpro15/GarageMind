# app/main.py
import os
import asyncio
import threading
from flask import Flask
from flask_cors import CORS
from app.api.routes import api_bp
from app.config.settings import settings
import logging

logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = settings.SECRET_KEY
CORS(app)  # разрешаем CORS для Mini App

app.register_blueprint(api_bp)

def run_bot():
    """Запуск Telegram бота в отдельном потоке."""
    from app.bot.dispatcher import start_bot
    asyncio.run(start_bot())

def main():
    # Запускаем бота в фоновом потоке
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == "__main__":
    main()