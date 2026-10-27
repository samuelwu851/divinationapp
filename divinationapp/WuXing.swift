import SwiftUI

/// 五行：天干地支单字 → 颜色（用于八字上色）。
enum WuXing {
    case wood, fire, earth, metal, water

    var color: Color {
        switch self {
        case .wood:  return .green
        case .fire:  return .red
        case .earth: return Color(red: 0.55, green: 0.35, blue: 0.15)  // 咖啡色
        case .metal: return .yellow
        case .water: return .blue
        }
    }

    /// 天干地支单字 → 五行。
    static func of(_ c: Character) -> WuXing? {
        switch c {
        case "甲", "乙", "寅", "卯":                return .wood
        case "丙", "丁", "巳", "午":                return .fire
        case "戊", "己", "辰", "戌", "丑", "未":     return .earth
        case "庚", "辛", "申", "酉":                return .metal
        case "壬", "癸", "子", "亥":                return .water
        default:                                   return nil
        }
    }
}

/// 一个干支单字，按五行上色（无 emoji）。
struct GanZhiChar: View {
    let c: Character
    var body: some View {
        Text(String(c))
            .foregroundStyle(WuXing.of(c)?.color ?? .primary)
            .bold()
    }
}

/// 四柱展示：四柱并排，每柱天干在上、地支在下，按五行上色。
/// 梅花时间起卦、皇极经世共用。
struct BaziPillarsView: View {
    let pillars: [String]          // [年柱, 月柱, 日柱, 时柱]，每柱两字
    var charFont: Font = .largeTitle

    var body: some View {
        HStack(spacing: 14) {
            ForEach(Array(pillars.enumerated()), id: \.offset) { _, pillar in
                let chars = Array(pillar)
                VStack(spacing: 2) {
                    if chars.count >= 1 { GanZhiChar(c: chars[0]).font(charFont) }
                    if chars.count >= 2 { GanZhiChar(c: chars[1]).font(charFont) }
                }
            }
        }
    }
}
