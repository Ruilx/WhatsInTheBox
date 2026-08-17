"""联合物品成员 DAO（dev-plan v4 §关联物品表 / §7.13）。"""
from typing import Optional
from app.dao.base_dao import BaseDao


class ComboItemDao(BaseDao):
    table = "combo_item"

    def get_by_id(self, combo_item_id: int) -> Optional[dict]:
        return super().get_by_id(combo_item_id)

    def add_item(
        self, combo_id: int, item_id: int, item_status: str, join_method: int
    ) -> int:
        sql = (
            "INSERT INTO `whatsinthebox`.`combo_item` "
            "(combo_id, item_id, item_status, join_method) "
            "VALUES (%s, %s, %s, %s)"
        )
        return self._insert(sql, (combo_id, item_id, item_status, int(join_method)))

    def remove_item(self, combo_item_id: int) -> int:
        return self.soft_delete(combo_item_id)
