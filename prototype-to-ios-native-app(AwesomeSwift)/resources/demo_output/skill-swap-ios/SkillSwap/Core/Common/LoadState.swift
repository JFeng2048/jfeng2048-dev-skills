import Foundation

/// 页面加载状态
///
/// 用枚举替代「isLoading + isEmpty + errorMessage」多个布尔量，
/// 避免互相矛盾的状态组合。
enum LoadState<Value> {
    case idle
    case loading
    case empty
    case loaded(Value)
    case failed(String)

    /// 已加载的值（仅 loaded 有）
    var value: Value? {
        if case .loaded(let value) = self { return value }
        return nil
    }

    /// 是否处于首次加载
    var isLoading: Bool {
        if case .loading = self { return true }
        if case .idle = self { return true }
        return false
    }

    /// 错误文案（仅 failed 有）
    var errorMessage: String? {
        if case .failed(let message) = self { return message }
        return nil
    }
}
