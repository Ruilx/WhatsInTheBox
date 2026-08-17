"""
pytest 公共夹具（dev-plan v4 QA）。

- client: 基于 FastAPI TestClient 的应用实例（同步 def 路由，无事件循环阻塞）。
- auth_client: 已用 admin/admin123 登录、携带会话 Cookie 的客户端（读写角色）。
- ro 场景本套件暂不覆盖（当前仅 seed 了 rw 管理员）；如需可再 seed 一个 ro 账号。

注意：所有接口依赖数据库；运行前需确保 .env 中的 MySQL 可达（见 DEPLOY.md）。
本地若 pymysql 无法连接（见 DEPLOY.md「本地开发环境」一节的环境说明），请改为在
Docker 容器内执行 `pytest`，容器内为官方 PyMySQL，可正常完成 caching_sha2 握手。
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app

API = "/whatsinthebox"
ADMIN_USER = "admin"
ADMIN_PASS = "admin123"


@pytest.fixture(scope="session")
def client():
    return TestClient(app)


@pytest.fixture(scope="session")
def auth_client(client):
    """登录 admin 并返回已携带会话 Cookie 的客户端。"""
    resp = client.post(f"{API}/auth/login", json={"username": ADMIN_USER, "password": ADMIN_PASS})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["code"] == 0, body
    assert "wb_session" in client.cookies, "登录未下发会话 Cookie"
    return client
