"""
联合物品路由（dev-plan v4 §3.2 / §关联物品表）。

组合实体 CRUD（成员增删在 combo_item 路由）。
list/detail（读）/ create/update/delete（写，需 rw）。
"""
from fastapi import APIRouter, Request, Depends

from app.core.response import ok
from app.models.combo import ComboCreate, ComboUpdate
from app.services.combo_service import ComboService
from app.middleware.auth import require_login, require_rw, client_ip


router = APIRouter(tags=["combo"])
service = ComboService()


@router.get("/combo/list")
def list_combo(keyword: str = "", status: int = None, page: int = 1, size: int = 50, op=Depends(require_login)):
    rows, total = service.list(keyword, status, page, size)
    return ok({"list": rows, "total": total, "page": page, "size": size})


@router.get("/combo/detail")
def detail_combo(id: int, op=Depends(require_login)):
    return ok(service.detail(id))


@router.post("/combo/create")
def create_combo(req: ComboCreate, request: Request, op=Depends(require_rw)):
    cid = service.create(req.model_dump(), op["user_id"], client_ip(request))
    return ok({"id": cid})


@router.post("/combo/update")
def update_combo(req: ComboUpdate, request: Request, op=Depends(require_rw)):
    cid = service.update(req.model_dump(), op["user_id"], client_ip(request))
    return ok({"id": cid})


@router.post("/combo/delete")
def delete_combo(data: dict, request: Request, op=Depends(require_rw)):
    service.delete(int(data.get("id")), op["user_id"], client_ip(request))
    return ok({})
