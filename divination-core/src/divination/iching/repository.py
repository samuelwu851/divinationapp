"""repository —— 数据源层：64 卦的只读参考资料。

这一层负责"查文字"：给一个卦，返回它的名字、卦辞、爻辞等。
资料本身是静态只读的（永远不变），存在同目录的 data/ 下。

对外先定义一个接口（要能查什么），底层实现现在就读内嵌的 JSON；
将来想换成 SQLite 或远程，只换实现、不动上层——这就是把"查什么"
和"从哪查"分开的好处。

注意：这里只管只读资料。用户自己的历史 / 收藏是可写数据，不归内核，
留给各平台（Swift、网页）自己存。
"""
import json
from importlib import resources

from divination.iching.model import Hexagram

def _load() -> dict[int, dict]:
    """从内嵌的 JSON 文件里加载 64 卦的资料。
    取出卦序、卦名和先天卦序"""
    path = resources.files("divination.iching") / "data" / "hexagrams.json"
    records = json.loads(path.read_text(encoding="utf-8"))
    result ={}
    for record in records:
        value = record["value"]
        result[value] = {
            "value": record["value"],
            "order": record["order"],
            "full_name": record["full_name"],
        }
    return result

_INDEX = _load()

def info_of(hexagram: Hexagram) -> dict:
    return _INDEX[hexagram.value]

def name_of(hexagram: Hexagram) -> str:
    return info_of(hexagram)["full_name"]

def value_of(hexagram: Hexagram) -> int:
    return info_of(hexagram)["value"]

def order_of(hexagram: Hexagram) -> int:
    return info_of(hexagram)["order"]

