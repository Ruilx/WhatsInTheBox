"""活动 DAO（dev-plan v4 §活动表 / §7.12）。"""
from typing import Optional
from app.dao.base_dao import BaseDao
from app.core.response import AppError, CODE_PARAM


class ActivityDao(BaseDao):
    table = "activity"

    def get_by_name(self, name: str) -> Optional[dict]:
        return self._query_one(
            "SELECT * FROM `whatsinthebox`.`activity` WHERE name=%s AND deleted=0", (name,)
        )

    def create(self, data: dict) -> int:
        sql = (
            "INSERT INTO `whatsinthebox`.`activity` "
            "(name, `desc`, type, start_time, end_time, status, note) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s)"
        )
        return self._insert(
            sql,
            (
                data["name"],
                data.get("desc", ""),
                data.get("type", ""),
                data.get("start_time"),
                data.get("end_time"),
                int(data.get("status", 0)),
                data.get("note", ""),
            ),
        )

    def update(self, data: dict) -> int:
        sql = (
            "UPDATE `whatsinthebox`.`activity` SET name=%s, `desc`=%s, type=%s, start_time=%s, "
            "end_time=%s, status=%s, note=%s, update_time=NOW() "
            "WHERE id=%s AND deleted=0"
        )
        return self._execute(
            sql,
            (
                data["name"],
                data.get("desc", ""),
                data.get("type", ""),
                data.get("start_time"),
                data.get("end_time"),
                int(data.get("status", 0)),
                data.get("note", ""),
                data["id"],
            ),
        )
