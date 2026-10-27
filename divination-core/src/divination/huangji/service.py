"""service —— 皇极经世排盘的门面层。

给一个年份（天文纪年），返回干支、元会运世定位、以及各层配卦：
  会卦(辟卦) → 运卦 → 世卦 → 十年卦 → 年卦。
每个卦只回 value + 卦名；要卦辞/爻辞/错综互，平台层拿 value 调 iching 的 lookup。
返回纯 JSON 可序列化的数据，不把内部类型漏给平台层。
"""
import json
from dataclasses import replace
from datetime import datetime

from divination.ganzhi import repository as ganzhi_repo
from divination.huangji import core, subyear
from divination.iching import repository as iching_repo
from divination.iching.model import Hexagram

# ==================================================================
# 排盘历法：岁首(3种) × 日卦起法(2种) = 6 种，按前端每次请求选择。
#
# 岁首与分月是绑定的——前端只选岁首，内部映射到 (year_start, month_boundary)：
#   大雪 daxue   : 子月起、节分月    (dongzhi + jieqi)
#   冬至 dongzhi : 子月起、中气分月  (dongzhi + zhongqi)  —— 皇极正统
#   立春 lichun  : 寅月起、节分月    (lichun  + jieqi)    —— 命理习惯
# 日卦起法：
#   月卦起 yuegua : 全息法(从月卦起、两月块)  = nested（我们之前的）
#   世卦起 shigua : app 法(岁首起、年内连续)  = year_restart（新加的）
#
# 时区、日界(23:00)、两月溢出规则等基础项由 BASE_CONFIG 给；岁首/日卦每次覆盖。
# ==================================================================
BASE_CONFIG = subyear.Config()

_YEAR_START = {                       # 前端岁首 → (内部 year_start, month_boundary)
    "daxue":   ("dongzhi", "jieqi"),
    "dongzhi": ("dongzhi", "zhongqi"),
    "lichun":  ("lichun",  "jieqi"),
}
_DAY_RULE = {                         # 前端日卦起法 → 内部 day_rule（兼收内部名）
    "yuegua": "nested",       "nested": "nested",
    "shigua": "year_restart", "year_restart": "year_restart",
}
DEFAULT_YEAR_START = "lichun"
DEFAULT_DAY_RULE = "yuegua"


def build_config(year_start: str = DEFAULT_YEAR_START, day_rule: str = DEFAULT_DAY_RULE) -> subyear.Config:
    """前端岁首(大雪/冬至/立春) + 日卦起法(月卦起/世卦起) → subyear.Config。"""
    if year_start not in _YEAR_START:
        raise ValueError(f"unknown year_start: {year_start!r}（可选 daxue/dongzhi/lichun）")
    if day_rule not in _DAY_RULE:
        raise ValueError(f"unknown day_rule: {day_rule!r}（可选 yuegua/shigua）")
    ys, mb = _YEAR_START[year_start]
    return replace(BASE_CONFIG, year_start=ys, month_boundary=mb, day_rule=_DAY_RULE[day_rule])


DEFAULT_CONFIG = build_config()       # 默认：立春 + 月卦起


def _pack(hexagram: Hexagram) -> dict:
    """把一个卦打包成 value + 卦名。"""
    return {"value": hexagram.value, "name": iching_repo.name_of(hexagram)}


def _pack_code(code: int) -> dict:
    """subyear 层给的是卦 code(=Hexagram.value)，统一打包成 value + 卦名。"""
    return _pack(Hexagram(code))


def paipan(year: int) -> dict:
    """年 → 干支 + 元会运世定位 + 各层配卦（排盘）。"""
    pos = core.locate(year)
    jieqi, term = core.jieqi_hexagram(year)
    return {
        "year": year,
        "ganzhi": core.ganzhi(year),
        "season": _pack(core.season_hexagram(year)),   # 季值卦(四象/监司正卦)
        "hui": {
            "index": pos["hui"], "branch": pos["hui_branch"],
            **_pack(core.hui_gua(year)),
        },
        "jieqi": {**_pack(jieqi), "term": term},        # 节气卦 + 节气名

        "yun": {
            "index": pos["yun"], "in_hui": pos["yun_in_hui"], "stem": pos["yun_stem"],
            **_pack(core.yun_gua(pos["yun"])),
        },
        "shi": {
            "index": pos["shi"], "branch": pos["shi_branch"],
            **_pack(core.shi_gua(pos["shi"])),
        },
        "decade": _pack(core.decade_gua(year)),     # 十年卦
        "annual": _pack(core.nian_gua(year)),       # 年卦
    }


def paipan_json(year: int) -> str:
    """平台层边界：皇极年(天文纪年)进，JSON 串出。"""
    return json.dumps(paipan(year), ensure_ascii=False)


def paipan_from_date(
    year: int, month: int, day: int, hour: int = 0, minute: int = 0,
    is_lunar: bool = False, is_leap: bool = False, year_start: str = DEFAULT_YEAR_START,
) -> dict:
    """前端日期(公历或农历的 年月日时) → 排盘。岁首由 year_start 选(大雪/冬至/立春)。

    农历先转公历；再按岁首定皇极年。会/运/世/十年/年只由"年"决定，月日时仅用于判断岁首前后。
    农历闰月：is_leap=True（month 仍填 1-12，内部转 lunar_python 的负数月）。
    """
    if is_lunar:
        lunar_month = -month if is_leap else month
        moment = ganzhi_repo.lunar_to_solar(year, lunar_month, day, hour, minute)
    else:
        moment = datetime(year, month, day, hour, minute)

    cfg = build_config(year_start)                               # 年层只看岁首
    hj_year = subyear.locate(moment, cfg)["hj_year"]             # 按岁首定皇极年(历史纪年)
    result = paipan(subyear._astro(hj_year))                     # → 天文纪年
    result["input_solar"] = moment.strftime("%Y-%m-%d %H:%M")  # 实际用的公历时刻
    return result


def paipan_from_date_json(
    year: int, month: int, day: int, hour: int = 0, minute: int = 0,
    is_lunar: bool = False, is_leap: bool = False, year_start: str = DEFAULT_YEAR_START,
) -> str:
    """平台层边界：前端日期进，JSON 串出。"""
    return json.dumps(
        paipan_from_date(year, month, day, hour, minute, is_lunar, is_leap, year_start),
        ensure_ascii=False,
    )


# ------------------------------------------------------------------ 全链：元会运世年·月日时分
def paipan_full(dt: datetime, cfg: subyear.Config = None) -> dict:
    """任一公历时刻 → 完整配卦链：会 运 世 十年 年 月 日 时 分。

    岁首与月/日/时界由 cfg 决定（默认 DEFAULT_CONFIG = 立春 + 月卦起、日界 23:00），
    上层(会/运/世/十年/年)由 subyear 定出的皇极年驱动，故整链自洽。
    每卦只回 value + 卦名（繁体，数据用繁）；时/分支用地支标号。
    """
    if cfg is None:
        cfg = DEFAULT_CONFIG
    f = subyear.full(dt, cfg)
    year = subyear._astro(f["hj_year"])          # 皇极年(历史纪年) → 天文纪年
    pos = core.locate(year)
    jieqi, term = core.jieqi_hexagram(year)
    return {
        "hj_year": f["hj_year"],
        "year": year,
        "ganzhi": core.ganzhi(year),
        "input_solar": f["dt"].strftime("%Y-%m-%d %H:%M"),
        "season": _pack(core.season_hexagram(year)),
        "hui": {"index": pos["hui"], "branch": pos["hui_branch"], **_pack(core.hui_gua(year))},
        "jieqi": {**_pack(jieqi), "term": term},
        "yun": {
            "index": pos["yun"], "in_hui": pos["yun_in_hui"], "stem": pos["yun_stem"],
            **_pack(core.yun_gua(pos["yun"])),
        },
        "shi": {"index": pos["shi"], "branch": pos["shi_branch"], **_pack(core.shi_gua(pos["shi"]))},
        "decade": _pack(core.decade_gua(year)),      # 十年卦(= subyear 旬卦)
        "annual": _pack(core.nian_gua(year)),        # 年卦
        # —— 年以下 ——
        "month": {"index": f["month"], "branch": f["month_branch"], **_pack_code(f["yue_gua_code"])},
        "day": {"index": f["day_idx"] + 1, **_pack_code(f["ri_gua_code"])},
        "hour": {"index": f["hour_idx"], "branch": f["hour_branch"], **_pack_code(f["shi_gua_code"])},
        "fen": {"index": f["fen_idx"] + 1, **_pack_code(f["fen_gua_code"])},
    }


def paipan_full_from_date(
    year: int, month: int, day: int, hour: int = 0, minute: int = 0,
    is_lunar: bool = False, is_leap: bool = False,
    year_start: str = DEFAULT_YEAR_START, day_rule: str = DEFAULT_DAY_RULE,
) -> dict:
    """前端日期(公历或农历的 年月日时分) → 完整配卦链。

    农历先转公历（闰月 is_leap=True，month 仍填 1-12）。
    year_start 选岁首：大雪 daxue / 冬至 dongzhi / 立春 lichun。
    day_rule 选日卦起法：月卦起 yuegua / 世卦起 shigua。（共 6 种组合）
    """
    if is_lunar:
        lunar_month = -month if is_leap else month
        moment = ganzhi_repo.lunar_to_solar(year, lunar_month, day, hour, minute)
    else:
        moment = datetime(year, month, day, hour, minute)
    cfg = build_config(year_start, day_rule)
    return paipan_full(moment, cfg)


def paipan_full_from_date_json(
    year: int, month: int, day: int, hour: int = 0, minute: int = 0,
    is_lunar: bool = False, is_leap: bool = False,
    year_start: str = DEFAULT_YEAR_START, day_rule: str = DEFAULT_DAY_RULE,
) -> str:
    """平台层边界：前端日期进，完整链 JSON 串出。"""
    return json.dumps(
        paipan_full_from_date(year, month, day, hour, minute, is_lunar, is_leap, year_start, day_rule),
        ensure_ascii=False,
    )
