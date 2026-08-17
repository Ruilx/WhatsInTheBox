"""
鉴权业务层（dev-plan v4 §账号登录与权限 / §7.8 / §7.9）。

- 登录：校验 sha256(salt+password)，签发随机 token，落 session 表（多端登录）。
- 登出：物理删除当前会话（其他端不受影响）。
- 改密：校验旧密码后重算 hash（仅 rw 可改，控制器层二次校验）。
- 滑动续期：每次有效请求由 deps 刷新 expire_at。
"""
from datetime import timedelta
from typing import Optional
from app.core import config
from app.core.security import verify_password, generate_token, generate_salt, hash_password
from app.core.response import AppError, CODE_UNAUTH, MSG_UNAUTH
from app.core.response import CODE_PARAM, MSG_PARAM
from app.dao.user_dao import UserDao
from app.dao.session_dao import SessionDao
from app.services.log_service import LogService
from app.utils.time_util import now_sh_naive


class AuthService:
    def __init__(self):
        self.user_dao = UserDao()
        self.session_dao = SessionDao()
        self.log_service = LogService()

    def login(self, username: str, password: str, ip: str, user_agent: str) -> dict:
        user = self.user_dao.get_by_username(username)
        if not user or not verify_password(password, user["salt"], user["password_hash"]):
            raise AppError(CODE_UNAUTH, "用户名或密码错误")
        token = generate_token()
        expire_at = now_sh_naive() + timedelta(hours=config.settings.SESSION_EXPIRE_HOURS)
        self.session_dao.create(user["id"], token, expire_at, ip, user_agent)
        self.log_service.write(
            action="login", object_type="user", object_id=user["id"],
            operator_id=user["id"], ip=ip, detail=f"用户 {username} 登录",
        )
        return {
            "token": token,
            "user": {
                "id": user["id"],
                "username": user["username"],
                "nickname": user.get("nickname", ""),
                "role": user.get("role", "rw"),
            },
        }

    def logout(self, token: Optional[str], operator_id: int, ip: str) -> None:
        if token:
            self.session_dao.delete_by_token(token)
            self.log_service.write(
                action="logout", object_type="user", object_id=operator_id,
                operator_id=operator_id, ip=ip, detail="用户登出",
            )

    def change_password(self, operator_id: int, old_pwd: str, new_pwd: str, ip: str) -> None:
        user = self.user_dao.get_by_id(operator_id)
        if not user:
            raise AppError(CODE_UNAUTH, MSG_UNAUTH)
        if not verify_password(old_pwd, user["salt"], user["password_hash"]):
            raise AppError(CODE_PARAM, "旧密码不正确")
        salt = generate_salt()
        pwd_hash = hash_password(new_pwd, salt)
        self.user_dao.update_password(operator_id, pwd_hash, salt)
        self.log_service.write(
            action="update", object_type="user", object_id=operator_id,
            operator_id=operator_id, ip=ip, detail="修改密码",
        )

    def refresh(self, token: str) -> None:
        """滑动续期：重置过期时间。"""
        expire_at = now_sh_naive() + timedelta(hours=config.settings.SESSION_EXPIRE_HOURS)
        self.session_dao.update_expire(token, expire_at)
