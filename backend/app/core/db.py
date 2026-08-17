"""
数据库连接模块（驱动：mysqlclient / MySQLdb，基于 libmysqlclient）。

为什么用 mysqlclient 而非 pymysql：
开发库 10.25.0.201（非标准 MySQL 前端：自签证书、隐藏 caching_sha2_password_public_key）
会拒绝 pymysql 的 caching_sha2 握手（1045，即使账号/密码正确）；mysqlclient 使用与 CLI
相同的 libmysqlclient，可正常完成认证。
关键约束（已验证）：开发库 10.25.0.201 为非标准 MySQL 前端，COM_INIT_DB（USE / 选默认库）
偶发 1044，且 mysqlclient 无法稳定协商 TLS 来绕过（服务端 TLS 端点时好时坏：同一 ssl 配置
10/10 成功与 10/10 失败交替出现）。因此【连接时绝不选中默认库】，所有 SQL 一律使用库限定表名
（如 whatsinthebox.activity），明文连接 + 库限定查询经验证 100% 稳定，不依赖 TLS / COM_INIT_DB。
故本地 dev 设 DB_SSL=false（明文）；标准 MySQL 8 生产环境若需可设 DB_SSL=true。
mysqlclient 对标准 MySQL 8 同样完全兼容（Docker 生产环境亦可用，需镜像内装 libmysqlclient-dev）。

设计（dev-plan v4 §1.1 / R1 / §7.3）：
- 不使用连接池，采用「惰性连接 + 自管连接」：真正需要访问 DB 时才建立连接，用完即释放。
- 字符集 utf8mb4 + utf8mb4_general_ci；会话时区统一 Asia/Shanghai（按北京时间存与展示）。
- 断线兜底：连接前 ping(reconnect=True)。
- 每个 DAO 方法自行获取连接并在 finally 中关闭，避免连接泄漏。

MySQLdb 与 pymysql 的差异（已在此处处理）：
- 连接参数用 passwd= / db=（非 password= / database=）；autocommit 连后设置，不传入 connect。
- connect 不接受 cursorclass，游标统一用 conn.cursor(cursorclass=DictCursor)。
"""
import time

import MySQLdb
from MySQLdb.cursors import DictCursor
from MySQLdb import OperationalError
from app.core import config


def get_ssl_config():
    """返回 MySQLdb 的 ssl 连接参数；DB_SSL=false 时返回 None（明文，本地 dev 默认）。

    历史教训（开发库 10.25.0.201）：COM_INIT_DB（USE / 选默认库）偶发 1044，且服务端 TLS
    端点时好时坏（同一 ssl 配置 10/10 成功与 10/10 失败交替）。由于我们已改为「连接不选默认库
    + 库限定表名」，查询本身可走明文，不再需要 TLS。因此本地 dev 设 DB_SSL=false。
    标准 MySQL 8 若确需 TLS，设 DB_SSL=true 即返回 ssl 参数（verify 关闭、强制 cipher）。
    """
    if not config.settings.DB_SSL:
        return None
    return {'verify_mode': 0, 'cipher': 'HIGH'}


# 连接类错误码：可重试（网络抖动 / SSL 握手失败）
RETRYABLE_CODES = (1045, 2013, 2003, 2026)


# 连接参数（供 dao / seed 复用）
_DB_CONFIG = dict(
    host=config.settings.DB_HOST,
    port=config.settings.DB_PORT,
    user=config.settings.DB_USER,
    passwd=config.settings.DB_PASSWORD,
    db=config.settings.DB_NAME,
    charset=config.settings.DB_CHARSET,
)


def _try_connect(max_attempts, base_delay, database):
    """执行一轮 MySQLdb 连接重试；成功返回连接，全部失败抛出最后一个 OperationalError。"""
    last_err = None
    for attempt in range(max_attempts):
        cfg = dict(_DB_CONFIG)
        if database is not None:
            cfg["db"] = database
        else:
            cfg.pop("db", None)
        ssl_cfg = get_ssl_config()
        if ssl_cfg:
            cfg["ssl"] = ssl_cfg
        try:
            conn = MySQLdb.connect(**cfg)
        except OperationalError as e:
            last_err = e
            code = e.args[0] if e.args else None
            if code in RETRYABLE_CODES:
                time.sleep(base_delay * (2 ** min(attempt, 4)))  # 指数退避
                continue
            raise
        # 连接成功：兜底确认可用 + 会话时区（北京时间）
        try:
            conn.autocommit(False)
            conn.ping(True)
            with conn.cursor(cursorclass=DictCursor) as cur:
                cur.execute("SET time_zone = '+08:00'")
            conn.commit()
        except Exception:
            conn.close()
            raise
        return conn
    raise last_err


def connect_with_retry(max_attempts: int = 12, base_delay: float = 0.3, database=None):
    """
    建立 MySQL 连接，对连接类错误做指数退避重试。

    :param database: 指定要选中的库；None 表示连接时不选库（供 CREATE DATABASE / ensure_database 使用）。
    :return: 已 ping 连通、会话时区已置 +08:00 的连接。
    """
    return _try_connect(max_attempts, base_delay, database)


def get_conn():
    """
    惰性建立并返回一条 MySQL 连接（含重连兜底与会话时区设置），【不选中默认库】。

    原因：开发库 10.25.0.201 为非标准 MySQL 前端，COM_INIT_DB（USE / 选库）偶发 1044，
    且 mysqlclient 无法稳定协商 TLS 来绕过；原生 CLI 走 PREFERRED SSL 才可稳定选库。
    因此统一「连接时不选库」，所有 SQL 用库限定表名（如 whatsinthebox.activity），
    已验证该方式 100% 稳定（不依赖 TLS / COM_INIT_DB）。
    ensure_database（CREATE DATABASE）本就走 connect_with_retry(database=None) 不选库。
    """
    return connect_with_retry()


def close_conn(conn) -> None:
    """释放连接（自管连接：用完即释放）。"""
    if conn is None:
        return
    try:
        conn.close()
    except Exception:
        # 关闭失败忽略，避免掩盖主流程异常
        pass


def execute_transaction(func, *args, **kwargs):
    """
    在一个事务中执行 func(conn, *args, **kwargs)。
    - 成功提交，返回 func 结果；
    - 失败回滚并上抛异常。
    调用方无需手动开关连接。
    """
    conn = get_conn()
    try:
        result = func(conn, *args, **kwargs)
        conn.commit()
        return result
    except Exception:
        conn.rollback()
        raise
    finally:
        close_conn(conn)
