"""
日志路由（dev-plan v4 §3.2 / §日志表 / §7.13）。

list：按 action / object_type 筛选分页。读接口本身不自动记日志（见 log_middleware 跳过列表）。
"""
from fastapi import APIRouter, Depends

from app.core.response import ok
from app.services.log_service import LogService
from app.middleware.auth import require_login


router = APIRouter(tags=["log"])
log_service = LogService()


@router.get("/log/list")
def list_log(action: str = "", object_type: str = "", page: int = 1, size: int = 50, op=Depends(require_login)):
    rows, total = log_service.list(action, object_type, page, size)
    return ok({"list": rows, "total": total, "page": page, "size": size})
