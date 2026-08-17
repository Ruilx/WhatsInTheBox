"""
联合物品业务层（dev-plan v4 §关联物品表 / §7.13）。

CRUD + 详情（含成员）。成员增删在 combo_item_service 中（本服务复用之）。
name 全局唯一（应用层校验，软删后可重用）。
"""
from typing import Optional
from app.core.response import (
    AppError, CODE_NOT_FOUND, MSG_NOT_FOUND,
    CODE_DUPLICATE, MSG_DUPLICATE, CODE_PARAM, MSG_PARAM,
)
from app.dao.combo_dao import ComboDao
from app.services.log_service import LogService


class ComboService:
    def __init__(self):
        self.dao = ComboDao()
        self.log = LogService()

    def _check_name(self, name: str, exclude_id: Optional[int] = None) -> None:
        existing = self.dao.get_by_name(name)
        if existing and (exclude_id is None or existing["id"] != exclude_id):
            raise AppError(CODE_DUPLICATE, MSG_DUPLICATE)

    def create(self, data: dict, operator_id: int, ip: str) -> int:
        name = (data.get("name") or "").strip()
        if not name:
            raise AppError(CODE_PARAM, "联合物品名称不能为空")
        self._check_name(name)
        row = {
            "name": name,
            "type": data.get("type", ""),
            "status": int(data.get("status", 0)),
            "note": data.get("note", ""),
        }
        cid = self.dao.create(row)
        self.log.write("create", "combo", cid, operator_id, ip, f"创建联合物品 {name}")
        return cid

    def update(self, data: dict, operator_id: int, ip: str) -> int:
        cid = int(data.get("id"))
        combo = self.dao.get_by_id(cid)
        if not combo:
            raise AppError(CODE_NOT_FOUND, MSG_NOT_FOUND)
        name = (data.get("name") or "").strip()
        if not name:
            raise AppError(CODE_PARAM, "联合物品名称不能为空")
        if name != combo["name"]:
            self._check_name(name, exclude_id=cid)
        row = {
            "id": cid,
            "name": name,
            "type": data.get("type", ""),
            "status": int(data.get("status", 0)),
            "note": data.get("note", ""),
        }
        self.dao.update(row)
        self.log.write("update", "combo", cid, operator_id, ip, f"更新联合物品 {name}")
        return cid

    def delete(self, combo_id: int, operator_id: int, ip: str) -> None:
        combo = self.dao.get_by_id(combo_id)
        if not combo:
            raise AppError(CODE_NOT_FOUND, MSG_NOT_FOUND)
        self.dao.soft_delete(combo_id)
        self.log.write("delete", "combo", combo_id, operator_id, ip, f"删除联合物品 {combo['name']}")

    def list(self, keyword: str, status: Optional[int], page: int, size: int):
        return self.dao.page_with_filters(keyword, status, page, size)

    def detail(self, combo_id: int) -> dict:
        combo = self.dao.get_by_id(combo_id)
        if not combo:
            raise AppError(CODE_NOT_FOUND, MSG_NOT_FOUND)
        items = self.dao.get_items(combo_id)
        return {"combo": combo, "items": items}
