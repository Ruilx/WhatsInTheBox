"""鉴权相关测试（dev-plan v4 §账号登录与权限）。"""
API = "/whatsinthebox"


def test_login_wrong_password(client):
    resp = client.post(f"{API}/auth/login", json={"username": "admin", "password": "wrong-pwd"})
    assert resp.status_code == 200
    assert resp.json()["code"] == 1002  # 用户名或密码错误


def test_me_without_cookie(client):
    resp = client.get(f"{API}/auth/me")
    assert resp.status_code == 200
    assert resp.json()["code"] == 1002  # 未登录


def test_login_and_me(auth_client):
    # 登录已在 fixture 中完成，这里校验受保护接口可访问
    resp = auth_client.get(f"{API}/auth/me")
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    data = body["data"]
    assert data["username"] == "admin"
    assert data["role"] == "rw"


def test_logout(auth_client):
    resp = auth_client.post(f"{API}/auth/logout")
    assert resp.status_code == 200
    assert resp.json()["code"] == 0
    # 登出后 cookie 失效
    after = auth_client.get(f"{API}/auth/me")
    assert after.json()["code"] == 1002


def test_change_password_requires_rw(auth_client):
    # admin 为 rw，可直接改密；验证写接口可达且旧密码校验生效
    resp = auth_client.post(
        f"{API}/auth/change_password",
        json={"old_pwd": "admin123", "new_pwd": "admin123"},  # 改回原密码，避免污染 seed
    )
    assert resp.status_code == 200
    # 旧密码错误应被拒
    bad = auth_client.post(
        f"{API}/auth/change_password",
        json={"old_pwd": "not-the-pwd", "new_pwd": "admin123"},
    )
    assert bad.json()["code"] == 1001
