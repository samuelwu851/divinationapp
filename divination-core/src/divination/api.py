"""api —— 对外总机：平台层（Swift / 网页）唯一需要知道的入口。

把一条 JSON 请求路由到对应功能，返回 JSON 响应。
以后加新命令 / 新术数，只在这里加分支，C 桥和 Swift 都不用动。

请求： {"cmd": "<命令>", ...参数}
响应： 命令决定（卦象 JSON，或 {"error": "..."}）
"""
import json

from divination.iching import service as iching_service


def handle(request_json: str) -> str:
    """平台层调用的唯一函数：请求 JSON 进，响应 JSON 出。"""
    try:
        req = json.loads(request_json)
        cmd = req.get("cmd")

        if cmd == "lookup":
            return iching_service.lookup_json(req["value"])
        elif cmd == "flip":
            return iching_service.flip_json(req["value"], req["line"])
        elif cmd == "yilin":
            return iching_service.yilin_json(req["org_value"], req["chg_value"])
        else:
            return _error(f"unknown cmd: {cmd!r}")
    except Exception as e:
        return _error(f"{type(e).__name__}: {e}")


def _error(message: str) -> str:
    return json.dumps({"error": message}, ensure_ascii=False)