"""
时间工具模块（dev-plan v4 §7.6）。

时区统一 Asia/Shanghai：按北京时间存、按北京时间展示。
前端原样显示、不做时区转换。本模块仅提供后端生成 SH 当前时间的辅助。
"""
from datetime import datetime, timezone, timedelta
from typing import Optional


def parse_dt(value: Optional[str]) -> Optional[datetime]:
    """
    将前端传入的时间字符串解析为 datetime（上海时间，naive）。
    支持 'YYYY-MM-DD HH:MM:SS'、'YYYY-MM-DDTHH:MM:SS'、'YYYY-MM-DD' 等常见格式；
    空值 / None / 无法解析 -> None（表示不设置时间）。
    """
    if value is None or value == "":
        return None
    text = str(value).strip()
    if not text:
        return None
    # 替换 'T' 为空格，统一为 'YYYY-MM-DD HH:MM:SS'
    text = text.replace("T", " ").replace("Z", "")
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(text[:19] if " " in text else text[:10], fmt)
        except ValueError:
            continue
    # 兜底：尝试 ISO 解析
    try:
        dt = datetime.fromisoformat(text)
        return dt.replace(tzinfo=None)
    except ValueError:
        return None

# 上海时区（UTC+8，无夏令时）
_SH_TZ = timezone(timedelta(hours=8))


def now_sh() -> datetime:
    """返回当前北京（上海）时间（带时区信息，便于序列化）。"""
    return datetime.now(_SH_TZ)


def now_sh_naive() -> datetime:
    """返回当前上海时间的 naive datetime（不带 tz，匹配 MySQL DATETIME）。"""
    return datetime.now(_SH_TZ).replace(tzinfo=None)


def format_sh(dt) -> str:
    """将 datetime 格式化为 'YYYY-MM-DD HH:MM:SS'（上海时间原样展示）。"""
    if dt is None:
        return ""
    if dt.tzinfo is not None:
        dt = dt.astimezone(_SH_TZ).replace(tzinfo=None)
    return dt.strftime("%Y-%m-%d %H:%M:%S")
