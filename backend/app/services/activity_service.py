"""
活动业务层（dev-plan v4 §活动表 / §7.12）。

- 活动名全局唯一（应用层校验，软删后可重用）。
- 活动名禁止等于配置前缀 GLOBAL_PREFIX（错误码 2003，应用层 + seed 双重校验）。
- 状态枚举：0 draft / 1 active / 2 stopped / 3 archived。
- stopped / archived 后子资源仍可编辑（无写入限制）。
"""
from typing import Optional
from app.core import config
from app.core.response import (
    AppError, CODE_NOT_FOUND, MSG_NOT_FOUND,
    CODE_DUPLICATE, MSG_DUPLICATE,
    CODE_RESERVED_PREFIX, MSG_RESERVED_PREFIX, CODE_PARAM, MSG_PARAM,
)
from app.dao.activity_dao import ActivityDao
from app.services.log_service import LogService
from app.utils.time_util import parse_dt


class ActivityService:
    def __init__(self):
        self.dao = ActivityDao()
        self.log = LogService()

    def _check_name(self, name: str, exclude_id: Optional[int] = None) -> None:
        if name == config.settings.GLOBAL_PREFIX:
            raise AppError(CODE_RESERVED_PREFIX, MSG_RESERVED_PREFIX)
        existing = self.dao.get_by_name(name)
        if existing and (exclude_id is None or existing["id"] != exclude_id):
            raise AppError(CODE_DUPLICATE, MSG_DUPLICATE)

    def create(self, data: dict, operator_id: int, ip: str) -> int:
        name = (data.get("name") or "").strip()
        if not name:
            raise AppError(CODE_PARAM, "活动名不能为空")
        self._check_name(name)
        row = {
            "name": name,
            "desc": data.get("desc", ""),
            "type": data.get("type", ""),
            "start_time": parse_dt(data.get("start_time")),
            "end_time": parse_dt(data.get("end_time")),
            "status": int(data.get("status", 0)),
            "note": data.get("note", ""),
        }
        aid = self.dao.create(row)
        self.log.write("create", "activity", aid, operator_id, ip, f"创建活动 {name}")
        return aid

    def update(self, data: dict, operator_id: int, ip: str) -> int:
        aid = int(data.get("id"))
        existing = self.dao.get_by_id(aid)
        if not existing:
            raise AppError(CODE_NOT_FOUND, MSG_NOT_FOUND)
        name = (data.get("name") or "").strip()
        if not name:
            raise AppError(CODE_PARAM, "活动名不能为空")
        if name != existing["name"]:
            self._check_name(name, exclude_id=aid)
        row = {
            "id": aid,
            "name": name,
            "desc": data.get("desc", ""),
            "type": data.get("type", ""),
            "start_time": parse_dt(data.get("start_time")),
            "end_time": parse_dt(data.get("end_time")),
            "status": int(data.get("status", 0)),
            "note": data.get("note", ""),
        }
        self.dao.update(row)
        self.log.write("update", "activity", aid, operator_id, ip, f"更新活动 {name}")
        return aid

    def delete(self, activity_id: int, operator_id: int, ip: str) -> None:
        existing = self.dao.get_by_id(activity_id)
        if not existing:
            raise AppError(CODE_NOT_FOUND, MSG_NOT_FOUND)
        self.dao.soft_delete(activity_id)
        self.log.write("delete", "activity", activity_id, operator_id, ip,
                       f"删除活动 {existing['name']}")

    def toggle_status(self, activity_id: int, status: int, operator_id: int, ip: str) -> None:
        existing = self.dao.get_by_id(activity_id)
        if not existing:
            raise AppError(CODE_NOT_FOUND, MSG_NOT_FOUND)
        self.dao.update({"id": activity_id, "name": existing["name"],
                         "desc": existing["desc"], "type": existing["type"],
                         "start_time": existing["start_time"], "end_time": existing["end_time"],
                         "status": int(status), "note": existing["note"]})
        self.log.write("update", "activity", activity_id, operator_id, ip,
                       f"活动状态切换为 {status}")

    def list(self, keyword: str, type_filter: str, status: Optional[int], page: int, size: int):
        where_clauses = []
        params: list = []
        if keyword:
            kw = f"%{keyword}%"
            where_clauses.append("(name LIKE %s OR `desc` LIKE %s OR note LIKE %s)")
            params.extend([kw, kw, kw])
        if type_filter:
            where_clauses.append("type=%s")
            params.append(type_filter)
        if status is not None:
            where_clauses.append("status=%s")
            params.append(status)
        where = " AND ".join(where_clauses) if where_clauses else ""
        return self.dao.page(where=where, params=tuple(params), page=page, size=size,
                             order="id DESC")

    def detail(self, activity_id: Optional[int] = None, name: Optional[str] = None) -> dict:
        row = None
        if activity_id:
            row = self.dao.get_by_id(activity_id)
        elif name:
            row = self.dao.get_by_name(name)
        if not row:
            raise AppError(CODE_NOT_FOUND, MSG_NOT_FOUND)
        return row

    def get_by_name(self, name: str) -> Optional[dict]:
        return self.dao.get_by_name(name)
