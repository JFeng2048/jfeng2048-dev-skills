import Foundation
import SwiftData

/// 技能（SwiftData 模型）
///
/// 注意：主键命名为 `skillID`，不要叫 `id`，
/// 否则会与 `PersistentModel: Identifiable` 自带的 `id` 冲突。
@Model
final class Skill {

    @Attribute(.unique) var skillID: String
    var title: String
    var author: String
    var avatar: String
    var tags: [String]
    var price: Double
    var detail: String
    var createdAt: String

    init(
        skillID: String,
        title: String,
        author: String = "",
        avatar: String = "",
        tags: [String] = [],
        price: Double = 0,
        detail: String = "",
        createdAt: String = ""
    ) {
        self.skillID = skillID
        self.title = title
        self.author = author
        self.avatar = avatar
        self.tags = tags
        self.price = price
        self.detail = detail
        self.createdAt = createdAt
    }

    /// 价格展示文案：0 元显示「免费」
    var priceText: String {
        price <= 0 ? String(localized: "detail.free") : String(format: "¥%.2f", price)
    }
}
