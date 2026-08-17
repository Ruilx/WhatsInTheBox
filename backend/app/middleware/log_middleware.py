"""
读操作日志中间件（dev-plan v4 §日志表 / §7.13 / §7.21 / R-log 全量）。

目标：对「读操作」自动落库（action=query/view/scan），与业务层显式写入的
写操作日志（create/update/delete/take_out/place/login/logout）互补，实现日志全量。

识别规则（按 URL 路径，参数化无关）：
- 仅处理 GET 请求且路径位于 /whatsinthebox/ 下；
- controller 不在 {auth, upload, log}（登录/上传/日志列表本身不自动记）；
- action 属于读动作：
    list / tree / keyword -> query
    detail / taken_out_list -> view
- operator 缺失（未登录）则跳过（读接口本身受 require_login 保护，正常会有 operator）。

日志写入失败不影响主流程（LogService.write 内部吞没异常）。
"""
from starlette.middleware.base import BaseHTTPMiddleware

from app.core import config
from app.services.log_service import LogService
from app.middleware.auth import client_ip, get_operator


# 读动作 -> 日志 action 映射
_READ_ACTION_MAP = {
    "list": "query",
    "tree": "query",
    "keyword": "query",
    "detail": "view",
    "taken_out_list": "view",
}
# 无需自动记录日志的 controller（其读操作已由业务层或自身处理）
_SKIP_CONTROLLERS = {"auth", "upload", "log"}

_log_service = LogService()
_api_prefix = config.settings.API_PREFIX.rstrip("/")  # 形如 /whatsinthebox


class LogMiddleware(BaseHTTPMiddleware):
    """对读操作自动写入日志（全量记录）。"""

    async def dispatch(self, request, call_next):
        response = await call_next(request)
        try:
            self._maybe_log(request)
        except Exception:  # noqa: BLE001
            # 读日志失败绝不阻断业务
            pass
        return response

    def _maybe_log(self, request) -> None:
        if request.method != "GET":
            return
        path = request.url.path
        if not path.startswith(_api_prefix + "/"):
            return
        # /whatsinthebox/controller/action
        rest = path[len(_api_prefix):].strip("/")
        parts = rest.split("/")
        if len(parts) != 2:
            return
        controller, action = parts[0], parts[1]
        if controller in _SKIP_CONTROLLERS:
            return
        if action not in _READ_ACTION_MAP:
            return
        op = get_operator(request)
        if not op:
            return
        log_action = _READ_ACTION_MAP[action]
        ip = client_ip(request)
        self._log_service.write(
            action=log_action,
            object_type=controller,
            object_id=0,
            operator_id=op["user_id"],
            ip=ip,
            detail=f"读操作 {controller}/{action}",
        )
