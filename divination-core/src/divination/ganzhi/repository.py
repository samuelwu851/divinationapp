"""
本层通过具体时刻返回干支历
用lunar_python拿到干支，并且转换成干支编码

"""
from datetime import datetime

from lunar_python import Solar

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