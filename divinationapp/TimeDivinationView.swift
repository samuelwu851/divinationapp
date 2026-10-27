import SwiftUI

/// 时间起卦页。不用 store：本地 @State 即可——每次从菜单进来都是全新实例，自动回到选时间页。
/// 选时间：日期(年/月/日)、时间(时/分) 用跨平台滚轮 WheelPicker 滚动选择。
/// 排盘：meihua 定本卦/动爻/变卦，bazi 给左上角八字/公历/农历，lookup 取两卦完整数据，yilin 取崔氏易林。
struct TimeDivinationView: View {
    // 用分量存储，方便接滚轮
    @State private var year: Int
    @State private var month: Int
    @State private var day: Int
    @State private var hour: Int
    @State private var minute: Int

    @State private var result: PaipanResult?
    @State private var errorMessage: String?
    @State private var showDatePicker = false   // 日期滚轮浮窗
    @State private var showTimePicker = false   // 时间滚轮浮窗

    private let client = DivinationClient()

    private var dateString: String { String(format: "%04d-%02d-%02d", year, month, day) }
    private var timeString: String { String(format: "%02d:%02d", hour, minute) }

    init() {
        let c = Calendar.current.dateComponents([.year, .month, .day, .hour, .minute], from: Date())
        _year   = State(initialValue: c.year   ?? 2026)
        _month  = State(initialValue: c.month  ?? 1)
        _day    = State(initialValue: c.day    ?? 1)
        _hour   = State(initialValue: c.hour   ?? 0)
        _minute = State(initialValue: c.minute ?? 0)
    }

    /// 当前年月对应的天数(28~31)，让"日"滚轮不出现无效日期。
    private var dayRange: [Int] {
        let cal = Calendar.current
        if let d = cal.date(from: DateComponents(year: year, month: month)),
           let r = cal.range(of: .day, in: .month, for: d) {
            return Array(r)
        }
        return Array(1...31)
    }

    var body: some View {
        if let r = result {
            resultPage(r)
        } else {
            inputPage
        }
    }

    // MARK: - 选时间页（两行：日期 / 时间，滚轮选择）

    private var inputPage: some View {
        VStack(spacing: 24) {
            Text("时间起卦").font(.largeTitle).bold()

            // 两行：日期 / 时间，显示当前值；点击弹出对应的滚轮浮窗。
            VStack(spacing: 0) {
                // 日期行
                HStack {
                    Text("日期").font(.title3)
                    Spacer()
                    Text(dateString).font(.title3).foregroundStyle(.secondary)
                }
                .padding(.vertical, 14)
                .contentShape(Rectangle())
                .onTapGesture { showDatePicker = true }
                .popover(isPresented: $showDatePicker) {
                    HStack(spacing: 10) {
                        WheelPicker(title: "年", values: Array(1950...2060), selection: $year).frame(width: 96)
                        WheelPicker(title: "月", values: Array(1...12), selection: $month).frame(width: 72)
                        WheelPicker(title: "日", values: dayRange, selection: $day).frame(width: 72)
                    }
                    .padding()
                    .presentationCompactAdaptation(.popover)   // iPhone 上也用浮窗而非整屏
                }

                Divider()

                // 时间行
                HStack {
                    Text("时间").font(.title3)
                    Spacer()
                    Text(timeString).font(.title3).foregroundStyle(.secondary)
                }
                .padding(.vertical, 14)
                .contentShape(Rectangle())
                .onTapGesture { showTimePicker = true }
                .popover(isPresented: $showTimePicker) {
                    HStack(spacing: 10) {
                        WheelPicker(title: "时", values: Array(0...23), selection: $hour).frame(width: 72)
                        WheelPicker(title: "分", values: Array(0...59), selection: $minute).frame(width: 72)
                    }
                    .padding()
                    .presentationCompactAdaptation(.popover)
                }
            }
            .padding(.horizontal, 20)
            .background(.quaternary.opacity(0.3), in: RoundedRectangle(cornerRadius: 12))
            .frame(maxWidth: 420)

            Text("地点：北京（默认）").foregroundStyle(.secondary)

            if let errorMessage {
                Text(errorMessage).foregroundStyle(.red).font(.footnote)
            }

            HStack(spacing: 24) {
                Button("重置") { resetToNow() }
                Button("排盘") { paipan() }
                    .buttonStyle(.borderedProminent)
            }
            .controlSize(.large)
        }
        .padding(40)
        .frame(maxWidth: .infinity, maxHeight: .infinity)   // 居中填满，内容一屏可见
        .onChange(of: month) { _, _ in clampDay() }
        .onChange(of: year) { _, _ in clampDay() }
    }

    private func clampDay() {
        if day > dayRange.count { day = dayRange.count }   // 换月后若日超出，收回
    }

    private func resetToNow() {
        let c = Calendar.current.dateComponents([.year, .month, .day, .hour, .minute], from: Date())
        year = c.year ?? year; month = c.month ?? month; day = c.day ?? day
        hour = c.hour ?? hour; minute = c.minute ?? minute
        errorMessage = nil
    }

    // MARK: - 排盘

    private func paipan() {
        guard let m = client.meihua(year: year, month: month, day: day, hour: hour, minute: minute) else {
            errorMessage = "排盘失败：引擎无响应（检查 lunar_python 是否已打包）"; return
        }
        guard let ben = client.lookup(m.benGua.value),
              let bian = client.lookup(m.bianGua.value) else {
            errorMessage = "排盘失败：取卦数据出错"; return
        }
        result = PaipanResult(
            bazi: client.bazi(year: year, month: month, day: day, hour: hour, minute: minute),
            original: ben,
            changed: bian,
            changingLines: [m.movingLine - 1],
            yilin: client.yilin(org: m.benGua.value, chg: m.bianGua.value)
        )
    }

    // MARK: - 结果页（左上角返回 + 时间信息 + 中心卦）

    private func resultPage(_ r: PaipanResult) -> some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                // 左上角返回：回到选时间页（保留已选时间）
                Button { result = nil } label: {
                    Image(systemName: "chevron.backward").font(.title2)
                }
                .buttonStyle(.plain)

                timeInfoPanel(r.bazi)

                DualGuaView(original: r.original, changed: r.changed,
                            changingLines: r.changingLines, yilin: r.yilin,
                            readOnly: true)
                    .frame(maxWidth: .infinity)
            }
            .padding(40)
        }
    }

    /// 左上角：公历 + 农历 + 八字（四柱，按五行上色，字号同卦名）。
    private func timeInfoPanel(_ b: BaziResult?) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            if let b {
                Text(b.inputTime).font(.body)
                Text(b.lunar).font(.body)
                BaziPillarsView(pillars: [b.year, b.month, b.day, b.hour])
            } else {
                Text("八字信息获取失败").foregroundStyle(.red)
            }
        }
    }
}

/// 一次排盘的结果（时间起卦页本地持有，不入 store）。
struct PaipanResult {
    let bazi: BaziResult?
    let original: Hexagram
    let changed: Hexagram
    let changingLines: Set<Int>
    let yilin: String?
}
