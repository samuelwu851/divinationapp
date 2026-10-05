# C ↔ Python 桥接速查（PyBridge）

记录 Swift → C 桥（`PyBridge.c`）里，和嵌入式 CPython 打交道的套路。
以后新增对外接口时照着查。

## 1. 一切都是"转换 / 装箱"，没有"直接传"

C 的裸类型和 Python 的对象是两个世界。C 侧想给 Python 一个值，必须用
`PyXxx_FromYyy` 把 C 值**装箱**成一个 Python 对象（`PyObject *`）；
反过来想读 Python 的值，用 `PyXxx_AsYyy` **拆箱**回 C 类型。

```c
PyObject *arg = PyLong_FromLong(value);   // C long  → Python int 对象
const char *s = PyUnicode_AsUTF8(result); // Python str → C 字符串(借用)
```

## 2. C API 名字 ↔ Python 类型对照（名字是历史旧称，容易绕）

| C API 前缀 | 对应 Python 类型 | 备注 |
|---|---|---|
| `PyLong`    | `int`   | Python2 的 int/long 在 Py3 合并为 int，C API 仍叫 PyLong |
| `PyUnicode` | `str`   | UTF-8 文本用 `PyUnicode_AsUTF8` 取 |
| `PyFloat`   | `float` | |
| `PyBool`    | `bool`  | |
| `PyList` / `PyDict` / `PyTuple` | `list` / `dict` / `tuple` | |

> 注意：Python 函数签名里的类型注解（如 `def f(value: int)`）**运行时不强制校验**，
> 真正保证类型正确的是 C 侧的转换函数。

## 3. 从 C 调用一个 Python 函数的标准五步

```c
// 1) 导入模块
PyObject *module = PyImport_ImportModule("divination.iching.service");
// 2) 取出函数对象
PyObject *func = PyObject_GetAttrString(module, "lookup_json");
// 3) 把参数装箱
PyObject *arg = PyLong_FromLong(value);
// 4) 调用（返回新对象）
PyObject *result = PyObject_CallOneArg(func, arg);
// 5) 拆箱结果回 C 类型
const char *utf8 = PyUnicode_AsUTF8(result);
```

每一步都可能返回 `NULL`（出错）——务必检查，出错时 `PyErr_Print()` 打印 Python 异常栈。

## 4. 引用计数：谁拥有，谁释放

Python 对象靠**引用计数**回收。C 侧要分清手里的引用是"拥有"还是"借用"：

- **拥有（owned）**：`PyXxx_From*`、`PyObject_GetAttrString`、`PyObject_Call*`、
  `PyImport_ImportModule` 返回的——用完必须 `Py_DECREF`（可能为 NULL 用 `Py_XDECREF`）。
- **借用（borrowed）**：`PySys_GetObject`、`PyUnicode_AsUTF8` 返回的内部指针——
  **不要** DECREF；且它的有效期绑在宿主对象上，宿主一释放它就失效。

**典型坑**：`PyUnicode_AsUTF8(result)` 给的是 `result` 内部缓冲的指针。
若先 `Py_DECREF(result)` 再用这个指针 → 野指针。正确做法：先 `strdup` 复制一份，
再 DECREF result。

## 5. 字符串跨边界的所有权约定（本项目）

- `py_lookup_json` 内部 `strdup` 出一份 C 字符串返回 → **调用方拥有**。
- Swift 用完必须调 `py_free_string` 释放，否则内存泄漏。

```swift
guard let c = py_lookup_json(63) else { return }
let json = String(cString: c)  // 复制进 Swift String
py_free_string(c)              // 释放 C 那份
```

## 6. GIL（以后多线程/后台调用时要注意）

现在都在主线程、启动期调用，没问题。将来若从后台线程调 Python，
需要用 `PyGILState_Ensure()` / `PyGILState_Release()` 包住调用，先占住 GIL 再动 Python 对象。
