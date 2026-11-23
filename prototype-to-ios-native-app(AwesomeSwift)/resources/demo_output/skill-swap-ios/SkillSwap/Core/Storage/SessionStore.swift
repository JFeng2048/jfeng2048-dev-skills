import Foundation
import Combine

/// 登录态：全应用唯一可信来源
///
/// `RootView` 观察 `isLoggedIn` 决定是否展示登录页；
/// 登录/退出都只改这里，不要在页面里各自记一份。
@MainActor
final class SessionStore: ObservableObject {

    @Published private(set) var isLoggedIn: Bool

    private let storage: TokenStorage

    init(storage: TokenStorage) {
        self.storage = storage
        self.isLoggedIn = !(storage.token ?? "").isEmpty
    }

    func signIn(token: String) {
        storage.token = token
        isLoggedIn = true
    }

    func signOut() {
        storage.clear()
        isLoggedIn = false
    }
}
