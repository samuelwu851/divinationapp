//
//  PyBridge.h
//  divinationapp
//
//  Swift 与嵌入式 Python 之间的"瘦边界"（C 侧）。
//  这里只声明朴素的 C 函数；所有 Python C API 的细节都藏在 PyBridge.c 里，
//  不让 <Python/Python.h> 泄漏进 Swift。
//

#ifndef PyBridge_h
#define PyBridge_h

/// 初始化并启动嵌入在 app 里的 Python 解释器。
///
/// - Parameter home: Python 运行时的 "home" 目录绝对路径，
///   即 app bundle 内 `Python.framework/Versions/3.13`（其下有 lib/python3.13 标准库）。
/// - Returns: 0 表示成功；非 0 表示某一步失败（见实现里的返回码）。
int py_bootstrap(const char *home, const char *appPath);

/// 通用分发入口：把请求 JSON 交给 Python 的 divination.api.handle，返回响应 JSON。
/// 返回值是 malloc 出来的 C 字符串，用完必须调 py_free_string 释放；出错返回 NULL。
char *py_dispatch(const char *request_json);

/// 释放 py_lookup_json 返回的字符串。
void py_free_string(char *s);

#endif /* PyBridge_h */

