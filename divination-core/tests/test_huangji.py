"""皇极经世 元会运世 推卦 —— 测试（适配本项目 huangji.core）。

数据来源：
  * 《皇极经世书解》(清·王植) 卷一~卷三原表片段（test_wangzhi_*）。
  * 《邵雍皇极经世129600年配卦表》(马振国, 曾华才, 2020) 的关键年份 / Table 8~11。
  * 全量 129,600 行 CSV（huangji_129600_table.csv）—— 缺省时 test_full_sweep 跳过。

被测实现：divination.huangji.core。下面的小写包装把 core 暴露成测试要的接口
（core.yun_gua/shi_gua/nian_gua/locate/ganzhi 直接复用；会/四象/节气/当值用 core 常量派生）。
"""
import csv
from pathlib import Path

import pytest

from divination.huangji import core

# 伏羲先天数 → 简体卦名（= core 里 Hexagram.value 的编码；仅用于可读断言）
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
N = lambda hs: [NAMES[h] for h in hs]

SIXTY = core._SIXTY
TERM_NAMES = core._JIEQI_NAMES
YUAN_START = core.YUAN_START


# ----- core 的薄包装：返回 int 卦号，便于用 NAMES 做可读断言 -----
def flip_line(h, line):
    return h ^ (1 << (6 - line))


def six_changes(h):
    return [flip_line(h, k) for k in range(1, 7)]


def gregorian_to_astro(g):
    """历史纪年(无0年) → 天文纪年。"""
    return g + 1 if g < 0 else g


def ganzhi(astro_year):
    return core.ganzhi(astro_year)


def position(astro_year):
    return core.locate(astro_year)


def yun_gua(yun):
    return core.yun_gua(yun).value


def shi_gua(shi):
    return core.shi_gua(shi).value


def nian_gua(astro_year):
    return core.nian_gua(astro_year).value


def shi_gua_three_changes(shi):
    return [(line, g.value) for line, g in core.shi_gua_decades(shi)]


def hui_gua(hui):                       # 会卦（辟卦），按会号 1..12
    return core._HUI_PI[hui - 1]


def emblem_gua(hui):                     # 四象/季正卦，按会号（每 3 会一象）
    return core._SEASON[(hui - 1) // 3]


def duty_gua(yun):                       # 当值卦（六十正卦），按运号（每 6 运一正卦）
    return SIXTY[(yun - 1) // 6]


def term_index(yun):                     # 节气序号 0..23（每 15 运一节气）
    return (yun - 1) // 15


def term_gua(yun):                       # 节气卦 = 季正卦翻爻
    return flip_line(core._SEASON[(yun - 1) // 90], term_index(yun) % 6 + 1)


def cycle_start_index(h):                # 年卦轮转起点在 SIXTY 中的下标（正卦取其后一卦）
    return SIXTY.index(core._PRINCIPAL_NEXT.get(h, h))


def full(astro_year):
    p = position(astro_year)
    return {
        "hui": p["hui"], "yun": p["yun"], "shi": p["shi"],
        "yun_gua": NAMES[yun_gua(p["yun"])],
        "shi_gua": NAMES[shi_gua(p["shi"])],
        "nian_gua": NAMES[nian_gua(astro_year)],
    }


# ================================================================ 王植《皇极经世书解》原表片段
@pytest.mark.parametrize("hexagram,expected", [
    ("复", ["坤", "临", "明夷", "震", "屯", "颐"]),        # 805-293
    ("姤", ["乾", "遁", "讼", "巽", "鼎", "大过"]),
    ("鼎", ["大有", "旅", "未济", "蛊", "姤", "恒"]),       # 805-294
    ("乾", ["姤", "同人", "履", "小畜", "大有", "夬"]),     # 805-364
    ("大过", ["夬", "咸", "困", "井", "恒", "姤"]),         # 马书 Table 10
])
def test_wangzhi_six_changes(hexagram, expected):
    code = {v: k for k, v in NAMES.items()}[hexagram]
    assert N(six_changes(code)) == expected


def test_wangzhi_sixty_order():
    assert N(SIXTY) == [
        "复", "颐", "屯", "益", "震", "噬嗑", "随", "无妄", "明夷", "贲", "既济", "家人", "丰", "革", "同人",
        "临", "损", "节", "中孚", "归妹", "睽", "兑", "履", "泰", "大畜", "需", "小畜", "大壮", "大有", "夬",
        "姤", "大过", "鼎", "恒", "巽", "井", "蛊", "升", "讼", "困", "未济", "解", "涣", "蒙", "师",
        "遁", "咸", "旅", "小过", "渐", "蹇", "艮", "谦", "否", "萃", "晋", "豫", "观", "比", "剥"]


def test_wangzhi_yun_gua_juan1():
    assert N(map(yun_gua, range(1, 25))) == [
        "坤", "临", "明夷", "震", "屯", "颐", "剥", "损", "贲", "噬嗑", "益", "复",
        "比", "节", "既济", "随", "复", "益", "观", "中孚", "家人", "无妄", "颐", "屯"]
    assert N(map(yun_gua, range(121, 137))) == [
        "未济", "噬嗑", "大有", "损", "履", "归妹", "困", "随", "夬", "节", "归妹", "履", "讼", "无妄", "乾", "中孚"]
    assert N(map(yun_gua, (180, 181, 183, 185))) == ["乾", "乾", "讼", "鼎"]


def test_wangzhi_shi_gua_juan2():
    assert N(map(shi_gua, range(2161, 2173))) == ["姤", "姤", "同人", "同人", "履", "履",
                                                   "小畜", "小畜", "大有", "大有", "夬", "夬"]
    assert N(map(shi_gua, range(2185, 2191))) == ["履", "履", "否", "否", "姤", "姤"]
    assert N(map(shi_gua, range(2213, 2221))) == ["未济", "未济", "蛊", "蛊", "姤", "姤", "恒", "恒"]
    assert shi_gua_three_changes(2214) == [(4, 17), (5, 23), (6, 20)]   # 蒙 讼 解
    assert shi_gua_three_changes(2215) == [(1, 57), (2, 9), (3, 17)]    # 大畜 艮 蒙


def test_wangzhi_nian_gua_juan3():
    y0 = gregorian_to_astro(-2397)                       # 世 2155 首年 甲子
    assert ganzhi(y0) == "甲子" and position(y0)["shi"] == 2155
    assert [NAMES[nian_gua(y0 + i)] for i in range(60)] == [
        "小畜", "大壮", "大有", "夬", "姤", "大过", "鼎", "恒", "巽", "井",
        "蛊", "升", "讼", "困", "未济", "解", "涣", "蒙", "师", "遁",
        "咸", "旅", "小过", "渐", "蹇", "艮", "谦", "否", "萃", "晋",
        "豫", "观", "比", "剥", "复", "颐", "屯", "益", "震", "噬嗑",
        "随", "无妄", "明夷", "贲", "既济", "家人", "丰", "革", "同人", "临",
        "损", "节", "中孚", "归妹", "睽", "兑", "履", "泰", "大畜", "需"]
    assert [NAMES[nian_gua(y0 + 60 + 30 * k)] for k in range(6)] == ["大有", "比", "夬", "剥", "姤", "复"]


# ================================================================ 节气 / 结构不变量
def test_term_names_cover_24():
    assert len(TERM_NAMES) == 24 and TERM_NAMES[0] == "冬至" and TERM_NAMES[12] == "夏至"
    assert [term_index(y) for y in (1, 15, 16, 180, 181, 360)] == [0, 0, 1, 11, 12, 23]


def test_structural_invariants():
    # 奇数世首年甲子，偶数世首年甲午
    for shi in (1, 2, 2155, 2156, 4319, 4320):
        y = YUAN_START + (shi - 1) * 30
        assert ganzhi(y) == ("甲子" if shi % 2 else "甲午")
    # 运卦 = 当值卦的第((运-1)%6+1)爻变；世卦 = 运卦的第((世-1)%12//2+1)爻变
    for yun in (1, 7, 121, 187, 360):
        assert yun_gua(yun) == flip_line(duty_gua(yun), (yun - 1) % 6 + 1)
    for shi in (1, 2, 13, 2293, 4320):
        yun = (shi - 1) // 12 + 1
        assert shi_gua(shi) == flip_line(yun_gua(yun), (shi - 1) % 12 // 2 + 1)
    # 每甲子 60 年恰好轮遍 60 正卦；年卦永不为四正卦
    for start in (-67016, -2336, 1744, 844):
        names = [nian_gua(start + i) for i in range(60)]
        assert set(names) == set(SIXTY)
    # 四正卦作世卦时，年卦起点为圆图上其后第一个正卦
    assert [NAMES[SIXTY[cycle_start_index(h)]] for h in (63, 18, 45, 0)] == ["姤", "蒙", "革", "复"]


# ================================================================ 关键年份（对实现）
LANDMARKS = [
    (-67017, 1, 1, 1, "坤", "复", "复"),
    (-67016, 1, 1, 1, "坤", "复", "颐"),
    (-2357, 6, 180, 2156, "乾", "小畜", "随"),   # 唐尧元年甲辰
    (-2337, 6, 180, 2157, "乾", "大有", "大有"),
    (-2217, 7, 181, 2161, "乾", "姤", "姤"),     # 午会首年甲子
    (-613, 7, 185, 2214, "鼎", "未济", "大畜"),  # 楚庄王元年戊申
    (-1, 7, 187, 2234, "夬", "大过", "大壮"),
    (1, 7, 187, 2234, "夬", "大过", "大有"),
    (244, 7, 187, 2243, "夬", "乾", "姤"),       # 世卦为四正卦乾 → 年卦自姤起
    (844, 7, 189, 2263, "困", "坎", "蒙"),       # 世卦坎 → 年卦自蒙起
    (1744, 7, 192, 2293, "姤", "乾", "姤"),
    (1984, 7, 192, 2301, "姤", "鼎", "鼎"),
    (2019, 7, 192, 2302, "姤", "鼎", "无妄"),    # 马书正文 2019 = 无妄
    (2044, 7, 192, 2303, "姤", "大过", "大过"),
    (62583, 12, 360, 4320, "坤", "剥", "比"),    # 元之末年癸亥
]


@pytest.mark.parametrize("g,hui,yun,shi,yg,sg,ng", LANDMARKS, ids=[str(x[0]) for x in LANDMARKS])
def test_landmark_years(g, hui, yun, shi, yg, sg, ng):
    f = full(gregorian_to_astro(g))
    assert (f["hui"], f["yun"], f["shi"]) == (hui, yun, shi)
    assert (f["yun_gua"], f["shi_gua"], f["nian_gua"]) == (yg, sg, ng)


# ================================================================ 会/四象/节气/当值（马书 Table 8,9）
HUI_TABLE = [
    (1, "复", "离", ("旅", "大有"), ("复", "颐", "屯", "益", "震")),
    (2, "临", "离", ("噬嗑", "贲"), ("噬嗑", "随", "无妄", "明夷", "贲")),
    (3, "泰", "离", ("同人", "丰"), ("既济", "家人", "丰", "革", "同人")),
    (4, "大壮", "乾", ("姤", "同人"), ("临", "损", "节", "中孚", "归妹")),
    (5, "夬", "乾", ("履", "小畜"), ("睽", "兑", "履", "泰", "大畜")),
    (6, "乾", "乾", ("大有", "夬"), ("需", "小畜", "大壮", "大有", "夬")),
    (7, "姤", "坎", ("节", "比"), ("姤", "大过", "鼎", "恒", "巽")),
    (8, "遁", "坎", ("井", "困"), ("井", "蛊", "升", "讼", "困")),
    (9, "否", "坎", ("师", "涣"), ("未济", "解", "涣", "蒙", "师")),
    (10, "观", "坤", ("复", "师"), ("遁", "咸", "旅", "小过", "渐")),
    (11, "剥", "坤", ("谦", "豫"), ("蹇", "艮", "谦", "否", "萃")),
    (12, "坤", "坤", ("比", "剥"), ("晋", "豫", "观", "比", "剥")),
]


@pytest.mark.parametrize("hui,pi,emblem,terms,duties", HUI_TABLE, ids=[f"hui{x[0]}" for x in HUI_TABLE])
def test_hui_level_tables(hui, pi, emblem, terms, duties):
    assert NAMES[hui_gua(hui)] == pi
    assert NAMES[emblem_gua(hui)] == emblem
    yun0 = (hui - 1) * 30 + 1
    assert tuple(NAMES[term_gua(yun0 + 15 * k)] for k in range(2)) == terms
    assert tuple(NAMES[duty_gua(yun0 + 6 * k)] for k in range(5)) == duties


# ================================================================ 马书 Table 10（大过运 187-192）
DAGUO = {
    187: ("夬", [(-57, "大过", "大过"), (4, "革", "革"), (64, "兑", "兑"), (124, "需", "需"), (184, "大壮", "大壮"), (244, "乾", "姤")]),
    188: ("咸", [(304, "革", "革"), (364, "大过", "大过"), (424, "萃", "萃"), (484, "蹇", "蹇"), (544, "小过", "小过"), (604, "遁", "遁")]),
    189: ("困", [(664, "兑", "兑"), (724, "萃", "萃"), (784, "大过", "大过"), (844, "坎", "蒙"), (904, "解", "解"), (964, "讼", "讼")]),
    190: ("井", [(1024, "需", "需"), (1084, "蹇", "蹇"), (1144, "坎", "蒙"), (1204, "大过", "大过"), (1264, "升", "升"), (1324, "巽", "巽")]),
    191: ("恒", [(1384, "大壮", "大壮"), (1444, "小过", "小过"), (1504, "解", "解"), (1564, "升", "升"), (1624, "大过", "大过"), (1684, "鼎", "鼎")]),
    192: ("姤", [(1744, "乾", "姤"), (1804, "遁", "遁"), (1864, "讼", "讼"), (1924, "巽", "巽"), (1984, "鼎", "鼎"), (2044, "大过", "大过")]),
}


@pytest.mark.parametrize("yun", sorted(DAGUO), ids=[f"yun{y}" for y in DAGUO])
def test_table10_daguo(yun):
    yun_name, jiazi = DAGUO[yun]
    assert NAMES[duty_gua(yun)] == "大过"
    assert NAMES[yun_gua(yun)] == yun_name
    for g, shi_name, first_year_name in jiazi:
        y = gregorian_to_astro(g)
        assert ganzhi(y) == "甲子"
        assert NAMES[shi_gua(position(y)["shi"])] == shi_name
        assert NAMES[nian_gua(y)] == first_year_name


# ================================================================ 马书 Table 11（甲子鼎 1984-2043）
TABLE11 = {
    1984: "鼎", 1985: "恒", 1986: "巽", 1987: "井", 1988: "蛊", 1989: "升", 1990: "讼", 1991: "困", 1992: "未济", 1993: "解",
    1994: "涣", 1995: "蒙", 1996: "师", 1997: "遁", 1998: "咸", 1999: "旅", 2000: "小过", 2001: "渐", 2002: "蹇", 2003: "艮",
    2004: "谦", 2005: "否", 2006: "萃", 2007: "晋", 2008: "豫", 2009: "观", 2010: "比", 2011: "剥", 2012: "复", 2013: "颐",
    2014: "屯", 2015: "益", 2016: "震", 2017: "噬嗑", 2018: "随", 2019: "无妄", 2020: "明夷", 2021: "贲", 2022: "既济", 2023: "家人",
    2024: "丰", 2025: "革", 2026: "同人", 2027: "临", 2028: "损", 2029: "节", 2030: "中孚", 2031: "归妹", 2032: "睽", 2033: "兑",
    2034: "履", 2035: "泰", 2036: "大畜", 2037: "需", 2038: "小畜", 2039: "大壮", 2040: "大有", 2041: "夬", 2042: "姤", 2043: "大过",
}


def test_table11_annual_1984_2043():
    for g, name in TABLE11.items():
        assert NAMES[nian_gua(gregorian_to_astro(g))] == name, g


# ================================================================ 全量 129,600 行（有 CSV 才跑）
CSV_PATH = Path(__file__).with_name("huangji_129600_table.csv")


@pytest.mark.skipif(not CSV_PATH.exists(), reason="缺少 huangji_129600_table.csv")
def test_full_sweep_matches_table():
    """逐年比对我们实现的 四象/会/节气/当值/运/世/年 七列卦（元卦已按产品舍去）。"""
    mism = []
    with CSV_PATH.open(newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            y = gregorian_to_astro(int(r["gregorian"]))
            p = position(y)
            got = (
                emblem_gua(p["hui"]), hui_gua(p["hui"]), term_gua(p["yun"]),
                duty_gua(p["yun"]), yun_gua(p["yun"]), shi_gua(p["shi"]), nian_gua(y),
            )
            exp = tuple(int(r[c]) for c in
                        ("emblem_hex", "hui_hex", "term_hex", "duty_hex", "yun_hex", "shi_hex", "year_hex"))
            if got != exp:
                mism.append((r["gregorian"], exp, got))
                if len(mism) >= 20:
                    break
    assert not mism, f"前 {len(mism)} 处不一致 (公历年, 表, 实现):\n" + "\n".join(map(str, mism))
