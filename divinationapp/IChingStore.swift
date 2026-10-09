import Foundation
import Observation

@Observable
final class IChingStore {
    private(set) var original: Hexagram?     // 本卦
    private(set) var changed: Hexagram?      // 变卦
    private(set) var yilin: String?          // 崔氏易林文本（仅变卦模式）
    private(set) var errorMessage: String?

    /// 变卦模式开关（UI 可双向绑定）
    var showChanged: Bool {
        didSet {
            UserDefaults.standard.set(showChanged, forKey: showKey)
            if showChanged {
                if changedValue == nil { changedValue = originalValue }  // 默认同本卦
                reloadChanged()
                recomputeYilin()
            } else {
                yilin = nil
            }
        }
    }

    private let engine: DivinationEngine
    private let orgKey = "originalValue"
    private let chgKey = "changedValue"
    private let showKey = "showChanged"

    private var originalValue: Int {
        get { UserDefaults.standard.object(forKey: orgKey) as? Int ?? 63 }
        set { UserDefaults.standard.set(newValue, forKey: orgKey) }
    }
    private var changedValue: Int? {
        get { UserDefaults.standard.object(forKey: chgKey) as? Int }
        set { UserDefaults.standard.set(newValue, forKey: chgKey) }
    }

    init(engine: DivinationEngine = PythonEngine()) {
        self.engine = engine
        self.showChanged = UserDefaults.standard.bool(forKey: showKey)  // didSet 在 init 里不触发
    }

    /// 动爻下标集合：本卦与变卦阴阳不同的那几爻
    var changingLines: Set<Int> {
        guard let o = original, let c = changed else { return [] }
        var s = Set<Int>()
        for i in 0..<min(o.lines.count, c.lines.count) where o.lines[i] != c.lines[i] {
            s.insert(i)
        }
        return s
    }

    func load() {
        original = fetchLookup(originalValue)
        if showChanged {
            if changedValue == nil { changedValue = originalValue }
            reloadChanged()
            recomputeYilin()
        }
    }

    func flipOriginal(line: Int) {
        guard let cur = original, let hex = fetchFlip(cur.value, line) else { return }
        original = hex
        originalValue = hex.value
        if showChanged { recomputeYilin() }   // 本卦变 → 重算易林
    }

    func flipChanged(line: Int) {
        guard let cur = changed, let hex = fetchFlip(cur.value, line) else { return }
        changed = hex
        changedValue = hex.value
        recomputeYilin()                       // 变卦变 → 重算易林
    }

    // —— 私有辅助 ——
    private func reloadChanged() {
        if let v = changedValue { changed = fetchLookup(v) }
    }

    private func recomputeYilin() {
        guard let o = original, let c = changed else { yilin = nil; return }
        guard let resp = dispatch(["cmd": "yilin", "org_value": o.value, "chg_value": c.value])
        else { return }
        let dec = JSONDecoder(); dec.keyDecodingStrategy = .convertFromSnakeCase
        yilin = (try? dec.decode(YilinResult.self, from: Data(resp.utf8)))?.text
    }

    private func fetchLookup(_ value: Int) -> Hexagram? {
        decodeHex(dispatch(["cmd": "lookup", "value": value]))
    }
    private func fetchFlip(_ value: Int, _ line: Int) -> Hexagram? {
        decodeHex(dispatch(["cmd": "flip", "value": value, "line": line]))
    }

    /// 发请求，拿回响应 JSON 字符串
    private func dispatch(_ request: [String: Any]) -> String? {
        guard let data = try? JSONSerialization.data(withJSONObject: request),
              let reqJSON = String(data: data, encoding: .utf8) else {
            errorMessage = "请求无法序列化"; return nil
        }
        guard let resp = engine.dispatch(reqJSON) else { errorMessage = "引擎无响应"; return nil }
        return resp
    }

    private func decodeHex(_ json: String?) -> Hexagram? {
        guard let json else { return nil }
        let dec = JSONDecoder(); dec.keyDecodingStrategy = .convertFromSnakeCase
        do { return try dec.decode(Hexagram.self, from: Data(json.utf8)) }
        catch { errorMessage = "解码失败: \(error)"; return nil }
    }
}

/// 易林响应：{"org_value":…, "chg_value":…, "text":"…"}，只取 text。
struct YilinResult: Codable {
    let text: String
}
