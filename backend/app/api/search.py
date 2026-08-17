"""
搜索路由（dev-plan v4 §3.2 / §7 搜索）。

keyword：后端 SQL 模糊匹配 name/`desc`/note + 可选 type，跨活动聚合。
读接口，由 log_middleware 自动记 action=query。
"""
from fastapi import APIRouter, Depends

from app.core.response import ok
from app.services.search_service import SearchService
from app.middleware.auth import require_login


router = APIRouter(tags=["search"])
service = SearchService()


@router.get("/search/keyword")
def search_keyword(keyword: str = "", type: str = "", page: int = 1, size: int = 50, op=Depends(require_login)):
    rows, total = service.search(keyword, type, page, size)
    return ok({"items": rows, "total": total, "page": page, "size": size})
