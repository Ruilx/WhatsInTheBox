"""
物品 DAO（dev-plan v4 §物品属性 / §取出动作 / §7.13 / §7.14）。

- box_id=0 为「已取出/没放箱里」哨兵（非真实箱）。
- activity_id 冗余列：取出后仍保留原所属活动，用于「已取出」按活动归集。
- 列表过滤：box_id 精确（箱视角）；已取出按 activity_id + box_id=0。
"""
from typing import Optional, List, Tuple
from app.dao.base_dao import BaseDao, kw_where, status_where


class ItemDao(BaseDao):
    table = "item"

    def get_by_id(self, item_id: int) -> Optional[dict]:
        return super().get_by_id(item_id)

    def create(self, data: dict) -> int:
        sql = (
            "INSERT INTO `whatsinthebox`.`item` "
            "(name, `desc`, type, activity_id, box_id, status, note, photo, thumb) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
        )
        return self._insert(
            sql,
            (
                data["name"],
                data.get("desc", ""),
                data.get("type", ""),
                int(data.get("activity_id", 0)),
                int(data.get("box_id", 0)),
                int(data.get("status", 0)),
                data.get("note", ""),
                data.get("photo", ""),
                data.get("thumb", ""),
            ),
        )

    def update(self, data: dict) -> int:
        sql = (
            "UPDATE `whatsinthebox`.`item` SET name=%s, `desc`=%s, type=%s, activity_id=%s, "
            "box_id=%s, status=%s, note=%s, photo=%s, thumb=%s, update_time=NOW() "
            "WHERE id=%s AND deleted=0"
        )
        return self._execute(
            sql,
            (
                data["name"],
                data.get("desc", ""),
                data.get("type", ""),
                int(data.get("activity_id", 0)),
                int(data.get("box_id", 0)),
                int(data.get("status", 0)),
                data.get("note", ""),
                data.get("photo", ""),
                data.get("thumb", ""),
                data["id"],
            ),
        )

    def set_box_and_status(self, item_id: int, box_id: int, status: int) -> int:
        """取出 / 重新放入：更新 box_id 与 status（activity_id 不变）。"""
        sql = (
            "UPDATE `whatsinthebox`.`item` SET box_id=%s, status=%s, update_time=NOW() "
            "WHERE id=%s AND deleted=0"
        )
        return self._execute(sql, (box_id, status, item_id))

    def page_by_box(
        self, box_id: int, keyword: str, status: Optional[int], page: int, size: int
    ) -> Tuple[List[dict], int]:
        where_clauses = ["box_id=%s"]
        params: list = [box_id]
        kw_sql, kw_params = kw_where(keyword)
        if kw_sql:
            where_clauses.append(kw_sql)
            params.extend(kw_params)
        st_sql, st_params = status_where(status)
        if st_sql:
            where_clauses.append(st_sql)
            params.extend(st_params)
        where = " AND ".join(where_clauses)
        return self.page(where=where, params=tuple(params), page=page, size=size,
                         order="id DESC")

    def taken_out_list(
        self, activity_id: int, keyword: str, page: int, size: int
    ) -> Tuple[List[dict], int]:
        where_clauses = ["activity_id=%s", "box_id=0"]
        params: list = [activity_id]
        kw_sql, kw_params = kw_where(keyword)
        if kw_sql:
            where_clauses.append(kw_sql)
            params.extend(kw_params)
        where = " AND ".join(where_clauses)
        return self.page(where=where, params=tuple(params), page=page, size=size,
                         order="id DESC")
