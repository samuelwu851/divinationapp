import model
"""core —— 易经的领域算法（纯逻辑，只依赖 model）。

这一层把"规则"变成"计算"，全部是纯函数，不碰文字资料、不碰 I/O：

    - 起卦：把输入（如筮法的 6/7/8/9）变成一个卦
    - 变卦：按动爻从本卦推出变卦
    - 互、错、综等衍生卦

它只知道卦象的数学结构，不知道每个卦叫什么、卦辞是什么——
那些文字属于 repository 层。
"""

"""
def flip

def zonggua

def cuogua

def hugua

def determine_yinyang
判断某一根爻是阴还是阳

def get_hexagram_by_value
根据卦的value获取卦对象


"""

