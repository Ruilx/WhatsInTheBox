#!/usr/bin/env bash
#
# 「箱子里面有什么（WhatsInTheBox）」本地镜像构建脚本
# 只烘焙运行环境 + 依赖，源码运行时外挂（见 docker/*.Dockerfile）。
#
# 用法：
#   ./docker/build.sh
#
# 说明：
#   - 后端镜像上下文为 backend/，dockerfile 指向 docker/backend.Dockerfile
#   - 前端镜像上下文为 frontend/，dockerfile 指向 docker/frontend.Dockerfile
#   - 两个镜像都不包含源码（dev 取向，源码用 bind mount 挂进容器）
set -euo pipefail

# 脚本位于 docker/，上一级即仓库根
cd "$(dirname "$0")/.."

echo "==> 构建后端镜像 whatsinthebox-backend:latest"
docker build -f docker/backend.Dockerfile -t whatsinthebox-backend:latest backend/

echo "==> 构建前端镜像 whatsinthebox-frontend:latest"
docker build -f docker/frontend.Dockerfile -t whatsinthebox-frontend:latest frontend/

echo "==> 完成：两个镜像已构建（仅含运行环境 + 依赖，源码运行时外挂）。"
echo "    下一步可用：docker compose up -d   启动开发联调环境"
