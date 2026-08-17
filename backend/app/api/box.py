"""
箱子路由（dev-plan v4 §3.2 / §7.12 / §7.14）。

list/detail/tree（读）/ create/update/delete/fold（写，需 rw）。
detail 按 activity_name + box_name 取（供前端 /活动名/箱子名 路由）。
type 多标签以逗号分隔传入，后端按「包含」过滤。
"""
from typing import List, Optional
from fastapi import APIRouter, Request, Depends

from app.core.response import ok
from app.models.box import BoxCreate, BoxUpdate
from app.services.box_service import BoxService
from app.middleware.auth import require_login, require_rw, client_ip


router = APIRouter(tags=["box"])
service = BoxService()


@router.get("/box/list")
def list_box(
    activity_id: int, keyword: str = "", type: str = "", status: Optional[int] = None,
    page: int = 1, size: int = 50, op=Depends(require_login),
):
    box_type: List[str] = [t.strip() for t in (type or "").split(",") if t.strip()]
    rows, total = service.list(activity_id, keyword, box_type, status, page, size)
    return ok({"list": rows, "total": total, "page": page, "size": size})


@router.get("/box/detail")
def detail_box(activity_name: str, box_name: str, op=Depends(require_login)):
    data = service.detail(activity_name, box_name)
    return ok(data)


@router.get("/box/tree")
def tree_box(activity_id: int, op=Depends(require_login)):
    return ok(service.tree(activity_id))


@router.post("/box/create")
def create_box(req: BoxCreate, request: Request, op=Depends(require_rw)):
    bid = service.create(req.model_dump(), op["user_id"], client_ip(request))
    return ok({"id": bid})


@router.post("/box/update")
def update_box(req: BoxUpdate, request: Request, op=Depends(require_rw)):
    bid = service.update(req.model_dump(), op["user_id"], client_ip(request))
    return ok({"id": bid})


@router.post("/box/delete")
def delete_box(data: dict, request: Request, op=Depends(require_rw)):
    service.delete(int(data.get("id")), op["user_id"], client_ip(request))
    return ok({})


@router.post("/box/fold")
def fold_box(data: dict, request: Request, op=Depends(require_rw)):
    service.fold(int(data.get("id")), int(data.get("status", 1)), op["user_id"], client_ip(request))
    return ok({})
