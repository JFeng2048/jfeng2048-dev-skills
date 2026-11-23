import Foundation

/// Mock 数据：与真实接口同形状，用于无后端时还原界面与交互
///
/// 刻意包含边界数据：超长标题、空标签、超长描述。
enum MockData {

    /// 12 条，足够触发两页分页
    static var skills: [Skill] { (1...12).map(makeSkill) }

    /// 分页 + 关键词过滤，语义与真实接口一致（page 从 0 开始）
    static func pageSkills(page: Int, pageSize: Int, keyword: String?) -> [Skill] {
        let all = skills
        let key = (keyword ?? "").trimmingCharacters(in: .whitespaces)
        let filtered = key.isEmpty
            ? all
            : all.filter { $0.title.contains(key) || $0.detail.contains(key) }

        let start = page * pageSize
        guard start < filtered.count else { return [] }
        return Array(filtered[start..<min(start + pageSize, filtered.count)])
    }

    static func skill(id: String) -> Skill? {
        skills.first { $0.skillID == id }
    }

    /// mock 登录：账号非空且密码不少于 6 位即通过
    static func login(username: String, password: String) -> String? {
        let name = username.trimmingCharacters(in: .whitespaces)
        guard !name.isEmpty, password.count >= 6 else { return nil }
        return "mock-token-\(name)"
    }

    // MARK: - 构造

    private static func makeSkill(_ index: Int) -> Skill {
        Skill(
            skillID: "\(index)",
            title: title(for: index),
            author: "同学\(index)",
            avatar: "https://picsum.photos/seed/skill\(index)/200/200",
            tags: index == 4 ? [] : ["线下", "周末", "免费"],
            price: index % 3 == 0 ? 0 : Double(30 + index),
            detail: index == 5
                ? String(repeating: "这是一个超长描述的边界用例。", count: 20)
                : "可线上或线下，时间灵活，欢迎私聊细聊。",
            createdAt: "2026-11-0\(index % 9 + 1)"
        )
    }

    private static func title(for index: Int) -> String {
        switch index {
        case 1:
            return "可以教你吉他入门到弹唱，学期内包会"
        case 2:
            return "Canva 海报设计 / 公众号首图 一对一辅导，含源文件"
        case 3:
            return "Python 数据分析入门（pandas + 可视化）"
        default:
            return "技能互换 #\(index)：我教你 X，你教我 Y"
        }
    }
}
