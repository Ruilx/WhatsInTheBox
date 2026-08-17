"""
会话 DAO（dev-plan v4 §账号登录与权限 / R3）。

session 表物理删除（登出/过期），无 deleted 字段。
支持多端登录：同一用户可有多条有效记录。
"""
from typing import Optional
from datetime import datetime
from app.core import db


class SessionDao:
    table = "session"

    def create(
        self, user_id: int, token: str, expire_at: datetime, ip: str, user_agent: str
    ) -> int:
        conn = db.get_conn()
        try:
            with conn.cursor(cursorclass=db.DictCursor) as cur:
                cur.execute(
                    "INSERT INTO `whatsinthebox`.`session` (user_id, token, expire_at, ip, user_agent) "
                    "VALUES (%s, %s, %s, %s, %s)",
                    (user_id, token, expire_at, ip, user_agent),
                )
                conn.commit()
                return cur.lastrowid
        finally:
            db.close_conn(conn)

    def get_by_token(self, token: str) -> Optional[dict]:
        """返回未过期的会话（expire_at > NOW()）。"""
        conn = db.get_conn()
        try:
            with conn.cursor(cursorclass=db.DictCursor) as cur:
                cur.execute(
                    "SELECT * FROM `whatsinthebox`.`session` WHERE token=%s AND expire_at > NOW()",
                    (token,),
                )
                return cur.fetchone()
        finally:
            db.close_conn(conn)

    def get_user_id_by_token(self, token: str) -> Optional[int]:
        row = self.get_by_token(token)
        return row["user_id"] if row else None

    def update_expire(self, token: str, expire_at: datetime) -> int:
        """滑动续期：重置过期时间。"""
        conn = db.get_conn()
        try:
            with conn.cursor(cursorclass=db.DictCursor) as cur:
                cur.execute(
                    "UPDATE `whatsinthebox`.`session` SET expire_at=%s, update_time=NOW() "
                    "WHERE token=%s",
                    (expire_at, token),
                )
                conn.commit()
                return cur.rowcount
        finally:
            db.close_conn(conn)

    def delete_by_token(self, token: str) -> int:
        """登出：物理删除当前会话。"""
        conn = db.get_conn()
        try:
            with conn.cursor(cursorclass=db.DictCursor) as cur:
                cur.execute("DELETE FROM `whatsinthebox`.`session` WHERE token=%s", (token,))
                conn.commit()
                return cur.rowcount
        finally:
            db.close_conn(conn)

    def delete_expired(self) -> int:
        """清理过期会话（可选定时任务）。"""
        conn = db.get_conn()
        try:
            with conn.cursor(cursorclass=db.DictCursor) as cur:
                cur.execute("DELETE FROM `whatsinthebox`.`session` WHERE expire_at <= NOW()")
                conn.commit()
                return cur.rowcount
        finally:
            db.close_conn(conn)
