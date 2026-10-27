import SwiftUI

/// 皇极经世页。公历/农历输入 → huangji 排盘（会/运/世/十年/年）+ 四柱。
/// 农历月/日滚轮按"某农历年的月份结构"来（含闰月、每月天数），年份滚动停下重新加载。
/// 公历、农历各记各的，不互相同步。
struct HuangjiView: View {
    @State private var isLunar = false
    @State private var yearStart = "lichun"   // 岁首：daxue/dongzhi/lichun，默认立春
    @State private var dayRule = "shigua"      // 日卦起法：yuegua/shigua，默认世卦起

    // 公历
    @State private var solarYear: Int
    @State private var solarMonth: Int
    @State private var solarDay: Int
    // 共享时间
    @State private var hour: Int
    @State private var minute: Int
    // 农历
    @State private var lunarYear: Int
    @State private var lunarMonths: [LunarMonth] = []
    @State private var lunarMonthIndex: Int = 0     // 下标(闰月会让月号重复，所以绑下标)
    @State private var lunarDay: Int = 1

    @State private var result: HuangjiPaipan?
    @State private var errorMessage: String?

    private let client = DivinationClient()

    init() {
        let c = Calendar.current.dateComponents([.year, .month, .day, .hour, .minute], from: Date())
        _solarYear  = State(initialValue: c.year   ?? 2026)
        _solarMonth = State(initialValue: c.month  ?? 1)
        _solarDay   = State(initialValue: c.day    ?? 1)
        _hour       = State(initialValue: c.hour   ?? 0)
        _minute     = State(initialValue: c.minute ?? 0)
        _lunarYear  = State(initialValue: c.year   ?? 2026)
    }

    /// 公历日范围（按选中的年月）。
    private var solarDayRange: [Int] {
        let cal = Calendar.current
        if let d = cal.date(from: DateComponents(year: solarYear, month: solarMonth)),
           let r = cal.range(of: .day, in: .month, for: d) { return Array(r) }
        return Array(1...31)
    }

    /// 当前农历月天数（下标无效时给 30 兜底）。
    private var currentLunarMonthDays: Int {
        lunarMonths.indices.contains(lunarMonthIndex) ? lunarMonths[lunarMonthIndex].days : 30
    }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 24) {
                Text("皇极经世").font(.largeTitle).bold()

                // 公历 / 农历 切换
                Picker("", selection: $isLunar) {
                    Text("公历日期").tag(false)
                    Text("农历日期").tag(true)
                }
                .pickerStyle(.segmented)
                .frame(maxWidth: 300)

                // 岁首 + 日卦起法（下拉菜单）
                HStack(spacing: 20) {
                    Picker("岁首", selection: $yearStart) {
                        Text("大雪").tag("daxue")
                        Text("冬至").tag("dongzhi")
                        Text("立春").tag("lichun")
                    }
                    Picker("日卦起法", selection: $dayRule) {
                        Text("以月卦起").tag("yuegua")
                        Text("以世卦起").tag("shigua")
                    }
                }
                .pickerStyle(.menu)
                .fixedSize()

                // 滚轮（上下各露一格，visibleRows: 3）+ 计算按钮（在滚轮右边）
                HStack(alignment: .center, spacing: 24) {
                    HStack(spacing: 10) {
                        if isLunar {
                            WheelPicker(title: "年", values: Array(1...3000), selection: $lunarYear, visibleRows: 3).frame(width: 96)
                            WheelPicker(title: "月",
                                        values: Array(0..<max(lunarMonths.count, 1)),
                                        format: { lunarMonths.indices.contains($0) ? lunarMonths[$0].label : "—" },
                                        selection: $lunarMonthIndex, visibleRows: 3).frame(width: 88)
                            WheelPicker(title: "日",
                                        values: Array(1...currentLunarMonthDays),
                                        format: { lunarDayName($0) },
                                        selection: $lunarDay, visibleRows: 3).frame(width: 88)
                        } else {
                            WheelPicker(title: "年", values: Array(1...3000), selection: $solarYear, visibleRows: 3).frame(width: 96)
                            WheelPicker(title: "月", values: Array(1...12),
                                        format: { "\($0)月" }, selection: $solarMonth, visibleRows: 3).frame(width: 72)
                            WheelPicker(title: "日", values: solarDayRange,
                                        format: { "\($0)日" }, selection: $solarDay, visibleRows: 3).frame(width: 72)
                        }
                        WheelPicker(title: "时", values: Array(0...23), selection: $hour, visibleRows: 3).frame(width: 72)
                        WheelPicker(title: "分", values: Array(0...59), selection: $minute, visibleRows: 3).frame(width: 72)
                    }

                    Button("计算") { paipan() }
                        .buttonStyle(.borderedProminent)
                        .controlSize(.large)
                }
                .frame(maxWidth: .infinity)          // 滚轮+按钮整排居中

                if let errorMessage {
                    Text(errorMessage).foregroundStyle(.red).font(.footnote)
                }

                if let r = result {
                    resultSection(r)
                }
            }
            .padding(40)
            .frame(maxWidth: .infinity, alignment: .leading)
            .onChange(of: isLunar) { _, now in if now { enterLunarMode() } }      // 切到农历：定默认 + 加载月份
            .onChange(of: lunarYear) { _, _ in if isLunar { refreshLunarMonths() } } // 年份停下：重载月份
            .onChange(of: lunarMonthIndex) { _, _ in if lunarDay > currentLunarMonthDays { lunarDay = currentLunarMonthDays } }
            .onChange(of: solarMonth) { _, _ in clampSolarDay() }
            .onChange(of: solarYear) { _, _ in clampSolarDay() }
        }
    }

    // MARK: - 农历加载

    /// 切到农历：把当前公历换算成农历默认值，并加载该农历年的月份结构。
    private func enterLunarMode() {
        if let sl = client.solarToLunar(year: solarYear, month: solarMonth, day: solarDay, hour: hour, minute: minute) {
            lunarYear = sl.lunarYear
            lunarMonths = client.lunarMonths(year: sl.lunarYear) ?? []
            lunarMonthIndex = lunarMonths.firstIndex(where: { $0.month == sl.lunarMonth && $0.isLeap == sl.isLeap }) ?? 0
            lunarDay = min(sl.lunarDay, currentLunarMonthDays)
        } else {
            lunarMonths = client.lunarMonths(year: lunarYear) ?? []
        }
    }

    /// 农历年份变化：重载月份结构，并把越界的月/日收回。
    private func refreshLunarMonths() {
        lunarMonths = client.lunarMonths(year: lunarYear) ?? []
        if lunarMonthIndex >= lunarMonths.count { lunarMonthIndex = max(0, lunarMonths.count - 1) }
        if lunarDay > currentLunarMonthDays { lunarDay = currentLunarMonthDays }
    }

    private func clampSolarDay() {
        if solarDay > solarDayRange.count { solarDay = solarDayRange.count }
    }

    // MARK: - 计算

    private func paipan() {
        let y: Int, m: Int, d: Int, lun: Bool, leap: Bool
        if isLunar {
            guard lunarMonths.indices.contains(lunarMonthIndex) else {
                errorMessage = "农历月份未加载"; return
            }
            let mon = lunarMonths[lunarMonthIndex]
            y = lunarYear; m = mon.month; d = lunarDay; lun = true; leap = mon.isLeap
        } else {
            y = solarYear; m = solarMonth; d = solarDay; lun = false; leap = false
        }

        guard let h = client.huangji(year: y, month: m, day: d, hour: hour, minute: minute,
                                     isLunar: lun, isLeap: leap,
                                     yearStart: yearStart, dayRule: dayRule) else {
            errorMessage = "计算失败：引擎无响应"; return
        }
        guard let hui = client.lookup(h.hui.value),
              let yun = client.lookup(h.yun.value),
              let shi = client.lookup(h.shi.value),
              let decade = client.lookup(h.decade.value),
              let annual = client.lookup(h.annual.value),
              let month = client.lookup(h.month.value),
              let day = client.lookup(h.day.value),
              let hour = client.lookup(h.hour.value) else {
            errorMessage = "计算失败：取卦数据出错"; return
        }
        // 崔氏易林：各层卦变的林辞；标题用短名"某卦之某卦"（如 同人之离）
        func yl(_ from: Int, _ to: Int) -> YilinLine {
            YilinLine(title: "\(hexShortName(from))之\(hexShortName(to))",
                      text: client.yilin(org: from, chg: to))
        }
        let yilin = HuangjiYilin(
            shiToAnnual:    yl(h.shi.value,    h.annual.value),
            decadeToAnnual: yl(h.decade.value, h.annual.value),
            annualToMonth:  yl(h.annual.value, h.month.value),
            monthToDay:     yl(h.month.value,  h.day.value),
            dayToHour:      yl(h.day.value,    h.hour.value)
        )

        result = HuangjiPaipan(
            ganzhi: h.ganzhi,
            huiIndex: h.hui.index, yunIndex: h.yun.index, shiIndex: h.shi.index,
            inputSolar: h.inputSolar,
            bazi: baziFrom(h.inputSolar),
            hui: hui, yun: yun, shi: shi, decade: decade, annual: annual,
            month: month, day: day, hour: hour,
            yilin: yilin
        )
        errorMessage = nil
    }

    /// 从 "YYYY-MM-DD HH:MM" 解析出公历并取四柱。
    private func baziFrom(_ solar: String) -> BaziResult? {
        let parts = solar.split(separator: " ")
        guard parts.count == 2 else { return nil }
        let d = parts[0].split(separator: "-")
        let t = parts[1].split(separator: ":")
        guard d.count == 3, t.count == 2,
              let y = Int(d[0]), let mo = Int(d[1]), let dd = Int(d[2]),
              let hh = Int(t[0]), let mi = Int(t[1]) else { return nil }
        return client.bazi(year: y, month: mo, day: dd, hour: hh, minute: mi)
    }

    // MARK: - 结果区

    @ViewBuilder
    private func resultSection(_ r: HuangjiPaipan) -> some View {
        Divider()

        VStack(alignment: .leading, spacing: 4) {
            Text("公历：\(r.inputSolar)").font(.title2)       // 比八字小、比正文大
            if let b = r.bazi {
                Text("农历：\(b.lunar)").font(.title2)
            }
            Text("皇极定位：第 \(r.huiIndex) 会 · 第 \(r.yunIndex) 运 · 第 \(r.shiIndex) 世")
                .font(.title2)
        }
        .frame(maxWidth: .infinity, alignment: .leading)

        if let b = r.bazi {
            BaziPillarsView(pillars: [b.year, b.month, b.day, b.hour])
                .frame(maxWidth: .infinity, alignment: .leading)
        }

        // 竖排各层卦；每行主卦+互综错横滑；对应易林放在该卦下方
        VStack(alignment: .leading, spacing: 18) {
            guaBlock("会卦", r.hui)
            guaBlock("运卦", r.yun)
            guaBlock("世卦", r.shi)
            guaBlock("旬卦", r.decade)
            guaBlock("年卦", r.annual, yilins: [r.yilin.shiToAnnual, r.yilin.decadeToAnnual])
            guaBlock("月卦", r.month, yilins: [r.yilin.annualToMonth])
            guaBlock("日卦", r.day,   yilins: [r.yilin.monthToDay])
            guaBlock("时卦", r.hour,  yilins: [r.yilin.dayToHour])
        }
    }

    /// 一个卦块：该卦行 +（可选）放在它下面的易林（卦变名 + 林辞）。
    @ViewBuilder
    private func guaBlock(_ label: String, _ hexagram: Hexagram?, yilins: [YilinLine] = []) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            GuaRow(label: label, hexagram: hexagram)
            ForEach(yilins) { y in
                VStack(alignment: .leading, spacing: 2) {
                    Text(y.title).font(.subheadline).bold()
                    Text(y.text ?? "—").font(.headline)       // 易林字号=卦名
                }
                .padding(.leading, 8)
            }
        }
    }
}

/// 一次皇极排盘的结果（本地持有）。卦都已 lookup 成完整 Hexagram，便于画图/看详情。
struct HuangjiPaipan {
    let ganzhi: String
    let huiIndex: Int
    let yunIndex: Int
    let shiIndex: Int
    let inputSolar: String
    let bazi: BaziResult?
    let hui: Hexagram
    let yun: Hexagram
    let shi: Hexagram
    let decade: Hexagram
    let annual: Hexagram
    let month: Hexagram
    let day: Hexagram
    let hour: Hexagram
    let yilin: HuangjiYilin
}

/// 皇极各层卦变的崔氏易林。
struct HuangjiYilin {
    let shiToAnnual: YilinLine      // 世卦之年卦
    let decadeToAnnual: YilinLine   // 旬卦之年卦
    let annualToMonth: YilinLine    // 年卦之月卦
    let monthToDay: YilinLine       // 月卦之日卦
    let dayToHour: YilinLine        // 日卦之时卦
}

/// 一条易林：卦变名（如"同人之离"）+ 林辞。
struct YilinLine: Identifiable {
    let title: String
    let text: String?
    var id: String { title }
}

/// 64 卦简体短名（按卦码 value=0坤…63乾），用于"某卦之某卦"的卦变名。
private let hexShortNames: [String] = [
    "坤", "剥", "比", "观", "豫", "晋", "萃", "否", "谦", "艮", "蹇", "渐", "小过", "旅", "咸", "遁",
    "师", "蒙", "坎", "涣", "解", "未济", "困", "讼", "升", "蛊", "井", "巽", "恒", "鼎", "大过", "姤",
    "复", "颐", "屯", "益", "震", "噬嗑", "随", "无妄", "明夷", "贲", "既济", "家人", "丰", "离", "革", "同人",
    "临", "损", "节", "中孚", "归妹", "睽", "兑", "履", "泰", "大畜", "需", "小畜", "大壮", "大有", "夬", "乾",
]
func hexShortName(_ value: Int) -> String {
    (0..<hexShortNames.count).contains(value) ? hexShortNames[value] : "?"
}

/// 农历日名：初一…初十、十一…十九、二十、廿一…廿九、三十。
func lunarDayName(_ d: Int) -> String {
    let units = ["", "一", "二", "三", "四", "五", "六", "七", "八", "九", "十"]
    switch d {
    case 1...10:  return "初" + units[d]
    case 11...19: return "十" + units[d - 10]
    case 20:      return "二十"
    case 21...29: return "廿" + units[d - 20]
    case 30:      return "三十"
    default:      return "\(d)"
    }
}

/// 可调大小的卦象图（阳=整条，阴=断开两段）。皇极用，约易经速查本卦的 2/3。
struct HexagramGlyph: View {
    let lines: [Int]               // lines[0]=初爻(最下)
    var width: CGFloat = 120
    var lineHeight: CGFloat = 17
    private let gap: CGFloat = 8   // 阴爻中间空隙

    var body: some View {
        VStack(spacing: 6) {
            ForEach((0..<lines.count).reversed(), id: \.self) { i in
                if lines[i] == 1 {
                    RoundedRectangle(cornerRadius: 3).frame(width: width, height: lineHeight)
                } else {
                    HStack(spacing: gap) {
                        RoundedRectangle(cornerRadius: 3).frame(width: (width - gap) / 2, height: lineHeight)
                        RoundedRectangle(cornerRadius: 3).frame(width: (width - gap) / 2, height: lineHeight)
                    }
                    .frame(width: width)
                }
            }
        }
    }
}

/// 一行：主卦 + 它的 互/综/错，横向滚动（小屏可左右滑）。主卦 nil 时只显示占位主卦。
struct GuaRow: View {
    let label: String
    let hexagram: Hexagram?

    var body: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(alignment: .top, spacing: 16) {
                MainGuaCard(label: label, hexagram: hexagram)
                if let hex = hexagram {
                    ForEach(hex.derived) { d in
                        DerivedGuaCard(derived: d)
                    }
                }
            }
            .padding(.horizontal, 4)
        }
    }
}

/// 主卦卡：类型标签 + 卦象图 + 卦名；点开看卦详情。nil 时显示占位"待接入"。
struct MainGuaCard: View {
    let label: String
    let hexagram: Hexagram?
    @State private var show = false

    var body: some View {
        VStack(spacing: 8) {
            Text(label).font(.subheadline).bold()
            if let hex = hexagram {
                HexagramGlyph(lines: hex.lines)
                Text(hex.name).font(.headline)
            } else {
                HexagramGlyph(lines: [0, 0, 0, 0, 0, 0]).opacity(0.12)
                Text("待接入").font(.footnote).foregroundStyle(.secondary)
            }
        }
        .frame(width: 150)
        .contentShape(Rectangle())
        .onTapGesture { if hexagram != nil { show = true } }
        .popover(isPresented: $show) {
            if let hex = hexagram {
                HexagramDetailView(hex: hex).presentationCompactAdaptation(.popover)
            }
        }
    }
}

/// 衍生卦卡（互/综/错）：类型标签 + 卦象图 + 卦名；点开看爻辞。
struct DerivedGuaCard: View {
    let derived: DerivedHexagram
    @State private var show = false

    var body: some View {
        VStack(spacing: 8) {
            Text(derived.label).font(.subheadline).bold()
            HexagramGlyph(lines: derived.lines)
            Text(derived.name).font(.headline)
        }
        .frame(width: 150)
        .contentShape(Rectangle())
        .onTapGesture { show = true }
        .popover(isPresented: $show) {
            DerivedDetailView(derived: derived).presentationCompactAdaptation(.popover)
        }
    }
}
