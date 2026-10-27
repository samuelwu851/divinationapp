"""
本层通过具体时刻返回干支历
用lunar_python拿到干支，并且转换成干支编码

"""
from datetime import datetime

from lunar_python import Lunar, LunarYear, Solar

from divination.ganzhi.model import DiZhi, GanZhi, SiZhu, TianGan

_GAN = "甲乙丙丁戊己庚辛壬癸"
_ZHI = "子丑寅卯辰巳午未申酉戌亥"

def _parse_ganzhi(text: str) -> GanZhi:
    """把库给的两字干支串(如 "甲辰")转成 GanZhi。"""
    gan = TianGan(_GAN.index(text[0]))
    zhi = DiZhi(_ZHI.index(text[1]))
    return GanZhi(gan, zhi)


def _lunar(moment: datetime):
    """把一个时刻交给 lunar_python，拿到它的 Lunar 对象。"""
    return Solar.fromYmdHms(
        moment.year, moment.month, moment.day,
        moment.hour, moment.minute, moment.second,
    ).getLunar()


def sizhu_of(jieqi_moment: datetime, local_moment: datetime | None = None) -> SiZhu:
    """返回四柱。年/月 与 日/时 可用不同时刻算：

      jieqi_moment —— 定年、月(节气锚定北京时间的那个时刻)
      local_moment —— 定日、时(当地真太阳时)；省略时四柱都用 jieqi_moment

    用 lunar_python 的 Exact 取法：
      年——按立春精确时刻翻
      月——按节(节令)精确时刻翻
      日——日界在23:00，不分早晚子
      时——子时按新一天的日干起
    """
    if local_moment is None:
        local_moment = jieqi_moment
    ym = _lunar(jieqi_moment)
    dh = _lunar(local_moment)
    return SiZhu(
        year=_parse_ganzhi(ym.getYearInGanZhiExact()),
        month=_parse_ganzhi(ym.getMonthInGanZhiExact()),
        day=_parse_ganzhi(dh.getDayInGanZhiExact()),
        hour=_parse_ganzhi(dh.getTimeInGanZhi()),
    )


def lunar_info(moment: datetime) -> dict:
    """农历日期 + 前后最近两个节气(按传入的北京时间算，全球统一)。"""
    lunar = _lunar(moment)
    prev = lunar.getPrevJieQi()
    nxt = lunar.getNextJieQi()
    return {
        "lunar_date": lunar.toString(),
        "month": abs(lunar.getMonth()),   # 农历月数字；闰月库返回负数，取绝对值(闰二月→2)
        "day": lunar.getDay(),            # 农历日数字
        "prev_jieqi": {"name": prev.getName(), "time": prev.getSolar().toYmdHms()},
        "next_jieqi": {"name": nxt.getName(), "time": nxt.getSolar().toYmdHms()},
    }


def lunar_to_solar(year: int, month: int, day: int,
                   hour: int = 0, minute: int = 0) -> datetime:
    """农历 → 公历 datetime。闰月用负数月份(lunar_python 约定，如闰二月 month=-2)。"""
    s = Lunar.fromYmdHms(year, month, day, hour, minute, 0).getSolar()
    return datetime(s.getYear(), s.getMonth(), s.getDay(),
                    s.getHour(), s.getMinute(), s.getSecond())


def lichun_of(solar_year: int) -> datetime:
    """某公历年的立春时刻(北京时间)。"""
    lc = _lunar(datetime(solar_year, 6, 1)).getJieQiTable()["立春"]
    return datetime(lc.getYear(), lc.getMonth(), lc.getDay(),
                    lc.getHour(), lc.getMinute(), lc.getSecond())


def solar_to_lunar(year: int, month: int, day: int,
                   hour: int = 0, minute: int = 0) -> dict:
    """公历 → 农历：年 / 月(1-12) / 是否闰月 / 日。"""
    lunar = _lunar(datetime(year, month, day, hour, minute))
    m = lunar.getMonth()
    return {
        "lunar_year": lunar.getYear(),
        "lunar_month": abs(m),
        "is_leap": m < 0,
        "lunar_day": lunar.getDay(),
    }


_MONTH_LABELS = ("正", "二", "三", "四", "五", "六", "七", "八", "九", "十", "冬", "腊")


def lunar_months(year: int) -> list[dict]:
    """某农历年的月份结构：[{month(1-12), is_leap, days, label}, ...]，闰月自然在列。"""
    result = []
    for m in LunarYear.fromYear(year).getMonths():
        if m.getYear() != year:
            continue
        mon = m.getMonth()
        leap = mon < 0
        number = abs(mon)
        label = ("闰" if leap else "") + _MONTH_LABELS[number - 1] + "月"
        result.append({"month": number, "is_leap": leap,
                       "days": m.getDayCount(), "label": label})
    return result