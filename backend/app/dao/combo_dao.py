"""联合物品 DAO（dev-plan v4 §关联物品表）。"""
from typing import Optional, List, Tuple
from app.dao.base_dao import BaseDao, kw_where, status_where
from app.dao.combo_item_dao import ComboItemDao


class ComboDao(BaseDao):
    table = "combo"

    def __init__(self):
        super().__init__()
        self.item_dao = ComboItemDao()

    def get_by_name(self, name: str) -> Optional[dict]:
        return self._query_one(
            "SELECT * FROM `whatsinthebox`.`combo` WHERE name=%s AND deleted=0", (name,)
        )

    def create(self, data: dict) -> int:
        sql = (
            "INSERT INTO `whatsinthebox`.`combo` (name, type, status, note) "
            "VALUES (%s, %s, %s, %s)"
        )
        return self._insert(
            sql,
            (
                data["name"],
                data.get("type", ""),
                int(data.get("status", 0)),
                data.get("note", ""),
            ),
        )

    def update(self, data: dict) -> int:
        sql = (
            "UPDATE `whatsinthebox`.`combo` SET name=%s, type=%s, status=%s, note=%s, "
            "update_time=NOW() WHERE id=%s AND deleted=0"
        )
        return self._execute(
            sql,
            (
                data["name"],
                data.get("type", ""),
                int(data.get("status", 0)),
                data.get("note", ""),
                data["id"],
            ),
        )

    def get_items(self, combo_id: int) -> List[dict]:
        """返回联合物品下的成员（含物品快照信息）。"""
        sql = (
            "SELECT ci.id AS combo_item_id, ci.combo_id, ci.item_id, ci.item_status, "
            "ci.join_method, i.name AS item_name, i.type AS item_type, i.status AS item_status_code "
            "FROM `whatsinthebox`.`combo_item` ci "
            "LEFT JOIN `whatsinthebox`.`item` i ON ci.item_id = i.id AND i.deleted=0 "
            "WHERE ci.combo_id=%s AND ci.deleted=0 "
            "ORDER BY ci.id ASC"
        )
        return self._query(sql, (combo_id,))

    def page_with_filters(
        self, keyword: str, status: Optional[int], page: int, size: int
    ) -> Tuple[List[dict], int]:
        where_clauses = []
        params: list = []
        kw_sql, kw_params = kw_where(keyword)
        if kw_sql:
            where_clauses.append(kw_sql)
            params.extend(kw_params)
        st_sql, st_params = status_where(status)
        if st_sql:
            where_clauses.append(st_sql)
            params.extend(st_params)
        where = " AND ".join(where_clauses) if where_clauses else ""
        return self.page(where=where, params=tuple(params), page=page, size=size,
                         order="id DESC")
