#!/usr/bin/env bash
# ============================================================
# WhatsInTheBox 上传文件备份脚本（dev-plan v4 §7.18 / R11）
# 使用 rsync 增量同步 uploads/ 目录到备份目标。
# 用法：BACKUP_DEST=/path/to/backup/uploads bash backup_uploads.sh
# 建议：配合 cron 每日执行。
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="${SCRIPT_DIR}/uploads"
BACKUP_DEST="${BACKUP_DEST:-${SCRIPT_DIR}/backups/uploads}"

if [ -z "${BACKUP_DEST}" ]; then
  echo "错误：请设置 BACKUP_DEST 环境变量（如 /data/backup/whatsinthebox/uploads）" >&2
  exit 1
fi

mkdir -p "${SRC_DIR}" "${BACKUP_DEST}"

echo "[$(date)] 开始同步上传目录 ${SRC_DIR} -> ${BACKUP_DEST}"

# -a 归档模式（保留权限/时间）；-v 详细；--delete 删除目标中已不存在的源文件
rsync -av --delete "${SRC_DIR}/" "${BACKUP_DEST}/"

echo "[$(date)] 上传目录同步完成"
