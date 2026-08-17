"""
安全工具模块。

职责：
- 密码存储：sha256(每用户随机盐 + 密码)，salt 与 password_hash 同存 user 表。
- 登录态：会话随机 token（secrets.token_urlsafe），cookie 仅存该 token。
- 不涉及 cookie 防伪（token 随机不可预测），也不对 token 做 HMAC（按原型定稿）。
"""
import hashlib
import secrets


def generate_salt() -> str:
    """生成每用户随机盐。"""
    return secrets.token_hex(16)


def hash_password(password: str, salt: str) -> str:
    """
    计算 sha256(salt + password) 的十六进制摘要。
    盐在前，密码在后，避免直接拼接空盐问题。
    """
    raw = f"{salt}{password}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def verify_password(password: str, salt: str, password_hash: str) -> bool:
    """校验明文密码是否匹配存储的 hash。"""
    return hash_password(password, salt) == password_hash


def generate_token() -> str:
    """生成会话随机 token（cookie 仅存此值）。"""
    return secrets.token_urlsafe(32)
