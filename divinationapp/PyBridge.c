//
//  PyBridge.c
//  divinationapp
//
//  C 侧的实现：唯一允许直接 #include Python 头、直接调 Python C API 的地方。
//

#include "PyBridge.h"
#include <Python/Python.h>

int py_bootstrap(const char *home) {
    PyStatus status;

    // ── 预配置（PyPreConfig）──────────────────────────────
    // 用"隔离"配置：忽略开发机上的 PYTHONHOME/PYTHONPATH 等环境变量，
    // 避免被系统里的另一个 Python 干扰，保证行为可复现。
    PyPreConfig preconfig;
    PyPreConfig_InitIsolatedConfig(&preconfig);
    preconfig.utf8_mode = 1;              // 官方建议：开启 UTF-8 模式
    status = Py_PreInitialize(&preconfig);
    if (PyStatus_Exception(status)) {
        return 1;
    }

    // ── 主配置（PyConfig）────────────────────────────────
    PyConfig config;
    PyConfig_InitIsolatedConfig(&config);
    config.buffered_stdio = 0;            // print 立即刷出，方便在 Xcode 控制台看到
    config.write_bytecode = 0;            // 不写 .pyc —— app bundle 是只读的

    // 把解释器 home 指向 bundle 内框架的 Versions/3.13，
    // 解释器据此找到标准库（lib/python3.13 及 lib-dynload）。
    if (home != NULL) {
        status = PyConfig_SetBytesString(&config, &config.home, home);
        if (PyStatus_Exception(status)) {
            PyConfig_Clear(&config);
            return 2;
        }
    }

    status = Py_InitializeFromConfig(&config);
    PyConfig_Clear(&config);
    if (PyStatus_Exception(status)) {
        return 3;
    }

    // ── 里程碑 0：证明解释器真的在 app 里活着 ──────────────
    PyRun_SimpleString(
        "import sys\n"
        "print('==================================')\n"
        "print('[divination] Python 已在 app 内启动')\n"
        "print('[divination] version:', sys.version)\n"
        "print('[divination] sys.path:', sys.path)\n"
        "print('==================================')\n"
    );

    return 0;
}
