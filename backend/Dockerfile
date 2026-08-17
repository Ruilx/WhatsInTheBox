# 「箱子里面有什么」后端镜像
# Python 3.12 + FastAPI + mysqlclient；uvicorn 多 worker。
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Pillow / pillow-heif 可能需要的系统库（按需；缺则构建时再补）
# mysqlclient 需要 libmysqlclient 头文件与构建工具（gcc/pkg-config）才能编译
RUN apt-get update && apt-get install -y --no-install-recommends \
        libheif1 libjpeg62-turbo libopenjp2-7 \
        default-libmysqlclient-dev build-essential pkg-config \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制后端代码（.env / .vendor 等敏感/本地目录由 .dockerignore 排除）
COPY . .

EXPOSE 8000

# 多 worker；生产建议 2~4，按容器 CPU 调整
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
