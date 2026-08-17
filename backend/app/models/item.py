"""
物品相关请求模型（dev-plan v4 §物品属性 / §取出动作）。
box_id = 0 为「已取出/没放箱里」哨兵（非真实箱）。
activity_id 为冗余列：创建时若未提供，由 service 根据 box 所属活动回填。
取出（take_out）由 service 置 box_id=0 + status=taken_out + 保留 activity_id。
"""
from typing import Optional, List
from pydantic import BaseModel, Field


class ItemCreate(BaseModel):
    box_id: int = 0  # 0 = 哨兵（已取出）
    name: str = Field(..., min_length=1, max_length=128)
    desc: str = ""
    type: str = ""  # 自由文本
    activity_id: int = 0  # 冗余列，可选；service 按 box 回填
    status: int = 0  # 0 in_box / 1 taken_out / 2 lent / 3 damaged / 4 lost
    note: str = ""
    photo: str = ""
    thumb: str = ""


class ItemUpdate(ItemCreate):
    id: int = Field(..., gt=0)


class ItemOut(BaseModel):
    id: int
    name: str
    desc: str = ""
    type: str = ""
    activity_id: int = 0
    box_id: int = 0
    photo: str = ""
    thumb: str = ""
    status: int = 0
    note: str = ""
