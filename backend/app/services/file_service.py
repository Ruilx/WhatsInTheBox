"""
文件业务层（dev-plan v4 §7.17 / R6）。

封装上传文件的落盘处理：调用 utils.file_util.process_image 完成
校验/HEIC 转 jpg/Pillow 压缩/缩略图生成，返回 {path, thumb}（相对 uploads/）。
"""
from app.utils import file_util
from app.utils.file_util import FileError


class FileService:
    def save(self, file_obj, filename: str) -> dict:
        """
        file_obj：UploadFile.file（底层文件对象，可同步 read）。
        返回 {"path": 相对路径, "thumb": 缩略图相对路径}。
        失败抛 FileError（控制器捕获后转 1001）。
        """
        data = file_obj.read()
        path, thumb = file_util.process_image(data, filename)
        return {"path": path, "thumb": thumb}
