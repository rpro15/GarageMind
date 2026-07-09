#!/bin/bash
# ============================================================
# 🔄 restore.sh — Восстановление БД из бекапа
# Использование: ./scripts/restore.sh 2026-01-15
# ============================================================

set -e

DATE=$1
BACKUP_DIR="/opt/backups/garage-mind"
APP_DIR="/opt/garage-mind"

if [ -z "$DATE" ]; then
    echo "❌ Укажи дату: ./scripts/restore.sh 2026-01-15"
    echo ""
    echo "Доступные бекапы:"
    ls -lah "$BACKUP_DIR"/*.gz 2>/dev/null | awk '{print "  ", $NF}'
    exit 1
fi

echo "🔄 Восстановление из бекапа от $DATE"
echo "══════════════════════════════"

# Останавливаем сервисы
docker compose -f "$APP_DIR/docker-compose.yml" down 2>/dev/null || true

# Восстанавливаем SQLite
if [ -f "$BACKUP_DIR/garage_mind_$DATE.db.gz" ]; then
    gunzip -c "$BACKUP_DIR/garage_mind_$DATE.db.gz" > "$APP_DIR/data/garage_mind.db"
    echo "✅ garage_mind.db восстановлен"
fi

if [ -f "$BACKUP_DIR/knowledge_$DATE.db.gz" ]; then
    gunzip -c "$BACKUP_DIR/knowledge_$DATE.db.gz" > "$APP_DIR/data/knowledge.db"
    echo "✅ knowledge.db восстановлен"
fi

if [ -f "$BACKUP_DIR/env_$DATE.txt" ]; then
    cp "$BACKUP_DIR/env_$DATE.txt" "$APP_DIR/.env"
    echo "✅ .env восстановлен"
fi

# Запускаем сервисы
docker compose -f "$APP_DIR/docker-compose.yml" up -d

echo "✅ Восстановление завершено"
echo "   Проверь: curl https://rpro.su/health"
