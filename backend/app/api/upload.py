"""
上传路由（dev-plan v4 §3.2 / §7.17 / R6）。

POST /whatsinthebox/upload/photo：multipart 上传照片，须 rw。
校验类型（jpg/png/webp，HEIC 经 pillow-heif 转 jpg）、≤MAX_UPLOAD_MB；
Pillow 重渲染压缩 + 生成缩略图；存 uploads/，DB 存相对路径，返回 URL 路径。
所有端点用 def（同步，避免阻塞事件循环）。
"""
from fastapi import APIRouter, Request, UploadFile, File, Depends

from app.core.response import ok, AppError, CODE_PARAM, MSG_PARAM
from app.services.file_service import FileService, FileError
from app.middleware.auth import require_rw, client_ip


router = APIRouter(tags=["upload"])
file_service = FileService()


@router.post("/upload/photo")
def upload_photo(file: UploadFile = File(...), request: Request = None, op=Depends(require_rw)):
    try:
        result = file_service.save(file.file, file.filename or "upload.bin")
    except FileError as e:
        raise AppError(CODE_PARAM, str(e))
    return ok(result)
