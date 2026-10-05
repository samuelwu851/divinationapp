import Foundation

struct Hexagram: Codable{
    let value: Int
    let name: String //full name
    let order: Int
    let lines: [Int]
    let hexagramText: HexagramText
}

struct HexagramText: Codable{
    let still: String //静卦辞
    let lines: [String] //爻辞
}
