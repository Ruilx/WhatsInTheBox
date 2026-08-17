"""
箱子 DAO（dev-plan v4 §箱子属性 / §取出动作 / §7.12 / §7.14）。

- type 为 JSON 多标签数组，入库前 json.dumps，读取后解析为 list（_norm_type）。
- box_id=0 哨兵仅用于 item，箱子本身无此约定。
- 唯一性：箱名（活动内）、serial_no（全局），应用层校验（见 service）。
"""
import json
from typing import Optional, List, Tuple
from app.dao.base_dao import BaseDao, kw_where, status_where, box_type_where


def _norm_type(row: Optional[dict]) -> Optional[dict]:
    """将 box.type（JSON 列）规整为 Python list。"""
    if row is None:
        return None
    t = row.get("type")
    if isinstance(t, str):
        try:
            t = json.loads(t)
        except (ValueError, TypeError):
            t = []
    if not isinstance(t, list):
        t = []
    row = dict(row)
    row["type"] = t
    return row


class BoxDao(BaseDao):
    table = "box"

    def get_by_id(self, box_id: int) -> Optional[dict]:
        return super().get_by_id(box_id, mapper=_norm_type)

    def get_by_name_and_activity(self, activity_id: int, name: str) -> Optional[dict]:
        sql = (
            "SELECT * FROM `whatsinthebox`.`box` WHERE activity_id=%s AND name=%s AND deleted=0"
        )
        return self._query_one(sql, (activity_id, name))

    def get_by_serial(self, serial_no: str) -> Optional[dict]:
        if not serial_no:
            return None
        sql = "SELECT * FROM `whatsinthebox`.`box` WHERE serial_no=%s AND deleted=0"
        return self._query_one(sql, (serial_no,))

    def get_by_activity(self, activity_id: int) -> List[dict]:
        """返回某活动下全部箱子（用于层级树构建）。"""
        return self.list_all(
            where="activity_id=%s", params=(activity_id,), order="id ASC",
            mapper=_norm_type,
        )

    def create(self, data: dict) -> int:
        sql = (
            "INSERT INTO `whatsinthebox`.`box` "
            "(activity_id, name, `desc`, type, size, material, parent_box_id, "
            "status, serial_no, note, first_using_time, photo, thumb) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        )
        return self._insert(
            sql,
            (
                data["activity_id"],
                data["name"],
                data.get("desc", ""),
                json.dumps(data.get("type", []), ensure_ascii=False),
                data.get("size", ""),
                data.get("material", ""),
                data.get("parent_box_id"),
                int(data.get("status", 0)),
                data.get("serial_no", ""),
                data.get("note", ""),
                data.get("first_using_time"),
                data.get("photo", ""),
                data.get("thumb", ""),
            ),
        )

    def update(self, data: dict) -> int:
        sql = (
            "UPDATE `whatsinthebox`.`box` SET name=%s, `desc`=%s, type=%s, size=%s, material=%s, "
            "parent_box_id=%s, status=%s, serial_no=%s, note=%s, "
            "first_using_time=%s, photo=%s, thumb=%s, update_time=NOW() "
            "WHERE id=%s AND deleted=0"
        )
        return self._execute(
            sql,
            (
                data["name"],
                data.get("desc", ""),
                json.dumps(data.get("type", []), ensure_ascii=False),
                data.get("size", ""),
                data.get("material", ""),
                data.get("parent_box_id"),
                int(data.get("status", 0)),
                data.get("serial_no", ""),
                data.get("note", ""),
                data.get("first_using_time"),
                data.get("photo", ""),
                data.get("thumb", ""),
                data["id"],
            ),
        )

    def page_with_filters(
        self, activity_id: int, keyword: str, box_type: List[str], status: Optional[int],
        page: int, size: int,
    ) -> Tuple[List[dict], int]:
        """活动内箱子列表：关键字 + 标签 + 状态过滤（全后端 SQL）。"""
        where_clauses = ["activity_id=%s"]
        params: list = [activity_id]
        kw_sql, kw_params = kw_where(keyword)
        if kw_sql:
            where_clauses.append(kw_sql)
            params.extend(kw_params)
        bt_sql, bt_params = box_type_where(box_type)
        if bt_sql:
            where_clauses.append(bt_sql)
            params.extend(bt_params)
        st_sql, st_params = status_where(status)
        if st_sql:
            where_clauses.append(st_sql)
            params.extend(st_params)
        where = " AND ".join(where_clauses)
        return self.page(
            where=where, params=tuple(params), page=page, size=size,
            order="id DESC", mapper=_norm_type,
        )

    def clear_serial_on_delete(self, box_id: int) -> int:
        """软删箱子时一并清空 serial_no（释放该串号，dev-plan v4 §7.7）。"""
        sql = (
            "UPDATE `whatsinthebox`.`box` SET deleted=1, serial_no='', update_time=NOW() "
            "WHERE id=%s AND deleted=0"
        )
        return self._execute(sql, (box_id,))
