import Foundation

/// 技能传输对象：字段与后端一一对应
///
/// 后端字段名不同时只改这里的 `CodingKeys`，不要污染 SwiftData 模型。
struct SkillDTO: Decodable {

    let skillID: String
    let title: String?
    let author: String?
    let avatar: String?
    let tags: [String]?
    let price: Double?
    let detail: String?
    let createdAt: String?

    /// 后端返回的是 `id`，这里映射成 `skillID`
    private enum CodingKeys: String, CodingKey {
        case skillID = "id"
        case title
        case author
        case avatar
        case tags
        case price
        case detail
        case createdAt
    }

    /// DTO → SwiftData 模型
    func toModel() -> Skill {
        Skill(
            skillID: skillID,
            title: title ?? "",
            author: author ?? "",
            avatar: avatar ?? "",
            tags: tags ?? [],
            price: price ?? 0,
            detail: detail ?? "",
            createdAt: createdAt ?? ""
        )
    }
}
