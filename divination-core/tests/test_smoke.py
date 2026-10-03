"""冒烟测试（smoke test）。

只验证项目结构和工具链是否就绪，不涉及任何业务逻辑。
跑通它，就证明"写代码 → pytest → 看结果"这个开发循环已经打通。
"""

import divination
from divination import iching


def test_package_imports():
    """内核顶层包与易经子包都能被导入。"""
    assert divination is not None
    assert iching is not None


def test_version_is_exposed():
    """顶层包对外暴露了版本号。"""
    assert divination.__version__ == "0.1.0"
