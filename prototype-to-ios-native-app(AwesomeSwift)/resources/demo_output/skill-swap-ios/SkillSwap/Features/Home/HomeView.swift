import SwiftUI

/// 首页（列表范式）
///
/// 只做两件事：订阅 `state` 渲染、把用户操作转成 ViewModel 调用。
struct HomeView: View {

    @StateObject private var viewModel: HomeViewModel

    private let onSelect: (Skill) -> Void
    private let onOpenMine: () -> Void

    init(
        repository: SkillRepository,
        onSelect: @escaping (Skill) -> Void,
        onOpenMine: @escaping () -> Void
    ) {
        _viewModel = StateObject(wrappedValue: HomeViewModel(repository: repository))
        self.onSelect = onSelect
        self.onOpenMine = onOpenMine
    }

    var body: some View {
        content
            .navigationTitle(Text("home.title"))
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button {
                        onOpenMine()
                    } label: {
                        Image(systemName: "person.crop.circle")
                    }
                    .accessibilityLabel(Text("mine.title"))
                }
            }
            .searchable(text: $viewModel.keyword, prompt: Text("home.search.placeholder"))
            .task {
                await viewModel.loadIfNeeded()
            }
    }

    @ViewBuilder
    private var content: some View {
        switch viewModel.state {
        case .idle, .loading:
            VStack(spacing: AppTheme.Spacing.sm) {
                ProgressView()
                Text("common.loading")
                    .font(.footnote)
                    .foregroundStyle(AppTheme.textSecondary)
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
            .background(AppTheme.background)

        case .empty:
            ContentUnavailableView(
                "home.empty.title",
                systemImage: "tray",
                description: Text("home.empty.desc")
            )
            .background(AppTheme.background)

        case .failed(let message):
            failedView(message)

        case .loaded(let skills):
            list(skills)
        }
    }

    private func failedView(_ message: String) -> some View {
        VStack(spacing: AppTheme.Spacing.md) {
            Image(systemName: "exclamationmark.triangle")
                .font(.largeTitle)
                .foregroundStyle(AppTheme.brandPrimary)
            Text("home.error.title")
                .font(.headline)
            Text(message)
                .font(.footnote)
                .foregroundStyle(AppTheme.textSecondary)
                .multilineTextAlignment(.center)
            Button("common.retry") {
                Task { await viewModel.refresh() }
            }
            .buttonStyle(.borderedProminent)
        }
        .padding(AppTheme.Spacing.xl)
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(AppTheme.background)
    }

    private func list(_ skills: [Skill]) -> some View {
        List {
            ForEach(skills) { skill in
                Button {
                    onSelect(skill)
                } label: {
                    SkillCard(skill: skill)
                }
                .buttonStyle(.plain)
                .listRowSeparator(.hidden)
                .listRowBackground(Color.clear)
                .onAppear {
                    guard skill.skillID == skills.last?.skillID else { return }
                    Task { await viewModel.loadMore() }
                }
            }

            if viewModel.isLoadingMore {
                HStack {
                    Spacer()
                    ProgressView()
                    Spacer()
                }
                .listRowSeparator(.hidden)
                .listRowBackground(Color.clear)
            } else if !viewModel.hasMore {
                Text("common.no_more")
                    .font(.footnote)
                    .foregroundStyle(AppTheme.textSecondary)
                    .frame(maxWidth: .infinity)
                    .listRowSeparator(.hidden)
                    .listRowBackground(Color.clear)
            }
        }
        .listStyle(.plain)
        .scrollContentBackground(.hidden)
        .background(AppTheme.background)
        .refreshable {
            await viewModel.refresh()
        }
    }
}
