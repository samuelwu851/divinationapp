import SwiftUI

struct ContentView: View {
    // @State 持有我们的状态中心；因为 IChingStore 标了 @Observable，
    // 它内部属性一变，界面自动重绘。
    @State private var store = IChingStore()

    var body: some View {
        VStack(spacing: 18) {
            if let hex = store.hexagram {
                // 头部：卦名、卦辞、用九。彼此间距收紧到一半(12)。
                VStack(spacing: 12) {
                    Text(hex.name)                      // 卦名
                        .font(.largeTitle).bold()
                }

//                    Text(hex.hexagramText.still)        // 卦辞（字号还原为 title3）
//                        .font(.title2)
                    // 用九 / 用六：仅乾坤有。空爻位 + 右侧文本，与爻辞左对齐；高度固定始终占位。
//                    HStack(spacing: 16) {
//                        Color.clear.frame(width: 180, height: 1)
//                        Text(hex.hexagramText.lines.count == 7 ? hex.hexagramText.lines[6] : "")
//                            .font(.title3)
//                            .frame(maxWidth: 320, alignment: .leading)
//                    }
//                    .frame(height: 16).padding(.top, 6)
//                }
                
                // 六爻：从上往下画 上爻→初爻。
                // lines[0] 是初爻（最下），所以把下标倒序，让 index 0 排最后。
                VStack(spacing: 4) {
                    ForEach((0..<hex.lines.count).reversed(), id: \.self) { index in
                        HStack(spacing: 16) {                 // 横向：左爻、右爻辞
                            LineView(isYang: hex.lines[index] == 1)
                                .onTapGesture {
                                    store.flip(line: index + 1)   // 下标0 → 第1爻(初爻)
                                }
                            if index < hex.hexagramText.lines.count {
                                Text(hex.hexagramText.lines[index])
                                    .font(.title3)                       // 爻辞字体大一点
                                    .frame(maxWidth: 320, alignment: .leading)
                            }
                        }
                        .frame(height: 44)                               // 固定行高：爻间距不再随爻辞长短改变
                    }
                }
                HStack(spacing: 16) {
                    Color.clear.frame(width: 180, height: 1)
                    Text(hex.hexagramText.lines.count == 7 ? hex.hexagramText.lines[6] : "")
                        .font(.title3)
                        .frame(maxWidth: 320, alignment: .leading)
                }.frame(height: 14).padding(.bottom, 6)
                
                Text("卦辞：\(hex.hexagramText.still)")        // 卦辞（字号还原为 title3）
                    .font(.title2)

                // 错 综 互：小图，卦名在上、卦图在中、类型在下，三卦并排
                HStack(spacing: 36) {
                    ForEach(hex.derived) { d in
                        DerivedHexagramCell(derived: d)   // 每个小卦自带 popover
                    }
                }
                .padding(.top, 12)
                


            } else if let msg = store.errorMessage {
                Text("出错了：\(msg)").foregroundStyle(.red)
            } else {
                ProgressView()                      // 还没加载时转圈
            }
        }
        .padding(40)
        .onAppear { store.load() }                  // 界面一出现就加载当前卦
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
/// 用 popover 呈现，点别处即关闭，无需按钮。
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

            // 爻辞：自下而上，初爻(下标0)在最前，带爻题前缀。
            // 乾坤会多第 7 条(下标6)=用九/用六，文本已含前缀，直接显示。
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

    /// 根据爻位(0=初…5=上)和阴阳，拼出爻题：初九 / 九二 / 上六 …
    private func yaoTitle(index: Int, isYang: Bool) -> String {
        let yinYang = isYang ? "九" : "六"
        switch index {
        case 0: return "初\(yinYang)"                       // 初九 / 初六
        case 5: return "上\(yinYang)"                       // 上九 / 上六
        default: return "\(yinYang)\(["二","三","四","五"][index - 1])" // 九二 / 六三…
        }
    }
}
