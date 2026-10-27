import SwiftUI

/// 跨平台滚轮选择列（Mac / iPhone / iPad 通用）。
/// macOS 没有系统滚轮，所以用 ScrollView 的"吸附滚动"自己造一个：
/// 竖向滚动、中间高亮带、滚到哪一项就选哪一项。
struct WheelPicker: View {
    let title: String
    let values: [Int]
    var format: (Int) -> String = { "\($0)" }
    @Binding var selection: Int

    var visibleRows: Int = 5                    // 可见行数(奇数，中间为选中)；3=上下各一格
    private let rowHeight: CGFloat = 36

    @State private var scrolledID: Int?

    var body: some View {
        VStack(spacing: 6) {
            Text(title).font(.caption).foregroundStyle(.secondary)

            ScrollView(.vertical, showsIndicators: false) {
                LazyVStack(spacing: 0) {
                    ForEach(values, id: \.self) { v in
                        Text(format(v))
                            .font(.title3)
                            .frame(maxWidth: .infinity)
                            .frame(height: rowHeight)
                            .foregroundStyle(v == selection ? Color.primary : .secondary)
                            .id(v)
                    }
                }
                .scrollTargetLayout()
            }
            .frame(height: rowHeight * CGFloat(visibleRows))
            // 上下留白，让首尾项也能滚到正中
            .contentMargins(.vertical, rowHeight * CGFloat(visibleRows / 2), for: .scrollContent)
            .scrollTargetBehavior(.viewAligned)
            .scrollPosition(id: $scrolledID, anchor: .center)
            .overlay(
                RoundedRectangle(cornerRadius: 8)       // 中间的选中带
                    .stroke(.quaternary, lineWidth: 1)
                    .frame(height: rowHeight)
                    .allowsHitTesting(false)
            )
            .onAppear {
                // 推迟到首次布局之后再定位，否则会被滚动视图写回的"首项"覆盖，停在顶部
                DispatchQueue.main.async { scrolledID = selection }
            }
            .onChange(of: scrolledID) { _, newValue in
                if let newValue { selection = newValue }
            }
            .onChange(of: selection) { _, newValue in
                if scrolledID != newValue { scrolledID = newValue }   // 外部(重置)改了，滚回去
            }
        }
    }
}
