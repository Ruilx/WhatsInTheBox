"""
搜索业务层（dev-plan v4 §7 / §3.2 search/keyword）。

全局/活动内关键字搜索：后端 SQL 模糊匹配 name/`desc`/note + 可选 type，
跨活动聚合（返回 items 与 total）。仅读，不写日志（由 log_middleware 自动记 query）。

为避免修改既有 DAO，这里通过 ItemDao 的通用 page 方法构造条件片段 + 参数，
值一律走参数化（%s），禁止拼接。
"""
from app.dao.item_dao import ItemDao


class SearchService:
    def __init__(self):
        self.item_dao = ItemDao()

    def search(self, keyword: str, item_type: str, page: int, size: int):
        where_clauses = []
        params: list = []
        if keyword:
            kw = f"%{keyword}%"
            where_clauses.append("(name LIKE %s OR `desc` LIKE %s OR note LIKE %s)")
            params.extend([kw, kw, kw])
        if item_type:
            where_clauses.append("type=%s")
            params.append(item_type)
        where = " AND ".join(where_clauses) if where_clauses else ""
        return self.item_dao.page(
            where=where, params=tuple(params), page=page, size=size, order="id DESC"
        )
