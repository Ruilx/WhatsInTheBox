"""
全局配置模块。

读取项目根目录下的 .env 文件（不入库、不提交），提供数据库连接、全局前缀、
Cookie 与登录态、上传目录等配置。所有配置项均有安全默认值，缺失 .env 时也能启动。

约定（dev-plan v4 §1.4 / §7.20）：
- 全局页 URL 前缀 GLOBAL_PREFIX 可配置，默认 _wb，前端/后端/nginx 三处须一致。
- 活动名全局唯一且禁止等于 GLOBAL_PREFIX（应用层 + seed 双重校验，值取自本配置）。
"""
import os
from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/ 目录绝对路径（app/core/config.py -> 上溯两级）
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class Settings(BaseSettings):
    """系统配置，从 .env 读取，环境变量可覆盖。"""

    model_config = SettingsConfigDict(
        env_file=os.path.join(BASE_DIR, ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ---------- 数据库 ----------
    DB_HOST: str = "127.0.0.1"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = ""
    DB_NAME: str = "whatsinthebox"
    DB_CHARSET: str = "utf8mb4"

    # 是否走 SSL 连接数据库（默认开启）。
    # 规避 MySQL 8 caching_sha2_password 在未加密连接、密码缓存为空时
    # 偶发的 RSA 公钥交换竞态（表现为间歇性 1045 Access denied）。
    # 服务端 @@have_ssl=YES 时生效；若目标库不支持 SSL 可设为 false。
    DB_SSL: bool = True

    # ---------- 全局前缀 / 路由 ----------
    # 可配置：全局页 URL 前缀（默认 _wb）。活动名禁止等于此值。
    GLOBAL_PREFIX: str = "_wb"

    # ---------- 登录态 / Cookie ----------
    COOKIE_NAME: str = "wb_session"
    # 有效期 4 小时 + 滑动续期（任意已鉴权请求重置）
    SESSION_EXPIRE_HOURS: int = 4
    # 仅用于会话随机 token 的密码学随机源，无需对外暴露
    SECRET_KEY: str = "change-me-in-production-please"

    # ---------- 上传 / 文件 ----------
    UPLOAD_DIR: str = "uploads"
    # 前端访问上传文件的 URL 前缀（由 nginx / 静态服务映射）
    UPLOAD_URL_PREFIX: str = "/uploads"
    MAX_UPLOAD_MB: int = 5
    # 允许上传的图片扩展名（HEIC 经 pillow-heif 转 jpg 后入库）
    ALLOWED_IMAGE_EXT: str = "jpg,jpeg,png,webp,heic"

    # ---------- 初始管理员（seed 用） ----------
    ADMIN_USER: str = "admin"
    ADMIN_PASS: str = "admin123"

    # ---------- 其它 ----------
    API_PREFIX: str = "/whatsinthebox"


# 单例配置
settings = Settings()


def get_upload_abs_dir() -> str:
    """返回上传目录的绝对路径（相对 backend/ 解析）。"""
    return os.path.join(BASE_DIR, settings.UPLOAD_DIR)
