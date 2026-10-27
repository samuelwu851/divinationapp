"""皇极经世 月·日·时·分 推卦 —— 测试（适配本项目 huangji.subyear / huangji.astro）。

数据来源：
  * 香港天文台 2025 / 2026 中气时刻表（校验节气算法）
  * 网传实例：2020 年卦明夷 → 月卦 谦泰复丰既济贲（燚燚）；2022 年卦既济 → 月卦 蹇需屯革明夷家人（知乎）
  * 其余为结构性不变量（由 运→世→年 规则递推，见《皇极经世-月日时推卦方法.md》）
"""
from datetime import datetime, timedelta

import pytest

from divination.huangji import astro, subyear as s
from divination.huangji.subyear import NAMES, SIXTY, FOUR_CARDINAL

CODE = {v: k for k, v in NAMES.items()}
N = lambda hs: [NAMES[h] for h in hs]
six_changes = lambda h: [s.flip_line(h, k) for k in range(1, 7)]
D = datetime.fromisoformat

# ---------------------------------------------------------------- 节气（对照香港天文台，UTC+8）
HKO = {
    2025: {"大寒": "01-20 04:00", "雨水": "02-18 18:07", "春分": "03-20 17:01", "谷雨": "04-20 03:56", "小满": "05-21 02:55",
           "夏至": "06-21 10:42", "大暑": "07-22 21:29", "处暑": "08-23 04:34", "秋分": "09-23 02:19", "霜降": "10-23 11:51",
           "小雪": "11-22 09:36", "冬至": "12-21 23:03"},
    2026: {"大寒": "01-20 09:45", "雨水": "02-18 23:52", "春分": "03-20 22:46", "谷雨": "04-20 09:39", "小满": "05-21 08:37",
           "夏至": "06-21 16:25", "大暑": "07-23 03:13", "处暑": "08-23 10:19", "秋分": "09-23 08:05", "霜降": "10-23 17:38",
           "小雪": "11-22 15:23", "冬至": "12-22 04:50"},
}


@pytest.mark.parametrize("year,name,hhmm", [(y, n, t) for y, d in HKO.items() for n, t in d.items()],
                         ids=[f"{y}{n}" for y, d in HKO.items() for n in d])
def test_solar_terms_match_hko_within_2_minutes(year, name, hhmm):
    exp = datetime.strptime(f"{year}-{hhmm}", "%Y-%m-%d %H:%M")
    got = astro.solar_term_local(year, name).replace(tzinfo=None)
    assert abs((got - exp).total_seconds()) <= 120, (name, exp, got)


def test_jieqi_longitudes():
    assert astro.JIEQI_LON["立春"] == 315 and astro.JIEQI_LON["冬至"] == 270
    assert astro.JIEQI_LON["春分"] == 0 and astro.JIEQI_LON["大寒"] == 300
    assert astro.ZHONGQI[0] == "冬至" and len(astro.ZHONGQI) == 12


# ---------------------------------------------------------------- 年 / 月 / 日 / 时 定位
def test_month_boundaries_2026():
    b, order = s.month_boundaries(2026)
    assert order == list(range(12))
    assert abs((b[0].replace(tzinfo=None) - D("2025-12-21T23:03")).total_seconds()) < 120
    assert abs((b[10].replace(tzinfo=None) - D("2026-10-23T17:38")).total_seconds()) < 120
    assert abs((b[12].replace(tzinfo=None) - D("2026-12-22T04:50")).total_seconds()) < 120
    assert [(b[i + 2] - b[i]).days for i in range(0, 12, 2)] == [59, 60, 62, 62, 61, 59]


@pytest.mark.parametrize("iso,hj_year,month,day_idx,hour_idx", [
    ("2026-10-26T10:00", 2026, 11, 3, 5),
    ("2026-10-26T02:00", 2026, 11, 3, 1),
    ("2026-10-23T17:00", 2026, 10, 61, 9),
    ("2026-10-23T18:00", 2026, 11, 0, 9),
    ("2026-01-20T09:00", 2026, 1, 29, 5),
    ("2026-01-20T10:00", 2026, 2, 29, 5),
    ("2026-12-22T03:00", 2026, 12, 60, 2),
    ("2026-12-22T05:00", 2027, 1, 0, 3),
    ("2019-12-22T13:00", 2020, 1, 0, 7),
])
def test_locate(iso, hj_year, month, day_idx, hour_idx):
    p = s.locate(D(iso))
    assert (p["hj_year"], p["month"], p["day_idx"], p["hour_idx"]) == (hj_year, month, day_idx, hour_idx)


def test_day_boundary_at_23():
    a, b = s.locate(D("2026-10-25T22:30")), s.locate(D("2026-10-25T23:30"))
    assert b["day_idx"] == a["day_idx"] + 1 and b["hour_idx"] == 0 and a["hour_idx"] == 11
    cfg = s.Config(day_start_hour=0)
    a, b = s.locate(D("2026-10-25T22:30"), cfg), s.locate(D("2026-10-25T23:30"), cfg)
    assert b["day_idx"] == a["day_idx"] and b["hour_idx"] == 0


def test_hour_index_mapping():
    hours = {0: 0, 1: 1, 2: 1, 3: 2, 4: 2, 5: 3, 6: 3, 7: 4, 8: 4, 9: 5, 10: 5, 11: 6, 12: 6, 13: 7, 14: 7, 15: 8, 16: 8,
             17: 9, 18: 9, 19: 10, 20: 10, 21: 11, 22: 11, 23: 0}
    for h, idx in hours.items():
        assert s.locate(D(f"2026-10-26T{h:02d}:30"))["hour_idx"] == idx, h


# ---------------------------------------------------------------- 月卦（外部实例 + 结构）
@pytest.mark.parametrize("year,nian,months", [
    (2020, "明夷", ["谦", "泰", "复", "丰", "既济", "贲"]),
    (2022, "既济", ["蹇", "需", "屯", "革", "明夷", "家人"]),
    (2026, "同人", ["遁", "乾", "无妄", "家人", "离", "革"]),
    (2027, "临", ["师", "复", "泰", "归妹", "节", "损"]),
])
def test_yue_gua_examples(year, nian, months):
    ng = s.nian_gua_of(year)
    assert NAMES[ng] == nian
    assert N(s.yue_gua(ng, m) for m in range(1, 13)) == [x for x in months for _ in (0, 1)]


def test_yue_gua_is_six_changes_of_nian_gua():
    for year in range(1900, 2100):
        ng = s.nian_gua_of(year)
        assert [s.yue_gua(ng, m) for m in (1, 3, 5, 7, 9, 11)] == six_changes(ng)
        for m in range(1, 13):
            assert s.yue_gua(ng, m) == s.yue_gua(ng, m + 1 if m % 2 else m - 1)


def test_xun_gua():
    assert NAMES[s.xun_gua(2020)] == "蛊"
    assert [NAMES[s.xun_gua(y)] for y in (1984, 1994, 2004, 2014, 2024, 2034)] == ["大有", "旅", "未济", "蛊", "姤", "恒"]


# ---------------------------------------------------------------- 日卦
def test_ri_gua_cycle_from_yue_gua():
    ge = CODE["革"]
    assert N(s.ri_gua(ge, i) for i in range(4)) == ["革", "同人", "临", "损"]
    assert N(s.ri_gua(CODE[g], 0) for g in ("乾", "坎", "离", "坤")) == ["姤", "蒙", "革", "复"]
    assert NAMES[s.ri_gua(ge, 59)] == "丰"            # 革起，第60日=环上革的前一卦
    assert NAMES[s.ri_gua(CODE["乾"], 59)] == "夬"     # 乾(正卦)起于姤，第60日=姤前一卦夬


def test_ri_gua_overflow_rules():
    ge = CODE["革"]
    assert s.ri_gua(ge, 60) == s.ri_gua(ge, 0)
    leap = s.Config(day_overflow="leap")
    assert N(s.ri_gua(ge, 61, pair=p, cfg=leap) for p in range(6)) == ["离", "离", "乾", "坎", "坎", "坤"]


def test_ri_gua_never_cardinal_over_a_year():
    dt = D("2025-12-22T12:00")
    while dt < D("2026-12-22T12:00"):
        assert s.full(dt)["ri_gua_code"] not in FOUR_CARDINAL, dt
        dt += timedelta(days=1)


def test_ri_gua_examples_2026():
    assert s.full(D("2026-10-23T18:00"))["ri_gua"] == "革"
    assert s.full(D("2026-10-26T10:00"))["ri_gua"] == "损"
    assert s.full(D("2026-02-19T12:00"))["ri_gua"] == "姤"
    assert s.full(D("2026-08-23T12:00"))["ri_gua"] == "革"
    assert s.full(D("2026-12-22T12:00"))["ri_gua"] == "师"


# ---------------------------------------------------------------- 时卦 / 分卦
def test_shi_gua():
    sun = CODE["损"]
    assert N(s.shi_gua(sun, h) for h in range(12)) == [x for x in N(six_changes(sun)) for _ in (0, 1)]
    assert s.full(D("2026-10-26T10:00"))["shi_gua"] == "大畜"
    assert s.full(D("2026-10-26T02:00"))["shi_gua"] == "蒙"
    assert s.full(D("2026-10-25T23:30"))["shi_gua"] == "蒙"


def test_fen_gua():
    f = s.full(D("2026-10-26T10:00"))
    assert f["fen_idx"] == 45 and f["fen_gua"] == "贲"
    assert s.full(D("2026-10-26T07:00"))["fen_gua"] == "大畜"
    assert s.full(D("2026-10-26T07:04"))["fen_gua"] == "需"


# ---------------------------------------------------------------- 全链路示例
def test_full_chain_examples():
    f = s.full(D("2026-10-26T10:00"))
    assert (f["hj_year"], f["month_branch"], f["day_idx"] + 1, f["hour_branch"]) == (2026, "戌", 4, "巳")
    assert (f["yun_gua"], f["shi_gua_"], f["xun_gua"], f["nian_gua"], f["yue_gua"], f["ri_gua"], f["shi_gua"], f["fen_gua"]) == \
        ("姤", "鼎", "姤", "同人", "革", "损", "大畜", "贲")
    f = s.full(D("2020-01-10T12:00"))
    assert (f["nian_gua"], f["yue_gua"], f["xun_gua"], f["ri_gua"], f["shi_gua"]) == ("明夷", "谦", "蛊", "家人", "同人")


# ---------------------------------------------------------------- 备选：卦气定表法（方法 A）
def test_method_A():
    assert N(s.month_gua_A(m) for m in range(1, 13)) == ["复", "临", "泰", "大壮", "夬", "乾", "姤", "遁", "否", "观", "剥", "坤"]
    assert N(s.day_gua_A(d) for d in range(1, 7)) == ["坤", "临", "明夷", "震", "屯", "颐"]
    assert N(SIXTY[(d - 1) // 6] for d in (1, 7, 13, 19, 25)) == ["复", "颐", "屯", "益", "震"]
    assert N(SIXTY[(d - 1) // 6] for d in (31, 37, 43, 49, 55)) == ["噬嗑", "随", "无妄", "明夷", "贲"]
    assert s.day_gua_A(361) == s.day_gua_A(1)
    assert NAMES[s.hour_gua_A(CODE["损"], 5)] == "大畜"


# ---------------------------------------------------------------- 配置：立春起年 / 节气分月
def test_lichun_jieqi_config():
    cfg = s.Config(year_start="lichun", month_boundary="jieqi")
    b, order = s.month_boundaries(2026, cfg)
    assert order == list(range(2, 12)) + [0, 1]
    assert abs((b[0].replace(tzinfo=None) - D("2026-02-04T04:02")).total_seconds()) < 600
    p = s.locate(D("2026-01-20T12:00"), cfg)
    assert p["hj_year"] == 2025 and p["month_branch"] == "丑"
