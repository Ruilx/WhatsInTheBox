"""
物品业务层（dev-plan v4 §物品属性 / §取出动作 / §7.13 / §7.14）。

- 活动内箱下物品 CRUD；创建时按 box 回填 activity_id（冗余列）。
- 取出 take_out：box_id 置 0（哨兵：已取出/没放箱里）+ status=taken_out + activity_id 保留。
- taken_out_list：按 activity_id 过滤 box_id=0（活动内「已取出」归集）。
- item.box_id=0 哨兵非真实箱，取出后仍在原活动下可追溯、可重新放入。
"""
from typing import Optional
from app.core.response import (
    AppError, CODE_NOT_FOUND, MSG_NOT_FOUND,
    CODE_PARAM, MSG_PARAM,
)
from app.dao.item_dao import ItemDao
from app.dao.box_dao import BoxDao
from app.dao.activity_dao import ActivityDao
from app.services.log_service import LogService


# 物品 status 枚举：0 in_box / 1 taken_out / 2 lent / 3 damaged / 4 lost
STATUS_TAKEN_OUT = 1


class ItemService:
    def __init__(self):
        self.dao = ItemDao()
        self.box_dao = BoxDao()
        self.activity_dao = ActivityDao()
        self.log = LogService()

    def _resolve_activity(self, data: dict, box_id: int) -> int:
        """按 box 回填 activity_id；无 box 时必须提供 activity_id。"""
        if box_id and int(box_id) > 0:
            box = self.box_dao.get_by_id(int(box_id))
            if not box:
                raise AppError(CODE_PARAM, "所属箱子不存在")
            return box["activity_id"]
        return int(data.get("activity_id", 0))

    def create(self, data: dict, operator_id: int, ip: str) -> int:
        box_id = int(data.get("box_id", 0))
        activity_id = self._resolve_activity(data, box_id)
        name = (data.get("name") or "").strip()
        if not name:
            raise AppError(CODE_PARAM, "物品名称不能为空")
        if activity_id <= 0:
            raise AppError(CODE_PARAM, "缺少所属活动（请指定箱子或活动）")
        row = self._build_row(data, activity_id, box_id, name)
        iid = self.dao.create(row)
        self.log.write("create", "item", iid, operator_id, ip, f"创建物品 {name}")
        return iid

    def update(self, data: dict, operator_id: int, ip: str) -> int:
        item_id = int(data.get("id"))
        item = self.dao.get_by_id(item_id)
        if not item:
            raise AppError(CODE_NOT_FOUND, MSG_NOT_FOUND)
        # 取出状态（box_id=0）下不允许改所属活动，保持冗余列一致
        box_id = int(data.get("box_id", item["box_id"]))
        activity_id = self._resolve_activity(data, box_id)
        name = (data.get("name") or "").strip()
        if not name:
            raise AppError(CODE_PARAM, "物品名称不能为空")
        if activity_id <= 0:
            activity_id = item["activity_id"]
        row = self._build_row(data, activity_id, box_id, name, item_id=item_id)
        self.dao.update(row)
        self.log.write("update", "item", item_id, operator_id, ip, f"更新物品 {name}")
        return item_id

    def delete(self, item_id: int, operator_id: int, ip: str) -> None:
        item = self.dao.get_by_id(item_id)
        if not item:
            raise AppError(CODE_NOT_FOUND, MSG_NOT_FOUND)
        self.dao.soft_delete(item_id)
        self.log.write("delete", "item", item_id, operator_id, ip, f"删除物品 {item['name']}")

    def take_out(self, item_id: int, operator_id: int, ip: str) -> None:
        """取出：box_id=0 哨兵 + status=taken_out + activity_id 保留。"""
        item = self.dao.get_by_id(item_id)
        if not item:
            raise AppError(CODE_NOT_FOUND, MSG_NOT_FOUND)
        self.dao.set_box_and_status(item_id, 0, STATUS_TAKEN_OUT)
        self.log.write("take_out", "item", item_id, operator_id, ip, f"取出物品 {item['name']}")

    # -------------------- 查询 --------------------
    def list(self, box_id: int, keyword: str, status: Optional[int], page: int, size: int):
        return self.dao.page_by_box(box_id, keyword, status, page, size)

    def taken_out_list(self, activity_id: int, keyword: str, page: int, size: int):
        return self.dao.taken_out_list(activity_id, keyword, page, size)

    def detail(self, item_id: int) -> dict:
        item = self.dao.get_by_id(item_id)
        if not item:
            raise AppError(CODE_NOT_FOUND, MSG_NOT_FOUND)
        return item

    # -------------------- 辅助 --------------------
    @staticmethod
    def _build_row(data: dict, activity_id: int, box_id: int, name: str, item_id: Optional[int] = None) -> dict:
        row = {
            "name": name,
            "desc": data.get("desc", ""),
            "type": data.get("type", ""),
            "activity_id": activity_id,
            "box_id": box_id,
            "status": int(data.get("status", 0)),
            "note": data.get("note", ""),
            "photo": data.get("photo", ""),
            "thumb": data.get("thumb", ""),
        }
        if item_id is not None:
            row["id"] = item_id
        return row
