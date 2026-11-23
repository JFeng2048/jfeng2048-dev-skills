import SwiftUI
import Kingfisher

/// 详情页（详情范式）：可滚动内容 + 底部固定操作栏
struct DetailView: View {

    @StateObject private var viewModel: DetailViewModel
    @State private var showContactDone = false

    init(repository: SkillRepository, skillID: String) {
        _viewModel = StateObject(wrappedValue: DetailViewModel(repository: repository, skillID: skillID))
    }

    var body: some View {
        content
            .navigationTitle(Text("detail.title"))
            .navigationBarTitleDisplayMode(.inline)
            .task {
                await viewModel.loadIfNeeded()
            }
    }

    @ViewBuilder
    private var content: some View {
        switch viewModel.state {
        case .idle, .loading:
            ProgressView()
                .frame(maxWidth: .infinity, maxHeight: .infinity)
                .background(AppTheme.background)

        case .empty:
            ContentUnavailableView("detail.not_found", systemImage: "questionmark.folder")

        case .failed(let message):
            VStack(spacing: AppTheme.Spacing.md) {
                Image(systemName: "exclamationmark.triangle")
                    .font(.largeTitle)
                    .foregroundStyle(AppTheme.brandPrimary)
                Text(message)
                    .font(.footnote)
                    .foregroundStyle(AppTheme.textSecondary)
                    .multilineTextAlignment(.center)
                Button("common.retry") {
                    Task { await viewModel.load() }
                }
                .buttonStyle(.borderedProminent)
            }
            .padding(AppTheme.Spacing.xl)
            .frame(maxWidth: .infinity, maxHeight: .infinity)
            .background(AppTheme.background)

        case .loaded(let skill):
            detailBody(skill)
        }
    }

    private func detailBody(_ skill: Skill) -> some View {
        ScrollView {
            VStack(alignment: .leading, spacing: AppTheme.Spacing.lg) {
                KFImage(URL(string: skill.avatar))
                    .placeholder {
                        Rectangle().fill(AppTheme.surface)
                    }
                    .resizable()
                    .scaledToFill()
                    .frame(maxWidth: .infinity)
                    .frame(height: AppTheme.Size.detailHero)
                    .clipShape(RoundedRectangle(cornerRadius: AppTheme.Radius.md, style: .continuous))

                Text(skill.title)
                    .font(.title3.weight(.semibold))
                    .foregroundStyle(AppTheme.textPrimary)

                HStack {
                    Text(skill.author)
                        .font(.subheadline)
                        .foregroundStyle(AppTheme.textSecondary)
                    Spacer()
                    Text(skill.priceText)
                        .font(.headline)
                        .foregroundStyle(AppTheme.brandPrimary)
                }

                if !skill.tags.isEmpty {
                    Text(skill.tags.joined(separator: " / "))
                        .font(.caption)
                        .foregroundStyle(AppTheme.textSecondary)
                }

                Divider()

                Text(skill.detail.isEmpty ? String(localized: "detail.empty_desc") : skill.detail)
                    .font(.body)
                    .foregroundStyle(AppTheme.textPrimary)
            }
            .padding(AppTheme.Spacing.lg)
        }
        .background(AppTheme.background)
        .safeAreaInset(edge: .bottom) {
            Button {
                showContactDone = true
            } label: {
                Text("detail.contact")
                    .frame(maxWidth: .infinity)
            }
            .buttonStyle(.borderedProminent)
            .controlSize(.large)
            .padding(AppTheme.Spacing.lg)
            .background(.thinMaterial)
        }
        .alert("detail.contact.done", isPresented: $showContactDone) {
            Button("common.confirm", role: .cancel) {}
        }
    }
}
