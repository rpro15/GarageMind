"""
WSGI entry point for Gunicorn.
Запуск: gunicorn wsgi:app -c gunicorn.conf.py
"""
from app.main import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)
