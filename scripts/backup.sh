#!/bin/bash
# ============================================================
# 📦 backup.sh — Бекап базы данных GarageMind
# Запуск: ./scripts/backup.sh
# Cron: 0 3 * * * /opt/garage-mind/scripts/backup.sh
# ============================================================

set -e

BACKUP_DIR="/opt/backups/garage-mind"
APP_DIR="/opt/garage-mind"
DATE=$(date +%Y-%m-%d)
RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-30}

mkdir -p "$BACKUP_DIR"

echo "📦 Бекап GarageMind — $DATE"
echo "══════════════════════════════"

# 1. Бекап SQLite
if [ -f "$APP_DIR/data/garage_mind.db" ]; then
    sqlite3 "$APP_DIR/data/garage_mind.db" ".backup '$BACKUP_DIR/garage_mind_$DATE.db'"
    gzip "$BACKUP_DIR/garage_mind_$DATE.db"
    SIZE=$(ls -la "$BACKUP_DIR/garage_mind_$DATE.db.gz" | awk '{print $5}')
    echo "✅ SQLite: $SIZE байт"
else
    echo "⚠️ Нет файла garage_mind.db"
fi

# 2. Бекап knowledge.db
if [ -f "$APP_DIR/data/knowledge.db" ]; then
    sqlite3 "$APP_DIR/data/knowledge.db" ".backup '$BACKUP_DIR/knowledge_$DATE.db'"
    gzip "$BACKUP_DIR/knowledge_$DATE.db"
    echo "✅ Knowledge: готово"
fi

# 3. Бекап .env
if [ -f "$APP_DIR/.env" ]; then
    cp "$APP_DIR/.env" "$BACKUP_DIR/env_$DATE.txt"
    echo "✅ .env сохранён"
fi

# 4. Чистка старых бекапов
find "$BACKUP_DIR" -name "*.gz" -mtime +$RETENTION_DAYS -delete
echo "🧹 Старые бекапы (>${RETENTION_DAYS}д) удалены"

# 5. Итог
echo "══════════════════════════════"
echo "📂 $BACKUP_DIR"
ls -lah "$BACKUP_DIR"/*.gz 2>/dev/null | awk '{print "   ", $5, $NF}'
echo "✅ Бекап завершён"
