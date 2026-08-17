"""
FastAPI 入口（dev-plan v4 §2 / §1.3 / R1 / §7）。

- 创建 app；配置 CORS（允许前端源，携带凭据）。
- 注册中间件：LogMiddleware（内层，读操作自动记日志）、AuthMiddleware（外层，注入 operator + 滑动续期）。
- 异常处理器：AppError -> 统一响应 {code,msg,data}；其余异常 -> 5000。
- 挂载各 router（统一前缀 config.settings.API_PREFIX = /whatsinthebox）。
- 挂载 /uploads 静态目录（上传文件下载）。
- 所有路由端点用 def（同步），避免 pymysql 同步驱动阻塞事件循环（R1）。
"""
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from app.core import config
from app.core.response import AppError, CODE_SERVER, MSG_SERVER, fail
from app.middleware.auth import AuthMiddleware
from app.middleware.log_middleware import LogMiddleware
from app.api import (
    auth, activity, box, item, combo, combo_item, log, search, upload,
)


settings = config.settings

app = FastAPI(title="WhatsInTheBox", version="1.0.0")

# -------------------- CORS --------------------
origins = [
    o.strip()
    for o in os.getenv(
        "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    ).split(",")
    if o.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------- 中间件（顺序：先注册=内层，后注册=外层） --------------------
# LogMiddleware 先注册 -> 内层（在 AuthMiddleware 之后执行，可读取 operator）
app.add_middleware(LogMiddleware)
# AuthMiddleware 后注册 -> 外层（最先执行，注入 request.state.operator + 滑动续期）
app.add_middleware(AuthMiddleware)


# -------------------- 异常处理器 -> 统一响应 --------------------
@app.exception_handler(AppError)
def handle_app_error(request: Request, exc: AppError):
    return JSONResponse(status_code=200, content=fail(exc.code, exc.msg))


@app.exception_handler(Exception)
def handle_exception(request: Request, exc: Exception):
    return JSONResponse(status_code=200, content=fail(CODE_SERVER, MSG_SERVER))


# -------------------- 静态目录：上传文件 --------------------
upload_dir = config.get_upload_abs_dir()
os.makedirs(upload_dir, exist_ok=True)
app.mount(settings.UPLOAD_URL_PREFIX, StaticFiles(directory=upload_dir), name="uploads")


# -------------------- 注册路由（统一前缀 /whatsinthebox） --------------------
_routers = [
    auth.router, activity.router, box.router, item.router,
    combo.router, combo_item.router, log.router, search.router, upload.router,
]
for _r in _routers:
    app.include_router(_r, prefix=settings.API_PREFIX)


@app.get("/")
def root():
    return {"name": "WhatsInTheBox API", "prefix": settings.API_PREFIX}
