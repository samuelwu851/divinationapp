import divination.iching.model as model
"""core —— 易经的领域算法（纯逻辑，只依赖 model）。

这一层把"规则"变成"计算"，全部是纯函数，不碰文字资料、不碰 I/O：

    - 起卦：把输入（如筮法的 6/7/8/9）变成一个卦
    - 变卦：按动爻从本卦推出变卦
    - 互、错、综等衍生卦

它只知道卦象的数学结构，不知道每个卦叫什么、卦辞是什么——
那些文字属于 repository 层。
"""


def determine_yinyang(Hexagram: model.Hexagram, line: int) -> model.Polarity:
    """判断某一根爻是阴还是阳"""
    index = 6 - line
    bit = (Hexagram.value >> index) & 1
    return model.Polarity(bit)

def flip(hexagram: model.Hexagram, line: int) -> model.Hexagram:
    """翻转第 line 爻，返回一个新卦（原卦不动）。line：1=初爻 … 6=上爻。"""
    index = 6 - line
    mask = 1 << index
    new_value = hexagram.value ^ mask
    return model.Hexagram(new_value)

def zonggua(hexagram: model.Hexagram) -> model.Hexagram:
    #value = int(format(hexagram.value, '06b')[::-1], 2)
    #return model.Hexagram(value)
    value = hexagram.value
    result = 0
    for i in range(6):
        bit = (value >> i) & 1 # 得到每一爻的阴阳
        result |= bit << (5 - i) # 放到镜像位置，并入result
    return model.Hexagram(result)

def cuogua(hexagram: model.Hexagram) -> model.Hexagram:
    result = hexagram.value ^ (0b111111)
    return model.Hexagram(result)

def hugua(hexagram: model.Hexagram) -> model.Hexagram:
    """取中间四爻重组。下卦=原2,3,4爻；上卦=原3,4,5爻。"""
    lower = (hexagram.value >> 2) & 0b111   # 原第2,3,4爻 → 互卦下卦
    upper = (hexagram.value >> 1) & 0b111   # 原第3,4,5爻 → 互卦上卦
    value = (lower << 3) | upper
    return model.Hexagram(value)




"""
def flip

def zonggua

def cuogua

def hugua

"""

