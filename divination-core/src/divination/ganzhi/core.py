"""
目前放真太阳时换算：把出生地的钟表时间，修正成当地"太阳说了算"的真太阳时。
两步修正：
  ① 经度时差——你不在本时区中央经线上，太阳到顶的时刻就有偏差
  ② 均时差 ——地球轨道是椭圆、黄赤有交角，太阳本身走得时快时慢
"""
import math
from datetime import datetime, timedelta


def equation_of_time(day_of_year: int) -> float:
    """均时差（分钟）：真太阳时 − 平太阳时，全年约在 −15 ~ +16 分钟之间。

    只跟"一年的第几天"有关。用常见近似式，精度约 ±30 秒，玄学足够。
    正值表示真太阳时比平太阳时快。
    """
    b = 2 * math.pi * (day_of_year - 81) / 364
    return 9.87 * math.sin(2 * b) - 7.53 * math.cos(b) - 1.5 * math.sin(b)


def true_solar_time(
    clock: datetime, longitude: float, tz_offset_hours: float
) -> datetime:
    """把当地钟表时间换算成真太阳时。

    clock：当地民用钟表时间（naive datetime）
    longitude：当地经度，东经为正、西经为负（北京约 116.4，纽约约 -74）
    tz_offset_hours：当地时区相对 UTC 的偏移（北京 8，纽约东部 -5）
    """
    # ① 经度时差：每偏离中央经线 1°，差 4 分钟
    central_meridian = tz_offset_hours * 15
    longitude_minutes = (longitude - central_meridian) * 4

    # ② 均时差
    eot_minutes = equation_of_time(clock.timetuple().tm_yday)

    return clock + timedelta(minutes=longitude_minutes + eot_minutes)
