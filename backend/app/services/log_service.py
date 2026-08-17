"""
日志业务层（dev-plan v4 §日志表 / §7.13 / §7.21）。

全量记录（含读操作 query/view/scan）：
- 写操作（create/update/delete/take_out/place/login/logout）由本服务在业务方法中显式写入；
- 读操作（query/view/scan）由 log_middleware 自动写入。
日志写入失败不影响主流程（见 write 的异常吞没）。
"""
import traceback
from app.dao.log_dao import LogDao


class LogService:
    def __init__(self):
        self.dao = LogDao()

    def write(
        self,
        action: str,
        object_type: str,
        object_id: int,
        operator_id: int,
        ip: str = None,
        detail: str = "",
        activity_id=None,
        box_id=None,
        item_id=None,
        combo_id=None,
    ) -> None:
        try:
            self.dao.insert(
                action=action,
                object_type=object_type,
                object_id=object_id,
                user_id=operator_id,
                ip=ip,
                detail=detail,
                activity_id=activity_id,
                box_id=box_id,
                item_id=item_id,
                combo_id=combo_id,
            )
        except Exception:  # noqa: BLE001
            # 日志仅作追溯，写入失败不应阻断业务
            traceback.print_exc()

    def list(self, action: str, object_type: str, page: int, size: int):
        return self.dao.list_with_filters(action, object_type, page, size)
