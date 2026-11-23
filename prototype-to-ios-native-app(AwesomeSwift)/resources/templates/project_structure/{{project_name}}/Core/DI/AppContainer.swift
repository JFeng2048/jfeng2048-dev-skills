import Foundation
import SwiftData

/// 组合根（唯一依赖装配点）
///
/// 页面通过构造器接收依赖，不直接访问单例；
/// 需要替换实现（如测试用的假 Repository）时只改这里。
@MainActor
final class AppContainer: ObservableObject {

    let modelContainer: ModelContainer
    let tokenStorage: TokenStorage
    let sessionStore: SessionStore
    let apiClient: APIClient
    let skillRepository: SkillRepository
    let authRepository: AuthRepository

    init(modelContainer: ModelContainer = SwiftDataStack.shared) {
        self.modelContainer = modelContainer

        // 存储
        let storage = UserDefaultsTokenStorage()
        self.tokenStorage = storage
        self.sessionStore = SessionStore(storage: storage)

        // 网络
        let client = APIClient(tokenStorage: storage)
        self.apiClient = client

        // 数据仓库
        self.skillRepository = DefaultSkillRepository(
            client: client,
            context: modelContainer.mainContext
        )
        self.authRepository = DefaultAuthRepository(client: client)
    }
}
