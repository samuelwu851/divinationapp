import Foundation
import Observation

/// 易经速查的状态中心（view-model）。
/// 负责：当前卦值(持久化)、当前卦的完整数据、以及"查 / 变爻"两个动作。
@Observable
final class IChingStore {

    /// 当前卦的完整信息；nil 表示还没加载 / 加载失败。
    private(set) var hexagram: Hexagram?

    /// 最近一次错误信息（给界面提示用）。
    private(set) var errorMessage: String?

    /// 底层引擎（面向协议，便于以后换成 Mock）。
    private let engine: DivinationEngine

    /// UserDefaults 里存"当前卦值"用的键名。
    private let storageKey = "currentHexagramValue"

    /// 当前卦值：读写都走 UserDefaults；没存过就默认乾卦(63)。
    private var currentValue: Int {
        get { UserDefaults.standard.object(forKey: storageKey) as? Int ?? 63 }
        set { UserDefaults.standard.set(newValue, forKey: storageKey) }
    }

    /// 依赖注入：默认用真的 PythonEngine
    init(engine: DivinationEngine = PythonEngine()) {
        self.engine = engine
    }

    /// 加载当前卦（app 打开、或变爻后调用）。
    func load() {
        send(["cmd": "lookup", "value": currentValue])
    }

    /// 翻转第 line 爻（1=初爻 … 6=上爻），得到新卦。
    func flip(line: Int) {
        send(["cmd": "flip", "value": currentValue, "line": line])
    }

    /// 核心流程：拼请求 → 调引擎 → 解码 → 更新状态并持久化。
    private func send(_ request: [String: Any]) {
        guard
            let data = try? JSONSerialization.data(withJSONObject: request),
            let requestJSON = String(data: data, encoding: .utf8)
        else { errorMessage = "请求无法序列化"; return }

        guard let responseJSON = engine.dispatch(requestJSON) else {
            errorMessage = "引擎无响应"; return
        }

        let decoder = JSONDecoder()
        decoder.keyDecodingStrategy = .convertFromSnakeCase   // hexagram_text → hexagramText
        do {
            let hex = try decoder.decode(Hexagram.self, from: Data(responseJSON.utf8))
            self.hexagram = hex
            self.currentValue = hex.value     // 记住最新卦值（写进 UserDefaults）
            self.errorMessage = nil
        } catch {
            self.errorMessage = "解码失败: \(error)"
        }
    }
}
