"""
这个文件是梅花易数的起卦逻辑
"""

from divination.iching.model import Hexagram, Trigram

def _trigram_of(total: int) -> Trigram:
    n = total % 8
    if n != 0:
        trigram =  n
    else:
        trigram = 8
    return Trigram(8 - trigram)

def qigua(year: int, month: int, day: int, hour: int) -> tuple[Hexagram, int]:
    up = _trigram_of(year + month + day)
    down = _trigram_of(year + month + day + hour)

    hexagram = Hexagram((down.value << 3) | up.value)
    moving = (year + month + day + hour) % 6
    if moving == 0:
        moving = 6                                   # 余 0 当第 6 爻(上爻)
    return hexagram, moving