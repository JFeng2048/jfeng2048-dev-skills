import SwiftUI

/// 根视图：按登录态分流，并统一承载导航栈。
///
/// 登录态变化时整棵树切换，不需要手动 push/pop 登录页。
struct RootView: View {

    @EnvironmentObject private var container: AppContainer
    @EnvironmentObject private var session: SessionStore

    @State private var path = NavigationPath()

    var body: some View {
        Group {
            if session.isLoggedIn {
                NavigationStack(path: $path) {
                    HomeView(
                        repository: container.skillRepository,
                        onSelect: { skill in
                            path.append(AppRoute.detail(id: skill.skillID))
                        },
                        onOpenMine: {
                            path.append(AppRoute.mine)
                        }
                    )
                    .navigationDestination(for: AppRoute.self) { route in
                        destination(for: route)
                    }
                }
            } else {
                LoginView(repository: container.authRepository, session: session)
            }
        }
        .animation(.default, value: session.isLoggedIn)
    }

    /// 路由分发：新增页面时在这里补 case
    @ViewBuilder
    private func destination(for route: AppRoute) -> some View {
        switch route {
        case .detail(let id):
            DetailView(repository: container.skillRepository, skillID: id)
        case .mine:
            MineView(session: session)
        }
    }
}
