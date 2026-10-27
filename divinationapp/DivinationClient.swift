import Foundation

/// 梅花排盘结果（对应后端 meihua 命令的 JSON）。
struct MeihuaResult: Codable {
    struct Gua: Codable { let value: Int; let name: String }
    let benGua: Gua       // ben_gua
    let movingLine: Int   // moving_line，动爻 1-6
    let bianGua: Gua      // bian_gua
}

/// 八字排盘结果（对应后端 bazi 命令的 JSON，只取要显示的字段）。
struct BaziResult: Codable {
    let inputTime: String   // input_time，公历
    let lunar: String       // 农历
    let year: String        // 四柱：年柱
    let month: String       // 月柱
    let day: String         // 日柱
    let hour: String        // 时柱
}

/// 皇极经世排盘结果（对应后端 huangji 命令的 JSON）。
/// 每个卦只有 value+name；要画卦象/看爻辞，拿 value 调 lookup。
struct HuangjiResult: Codable {
    struct Gua: Codable { let value: Int; let name: String }
    struct Hui: Codable { let index: Int; let branch: String; let value: Int; let name: String }
    struct Yun: Codable { let index: Int; let inHui: Int; let stem: String; let value: Int; let name: String }
    struct Shi: Codable { let index: Int; let branch: String; let value: Int; let name: String }
    struct Indexed: Codable { let index: Int; let value: Int; let name: String }   // 日卦(无地支)

    let year: Int            // 皇极年
    let ganzhi: String       // 年干支
    let hui: Hui             // 会卦
    let yun: Yun             // 运卦
    let shi: Shi             // 世卦
    let decade: Gua          // 旬卦(原十年卦)
    let annual: Gua          // 年卦
    let month: Hui           // 月卦 {index,branch,value,name}
    let day: Indexed         // 日卦 {index,value,name}
    let hour: Hui            // 时卦 {index,branch,value,name}
    let inputSolar: String   // input_solar，实际用的公历时刻 "YYYY-MM-DD HH:MM"
}

/// 公历→农历 结果（对应后端 solar_to_lunar）。
struct SolarToLunarResult: Codable {
    let lunarYear: Int      // lunar_year
    let lunarMonth: Int     // lunar_month(1-12)
    let isLeap: Bool        // is_leap
    let lunarDay: Int       // lunar_day
}

/// 一个农历月（对应后端 lunar_months 的每一项）。
struct LunarMonth: Codable, Identifiable {
    let month: Int          // 1-12
    let isLeap: Bool        // is_leap
    let days: Int           // 该月天数(29/30)
    let label: String       // "正月"/"闰冬月"…
    var id: String { label }  // 同一年内 label 唯一
}

/// 某农历年的月份结构（对应后端 lunar_months）。
struct LunarMonthsResult: Codable {
    let year: Int
    let months: [LunarMonth]
}

/// 皇极日历·一天（对应后端 huangji_calendar 的 days[] 每项）。
struct CalendarDay: Codable, Identifiable {
    struct Gua: Codable { let value: Int; let name: String }
    let solarDay: Int        // solar_day 公历日
    let weekday: Int         // 0=周日 … 6=周六（对齐 日..六 列）
    let lunar: String        // 农历中文，如 "八月廿一"
    let ganzhi: String       // 日干支
    let jieqi: String?       // 当天节气名或 nil
    let monthGua: Gua        // month_gua 该天所属皇极月的月卦
    let dayGua: Gua          // day_gua 日卦
    var id: Int { solarDay }
}

/// 皇极日历·一整月（对应后端 huangji_calendar）。
struct CalendarMonth: Codable {
    let solarYear: Int       // solar_year
    let solarMonth: Int      // solar_month
    let days: [CalendarDay]
}

/// 无状态小帮手：包一下 engine + JSON 解码。不持有状态、不是 store。
/// 时间起卦用它一次性取数据，结果存进视图自己的 @State。
struct DivinationClient {
    private let engine: DivinationEngine = PythonEngine()

    func lookup(_ value: Int) -> Hexagram? {
        decode(send(["cmd": "lookup", "value": value]))
    }

    func meihua(year: Int, month: Int, day: Int, hour: Int, minute: Int) -> MeihuaResult? {
        decode(send(["cmd": "meihua", "year": year, "month": month,
                     "day": day, "hour": hour, "minute": minute]))
    }

    func bazi(year: Int, month: Int, day: Int, hour: Int, minute: Int) -> BaziResult? {
        decode(send(["cmd": "bazi", "year": year, "month": month,
                     "day": day, "hour": hour, "minute": minute]))
    }

    func yilin(org: Int, chg: Int) -> String? {
        let r: YilinResult? = decode(send(["cmd": "yilin", "org_value": org, "chg_value": chg]))
        return r?.text
    }

    func huangji(year: Int, month: Int, day: Int, hour: Int, minute: Int,
                 isLunar: Bool, isLeap: Bool,
                 yearStart: String, dayRule: String) -> HuangjiResult? {
        decode(send(["cmd": "huangji_full", "year": year, "month": month, "day": day,
                     "hour": hour, "minute": minute, "is_lunar": isLunar, "is_leap": isLeap,
                     "year_start": yearStart, "day_rule": dayRule]))
    }

    /// 皇极日历：给公历年月，返回整月每天的 干支/节气/日卦/月卦。
    func huangjiCalendar(year: Int, month: Int, yearStart: String, dayRule: String) -> CalendarMonth? {
        decode(send(["cmd": "huangji_calendar", "year": year, "month": month,
                     "year_start": yearStart, "day_rule": dayRule]))
    }

    /// 公历 → 农历（定农历默认值）。
    func solarToLunar(year: Int, month: Int, day: Int, hour: Int, minute: Int) -> SolarToLunarResult? {
        decode(send(["cmd": "solar_to_lunar", "year": year, "month": month, "day": day,
                     "hour": hour, "minute": minute]))
    }

    /// 某农历年的月份结构（含闰月、每月天数）。
    func lunarMonths(year: Int) -> [LunarMonth]? {
        let r: LunarMonthsResult? = decode(send(["cmd": "lunar_months", "year": year]))
        return r?.months
    }

    // MARK: - 私有：发请求 + 泛型解码

    private func send(_ request: [String: Any]) -> String? {
        guard let data = try? JSONSerialization.data(withJSONObject: request),
              let req = String(data: data, encoding: .utf8) else { return nil }
        return engine.dispatch(req)
    }

    private func decode<T: Decodable>(_ json: String?) -> T? {
        guard let json else { return nil }
        let dec = JSONDecoder()
        dec.keyDecodingStrategy = .convertFromSnakeCase
        return try? dec.decode(T.self, from: Data(json.utf8))
    }
}
