"""service —— 梅花易数时间起卦的门面层。

流程：时间地点 → (复用 ganzhi.resolve 拿四柱+农历) → 四个数 → core.qigua
     → 本卦+动爻 → (复用 iching.core.flip) → 变卦 → JSON。
"""
import json
from datetime import datetime

from divination.ganzhi import service as ganzhi_service
from divination.iching import core as iching_core
from divination.iching import repository as iching_repo
from divination.meihua import core


def qigua(
    moment: datetime,
    longitude: float | None = None,
    tz_offset_hours: float = 8,
) -> dict:
    """时间起卦：返回本卦、动爻、变卦。"""
    r = ganzhi_service.resolve(moment, longitude, tz_offset_hours)
    sizhu = r["sizhu"]
    lunar = r["lunar"]

    year = sizhu.year.zhi + 1      # 地支 子=0 → 梅花数 子=1
    hour = sizhu.hour.zhi + 1
    month = lunar["month"]
    day = lunar["day"]

    ben, moving = core.qigua(year, month, day, hour)
    bian = iching_core.flip(ben, moving)    # 变卦 = 本卦动爻变，复用易经

    return {
        "numbers": {"year": year, "month": month, "day": day, "hour": hour},
        "ben_gua": {"value": ben.value, "name": iching_repo.name_of(ben)},
        "moving_line": moving,
        "bian_gua": {"value": bian.value, "name": iching_repo.name_of(bian)},
    }


def qigua_json(
    year: int, month: int, day: int, hour: int, minute: int,
    longitude: float | None = None,
    tz_offset_hours: float = 8,
) -> str:
    """平台层边界：基本类型进，JSON 串出。"""
    moment = datetime(year, month, day, hour, minute)
    return json.dumps(
        qigua(moment, longitude, tz_offset_hours),
        ensure_ascii=False,
    )
