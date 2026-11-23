import SwiftUI

/// 我的页面（个人中心 / 设置范式）
struct MineView: View {

    @StateObject private var viewModel: MineViewModel
    @State private var showLogoutConfirm = false

    init(session: SessionStore) {
        _viewModel = StateObject(wrappedValue: MineViewModel(session: session))
    }

    var body: some View {
        List {
            Section {
                HStack(spacing: AppTheme.Spacing.md) {
                    Circle()
                        .fill(AppTheme.brandPrimary.opacity(0.15))
                        .frame(width: AppTheme.Size.avatar, height: AppTheme.Size.avatar)
                        .overlay {
                            Text("mine.nickname")
                                .font(.headline)
                                .foregroundStyle(AppTheme.brandPrimary)
                        }

                    VStack(alignment: .leading, spacing: AppTheme.Spacing.xs) {
                        Text("mine.nickname")
                            .font(.headline)
                        Text("mine.signature")
                            .font(.caption)
                            .foregroundStyle(AppTheme.textSecondary)
                    }
                }
                .padding(.vertical, AppTheme.Spacing.xs)
            }

            Section {
                Label("mine.my_posts", systemImage: "square.grid.2x2")
                Label("mine.settings", systemImage: "gearshape")
                Label("mine.about", systemImage: "info.circle")
            }

            Section {
                Button(role: .destructive) {
                    showLogoutConfirm = true
                } label: {
                    Text("mine.logout")
                        .frame(maxWidth: .infinity)
                }
            }
        }
        .navigationTitle(Text("mine.title"))
        .navigationBarTitleDisplayMode(.inline)
        .confirmationDialog(
            "mine.logout.confirm.title",
            isPresented: $showLogoutConfirm,
            titleVisibility: .visible
        ) {
            Button("mine.logout", role: .destructive) {
                viewModel.logout()
            }
            Button("common.cancel", role: .cancel) {}
        } message: {
            Text("mine.logout.confirm.message")
        }
    }
}
