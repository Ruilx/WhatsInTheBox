"""活动 CRUD 测试（dev-plan v4 §3.2）。

流程：list(空) -> create -> list(命中) -> detail -> update -> toggle_status -> delete。
活动名全局唯一且禁止等于 GLOBAL_PREFIX(_wb)。
"""
import time
API = "/whatsinthebox"


def _uniq_name(prefix="QA活动"):
    return f"{prefix}{int(time.time() * 1000)}"


def test_activity_list_empty(auth_client):
    resp = auth_client.get(f"{API}/activity/list", params={"keyword": "___no_such_activity___"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["list"] == []


def test_activity_crud(auth_client):
    name = _uniq_name()
    # create
    c = auth_client.post(f"{API}/activity/create", json={"name": name, "desc": "qa", "type": "搬家", "status": 1})
    assert c.status_code == 200
    aid = c.json()["data"]["id"]
    assert aid > 0

    # list by keyword
    l = auth_client.get(f"{API}/activity/list", params={"keyword": name})
    assert l.json()["code"] == 0
    assert any(r["id"] == aid for r in l.json()["data"]["list"])

    # detail by id
    d = auth_client.get(f"{API}/activity/detail", params={"id": aid})
    assert d.json()["code"] == 0
    assert d.json()["data"]["name"] == name

    # update
    u = auth_client.post(f"{API}/activity/update", json={"id": aid, "name": name, "desc": "updated", "status": 2})
    assert u.json()["code"] == 0

    # toggle_status
    t = auth_client.post(f"{API}/activity/toggle_status", json={"id": aid, "status": 3})
    assert t.json()["code"] == 0

    # delete
    dele = auth_client.post(f"{API}/activity/delete", json={"id": aid})
    assert dele.json()["code"] == 0

    # 复查已删
    d2 = auth_client.get(f"{API}/activity/detail", params={"id": aid})
    assert d2.json()["code"] == 2001  # 资源不存在


def test_activity_name_reserved_prefix(auth_client):
    # 活动名等于 GLOBAL_PREFIX(_wb) 应被拒（2003）
    r = auth_client.post(f"{API}/activity/create", json={"name": "_wb"})
    assert r.json()["code"] == 2003
