#!/usr/bin/env bash
# ============================================================
# WhatsInTheBox 数据库备份脚本（dev-plan v4 §7.18 / R11）
# 使用 mysqldump 全量备份 MySQL 数据库，按日期生成 .sql 文件。
# 用法：bash backup_db.sh            （默认读取 .env 同目录或环境变量）
#       DB_NAME=whatsinthebox bash backup_db.sh
# 建议：配合 cron 每日执行；保留近 N 天备份。
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="${SCRIPT_DIR}/backups/db"
mkdir -p "${BACKUP_DIR}"

# 尽量从 .env 读取（若存在）
if [ -f "${SCRIPT_DIR}/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  source "${SCRIPT_DIR}/.env"
  set +a
fi

DB_HOST="${DB_HOST:-127.0.0.1}"
DB_PORT="${DB_PORT:-3306}"
DB_USER="${DB_USER:-root}"
DB_PASSWORD="${DB_PASSWORD:-}"
DB_NAME="${DB_NAME:-whatsinthebox}"

DATE="$(date +%Y%m%d_%H%M%S)"
OUT_FILE="${BACKUP_DIR}/${DB_NAME}_${DATE}.sql"
LATEST_LINK="${BACKUP_DIR}/${DB_NAME}_latest.sql"

echo "[$(date)] 开始备份数据库 ${DB_NAME} -> ${OUT_FILE}"

# 使用 --single-transaction 保证一致性，不锁表
MYSQLDUMP_OPTS=(--single-transaction --routines --events --default-character-set=utf8mb4)

if [ -n "${DB_PASSWORD}" ]; then
  mysqldump "${MYSQLDUMP_OPTS[@]}" -h "${DB_HOST}" -P "${DB_PORT}" -u "${DB_USER}" -p"${DB_PASSWORD}" "${DB_NAME}" > "${OUT_FILE}"
else
  mysqldump "${MYSQLDUMP_OPTS[@]}" -h "${DB_HOST}" -P "${DB_PORT}" -u "${DB_USER}" "${DB_NAME}" > "${OUT_FILE}"
fi

# 维护 latest 软链
rm -f "${LATEST_LINK}"
ln -s "${OUT_FILE}" "${LATEST_LINK}"

# 清理 30 天前的备份
find "${BACKUP_DIR}" -name "${DB_NAME}_*.sql" -mtime +30 -delete 2>/dev/null || true

echo "[$(date)] 备份完成：${OUT_FILE}"
