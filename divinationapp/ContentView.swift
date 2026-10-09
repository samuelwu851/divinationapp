import SwiftUI

struct ContentView: View {
    @State private var store = IChingStore()

    var body: some View {
        ScrollView {
            VStack(spacing: 18) {
                // 开关放右上角
                HStack {
                    Spacer()
                    Toggle("变卦模式", isOn: $store.showChanged).fixedSize()
                }

                if let org = store.original {
                    if store.showChanged, let chg = store.changed {
                        // 本卦 | 变卦 并排（紧凑：只有卦名+六爻，点卦名看浮窗）
                        HStack(alignment: .top, spacing: 48) {
                            HexagramPanelView(hex: org, compact: true,
                                              changingLines: store.changingLines,
                                              showArrow: true,            // 本卦侧画 → 指向变卦
                                              onFlip: { store.flipOriginal(line: $0) })
                            HexagramPanelView(hex: chg, compact: true,
                                              changingLines: store.changingLines,
                                              showArrow: false,
                                              onFlip: { store.flipChanged(line: $0) })
                        }

                        // 焦氏易林：两卦下方
                        if let yilin = store.yilin {
                            Divider()
                            VStack(spacing: 6) {
                                Text("焦氏易林").font(.headline)
                                Text(yilin).font(.title3).frame(maxWidth: 600)
                            }
                        }

                        // 错 / 综 / 互：在易林下方（本卦、变卦各一组）
                        HStack(alignment: .top, spacing: 48) {
                            VStack(spacing: 6) {
                                Text("本卦").font(.caption).foregroundStyle(.secondary)
                                DerivedRow(hex: org)
                            }
                            VStack(spacing: 6) {
                                Text("变卦").font(.caption).foregroundStyle(.secondary)
                                DerivedRow(hex: chg)
                            }
                        }
                        .padding(.top, 8)

                    } else {
                        // 速查模式：完整面板（内联爻辞/卦辞/错综互）
                        HexagramPanelView(hex: org, onFlip: { store.flipOriginal(line: $0) })
                    }
                } else if let msg = store.errorMessage {
                    Text("出错了：\(msg)").foregroundStyle(.red)
                } else {
                    ProgressView()
                }
            }
            .padding(40)
        }
        .onAppear { store.load() }
    }
}

/// 一个卦的面板。两种模式：
/// - 完整版(compact=false)：卦名 + 六爻+爻辞 + 用九/用六 + 卦辞 + 错综互（速查用）。
/// - 紧凑版(compact=true)：只有卦名 + 六爻；点卦名弹浮窗看卦辞/爻辞（变卦模式用）。
/// onFlip 把被点的爻位(1-6)回调给外面。
struct HexagramPanelView: View {
    let hex: Hexagram
    var compact: Bool = false
    var changingLines: Set<Int> = []     // 动爻下标(0-5)
    var showArrow: Bool = false          // 动爻右侧是否画 →（本卦为 true）
    let onFlip: (Int) -> Void

    @State private var showDetail = false   // 紧凑版：卦名点开的浮窗

    var body: some View {
        VStack(spacing: 12) {
            // 卦名（紧凑版可点开浮窗看卦辞/爻辞）
            Text(hex.name).font(.largeTitle).bold()
                .contentShape(Rectangle())
                .onTapGesture { if compact { showDetail = true } }
                .popover(isPresented: $showDetail) { HexagramDetailView(hex: hex) }

            // 六爻（点击 = 变爻）
            VStack(spacing: 4) {
                ForEach((0..<hex.lines.count).reversed(), id: \.self) { index in
                    HStack(spacing: 12) {
                        LineView(isYang: hex.lines[index] == 1)
                            .onTapGesture { onFlip(index + 1) }

                        // 动爻箭头（只有 →，且只在本卦侧）
                        if showArrow {
                            Text(changingLines.contains(index) ? "→" : "")
                                .font(.title3).foregroundStyle(.orange).frame(width: 22)
                        }

                        // 完整版才内联爻辞
                        if !compact, index < hex.hexagramText.lines.count {
                            Text(hex.hexagramText.lines[index])
                                .font(.title3).frame(maxWidth: 320, alignment: .leading)
                        }
                    }
                    .frame(height: 44)
                }
            }

            // 完整版才显示：用九/用六、卦辞、错综互
            if !compact {
                Text(hex.hexagramText.lines.count == 7 ? hex.hexagramText.lines[6] : "")
                    .font(.title3).frame(height: 14)
                Text("卦辞：\(hex.hexagramText.still)").font(.title2)
                DerivedRow(hex: hex).padding(.top, 12)
            }
        }
    }
}

/// 错 / 综 / 互 三个小卦一排（点各自弹 popover）。
struct DerivedRow: View {
    let hex: Hexagram
    var body: some View {
        HStack(spacing: 36) {
            ForEach(hex.derived) { d in
                DerivedHexagramCell(derived: d)
            }
        }
    }
}

/// 单根爻的画法：阳 = 一整条；阴 = 中间断开两段。
struct LineView: View {
    let isYang: Bool

    var body: some View {
        HStack(spacing: 12) {
            if isYang {
                Rectangle().frame(width: 172, height: 26)
            } else {
                Rectangle().frame(width: 80, height: 26)
                Rectangle().frame(width: 80, height: 26)
            }
        }
        .frame(width: 180)                 // 固定总宽，阴阳两种对齐
        .contentShape(Rectangle())         // 整行(含阴爻中间空隙)都能点
    }
}

// 用于互卦、综卦、错卦的小号【单爻】
struct MiniLine: View {
    let isYang: Bool
    var body: some View {
        HStack(spacing: 6) {
            if isYang {
                Rectangle().frame(width: 60, height: 8)
            } else {
                Rectangle().frame(width: 27, height: 8)
                Rectangle().frame(width: 27, height: 8)
            }
        }
        .frame(width: 60)
    }
}

/// 用于互卦、综卦、错卦的小号【整卦图】：六根 MiniLine 自下而上叠起来。
struct MiniHexagram: View {
    let lines: [Int]            // lines[0] = 初爻(最下)
    var body: some View {
        VStack(spacing: 4) {
            ForEach((0..<lines.count).reversed(), id: \.self) { i in
                MiniLine(isYang: lines[i] == 1)
            }
        }
    }
}

/// 一个衍生卦的小卡片：卦名 + 小卦图 + 类型标签；点自己弹出详情 popover。
struct DerivedHexagramCell: View {
    let derived: DerivedHexagram
    @State private var showing = false          // 本 cell 自己的弹窗开关

    var body: some View {
        VStack(spacing: 8) {
            Text(derived.name).font(.headline)        // 卦名在上
            MiniHexagram(lines: derived.lines)         // 卦图在中
            Text(derived.label)                        // 错/综/互 在下
                .font(.caption)
                .foregroundStyle(.secondary)
        }
        .contentShape(Rectangle())                     // 整块可点
        .onTapGesture { showing = true }               // 点→弹出自己的 popover
        .popover(isPresented: $showing) {              // 从这个小卦冒出来；点别处关闭
            DerivedDetailView(derived: derived)
        }
    }
}

/// 衍生卦详情弹窗：卦名、卦辞、带爻题前缀的爻辞（初爻在最前）。
struct DerivedDetailView: View {
    let derived: DerivedHexagram

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("\(derived.label)：\(derived.name)")
                .font(.title).bold()
                .frame(maxWidth: .infinity, alignment: .center)

            Text("卦辞：\(derived.text.still)")
                .font(.title3)

            Divider()

            ForEach(0..<derived.text.lines.count, id: \.self) { i in
                if i < 6 {
                    Text("\(yaoTitle(index: i, isYang: derived.lines[i] == 1))　\(derived.text.lines[i])")
                } else {
                    Text(derived.text.lines[i])
                }
            }
        }
        .padding(28)
        .frame(minWidth: 320)
    }
}

/// 本卦 / 变卦 的详情浮窗（变卦模式点卦名弹出）：卦名、卦辞、带爻题的爻辞。
struct HexagramDetailView: View {
    let hex: Hexagram

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text(hex.name).font(.title).bold()
                .frame(maxWidth: .infinity, alignment: .center)

            Text("卦辞：\(hex.hexagramText.still)").font(.title3)

            Divider()

            ForEach(0..<hex.hexagramText.lines.count, id: \.self) { i in
                if i < 6 {
                    Text("\(yaoTitle(index: i, isYang: hex.lines[i] == 1))　\(hex.hexagramText.lines[i])")
                } else {
                    Text(hex.hexagramText.lines[i])
                }
            }
        }
        .padding(28)
        .frame(minWidth: 320)
    }
}

/// 根据爻位(0=初…5=上)和阴阳，拼出爻题：初九 / 九二 / 上六 …
func yaoTitle(index: Int, isYang: Bool) -> String {
    let yinYang = isYang ? "九" : "六"
    switch index {
    case 0: return "初\(yinYang)"                       // 初九 / 初六
    case 5: return "上\(yinYang)"                       // 上九 / 上六
    default: return "\(yinYang)\(["二","三","四","五"][index - 1])" // 九二 / 六三…
    }
}
