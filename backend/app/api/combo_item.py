"""
联合物品成员路由（dev-plan v4 §关联物品表 / §7.13）。

成员增删（join_method 枚举：0 original / 1 supplement / 2 replaced）。
写接口需 rw。
"""
from fastapi import APIRouter, Request, Depends

from app.core.response import ok
from app.models.combo import ComboItemAdd, ComboItemRemove
from app.services.combo_item_service import ComboItemService
from app.middleware.auth import require_login, require_rw, client_ip


router = APIRouter(tags=["combo_item"])
service = ComboItemService()


@router.post("/combo_item/add")
def add_item(req: ComboItemAdd, request: Request, op=Depends(require_rw)):
    ciid = service.add_item(
        req.combo_id, req.item_id, req.item_status, req.join_method,
        op["user_id"], client_ip(request),
    )
    return ok({"id": ciid})


@router.post("/combo_item/remove")
def remove_item(req: ComboItemRemove, request: Request, op=Depends(require_rw)):
    service.remove_item(req.combo_item_id, op["user_id"], client_ip(request))
    return ok({})
