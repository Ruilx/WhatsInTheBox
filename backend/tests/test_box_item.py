"""箱子 / 物品 / 取出 流程测试（dev-plan v4 §3.2 / §7.12-§7.14）。

覆盖核心业务链路：
  建活动 -> 建箱子 -> 建物品(入箱) -> 取出(take_out) -> 已取出列表命中 -> 日志可查。
"""
import time
API = "/whatsinthebox"


def _uniq(prefix):
    return f"{prefix}{int(time.time() * 1000)}"


def test_box_item_takeout_flow(auth_client):
    act_name = _uniq("QA活动")
    # 建活动
    ac = auth_client.post(f"{API}/activity/create", json={"name": act_name, "status": 1})
    aid = ac.json()["data"]["id"]
    assert aid > 0

    # 建箱子
    bc = auth_client.post(f"{API}/box/create", json={"activity_id": aid, "name": _uniq("箱"), "type": ["主要", "易碎"]})
    bid = bc.json()["data"]["id"]
    assert bid > 0

    # 建物品（入箱）
    ic = auth_client.post(f"{API}/item/create", json={"box_id": bid, "name": _uniq("物"), "activity_id": aid})
    iid = ic.json()["data"]["id"]
    assert iid > 0

    # 物品列表（箱内）
    il = auth_client.get(f"{API}/item/list", params={"box_id": bid})
    assert il.json()["code"] == 0
    assert any(r["id"] == iid for r in il.json()["data"]["list"])

    # 取出
    to = auth_client.post(f"{API}/item/take_out", json={"id": iid})
    assert to.json()["code"] == 0

    # 已取出列表命中（box_id=0 归集到活动）
    tol = auth_client.get(f"{API}/item/taken_out_list", params={"activity_id": aid})
    assert tol.json()["code"] == 0
    assert any(r["id"] == iid for r in tol.json()["data"]["list"])

    # 箱子树
    tree = auth_client.get(f"{API}/box/tree", params={"activity_id": aid})
    assert tree.json()["code"] == 0

    # 清理：删物品 / 箱子 / 活动
    auth_client.post(f"{API}/item/delete", json={"id": iid})
    auth_client.post(f"{API}/box/delete", json={"id": bid})
    auth_client.post(f"{API}/activity/delete", json={"id": aid})


def test_log_list_contains_entries(auth_client):
    # 登录与上面的活动操作都会写日志；list 应返回非空
    resp = auth_client.get(f"{API}/log/list", params={"page": 1, "size": 20})
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["total"] >= 1
