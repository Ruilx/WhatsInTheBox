"""
日志 DAO（dev-plan v4 §日志表 / §7.13 / §7.21）。

日志全量记录（含读操作 query/view/scan），实质只追加（不做 update/delete）。
四个可空外键：activity_id / box_id / item_id / combo_id；object_type 标识对象类型。
"""
from typing import Optional
from app.dao.base_dao import BaseDao


class LogDao(BaseDao):
    table = "log"

    def insert(
        self,
        action: str,
        object_type: str,
        object_id: int,
        user_id: int,
        ip: Optional[str],
        detail: str = "",
        activity_id: Optional[int] = None,
        box_id: Optional[int] = None,
        item_id: Optional[int] = None,
        combo_id: Optional[int] = None,
    ) -> int:
        sql = (
            "INSERT INTO `whatsinthebox`.`log` "
            "(activity_id, box_id, item_id, combo_id, user_id, action, "
            "object_type, object_id, detail, ip, create_time, update_time) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())"
        )
        return self._insert(
            sql,
            (
                activity_id,
                box_id,
                item_id,
                combo_id,
                user_id,
                action,
                object_type,
                object_id,
                detail,
                ip,
            ),
        )

    def list_with_filters(
        self, action: str, object_type: str, page: int, size: int
    ):
        where_clauses = []
        params: list = []
        if action:
            where_clauses.append("action=%s")
            params.append(action)
        if object_type:
            where_clauses.append("object_type=%s")
            params.append(object_type)
        where = " AND ".join(where_clauses) if where_clauses else ""
        return self.page(
            where=where, params=tuple(params), page=page, size=size,
            order="id DESC",
        )
