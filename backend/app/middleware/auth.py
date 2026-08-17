"""
鉴权中间件与依赖（dev-plan v4 §账号登录与权限 / R2 / R3 / §7.8 / §7.9）。

- AuthMiddleware：从 cookie 取 token → 查未过期 session → 取 user；
  注入 request.state.operator = {user_id, role, username}；
  已鉴权请求执行 4h 滑动续期（重置 expire_at）。
- 依赖 require_login / require_rw：供各路由复用，缺失登录返回 1002，
  ro 调写接口返回 1003。
- client_ip：统一获取客户端 IP（兼容 x-forwarded-for，nginx 前置）。
"""
from typing import Optional, Dict, Any
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core import config
from app.core.response import AppError, CODE_UNAUTH, MSG_UNAUTH, CODE_FORBIDDEN, MSG_FORBIDDEN
from app.dao.session_dao import SessionDao
from app.dao.user_dao import UserDao
from app.services.auth_service import AuthService


_session_dao = SessionDao()
_user_dao = UserDao()
_auth_service = AuthService()


def client_ip(request: Request) -> str:
    """获取客户端真实 IP（兼容反向代理 x-forwarded-for）。"""
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else ""


class AuthMiddleware(BaseHTTPMiddleware):
    """解析 cookie token，注入 operator，并执行滑动续期。"""

    async def dispatch(self, request: Request, call_next):
        token = request.cookies.get(config.settings.COOKIE_NAME)
        operator: Optional[Dict[str, Any]] = None
        if token:
            session = _session_dao.get_by_token(token)
            if session:
                user = _user_dao.get_by_id(session["user_id"])
                if user:
                    operator = {
                        "user_id": user["id"],
                        "role": user.get("role", "rw"),
                        "username": user.get("username", ""),
                    }
                    # 4h 滑动续期：任一已鉴权请求重置过期时间
                    try:
                        _auth_service.refresh(token)
                    except Exception:  # noqa: BLE001
                        # 续期失败不应阻断主流程
                        pass
        request.state.operator = operator
        response = await call_next(request)
        return response


def get_operator(request: Request) -> Optional[Dict[str, Any]]:
    """从 request.state 读取已注入的 operator。"""
    return getattr(request.state, "operator", None)


def require_login(request: Request) -> Dict[str, Any]:
    """依赖：要求已登录，返回 operator；否则抛 1002。"""
    op = get_operator(request)
    if not op:
        raise AppError(CODE_UNAUTH, MSG_UNAUTH)
    return op


def require_rw(request: Request) -> Dict[str, Any]:
    """依赖：要求 rw 角色，否则抛 1003（ro 调写接口被拒）。"""
    op = require_login(request)
    if op.get("role") != "rw":
        raise AppError(CODE_FORBIDDEN, MSG_FORBIDDEN)
    return op
