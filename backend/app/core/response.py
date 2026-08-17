"""
统一响应体模块（dev-plan v4 §7.4 / §7.5）。

所有接口返回 {"code":0,"msg":"ok","data":{...}}。
错误码规范：
  0     成功
  1001  参数错误
  1002  未登录/过期
  1003  无权限（role 不足 / ro 调写接口）
  2001  资源不存在
  2002  名称/串号重复（唯一性冲突）
  2003  活动名等于配置前缀 GLOBAL_PREFIX（新建/改名被拒）
  5000  服务器错误
"""


class AppError(Exception):
    """业务异常，携带错误码与消息，由异常处理器转换为统一响应。"""

    def __init__(self, code: int, msg: str):
        super().__init__(msg)
        self.code = code
        self.msg = msg


# ---------- 错误码常量 ----------
CODE_OK = 0
CODE_PARAM = 1001
CODE_UNAUTH = 1002
CODE_FORBIDDEN = 1003
CODE_NOT_FOUND = 2001
CODE_DUPLICATE = 2002
CODE_RESERVED_PREFIX = 2003
CODE_SERVER = 5000

# ---------- 常用提示 ----------
MSG_OK = "ok"
MSG_PARAM = "参数错误"
MSG_UNAUTH = "未登录或登录已过期"
MSG_FORBIDDEN = "无权限（需要读写角色）"
MSG_NOT_FOUND = "资源不存在"
MSG_DUPLICATE = "名称或串号重复"
MSG_RESERVED_PREFIX = "活动名不可等于系统保留前缀"
MSG_SERVER = "服务器内部错误"


def ok(data=None, msg: str = MSG_OK) -> dict:
    """成功响应。"""
    return {"code": CODE_OK, "msg": msg, "data": data}


def fail(code: int, msg: str, data=None) -> dict:
    """失败响应。"""
    return {"code": code, "msg": msg, "data": data}
