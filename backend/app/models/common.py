"""
公共模型：分页请求/响应（dev-plan v4 §7.10）。

约定：page 从 1 开始，size 默认 50、最大 100；列表统一返回 {list, total, page, size}。
响应体统一 {code, msg, data} 由各层包装，本模块只定义数据结构。
"""
from typing import Optional, List, Any


class PageReq:
    """分页 + 关键字 + 筛选基础参数（从查询参数解析）。"""

    def __init__(
        self,
        page: int = 1,
        size: int = 50,
        keyword: str = "",
        type: str = "",
        status: Optional[int] = None,
    ):
        self.page = max(1, int(page or 1))
        # size 默认 50，最大 100（防止超大翻页压垮低负载实例）
        try:
            self.size = int(size or 50)
        except (TypeError, ValueError):
            self.size = 50
        self.size = min(max(self.size, 1), 100)
        self.keyword = (keyword or "").strip()
        self.type = (type or "").strip()
        self.status = status

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size

    @property
    def limit(self) -> int:
        return self.size


class PageResp:
    """分页响应数据。"""

    def __init__(self, list_data: List[Any], total: int, page: int, size: int):
        self.list = list_data
        self.total = total
        self.page = page
        self.size = size

    def to_dict(self) -> dict:
        return {
            "list": self.list,
            "total": self.total,
            "page": self.page,
            "size": self.size,
        }
