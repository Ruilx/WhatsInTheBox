"""
活动相关请求模型（dev-plan v4 §3.1 / §活动表）。
时间字段以字符串传入（ISO 或 'YYYY-MM-DD HH:MM:SS'），由 service 解析为 datetime/None。
"""
from typing import Optional
from pydantic import BaseModel, Field


class ActivityCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    desc: str = ""
    type: str = ""
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    status: int = 0  # 0 draft / 1 active / 2 stopped / 3 archived
    note: str = ""


class ActivityUpdate(ActivityCreate):
    id: int = Field(..., gt=0)


class ActivityOut(BaseModel):
    id: int
    name: str
    desc: str = ""
    type: str = ""
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    status: int = 0
    note: str = ""
