import Foundation

struct Hexagram: Codable {
    let value: Int
    let name: String            // 本卦全名
    let order: Int
    let lines: [Int]
    let hexagramText: HexagramText

    // —— 三个衍生卦（扁平字段，对应 JSON：cuogua / cuogua_lines / cuogua_text …）——
    let cuogua: String
    let cuoguaLines: [Int]
    let cuoguaText: HexagramText
    let zonggua: String
    let zongguaLines: [Int]
    let zongguaText: HexagramText
    let hugua: String
    let huguaLines: [Int]
    let huguaText: HexagramText

    /// 把三个衍生卦整理成统一结构，方便界面遍历。computed 属性不参与解码。
    var derived: [DerivedHexagram] {
        [
            DerivedHexagram(label: "错卦", name: cuogua,  lines: cuoguaLines,  text: cuoguaText),
            DerivedHexagram(label: "综卦", name: zonggua, lines: zongguaLines, text: zongguaText),
            DerivedHexagram(label: "互卦", name: hugua,   lines: huguaLines,   text: huguaText),
        ]
    }
}

struct HexagramText: Codable {
    let still: String           // 卦辞
    let lines: [String]         // 爻辞
}

/// 一个衍生卦（错 / 综 / 互）的统一表示，供界面和弹窗使用。
struct DerivedHexagram: Identifiable {
    let label: String           // 错卦 / 综卦 / 互卦
    let name: String            // 卦名
    let lines: [Int]
    let text: HexagramText
    var id: String { label }
}
