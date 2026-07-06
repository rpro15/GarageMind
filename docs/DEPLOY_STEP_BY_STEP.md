# 🚀 Пошаговая инструкция по деплою GarageMind AI на rpro.su

> **Для кого**: ты — начинающий DevOps  
> **Цель**: запустить проект на своём VPS с доменом rpro.su  
> **Время**: ~1 час, если всё готово  

---

## 📋 Что нам понадобится

- **VPS** (Ubuntu 22.04/24.04) — доступ по SSH
- **Домен** rpro.su — направлен на IP сервера
- **GitHub** аккаунт (чтобы склонировать проект)

---

## 🎯 Этап 1 — Подготовка сервера

### 1.1. Заходим на сервер по SSH

```bash
ssh root@<IP_ВАШЕГО_СЕРВЕРА>
```

Введи пароль (если запросит).

### 1.2. Создаём отдельного пользователя (безопасно)

```bash
adduser garagemind          # создаём пользователя
usermod -aG sudo garagemind  # даём права sudo

# Копируем SSH-ключ, чтобы заходить без пароля
mkdir -p /home/garagemind/.ssh
cp ~/.ssh/authorized_keys /home/garagemind/.ssh/
chown -R garagemind:garagemind /home/garagemind/.ssh
```

### 1.3. Запрещаем вход под root

```bash
sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
systemctl restart sshd
```

### 1.4. Выходим и заходим под новым пользователем

```bash
exit
# Теперь заходим как garagemind
ssh garagemind@<IP_ВАШЕГО_СЕРВЕРА>
```

### 1.5. Обновляем пакеты

```bash
sudo apt update && sudo apt upgrade -y
sudo apt autoremove -y
```

---

## 🐳 Этап 2 — Установка Docker

### 2.1. Ставим Docker

```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker garagemind
```

### 2.2. Ставим Docker Compose

```bash
sudo apt install docker-compose-plugin -y
```

### 2.3. Проверяем, что всё встало

```bash
docker --version
docker compose version
```

Если видишь версии — ✅

---

## 🔥 Этап 3 — Настройка файрвола (UFW)

```bash
sudo apt install ufw -y

# Разрешаем только нужное
sudo ufw allow 22/tcp        # SSH
sudo ufw allow 80/tcp        # HTTP
sudo ufw allow 443/tcp       # HTTPS

# ЗАПРЕЩАЕМ порт 8000 (доступ к API только через Nginx!)
sudo ufw deny 8000/tcp

# Включаем
sudo ufw enable

# Проверяем
sudo ufw status verbose
```

---

## 📂 Этап 4 — Клонируем проект

### 4.1. Создаём папку

```bash
cd /opt
sudo mkdir -p /opt/garage-mind
sudo chown garagemind:garagemind /opt/garage-mind
cd /opt/garage-mind
```

### 4.2. Клонируем репозиторий

```bash
git clone https://github.com/rpro15/GarageMind.git .
```

### 4.3. Создаём папки для данных

```bash
mkdir -p data/chromadb data/logs
```

### 4.4. Создаём .env файл

```bash
nano .env
```

Вставь это (заменив значения на свои):

```ini
# === DeepSeek AI ===
DEEPSEEK_API_KEY=sk-ваш_ключ_от_DeepSeek
DEEPSEEK_MODEL=deepseek-chat

# === Flask ===
SECRET_KEY=придумай_сложный_ключ_из_букв_и_цифр
LOG_LEVEL=INFO

# === Telegram Bot (опционально) ===
BOT_TOKEN=

# === Redis (кэш) ===
REDIS_URL=redis://redis:6379/0

# === Mini App ===
MINIAPP_URL=https://rpro.su/miniapp/

# === Автосборщик знаний ===
COLLECTOR_DAILY_LIMIT=100
AUTO_COLLECTOR_INTERVAL_MINUTES=60
```

**Как придумать SECRET_KEY:**
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

**💡 Если нет DEEPSEEK_API_KEY** — оставь пустым.  
Проект будет работать в режиме заглушек (мок-данные).

Сохрани: `Ctrl+X`, потом `Y`, потом `Enter`.

---

## 🏗️ Этап 5 — Запускаем через Docker Compose

### 5.1. Запускаем сначала Redis и API

```bash
docker compose up -d redis api
```

### 5.2. Смотрим логи

```bash
docker compose logs -f api
```

Подожди 10-15 секунд. Должен увидеть:
```
AutoCollector started...
Starting Flask server on 0.0.0.0:8000
```

Выйди из логов: `Ctrl+C`

### 5.3. Проверяем, что API работает

```bash
curl http://localhost:8000/health
```

Должен вернуть:
```json
{"status":"ok","service":"avto-expert-ai"}
```

### 5.4. Заполняем базу начальными данными

```bash
docker compose exec api python -m app.services.database.migrations.seed_data
```

Должен увидеть:
```
✅ Добавлено 10 моделей авто
✅ Добавлено 7 отзывов
✅ Добавлено 4 проблем
✅ Добавлено 4 ТТХ шин
```

---

## 🌐 Этап 6 — Настройка Nginx

### 6.1. Ставим Nginx

```bash
sudo apt install nginx -y
sudo systemctl enable nginx
sudo systemctl start nginx
```

### 6.2. Создаём конфиг

```bash
sudo nano /etc/nginx/sites-available/garage-mind
```

Вставь это:

```nginx
server {
    listen 80;
    server_name rpro.su www.rpro.su;

    access_log /var/log/nginx/garage-mind-access.log;
    error_log /var/log/nginx/garage-mind-error.log;

    # Mini App — фронтенд
    location /miniapp/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
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

Сохрани: `Ctrl+X`, потом `Y`, потом `Enter`.

### 6.3. Включаем сайт

```bash
sudo ln -s /etc/nginx/sites-available/garage-mind /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default  # удаляем дефолтный

# Проверяем конфиг
sudo nginx -t

# Должен быть ответ: test is successful
```

### 6.4. Перезагружаем Nginx

```bash
sudo systemctl reload nginx
```

### 6.5. Проверяем через браузер

Открой в браузере: `http://rpro.su`

Должен открыться Mini App (если DNS уже настроен).

Проверь API:
```bash
curl http://localhost/health
curl http://localhost/api/brands
```

---

## 🔒 Этап 7 — SSL Сертификат (Let's Encrypt)

### 7.1. Ставим certbot

```bash
sudo apt install certbot python3-certbot-nginx -y
```

### 7.2. Получаем сертификат

```bash
sudo certbot --nginx -d rpro.su -d www.rpro.su
```

В процессе:
1. Введи email (для уведомлений о продлении)
2. Согласись с условиями — `A`
3. Выбери редирект HTTP → HTTPS — `2`

### 7.3. Проверяем HTTPS

Открой: `https://rpro.su`

Проверь:
```bash
curl https://rpro.su/health
curl https://rpro.su/api/brands
```

### 7.4. Проверяем автообновление SSL

```bash
sudo certbot renew --dry-run
```

Если видишь `Congratulations` — ✅ SSL будет обновляться автоматически.

---

## 📱 Этап 8 — Настройка Telegram Mini App

### 8.1. Открой @BotFather

Перейди в Telegram → найди [@BotFather](https://t.me/BotFather)

### 8.2. Настрой кнопку меню

Напиши команду: `/mybots` → выбери своего бота → **Bot Settings** → **Menu Button**

Укажи URL:
```
https://rpro.su/miniapp/index.html
```

### 8.3. Добавь домен

Там же: **Bot Settings** → **Domain**

Укажи:
```
rpro.su
```

### 8.4. Проверь

Открой бота в Telegram → нажми кнопку меню внизу слева.

Должна открыться Mini App 🚗

---

## 🔄 Этап 9 — Полезные команды

### Логи

```bash
# Все сервисы
docker compose logs -f

# Только API
docker compose logs -f api

# Только Nginx
sudo tail -f /var/log/nginx/garage-mind-access.log
```

### Перезапуск

```bash
# После изменений в коде
docker compose up -d --build api

# Полный перезапуск
docker compose down && docker compose up -d
```

### Проверка БД

```bash
# Сколько собрано данных
docker compose exec api python -c "
from app.services.database import DatabaseService
db = DatabaseService()
stats = db.stats()
print(f'Авто: {stats[\"cars\"]}')
print(f'Отзывов: {stats[\"reviews\"]}')
print(f'Размер БД: {stats[\"db_size_mb\"]} MB')
"
```

### Проверка автосборщика

```bash
# Разовый сбор отзывов
docker compose exec api python -m app.services.knowledge.auto_collector

# Демон (если main.py не запущен)
docker compose exec api python -m app.services.knowledge.auto_collector --daemon
```

---

## 🧪 Этап 10 — Проверка API (тесты)

```bash
# Проверить все эндпоинты
curl https://rpro.su/health

# Список брендов
curl https://rpro.su/api/brands

# Модели
curl "https://rpro.su/api/models?brand=Toyota"

# Рекомендация шин
curl -X POST https://rpro.su/api/recommend_tires \
  -H "Content-Type: application/json" \
  -d '{"brand":"Toyota","model":"Camry","year":2024,"driving_style":"comfort","season":"summer"}'

# Распознавание VIN
curl "https://rpro.su/api/decode-vin?vin=1HGCM82633A004352"
```

---

## 🛠️ Что делать, если что-то пошло не так

### 1. Docker не запускается

```bash
# Посмотреть детальные логи
docker compose logs api

# Пересобрать
docker compose down --rmi all
docker compose up -d --build
```

### 2. Nginx 502 Bad Gateway

```bash
# Проверить, работает ли API
curl http://localhost:8000/health

# Если нет — проверить Docker
docker compose ps
docker compose logs api
```

### 3. DNS не работает

```bash
# Проверить,指向 ли домен на сервер
ping rpro.su

# Должен показать твой IP сервера
```

### 4. SSL не обновляется

```bash
# Принудительное обновление
sudo certbot renew --force-renewal

# Проверить сертификат
sudo certbot certificates
```

---

## 🎉 Поздравляю!

После всех этапов ты получишь:

- [x] **Flask API** с DeepSeek AI
- [x] **Nginx** с HTTPS (SSL)
- [x] **Redis** для кэша
- [x] **Telegram Mini App** на rpro.su
- [x] **SQLite база** с авто и отзывами
- [x] **Автосборщик** +100 отзывов в день

---

## 🚀 Что дальше (после деплоя)

1. **Проверь автосборщик** — через день посмотри сколько отзывов собралось
2. **Подключи DeepSeek API** — если оставил пустым, вернись и добавь ключ
3. **Настрой партнёрок** — см. `docs/PARTNER_INTEGRATION.md`
4. **Добавь мониторинг** — Prometheus + Grafana (по желанию)

---

*Вопросы? Спрашивай!*
