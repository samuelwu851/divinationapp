#include "PyBridge.h"
#include <Python/Python.h>
#include <string.h>
#include <stdlib.h>

// 把一个目录加到 Python 的 sys.path 最前面，让 import 能在这里找包。
static void add_to_sys_path(const char *path) {
    if (path == NULL) return;
    PyObject *sys_path = PySys_GetObject("path"); // 借用引用，不用我们释放
    if (sys_path == NULL) return;
    PyObject *p = PyUnicode_FromString(path);      // 新建引用，我们拥有
    if (p == NULL) return;
    PyList_Insert(sys_path, 0, p);                 // 插到最前
    Py_DECREF(p);                                  // 我们用完了，释放自己那份
}

int py_bootstrap(const char *home, const char *appPath) {
    PyStatus status;

    PyPreConfig preconfig;
    PyPreConfig_InitIsolatedConfig(&preconfig);
    preconfig.utf8_mode = 1;
    status = Py_PreInitialize(&preconfig);
    if (PyStatus_Exception(status)) return 1;

    PyConfig config;
    PyConfig_InitIsolatedConfig(&config);
    config.buffered_stdio = 0;
    config.write_bytecode = 0;
    if (home != NULL) {
        status = PyConfig_SetBytesString(&config, &config.home, home);
        if (PyStatus_Exception(status)) { PyConfig_Clear(&config); return 2; }
    }
    status = Py_InitializeFromConfig(&config);
    PyConfig_Clear(&config);
    if (PyStatus_Exception(status)) return 3;

    // 解释器起来后，把我们包的目录加进 sys.path
    add_to_sys_path(appPath);

    PyRun_SimpleString("import sys; print('[divination] Python', sys.version.split()[0], 'ready')");
    return 0;
}

char *py_dispatch(const char *request_json) {
    // 1) 导入总机模块 divination.api
    PyObject *module = PyImport_ImportModule("divination.api");
    if (module == NULL) { PyErr_Print(); return NULL; }

    // 2) 取出 handle 函数
    PyObject *func = PyObject_GetAttrString(module, "handle");
    Py_DECREF(module);
    if (func == NULL || !PyCallable_Check(func)) {
        PyErr_Print(); Py_XDECREF(func); return NULL;
    }

    // 3) 参数：C 字符串 → Python str，然后调用 handle(request_json)
    PyObject *arg = PyUnicode_FromString(request_json);
    PyObject *result = PyObject_CallOneArg(func, arg);
    Py_DECREF(arg);
    Py_DECREF(func);
    if (result == NULL) { PyErr_Print(); return NULL; }

    // 4) 把返回的 Python 字符串转成 UTF-8 的 C 字符串，并复制一份带回去
    const char *utf8 = PyUnicode_AsUTF8(result); // 指向 result 内部，result 一释放就失效
    char *copy = (utf8 != NULL) ? strdup(utf8) : NULL; // 所以先复制一份自己的
    Py_DECREF(result);
    return copy;
}

void py_free_string(char *s) {
    free(s);
}
