# 「箱子里面有什么（WhatsInTheBox）」后端 DEV 镜像
# 设计原则（按用户要求）：镜像里只烘焙「运行环境 + 依赖」，
# 源码（backend/ 下的全部代码）在运行时通过 bind mount 外挂进容器，不 COPY 进镜像。
# 这样改代码即时生效，且镜像可复用、不随业务代码膨胀。
#
# 依赖（fastapi / uvicorn / gunicorn / mysqlclient / Pillow / pillow-heif 等）
# 由 pip 装进 Python 的全局 site-packages（/usr/local/lib/python3.13/site-packages），
# 不在 /app 目录下，因此运行时把源码挂到 /app 不会覆盖依赖，安全。
FROM python:3.13-slim

# 不写 .pyc 缓存 / 输出不缓冲（容器日志更实时、镜像更干净）
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# 编译期系统库：
#   default-libmysqlclient-dev + build-essential + pkg-config -> mysqlclient 需要编译
#   libheif1（运行时） + libheif-dev（构建时）                     -> pillow-heif 需要
#   libjpeg62-turbo                                            -> Pillow 解码所需（可选，保留无害）
RUN apt-get update && apt-get install -y --no-install-recommends \
        default-libmysqlclient-dev build-essential pkg-config \
        libheif1 libheif-dev libjpeg62-turbo \
    && rm -rf /var/lib/apt/lists/*

# 仅把依赖清单拷进镜像并安装（不拷源码）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 注意：这里【不 COPY 任何源码】。源码在 compose / docker run 时通过 bind mount 挂到 /app。
# 例：docker run -v "$(pwd)/backend:/app" whatsinthebox-backend:latest

EXPOSE 8004

# DEV 取向：带 --reload，外挂改码即时热重载（单 worker）。
# 生产可去掉 --reload，或用 gunicorn / 多 worker：
#   python run.py --host 0.0.0.0 --port 8004          # 默认 4 worker（见 run.py）
#   或 CMD ["gunicorn", "app.main:app", "-k", "uvicorn.workers.UvicornWorker",
#           "-b", "0.0.0.0:8004", "-w", "4"]
CMD ["python", "run.py", "--host", "0.0.0.0", "--port", "8004", "--reload"]
