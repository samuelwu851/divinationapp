# Swift ↔ Python 的交互：单一通用分发器（dispatch）

这份文档解释本项目里 Swift 和内嵌 Python 之间**怎么通信**，以及为什么这么设计。
目标：以后你加新功能时，知道该改哪里、不该动哪里。

---

## 1. 一句话概括

Swift 和 Python 之间**只有一个洞**：一个叫 `py_dispatch` 的 C 函数。
所有交互都走它——**字符串进（请求 JSON），字符串出（响应 JSON）**。
要调哪个具体功能，由 Python 内部的"总机" `divination.api.handle` 根据请求里的
`cmd` 字段决定。

```
Swift  ──"{cmd:...}"──▶  py_dispatch (C桥)  ──▶  divination.api.handle (Python总机)
                                                        │ 按 cmd 分发
                                                        ▼
                                              iching.service.lookup_json / flip_json
Swift  ◀──"卦象JSON"──  py_dispatch  ◀──────────────────┘
```

---

## 2. 为什么这么设计

我们一开始就定了**瘦边界**：两边只交换朴素的 JSON 字符串，谁也不碰对方的内部类型。
单一分发器把这个思想推到极致，好处有三：

1. **C 桥冻结**：`py_dispatch` 写一次，永远不改。不管 Python 里加多少功能，
   C 层、Swift 的调用机制都不动。
2. **扩展只在 Python**：加新功能 = 在 `api.py` 的 `handle` 里多一个 `elif`。
3. **可移植**：这套"命令 + JSON"契约和语言无关。将来做网页版，JS 用同样的
   请求格式即可，Python 内核与总机原样复用。

代价：失去 C 层对每个函数参数的类型检查（全是字符串）。但我们的契约本来就是
"字符串进、JSON 出"，损失很小。

> 这其实是经典的 **命令模式 / 字符串上的极简 RPC**。

---

## 3. 请求 / 响应契约

**请求**（Swift → Python）：一个 JSON 对象，必带 `cmd`，其余是该命令的参数。

```jsonc
{"cmd": "lookup", "value": 63}          // 查某个卦
{"cmd": "flip",   "value": 63, "line": 2} // 翻某一爻，得到新卦
```

**响应**（Python → Swift）：
- 成功：对应命令的结果 JSON（目前是整个卦象对象）。
- 失败：`{"error": "错误描述"}`。总机用 try/except 兜底，**内核异常不会让 app 崩**，
  而是变成一条 error JSON 回给 Swift。

---

## 4. 一条请求的完整旅程（以 `{"cmd":"lookup","value":63}` 为例）

1. **Swift** 把请求字符串传给 `py_dispatch(request)`（C 函数，经桥接头对 Swift 可见）。
2. **C 桥 `py_dispatch`**（见 `PyBridge.c`）：
   - 导入 Python 模块 `divination.api`
   - 取出函数 `handle`
   - 把 C 字符串装箱成 Python `str`
   - 调用 `handle(request)`
   - 把返回的 Python `str` 拆箱成 UTF-8 的 C 字符串，`strdup` 复制一份返回
3. **Python 总机 `handle`**（见 `divination/api.py`）：
   - `json.loads` 解析请求，读 `cmd == "lookup"`
   - 调 `iching.service.lookup_json(63)`
4. **内核** 算出卦象，`json.dumps` 成字符串，层层原样返回。
5. **Swift** 拿到 C 字符串 → 转成 `String` → 调 `py_free_string` 释放 C 那份。
   （内存所有权约定见 `docs/python-c-bridge.md`。）

---

## 5. 怎么加一个新功能（唯一要记的流程）

假设以后要加"随机起卦" `random`：

1. 在 `divination/iching/service.py`（或相应内核）写好 `random_json()`。
2. 在 `divination/api.py` 的 `handle` 里加一行分发：
   ```python
   elif cmd == "random":
       return iching_service.random_json()
   ```
3. Swift 侧发 `{"cmd":"random"}` 即可。

**C 桥、桥接头、构建脚本——全都不用动。** 这就是这套设计买到的东西。

---

## 6. 相关文件一览

| 文件 | 角色 |
|---|---|
| `divinationapp/PyBridge.h` / `.c` | C 桥，唯一入口 `py_dispatch`（已冻结）|
| `divination-core/src/divination/api.py` | Python 总机 `handle`，分发中心（扩展点）|
| `divination-core/src/divination/iching/service.py` | 易经功能实现 |
| `docs/python-c-bridge.md` | C↔Python 类型转换与内存所有权细节 |
