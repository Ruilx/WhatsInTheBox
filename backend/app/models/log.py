"""
日志相关模型（dev-plan v4 §日志表 / §7.13 / §7.21）。
日志全量记录（含读操作 query/view/scan），实质只追加。
"""
from typing import Optional
from pydantic import BaseModel, Field


class LogQuery(BaseModel):
    page: int = 1
    size: int = 50
    action: str = ""  # 可选过滤：query/view/create/... 留空=全部
    object_type: str = ""  # 可选过滤：activity/box/item/combo


class LogOut(BaseModel):
    id: int
    activity_id: Optional[int] = None
    box_id: Optional[int] = None
    item_id: Optional[int] = None
    combo_id: Optional[int] = None
    user_id: int = 0
    action: str = ""
    object_type: str = ""
    object_id: int = 0
    detail: str = ""
    ip: Optional[str] = None
