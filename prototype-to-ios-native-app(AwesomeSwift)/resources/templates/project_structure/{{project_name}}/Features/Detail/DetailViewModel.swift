import Foundation
import Combine

/// 详情页 ViewModel
@MainActor
final class DetailViewModel: ObservableObject {

    @Published private(set) var state: LoadState<Skill> = .idle

    private let repository: SkillRepository
    private let skillID: String

    init(repository: SkillRepository, skillID: String) {
        self.repository = repository
        self.skillID = skillID
    }

    func loadIfNeeded() async {
        guard case .idle = state else { return }
        await load()
    }

    func load() async {
        state = .loading
        do {
            let skill = try await repository.fetchDetail(id: skillID)
            state = .loaded(skill)
        } catch {
            state = .failed(APIError.from(error).localizedDescription)
        }
    }
}
