import Foundation

protocol DivinationEngine {
    func dispatch(_ requestJSON: String) -> String?
}

// 用内嵌 Python 实现：把请求发给 C 桥的 py_dispatch。
struct PythonEngine: DivinationEngine {
    func dispatch(_ requestJSON: String) -> String? {
        guard let c = py_dispatch(requestJSON) else { return nil }
        defer { py_free_string(c) }      // 无论从哪条路径返回，都释放 C 那份
        return String(cString: c)
    }
}


