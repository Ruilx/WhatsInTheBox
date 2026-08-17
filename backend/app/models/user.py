"""
用户相关请求模型（dev-plan v4 §1.1 / §账号登录与权限）。
响应（UserInfo）去除 password_hash / salt，避免泄露。
"""
from pydantic import BaseModel, Field


class LoginReq(BaseModel):
    username: str = Field(..., min_length=1, max_length=64)
    password: str = Field(..., min_length=1, max_length=128)


class ChangePwdReq(BaseModel):
    old_pwd: str = Field(..., min_length=1, max_length=128)
    new_pwd: str = Field(..., min_length=6, max_length=128)


class UserInfo(BaseModel):
    id: int
    username: str
    nickname: str = ""
    role: str = "rw"
