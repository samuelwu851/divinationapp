"""core —— 皇极经世推卦（依王植《皇极经世书解》四库全书本）。

    元(129600年) ─12→ 会(10800) ─30→ 运(360) ─12→ 世(30) ─30→ 年

  会卦 = 十二辟卦（消息卦，子会起）。
  运卦 = 六十正卦（先天圆图去乾坤坎离）逐爻变，每正卦管 6 运。
  世卦 = 运卦逐爻变，每爻变管两世（= 一甲子 60 年）。
  十年卦 = 世卦的三爻变（一世 30 年分三旬，各 10 年一卦）。
  年卦 = 甲子内以世卦为首，沿六十正卦圆图逐年轮转，跳过四正卦。

卦用 iching.Hexagram（伏羲先天数 = 其 value：初爻最高位，坤0…乾63），
爻变复用 iching.core.flip。年份用天文纪年（公元1年=1，公元前1年=0，公元前N年=1−N）。
"""
from divination.iching.core import flip
from divination.iching.model import Hexagram

YEARS_PER_SHI = 30
SHI_PER_YUN = 12
YUN_PER_HUI = 30
YEARS_PER_YUAN = 129600

# 元首年（天文纪年）：由世2157(申)首年甲子 = 公元前2337年(-2336) 上推。
# → 元首年 = 公元前67017年(-67016)，本元终于公元62583年。
YUAN_START = -2336 - (2157 - 1) * YEARS_PER_SHI   # == -67016

STEMS = "甲乙丙丁戊己庚辛壬癸"
BRANCHES = "子丑寅卯辰巳午未申酉戌亥"

# 十二辟卦（消息卦）= 会卦，子会起（伏羲先天数）：
# 复 临 泰 大壮 夬 乾 姤 遁 否 观 剥 坤
_HUI_PI = (32, 48, 56, 60, 62, 63, 31, 15, 7, 3, 1, 0)

# 先天圆图左旋（自复起）去四正卦(乾63 坤0 坎18 离45) = 六十正卦，首复末剥。
_SIXTY = [h for h in (list(range(32, 64)) + list(range(31, -1, -1)))
          if h not in (0, 63, 18, 45)]

# 年卦轮转时，世卦若为四正卦（闰卦），取圆环上的下一卦（避开正卦）。
_PRINCIPAL_NEXT = {0: 32, 18: 17, 45: 46, 63: 31}

# 四象/季值卦：4 监司正卦，各镇一季(32400年)，离乾坎坤为序。
# 注意：这 4 卦是"监司/闰卦"，与生成运/世的"六十正卦"(_SIXTY) 是两回事。
_SEASON = (45, 63, 18, 0)   # 离 乾 坎 坤

# 24 节气名，从冬至起（元首年即冬至）。借日历节气之名，表 5400 年的宇宙节气，
# 与某一年的日历节气是两回事。
_JIEQI_NAMES = (
    "冬至", "小寒", "大寒", "立春", "雨水", "惊蛰",
    "春分", "清明", "谷雨", "立夏", "小满", "芒种",
    "夏至", "小暑", "大暑", "立秋", "处暑", "白露",
    "秋分", "寒露", "霜降", "立冬", "小雪", "大雪",
)


def ganzhi(year: int) -> str:
    """天文纪年 → 干支（公元4年=甲子）。"""
    i = (year - 4) % 60
    return STEMS[i % 10] + BRANCHES[i % 12]


def locate(year: int) -> dict:
    """年 → 元会运世坐标（本元内，序号从 1 起，附干支标号）。"""
    n = year - YUAN_START
    if not 0 <= n < YEARS_PER_YUAN:
        raise ValueError(f"超出本元范围（公元前67017 – 公元62583）：{year}")
    shi = n // YEARS_PER_SHI + 1              # 1..4320
    yun = (shi - 1) // SHI_PER_YUN + 1        # 1..360
    hui = (yun - 1) // YUN_PER_HUI + 1        # 1..12
    return {
        "hui": hui,
        "hui_branch": BRANCHES[hui - 1],
        "yun": yun,
        "yun_in_hui": (yun - 1) % YUN_PER_HUI + 1,
        "yun_stem": STEMS[(yun - 1) % 10],
        "shi": shi,
        "shi_branch": BRANCHES[(shi - 1) % 12],
        "year_in_shi": n % YEARS_PER_SHI + 1,
    }


def hui_gua(year: int) -> Hexagram:
    """会卦 = 该会的辟卦（十二消息卦）。直接查表，不从运卦推。"""
    return Hexagram(_HUI_PI[locate(year)["hui"] - 1])


def season_hexagram(year: int) -> Hexagram:
    """季值卦（四象/监司正卦）：离乾坎坤各镇一季(32400年)。"""
    return Hexagram(_SEASON[(year - YUAN_START) // 32400])


def jieqi_hexagram(year: int) -> tuple[Hexagram, str]:
    """节气卦 = 季正卦翻第 k 爻（D-1..D-6，5400年一节气），连同节气名。"""
    n = year - YUAN_START
    season = Hexagram(_SEASON[n // 32400])
    line = (n // 5400) % 6 + 1          # 1..6 → D-1..D-6（初爻..上爻）
    return flip(season, line), _JIEQI_NAMES[n // 5400]


def yun_gua(yun: int) -> Hexagram:
    """运卦：运序号 1..360。正卦逐爻变，每正卦管 6 运。"""
    zheng = _SIXTY[(yun - 1) // 6]
    return flip(Hexagram(zheng), (yun - 1) % 6 + 1)


def shi_gua(shi: int) -> Hexagram:
    """世卦：世序号 1..4320。运卦逐爻变，每爻变管两世（一甲子）。"""
    yun = (shi - 1) // SHI_PER_YUN + 1
    k = (shi - 1) % SHI_PER_YUN              # 本运内第 0..11 世
    return flip(yun_gua(yun), k // 2 + 1)


def shi_gua_decades(shi: int) -> list[tuple[int, Hexagram]]:
    """十年卦：世卦的三爻变（一世30年分三旬）。
    本运内奇数位世（全元奇数世）取初二三变，偶数位取四五上变。
    返回 [(爻位, 卦), (爻位, 卦), (爻位, 卦)]，依旬次序。
    """
    k = (shi - 1) % SHI_PER_YUN
    g = shi_gua(shi)
    lines = (1, 2, 3) if k % 2 == 0 else (4, 5, 6)
    return [(line, flip(g, line)) for line in lines]


def nian_gua(year: int) -> Hexagram:
    """年卦：甲子(60年)内以世卦为首，沿六十正卦圆图逐年轮转，跳过四正卦。"""
    pos = locate(year)
    shi = pos["shi"]
    first = shi if (shi - 1) % 2 == 0 else shi - 1       # 该甲子首世（全元奇数世）
    base = shi_gua(first).value
    base = _PRINCIPAL_NEXT.get(base, base)               # 世卦若为正卦，取环上下一卦
    offset = year - (YUAN_START + (first - 1) * YEARS_PER_SHI)   # 甲子内第 0..59 年
    return Hexagram(_SIXTY[(_SIXTY.index(base) + offset) % 60])


def decade_gua(year: int) -> Hexagram:
    """十年卦：该年所在旬（世内第几个10年）的卦。"""
    pos = locate(year)
    decade = (pos["year_in_shi"] - 1) // 10              # 0, 1, 2
    return shi_gua_decades(pos["shi"])[decade][1]
