import Foundation
import SwiftData

/// 技能数据接缝
///
/// 页面与 ViewModel 只依赖这个协议；mock / 真实接口 / 缓存回落都在实现里。
@MainActor
protocol SkillRepository {
    func fetchSkills(page: Int, pageSize: Int, keyword: String?) async throws -> [Skill]
    func fetchDetail(id: String) async throws -> Skill
}

@MainActor
final class DefaultSkillRepository: SkillRepository {

    private let client: APIClient
    private let context: ModelContext

    init(client: APIClient, context: ModelContext) {
        self.client = client
        self.context = context
    }

    // MARK: - 列表

    func fetchSkills(page: Int, pageSize: Int, keyword: String?) async throws -> [Skill] {
        if AppConfig.useMock {
            try await Task.sleep(nanoseconds: 300_000_000) // 让 Loading 态可见
            return MockData.pageSkills(page: page, pageSize: pageSize, keyword: keyword)
        }

        do {
            let dtos: [SkillDTO] = try await client.request(
                .skills(page: page, pageSize: pageSize, keyword: keyword)
            )
            let models = dtos.map { $0.toModel() }

            // 第一页覆盖式写入，后续页追加
            if page == 0 {
                try? context.delete(model: Skill.self)
            }
            models.forEach { context.insert($0) }
            try? context.save()

            return models
        } catch {
            // 仅第一页回落到缓存，避免分页拼接错乱
            if page == 0 {
                let cached = (try? context.fetch(FetchDescriptor<Skill>())) ?? []
                if !cached.isEmpty { return cached }
            }
            throw APIError.from(error)
        }
    }

    // MARK: - 详情

    func fetchDetail(id: String) async throws -> Skill {
        if AppConfig.useMock {
            try await Task.sleep(nanoseconds: 200_000_000)
            guard let skill = MockData.skill(id: id) else { throw APIError.emptyData }
            return skill
        }

        do {
            let dto: SkillDTO = try await client.request(.skillDetail(id: id))
            let model = dto.toModel()
            context.insert(model)
            try? context.save()
            return model
        } catch {
            let descriptor = FetchDescriptor<Skill>(predicate: #Predicate { $0.skillID == id })
            if let cached = try? context.fetch(descriptor), let first = cached.first {
                return first
            }
            throw APIError.from(error)
        }
    }
}
