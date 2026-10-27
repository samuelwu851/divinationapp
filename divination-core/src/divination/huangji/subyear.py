"""subyear —— 皇极经世 年以下（月·日·时·分）推卦。

依《观物外篇》"举年见月，举月见日，举日见时，阳统阴也"，把 运→世→年 的两种操作
（六爻变 / 六十卦轮）按 12/30 交替结构向下递推：

    年(12月) --六爻变,每变管二月--> 月(30日) --两月六十日,六十卦轮--> 日
    日(12时) --六爻变,每变管二时--> 时(30分) --两时六十分,六十卦轮--> 分(长分,4分钟)

上层(元会运世年)用 huangji.core；节气时刻用 huangji.astro。
历法约定（可配置 Config）：皇极年自冬至/子月起、月以十二中气分、日界 23:00。
依据与取舍详见《皇极经世-月日时推卦方法.md》。
"""
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from typing import Callable

from divination.huangji import astro, core

# 简体卦名（= Hexagram.value 编码，0坤…63乾），用于本层可读输出
NAMES = {
    0: "坤", 1: "剥", 2: "比", 3: "观", 4: "豫", 5: "晋", 6: "萃", 7: "否",
    8: "谦", 9: "艮", 10: "蹇", 11: "渐", 12: "小过", 13: "旅", 14: "咸", 15: "遁",
    16: "师", 17: "蒙", 18: "坎", 19: "涣", 20: "解", 21: "未济", 22: "困", 23: "讼",
    24: "升", 25: "蛊", 26: "井", 27: "巽", 28: "恒", 29: "鼎", 30: "大过", 31: "姤",
    32: "复", 33: "颐", 34: "屯", 35: "益", 36: "震", 37: "噬嗑", 38: "随", 39: "无妄",
    40: "明夷", 41: "贲", 42: "既济", 43: "家人", 44: "丰", 45: "离", 46: "革", 47: "同人",
    48: "临", 49: "损", 50: "节", 51: "中孚", 52: "归妹", 53: "睽", 54: "兑", 55: "履",
    56: "泰", 57: "大畜", 58: "需", 59: "小畜", 60: "大壮", 61: "大有", 62: "夬", 63: "乾",
}
SIXTY = core._SIXTY
FOUR_CARDINAL = {0, 63, 18, 45}
BRANCHES = core.BRANCHES
SEASON_RUN_GUA = {0: 45, 1: 63, 2: 18, 3: 0}   # 闰卦（四象）：子丑寅离 卯辰巳乾 午未申坎 酉戌亥坤

# year_restart 日法（兼容「皇极经世历法」app，plus.hjjs）：每年岁首民用日起、按六十卦圆图
# 逐日、年内连续、跨年重起，不看时刻与年中节气。起始卦 = 世卦在圆图退 RETREAT 位；
# 岁首交节早于 CUTOFF_HOUR 的年份起始卦再顺延一位（作者把一天的起点定在卯时 05:00）。
YEAR_RESTART_SHI_RETREAT = 16
YEAR_RESTART_CUTOFF_HOUR = 5


def flip_line(h: int, k: int) -> int:
    """第 k 爻变（k=1 初爻…6 上爻），初爻为最高位 bit5。"""
    return h ^ (1 << (6 - k))


def cycle_start_index(h: int) -> int:
    """h 在六十卦圆图中的起点下标；h 为四正卦时取其后第一正卦（乾→姤 坎→蒙 离→革 坤→复）。"""
    return SIXTY.index(core._PRINCIPAL_NEXT.get(h, h))


def _astro(hj_year: int) -> int:
    """皇极年(历史纪年) → 天文纪年。公元后一致；公元前 N 年 = 1−N。"""
    return hj_year if hj_year > 0 else hj_year + 1


# ------------------------------------------------------------------ 配置
@dataclass
class Config:
    tz_hours: float = 8
    year_start: str = "dongzhi"           # dongzhi: 自冬至/子月起；lichun: 自立春/寅月起
    month_boundary: str = "zhongqi"       # zhongqi: 中气分月(子月起冬至)；jieqi: 节气分月(子月起大雪)
    day_start_hour: int = 23              # 日界：23 = 子时起(晚子归次日)；0 = 民用午夜
    day_overflow: str = "wrap"            # 两月超 60 日：wrap 续轮 / leap 用本季四正卦作闰卦
    day_rule: str = "nested"              # 日卦起法：nested=全息(从月卦起、两月块) / year_restart=app(岁首起、年内连续)
    solar_term_provider: Callable[[int, str], datetime] = field(default=astro.solar_term_utc)


DEFAULT = Config()


# ------------------------------------------------------------------ 年 / 月定位
def _tz(cfg: Config) -> timezone:
    return timezone(timedelta(hours=cfg.tz_hours))


def _term(cfg: Config, year: int, name: str) -> datetime:
    return cfg.solar_term_provider(year, name).astimezone(_tz(cfg))


def month_boundaries(hj_year: int, cfg: Config = DEFAULT):
    """皇极年的 13 个月界（12 月首 + 年末），本地时间；返回 (bounds, order)。"""
    if cfg.month_boundary == "zhongqi":
        names = astro.ZHONGQI
    elif cfg.month_boundary == "jieqi":
        names = astro.JIEQI_MONTH_START
    else:
        raise ValueError(cfg.month_boundary)
    if cfg.year_start == "dongzhi":
        bounds = [_term(cfg, hj_year - 1, names[0])] + [_term(cfg, hj_year, n) for n in names[1:]]
        bounds.append(_term(cfg, hj_year, names[0]))
        order = list(range(12))
    elif cfg.year_start == "lichun":
        seq = names[2:] + names[:2]
        bounds = ([_term(cfg, hj_year, n) for n in seq[:10]]
                  + [_term(cfg, hj_year, seq[10]), _term(cfg, hj_year + 1, seq[11])])
        bounds.append(_term(cfg, hj_year + 1, names[2]))
        order = list(range(2, 12)) + [0, 1]
    else:
        raise ValueError(cfg.year_start)
    for i in range(12):
        assert bounds[i] < bounds[i + 1], "月界次序错误"
    return bounds, order


def _day_label(dt: datetime, cfg: Config) -> date:
    if cfg.day_start_hour == 23:
        return (dt + timedelta(hours=1)).date()
    return dt.date()


def locate(dt: datetime, cfg: Config = DEFAULT) -> dict:
    """任一时刻 → 皇极年 / 月(子=1…亥=12) / 两月块 / 日序 / 时辰 / 长分。"""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=_tz(cfg))
    dt = dt.astimezone(_tz(cfg))
    for cand in (dt.year + 1, dt.year, dt.year - 1):
        bounds, order = month_boundaries(cand, cfg)
        if bounds[0] <= dt < bounds[12]:
            hj_year = cand
            break
    else:
        raise AssertionError("无法定位皇极年")
    k = max(i for i in range(12) if bounds[i] <= dt)
    month = order[k] + 1
    pair = (month - 1) // 2
    k_pair_start = k if order[k] % 2 == 0 else k - 1
    block_start = bounds[k_pair_start]
    day_idx = (_day_label(dt, cfg) - _day_label(block_start, cfg)).days
    hour_idx = ((dt.hour + 1) // 2) % 12
    pair_start_hour = (hour_idx // 2) * 4 - 1
    day_label = _day_label(dt, cfg)
    pair_start = datetime.combine(day_label, datetime.min.time(), tzinfo=_tz(cfg)) + timedelta(hours=pair_start_hour)
    if cfg.day_start_hour == 0 and dt.hour == 23:
        pair_start = datetime.combine(day_label, datetime.min.time(), tzinfo=_tz(cfg)) + timedelta(hours=23)
    fen_idx = int((dt - pair_start).total_seconds() // 240) % 60
    return {
        "dt": dt, "hj_year": hj_year, "month": month, "month_branch": BRANCHES[month - 1],
        "month_ord": k + 1,                 # 月在岁首年内的序位(1=岁首首月…12)；冬至岁首时==地支序
        "month_start": bounds[k], "pair": pair, "block_start": block_start,
        "day_idx": day_idx, "day_label": day_label,
        "hour_idx": hour_idx, "hour_branch": BRANCHES[hour_idx], "fen_idx": fen_idx,
    }


# ------------------------------------------------------------------ 推卦（递推法）
def nian_gua_of(hj_year: int) -> int:
    return core.nian_gua(_astro(hj_year)).value


def yue_gua(nian: int, month_ord: int) -> int:
    """月卦 = 年卦第 ((序位-1)//2+1) 爻变，每爻变管两月。

    爻位锚定岁首：month_ord 是月在岁首年内的序位(1=岁首首月)，岁首首月=初爻变。
    冬至岁首时序位==地支序(子=1)，与"子丑初爻…戌亥上爻"一致；立春岁首时寅月(序位1)=初爻变。
    """
    return flip_line(nian, (month_ord - 1) // 2 + 1)


def ri_gua(yue: int, day_idx: int, pair: int = 0, cfg: Config = DEFAULT) -> int:
    """日卦：自两月块首日起，以月卦为首（四正卦取其后一卦）循六十卦逐日。"""
    if day_idx >= 60:
        if cfg.day_overflow == "leap":
            return SEASON_RUN_GUA[(2 * pair) // 3]
        day_idx %= 60
    return SIXTY[(cycle_start_index(yue) + day_idx) % 60]


def shi_gua(ri: int, hour_idx: int) -> int:
    """时卦 = 日卦第 (时辰//2+1) 爻变；子丑初爻…戌亥上爻。"""
    return flip_line(ri, hour_idx // 2 + 1)


def fen_gua(shi: int, fen_idx: int) -> int:
    """分卦（可选）：两时辰 60 长分，自时卦（四正卦取其后一卦）循六十卦每 4 分钟。"""
    return SIXTY[(cycle_start_index(shi) + fen_idx) % 60]


def xun_gua(hj_year: int) -> int:
    """旬卦(十年卦) = 甲子世卦第 (甲子内第几年//10+1) 爻变。"""
    y = _astro(hj_year)
    pos = core.locate(y)
    shi = pos["shi"]
    first = shi if (shi - 1) % 2 == 0 else shi - 1
    offset = y - (core.YUAN_START + (first - 1) * 30)
    return flip_line(core.shi_gua(first).value, offset // 10 + 1)


# ------------------------------------------------------------------ year_restart 日法（app 兼容）
def _year_start_dt(hj_year: int, cfg: Config) -> datetime:
    """皇极年的岁首时刻（本地）。lichun 岁首时即该年立春。"""
    bounds, _ = month_boundaries(hj_year, cfg)
    return bounds[0]


def year_restart_start_gua(hj_year: int, cfg: Config = DEFAULT) -> int:
    """year_restart 的岁首起始卦：世卦在六十卦圆图退 16 位；岁首交节早于 05:00 则顺延一位。"""
    shi_val = core.shi_gua(core.locate(_astro(hj_year))["shi"]).value
    i = (SIXTY.index(shi_val) - YEAR_RESTART_SHI_RETREAT) % 60
    if _year_start_dt(hj_year, cfg).hour < YEAR_RESTART_CUTOFF_HOUR:
        i = (i + 1) % 60
    return SIXTY[i]


def ri_gua_year_restart(dt: datetime, hj_year: int, cfg: Config = DEFAULT) -> int:
    """year_restart 日卦：自岁首民用日起按六十卦圆图逐日，年内连续、跨年重起（不看时刻）。"""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=_tz(cfg))
    dt = dt.astimezone(_tz(cfg))
    n = (dt.date() - _year_start_dt(hj_year, cfg).date()).days
    start = year_restart_start_gua(hj_year, cfg)
    return SIXTY[(SIXTY.index(start) + n) % 60]


def full(dt: datetime, cfg: Config = DEFAULT) -> dict:
    """任一时刻的全部配卦（含上层元会运世年）。卦同时给 code 与简体名。"""
    p = locate(dt, cfg)
    y = _astro(p["hj_year"])
    pos = core.locate(y)
    ng = core.nian_gua(y).value
    yg = yue_gua(ng, p["month_ord"])        # 爻位锚定岁首
    if cfg.day_rule == "year_restart":
        rg = ri_gua_year_restart(dt, p["hj_year"], cfg)
    else:
        rg = ri_gua(yg, p["day_idx"], p["pair"], cfg)
    sg = shi_gua(rg, p["hour_idx"])
    fg = fen_gua(sg, p["fen_idx"])
    xg = xun_gua(p["hj_year"])
    p.update({
        "yun_gua": NAMES[core.yun_gua(pos["yun"]).value],
        "shi_gua_": NAMES[core.shi_gua(pos["shi"]).value],
        "xun_gua": NAMES[xg],
        "nian_gua": NAMES[ng], "yue_gua": NAMES[yg], "ri_gua": NAMES[rg],
        "shi_gua": NAMES[sg], "fen_gua": NAMES[fg],
        "nian_gua_code": ng, "yue_gua_code": yg, "ri_gua_code": rg,
        "shi_gua_code": sg, "fen_gua_code": fg, "xun_gua_code": xg,
    })
    return p


# ------------------------------------------------------------------ 备选：卦气定表法（方法 A）
def month_gua_A(month: int) -> int:
    """月卦(定表法) = 十二辟卦按月支。"""
    return core._HUI_PI[month - 1]


def day_gua_A(day_of_year: int) -> int:
    """日卦(定表法)：一年 360 日如一元 360 运，六十正卦每卦六日依次六爻变；自冬至起。"""
    d = (day_of_year - 1) % 360
    return flip_line(SIXTY[d // 6], d % 6 + 1)


def hour_gua_A(day_gua: int, hour_idx: int) -> int:
    return flip_line(day_gua, hour_idx // 2 + 1)
