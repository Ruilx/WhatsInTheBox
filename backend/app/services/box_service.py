"""
箱子业务层（dev-plan v4 §箱子属性 / §取出动作 / §7.12 / §7.14 / §7.7）。

- 活动内箱名唯一（应用层校验，软删后可重用）。
- serial_no 全局唯一、不可变；软删时清空释放（clear_serial_on_delete）。
- 折叠仅改 status（无空箱硬校验）。
- 删除前校验：箱内仍有在箱物品（status=in_box 且 deleted=0）则拒绝；
  仍有子箱子也拒绝（避免孤儿引用）。
- 嵌套：parent_box_id 自引用，支持多层钻取。
"""
from typing import Optional, List
from app.core.response import (
    AppError, CODE_NOT_FOUND, MSG_NOT_FOUND,
    CODE_DUPLICATE, MSG_DUPLICATE, CODE_PARAM, MSG_PARAM,
)
from app.dao.box_dao import BoxDao
from app.dao.item_dao import ItemDao
from app.dao.activity_dao import ActivityDao
from app.services.log_service import LogService


class BoxService:
    def __init__(self):
        self.dao = BoxDao()
        self.item_dao = ItemDao()
        self.activity_dao = ActivityDao()
        self.log = LogService()

    # -------------------- 唯一性校验 --------------------
    def _check_name(self, activity_id: int, name: str, exclude_id: Optional[int] = None) -> None:
        existing = self.dao.get_by_name_and_activity(activity_id, name)
        if existing and (exclude_id is None or existing["id"] != exclude_id):
            raise AppError(CODE_DUPLICATE, MSG_DUPLICATE)

    def _check_serial(self, serial_no: str, exclude_id: Optional[int] = None) -> None:
        if not serial_no:
            return
        existing = self.dao.get_by_serial(serial_no)
        if existing and (exclude_id is None or existing["id"] != exclude_id):
            raise AppError(CODE_DUPLICATE, "物理串号重复（全局唯一）")

    # -------------------- CRUD --------------------
    def create(self, data: dict, operator_id: int, ip: str) -> int:
        activity_id = int(data.get("activity_id", 0))
        act = self.activity_dao.get_by_id(activity_id)
        if not act:
            raise AppError(CODE_PARAM, "所属活动不存在")
        name = (data.get("name") or "").strip()
        if not name:
            raise AppError(CODE_PARAM, "箱子名称不能为空")
        self._check_name(activity_id, name)
        self._check_serial((data.get("serial_no") or "").strip())
        row = self._build_row(data, activity_id, name)
        bid = self.dao.create(row)
        self.log.write("create", "box", bid, operator_id, ip, f"创建箱子 {name}")
        return bid

    def update(self, data: dict, operator_id: int, ip: str) -> int:
        box_id = int(data.get("id"))
        box = self.dao.get_by_id(box_id)
        if not box:
            raise AppError(CODE_NOT_FOUND, MSG_NOT_FOUND)
        activity_id = int(data.get("activity_id", box["activity_id"]))
        name = (data.get("name") or "").strip()
        if not name:
            raise AppError(CODE_PARAM, "箱子名称不能为空")
        if name != box["name"]:
            self._check_name(activity_id, name, exclude_id=box_id)
        serial = (data.get("serial_no") or "").strip()
        if serial != (box.get("serial_no") or ""):
            self._check_serial(serial, exclude_id=box_id)
        row = self._build_row(data, activity_id, name, box_id=box_id)
        self.dao.update(row)
        self.log.write("update", "box", box_id, operator_id, ip, f"更新箱子 {name}")
        return box_id

    def delete(self, box_id: int, operator_id: int, ip: str) -> None:
        box = self.dao.get_by_id(box_id)
        if not box:
            raise AppError(CODE_NOT_FOUND, MSG_NOT_FOUND)
        # 仍有在箱物品（status=in_box 且未删）则拒绝
        _, total = self.item_dao.page_by_box(box_id, "", 0, 1, 1)
        if total > 0:
            raise AppError(CODE_PARAM, "箱子内仍有在箱物品，请先取出或删除后再删除")
        # 仍有子箱子则拒绝（避免孤儿引用）
        children = self.dao.get_by_activity(box["activity_id"])
        if any((b.get("parent_box_id") or 0) == box_id for b in children):
            raise AppError(CODE_PARAM, "该箱子下仍有子箱子，请先处理子箱子")
        # 软删 + 清空 serial_no（释放串号）
        self.dao.clear_serial_on_delete(box_id)
        self.log.write("delete", "box", box_id, operator_id, ip, f"删除箱子 {box['name']}")

    def fold(self, box_id: int, status: int, operator_id: int, ip: str) -> None:
        """折叠/改状态：仅更新 status（非空箱也可折叠，仅标志）。"""
        box = self.dao.get_by_id(box_id)
        if not box:
            raise AppError(CODE_NOT_FOUND, MSG_NOT_FOUND)
        row = dict(box)
        row["status"] = int(status)
        self.dao.update(row)
        self.log.write("update", "box", box_id, operator_id, ip, f"箱子状态变更为 {status}")

    # -------------------- 查询 --------------------
    def list(self, activity_id: int, keyword: str, box_type: List[str], status: Optional[int], page: int, size: int):
        return self.dao.page_with_filters(activity_id, keyword, box_type, status, page, size)

    def detail(self, activity_name: str, box_name: str) -> dict:
        act = self.activity_dao.get_by_name(activity_name)
        if not act:
            raise AppError(CODE_NOT_FOUND, MSG_NOT_FOUND)
        box = self.dao.get_by_name_and_activity(act["id"], box_name)
        if not box:
            raise AppError(CODE_NOT_FOUND, MSG_NOT_FOUND)
        items, _ = self.item_dao.page_by_box(box["id"], "", None, 1, 10000)
        all_boxes = self.dao.get_by_activity(act["id"])
        child_boxes = [b for b in all_boxes if (b.get("parent_box_id") or 0) == box["id"]]
        return {"box": box, "items": items, "child_boxes": child_boxes}

    def tree(self, activity_id: int) -> List[dict]:
        """返回活动的箱子层级树（多层嵌套钻取用）。"""
        boxes = self.dao.get_by_activity(activity_id)
        by_parent: dict = {}
        for b in boxes:
            pid = (b.get("parent_box_id") or 0) or 0
            by_parent.setdefault(pid, []).append(b)

        def build(pid: int, depth: int) -> List[dict]:
            nodes = []
            for b in by_parent.get(pid, []):
                node = dict(b)
                node["depth"] = depth
                node["children"] = build(b["id"], depth + 1)
                nodes.append(node)
            return nodes

        return build(0, 0)

    # -------------------- 辅助 --------------------
    @staticmethod
    def _build_row(data: dict, activity_id: int, name: str, box_id: Optional[int] = None) -> dict:
        row = {
            "activity_id": activity_id,
            "name": name,
            "desc": data.get("desc", ""),
            "type": data.get("type", []),
            "size": data.get("size", ""),
            "material": data.get("material", ""),
            "parent_box_id": data.get("parent_box_id"),
            "status": int(data.get("status", 0)),
            "serial_no": (data.get("serial_no") or "").strip(),
            "note": data.get("note", ""),
            "first_using_time": data.get("first_using_time"),
            "photo": data.get("photo", ""),
            "thumb": data.get("thumb", ""),
        }
        if box_id is not None:
            row["id"] = box_id
        return row
