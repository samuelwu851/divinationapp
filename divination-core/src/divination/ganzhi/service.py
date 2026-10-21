"""service —— 干支历对外的门面层：把各层拼成一个干净接口。

核心规则(真太阳时为基准，节气锚定北京时间)：
  1. 选了地区 → 先把时间栏换成当地真太阳时(core)
  2. 定节气(年/月)时，把真太阳时按整小时挪到北京时区(日期/小时变、分钟不变)，
     这样全球统一；日/时仍用当地真太阳时
  3. 没选地区 → 用设备(北京)时间直接算
返回纯 JSON 可序列化的数据，不把内部类型漏给平台层。
"""
import json
from datetime import datetime, timedelta

from divination.ganzhi import core, repository


def bazi(
    moment: datetime,
    longitude: float | None = None,
    tz_offset_hours: float = 8,
) -> dict:
    """时间栏时刻进；选了地区(传经度)就按真太阳时排盘，否则用时间栏。"""
    if longitude is not None:
        tst = core.true_solar_time(moment, longitude, tz_offset_hours)
    else:
        tst = moment

    # 节气(年/月)锚定北京时间：真太阳时按整小时挪到北京时区，分钟不变
    beijing = tst + timedelta(hours=(8 - tz_offset_hours))

    sizhu = repository.sizhu_of(beijing, tst)   # 年/月←北京时间，日/时←真太阳时
    info = repository.lunar_info(beijing)        # 农历/节气按北京时间

    return {
        "input_time": moment.strftime("%Y-%m-%d %H:%M:%S"),             # 时间栏(原样)
        "true_solar_time": tst.strftime("%Y-%m-%d %H:%M:%S") if longitude is not None else None,
        "year": sizhu.year.name,
        "month": sizhu.month.name,
        "day": sizhu.day.name,
        "hour": sizhu.hour.name,
        "lunar": info["lunar_date"],
        "prev_jieqi": info["prev_jieqi"],
        "next_jieqi": info["next_jieqi"],
    }


def bazi_json(
    year: int, month: int, day: int, hour: int, minute: int,
    longitude: float | None = None,
    tz_offset_hours: float = 8,
) -> str:
    """平台层边界：基本类型进，JSON 串出。"""
    moment = datetime(year, month, day, hour, minute)
    return json.dumps(
        bazi(moment, longitude, tz_offset_hours),
        ensure_ascii=False,
    )
