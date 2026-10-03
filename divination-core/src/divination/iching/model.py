"""model —— 易经的领域模型（最底层，谁都不依赖）。

这一层只定义"东西长什么样"的数据结构，不含任何算法、不碰 I/O：

    - 爻（Line）：阴 / 阳，动 / 不动
    - 卦（Hexagram）：六个爻组成的静态卦象，64 个之一
    - 一次起卦结果（Reading）：本卦 + 变爻 → 变卦

真正的类型定义会在我们敲定"爻怎么表示"之后填进来。
上面的 core / repository / service 三层都依赖本层，本层不依赖任何人。
"""
"""
这一层的数据结构定义易经的基本概念，如：什么是阴、阳、爻、动爻等等
"""
from dataclasses import dataclass
from enum import IntEnum
class Polarity(IntEnum):
    """爻的阴阳属性
        把阳设置成1，阴设置成0，方便未来在运算的时候
        可以直接通过二进制得到卦和卦序
    """
    yin = 0b0
    yang = 0b1

class Trigram(IntEnum):
    """三爻卦的枚举
        二进制最低位的是上爻，
        为了可以和先天卦序对应，上爻变化最快，
        后续变成64卦的先天卦序话可以递减得到
    """
    qian = 0b111
    dui = 0b110
    li = 0b101
    zhen = 0b100
    xun = 0b011
    kan = 0b010
    gen = 0b001
    kun = 0b000

@dataclass(frozen=True)
class Hexagram:
    """一个卦 = 一个 6 位二进制数（0~63）。"""
    value: int


