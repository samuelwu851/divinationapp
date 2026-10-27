import SwiftUI

extension Color {
    /// 用 0xRRGGBB 十六进制建色。
    init(hex: UInt) {
        self.init(.sRGB,
                  red:   Double((hex >> 16) & 0xFF) / 255,
                  green: Double((hex >> 8) & 0xFF) / 255,
                  blue:  Double(hex & 0xFF) / 255,
                  opacity: 1)
    }
}

/// 全 app 背景：pattern.svg 平铺填满。
/// 底下垫一层同底色(#e9e7e2)，这样平铺产生的亚像素缝隙透出的也是同色，看不出缝。
struct PatternBackground: View {
    var body: some View {
        ZStack {
            Color(hex: 0xE9E7E2)
            Image("pattern").resizable(resizingMode: .tile)
        }
        .ignoresSafeArea()
    }
}
