import Foundation
import Combine

/// 我的页面 ViewModel：目前只负责退出登录
///
/// 后续接入用户信息接口时在这里加 `loadProfile()`，不要在 View 里发请求。
@MainActor
final class MineViewModel: ObservableObject {

    private let session: SessionStore

    init(session: SessionStore) {
        self.session = session
    }

    func logout() {
        session.signOut()
    }
}
