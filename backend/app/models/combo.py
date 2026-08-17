"""
联合物品相关请求模型（dev-plan v4 §关联物品表）。
join_method：0 original 原装 / 1 supplement 补配 / 2 replaced 已替代。
"""
from typing import Optional
from pydantic import BaseModel, Field


class ComboCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    type: str = ""
    status: int = 0  # 0 normal / 1 invalid
    note: str = ""


class ComboUpdate(ComboCreate):
    id: int = Field(..., gt=0)


class ComboItemAdd(BaseModel):
    combo_id: int = Field(..., gt=0)
    item_id: int = Field(..., gt=0)
    item_status: str = ""
    join_method: int = 0  # 0 original / 1 supplement / 2 replaced


class ComboItemRemove(BaseModel):
    combo_item_id: int = Field(..., gt=0)


class ComboOut(BaseModel):
    id: int
    name: str
    type: str = ""
    status: int = 0
    note: str = ""
