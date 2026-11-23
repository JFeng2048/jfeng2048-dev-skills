import Foundation

/// token 存储抽象
///
/// 默认实现用 UserDefaults（简单、无依赖）；
/// 生产环境建议换成 Keychain 实现，只需替换 AppContainer 里的一行。
protocol TokenStorage: AnyObject {
    var token: String? { get set }
    func clear()
}

final class UserDefaultsTokenStorage: TokenStorage {

    private let key = "app.access_token"
    private let defaults: UserDefaults

    init(defaults: UserDefaults = .standard) {
        self.defaults = defaults
    }

    var token: String? {
        get { defaults.string(forKey: key) }
        set {
            if let newValue, !newValue.isEmpty {
                defaults.set(newValue, forKey: key)
            } else {
                defaults.removeObject(forKey: key)
            }
        }
    }

    func clear() {
        defaults.removeObject(forKey: key)
    }
}
