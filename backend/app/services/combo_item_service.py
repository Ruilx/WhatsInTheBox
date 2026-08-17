"""
联合物品成员业务层（dev-plan v4 §关联物品表 / §7.13）。

负责 combo_item 的成员增删与校验：
- add_item：校验 combo 与 item 存在，写入成员（join_method 枚举）。
- remove_item：软删成员。
- join_method：0 original 原装 / 1 supplement 补配 / 2 replaced 已替代。
"""
from app.core.response import (
    AppError, CODE_NOT_FOUND, MSG_NOT_FOUND, CODE_PARAM, MSG_PARAM,
)
from app.dao.combo_item_dao import ComboItemDao
from app.dao.combo_dao import ComboDao
from app.dao.item_dao import ItemDao
from app.services.log_service import LogService


class ComboItemService:
    def __init__(self):
        self.dao = ComboItemDao()
        self.combo_dao = ComboDao()
        self.item_dao = ItemDao()
        self.log = LogService()

    def add_item(self, combo_id: int, item_id: int, item_status: str, join_method: int, operator_id: int, ip: str) -> int:
        combo = self.combo_dao.get_by_id(combo_id)
        if not combo:
            raise AppError(CODE_NOT_FOUND, MSG_NOT_FOUND)
        item = self.item_dao.get_by_id(item_id)
        if not item:
            raise AppError(CODE_NOT_FOUND, "物品不存在")
        ciid = self.dao.add_item(combo_id, item_id, item_status, int(join_method))
        self.log.write("update", "combo", combo_id, operator_id, ip,
                       f"联合物品「{combo['name']}」添加成员 {item.get('name')}")
        return ciid

    def remove_item(self, combo_item_id: int, operator_id: int, ip: str) -> None:
        ci = self.dao.get_by_id(combo_item_id)
        if not ci:
            raise AppError(CODE_NOT_FOUND, MSG_NOT_FOUND)
        self.dao.remove_item(combo_item_id)
        self.log.write("update", "combo", ci["combo_id"], operator_id, ip,
                       "移除联合物品成员")
