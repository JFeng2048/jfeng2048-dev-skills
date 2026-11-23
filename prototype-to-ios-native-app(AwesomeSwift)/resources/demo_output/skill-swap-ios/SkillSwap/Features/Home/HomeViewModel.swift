import Foundation
import Combine

/// 首页（信息流）ViewModel
///
/// 只依赖 Repository 协议，不 import SwiftUI / Alamofire。
@MainActor
final class HomeViewModel: ObservableObject {

    @Published private(set) var state: LoadState<[Skill]> = .idle
    @Published private(set) var isLoadingMore = false
    @Published private(set) var hasMore = true

    /// 搜索关键词：与 `.searchable` 双向绑定，Combine 防抖后触发重载
    @Published var keyword: String = ""

    private let repository: SkillRepository
    private var page = 0
    private var cancellables = Set<AnyCancellable>()

    init(repository: SkillRepository) {
        self.repository = repository
        bindKeyword()
    }

    private func bindKeyword() {
        $keyword
            .dropFirst()                              // 忽略初始空串
            .debounce(for: .milliseconds(300), scheduler: RunLoop.main)
            .removeDuplicates()
            .sink { [weak self] _ in
                Task { await self?.reload() }
            }
            .store(in: &cancellables)
    }

    /// 页面首次出现时调用，避免重复加载
    func loadIfNeeded() async {
        guard case .idle = state else { return }
        await reload()
    }

    /// 下拉刷新 / 重试
    func refresh() async {
        await reload()
    }

    private func reload() async {
        state = .loading
        page = 0
        do {
            let skills = try await repository.fetchSkills(
                page: 0,
                pageSize: AppConfig.pageSize,
                keyword: keyword
            )
            page = 1
            hasMore = skills.count >= AppConfig.pageSize
            state = skills.isEmpty ? .empty : .loaded(skills)
        } catch {
            state = .failed(APIError.from(error).localizedDescription)
        }
    }

    /// 上拉加载：由列表最后一项触发
    func loadMore() async {
        guard hasMore, !isLoadingMore, case .loaded(let current) = state else { return }

        isLoadingMore = true
        defer { isLoadingMore = false }

        do {
            let next = try await repository.fetchSkills(
                page: page,
                pageSize: AppConfig.pageSize,
                keyword: keyword
            )
            page += 1
            hasMore = next.count >= AppConfig.pageSize
            state = .loaded(current + next)
        } catch {
            // 加载更多失败不打断已有内容，只停止继续加载
            hasMore = false
        }
    }
}
