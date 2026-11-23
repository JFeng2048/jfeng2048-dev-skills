import SwiftUI

/// 应用入口
///
/// 只做三件事：
/// 1. 创建组合根 `AppContainer`（唯一装配点）
/// 2. 把 container 与 sessionStore 下发到视图树
/// 3. 挂载 SwiftData 容器
@main
struct {{project_name}}App: App {

    @StateObject private var container = AppContainer()

    var body: some Scene {
        WindowGroup {
            RootView()
                .environmentObject(container)
                .environmentObject(container.sessionStore)
        }
        .modelContainer(container.modelContainer)
    }
}
