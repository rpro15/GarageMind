"""WSGI entry point for Gunicorn.
Запуск: gunicorn wsgi:app -c gunicorn.conf.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.main import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)
