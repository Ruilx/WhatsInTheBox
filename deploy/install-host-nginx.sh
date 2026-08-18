#!/usr/bin/env bash
# ============================================================================
# WhatsInTheBox（箱子里面有什么）宿主机 nginx 配置安装助手
# ============================================================================
# 作用：把 deploy/host-nginx-wib.conf 软链到 /etc/nginx/conf.d/whatsinthebox.conf，
#       执行 nginx -t 语法校验，通过后热重载 nginx（systemctl reload 优先，
#       回退 nginx -s reload）。
#
# 用法：sudo bash deploy/install-host-nginx.sh
#       DRY_RUN=1 bash deploy/install-host-nginx.sh   # 只校验，不改动系统
#
# 说明：使用软链而非拷贝，便于 git pull 更新配置后仅 reload 即可生效。
# ============================================================================
set -euo pipefail

# ---------- 常量 ----------
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
SRC_CONF="${SCRIPT_DIR}/host-nginx-wib.conf"
DEST_DIR="${NGINX_CONF_DIR:-/etc/nginx/conf.d}"
DEST_CONF="${DEST_DIR}/whatsinthebox.conf"
DRY_RUN="${DRY_RUN:-0}"

# ---------- 输出helpers ----------
info() { printf '\033[32m[INFO]\033[0m %s\n' "$*"; }
warn() { printf '\033[33m[WARN]\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[31m[FAIL]\033[0m %s\n' "$*" >&2; exit 1; }

# ---------- 1. 前置检查 ----------
[[ -f "${SRC_CONF}" ]] || die "找不到配置源文件：${SRC_CONF}"
command -v nginx >/dev/null 2>&1 || die "未检测到 nginx 命令，请先安装 nginx（如 apt install nginx）。"

if [[ "${DRY_RUN}" == "1" ]]; then
    info "DRY_RUN=1：仅做语法校验，不写入系统目录。"
    nginx -t -c /dev/stdin <<EOF || die "配置语法校验失败（DRY_RUN）。"
events {}
http {
    $(sed 's/^/    /' "${SRC_CONF}")
}
EOF
    info "DRY_RUN 语法校验通过。"
    exit 0
fi

[[ "$(id -u)" -eq 0 ]] || die "需要 root 权限写入 ${DEST_DIR}，请用 sudo 重新执行：sudo bash $0"
[[ -d "${DEST_DIR}" ]] || die "nginx 配置目录不存在：${DEST_DIR}（可用 NGINX_CONF_DIR 环境变量指定）。"

# ---------- 2. 备份已有的非软链配置 ----------
if [[ -e "${DEST_CONF}" && ! -L "${DEST_CONF}" ]]; then
    BACKUP="${DEST_CONF}.bak.$(date +%Y%m%d%H%M%S)"
    cp -a -- "${DEST_CONF}" "${BACKUP}"
    warn "已存在同名普通文件，已备份到：${BACKUP}"
fi

# ---------- 3. 建立软链 ----------
ln -sfn -- "${SRC_CONF}" "${DEST_CONF}"
info "已软链：${DEST_CONF} -> ${SRC_CONF}"

# ---------- 4. 语法校验（失败则回滚软链） ----------
if ! nginx -t; then
    rm -f -- "${DEST_CONF}"
    info "已移除刚建立的软链（回滚）。"
    die "nginx -t 校验失败，配置未生效。请检查上方报错（常见：与已有 default_server 冲突）。"
fi
info "nginx -t 语法校验通过。"

# ---------- 5. 热重载 ----------
if command -v systemctl >/dev/null 2>&1 && systemctl is-active --quiet nginx; then
    systemctl reload nginx || die "systemctl reload nginx 失败。"
    info "已通过 systemctl 重载 nginx。"
elif nginx -s reload 2>/dev/null; then
    info "已通过 nginx -s reload 重载 nginx。"
else
    warn "nginx 似未在运行，未执行 reload。请手动启动：systemctl start nginx"
fi

cat <<'TIP'

[NEXT] 安装完成。请确认：
  1. 容器已启动：docker compose -f docker-compose.prod.yml up -d --build
  2. 容器 IP 正确：docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' \
       whatsinthebox-prod-frontend-1 whatsinthebox-prod-backend-1
     期望 frontend=172.19.0.3、backend=172.19.0.2
  3. 冒烟自测：
       curl -I  http://127.0.0.1/2026trip          # 期望 301 -> /2026trip/
       curl -sI http://127.0.0.1/2026trip/         # 期望 200 text/html
       curl -sI http://127.0.0.1/whatsinthebox/    # 期望后端响应（非 502）
TIP
