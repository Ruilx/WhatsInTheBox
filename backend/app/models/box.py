"""
箱子相关请求模型（dev-plan v4 §箱子属性）。
type 为 JSON 多标签数组（主要/次要/易碎/需保护/防水/要求向上/旧箱）。
parent_box_id 支持多层嵌套（NULL 为顶层）。
"""
from typing import Optional, List
from pydantic import BaseModel, Field


class BoxCreate(BaseModel):
    activity_id: int = Field(..., gt=0)
    name: str = Field(..., min_length=1, max_length=128)
    desc: str = ""
    type: List[str] = []  # JSON 多标签数组
    size: str = ""
    material: str = ""
    parent_box_id: Optional[int] = None
    status: int = 0  # 0 open / 1 folded / 2 sealed / 3 in_transit / 4 damaged / 5 retired
    serial_no: str = ""
    note: str = ""
    first_using_time: Optional[str] = None
    photo: str = ""
    thumb: str = ""


class BoxUpdate(BoxCreate):
    id: int = Field(..., gt=0)


class BoxOut(BaseModel):
    id: int
    activity_id: int
    name: str
    desc: str = ""
    type: List[str] = []
    size: str = ""
    material: str = ""
    parent_box_id: Optional[int] = None
    status: int = 0
    serial_no: str = ""
    note: str = ""
    first_using_time: Optional[str] = None
    photo: str = ""
    thumb: str = ""
