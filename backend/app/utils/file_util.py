"""
文件工具（dev-plan v4 §7.17 / R6）。

- 校验图片扩展名（取自配置 ALLOWED_IMAGE_EXT）与大小（MAX_UPLOAD_MB）。
- HEIC 经 pillow-heif 转为可处理的图像。
- Pillow 重渲染压缩（长边 ≤1600）+ 生成缩略图（长边 ≤400）。
- 落盘到 uploads/，文件名用 uuid 避免冲突；返回相对路径（DB 存储用）。
"""
import io
import os
import uuid

from PIL import Image

# 注册 HEIC 解码器（缺失 pillow-heif 时静默跳过，HEIC 将无法处理）
try:
    import pillow_heif

    pillow_heif.register_heif_opener()
except Exception:  # noqa: BLE001
    pillow_heif = None

from app.core import config

_ALLOWED = set(config.settings.ALLOWED_IMAGE_EXT.lower().split(","))
_MAX_BYTES = config.settings.MAX_UPLOAD_MB * 1024 * 1024
_MAX_SIDE = 1600
_THUMB_SIDE = 400


class FileError(Exception):
    """上传文件校验/处理失败。"""


def _validate(filename: str, data: bytes) -> str:
    ext = os.path.splitext(filename)[1].lower().lstrip(".")
    if ext not in _ALLOWED:
        raise FileError(f"不支持的图片格式：{ext or '未知'}")
    if len(data) > _MAX_BYTES:
        raise FileError(f"文件超过大小限制（≤{config.settings.MAX_UPLOAD_MB}MB）")
    return ext


def _open(data: bytes, ext: str) -> Image.Image:
    img = Image.open(io.BytesIO(data))
    img.load()
    if ext in ("heic", "heif") and pillow_heif is None:
        raise FileError("服务器未安装 pillow-heif，无法处理 HEIC")
    return img


def _downscale(img: Image.Image, max_side: int) -> Image.Image:
    if max(img.size) <= max_side:
        return img
    ratio = max_side / float(max(img.size))
    return img.resize((int(img.size[0] * ratio), int(img.size[1] * ratio)))


def process_image(data: bytes, filename: str) -> tuple:
    """
    处理上传图片，返回 (相对路径, 缩略图相对路径)。
    相对路径相对于 uploads/ 目录，前端以 UPLOAD_URL_PREFIX 拼接访问。
    """
    if isinstance(data, str):
        data = data.encode("utf-8")
    ext = _validate(filename, data)
    img = _open(data, ext)
    # 统一为 RGB（去除透明通道，JPEG 不支持透明）
    if img.mode in ("RGBA", "P", "LA"):
        img = img.convert("RGB")

    img = _downscale(img, _MAX_SIDE)

    upload_dir = config.get_upload_abs_dir()
    os.makedirs(upload_dir, exist_ok=True)
    base = uuid.uuid4().hex
    path = f"{base}.jpg"
    thumb_path = f"{base}_thumb.jpg"

    img.save(os.path.join(upload_dir, path), "JPEG", quality=85)

    thumb = _downscale(img, _THUMB_SIDE)
    thumb.save(os.path.join(upload_dir, thumb_path), "JPEG", quality=80)

    return path, thumb_path
