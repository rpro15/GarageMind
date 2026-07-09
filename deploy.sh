#!/bin/bash
# ============================================================
# 🚀 deploy.sh — Быстрый деплой GarageMind одной командой
# Использование: ./deploy.sh
# ============================================================

set -e

echo "🚀 GarageMind — Деплой"
echo "═══════════════════════"
echo ""

# 1. Проверка .env
if [ ! -f .env ]; then
    echo "❌ Файл .env не найден!"
    echo "   Создай: cp .env.example .env"
    exit 1
fi
echo "✅ .env найден"

# 2. Обновить код
echo "📥 Обновление кода..."
git pull origin main
echo "✅ Код обновлён"

# 3. Бекап базы
BACKUP_DATE=$(date +%Y-%m-%d)
BACKUP_DIR="backups/$BACKUP_DATE"
mkdir -p "$BACKUP_DIR"
if [ -f data/garage_mind.db ]; then
    cp data/garage_mind.db "$BACKUP_DIR/"
    echo "✅ Бекап БД: $BACKUP_DIR/garage_mind.db"
fi
if [ -f data/knowledge.db ]; then
    cp data/knowledge.db "$BACKUP_DIR/"
    echo "✅ Бекап знаний: $BACKUP_DIR/knowledge.db"
fi

# 4. Собрать и запустить
echo "🐳 Сборка Docker..."
docker compose down
docker compose up --build -d
echo "✅ Docker запущен"

# 5. Проверка здоровья
echo "⏳ Проверка здоровья..."
sleep 5
for i in 1 2 3 4 5; do
    if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Healthcheck OK"
        break
    fi
    echo "   Попытка $i... ждём"
    sleep 3
done

# 6. Прогрев кэша
echo "🔥 Прогрев кэша..."
curl -s https://rpro.su/api/brands > /dev/null 2>&1 && echo "✅ Brands кэширован" || true

# 7. Очистка
echo "🧹 Очистка..."
docker system prune -f
echo "✅ Очищено"

echo ""
echo "═══════════════════════"
echo "✅ Деплой завершён!"
echo "   https://rpro.su"
echo "   https://rpro.su/health"
