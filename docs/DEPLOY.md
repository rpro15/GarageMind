# 🚀 DevOps Deployment Guide — GarageMind AI

**Полное руководство по деплою Telegram Mini App с нуля до продакшена**

---

## 📋 Содержание

1. [Архитектура](#1-архитектура)
2. [Требования](#2-требования)
3. [Этап 1 — VPS и базовая настройка](#3-этап-1--vps-и-базовая-настройка)
4. [Этап 2 — Клонирование и .env](#4-этап-2--клонирование-и-env)
5. [Этап 3 — Docker Compose](#5-этап-3--docker-compose)
6. [Этап 4 — Nginx Reverse Proxy](#6-этап-4--nginx-reverse-proxy)
7. [Этап 5 — SSL (Let's Encrypt)](#7-этап-5--ssl-lets-encrypt)
8. [Этап 6 — Запуск приложения](#8-этап-6--запуск-приложения)
9. [Этап 7 — Telegram Mini App](#9-этап-7--telegram-mini-app)
10. [Этап 8 — RAG индексация](#10-этап-8--rag-индексация)
11. [Этап 9 — Мониторинг (опционально)](#11-этап-9--мониторинг-опционально)
12. [Этап 10 — CI/CD (GitHub Actions)](#12-этап-10--cicd-github-actions)
13. [Безопасность](#13-безопасность)
14. [Production — ChromaDB → Qdrant](#14-production--chromadb--qdrant)
15. [Полезные команды](#15-полезные-команды)

---

## 1. Архитектура

```
┌─────────────────────────────────────────────────────┐
│                   Cloudflare                         │
│                   (DNS + DDoS)                       │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│               Let's Encrypt (SSL)                    │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│                  Nginx (порт 443)                    │
│          ┌─────────┴──────────┐                     │
│          │  /api/*            │  /miniapp/*         │
│          │  proxy -> Flask    │  static files       │
│          └─────────┬──────────┘                     │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│              Docker Network                          │
│                                                      │
│  ┌──────────────────────────────────────────────┐   │
│  │  garage-mind-api (Flask :8000)               │   │
│  │  ├── DeepSeek API (эмбеддинги + LLM)         │   │
│  │  ├── ChromaDB (векторная БД)                 │   │
│  │  ├── Mock Partner API (каталог)              │   │
│  │  └── Prometheus метрики                      │   │
│  └──────────────────────────────────────────────┘   │
│                                                      │
│  ┌──────────────────────────────────────────────┐   │
│  │  Redis (кэш, очереди)                        │   │
│  └──────────────────────────────────────────────┘   │
│                                                      │
│  ┌──────────────────────────────────────────────┐   │
│  │  Qdrant (векторная БД — для продакшена)      │   │
│  └──────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

---

## 2. Требования

### Минимальные
- **VPS**: 1 vCPU, 2 GB RAM, 20 GB SSD
- **OS**: Ubuntu 22.04 / 24.04 LTS
- **Домен**: привязан к Cloudflare

### Рекомендуемые
- **VPS**: 2 vCPU, 4 GB RAM, 40 GB SSD
- **OS**: Ubuntu 24.04 LTS
- **Домен**: через Cloudflare (прокси включён — оранжевая туча)

### Что нам понадобится
- **Docker** + **Docker Compose** — контейнеризация
- **Nginx** — reverse proxy (в контейнере или на хосте)
- **Let's Encrypt (certbot)** — SSL сертификаты
- **Git** — для клонирования проекта
- **Python 3.13** — рантайм (идёт в Docker образе)

---

## 3. Этап 1 — VPS и базовая настройка

### 3.1. Заходим на сервер

```bash
ssh root@<IP_ВАШЕГО_СЕРВЕРА>
```

### 3.2. Создаём пользователя (безопасность)

```bash
adduser garagemind
usermod -aG sudo garagemind

# Копируем SSH ключ
mkdir -p /home/garagemind/.ssh
cp ~/.ssh/authorized_keys /home/garagemind/.ssh/
chown -R garagemind:garagemind /home/garagemind/.ssh

# Отключаем вход под root
sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
systemctl restart sshd
```

### 3.3. Обновляем систему

```bash
sudo apt update && sudo apt upgrade -y
sudo apt autoremove -y
```

### 3.4. Устанавливаем Docker

```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker garagemind

# Docker Compose (плагин)
sudo apt install docker-compose-plugin -y

# Проверка
docker --version
docker compose version
```

### 3.5. Настраиваем файрвол

```bash
sudo apt install ufw -y

# Только нужные порты
sudo ufw allow 22/tcp        # SSH
sudo ufw allow 80/tcp        # HTTP
sudo ufw allow 443/tcp       # HTTPS
sudo ufw allow 9090/tcp      # Prometheus (если будет)
sudo ufw allow 3000/tcp      # Grafana (если будет)

# ЗАПРЕЩАЕМ доступ к 8000 извне!
sudo ufw deny 8000/tcp

sudo ufw enable
sudo ufw status verbose
```

### 🔍 Чекпоинт ✅

```bash
# Выйти и зайти под новым пользователем
exit
ssh garagemind@<IP_ВАШЕГО_СЕРВЕРА>

docker --version    # Должен показать версию
docker compose version  # Должен показать версию
```

---

## 4. Этап 2 — Клонирование и .env

### 4.1. Клонируем проект

```bash
cd /opt
sudo mkdir -p /opt/garage-mind
sudo chown garagemind:garagemind /opt/garage-mind
cd /opt/garage-mind

git clone https://github.com/rpro15/GarageMind.git .
```

### 4.2. Создаём .env с реальными данными

```bash
nano .env
```

Вставьте это (заменив значения на свои):

```ini
# === DeepSeek ===
DEEPSEEK_API_KEY=sk-ваш_реальный_ключ_от_DeepSeek
DEEPSEEK_MODEL=deepseek-chat

# === Flask ===
SECRET_KEY=<сгенерируйте командой ниже>
LOG_LEVEL=INFO
PORT=8000

# === Telegram Bot ===
BOT_TOKEN=ваш_токен_от_BotFather

# === Redis ===
REDIS_URL=redis://redis:6379/0

# === Mini App ===
MINIAPP_URL=https://ваш-домен.ru/miniapp/
```

Сгенерировать `SECRET_KEY`:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### 4.3. Создаём папки для данных

```bash
mkdir -p data/chromadb data/logs data/qdrant
```

### 🔍 Чекпоинт ✅

```bash
ls -la .env
cat .env | grep -v TOKEN | grep -v SECRET  # проверить, что не пустой
```

---

## 5. Этап 3 — Docker Compose

Актуальный `docker-compose.yml` уже в проекте. Вот что он делает:

```yaml
version: '3.8'

services:
  api:
    build: .                          # Собирает из Dockerfile
    container_name: garage-mind-api
    restart: always
    ports:
      - "8000:8000"                   # Внутри Docker, Nginx проксирует
    env_file: .env                     # Все секреты из .env
    volumes:
      - ./data/chromadb:/data/chromadb  # ChromaDB persistent
      - ./data/logs:/app/logs           # Логи
    healthcheck:                        # Docker проверяет живость
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 5s
      start_period: 10s
      retries: 3
    networks:
      - garage-mind-net

  redis:
    image: redis:alpine               # Кэш + очереди
    container_name: garage-mind-redis
    restart: always
    volumes:
      - ./data/redis:/data
    networks:
      - garage-mind-net

  nginx:
    image: nginx:alpine               # Reverse Proxy + SSL
    container_name: garage-mind-nginx
    restart: always
    ports:
      - "80:80"                        # HTTP (редирект на HTTPS)
      - "443:443"                      # HTTPS
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf
      - ./app/miniapp/static:/usr/share/nginx/html/miniapp
      - /etc/letsencrypt:/etc/letsencrypt:ro  # SSL серты
    depends_on:
      - api
    networks:
      - garage-mind-net

networks:
  garage-mind-net:
    driver: bridge
```

### Сборка и запуск (пока без SSL, для проверки)

```bash
# Пропускаем nginx пока (SSL ещё нет)
docker compose up -d api redis

# Смотрим логи
docker compose logs -f api
```

---

## 6. Этап 4 — Nginx Reverse Proxy

### 6.1. Устанавливаем Nginx на хост (если не через контейнер)

```bash
sudo apt install nginx -y
sudo systemctl enable nginx
sudo systemctl start nginx
```

### 6.2. Создаём конфиг

```bash
sudo nano /etc/nginx/sites-available/garage-mind
```

```nginx
server {
    listen 80;
    server_name ваш-домен.ru www.ваш-домен.ru;

    # Логи
    access_log /var/log/nginx/garage-mind-access.log;
    error_log /var/log/nginx/garage-mind-error.log;

    # Mini App (Telegram Web App) — статика
    location /miniapp/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # API запросы
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Увеличиваем лимиты для больших запросов
        client_max_body_size 10M;
        proxy_read_timeout 60s;
    }

    # Healthcheck
    location /health {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
    }

    # Корень — редирект на Mini App
    location / {
        return 301 /miniapp/index.html;
    }
}
```

```bash
# Включаем сайт
sudo ln -s /etc/nginx/sites-available/garage-mind /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default  # удаляем дефолтный

# Проверяем конфиг
sudo nginx -t

# Перезагружаем
sudo systemctl reload nginx
```

### 🔍 Чекпоинт ✅

```bash
curl -I http://localhost
# Должен вернуть 301 → /miniapp/index.html

curl http://localhost/health
# {"service":"avto-expert-ai","status":"ok"}
```

---

## 7. Этап 5 — SSL (Let's Encrypt)

### 7.1. Устанавливаем certbot

```bash
sudo apt install certbot python3-certbot-nginx -y
```

### 7.2. Получаем сертификат

```bash
sudo certbot --nginx -d ваш-домен.ru -d www.ваш-домен.ru

# Следуйте инструкциям:
# 1. Введите email для уведомлений
# 2. Согласитесь с условиями (A)
# 3. Выберите редирект HTTP→HTTPS (2)
```

### 7.3. Проверяем автообновление

```bash
sudo certbot renew --dry-run

# Таймер автообновления
systemctl list-timers | grep certbot
```

### 7.4. Даём Docker доступ к сертификатам

```bash
# Сертификаты лежат в /etc/letsencrypt
# Docker контейнер nginx уже имеет доступ (read-only)
```

### 🔍 Чекпоинт ✅

```bash
curl -I https://ваш-домен.ru
# Должен вернуть 301 → /miniapp/index.html

curl https://ваш-домен.ru/health
# {"service":"avto-expert-ai","status":"ok"}
```

---

## 8. Этап 6 — Запуск приложения

### 8.1. Полный запуск

```bash
cd /opt/garage-mind

# Останавливаем если что-то запущено
docker compose down

# Собираем и запускаем всё
docker compose up -d --build

# Проверяем
docker compose ps
```

### 8.2. Проверка

```bash
# Healthcheck
curl https://ваш-домен.ru/health

# API
curl https://ваш-домен.ru/api/brands

# Mini App
curl -I https://ваш-домен.ru/miniapp/index.html
```

### 8.3. Логи

```bash
# Все логи
docker compose logs -f

# Только API
docker compose logs -f api

# Только Nginx
docker compose logs -f nginx
```

### 8.4. Рестарт

```bash
# После изменений в коде
docker compose up -d --build api

# Полный рестарт
docker compose down && docker compose up -d
```

---

## 9. Этап 7 — Telegram Mini App

### 9.1. Настройка бота

1. Откройте [@BotFather](https://t.me/BotFather)
2. Выберите своего бота → **Bot Settings**
3. **Menu Button** → укажите:
   ```
   https://ваш-домен.ru/miniapp/index.html
   ```
4. **Domain** → укажите:
   ```
   ваш-домен.ru
   ```

### 9.2. Проверка

1. Откройте бота в Telegram
2. Нажмите кнопку меню внизу
3. Должна открыться Mini App

---

## 10. Этап 8 — RAG индексация

### 10.1. Первичная индексация

```bash
# Заходим в контейнер и запускаем индексацию
docker compose exec api python -m app.services.rag.index_catalog

# Должны увидеть:
# ✅ Индексировано X товаров в векторную базу
#    Всего в базе: X
```

### 10.2. Проверка RAG

```bash
curl -X POST https://ваш-домен.ru/api/recommend_tires \
  -H "Content-Type: application/json" \
  -d '{"brand":"Toyota","model":"Camry","year":2024,"driving_style":"comfort","season":"summer"}'
```

---

## 11. Этап 9 — Мониторинг (опционально)

### 11.1. Добавляем Prometheus + Grafana в docker-compose.yml

Добавьте в `docker-compose.yml`:

```yaml
  prometheus:
    image: prom/prometheus:latest
    container_name: garage-mind-prometheus
    restart: always
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - ./data/prometheus:/prometheus
    ports:
      - "9090:9090"
    networks:
      - garage-mind-net

  grafana:
    image: grafana/grafana:latest
    container_name: garage-mind-grafana
    restart: always
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin123  # Сменить!
    volumes:
      - ./data/grafana:/var/lib/grafana
    ports:
      - "3000:3000"
    depends_on:
      - prometheus
    networks:
      - garage-mind-net
```

### 11.2. Создаём prometheus.yml

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'garage-mind-api'
    static_configs:
      - targets: ['api:8000']
```

### 11.3. Дашборд

1. Открыть `https://ваш-домен.ru:3000`
2. Логин: `admin`, пароль: `admin123`
3. Add data source → Prometheus → `http://prometheus:9090`
4. Import dashboard → вставить ID: `1860` (Flask dashboard)

---

## 12. Этап 10 — CI/CD (GitHub Actions)

### 12.1. Создаём `.github/workflows/deploy.yml`

```bash
mkdir -p .github/workflows
nano .github/workflows/deploy.yml
```

```yaml
name: Deploy to VPS

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Deploy via SSH
        uses: appleboy/ssh-action@v1.0.0
        with:
          host: ${{ secrets.HOST }}
          username: ${{ secrets.USER }}
          key: ${{ secrets.SSH_KEY }}
          script: |
            cd /opt/garage-mind
            docker compose pull
            docker compose down
            docker compose up -d --build
            docker system prune -f
```

### 12.2. Настройка секретов GitHub

Перейдите в GitHub репозиторий:
- Settings → Secrets and variables → Actions
- Add **3 secrets**:

| Secret | Значение |
|:-------|:---------|
| `HOST` | IP вашего VPS |
| `USER` | `garagemind` |
| `SSH_KEY` | Приватный SSH ключ |

### 12.3. Генерация SSH ключа

```bash
# На VPS
ssh-keygen -t ed25519 -f ~/.ssh/deploy_key
cat ~/.ssh/deploy_key.pub >> ~/.ssh/authorized_keys
cat ~/.ssh/deploy_key   # скопировать в GitHub Secrets
```

---

## 13. Безопасность

### 13.1. ❌ Чего НЕ делать

- ❌ Открывать порт 8000 наружу (только через Nginx)
- ❌ Пушить `.env` в Git (он уже в `.gitignore`)
- ❌ Использовать дефолтные пароли
- ❌ Давать root доступ приложению

### 13.2. ✅ Что нужно сделать

- ✅ Ограничить доступ к `/api` по IP (опционально)
- ✅ Использовать `ufw` или `iptables`
- ✅ Регулярно обновлять Docker образы
- ✅ Следить за логами на предмет ошибок
- ✅ Сделать бэкапы `data/chromadb` и `data/redis`

### 13.3. Бэкапы

```bash
# Создать скрипт бэкапа /opt/garage-mind/backup.sh
#!/bin/bash
BACKUP_DIR="/opt/backups/garage-mind"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

docker compose exec -T redis redis-cli SAVE
tar -czf "$BACKUP_DIR/garage-mind-$DATE.tar.gz" \
  /opt/garage-mind/data \
  /opt/garage-mind/.env

# Хранить 7 дней
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
```

Добавить в cron:

```bash
crontab -e
# Добавить строку:
0 3 * * * /opt/garage-mind/backup.sh
```

---

## 14. Production — ChromaDB → Qdrant

Когда товаров станет > 10 000, замените ChromaDB на Qdrant.

### 14.1. Добавить в docker-compose.yml

```yaml
  qdrant:
    image: qdrant/qdrant:latest
    container_name: garage-mind-qdrant
    restart: always
    ports:
      - "6333:6333"   # gRPC
      - "6334:6334"   # HTTP API
    volumes:
      - ./data/qdrant:/qdrant/storage
    environment:
      - QDRANT__SERVICE__GRPC_PORT=6333
      - QDRANT__SERVICE__HTTP_PORT=6334
    networks:
      - garage-mind-net
```

### 14.2. Обновить VectorStore

Заменить импорт в `app/services/rag/vector_store.py`:

```python
# Было
from chromadb import ...

# Стало
from qdrant_client import QdrantClient
```

---

## 15. Полезные команды

### Docker

```bash
# Статус всех контейнеров
docker compose ps

# Логи конкретного сервиса
docker compose logs -f api
docker compose logs -f nginx

# Перезапуск одного сервиса
docker compose restart api

# Полный перезапуск
docker compose down && docker compose up -d

# Очистка неиспользуемых образов
docker system prune -f
```

### Nginx

```bash
# Проверка конфига
sudo nginx -t

# Перезагрузка
sudo systemctl reload nginx

# Просмотр логов
sudo tail -f /var/log/nginx/garage-mind-access.log
sudo tail -f /var/log/nginx/garage-mind-error.log
```

### SSL

```bash
# Проверка сертификата
sudo certbot certificates

# Принудительное обновление
sudo certbot renew --force-renewal

# Тест автообновления
sudo certbot renew --dry-run
```

### Система

```bash
# Использование диска
df -h

# Память
free -h

# Нагрузка
htop

# Docker занимаемое место
docker system df
```

---

## 🎉 Поздравляю!

После выполнения всех этапов у тебя будет:

- ✅ **Production Flask API** с Docker
- ✅ **Nginx** с SSL (HTTPS)
- ✅ **Telegram Mini App** на домене
- ✅ **RAG-поиск** через ChromaDB + DeepSeek
- ✅ **Redis** для кэша
- ✅ **Prometheus + Grafana** мониторинг
- ✅ **CI/CD** автодеплой через GitHub
- ✅ **Бэкапы** каждый день

---

**© 2026 Garage Mind AI** — Если что-то непонятно, просто спроси!
