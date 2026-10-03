# divination-core

术数内核，纯 Python 实现。只做计算，不含 UI、平台、I/O —— 这样它既能被
iPhone / iPad / Mac 的 Swift 层调用，将来也能被网页（JS）复用。

## 目录结构

```
divination-core/
  pyproject.toml          项目元数据 / 依赖 / 打包与测试配置
  src/
    divination/           内核顶层包
      iching/             易经（当前在做）
      # bazi/   八字（未来，平级新增）
      # liuren/ 六壬（未来，平级新增）
  tests/                  单元测试
```

每种术数都是 `divination/` 下一个平级子包，互不依赖。跨术数共用的基础概念
（阴阳 / 五行 / 干支）等到第二种术数真正用到时，再抽到 `divination/shared/`。

## 开发

```bash
# 1. 创建并激活虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 2. 安装测试依赖
pip install -e ".[dev]"

# 3. 跑测试
pytest
```

> 即使不执行 `pip install`，`pyproject.toml` 里的 `pythonpath = ["src"]`
> 也能让 `pytest` 直接找到 `divination` 包，方便快速起步。
