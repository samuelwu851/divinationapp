//
//  divinationappApp.swift
//  divinationapp
//
//  Created by samuelwu on 2026/10/03.
//

import SwiftUI

@main
struct divinationappApp: App {

    init() {
        Self.bootstrapPython()
        Self.testLookup()          // 里程碑 1 自检
    }

    var body: some Scene {
        WindowGroup {
            ContentView()
        }
    }

    /// 在 app 启动时初始化嵌入的 Python 解释器，并把我们的包目录加入搜索路径。
    private static func bootstrapPython() {
        // 嵌入的框架位于 app bundle 的 Frameworks 目录下。
        // 注意：Versions/3.13 这段是 macOS 框架布局；之后推 iOS 时再按 iOS 布局调整。
        guard let frameworks = Bundle.main.privateFrameworksURL else {
            print("❌ 找不到 Frameworks 目录"); return
        }
        let home = frameworks
            .appendingPathComponent("Python.framework/Versions/3.13").path

        // divination 包被打进了 app 资源区，它的父目录就是 resourceURL。
        guard let appPath = Bundle.main.resourceURL?.path else {
            print("❌ 找不到资源目录"); return
        }

        let rc = py_bootstrap(home, appPath)
        print(rc == 0 ? "✅ py_bootstrap 成功" : "❌ py_bootstrap 失败 rc=\(rc)")
    }

    /// 里程碑 1 自检：调一次真正的内核接口，把卦象 JSON 打印出来。
    private static func testLookup() {
        guard let c = py_lookup_json(63) else {
            print("❌ lookup_json 返回 NULL（看上面有没有 Python 报错）"); return
        }
        let json = String(cString: c)   // C 字符串 → Swift String（会复制）
        py_free_string(c)               // 复制完，释放 C 那份，避免泄漏
        print("✅ lookup_json(63) =\n\(json)")
    }
}
