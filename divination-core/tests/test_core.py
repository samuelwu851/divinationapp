from divination.iching.model import Hexagram, Polarity
from divination.iching import core

def test_determine_yinyang():
    assert core.determine_yinyang(Hexagram(0b000001), 6) == Polarity.yang  # 剝卦上爻 → Polarity.yang
    assert core.determine_yinyang(Hexagram(0b000001), 1) == Polarity.yin  # 剝卦初爻 → Polarity.yin

def test_determine_yinyang_qian_all_yang():
    """乾卦（0b111111）：六爻皆阳。"""
    qian = Hexagram(0b111111)
    for line in range(1, 7):
        assert core.determine_yinyang(qian, line) == Polarity.yang

def test_zonggua():
    assert core.zonggua(Hexagram(0b000001)) == Hexagram(0b100000)   # 剝 → 復
    assert core.zonggua(Hexagram(0b100010)) == Hexagram(0b010001)   # 屯 → 蒙
    assert core.zonggua(Hexagram(0b101010)) == Hexagram(0b010101)   # 既濟 → 未濟


def test_zonggua_symmetric():
    """上下对称的卦，综卦等于自己。"""
    assert core.zonggua(Hexagram(0b111111)) == Hexagram(0b111111)   # 乾
    assert core.zonggua(Hexagram(0b000000)) == Hexagram(0b000000)   # 坤
    assert core.zonggua(Hexagram(0b010010)) == Hexagram(0b010010)   # 坎


def test_zonggua_is_involution():
    """综的综 = 本卦：翻两次回到原样（对全部 64 卦都成立）。"""
    for v in range(64):
        h = Hexagram(v)
        assert core.zonggua(core.zonggua(h)) == h

def test_cuogua():
    assert core.cuogua(Hexagram(0b111111)) == Hexagram(0b000000)   # 乾 → 坤
    assert core.cuogua(Hexagram(0b000000)) == Hexagram(0b111111)   # 坤 → 乾
    assert core.cuogua(Hexagram(0b000001)) == Hexagram(0b111110)   # 剝 → 夬
    assert core.cuogua(Hexagram(0b010010)) == Hexagram(0b101101)   # 坎 → 離


def test_cuogua_is_involution():
    """错的错 = 本卦（对全部 64 卦成立）。"""
    for v in range(64):
        h = Hexagram(v)
        assert core.cuogua(core.cuogua(h)) == h


def test_cuogua_inverts_every_line():
    """本卦与错卦六爻全相反，所以两者 value 之和必为 63。"""
    for v in range(64):
        assert v + core.cuogua(Hexagram(v)).value == 63

def test_hugua():
    assert core.hugua(Hexagram(0b111111)) == Hexagram(0b111111)   # 乾 → 乾
    assert core.hugua(Hexagram(0b000000)) == Hexagram(0b000000)   # 坤 → 坤
    assert core.hugua(Hexagram(0b100010)) == Hexagram(0b000001)   # 屯 → 剝
    assert core.hugua(Hexagram(0b101010)) == Hexagram(0b010101)   # 既濟 → 未濟
