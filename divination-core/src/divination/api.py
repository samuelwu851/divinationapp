"""api —— 对外总机：平台层（Swift / 网页）唯一需要知道的入口。

把一条 JSON 请求路由到对应功能，返回 JSON 响应。
以后加新命令 / 新术数，只在这里加分支，C 桥和 Swift 都不用动。

请求： {"cmd": "<命令>", ...参数}
响应： 命令决定（卦象 JSON，或 {"error": "..."}）
"""
import json

from divination.iching import service as iching_service
from divination.ganzhi import service as ganzhi_service
from divination.meihua import service as meihua_service
from divination.huangji import service as huangji_service


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
        elif cmd == "bazi":
            return ganzhi_service.bazi_json(
                req["year"], req["month"], req["day"], req["hour"], req["minute"],
                req.get("longitude"),              # 没选地区就是 None
                req.get("tz_offset_hours", 8),     # 默认北京 +8
            )
        elif cmd == "meihua":
            return meihua_service.qigua_json(
                req["year"], req["month"], req["day"], req["hour"], req["minute"],
                req.get("longitude"),
                req.get("tz_offset_hours", 8),
            )
        elif cmd == "huangji":
            return huangji_service.paipan_from_date_json(
                req["year"], req["month"], req["day"],
                req.get("hour", 0), req.get("minute", 0),
                req.get("is_lunar", False),         # 前端传农历则 True
                req.get("is_leap", False),          # 农历闰月则 True（month 仍填 1-12）
                req.get("year_start", "lichun"),    # 岁首：daxue / dongzhi / lichun
            )
        elif cmd == "huangji_full":
            return huangji_service.paipan_full_from_date_json(
                req["year"], req["month"], req["day"],
                req.get("hour", 0), req.get("minute", 0),
                req.get("is_lunar", False),         # 前端传农历则 True
                req.get("is_leap", False),          # 农历闰月则 True（month 仍填 1-12）
                req.get("year_start", "lichun"),    # 岁首：daxue / dongzhi / lichun
                req.get("day_rule", "yuegua"),      # 日卦起法：yuegua(月卦起) / shigua(世卦起)
            )
        elif cmd == "solar_to_lunar":
            return ganzhi_service.solar_to_lunar_json(
                req["year"], req["month"], req["day"],
                req.get("hour", 0), req.get("minute", 0),
            )
        elif cmd == "lunar_months":
            return ganzhi_service.lunar_months_json(req["year"])
        else:
            return _error(f"unknown cmd: {cmd!r}")
    except Exception as e:
        return _error(f"{type(e).__name__}: {e}")


def _error(message: str) -> str:
    return json.dumps({"error": message}, ensure_ascii=False)