from divination.meihua.core import qigua


def test_qian_wei_tian():
    """上乾下乾 → 乾为天(63)，动爻 5。"""
    hexagram, moving = qigua(1, 4, 4, 8)   # 上=9%8=1乾, 下=17%8=1乾, 动=17%6=5
    assert hexagram.value == 63
    assert moving == 5


def test_di_tian_tai():
    """上坤下乾 → 地天泰(56)，动爻 3。"""
    hexagram, moving = qigua(2, 3, 3, 1)   # 上=8%8=0坤, 下=9%8=1乾, 动=9%6=3
    assert hexagram.value == 56
    assert moving == 3


def test_moving_zero_becomes_six():
    """总和整除 6 时，动爻取第 6 爻。"""
    hexagram, moving = qigua(3, 3, 3, 3)   # 上=9%8=1乾, 下=12%8=4震, 动=12%6=0→6
    assert hexagram.value == 39            # (4<<3)|7
    assert moving == 6


def test_kun_wei_di():
    """上坤下坤 → 坤为地(0)，动爻 2。"""
    hexagram, moving = qigua(8, 8, 8, 8)   # 上=24%8=0坤, 下=32%8=0坤, 动=32%6=2
    assert hexagram.value == 0
    assert moving == 2


def test_result_always_valid():
    """任意输入：卦值 0–63、动爻 1–6。"""
    for y in range(1, 13):
        for h in range(1, 13):
            hexagram, moving = qigua(y, 6, 15, h)
            assert 0 <= hexagram.value <= 63
            assert 1 <= moving <= 6
