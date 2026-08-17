"""
初始化脚本（dev-plan v4 §2 / T03）。

职责：
1. 确保数据库存在（不存在则 CREATE DATABASE，字符集 utf8mb4）。
2. 执行 sql/init_db.sql 中的建表语句（跳过 CREATE DATABASE / USE，连接时不选默认库，表名已带 whatsinthebox. 库限定，明文连接即可落库）。
3. 创建首个管理员账号：
   - 读取 .env 的 ADMIN_USER / ADMIN_PASS（默认 admin/admin123）；
   - 若管理员已存在则不重复创建；`--reset` 可重设密码。
4. 配置一致性校验：打印 GLOBAL_PREFIX，提示活动名禁止等于该前缀。

用法：
    python seed.py            # 初始化库表 + 创建管理员
    python seed.py --reset    # 已存在则重设管理员密码
"""
import argparse
import os
import sys

# 允许直接以脚本方式运行（backend/ 加入 sys.path）
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.core import config
from app.core.security import generate_salt, hash_password
from app.core import db


def ensure_database() -> None:
    """确保目标数据库存在（连接时不选库，CREATE DATABASE IF NOT EXISTS）。"""
    tmp_conn = db.connect_with_retry(database=None)
    try:
        with tmp_conn.cursor(cursorclass=db.DictCursor) as cur:
            cur.execute(
                "CREATE DATABASE IF NOT EXISTS `{}` "
                "DEFAULT CHARACTER SET utf8mb4 DEFAULT COLLATE utf8mb4_general_ci".format(
                    config.settings.DB_NAME
                )
            )
        tmp_conn.commit()
    finally:
        tmp_conn.close()


def ensure_schema(conn) -> None:
    """执行 init_db.sql（去掉 CREATE DATABASE / USE 行）。"""
    sql_path = os.path.join(BACKEND_DIR, "sql", "init_db.sql")
    if not os.path.exists(sql_path):
        print(f"警告：未找到 {sql_path}，跳过自动建表。请手动执行建表 SQL。")
        return
    with open(sql_path, "r", encoding="utf-8") as f:
        content = f.read()
    statements = []
    for raw in content.split(";"):
        # 去掉以 -- 开头的 SQL 注释行，避免「注释 + CREATE TABLE」整块被误跳过
        # （init_db.sql 每个建表语句前都有 -- 注释行）。
        lines = [ln for ln in raw.splitlines() if not ln.strip().startswith("--")]
        stmt = "\n".join(lines).strip()
        if not stmt:
            continue
        upper = stmt.upper()
        if upper.startswith("CREATE DATABASE") or upper.startswith("USE"):
            continue
        statements.append(stmt)
    with conn.cursor(cursorclass=db.DictCursor) as cur:
        for stmt in statements:
            cur.execute(stmt)
    conn.commit()
    print(f"已确保数据库表结构（{len(statements)} 条语句）。")


def create_admin(conn, reset: bool) -> None:
    """创建/重设管理员。"""
    username = config.settings.ADMIN_USER
    password = config.settings.ADMIN_PASS
    with conn.cursor(cursorclass=db.DictCursor) as cur:
        cur.execute(
            "SELECT id, username FROM `whatsinthebox`.`user` WHERE username=%s AND deleted=0",
            (username,),
        )
        row = cur.fetchone()
        if row is None:
            salt = generate_salt()
            pwd_hash = hash_password(password, salt)
            cur.execute(
                "INSERT INTO `whatsinthebox`.`user` (username, password_hash, salt, nickname, role) "
                "VALUES (%s, %s, %s, %s, %s)",
                (username, pwd_hash, salt, username, "rw"),
            )
            conn.commit()
            print(f"已创建管理员账号：{username} / {password}（角色 rw）")
        elif reset:
            salt = generate_salt()
            pwd_hash = hash_password(password, salt)
            cur.execute(
                "UPDATE `whatsinthebox`.`user` SET password_hash=%s, salt=%s, update_time=NOW() "
                "WHERE id=%s",
                (pwd_hash, salt, row["id"]),
            )
            conn.commit()
            print(f"已重设管理员密码：{username} / {password}")
        else:
            print(f"管理员 {username} 已存在，跳过创建（如需重设加 --reset）。")


def main() -> None:
    parser = argparse.ArgumentParser(description="WhatsInTheBox 初始化")
    parser.add_argument("--reset", action="store_true", help="重设管理员密码")
    args = parser.parse_args()

    print(f"数据库：{config.settings.DB_HOST}:{config.settings.DB_PORT}/{config.settings.DB_NAME}")
    print(f"全局前缀 GLOBAL_PREFIX = {config.settings.GLOBAL_PREFIX}（活动名禁止等于此值）")

    ensure_database()
    conn = db.get_conn()
    try:
        ensure_schema(conn)
        create_admin(conn, args.reset)
        print("初始化完成。")
    finally:
        db.close_conn(conn)


if __name__ == "__main__":
    main()
