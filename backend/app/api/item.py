"""
物品路由（dev-plan v4 §3.2 / §7.13 / §7.14）。

list/detail/taken_out_list（读）/ create/update/delete/take_out（写，需 rw）。
taken_out_list 按 activity_id（或 activity_name）过滤 box_id=0（活动内已取出归集）。
"""
from typing import Optional
from fastapi import APIRouter, Request, Depends

from app.core.response import ok, AppError, CODE_NOT_FOUND, MSG_NOT_FOUND, CODE_PARAM, MSG_PARAM
from app.models.item import ItemCreate, ItemUpdate
from app.services.item_service import ItemService
from app.services.activity_service import ActivityService
from app.middleware.auth import require_login, require_rw, client_ip


router = APIRouter(tags=["item"])
service = ItemService()


@router.get("/item/list")
def list_item(
    box_id: int, keyword: str = "", status: Optional[int] = None,
    page: int = 1, size: int = 50, op=Depends(require_login),
):
    rows, total = service.list(box_id, keyword, status, page, size)
    return ok({"list": rows, "total": total, "page": page, "size": size})


@router.get("/item/taken_out_list")
def taken_out_list(
    activity_id: int = 0, activity_name: str = "", keyword: str = "",
    page: int = 1, size: int = 50, op=Depends(require_login),
):
    if not activity_id and activity_name:
        act = ActivityService().get_by_name(activity_name)
        if not act:
            raise AppError(CODE_NOT_FOUND, MSG_NOT_FOUND)
        activity_id = act["id"]
    if not activity_id:
        raise AppError(CODE_PARAM, MSG_PARAM)
    rows, total = service.taken_out_list(activity_id, keyword, page, size)
    return ok({"list": rows, "total": total, "page": page, "size": size})


@router.get("/item/detail")
def detail_item(id: int, op=Depends(require_login)):
    return ok(service.detail(id))


@router.post("/item/create")
def create_item(req: ItemCreate, request: Request, op=Depends(require_rw)):
    iid = service.create(req.model_dump(), op["user_id"], client_ip(request))
    return ok({"id": iid})


@router.post("/item/update")
def update_item(req: ItemUpdate, request: Request, op=Depends(require_rw)):
    iid = service.update(req.model_dump(), op["user_id"], client_ip(request))
    return ok({"id": iid})


@router.post("/item/delete")
def delete_item(data: dict, request: Request, op=Depends(require_rw)):
    service.delete(int(data.get("id")), op["user_id"], client_ip(request))
    return ok({})


@router.post("/item/take_out")
def take_out(data: dict, request: Request, op=Depends(require_rw)):
    service.take_out(int(data.get("id")), op["user_id"], client_ip(request))
    return ok({})
