"""WSGI entry point for Gunicorn.
Запуск: gunicorn wsgi:app -c gunicorn.conf.py

Важно: загружает .env из корня проекта.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Загружаем .env до создания app, чтобы Settings видел переменные
from dotenv import load_dotenv
dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

from app.main import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)

