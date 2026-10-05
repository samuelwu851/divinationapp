from divination.iching.model import Hexagram
from divination.iching import repository
from divination.iching import core

def test_name_of_returns_full_name():
    """给一个卦，查出的是全名。"""
    # 准备 + 执行 + 断言
    assert repository.name_of(Hexagram(0b111111)) == "乾為天"
    assert repository.name_of(Hexagram(0b000000)) == "坤為地"
    assert repository.name_of(Hexagram(0b000001)) == "山地剝"


def test_order_is_king_wen_number():
    """order 是周易卦序：乾=1，坤=2，剝=23。"""
    assert repository.order_of(Hexagram(0b111111)) == 1
    assert repository.order_of(Hexagram(0b000000)) == 2
    assert repository.order_of(Hexagram(0b000001)) == 23


def test_info_of_has_three_fields():
    """info_of 返回 value / order / full_name 三个字段。"""
    info = repository.info_of(Hexagram(0b111111))
    assert info == {"value": 63, "order": 1, "full_name": "乾為天"}


def test_get_hexagram_text_qian():
    """乾卦(63)：卦辞、初爻、上爻爻辞正确。"""
    t = repository.get_hexagram_text(Hexagram(63))
    assert t["still"] == "元亨利貞。"
    assert t["lines"][0] == "潛龍勿用。"   # 初爻
    assert t["lines"][5] == "亢龍有悔。"   # 上爻


def test_get_hexagram_text_kun():
    """坤卦(0)：卦辞开头正确，爻辞恰好 6 条。"""
    t = repository.get_hexagram_text(Hexagram(0))
    assert t["still"].startswith("元亨，利牝馬之貞。")
    assert len(t["lines"]) == 7


def test_get_hexagram_text_bo():
    """剝卦(1)：卦辞与上爻爻辞。"""
    t = repository.get_hexagram_text(Hexagram(1))
    assert t["still"] == "不利有攸往。"
    assert t["lines"][5] == "碩果不食，君子得輿，小人剝廬。"
