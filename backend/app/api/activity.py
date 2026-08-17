"""
活动路由（dev-plan v4 §3.2）。

list/detail（读）/ create/update/delete/toggle_status（写，需 rw）。
detail 支持按 id 或 name 取（供前端 /活动名 路由）。
"""
from typing import Optional
from fastapi import APIRouter, Request, Depends

from app.core.response import ok
from app.models.activity import ActivityCreate, ActivityUpdate
from app.services.activity_service import ActivityService
from app.middleware.auth import require_login, require_rw, client_ip


router = APIRouter(tags=["activity"])
service = ActivityService()


@router.get("/activity/list")
def list_activity(
    keyword: str = "", type: str = "", status: Optional[int] = None,
    page: int = 1, size: int = 50, op=Depends(require_login),
):
    rows, total = service.list(keyword, type, status, page, size)
    return ok({"list": rows, "total": total, "page": page, "size": size})


@router.get("/activity/detail")
def detail_activity(id: Optional[int] = None, name: Optional[str] = None, op=Depends(require_login)):
    row = service.detail(id, name)
    return ok(row)


@router.post("/activity/create")
def create_activity(req: ActivityCreate, request: Request, op=Depends(require_rw)):
    aid = service.create(req.model_dump(), op["user_id"], client_ip(request))
    return ok({"id": aid})


@router.post("/activity/update")
def update_activity(req: ActivityUpdate, request: Request, op=Depends(require_rw)):
    aid = service.update(req.model_dump(), op["user_id"], client_ip(request))
    return ok({"id": aid})


@router.post("/activity/delete")
def delete_activity(data: dict, request: Request, op=Depends(require_rw)):
    service.delete(int(data.get("id")), op["user_id"], client_ip(request))
    return ok({})


@router.post("/activity/toggle_status")
def toggle_status(data: dict, request: Request, op=Depends(require_rw)):
    service.toggle_status(int(data.get("id")), int(data.get("status")), op["user_id"], client_ip(request))
    return ok({})
