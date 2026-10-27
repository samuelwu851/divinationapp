import SwiftUI
#if os(macOS)
import AppKit
#endif

/// 根视图：默认进"易经速查"，右上角 ⋯ 菜单切换两个功能。
/// 用 switch 选择页面——切走再切回"时间起卦"时会重建视图、@State 自动归零，
/// 正好满足"每次进时间起卦都回到选时间页"。
struct RootView: View {
    enum Page: String, CaseIterable {
        case iching  = "易经速查"
        case time    = "时间起卦"
        case huangji = "皇极经世"
    }

    @State private var page: Page = .iching

    var body: some View {
        NavigationStack {
            Group {
                switch page {
                case .iching:  ContentView()
                case .time:    TimeDivinationView()
                case .huangji: HuangjiView()
                }
            }
            .frame(minWidth: 480, minHeight: 520)   // 仅设一个很小的下限，允许自由缩放
            .toolbar {
                ToolbarItem(placement: .primaryAction) {
                    Menu {
                        ForEach(Page.allCases, id: \.self) { p in
                            Button(p.rawValue) { page = p }
                        }
                    } label: {
                        Image(systemName: "ellipsis.circle")
                    }
                }
            }
        }
        #if os(macOS)
        // macOS：每次启动都用默认大小、不记住上次
        .background(WindowConfigurator(width: 1000, height: 820))
        #endif
    }
}

#if os(macOS)
/// 禁用窗口状态恢复，并在启动时把窗口设回默认大小（之后用户仍可自由缩放）。
private struct WindowConfigurator: NSViewRepresentable {
    let width: CGFloat
    let height: CGFloat

    func makeNSView(context: Context) -> NSView {
        let view = NSView()
        DispatchQueue.main.async {
            guard let window = view.window else { return }
            window.isRestorable = false                                  // 不保存/恢复窗口状态
            window.setContentSize(NSSize(width: width, height: height))  // 每次启动设回默认大小
            window.center()
        }
        return view
    }

    func updateNSView(_ nsView: NSView, context: Context) {}
}
#endif
