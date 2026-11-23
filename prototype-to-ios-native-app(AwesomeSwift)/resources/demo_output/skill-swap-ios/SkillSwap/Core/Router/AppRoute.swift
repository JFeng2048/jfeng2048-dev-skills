import Foundation

/// 应用路由
///
/// 约定：
/// - 带参数用关联值，禁止拼字符串 URL；
/// - 新增 case 必须同时在 `RootView.destination(for:)` 中处理。
enum AppRoute: Hashable {
    case detail(id: String)
    case mine
}
