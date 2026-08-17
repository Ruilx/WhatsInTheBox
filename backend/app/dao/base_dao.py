"""
DAO 基类（dev-plan v4 §2 / T02 / §7.3）。

统一封装：
- 参数化查询（占位符 %s，参数经 data 传入，禁止字符串拼接）；
- 逻辑删除默认追 deleted=0；
- 分页（LIMIT %s OFFSET %s）；
- 软删统一 UPDATE ... SET deleted=1, update_time=NOW()。

动态筛选走「条件片段 + 参数列表」拼装，值不入 SQL 文本。
表名来自子类常量（非用户数据），安全。
提供映射器 mapper 支持行级转换（如 box.type 的 JSON 解析）。
"""
from typing import Callable, Optional, Tuple, List, Any
from app.core import db


class BaseDao:
    table: str = ""

    # -------------------- 底层执行（每条查询自管连接） --------------------
    def _query(self, sql: str, params: tuple = ()) -> List[dict]:
        conn = db.get_conn()
        try:
            with conn.cursor(cursorclass=db.DictCursor) as cur:
                cur.execute(sql, params or ())
                return cur.fetchall()
        finally:
            db.close_conn(conn)

    def _query_one(self, sql: str, params: tuple = ()) -> Optional[dict]:
        rows = self._query(sql, params)
        return rows[0] if rows else None

    def _execute(self, sql: str, params: tuple = ()) -> int:
        conn = db.get_conn()
        try:
            with conn.cursor(cursorclass=db.DictCursor) as cur:
                cur.execute(sql, params or ())
                conn.commit()
                return cur.rowcount
        finally:
            db.close_conn(conn)

    def _insert(self, sql: str, params: tuple = ()) -> int:
        conn = db.get_conn()
        try:
            with conn.cursor(cursorclass=db.DictCursor) as cur:
                cur.execute(sql, params or ())
                conn.commit()
                return cur.lastrowid
        finally:
            db.close_conn(conn)

    # -------------------- 通用查询（默认 deleted=0） --------------------
    def get_by_id(
        self, id_value: Any, id_field: str = "id", mapper: Callable = lambda r: r
    ) -> Optional[dict]:
        sql = f"SELECT * FROM `whatsinthebox`.`{self.table}` WHERE `{id_field}`=%s AND deleted=0"
        row = self._query_one(sql, (id_value,))
        return mapper(row) if row else None

    def list_all(
        self, where: str = "", params: tuple = (), order: str = "id DESC",
        mapper: Callable = lambda r: r,
    ) -> List[dict]:
        sql = f"SELECT * FROM `whatsinthebox`.`{self.table}` WHERE deleted=0"
        if where:
            sql += f" AND {where}"
        sql += f" ORDER BY {order}"
        return [mapper(r) for r in self._query(sql, params)]

    def page(
        self, where: str = "", params: tuple = (), page: int = 1, size: int = 50,
        order: str = "id DESC", mapper: Callable = lambda r: r,
    ) -> Tuple[List[dict], int]:
        count_sql = f"SELECT COUNT(*) AS cnt FROM `whatsinthebox`.`{self.table}` WHERE deleted=0"
        if where:
            count_sql += f" AND {where}"
        total = self._query_one(count_sql, params)["cnt"]

        list_sql = f"SELECT * FROM `whatsinthebox`.`{self.table}` WHERE deleted=0"
        if where:
            list_sql += f" AND {where}"
        list_sql += f" ORDER BY {order} LIMIT %s OFFSET %s"
        rows = self._query(list_sql, tuple(list(params)) + (size, (page - 1) * size))
        return [mapper(r) for r in rows], total

    def soft_delete(self, id_value: Any, id_field: str = "id") -> int:
        sql = (
            f"UPDATE `whatsinthebox`.`{self.table}` SET deleted=1, update_time=NOW() "
            f"WHERE `{id_field}`=%s AND deleted=0"
        )
        return self._execute(sql, (id_value,))


# -------------------- 通用条件构造辅助（禁止值拼接） --------------------
def kw_where(keyword: str) -> Tuple[str, tuple]:
    """关键字模糊匹配 name / `desc` / note（参数化）。"""
    if not keyword:
        return "", ()
    kw = f"%{keyword}%"
    return ("(name LIKE %s OR `desc` LIKE %s OR note LIKE %s)", (kw, kw, kw))


def status_where(status: Optional[int]) -> Tuple[str, tuple]:
    """状态精确匹配（枚举走 WHERE）。"""
    if status is None:
        return "", ()
    return ("status=%s", (status,))


def box_type_where(labels: List[str]) -> Tuple[str, tuple]:
    """箱子 type（JSON 多标签）按「包含某标签」过滤，参数化。"""
    import json
    if not labels:
        return "", ()
    clauses = []
    params: List[Any] = []
    for lb in labels:
        clauses.append("JSON_CONTAINS(type, %s)")
        params.append(json.dumps(lb, ensure_ascii=False))
    return (" AND ".join(clauses), tuple(params))
