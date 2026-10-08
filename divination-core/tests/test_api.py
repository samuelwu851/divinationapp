import json

from divination.api import handle


def test_handle_lookup():
    resp = json.loads(handle('{"cmd": "lookup", "value": 63}'))
    assert resp["name"] == "乾為天"
    assert resp["lines"] == [1, 1, 1, 1, 1, 1]


def test_handle_flip():
    resp = json.loads(handle('{"cmd": "flip", "value": 63, "line": 1}'))
    assert resp["value"] == 31          # 乾翻初爻 → 天風姤
    assert resp["name"] == "天風姤"


def test_handle_yilin():
    resp = json.loads(handle('{"cmd": "yilin", "org_value": 63, "chg_value": 0}'))
    assert resp["org_value"] == 63
    assert resp["chg_value"] == 0
    assert resp["text"] == "招殃來螫，害我邦國；病在手足，不得安息。"


def test_handle_unknown_cmd():
    """未知命令返回 error，而不是崩。"""
    resp = json.loads(handle('{"cmd": "bogus"}'))
    assert "error" in resp


def test_handle_bad_json():
    """坏 JSON 也被兜住，返回 error。"""
    resp = json.loads(handle("not json"))
    assert "error" in resp
