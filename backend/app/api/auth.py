"""
鉴权路由（dev-plan v4 §账号登录与权限 / §3.2）。

- POST /whatsinthebox/auth/login  -> 校验密码，签发 token，Set-Cookie
- POST /whatsinthebox/auth/logout -> 清 session + 清 cookie
- GET  /whatsinthebox/auth/me     -> 当前用户（受保护）
- POST /whatsinthebox/auth/change_password -> 校验旧密码后改密（rw）
"""
import os
from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse

from app.core import config
from app.core.response import ok
from app.models.user import LoginReq, ChangePwdReq
from app.services.auth_service import AuthService
from app.middleware.auth import require_login, require_rw, client_ip


router = APIRouter(tags=["auth"])
auth_service = AuthService()


@router.post("/auth/login")
def login(req: LoginReq, request: Request):
    ip = client_ip(request)
    ua = request.headers.get("user-agent", "")
    result = auth_service.login(req.username, req.password, ip, ua)
    # 生产 HTTPS 前置 nginx 时建议置 COOKIE_SECURE=1；本地 http 开发置 0
    secure = os.getenv("COOKIE_SECURE", "0") == "1"
    resp = JSONResponse(content=ok(result))
    resp.set_cookie(
        key=config.settings.COOKIE_NAME,
        value=result["token"],
        httponly=True,
        secure=secure,
        samesite="lax",
        max_age=config.settings.SESSION_EXPIRE_HOURS * 3600,
    )
    return resp


@router.post("/auth/logout")
def logout(request: Request, op=Depends(require_login)):
    token = request.cookies.get(config.settings.COOKIE_NAME)
    auth_service.logout(token, op["user_id"], client_ip(request))
    resp = JSONResponse(content=ok({}))
    resp.delete_cookie(config.settings.COOKIE_NAME)
    return resp


@router.get("/auth/me")
def me(op=Depends(require_login)):
    return ok({"id": op["user_id"], "username": op["username"], "role": op["role"]})


@router.post("/auth/change_password")
def change_password(req: ChangePwdReq, request: Request, op=Depends(require_rw)):
    auth_service.change_password(op["user_id"], req.old_pwd, req.new_pwd, client_ip(request))
    return ok({})
