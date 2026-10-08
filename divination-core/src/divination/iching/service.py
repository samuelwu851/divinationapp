"""service —— 应用层门面：对外的唯一入口。

这一层把下面三层编排成"一个完整用例"，并负责和外界交换
朴素、可序列化的数据（给 Swift / 将来的网页用）：

    外界给我输入（如 6 个爻）
        → core 算出本卦、变卦
        → repository 查出它们的名字、卦辞、爻辞
        → 拼成一个朴素的结果（dict / 可转 JSON）返回

UI 和平台只认识这一层，不直接碰 core / repository / model。
依赖方向：service → core / repository → model，始终单向往下。
"""

from divination.iching import core, repository
from divination.iching.model import Hexagram
import json

def checkandpack(value: int) -> dict:
    """
        这个函数通过数字来得到本卦、错卦、互卦、综卦
    """
    
    """得到每一根爻的阴阳，而且下标越小，爻位越低
        因为先传进去的是小数。所以在determine_yinyang里面会右移掉更多的位数，先读取
        下面的爻、先放进列表，所以列表的下标和爻位对应
    """
    hexagram = Hexagram(value)
    lines = [core.determine_yinyang(hexagram, line).value for line in range(1, 7)]
    hexagram_text = repository.get_hexagram_text(hexagram)
    cuogua = core.cuogua(hexagram)
    cuogua_lines = [core.determine_yinyang(cuogua, line).value for line in range(1, 7)]
    cuogua_text = repository.get_hexagram_text(cuogua)
    zonggua = core.zonggua(hexagram)
    zonggua_lines = [core.determine_yinyang(zonggua, line).value for line in range(1, 7)]
    zonggua_text = repository.get_hexagram_text(zonggua)
    hugua = core.hugua(hexagram)
    hugua_lines = [core.determine_yinyang(hugua, line).value for line in range(1, 7)]
    hugua_text = repository.get_hexagram_text(hugua)
    
    return {
        "value": hexagram.value,
        "name": repository.name_of(hexagram),
        "order": repository.order_of(hexagram),
        "lines": lines,
        "hexagram_text": hexagram_text,
        "cuogua": repository.name_of(cuogua),
        "cuogua_lines": cuogua_lines,
        "cuogua_text": cuogua_text,
        "zonggua": repository.name_of(zonggua),
        "zonggua_lines": zonggua_lines,
        "zonggua_text": zonggua_text,
        "hugua": repository.name_of(hugua),
        "hugua_lines": hugua_lines,
        "hugua_text": hugua_text
    }

def flip(value: int, line: int) -> dict:
    """翻某一爻，返回新卦的完整显示数据（UI 不碰任何运算）。"""
    new_hexagram = core.flip(Hexagram(value), line)
    return checkandpack(new_hexagram.value)

def yilin(org_value: int, chg_value: int) -> dict:
    """
        通过本卦和变卦的value得到易林的文本
    """
    original = Hexagram(org_value)
    changed = Hexagram(chg_value)
    return {
        "org_value": org_value,
        "chg_value": chg_value,
        "text": repository.get_yilin_text(original, changed)
    }



"""
    以下的函数是divination-core 的对外接口
    接收int输出所有关于这个卦的信息（以json格式）
    包括本卦、互卦、错卦、综卦的爻、爻辞、卦辞
"""
def lookup_json(value: int) -> str:
    """供swift调用：输入卦的数字，返回json字符串。"""
    return json.dumps(checkandpack(value), ensure_ascii=False)


def flip_json(value: int, line: int) -> str:
    """供swift调用：翻某一爻，返回新卦的json字符串。"""
    return json.dumps(flip(value, line), ensure_ascii=False)

def yilin_json(original_value: int, changed_value: int) -> str:
    return json.dumps(yilin(original_value, changed_value), ensure_ascii=False)