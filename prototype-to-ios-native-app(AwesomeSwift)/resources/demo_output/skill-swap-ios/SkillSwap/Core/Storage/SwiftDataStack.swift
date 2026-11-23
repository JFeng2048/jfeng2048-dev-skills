import Foundation
import SwiftData

/// SwiftData 容器
///
/// 本地库损坏时退化为内存库，避免启动直接崩溃（数据丢失，但能进 App）。
enum SwiftDataStack {

    static let shared: ModelContainer = {
        let schema = Schema([Skill.self])

        do {
            let configuration = ModelConfiguration(schema: schema, isStoredInMemoryOnly: false)
            return try ModelContainer(for: schema, configurations: [configuration])
        } catch {
            // 注意：内存库只用于兜底，正式项目应在这里上报异常并引导用户清理数据
            let fallback = ModelConfiguration(schema: schema, isStoredInMemoryOnly: true)
            do {
                return try ModelContainer(for: schema, configurations: [fallback])
            } catch {
                fatalError("SwiftData 初始化失败：\(error)")
            }
        }
    }()
}
