from divination.iching.model import Hexagram
from divination.iching import repository

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