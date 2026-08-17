"""用户 DAO（dev-plan v4 §账号登录与权限）。"""
from typing import Optional

from app.dao.base_dao import BaseDao


class UserDao(BaseDao):
    table = "user"

    def get_by_username(self, username: str) -> Optional[dict]:
        sql = "SELECT * FROM `whatsinthebox`.`user` WHERE username=%s AND deleted=0"
        return self._query_one(sql, (username,))

    def get_by_id(self, user_id: int) -> Optional[dict]:
        return super().get_by_id(user_id)

    def create(
        self, username: str, password_hash: str, salt: str, nickname: str, role: str
    ) -> int:
        sql = (
            "INSERT INTO `whatsinthebox`.`user` (username, password_hash, salt, nickname, role) "
            "VALUES (%s, %s, %s, %s, %s)"
        )
        return self._insert(sql, (username, password_hash, salt, nickname, role))

    def update_password(self, user_id: int, password_hash: str, salt: str) -> int:
        sql = (
            "UPDATE `whatsinthebox`.`user` SET password_hash=%s, salt=%s, update_time=NOW() "
            "WHERE id=%s AND deleted=0"
        )
        return self._execute(sql, (password_hash, salt, user_id))
