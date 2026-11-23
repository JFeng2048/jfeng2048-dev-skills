import Foundation

/// 运行时配置
///
/// 唯一读取 `Info.plist` 的入口；plist 里的值来自 `Configs/*.xcconfig`。
/// 页面与 ViewModel 不要直接读 Bundle。
enum AppConfig {

    /// 列表分页大小
    static let pageSize = 10

    /// 是否使用 mock 数据（Debug 默认 YES）
    static var useMock: Bool {
        infoString("USE_MOCK").uppercased() == "YES"
    }

    /// 接口根地址，末尾必须带 `/`
    static var apiBaseURL: URL {
        let raw = infoString("API_BASE_URL")
        if !raw.isEmpty, let url = URL(string: raw) {
            return url
        }
        // 保底值：xcconfig 未正确注入时不至于崩溃
        return URL(string: "https://dev-api.example.com/")!
    }

    private static func infoString(_ key: String) -> String {
        (Bundle.main.object(forInfoDictionaryKey: key) as? String) ?? ""
    }
}
